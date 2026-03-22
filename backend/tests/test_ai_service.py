"""
Phase 4 AI 图像识别链路测试。
通过 mock 模型推理结果，验证服务编排、接口校验和历史记录写入。
"""
import io
import os
import shutil
import tempfile
from unittest.mock import patch

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

from app import create_app
from app.models import db as _db
from app.models.category import Category
from app.models.garbage_item import GarbageItem
from app.models.query_history import QueryHistory
from app.models.user import User
from app.services.ai_service import classify_image
from app.utils.auth import generate_token


def _make_png_bytes(color=(30, 144, 255)):
    image = Image.new("RGB", (64, 64), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(scope="module")
def app():
    previous_database_url = os.environ.get("DATABASE_URL")
    previous_redis_url = os.environ.get("REDIS_URL")
    previous_upload_folder = os.environ.get("UPLOAD_FOLDER")

    upload_root = tempfile.mkdtemp(prefix="phase4-uploads-")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = ""
    os.environ["UPLOAD_FOLDER"] = upload_root

    application = create_app("development")
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "phase4-test-secret",
        "REDIS_URL": "",
        "UPLOAD_FOLDER": upload_root,
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
            components="PET 塑料",
            reason="材质可回收再生",
            tips="倒空并压扁后投放",
        )
        battery = GarbageItem(
            name="干电池",
            alias="5号电池,7号电池",
            category=hazardous,
            description="常见一次性电池",
            components="锌锰材料",
            reason="含有害化学物质",
            tips="单独投放",
        )
        user = User(openid="phase4-user-openid", nickname="图像测试用户")
        _db.session.add_all([bottle, battery, user])
        _db.session.commit()

        yield application

        _db.drop_all()

    shutil.rmtree(upload_root, ignore_errors=True)

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


@pytest.fixture
def auth_header(app):
    with app.app_context():
        user = User.query.filter_by(openid="phase4-user-openid").first()
        token = generate_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def test_classify_image_returns_matched_item(app):
    with app.app_context():
        file_storage = FileStorage(
            stream=io.BytesIO(_make_png_bytes()),
            filename="矿泉水瓶.png",
            content_type="image/png",
        )
        with patch("app.services.ai_service.predict", return_value={
            "label": "recyclable",
            "label_zh": "可回收物",
            "confidence": 0.91,
            "top3": [
                {"label": "recyclable", "label_zh": "可回收物", "confidence": 0.91},
                {"label": "other", "label_zh": "其他垃圾", "confidence": 0.05},
                {"label": "hazardous", "label_zh": "有害垃圾", "confidence": 0.04},
            ],
        }):
            payload = classify_image(file_storage)

    assert payload["category"] == "可回收物"
    assert payload["itemId"] is not None
    assert payload["matchedItem"]["name"] == "矿泉水瓶"
    assert payload["uncertain"] is False


def test_classify_image_low_confidence_marks_uncertain(app):
    with app.app_context():
        file_storage = FileStorage(
            stream=io.BytesIO(_make_png_bytes(color=(200, 200, 200))),
            filename="模糊样本.png",
            content_type="image/png",
        )
        with patch("app.services.ai_service.predict", return_value={
            "label": "recyclable",
            "label_zh": "可回收物",
            "confidence": 0.42,
            "top3": [
                {"label": "recyclable", "label_zh": "可回收物", "confidence": 0.42},
                {"label": "other", "label_zh": "其他垃圾", "confidence": 0.31},
                {"label": "hazardous", "label_zh": "有害垃圾", "confidence": 0.27},
            ],
        }):
            payload = classify_image(file_storage)

    assert payload["uncertain"] is True
    assert payload["categoryCode"] == "recyclable"
    assert payload["matchedItem"] is not None


def test_classify_image_uses_cache_when_same_image_repeated(app):
    fake_cache = {}

    class FakeRedis:
        def ping(self):
            return True

        def get(self, key):
            return fake_cache.get(key)

        def setex(self, key, ttl, value):
            fake_cache[key] = value

    with app.app_context():
        first_file = FileStorage(
            stream=io.BytesIO(_make_png_bytes(color=(60, 179, 113))),
            filename="矿泉水瓶.png",
            content_type="image/png",
        )
        second_file = FileStorage(
            stream=io.BytesIO(_make_png_bytes(color=(60, 179, 113))),
            filename="矿泉水瓶.png",
            content_type="image/png",
        )

        with patch("app.services.ai_service._get_redis_client", return_value=FakeRedis()), patch(
            "app.services.ai_service.predict",
            return_value={
                "label": "recyclable",
                "label_zh": "可回收物",
                "confidence": 0.95,
                "top3": [
                    {"label": "recyclable", "label_zh": "可回收物", "confidence": 0.95},
                    {"label": "other", "label_zh": "其他垃圾", "confidence": 0.03},
                    {"label": "hazardous", "label_zh": "有害垃圾", "confidence": 0.02},
                ],
            },
        ) as mock_predict:
            first_payload = classify_image(first_file)
            second_payload = classify_image(second_file)

    assert first_payload["cacheHit"] is False
    assert second_payload["cacheHit"] is True
    assert first_payload["category"] == second_payload["category"] == "可回收物"
    assert mock_predict.call_count == 1


def test_image_endpoint_rejects_invalid_extension(client):
    response = client.post(
        "/api/v1/classify/image",
        data={"file": (io.BytesIO(b"plain text"), "note.txt", "text/plain")},
        content_type="multipart/form-data",
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["code"] == 40001
    assert "文件格式不支持" in body["message"]


def test_image_endpoint_rejects_oversized_file(client):
    large_file = io.BytesIO(b"0" * (5 * 1024 * 1024 + 1))
    response = client.post(
        "/api/v1/classify/image",
        data={"file": (large_file, "too-large.png", "image/png")},
        content_type="multipart/form-data",
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["code"] == 40001
    assert "文件大小超限" in body["message"]


def test_image_endpoint_creates_history_when_authenticated(client, app, auth_header):
    with patch("app.services.ai_service.predict", return_value={
        "label": "recyclable",
        "label_zh": "可回收物",
        "confidence": 0.88,
        "top3": [
            {"label": "recyclable", "label_zh": "可回收物", "confidence": 0.88},
            {"label": "other", "label_zh": "其他垃圾", "confidence": 0.08},
            {"label": "hazardous", "label_zh": "有害垃圾", "confidence": 0.04},
        ],
    }):
        response = client.post(
            "/api/v1/classify/image",
            data={"file": (io.BytesIO(_make_png_bytes()), "矿泉水瓶.png", "image/png")},
            headers=auth_header,
            content_type="multipart/form-data",
        )
    body = response.get_json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["category"] == "可回收物"

    with app.app_context():
        history = QueryHistory.query.order_by(QueryHistory.id.desc()).first()
        assert history is not None
        assert history.query_type == "image"
        assert history.query_input == "矿泉水瓶.png"
        assert history.garbage_item_id is not None
