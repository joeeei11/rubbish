"""
配置管理模块
通过 .env 文件注入所有配置项，使用 python-dotenv 加载
"""
import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """基础配置"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 数据库
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/garbage_db"
    )

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # 微信小程序
    WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
    WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")

    # 百度 ASR
    BAIDU_ASR_APP_ID = os.getenv("BAIDU_ASR_APP_ID", "")
    BAIDU_ASR_API_KEY = os.getenv("BAIDU_ASR_API_KEY", "")
    BAIDU_ASR_SECRET_KEY = os.getenv("BAIDU_ASR_SECRET_KEY", "")

    # 腾讯云 COS
    COS_SECRET_ID = os.getenv("COS_SECRET_ID", "")
    COS_SECRET_KEY = os.getenv("COS_SECRET_KEY", "")
    COS_BUCKET = os.getenv("COS_BUCKET", "")
    COS_REGION = os.getenv("COS_REGION", "ap-guangzhou")

    # AI 模型
    MODEL_WEIGHTS_PATH = os.getenv(
        "MODEL_WEIGHTS_PATH",
        "ai_model/weights/mobilenetv3_garbage.pth"
    )
    MODEL_INPUT_SIZE = int(os.getenv("MODEL_INPUT_SIZE", "224"))
    MODEL_CONFIDENCE_THRESHOLD = float(
        os.getenv("MODEL_CONFIDENCE_THRESHOLD", "0.6")
    )

    # 文件上传
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(10 * 1024 * 1024)))  # 默认 10MB

    # JWT 过期时间（秒）
    JWT_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7天


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # True 时会打印所有 SQL，调试 ORM 时可开启


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


# 配置映射，与 FLASK_ENV 对应
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
