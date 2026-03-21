"""
用户模块 Blueprint
POST /api/v1/user/login   — 微信登录，返回 JWT
GET  /api/v1/user/profile — 获取当前用户信息（需鉴权）
"""
import os
import requests
from flask import Blueprint, request, g
from datetime import datetime, timezone

from app.models import db
from app.models.user import User
from app.utils.auth import generate_token, require_auth
from app.utils.response import success, error, ErrorCode

user_bp = Blueprint("user", __name__)

# 微信 code2session 接口地址
WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


def _code2session(code: str) -> dict:
    """
    调用微信 code2session 接口获取 openid
    返回：{"openid": "xxx", "session_key": "xxx"} 或含 errcode 的错误字典
    """
    params = {
        "appid": os.getenv("WECHAT_APP_ID", ""),
        "secret": os.getenv("WECHAT_APP_SECRET", ""),
        "js_code": code,
        "grant_type": "authorization_code",
    }
    resp = requests.get(WECHAT_CODE2SESSION_URL, params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()


@user_bp.post("/user/login")
def login():
    """
    微信登录接口
    请求体：{"code": "wx_code_string"}
    响应：{"token": "jwt_string", "userInfo": {"id", "nickname", "avatarUrl"}}
    """
    body = request.get_json(silent=True) or {}
    code = (body.get("code") or "").strip()

    if not code:
        return error(ErrorCode.PARAM_ERROR, "code不能为空")

    # 调用微信 code2session
    try:
        wx_data = _code2session(code)
    except Exception as exc:
        return error(ErrorCode.WECHAT_AUTH_FAILED, f"微信服务请求失败：{exc}")

    if "errcode" in wx_data and wx_data["errcode"] != 0:
        return error(
            ErrorCode.WECHAT_AUTH_FAILED,
            f"微信授权失败：{wx_data.get('errmsg', '未知错误')}"
        )

    openid = wx_data.get("openid")
    if not openid:
        return error(ErrorCode.WECHAT_AUTH_FAILED, "获取 openid 失败")

    # 查找或创建用户
    user = User.query.filter_by(openid=openid).first()
    if user is None:
        user = User(openid=openid)
        db.session.add(user)

    user.last_login_at = datetime.now(tz=timezone.utc)
    db.session.commit()

    token = generate_token(user.id)

    return success({
        "token": token,
        "userInfo": {
            "id": user.id,
            "nickname": user.nickname or "",
            "avatarUrl": user.avatar_url or "",
        }
    })


@user_bp.get("/user/profile")
@require_auth
def profile():
    """
    获取当前用户信息（需 JWT 鉴权）
    响应：{"id", "nickname", "avatarUrl", "createdAt"}
    """
    user: User = g.current_user
    return success({
        "id": user.id,
        "nickname": user.nickname or "",
        "avatarUrl": user.avatar_url or "",
        "createdAt": user.created_at.isoformat() if user.created_at else None,
    })
