"""
用户模型
存储微信用户基本信息与登录凭证
"""
from datetime import datetime
from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    openid = db.Column(db.String(64), unique=True, nullable=False, comment="微信 openid")
    nickname = db.Column(db.String(64), nullable=True, comment="用户昵称")
    avatar_url = db.Column(db.String(512), nullable=True, comment="头像 URL")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="注册时间")
    last_login_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最后登录时间")

    # 关联关系
    histories = db.relationship("QueryHistory", back_populates="user", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
