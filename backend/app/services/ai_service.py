"""
AI 图像识别服务。
负责图片读取、模型推理、知识库物品匹配与结果组装。
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import redis
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from ai_model.model import get_model_error, predict
from app.models.category import Category
from app.models.garbage_item import GarbageItem
from app.services.search_service import get_item_by_id, search_by_keyword


ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
IMAGE_CACHE_TTL_SECONDS = 3600


def _normalize_filename(filename: str) -> str:
    """提取文件名主体，便于做回退匹配。"""
    return Path(filename or "").stem.strip()


def _guess_prediction_from_filename(filename: str) -> dict | None:
    """
    当模型权重未就绪时，基于文件名做开发期兜底。
    该逻辑不替代真实模型，仅用于保障本地联调可继续进行。
    """
    keyword = _normalize_filename(filename)
    if not keyword:
        return None

    payload = search_by_keyword(keyword, 1, 5)
    items = payload.get("list", [])
    if not items:
        return None

    best_item = items[0]
    category = best_item.get("category") or {}
    label = category.get("code")
    label_zh = category.get("name")
    if not label or not label_zh:
        return None

    confidence = 0.78 if best_item.get("name") == keyword else 0.68
    top3 = []
    used_codes = set()
    for item in items:
        item_category = item.get("category") or {}
        code = item_category.get("code")
        name = item_category.get("name")
        if not code or code in used_codes:
            continue
        used_codes.add(code)
        score = confidence if code == label else max(0.41, confidence - len(top3) * 0.12)
        top3.append({
            "label": code,
            "label_zh": name,
            "confidence": round(score, 4),
        })
        if len(top3) >= 3:
            break

    return {
        "label": label,
        "label_zh": label_zh,
        "confidence": round(confidence, 4),
        "top3": top3,
        "fallback_item_id": best_item.get("id"),
        "prediction_source": "filename-fallback",
    }


def _save_uploaded_image(image_bytes: bytes, filename: str) -> str:
    """将上传图片保存到本地上传目录，并返回相对路径。"""
    from flask import current_app

    extension = Path(filename or "").suffix.lower().lstrip(".")
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        extension = "jpg"

    upload_root = Path(current_app.root_path).parent / current_app.config.get("UPLOAD_FOLDER", "uploads")
    image_dir = upload_root / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(filename or "") or f"image.{extension}"
    target_name = f"{uuid.uuid4().hex}_{safe_name}"
    target_path = image_dir / target_name
    target_path.write_bytes(image_bytes)
    return f"/uploads/images/{target_name}"


def _get_redis_client():
    """获取 Redis 客户端，连接失败时返回 None。"""
    from flask import current_app

    redis_url = current_app.config.get("REDIS_URL", "").strip()
    if not redis_url:
        return None

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def _build_image_cache_key(image_bytes: bytes) -> str:
    """基于图片内容构建缓存键。"""
    return f"image-classify:{hashlib.md5(image_bytes).hexdigest()}"


def _get_cached_result(cache_key: str) -> dict | None:
    """读取图像识别缓存。"""
    client = _get_redis_client()
    if client is None:
        return None

    try:
        payload = client.get(cache_key)
        return json.loads(payload) if payload else None
    except Exception:
        return None


def _set_cached_result(cache_key: str, payload: dict):
    """写入图像识别缓存。"""
    client = _get_redis_client()
    if client is None:
        return

    try:
        client.setex(cache_key, IMAGE_CACHE_TTL_SECONDS, json.dumps(payload, ensure_ascii=False))
    except Exception:
        return


def _find_item_by_filename(category_id: int | None, filename: str) -> GarbageItem | None:
    """尝试依据文件名在当前分类下匹配更具体的物品。"""
    keyword = _normalize_filename(filename)
    if not keyword:
        return None

    payload = search_by_keyword(keyword, 1, 10)
    for item in payload.get("list", []):
        category = item.get("category") or {}
        if category_id and category.get("id") != category_id:
            continue
        item_id = item.get("id")
        if item_id:
            return (
                GarbageItem.query
                .options(joinedload(GarbageItem.category))
                .filter_by(id=item_id, is_active=True)
                .first()
            )
    return None


def _find_default_item_by_category(category_id: int | None) -> GarbageItem | None:
    """按分类选择一个代表性物品，便于结果页联动显示。"""
    if not category_id:
        return None

    return (
        GarbageItem.query
        .options(joinedload(GarbageItem.category))
        .filter_by(category_id=category_id, is_active=True)
        .order_by(GarbageItem.id.asc())
        .first()
    )


def _get_category_suggestions(category_id: int | None, exclude_item_id: int | None = None, limit: int = 5):
    """返回同分类下的候选物品，用于低置信度提示。"""
    if not category_id:
        return []

    query = (
        GarbageItem.query
        .options(joinedload(GarbageItem.category))
        .filter_by(category_id=category_id, is_active=True)
        .order_by(GarbageItem.id.asc())
    )
    if exclude_item_id:
        query = query.filter(GarbageItem.id != exclude_item_id)
    return [item.to_dict(include_category=True) for item in query.limit(limit).all()]


def classify_image(file_storage) -> dict:
    """
    执行图像分类，并拼装知识库联动结果。
    """
    from flask import current_app

    if file_storage is None or not file_storage.filename:
        raise ValueError("请上传图片文件")

    image_bytes = file_storage.read()
    file_storage.stream.seek(0)
    if not image_bytes:
        raise ValueError("上传文件为空")

    image_url = _save_uploaded_image(image_bytes, file_storage.filename)
    cache_key = _build_image_cache_key(image_bytes)
    cached_payload = _get_cached_result(cache_key)
    if cached_payload is not None:
        return {
            **cached_payload,
            "imageUrl": image_url,
            "cacheHit": True,
        }

    try:
        prediction = predict(image_bytes)
        prediction_source = "model"
    except RuntimeError as exc:
        fallback_prediction = _guess_prediction_from_filename(file_storage.filename)
        if fallback_prediction is None:
            model_error = get_model_error()
            reason = str(model_error or exc)
            raise RuntimeError(f"AI 模型暂不可用：{reason}") from exc
        prediction = fallback_prediction
        prediction_source = fallback_prediction.get("prediction_source", "filename-fallback")

    category = Category.query.filter_by(code=prediction["label"]).first()
    category_id = category.id if category else None

    matched_item = _find_item_by_filename(category_id, file_storage.filename)
    if matched_item is None and prediction.get("fallback_item_id"):
        matched_item = (
            GarbageItem.query
            .options(joinedload(GarbageItem.category))
            .filter_by(id=prediction["fallback_item_id"], is_active=True)
            .first()
        )
    # 仅当文件名回退模式时才用默认物品填充；
    # 模型预测模式下不强制匹配具体物品，避免误导用户
    if matched_item is None and prediction_source != "model":
        matched_item = _find_default_item_by_category(category_id)

    item_payload = get_item_by_id(matched_item.id) if matched_item else None
    threshold = float(current_app.config.get("MODEL_CONFIDENCE_THRESHOLD", 0.6))
    is_uncertain = float(prediction["confidence"]) < threshold

    related_items = []
    if item_payload:
        related_items = item_payload.get("relatedItems", [])
        if not related_items and matched_item:
            related_items = _get_category_suggestions(category_id, exclude_item_id=matched_item.id)
    else:
        # 模型预测模式：展示同分类下的常见物品作为参考
        related_items = _get_category_suggestions(category_id, limit=8)

    payload = {
        "category": category.name if category else prediction["label_zh"],
        "categoryCode": prediction["label"],
        "categoryDescription": category.description if category else "",
        "disposalGuide": category.disposal_guide if category else "",
        "label": prediction["label"],
        "labelZh": prediction["label_zh"],
        "confidence": round(float(prediction["confidence"]), 4),
        "uncertain": is_uncertain,
        "top3": prediction.get("top3", []),
        "itemId": item_payload["id"] if item_payload else None,
        "matchedItem": item_payload,
        "relatedItems": related_items,
        "imageUrl": image_url,
        "predictionSource": prediction_source,
        "cacheHit": False,
    }
    _set_cached_result(cache_key, payload)
    return payload
