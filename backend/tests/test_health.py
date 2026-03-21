"""
健康检查接口测试
验证 GET /api/v1/health 返回正确格式
"""
import os
import pytest
from app import create_app


@pytest.fixture
def client():
    previous_database_url = os.environ.get("DATABASE_URL")
    previous_redis_url = os.environ.get("REDIS_URL")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = ""
    app = create_app("development")
    app.config["TESTING"] = True
    # 使用 SQLite 内存库避免测试依赖 MySQL
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        yield client

    if previous_database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = previous_database_url

    if previous_redis_url is None:
        os.environ.pop("REDIS_URL", None)
    else:
        os.environ["REDIS_URL"] = previous_redis_url


def test_health_check(client):
    """健康检查返回 200 和正确结构"""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["code"] == 200
    assert body["data"]["status"] == "ok"
    assert body["data"]["version"] == "1.0.0"
