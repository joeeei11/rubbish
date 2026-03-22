"""
Phase 6 集成测试。
覆盖登录、搜索、详情、图谱、图像识别与历史记录主链路。
"""
import io
import os
from unittest.mock import patch

import pytest
from PIL import Image

from app import create_app
from app.models import db as _db
from app.models.article import Article
from app.models.category import Category
from app.models.garbage_item import GarbageItem
from app.models.knowledge_relation import KnowledgeRelation


def _make_png_bytes(color=(52, 211, 153)):
    image = Image.new("RGB", (64, 64), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(scope="module")
def app():
    previous_database_url = os.environ.get("DATABASE_URL")
    previous_redis_url = os.environ.get("REDIS_URL")
    previous_upload_folder = os.environ.get("UPLOAD_FOLDER")

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = ""
    os.environ["UPLOAD_FOLDER"] = "integration-uploads"

    application = create_app("development")
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "integration-test-secret",
        "REDIS_URL": "",
        "UPLOAD_FOLDER": "integration-uploads",
    })

    with application.app_context():
        _db.create_all()

        recyclable = Category(name="可回收物", code="recyclable", color="#4CAF50")
        hazardous = Category(name="有害垃圾", code="hazardous", color="#F44336")
        kitchen = Category(name="厨余垃圾", code="kitchen", color="#FF9800")
        other = Category(name="其他垃圾", code="other", color="#9E9E9E")
        _db.session.add_all([recyclable, hazardous, kitchen, other])
        _db.session.flush()

        bottle = GarbageItem(
            name="矿泉水瓶",
            alias="饮料瓶,塑料瓶",
            category=recyclable,
            description="常见塑料饮料瓶",
            components="PET塑料",
            reason="材质可回收再生",
            tips="倒空后投放",
        )
        cola_bottle = GarbageItem(
            name="可乐瓶",
            alias="饮料瓶",
            category=recyclable,
            description="含糖饮料瓶",
            components="PET塑料",
            reason="清洁后可回收",
            tips="压扁后投放",
        )
        battery = GarbageItem(
            name="干电池",
            alias="5号电池,7号电池",
            category=hazardous,
            description="常见一次性电池",
            components="锌锰、碱性电解液",
            reason="含有害化学物质",
            tips="单独投放",
        )
        _db.session.add_all([bottle, cola_bottle, battery])
        _db.session.flush()

        _db.session.add(
            KnowledgeRelation(
                source_item_id=bottle.id,
                target_item_id=cola_bottle.id,
                relation_type="similar_to",
                description="同属塑料饮料瓶",
            )
        )
        _db.session.add(
            Article(
                title="矿泉水瓶为什么属于可回收物",
                summary="解释矿泉水瓶的回收逻辑。",
                content="PET 材料可以回收再利用。",
                category_tag="recyclable",
            )
        )
        _db.session.commit()

        yield application
        _db.drop_all()

    if previous_database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = previous_database_url

    if previous_redis_url is None:
        os.environ.pop("REDIS_URL", None)
    else:
        os.environ["REDIS_URL"] = previous_redis_url

    if previous_upload_folder is None:
        os.environ.pop("UPLOAD_FOLDER", None)
    else:
        os.environ["UPLOAD_FOLDER"] = previous_upload_folder


@pytest.fixture
def client(app):
    return app.test_client()


def test_history_endpoint_requires_auth(client):
    response = client.get("/api/v1/history?page=1&size=20")
    body = response.get_json()

    assert response.status_code == 200
    assert body["code"] == 40101


def test_login_search_detail_graph_history_and_image_flow(client):
    with patch("app.api.user._code2session", return_value={"openid": "integration-openid"}):
        login_resp = client.post("/api/v1/user/login", json={"code": "mock-code"})
    login_body = login_resp.get_json()

    assert login_body["code"] == 200
    token = login_body["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    search_resp = client.get("/api/v1/classify/search?q=矿泉水瓶&page=1&size=10", headers=headers)
    search_body = search_resp.get_json()
    assert search_body["code"] == 200
    assert search_body["data"]["list"][0]["name"] == "矿泉水瓶"
    item_id = search_body["data"]["list"][0]["id"]

    detail_resp = client.get(f"/api/v1/garbage/{item_id}")
    detail_body = detail_resp.get_json()
    assert detail_body["code"] == 200
    assert detail_body["data"]["name"] == "矿泉水瓶"

    graph_resp = client.get(f"/api/v1/knowledge/graph?item_id={item_id}")
    graph_body = graph_resp.get_json()
    assert graph_body["code"] == 200
    assert graph_body["data"]["centerItemId"] == item_id

    with patch("app.services.ai_service.predict", return_value={
        "label": "recyclable",
        "label_zh": "可回收物",
        "confidence": 0.93,
        "top3": [
            {"label": "recyclable", "label_zh": "可回收物", "confidence": 0.93},
            {"label": "other", "label_zh": "其他垃圾", "confidence": 0.05},
            {"label": "hazardous", "label_zh": "有害垃圾", "confidence": 0.02},
        ],
    }):
        image_resp = client.post(
            "/api/v1/classify/image",
            data={"file": (io.BytesIO(_make_png_bytes()), "矿泉水瓶.png", "image/png")},
            headers=headers,
            content_type="multipart/form-data",
        )
    image_body = image_resp.get_json()
    assert image_body["code"] == 200
    assert image_body["data"]["category"] == "可回收物"

    history_resp = client.get("/api/v1/history?page=1&size=20", headers=headers)
    history_body = history_resp.get_json()
    assert history_body["code"] == 200
    assert history_body["data"]["pagination"]["total"] >= 2

    history_types = [item["queryType"] for item in history_body["data"]["list"]]
    assert "text" in history_types
    assert "image" in history_types


def test_search_returns_empty_list_for_missing_keyword(client):
    response = client.get("/api/v1/classify/search?q=完全不存在的垃圾&page=1&size=10")
    body = response.get_json()

    assert body["code"] == 200
    assert body["data"]["list"] == []


def test_garbage_detail_returns_not_found_for_invalid_id(client):
    response = client.get("/api/v1/garbage/99999")
    body = response.get_json()

    assert body["code"] == 40401
