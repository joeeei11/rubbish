"""
Phase 3 搜索、详情、图谱与文章接口测试
"""
import os
from unittest.mock import patch
import pytest

from app import create_app
from app.models import db as _db
from app.models.article import Article
from app.models.category import Category
from app.models.garbage_item import GarbageItem
from app.models.knowledge_relation import KnowledgeRelation
from app.services.search_service import build_knowledge_graph, get_item_by_id, search_by_keyword


@pytest.fixture(scope="module")
def app():
    """创建测试应用并写入示例数据。"""
    previous_database_url = os.environ.get("DATABASE_URL")
    previous_redis_url = os.environ.get("REDIS_URL")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = ""
    application = create_app("development")
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "REDIS_URL": "",
        "SECRET_KEY": "phase3-test-secret",
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
        rechargeable = GarbageItem(
            name="充电电池",
            alias="锂电池",
            category=hazardous,
            description="可充电电池",
            components="锂、镍、电解液",
            reason="含重金属和电解液",
            tips="避免短路",
        )
        leftover = GarbageItem(
            name="剩米饭",
            alias="剩饭",
            category=kitchen,
            description="剩余主食",
            components="淀粉和水分",
            reason="属于易腐有机物",
            tips="去掉包装袋",
        )
        tissue = GarbageItem(
            name="纸巾",
            alias="用过的纸",
            category=other,
            description="受污染纸巾",
            components="短纤维纸",
            reason="受污染后无法高质量回收",
            tips="装袋投放",
        )
        _db.session.add_all([bottle, cola_bottle, battery, rechargeable, leftover, tissue])
        _db.session.flush()

        _db.session.add_all([
            KnowledgeRelation(
                source_item_id=bottle.id,
                target_item_id=cola_bottle.id,
                relation_type="similar_to",
                description="同属塑料饮料瓶",
            ),
            KnowledgeRelation(
                source_item_id=battery.id,
                target_item_id=rechargeable.id,
                relation_type="similar_to",
                description="都属于废电池",
            ),
        ])

        _db.session.add_all([
            Article(
                title="矿泉水瓶为什么属于可回收物",
                summary="解释矿泉水瓶的回收逻辑。",
                content="PET 材料可以回收再利用。",
                category_tag="recyclable",
            ),
            Article(
                title="电池为什么要单独投放",
                summary="解释电池的环境风险。",
                content="电池中含有电解液和重金属。",
                category_tag="hazardous",
            ),
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


@pytest.fixture
def client(app):
    return app.test_client()


def test_search_service_returns_mineral_bottle(app):
    """关键词搜索应返回矿泉水瓶。"""
    with app.app_context():
        payload = search_by_keyword("矿泉水瓶", 1, 10)

    assert payload["pagination"]["total"] >= 1
    assert payload["list"][0]["name"] == "矿泉水瓶"
    assert payload["list"][0]["category"]["name"] == "可回收物"


def test_search_service_returns_battery_by_keyword(app):
    """搜索“电池”时应能命中干电池。"""
    with app.app_context():
        payload = search_by_keyword("电池", 1, 10)

    names = [item["name"] for item in payload["list"]]
    assert "干电池" in names


def test_search_service_uses_cache_for_same_keyword(app):
    fake_cache = {}

    class FakeRedis:
        def ping(self):
            return True

        def get(self, key):
            return fake_cache.get(key)

        def setex(self, key, ttl, value):
            fake_cache[key] = value

    with app.app_context():
        items = GarbageItem.query.filter(GarbageItem.name.in_(["矿泉水瓶", "可乐瓶"])).all()
        with patch("app.services.search_service._get_redis_client", return_value=FakeRedis()), patch(
            "app.services.search_service._run_fulltext_search",
            return_value=[],
        ), patch(
            "app.services.search_service._run_like_search",
            return_value=items,
        ) as mock_like_search:
            first_payload = search_by_keyword("矿泉水瓶", 1, 10)
            second_payload = search_by_keyword("矿泉水瓶", 1, 10)

    assert [item["name"] for item in first_payload["list"]] == [item["name"] for item in second_payload["list"]]
    assert "矿泉水瓶" in [item["name"] for item in first_payload["list"]]
    assert mock_like_search.call_count == 1


def test_get_item_by_id_contains_related_items(app):
    """详情查询应返回关联物品。"""
    with app.app_context():
        bottle = GarbageItem.query.filter_by(name="矿泉水瓶").first()
        payload = get_item_by_id(bottle.id)

    assert payload["name"] == "矿泉水瓶"
    assert payload["relatedItems"][0]["name"] == "可乐瓶"
    assert payload["relations"][0]["relationType"] == "similar_to"


def test_build_knowledge_graph_returns_nodes_and_edges(app):
    """知识图谱应返回节点和边。"""
    with app.app_context():
        bottle = GarbageItem.query.filter_by(name="矿泉水瓶").first()
        payload = build_knowledge_graph(bottle.id)

    assert payload["centerItemId"] == bottle.id
    assert len(payload["nodes"]) >= 2
    assert payload["edges"][0]["label"] == "similar_to"


def test_classify_search_endpoint(client):
    """搜索接口应返回标准分页结构。"""
    resp = client.get("/api/v1/classify/search?q=矿泉水瓶&page=1&size=10")
    body = resp.get_json()

    assert resp.status_code == 200
    assert body["code"] == 200
    assert body["data"]["list"][0]["name"] == "矿泉水瓶"


def test_garbage_detail_endpoint(client, app):
    """详情接口应返回完整物品信息。"""
    with app.app_context():
        battery = GarbageItem.query.filter_by(name="干电池").first()

    resp = client.get(f"/api/v1/garbage/{battery.id}")
    body = resp.get_json()

    assert body["code"] == 200
    assert body["data"]["name"] == "干电池"
    assert body["data"]["category"]["name"] == "有害垃圾"


def test_knowledge_graph_endpoint(client, app):
    """图谱接口应返回 ECharts 兼容结构。"""
    with app.app_context():
        bottle = GarbageItem.query.filter_by(name="矿泉水瓶").first()

    resp = client.get(f"/api/v1/knowledge/graph?item_id={bottle.id}")
    body = resp.get_json()

    assert body["code"] == 200
    assert "nodes" in body["data"]
    assert "edges" in body["data"]
    assert body["data"]["categories"][0]["name"] == "可回收物"


def test_article_endpoints(client):
    """文章列表和详情接口应可用。"""
    list_resp = client.get("/api/v1/articles?page=1&size=10")
    list_body = list_resp.get_json()

    assert list_body["code"] == 200
    assert len(list_body["data"]["list"]) == 2

    article_id = list_body["data"]["list"][0]["id"]
    detail_resp = client.get(f"/api/v1/articles/{article_id}")
    detail_body = detail_resp.get_json()

    assert detail_body["code"] == 200
    assert "content" in detail_body["data"]
