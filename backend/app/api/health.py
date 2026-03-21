"""
健康检查接口
GET /api/v1/health
"""
from flask import Blueprint
from app.utils.response import success

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """健康检查，供运维和前端验证服务状态"""
    return success(data={"status": "ok", "version": "1.0.0"})
