"""
查询历史接口。
"""
from flask import Blueprint, g, request
from sqlalchemy.orm import joinedload

from app.models.garbage_item import GarbageItem
from app.models.query_history import QueryHistory
from app.models.user import User
from app.utils.auth import require_auth
from app.utils.response import success


history_bp = Blueprint("history", __name__)


def _serialize_history(history: QueryHistory) -> dict:
    """序列化历史记录，补充物品与分类信息。"""
    garbage_item = history.garbage_item
    garbage_item_payload = None
    if garbage_item is not None:
        garbage_item_payload = garbage_item.to_dict(include_category=True)

    return {
        "id": history.id,
        "queryType": history.query_type,
        "queryInput": history.query_input,
        "confidence": history.confidence,
        "imageUrl": history.image_url,
        "garbageItem": garbage_item_payload,
        "createdAt": history.created_at.isoformat() if history.created_at else None,
    }


@history_bp.get("/history")
@require_auth
def list_history():
    """分页获取当前用户的查询历史。"""
    user: User = g.current_user
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    size = request.args.get("size", 20, type=int) or 20
    size = max(min(size, 50), 1)

    query = (
        QueryHistory.query
        .options(joinedload(QueryHistory.garbage_item).joinedload(GarbageItem.category))
        .filter_by(user_id=user.id)
        .order_by(QueryHistory.created_at.desc(), QueryHistory.id.desc())
    )

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    return success({
        "list": [_serialize_history(item) for item in items],
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "hasMore": page * size < total,
        },
    })
