"""
科普文章模型
存储垃圾分类相关科普内容
"""
from datetime import datetime
from . import db


class Article(db.Model):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(128), nullable=False, comment="文章标题")
    summary = db.Column(db.String(256), nullable=True, comment="文章摘要")
    content = db.Column(db.Text, nullable=False, comment="文章正文（支持 Markdown）")
    cover_image = db.Column(db.String(512), nullable=True, comment="封面图片 URL")
    category_tag = db.Column(db.String(32), nullable=True, comment="关联分类标签，如：recyclable")
    view_count = db.Column(db.Integer, default=0, comment="阅读次数")
    is_published = db.Column(db.Boolean, default=True, comment="是否发布")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    def to_dict(self, include_content=False):
        data = {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "cover_image": self.cover_image,
            "category_tag": self.category_tag,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_content:
            data["content"] = self.content
        return data
