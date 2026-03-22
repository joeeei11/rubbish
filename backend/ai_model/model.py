"""
AI 模型加载与推理工具。
优先加载训练好的 MobileNetV3-Small 权重；若本地权重缺失，则保留未就绪状态，
由上层服务决定是否回退到文件名匹配方案。
"""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image, UnidentifiedImageError
from flask import current_app, has_app_context


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
LABEL_MAP_PATH = BASE_DIR / "label_map.json"
DEFAULT_WEIGHTS_PATH = BASE_DIR / "weights" / "mobilenetv3_garbage.pth"
IMAGE_MEAN = [0.485, 0.456, 0.406]
IMAGE_STD = [0.229, 0.224, 0.225]

_MODEL = None
_MODEL_ERROR = None
_LABEL_MAP = None
_LABEL_MAP_ZH = None
_TORCH_MODULE = None
_TRANSFORMS_MODULE = None
_MOBILENET_FACTORY_SMALL = None
_MOBILENET_FACTORY_LARGE = None


def _ensure_ml_dependencies():
    """按需导入 PyTorch 与 torchvision，避免未安装时阻塞整个应用。"""
    global _TORCH_MODULE, _TRANSFORMS_MODULE, _MOBILENET_FACTORY_SMALL, _MOBILENET_FACTORY_LARGE

    if _TORCH_MODULE is not None and _TRANSFORMS_MODULE is not None:
        return _TORCH_MODULE, _TRANSFORMS_MODULE

    try:
        import torch
        from torchvision import transforms
        from torchvision.models import mobilenet_v3_large, mobilenet_v3_small
    except ModuleNotFoundError as exc:
        raise RuntimeError("未安装 PyTorch 或 torchvision，请先安装 AI 推理依赖") from exc

    _TORCH_MODULE = torch
    _TRANSFORMS_MODULE = transforms
    _MOBILENET_FACTORY_SMALL = mobilenet_v3_small
    _MOBILENET_FACTORY_LARGE = mobilenet_v3_large
    return _TORCH_MODULE, _TRANSFORMS_MODULE


def _load_label_maps() -> tuple[Dict[int, str], Dict[str, str]]:
    """加载标签映射文件。"""
    with LABEL_MAP_PATH.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)

    label_map = {
        int(index): label
        for index, label in payload.items()
        if str(index).isdigit()
    }
    label_map_zh = payload.get("_labels", {})
    return label_map, label_map_zh


def _get_weights_path() -> Path:
    """根据配置解析权重文件路径。"""
    configured_path = None
    if has_app_context():
        configured_path = current_app.config.get("MODEL_WEIGHTS_PATH")

    raw_path = (configured_path or str(DEFAULT_WEIGHTS_PATH)).strip()
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


def _get_input_size() -> int:
    """读取模型输入尺寸配置。"""
    if has_app_context():
        return int(current_app.config.get("MODEL_INPUT_SIZE", 224))
    return 224


def _build_model(num_classes: int, arch: str = "auto"):
    """
    构建分类模型，自动适配 MobileNetV3-Large 或 Small。
    arch: "large" / "small" / "auto"（自动从权重文件中读取）
    """
    torch, _ = _ensure_ml_dependencies()

    if arch in ("large", "mobilenet_v3_large", "auto"):
        # 优先尝试 Large
        model = _MOBILENET_FACTORY_LARGE(weights=None)
        model.classifier = torch.nn.Sequential(
            torch.nn.Linear(960, 1280),
            torch.nn.Hardswish(inplace=True),
            torch.nn.Dropout(p=0.3, inplace=True),
            torch.nn.Linear(1280, num_classes),
        )
    else:
        model = _MOBILENET_FACTORY_SMALL(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = torch.nn.Linear(in_features, num_classes)

    return model


def _clean_state_dict(state_dict: Dict[str, object]) -> Dict[str, object]:
    """兼容 DataParallel 等带 module. 前缀的权重文件。"""
    cleaned = {}
    for key, value in state_dict.items():
        cleaned[key.replace("module.", "", 1)] = value
    return cleaned


def load_model(force_reload: bool = False):
    """
    单例加载模型。
    若权重不存在或依赖未安装，则返回 None，由上层决定如何处理。
    """
    global _MODEL, _MODEL_ERROR, _LABEL_MAP, _LABEL_MAP_ZH

    if _MODEL is not None and not force_reload:
        return _MODEL

    _LABEL_MAP, _LABEL_MAP_ZH = _load_label_maps()
    weights_path = _get_weights_path()
    if not weights_path.exists():
        _MODEL = None
        _MODEL_ERROR = FileNotFoundError(f"未找到模型权重文件：{weights_path}")
        return None

    try:
        torch, _ = _ensure_ml_dependencies()
        raw_checkpoint = torch.load(weights_path, map_location="cpu")

        # 从权重文件中读取模型架构信息
        arch = "auto"
        if isinstance(raw_checkpoint, dict):
            arch = raw_checkpoint.get("model_arch", "auto")

        checkpoint = raw_checkpoint
        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            checkpoint = checkpoint["state_dict"]
        if not isinstance(checkpoint, dict):
            raise RuntimeError("模型权重格式不正确，无法加载")

        # 自动检测架构：Large 的 classifier.0 权重形状为 [1280, 960]
        if arch == "auto":
            cls0_shape = checkpoint.get("classifier.0.weight", None)
            if cls0_shape is not None and cls0_shape.shape[0] == 1280:
                arch = "large"
            else:
                arch = "small"

        model = _build_model(len(_LABEL_MAP), arch=arch)
        model.load_state_dict(_clean_state_dict(checkpoint), strict=True)
        model.eval()

        _MODEL = model
        _MODEL_ERROR = None
        return _MODEL
    except Exception as exc:
        _MODEL = None
        _MODEL_ERROR = exc
        return None


def get_model_error() -> Optional[Exception]:
    """获取最近一次模型加载错误。"""
    return _MODEL_ERROR


def is_model_ready() -> bool:
    """判断模型是否已成功加载。"""
    return load_model() is not None


def _build_transform():
    """构建与训练阶段一致的预处理。"""
    _, transforms = _ensure_ml_dependencies()
    input_size = _get_input_size()
    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGE_MEAN, std=IMAGE_STD),
    ])


def predict(image_bytes: bytes) -> dict:
    """
    执行单张图片推理。

    :return: {
        "label": "recyclable",
        "label_zh": "可回收物",
        "confidence": 0.92,
        "top3": [...]
    }
    """
    global _LABEL_MAP, _LABEL_MAP_ZH

    model = load_model()
    if model is None:
        raise RuntimeError(str(_MODEL_ERROR or "AI 模型未就绪"))

    torch, _ = _ensure_ml_dependencies()
    if _LABEL_MAP is None or _LABEL_MAP_ZH is None:
        _LABEL_MAP, _LABEL_MAP_ZH = _load_label_maps()

    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise ValueError("文件内容不是有效图片") from exc

    transform = _build_transform()
    tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=1)[0]

    top_k = min(3, probabilities.shape[0])
    confidence_values, class_indices = torch.topk(probabilities, k=top_k)

    top3: List[dict] = []
    for index, confidence in zip(class_indices.tolist(), confidence_values.tolist()):
        label = _LABEL_MAP[index]
        top3.append({
            "label": label,
            "label_zh": _LABEL_MAP_ZH.get(label, label),
            "confidence": round(float(confidence), 4),
        })

    best = top3[0]
    return {
        "label": best["label"],
        "label_zh": best["label_zh"],
        "confidence": best["confidence"],
        "top3": top3,
    }
