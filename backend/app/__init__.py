"""
Flask 应用工厂函数
使用工厂模式创建 app 实例，便于测试与多环境配置
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate

from app.config import config_map
from app.models import db


def create_app(env=None):
    """
    创建并配置 Flask 应用实例

    :param env: 环境名称（development / production），默认从 FLASK_ENV 读取
    :return: Flask app 实例
    """
    app = Flask(__name__)

    # ---- 加载配置 ----
    env = env or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_map.get(env, config_map["default"]))

    # ---- 扩展初始化 ----
    db.init_app(app)
    Migrate(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ---- 注册蓝图 ----
    _register_blueprints(app)

    # ---- 全局错误处理 ----
    _register_error_handlers(app)

    # ---- 确保上传目录存在 ----
    upload_dir = os.path.join(app.root_path, "..", app.config.get("UPLOAD_FOLDER", "uploads"))
    os.makedirs(upload_dir, exist_ok=True)

    return app


def _register_blueprints(app):
    """注册所有蓝图"""
    from app.api.health import health_bp
    from app.api.user import user_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(user_bp, url_prefix="/api/v1")


def _register_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"code": 40401, "message": "资源不存在", "data": {}}), 200

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"code": 40501, "message": "请求方法不允许", "data": {}}), 200

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"code": 50001, "message": "服务器内部错误", "data": {}}), 200
