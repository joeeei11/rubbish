"""
分类模块接口
当前阶段先实现文字搜索接口
"""
from flask import Blueprint, request

from app.services.search_service import search_by_keyword
from app.utils.response import ErrorCode, error, success


classify_bp = Blueprint("classify", __name__)


@classify_bp.get("/classify/search")
def classify_search():
    """文字搜索接口。"""
    keyword = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1)
    size = request.args.get("size", 10)

    if not keyword:
        return error(ErrorCode.PARAM_ERROR, "搜索关键词不能为空")

    return success(search_by_keyword(keyword, page, size))
