"""
MobileNetV3-Large 垃圾分类训练脚本。
使用 ImageFolder 目录结构读取数据集，支持类别权重补偿、余弦退火调度、
增强数据增广和 early stopping，保存最佳权重文件。
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import torch
from torch import nn, optim
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large


IMAGE_MEAN = [0.485, 0.456, 0.406]
IMAGE_STD = [0.229, 0.224, 0.225]
EXPECTED_CLASSES = ["recyclable", "hazardous", "kitchen", "other"]


def parse_args():
    parser = argparse.ArgumentParser(description="训练垃圾分类 MobileNetV3-Large 模型")
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parents[2] / "data" / "garbage_dataset"),
        help="数据集根目录，内部需包含 train/ 和 val/",
    )
    parser.add_argument("--epochs", type=int, default=60, help="训练轮数")
    parser.add_argument("--batch-size", type=int, default=32, help="批大小")
    parser.add_argument("--lr", type=float, default=3e-4, help="初始学习率")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader 线程数")
    parser.add_argument("--image-size", type=int, default=224, help="输入尺寸")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping 耐心轮数")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent / "weights" / "mobilenetv3_garbage.pth"),
        help="最佳模型输出路径",
    )
    parser.add_argument(
        "--no-pretrained",
        action="store_true",
        help="不加载 torchvision 预训练权重",
    )
    return parser.parse_args()


def build_transforms(image_size: int):
    """
    训练阶段使用更激进的数据增广：
    - RandomResizedCrop 放宽裁剪范围
    - RandomRotation 随机旋转
    - RandomAffine 仿射变换
    - ColorJitter 更强的颜色抖动
    - RandomErasing 随机擦除（模拟遮挡）
    """
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(image_size, scale=(0.6, 1.0), ratio=(0.8, 1.2)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(p=0.1),
        transforms.RandomRotation(degrees=15),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGE_MEAN, std=IMAGE_STD),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.15)),
    ])
    val_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGE_MEAN, std=IMAGE_STD),
    ])
    return train_transform, val_transform


def compute_class_weights(dataset):
    """根据训练集样本数计算反比类别权重，用于 CrossEntropyLoss。"""
    targets = [sample[1] for sample in dataset.samples]
    counter = Counter(targets)
    total = len(targets)
    num_classes = len(counter)

    weights = []
    for cls_idx in range(num_classes):
        count = counter.get(cls_idx, 1)
        # 反比权重：样本越少，权重越大
        weights.append(total / (num_classes * count))

    # 归一化使权重均值为 1
    mean_weight = sum(weights) / len(weights)
    weights = [w / mean_weight for w in weights]

    print(f"[train] 类别权重: {dict(zip(dataset.classes, [f'{w:.3f}' for w in weights]))}")
    return torch.tensor(weights, dtype=torch.float32)


def build_dataloaders(data_dir: Path, image_size: int, batch_size: int, num_workers: int):
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError("未找到 train/ 或 val/ 目录，请先准备数据集")

    train_transform, val_transform = build_transforms(image_size)
    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transform)

    if sorted(train_dataset.classes) != sorted(EXPECTED_CLASSES):
        raise ValueError(
            f"数据集类别必须为 {EXPECTED_CLASSES}，当前为 {train_dataset.classes}"
        )
    if train_dataset.classes != val_dataset.classes:
        raise ValueError("train/ 与 val/ 的类别目录不一致")

    # 打印数据集统计
    print(f"[train] 数据集路径: {data_dir}")
    for cls_name in train_dataset.classes:
        cls_idx = train_dataset.class_to_idx[cls_name]
        train_count = sum(1 for _, label in train_dataset.samples if label == cls_idx)
        val_count = sum(1 for _, label in val_dataset.samples if label == cls_idx)
        print(f"[train] {cls_name}: 训练 {train_count} 张, 验证 {val_count} 张")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )
    return train_dataset, train_loader, val_loader


def build_model(num_classes: int, pretrained: bool):
    """构建 MobileNetV3-Large 并替换分类头。"""
    weights = None if not pretrained else MobileNet_V3_Large_Weights.DEFAULT
    model = mobilenet_v3_large(weights=weights)

    # 冻结前几层特征提取器（微调策略）
    if pretrained:
        for param in model.features[:12].parameters():
            param.requires_grad = False

    # 替换分类头：增加 Dropout 防止过拟合
    in_features = model.classifier[-1].in_features
    model.classifier = nn.Sequential(
        nn.Linear(960, 1280),
        nn.Hardswish(inplace=True),
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(1280, num_classes),
    )
    return model


def evaluate(model, dataloader, criterion, device):
    """评估模型，返回损失、总准确率和各类别准确率。"""
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_count = 0
    class_correct = {}
    class_count = {}

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)

            preds = logits.argmax(dim=1)
            total_loss += loss.item() * images.size(0)
            total_correct += (preds == labels).sum().item()
            total_count += images.size(0)

            for pred, label in zip(preds.tolist(), labels.tolist()):
                class_count[label] = class_count.get(label, 0) + 1
                if pred == label:
                    class_correct[label] = class_correct.get(label, 0) + 1

    avg_loss = total_loss / max(total_count, 1)
    accuracy = total_correct / max(total_count, 1)
    per_class_acc = {}
    for cls_idx in sorted(class_count.keys()):
        correct = class_correct.get(cls_idx, 0)
        count = class_count[cls_idx]
        per_class_acc[cls_idx] = correct / count if count > 0 else 0.0

    return avg_loss, accuracy, per_class_acc


def main():
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[train] 模型: MobileNetV3-Large")
    print(f"[train] 预训练: {'是' if not args.no_pretrained else '否'}")
    print(f"[train] 轮数: {args.epochs}, 批大小: {args.batch_size}, 学习率: {args.lr}")
    print(f"[train] Early stopping 耐心: {args.patience} 轮")

    train_dataset, train_loader, val_loader = build_dataloaders(
        data_dir=data_dir,
        image_size=args.image_size,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[train] 设备: {device}")

    model = build_model(len(train_dataset.classes), pretrained=not args.no_pretrained).to(device)

    # 类别权重补偿：解决数据��均衡
    class_weights = compute_class_weights(train_dataset).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)

    # 分层学习率：冻结层不参与优化
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.AdamW(trainable_params, lr=args.lr, weight_decay=1e-4)

    # 余弦退火学习率调度
    scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2, eta_min=1e-6)

    best_val_acc = 0.0
    patience_counter = 0

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        model.train()
        running_loss = 0.0
        running_correct = 0
        running_count = 0

        # 第 15 轮后解冻全部参��进行全模型微调
        if epoch == 15 and not args.no_pretrained:
            print("[train] 解冻全部参数，开始全模型微调")
            for param in model.parameters():
                param.requires_grad = True
            optimizer = optim.AdamW(model.parameters(), lr=args.lr * 0.3, weight_decay=1e-4)
            scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2, eta_min=1e-6)

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()

            # 梯度裁剪防止梯度爆炸
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            running_correct += (logits.argmax(dim=1) == labels).sum().item()
            running_count += images.size(0)

        scheduler.step()

        train_loss = running_loss / max(running_count, 1)
        train_acc = running_correct / max(running_count, 1)
        val_loss, val_acc, per_class_acc = evaluate(model, val_loader, criterion, device)
        epoch_time = time.time() - epoch_start

        # 格式化各类别准确率
        cls_acc_str = " | ".join(
            f"{train_dataset.classes[k]}={v:.2%}"
            for k, v in per_class_acc.items()
        )

        current_lr = optimizer.param_groups[0]["lr"]
        print(
            f"[Epoch {epoch:02d}/{args.epochs}] "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} "
            f"lr={current_lr:.6f} time={epoch_time:.1f}s"
        )
        print(f"  各类别准确率: {cls_acc_str}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "class_to_idx": train_dataset.class_to_idx,
                    "best_val_acc": best_val_acc,
                    "image_size": args.image_size,
                    "model_arch": "mobilenet_v3_large",
                },
                output_path,
            )
            print(f"  >>> 新最佳模型已保存 (val_acc={val_acc:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"[train] Early stopping：验证集准确率连续 {args.patience} 轮无提升")
                break

    label_map_path = Path(__file__).resolve().parent / "label_map.json"
    if label_map_path.exists():
        with label_map_path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)
        print(f"标签映射已确认：{payload}")

    print(f"\n训练完成，最佳验证集准确率：{best_val_acc:.4f}")
    print(f"最佳模型已保存到：{output_path}")


if __name__ == "__main__":
    main()
