"""
JWT 认证工具
提供 token 生成、验证及 require_auth 装饰器
"""
import functools
import os
from datetime import datetime, timezone, timedelta

import jwt
from flask import g, request

from app.utils.response import error, ErrorCode

# JWT 有效期（秒）
TOKEN_EXPIRE_SECONDS = 7200


def _get_secret() -> str:
    """从环境变量获取 JWT 密钥"""
    secret = os.getenv("SECRET_KEY", "dev-secret-please-change-in-production")
    return secret


def generate_token(user_id: int) -> str:
    """
    生成 JWT token

    :param user_id: 用户 ID
    :return: JWT 字符串
    """
    now = datetime.now(tz=timezone.utc)
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=TOKEN_EXPIRE_SECONDS),
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def verify_token(token: str) -> int:
    """
    验证 JWT token 并返回 user_id

    :param token: JWT 字符串
    :return: user_id（int）
    :raises jwt.ExpiredSignatureError: token 已过期
    :raises jwt.InvalidTokenError: token 无效
    """
    payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
    return int(payload["user_id"])


def require_auth(func):
    """
    登录鉴权装饰器
    从 Authorization: Bearer <token> 头中提取并验证 token，
    验证通过后将 User 对象注入 g.current_user
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error(ErrorCode.UNAUTHORIZED, "缺少认证 token")

        token = auth_header[len("Bearer "):]
        try:
            user_id = verify_token(token)
        except jwt.ExpiredSignatureError:
            return error(ErrorCode.TOKEN_EXPIRED, "token 已过期，请重新登录")
        except jwt.InvalidTokenError:
            return error(ErrorCode.UNAUTHORIZED, "token 无效")

        # 延迟导入，避免循环依赖
        from app.models.user import User
        user = User.query.get(user_id)
        if user is None:
            return error(ErrorCode.UNAUTHORIZED, "用户不存在")

        g.current_user = user
        return func(*args, **kwargs)

    return wrapper
