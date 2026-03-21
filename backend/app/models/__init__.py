"""
数据库实例
在此统一创建 db 对象，避免循环导入
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入所有模型，确保 Flask-Migrate 能检测到所有表
from .user import User              # noqa: F401, E402
from .category import Category      # noqa: F401, E402
from .garbage_item import GarbageItem  # noqa: F401, E402
from .knowledge_relation import KnowledgeRelation  # noqa: F401, E402
from .query_history import QueryHistory  # noqa: F401, E402
from .article import Article        # noqa: F401, E402
