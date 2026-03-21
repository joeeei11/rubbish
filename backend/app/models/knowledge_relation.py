"""
知识关系模型
存储垃圾物品之间的关联关系，用于知识图谱可视化
"""
from . import db


class KnowledgeRelation(db.Model):
    __tablename__ = "knowledge_relations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_item_id = db.Column(
        db.Integer,
        db.ForeignKey("garbage_items.id"),
        nullable=False,
        comment="源节点物品 ID"
    )
    target_item_id = db.Column(
        db.Integer,
        db.ForeignKey("garbage_items.id"),
        nullable=False,
        comment="目标节点物品 ID"
    )
    relation_type = db.Column(
        db.String(32),
        nullable=False,
        comment="关系类型，如：contains（包含）/ similar（相似）/ derived_from（来源）"
    )
    description = db.Column(db.String(256), nullable=True, comment="关系说明")

    # 关联关系
    source_item = db.relationship(
        "GarbageItem",
        foreign_keys=[source_item_id],
        back_populates="knowledge_relations"
    )
    target_item = db.relationship(
        "GarbageItem",
        foreign_keys=[target_item_id]
    )

    def to_dict(self):
        return {
            "id": self.id,
            "source_item_id": self.source_item_id,
            "target_item_id": self.target_item_id,
            "relation_type": self.relation_type,
            "description": self.description,
        }
