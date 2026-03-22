"""
Phase 5 语音识别链路测试。
覆盖百度 ASR 服务封装、语音分类接口与历史记录写入。
"""
import io
import os
from unittest.mock import Mock, patch

import pytest

from app import create_app
from app.models import db as _db
from app.models.category import Category
from app.models.garbage_item import GarbageItem
from app.models.query_history import QueryHistory
from app.models.user import User
from app.services.asr_service import ASRException, recognize_audio
from app.utils.auth import generate_token


@pytest.fixture(scope="module")
def app():
    previous_database_url = os.environ.get("DATABASE_URL")
    previous_redis_url = os.environ.get("REDIS_URL")
    previous_app_id = os.environ.get("BAIDU_ASR_APP_ID")
    previous_api_key = os.environ.get("BAIDU_ASR_API_KEY")
    previous_secret_key = os.environ.get("BAIDU_ASR_SECRET_KEY")

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = ""
    os.environ["BAIDU_ASR_APP_ID"] = "test-app-id"
    os.environ["BAIDU_ASR_API_KEY"] = "test-api-key"
    os.environ["BAIDU_ASR_SECRET_KEY"] = "test-secret-key"

    application = create_app("development")
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "phase5-test-secret",
        "REDIS_URL": "",
        "BAIDU_ASR_APP_ID": "test-app-id",
        "BAIDU_ASR_API_KEY": "test-api-key",
        "BAIDU_ASR_SECRET_KEY": "test-secret-key",
    })

    with application.app_context():
        _db.create_all()

        recyclable = Category(name="可回收物", code="recyclable", color="#4CAF50")
        hazardous = Category(name="有害垃圾", code="hazardous", color="#F44336")
        kitchen = Category(name="厨余垃圾", code="kitchen", color="#FF9800")
        other = Category(name="其他垃圾", code="other", color="#9E9E9E")
        _db.session.add_all([recyclable, hazardous, kitchen, other])
        _db.session.flush()

        _db.session.add_all([
            GarbageItem(
                name="矿泉水瓶",
                alias="饮料瓶,塑料瓶",
                category=recyclable,
                description="常见塑料饮料瓶",
                components="PET塑料",
                reason="材质可回收再生",
                tips="倒空后投放",
            ),
            GarbageItem(
                name="干电池",
                alias="5号电池,7号电池",
                category=hazardous,
                description="常见一次性电池",
                components="锌锰、碱性电解液",
                reason="含有害化学物质",
                tips="单独投放",
            ),
            User(openid="phase5-user-openid", nickname="语音测试用户"),
        ])
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

    if previous_app_id is None:
        os.environ.pop("BAIDU_ASR_APP_ID", None)
    else:
        os.environ["BAIDU_ASR_APP_ID"] = previous_app_id

    if previous_api_key is None:
        os.environ.pop("BAIDU_ASR_API_KEY", None)
    else:
        os.environ["BAIDU_ASR_API_KEY"] = previous_api_key

    if previous_secret_key is None:
        os.environ.pop("BAIDU_ASR_SECRET_KEY", None)
    else:
        os.environ["BAIDU_ASR_SECRET_KEY"] = previous_secret_key


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_header(app):
    with app.app_context():
        user = User.query.filter_by(openid="phase5-user-openid").first()
        token = generate_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def test_recognize_audio_returns_text(app):
    mock_client = Mock()
    mock_client.asr.return_value = {
        "err_no": 0,
        "result": ["矿泉水瓶。"],
    }

    with app.app_context(), patch("app.services.asr_service.get_asr_client", return_value=mock_client):
        result = recognize_audio(b"pcm-audio", "pcm")

    assert result == "矿泉水瓶"


def test_recognize_audio_raises_on_failed_response(app):
    mock_client = Mock()
    mock_client.asr.return_value = {
        "err_no": 3301,
        "err_msg": "speech quality error.",
        "result": [],
    }

    with app.app_context(), patch("app.services.asr_service.get_asr_client", return_value=mock_client):
        with pytest.raises(ASRException) as exc_info:
            recognize_audio(b"bad-audio", "pcm")

    assert "speech quality error" in str(exc_info.value)


def test_recognize_audio_raises_on_timeout(app):
    mock_client = Mock()
    mock_client.asr.side_effect = TimeoutError("request timeout")

    with app.app_context(), patch("app.services.asr_service.get_asr_client", return_value=mock_client):
        with pytest.raises(ASRException) as exc_info:
            recognize_audio(b"slow-audio", "pcm")

    assert "调用失败" in str(exc_info.value)


def test_voice_endpoint_returns_recognized_text_and_results(client):
    with patch("app.api.classify.recognize_audio", return_value="矿泉水瓶"):
        response = client.post(
            "/api/v1/classify/voice",
            data={"audio": (io.BytesIO(b"pcm-data"), "voice.pcm", "application/octet-stream")},
            content_type="multipart/form-data",
        )
    body = response.get_json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["recognized_text"] == "矿泉水瓶"
    assert body["data"]["results"][0]["name"] == "矿泉水瓶"


def test_voice_endpoint_returns_friendly_error_when_asr_fails(client):
    with patch("app.api.classify.recognize_audio", side_effect=ASRException("noise")):
        response = client.post(
            "/api/v1/classify/voice",
            data={"audio": (io.BytesIO(b""), "voice.pcm", "application/octet-stream")},
            content_type="multipart/form-data",
        )
    body = response.get_json()

    assert response.status_code == 200
    assert body["code"] == 42002
    assert "语音识别失败" in body["message"]


def test_voice_endpoint_creates_history_when_authenticated(client, app, auth_header):
    with patch("app.api.classify.recognize_audio", return_value="矿泉水瓶"):
        response = client.post(
            "/api/v1/classify/voice",
            data={"audio": (io.BytesIO(b"pcm-data"), "voice.pcm", "application/octet-stream")},
            headers=auth_header,
            content_type="multipart/form-data",
        )
    body = response.get_json()

    assert response.status_code == 200
    assert body["code"] == 200

    with app.app_context():
        history = QueryHistory.query.order_by(QueryHistory.id.desc()).first()
        assert history is not None
        assert history.query_type == "voice"
        assert history.query_input == "矿泉水瓶"
        assert history.garbage_item_id is not None
