"""
垃圾物品详情接口
"""
from flask import Blueprint

from app.services.search_service import get_item_by_id
from app.utils.response import ErrorCode, error, success


garbage_bp = Blueprint("garbage", __name__)


@garbage_bp.get("/garbage/<int:item_id>")
def garbage_detail(item_id):
    """获取垃圾物品详情。"""
    payload = get_item_by_id(item_id)
    if payload is None:
        return error(ErrorCode.NOT_FOUND, "垃圾物品不存在")

    return success(payload)
