"""
知识图谱接口
"""
from flask import Blueprint, request

from app.services.search_service import build_knowledge_graph
from app.utils.response import ErrorCode, error, success


knowledge_bp = Blueprint("knowledge", __name__)


@knowledge_bp.get("/knowledge/graph")
def knowledge_graph():
    """获取知识图谱节点和边。"""
    item_id = request.args.get("item_id", type=int)
    if not item_id:
        return error(ErrorCode.PARAM_ERROR, "item_id不能为空")

    payload = build_knowledge_graph(item_id)
    if payload is None:
        return error(ErrorCode.NOT_FOUND, "目标物品不存在")

    return success(payload)
