"""
垃圾物品模型
存储具体垃圾条目，支持全文索引搜索
"""
from datetime import datetime
from . import db


class GarbageItem(db.Model):
    __tablename__ = "garbage_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False, comment="物品名称，如：矿泉水瓶")
    alias = db.Column(db.Text, nullable=True, comment="别名列表，逗号分隔，用于全文搜索")
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, comment="所属分类 ID")
    image_url = db.Column(db.String(512), nullable=True, comment="示例图片 URL")
    description = db.Column(db.Text, nullable=True, comment="物品说明")
    tips = db.Column(db.Text, nullable=True, comment="投放小贴士，如：需清洗后投放")
    is_active = db.Column(db.Boolean, default=True, comment="是否启用")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    category = db.relationship("Category", back_populates="items")
    knowledge_relations = db.relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.source_item_id",
        back_populates="source_item",
        lazy="dynamic"
    )
    query_histories = db.relationship("QueryHistory", back_populates="garbage_item", lazy="dynamic")

    # 注意：alias 字段需要在 MySQL 中手动创建 FULLTEXT 索引（见迁移脚本）
    __table_args__ = (
        db.Index("idx_garbage_items_name", "name"),
        # FULLTEXT 索引通过迁移脚本单独执行：
        # ALTER TABLE garbage_items ADD FULLTEXT INDEX ft_alias (name, alias);
    )

    def to_dict(self, include_category=True):
        data = {
            "id": self.id,
            "name": self.name,
            "alias": self.alias,
            "category_id": self.category_id,
            "image_url": self.image_url,
            "description": self.description,
            "tips": self.tips,
        }
        if include_category and self.category:
            data["category"] = self.category.to_dict()
        return data
