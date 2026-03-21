"""
用户认证模块测试
覆盖：token生成与验证、过期场景、无效token、require_auth装饰器、登录接口
"""
import time
import pytest
from unittest.mock import patch, MagicMock

import jwt

from app import create_app
from app.models import db as _db
from app.utils.auth import generate_token, verify_token, TOKEN_EXPIRE_SECONDS


# ─────────────────────────── Fixtures ───────────────────────────

@pytest.fixture(scope="module")
def app():
    """创建测试用 Flask 应用（SQLite 内存库）"""
    application = create_app("development")
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-for-pytest",
    })
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_header(app):
    """生成有效的 Authorization 头"""
    # 先在数据库中创建用户
    from app.models.user import User
    with app.app_context():
        user = User.query.filter_by(openid="test_openid_fixture").first()
        if user is None:
            user = User(openid="test_openid_fixture", nickname="测试用户")
            _db.session.add(user)
            _db.session.commit()
        token = generate_token(user.id)
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────── Token 单元测试 ─────────────────────────

class TestTokenGeneration:
    def test_generate_returns_string(self, app):
        """generate_token 应返回字符串"""
        with app.app_context():
            token = generate_token(42)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_returns_correct_user_id(self, app):
        """verify_token 应解码出正确的 user_id"""
        with app.app_context():
            token = generate_token(99)
            user_id = verify_token(token)
        assert user_id == 99

    def test_token_contains_exp(self, app):
        """生成的 token payload 应含有 exp 字段"""
        with app.app_context():
            token = generate_token(1)
            payload = jwt.decode(
                token,
                app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        assert "exp" in payload
        assert "user_id" in payload

    def test_expired_token_raises(self, app):
        """过期 token 应抛出 ExpiredSignatureError"""
        with app.app_context():
            # 手动构造一个 exp 在过去的 token
            import jwt as _jwt
            from datetime import datetime, timezone, timedelta
            payload = {
                "user_id": 1,
                "exp": datetime.now(tz=timezone.utc) - timedelta(seconds=10),
            }
            expired_token = _jwt.encode(
                payload, app.config["SECRET_KEY"], algorithm="HS256"
            )
            with pytest.raises(_jwt.ExpiredSignatureError):
                verify_token(expired_token)

    def test_invalid_token_raises(self, app):
        """篡改的 token 应抛出 InvalidTokenError"""
        with app.app_context():
            with pytest.raises(jwt.InvalidTokenError):
                verify_token("invalid.token.value")

    def test_wrong_secret_raises(self, app):
        """使用错误密钥签名的 token 应抛出 InvalidSignatureError"""
        import jwt as _jwt
        from datetime import datetime, timezone, timedelta
        payload = {
            "user_id": 1,
            "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
        }
        bad_token = _jwt.encode(payload, "wrong-secret", algorithm="HS256")
        with app.app_context():
            with pytest.raises(_jwt.InvalidSignatureError):
                verify_token(bad_token)


# ──────────────────────── 登录接口测试 ──────────────────────────

class TestLoginEndpoint:
    def test_missing_code_returns_400(self, client):
        """缺少 code 字段应返回业务错误码 40001"""
        resp = client.post("/api/v1/user/login", json={})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 40001
        assert "code不能为空" in body["message"]

    def test_empty_code_returns_400(self, client):
        """空字符串 code 应返回业务错误码 40001"""
        resp = client.post("/api/v1/user/login", json={"code": "  "})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 40001

    def test_wechat_api_error_returns_43001(self, client):
        """微信 API 返回 errcode 时应返回 43001"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errcode": 40029, "errmsg": "invalid code"}
        mock_resp.raise_for_status = MagicMock()

        with patch("app.api.user.requests.get", return_value=mock_resp):
            resp = client.post("/api/v1/user/login", json={"code": "bad_code"})

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 43001

    def test_successful_login_returns_token(self, client):
        """有效 code 换取 token，首次登录创建用户"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"openid": "wx_openid_new_user_001"}
        mock_resp.raise_for_status = MagicMock()

        with patch("app.api.user.requests.get", return_value=mock_resp):
            resp = client.post("/api/v1/user/login", json={"code": "valid_code_001"})

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 200
        assert "token" in body["data"]
        assert "userInfo" in body["data"]
        assert isinstance(body["data"]["token"], str)
        assert body["data"]["userInfo"]["id"] > 0

    def test_login_twice_same_user(self, client):
        """相同 openid 两次登录应返回同一用户 ID"""
        openid = "wx_openid_repeat_user_001"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"openid": openid}
        mock_resp.raise_for_status = MagicMock()

        with patch("app.api.user.requests.get", return_value=mock_resp):
            resp1 = client.post("/api/v1/user/login", json={"code": "code_a"})
            resp2 = client.post("/api/v1/user/login", json={"code": "code_b"})

        id1 = resp1.get_json()["data"]["userInfo"]["id"]
        id2 = resp2.get_json()["data"]["userInfo"]["id"]
        assert id1 == id2

    def test_requests_exception_returns_43001(self, client):
        """网络异常时应返回 43001"""
        with patch("app.api.user.requests.get", side_effect=Exception("timeout")):
            resp = client.post("/api/v1/user/login", json={"code": "any_code"})

        body = resp.get_json()
        assert body["code"] == 43001


# ────────────────────── profile 接口测试 ──────────────────────────

class TestProfileEndpoint:
    def test_no_token_returns_401(self, client):
        """未携带 token 应返回 40101"""
        resp = client.get("/api/v1/user/profile")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 40101

    def test_invalid_token_returns_401(self, client):
        """无效 token 应返回 40101"""
        resp = client.get(
            "/api/v1/user/profile",
            headers={"Authorization": "Bearer totally.invalid.token"}
        )
        body = resp.get_json()
        assert body["code"] == 40101

    def test_expired_token_returns_40102(self, client, app):
        """过期 token 应返回 40102"""
        import jwt as _jwt
        from datetime import datetime, timezone, timedelta
        payload = {
            "user_id": 9999,
            "exp": datetime.now(tz=timezone.utc) - timedelta(seconds=1),
        }
        expired = _jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

        resp = client.get(
            "/api/v1/user/profile",
            headers={"Authorization": f"Bearer {expired}"}
        )
        body = resp.get_json()
        assert body["code"] == 40102

    def test_valid_token_returns_profile(self, client, auth_header):
        """有效 token 应返回用户信息"""
        resp = client.get("/api/v1/user/profile", headers=auth_header)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 200
        assert "id" in body["data"]
        assert "nickname" in body["data"]
        assert "avatarUrl" in body["data"]
