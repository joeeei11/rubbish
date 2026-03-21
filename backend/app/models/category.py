"""
垃圾分类类别模型
对应四大分类：可回收物、有害垃圾、厨余垃圾、其他垃圾
"""
from . import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), unique=True, nullable=False, comment="分类名称，如：可回收物")
    code = db.Column(db.String(16), unique=True, nullable=False, comment="分类代码，如：recyclable")
    color = db.Column(db.String(16), nullable=True, comment="前端展示颜色，如：#4CAF50")
    icon = db.Column(db.String(128), nullable=True, comment="图标路径或 URL")
    description = db.Column(db.Text, nullable=True, comment="分类说明")
    disposal_guide = db.Column(db.Text, nullable=True, comment="投放指南")

    # 关联关系
    items = db.relationship("GarbageItem", back_populates="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
            "disposal_guide": self.disposal_guide,
        }
