"""
分类模块接口。
当前阶段同时提供文字搜索与图像识别接口。
"""
from __future__ import annotations

import os

import jwt
from flask import Blueprint, request

from app.models import db
from app.models.query_history import QueryHistory
from app.models.user import User
from app.services.asr_service import ASRException, recognize_audio
from app.services.ai_service import ALLOWED_IMAGE_EXTENSIONS, classify_image
from app.services.search_service import search_by_keyword
from app.utils.auth import verify_token
from app.utils.response import ErrorCode, error, success


classify_bp = Blueprint("classify", __name__)
MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_AUDIO_SIZE = 2 * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {"pcm"}


@classify_bp.get("/classify/search")
def classify_search():
    """文字搜索接口。"""
    keyword = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1)
    size = request.args.get("size", 10)

    if not keyword:
        return error(ErrorCode.PARAM_ERROR, "搜索关键词不能为空")

    payload = search_by_keyword(keyword, page, size)
    results = payload.get("list", [])
    first_item_id = results[0].get("id") if results else None

    _save_query_history(
        _get_optional_user(),
        "text",
        keyword,
        garbage_item_id=first_item_id,
    )
    return success(payload)


def _get_file_size(file_storage) -> int:
    """读取上传文件大小。"""
    current_position = file_storage.stream.tell()
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(current_position)
    return size


def _get_optional_user():
    """从 Authorization 头中提取当前用户，失败时静默返回 None。"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[len("Bearer "):]
    try:
        user_id = verify_token(token)
    except jwt.InvalidTokenError:
        return None

    return db.session.get(User, user_id)


def _save_query_history(user, query_type: str, query_input: str, **extra_fields):
    """在已登录场景下记录查询历史。"""
    if user is None:
        return

    history = QueryHistory(
        user_id=user.id,
        query_type=query_type,
        query_input=query_input,
        garbage_item_id=extra_fields.get("garbage_item_id"),
        confidence=extra_fields.get("confidence"),
        image_url=extra_fields.get("image_url"),
    )
    db.session.add(history)
    db.session.commit()


@classify_bp.post("/classify/image")
def classify_image_endpoint():
    """图像识别接口。"""
    file_storage = request.files.get("file")
    if file_storage is None or not file_storage.filename:
        return error(ErrorCode.PARAM_ERROR, "请上传图片文件")

    extension = os.path.splitext(file_storage.filename)[1].lower().lstrip(".")
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return error(ErrorCode.PARAM_ERROR, "文件格式不支持")

    if file_storage.mimetype and not file_storage.mimetype.startswith("image/"):
        return error(ErrorCode.PARAM_ERROR, "文件格式不支持")

    if _get_file_size(file_storage) > MAX_IMAGE_SIZE:
        return error(ErrorCode.PARAM_ERROR, "文件大小超限")

    try:
        payload = classify_image(file_storage)
    except ValueError as exc:
        return error(ErrorCode.PARAM_ERROR, str(exc))
    except RuntimeError as exc:
        return error(ErrorCode.CLASSIFY_FAILED, str(exc))
    except Exception:
        return error(ErrorCode.CLASSIFY_FAILED, "图像识别失败，请稍后重试")

    _save_query_history(
        _get_optional_user(),
        "image",
        file_storage.filename,
        garbage_item_id=payload.get("itemId"),
        confidence=payload.get("confidence"),
        image_url=payload.get("imageUrl"),
    )
    return success(payload)


@classify_bp.post("/classify/voice")
def classify_voice_endpoint():
    """语音识别并转文字搜索接口。"""
    file_storage = request.files.get("audio")
    if file_storage is None or not file_storage.filename:
        return error(ErrorCode.PARAM_ERROR, "请上传音频文件")

    extension = os.path.splitext(file_storage.filename)[1].lower().lstrip(".")
    if extension and extension not in ALLOWED_AUDIO_EXTENSIONS:
        return error(ErrorCode.PARAM_ERROR, "仅支持 PCM 音频格式")

    if _get_file_size(file_storage) > MAX_AUDIO_SIZE:
        return error(ErrorCode.PARAM_ERROR, "音频文件大小超限")

    audio_bytes = file_storage.read()
    file_storage.stream.seek(0)

    try:
        recognized_text = recognize_audio(audio_bytes, audio_format=extension or "pcm")
    except ASRException:
        return error(ErrorCode.ASR_FAILED, "语音识别失败，请重试或使用文字搜索")
    except Exception:
        return error(ErrorCode.ASR_FAILED, "语音识别失败，请重试或使用文字搜索")

    search_payload = search_by_keyword(recognized_text, 1, 10)
    results = search_payload.get("list", [])
    first_item_id = results[0].get("id") if results else None

    _save_query_history(
        _get_optional_user(),
        "voice",
        recognized_text,
        garbage_item_id=first_item_id,
    )

    return success({
        "recognized_text": recognized_text,
        "results": results,
        "pagination": search_payload.get("pagination", {}),
    })
