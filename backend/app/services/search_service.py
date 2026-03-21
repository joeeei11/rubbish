"""
搜索与详情服务
处理关键词检索、物品详情查询与知识图谱数据拼装
"""
import json
from collections import deque

import redis
from flask import current_app
from sqlalchemy import or_, text
from sqlalchemy.orm import joinedload

from app.models.article import Article
from app.models import db
from app.models.category import Category
from app.models.garbage_item import GarbageItem
from app.models.knowledge_relation import KnowledgeRelation


CACHE_TTL_SECONDS = 300


def _get_redis_client():
    """获取 Redis 客户端，连接失败时返回 None。"""
    redis_url = current_app.config.get("REDIS_URL", "").strip()
    if not redis_url:
        return None

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def _cache_get(cache_key):
    """读取缓存。"""
    client = _get_redis_client()
    if client is None:
        return None

    try:
        payload = client.get(cache_key)
        return json.loads(payload) if payload else None
    except Exception:
        return None


def _cache_set(cache_key, payload):
    """写入缓存。"""
    client = _get_redis_client()
    if client is None:
        return

    try:
        client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(payload, ensure_ascii=False))
    except Exception:
        return


def _serialize_item(item):
    """序列化物品对象。"""
    return item.to_dict(include_category=True)


def _serialize_relation(relation, current_item_id):
    """序列化关系对象，并补齐关联物品。"""
    related_item = relation.target_item if relation.source_item_id == current_item_id else relation.source_item
    if related_item is None:
        return None

    return {
        "id": relation.id,
        "relationType": relation.relation_type,
        "description": relation.description,
        "relatedItem": related_item.to_dict(include_category=True),
    }


def _run_fulltext_search(keyword):
    """在 MySQL 下尝试执行 FULLTEXT 查询，失败时返回空列表。"""
    bind = db.session.get_bind()
    if bind is None or bind.dialect.name != "mysql":
        return []

    sql = text(
        """
        SELECT id
        FROM garbage_items
        WHERE is_active = 1
          AND MATCH(name, alias, description, components, reason)
              AGAINST (:keyword IN NATURAL LANGUAGE MODE)
        ORDER BY MATCH(name, alias, description, components, reason)
                 AGAINST (:keyword IN NATURAL LANGUAGE MODE) DESC,
                 id ASC
        LIMIT 200
        """
    )

    try:
        rows = GarbageItem.query.session.execute(sql, {"keyword": keyword}).fetchall()
        return [int(row[0]) for row in rows]
    except Exception:
        return []


def _run_like_search(keyword):
    """执行 LIKE 兜底搜索。"""
    pattern = f"%{keyword}%"

    query = (
        GarbageItem.query
        .options(joinedload(GarbageItem.category))
        .filter(GarbageItem.is_active.is_(True))
        .filter(
            or_(
                GarbageItem.name.like(pattern),
                GarbageItem.alias.like(pattern),
                GarbageItem.description.like(pattern),
                GarbageItem.components.like(pattern),
                GarbageItem.reason.like(pattern),
            )
        )
        .order_by(
            GarbageItem.name.asc(),
            GarbageItem.id.asc(),
        )
        .limit(200)
    )
    return query.all()


def search_by_keyword(keyword, page=1, size=10):
    """
    按关键词搜索物品。

    优先读取 Redis 缓存；未命中则尝试 MySQL FULLTEXT，再使用 LIKE 兜底。
    """
    normalized_keyword = (keyword or "").strip()
    page = max(int(page or 1), 1)
    size = max(min(int(size or 10), 50), 1)

    cache_key = f"search:{normalized_keyword}:{page}:{size}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    fulltext_ids = _run_fulltext_search(normalized_keyword)
    merged_items = []
    seen_ids = set()

    if fulltext_ids:
        for item in (
            GarbageItem.query
            .options(joinedload(GarbageItem.category))
            .filter(GarbageItem.id.in_(fulltext_ids))
            .all()
        ):
            seen_ids.add(item.id)
            merged_items.append(item)

        merged_items.sort(key=lambda item: fulltext_ids.index(item.id))

    for item in _run_like_search(normalized_keyword):
        if item.id not in seen_ids:
            seen_ids.add(item.id)
            merged_items.append(item)

    total = len(merged_items)
    start = (page - 1) * size
    end = start + size
    page_items = merged_items[start:end]

    result = {
        "list": [_serialize_item(item) for item in page_items],
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "hasMore": end < total,
        },
    }
    _cache_set(cache_key, result)
    return result


