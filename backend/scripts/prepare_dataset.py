"""
将原始垃圾图像数据整理为项目要求的四分类目录结构。

支持把常见公开数据集中的类别名映射到：
- recyclable
- hazardous
- kitchen
- other
"""
from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
TARGET_CLASSES = ("recyclable", "hazardous", "kitchen", "other")
CLASS_ALIASES = {
    "recyclable": {
        "recyclable", "recycle", "cardboard", "glass", "metal", "paper", "plastic",
        "bottle", "bottles", "can", "cans", "carton",
    },
    "hazardous": {
        "hazardous", "battery", "batteries", "bulb", "bulbs", "lamp", "lamps",
        "electronics", "electronic", "ewaste", "e-waste", "medicine", "medicines",
    },
    "kitchen": {
        "kitchen", "organic", "organics", "food", "foodwaste", "food-waste",
        "kitchenwaste", "kitchen-waste", "bio", "biological", "compost",
    },
    "other": {
        "other", "trash", "residual", "landfill", "general", "clothes", "shoes",
        "fabric", "mask", "tissue",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description="整理垃圾图像数据集为四分类目录")
    parser.add_argument("--raw-dir", required=True, help="原始数据目录，按类别文件夹存放图片")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[2] / "data" / "garbage_dataset"),
        help="输出目录，默认写入 data/garbage_dataset",
    )
    parser.add_argument("--train-ratio", type=float, default=0.8, help="训练集比例")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument(
        "--mode",
        choices=("copy", "move"),
        default="copy",
        help="整理方式：复制或移动",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="写入前先清空 output-dir 下 train/ 和 val/ 中已有图片",
    )
    return parser.parse_args()


def normalize_name(name: str) -> str:
    return (
        name.strip().lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def guess_target_class(folder_name: str) -> str | None:
    normalized = normalize_name(folder_name)
    for target_class, aliases in CLASS_ALIASES.items():
        if normalized in aliases:
            return target_class
    return None


def list_images(folder: Path):
    return sorted(
        path for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def ensure_output_dirs(output_dir: Path):
    for split in ("train", "val"):
        for target_class in TARGET_CLASSES:
            (output_dir / split / target_class).mkdir(parents=True, exist_ok=True)


def clean_existing_images(output_dir: Path):
    for split in ("train", "val"):
        for target_class in TARGET_CLASSES:
            class_dir = output_dir / split / target_class
            if not class_dir.exists():
                continue
            for image_path in class_dir.iterdir():
                if image_path.is_file():
                    image_path.unlink()


def copy_or_move(src: Path, dst: Path, mode: str):
    if mode == "move":
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(src, dst)


def main():
    args = parse_args()
    raw_dir = Path(args.raw_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not raw_dir.exists():
        raise FileNotFoundError(f"未找到原始数据目录：{raw_dir}")

    ensure_output_dirs(output_dir)
    if args.clean:
        clean_existing_images(output_dir)

    rng = random.Random(args.seed)
    summary = {
        split: {target_class: 0 for target_class in TARGET_CLASSES}
        for split in ("train", "val")
    }
    skipped_folders = []

    for folder in sorted(path for path in raw_dir.iterdir() if path.is_dir()):
        target_class = guess_target_class(folder.name)
        if target_class is None:
            skipped_folders.append(folder.name)
            continue

        images = list_images(folder)
        if not images:
            continue

        rng.shuffle(images)
        train_count = max(1, int(len(images) * args.train_ratio))
        train_images = images[:train_count]
        val_images = images[train_count:] or images[-1:]

        for split, split_images in (("train", train_images), ("val", val_images)):
            for index, image_path in enumerate(split_images, start=1):
                dst_name = f"{folder.name}_{index:05d}{image_path.suffix.lower()}"
                dst_path = output_dir / split / target_class / dst_name
                copy_or_move(image_path, dst_path, args.mode)
                summary[split][target_class] += 1

    print("数据整理完成。")
    for split in ("train", "val"):
        print(f"[{split}]")
        for target_class in TARGET_CLASSES:
            print(f"  {target_class}: {summary[split][target_class]}")

    if skipped_folders:
        print("以下目录未匹配到目标分类，已跳过：")
        for folder_name in skipped_folders:
            print(f"  - {folder_name}")


if __name__ == "__main__":
    main()
