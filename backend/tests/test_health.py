"""
健康检查接口测试
验证 GET /api/v1/health 返回正确格式
"""
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app("development")
    app.config["TESTING"] = True
    # 使用 SQLite 内存库避免测试依赖 MySQL
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """健康检查返回 200 和正确结构"""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["code"] == 200
    assert body["data"]["status"] == "ok"
    assert body["data"]["version"] == "1.0.0"
