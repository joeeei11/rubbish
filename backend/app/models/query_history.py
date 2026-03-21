"""
查询历史模型
记录用户每次识别/搜索行为
"""
from datetime import datetime
from . import db


class QueryHistory(db.Model):
    __tablename__ = "query_histories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="用户 ID")
    query_type = db.Column(
        db.Enum("image", "voice", "text"),
        nullable=False,
        comment="查询类型：图像/语音/文字"
    )
    query_input = db.Column(db.String(256), nullable=True, comment="输入内容（文字搜索词或语音识别结果）")
    garbage_item_id = db.Column(db.Integer, db.ForeignKey("garbage_items.id"), nullable=True, comment="识别结果物品 ID")
    confidence = db.Column(db.Float, nullable=True, comment="AI 识别置信度（仅图像识别有效）")
    image_url = db.Column(db.String(512), nullable=True, comment="上传图片 URL（仅图像识别有效）")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="查询时间")

    # 关联关系
    user = db.relationship("User", back_populates="histories")
    garbage_item = db.relationship("GarbageItem", back_populates="query_histories")

    def to_dict(self):
        return {
            "id": self.id,
            "query_type": self.query_type,
            "query_input": self.query_input,
            "garbage_item": self.garbage_item.to_dict() if self.garbage_item else None,
            "confidence": self.confidence,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
