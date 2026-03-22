"""
检查 Phase 4 图像数据集是否满足最小样本量要求。
"""
from __future__ import annotations

import argparse
from pathlib import Path


MIN_COUNTS = {
    "train": {
        "recyclable": 300,
        "hazardous": 200,
        "kitchen": 300,
        "other": 200,
    },
    "val": {
        "recyclable": 60,
        "hazardous": 40,
        "kitchen": 60,
        "other": 40,
    },
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def parse_args():
    parser = argparse.ArgumentParser(description="检查垃圾图像数据集样本量")
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parents[2] / "data" / "garbage_dataset"),
        help="数据集根目录",
    )
    return parser.parse_args()


def count_images(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(
        1
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def main():
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    if not data_dir.exists():
        raise FileNotFoundError(f"未找到数据集目录：{data_dir}")

    all_passed = True
    for split, class_rules in MIN_COUNTS.items():
        print(f"[{split}]")
        for target_class, expected in class_rules.items():
            class_dir = data_dir / split / target_class
            actual = count_images(class_dir)
            passed = actual >= expected
            all_passed = all_passed and passed
            status = "PASS" if passed else "FAIL"
            print(f"  {target_class:<11} actual={actual:<4} expected>={expected:<3} {status}")

    print()
    print("结论：样本量满足最小要求。" if all_passed else "结论：样本量尚未满足最小要求。")


if __name__ == "__main__":
    main()
