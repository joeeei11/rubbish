"""
将 YOLO 检测数据集转换为四分类图片数据集。

转换策略：
1. 读取 `data.yaml` 中 40 个细分类与四大类映射；
2. 遍历 images/train|val 与对应 labels/train|val；
3. 按标注框从原图裁剪垃圾主体；
4. 按四大类输出到 `data/garbage_dataset/{train,val}/{recyclable,hazardous,kitchen,other}`。
"""
from __future__ import annotations

import argparse
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageFile
import yaml

ImageFile.LOAD_TRUNCATED_IMAGES = True

TARGET_CLASS_MAP = {
    "Recyclables": "recyclable",
    "HazardousWaste": "hazardous",
    "KitchenWaste": "kitchen",
    "OtherGarbage": "other",
}


def parse_args():
    parser = argparse.ArgumentParser(description="将 YOLO 检测数据集转换为四分类图片集")
    parser.add_argument("--dataset-root", required=True, help="YOLO 数据集根目录，包含 data.yaml 与 datasets/")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[2] / "data" / "garbage_dataset"),
        help="输出目录，默认 data/garbage_dataset",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=32,
        help="裁剪后最小边长，小于该值的框会被跳过",
    )
    parser.add_argument(
        "--padding",
        type=float,
        default=0.08,
        help="在标注框周围额外保留的边界比例",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="转换前清空输出目录中的已有图片",
    )
    return parser.parse_args()


def ensure_output_dirs(output_dir: Path):
    for split in ("train", "val"):
        for class_name in TARGET_CLASS_MAP.values():
            (output_dir / split / class_name).mkdir(parents=True, exist_ok=True)


def clean_output_dirs(output_dir: Path):
    for split in ("train", "val"):
        for class_name in TARGET_CLASS_MAP.values():
            class_dir = output_dir / split / class_name
            if not class_dir.exists():
                continue
            for file_path in class_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()


def load_class_mapping(dataset_root: Path):
    yaml_path = dataset_root / "data.yaml"
    with yaml_path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)

    names = data["names"]
    category_mapping = data["category_mapping"]

    fine_to_target = {}
    for group_name, fine_classes in category_mapping.items():
        target_name = TARGET_CLASS_MAP[group_name]
        for fine_class in fine_classes:
            fine_to_target[fine_class] = target_name

    class_id_to_target = {}
    for class_id, fine_class_name in enumerate(names):
        if fine_class_name not in fine_to_target:
            raise ValueError(f"未找到细分类 {fine_class_name} 的大类映射")
        class_id_to_target[class_id] = fine_to_target[fine_class_name]

    return class_id_to_target


def yolo_to_xyxy(x_center, y_center, width, height, image_width, image_height, padding_ratio):
    box_width = width * image_width
    box_height = height * image_height
    x_center *= image_width
    y_center *= image_height

    pad_x = box_width * padding_ratio
    pad_y = box_height * padding_ratio

    left = max(0, int(round(x_center - box_width / 2 - pad_x)))
    top = max(0, int(round(y_center - box_height / 2 - pad_y)))
    right = min(image_width, int(round(x_center + box_width / 2 + pad_x)))
    bottom = min(image_height, int(round(y_center + box_height / 2 + pad_y)))
    return left, top, right, bottom


def convert_split(dataset_root: Path, output_dir: Path, split: str, class_id_to_target: dict, min_size: int, padding: float):
    image_dir = dataset_root / "datasets" / "images" / split
    label_dir = dataset_root / "datasets" / "labels" / split
    summary = defaultdict(int)
    skipped_images = 0

    image_paths = sorted(path for path in image_dir.iterdir() if path.is_file())
    for image_path in image_paths:
        label_path = label_dir / f"{image_path.stem}.txt"
        if not label_path.exists():
            continue

        try:
            with Image.open(image_path) as image:
                image = image.convert("RGB")
                image_width, image_height = image.size
                label_lines = [line.strip() for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]

                for index, line in enumerate(label_lines, start=1):
                    parts = line.split()
                    if len(parts) != 5:
                        continue

                    class_id = int(float(parts[0]))
                    x_center, y_center, width, height = map(float, parts[1:])
                    left, top, right, bottom = yolo_to_xyxy(
                        x_center=x_center,
                        y_center=y_center,
                        width=width,
                        height=height,
                        image_width=image_width,
                        image_height=image_height,
                        padding_ratio=padding,
                    )

                    crop_width = right - left
                    crop_height = bottom - top
                    if crop_width < min_size or crop_height < min_size:
                        continue

                    target_class = class_id_to_target[class_id]
                    crop = image.crop((left, top, right, bottom))
                    output_name = f"{image_path.stem}_{index:02d}.jpg"
                    output_path = output_dir / split / target_class / output_name
                    crop.save(output_path, format="JPEG", quality=95)
                    summary[target_class] += 1
        except Exception:
            skipped_images += 1
            continue

    summary["_skipped_images"] = skipped_images
    return summary


def main():
    args = parse_args()
    dataset_root = Path(args.dataset_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not dataset_root.exists():
        raise FileNotFoundError(f"未找到数据集目录：{dataset_root}")

    ensure_output_dirs(output_dir)
    if args.clean:
        clean_output_dirs(output_dir)

    class_id_to_target = load_class_mapping(dataset_root)
    total_summary = {}
    for split in ("train", "val"):
        total_summary[split] = convert_split(
            dataset_root=dataset_root,
            output_dir=output_dir,
            split=split,
            class_id_to_target=class_id_to_target,
            min_size=args.min_size,
            padding=args.padding,
        )

    print("YOLO 检测集转换完成。")
    for split in ("train", "val"):
        print(f"[{split}]")
        for class_name in TARGET_CLASS_MAP.values():
            print(f"  {class_name}: {total_summary[split].get(class_name, 0)}")


if __name__ == "__main__":
    main()
