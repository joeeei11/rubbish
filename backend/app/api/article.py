"""
科普文章接口
"""
from flask import Blueprint, request

from app.services.search_service import get_article_by_id, list_articles
from app.utils.response import ErrorCode, error, success


article_bp = Blueprint("article", __name__)


@article_bp.get("/articles")
def article_list():
    """获取文章列表。"""
    page = request.args.get("page", 1)
    size = request.args.get("size", 10)
    return success(list_articles(page, size))


@article_bp.get("/articles/<int:article_id>")
def article_detail(article_id):
    """获取文章详情。"""
    payload = get_article_by_id(article_id)
    if payload is None:
        return error(ErrorCode.NOT_FOUND, "文章不存在")

    return success(payload)