def get_item_by_id(item_id):
    """获取物品详情与关联物品。"""
    item = (
        GarbageItem.query
        .options(joinedload(GarbageItem.category))
        .filter_by(id=item_id, is_active=True)
        .first()
    )
    if item is None:
        return None

    relations = (
        KnowledgeRelation.query
        .options(
            joinedload(KnowledgeRelation.source_item).joinedload(GarbageItem.category),
            joinedload(KnowledgeRelation.target_item).joinedload(GarbageItem.category),
        )
        .filter(
            or_(
                KnowledgeRelation.source_item_id == item.id,
                KnowledgeRelation.target_item_id == item.id,
            )
        )
        .all()
    )

    serialized_relations = []
    related_items = []
    related_seen = set()
    for relation in relations:
        payload = _serialize_relation(relation, item.id)
        if payload is None:
            continue

        serialized_relations.append(payload)
        related_item = payload["relatedItem"]
        if related_item["id"] not in related_seen:
            related_seen.add(related_item["id"])
            related_items.append(related_item)

    return {
        **_serialize_item(item),
        "relations": serialized_relations,
        "relatedItems": related_items,
    }


def build_knowledge_graph(item_id, max_depth=2, max_nodes=20):
    """构建知识图谱数据，返回 ECharts 兼容结构。"""
    center_item = (
        GarbageItem.query
        .options(joinedload(GarbageItem.category))
        .filter_by(id=item_id, is_active=True)
        .first()
    )
    if center_item is None:
        return None

    all_categories = Category.query.order_by(Category.id.asc()).all()
    category_index = {category.id: index for index, category in enumerate(all_categories)}

    node_map = {}
    edge_keys = set()
    edges = []
    queue = deque([(center_item.id, 0)])
    visited = {center_item.id}

    while queue and len(node_map) < max_nodes:
        current_id, depth = queue.popleft()
        current_item = (
            GarbageItem.query
            .options(joinedload(GarbageItem.category))
            .filter_by(id=current_id, is_active=True)
            .first()
        )
        if current_item is None:
            continue

        node_map[current_item.id] = {
            "id": current_item.id,
            "name": current_item.name,
            "category": category_index.get(current_item.category_id, 0),
            "symbolSize": 36 if current_item.id == center_item.id else 24,
        }

        if depth >= max_depth:
            continue

        relations = (
            KnowledgeRelation.query
            .options(
                joinedload(KnowledgeRelation.source_item).joinedload(GarbageItem.category),
                joinedload(KnowledgeRelation.target_item).joinedload(GarbageItem.category),
            )
            .filter(
                or_(
                    KnowledgeRelation.source_item_id == current_item.id,
                    KnowledgeRelation.target_item_id == current_item.id,
                )
            )
            .all()
        )

        for relation in relations:
            related_item = relation.target_item if relation.source_item_id == current_item.id else relation.source_item
            if related_item is None:
                continue
            if related_item.id not in node_map and len(node_map) >= max_nodes:
                continue

            node_map.setdefault(
                related_item.id,
                {
                    "id": related_item.id,
                    "name": related_item.name,
                    "category": category_index.get(related_item.category_id, 0),
                    "symbolSize": 24,
                }
            )

            edge_key = tuple(sorted((current_item.id, related_item.id)) + [relation.relation_type])
            if edge_key not in edge_keys:
                edge_keys.add(edge_key)
                edges.append(
                    {
                        "source": current_item.id,
                        "target": related_item.id,
                        "label": relation.relation_type,
                    }
                )

            if related_item.id not in visited and len(node_map) < max_nodes:
                visited.add(related_item.id)
                queue.append((related_item.id, depth + 1))

    return {
        "nodes": list(node_map.values())[:max_nodes],
        "edges": edges,
        "categories": [{"name": category.name} for category in all_categories],
        "centerItemId": center_item.id,
    }


def list_articles(page=1, size=10):
    """分页获取文章列表。"""
    page = max(int(page or 1), 1)
    size = max(min(int(size or 10), 50), 1)
    query = Article.query.filter_by(is_published=True).order_by(Article.created_at.desc(), Article.id.desc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {
        "list": [item.to_dict(include_content=False) for item in items],
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "hasMore": page * size < total,
        },
    }


def get_article_by_id(article_id):
    """获取文章详情，并累加浏览数。"""
    article = Article.query.filter_by(id=article_id, is_published=True).first()
    if article is None:
        return None

    article.view_count += 1
    from app.models import db
    db.session.commit()
    return article.to_dict(include_content=True)
