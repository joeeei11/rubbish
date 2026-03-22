# 垃圾图像数据集目录

本目录用于放置 Phase 4 的图像分类训练数据，仓库中仅保留目录结构，不提交真实图片文件。

推荐结构：

```text
data/garbage_dataset/
├── train/
│   ├── recyclable/
│   ├── hazardous/
│   ├── kitchen/
│   └── other/
└── val/
    ├── recyclable/
    ├── hazardous/
    ├── kitchen/
    └── other/
```

建议最小样本量：

- `train/recyclable/`：不少于 300 张
- `train/hazardous/`：不少于 200 张
- `train/kitchen/`：不少于 300 张
- `train/other/`：不少于 200 张
- `val/recyclable/`：不少于 60 张
- `val/hazardous/`：不少于 40 张
- `val/kitchen/`：不少于 60 张
- `val/other/`：不少于 40 张

准备完数据后，可在 `backend/` 目录执行：

```bash
python ai_model/train.py --epochs 50
```
