"""
种子数据导入脚本
读取 data/knowledge_base.json 并幂等写入数据库
"""
import json
from pathlib import Path

from app import create_app
from app.models import db
from app.models.article import Article
from app.models.category import Category
from app.models.garbage_item import GarbageItem
from app.models.knowledge_relation import KnowledgeRelation


ROOT_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_PATH = ROOT_DIR / "data" / "knowledge_base.json"

CATEGORY_CODE_MAP = {
    "可回收物": "recyclable",
    "有害垃圾": "hazardous",
    "厨余垃圾": "kitchen",
    "其他垃圾": "other",
}


def load_knowledge_base():
    """读取知识库 JSON 文件。"""
    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError(f"未找到知识库文件：{KNOWLEDGE_BASE_PATH}")

    with KNOWLEDGE_BASE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def upsert_categories(category_records):
    """导入分类数据。"""
    created_count = 0
    updated_count = 0
    category_map = {}

    for record in category_records:
        name = (record.get("name") or "").strip()
        if not name:
            continue

        category = Category.query.filter_by(name=name).first()
        is_created = category is None
        if is_created:
            category = Category(name=name)
            db.session.add(category)
            created_count += 1
        else:
            updated_count += 1

        category.code = record.get("code") or CATEGORY_CODE_MAP.get(name, name)
        category.color = record.get("color")
        category.description = record.get("description")
        category.disposal_guide = record.get("disposal_method") or record.get("disposal_guide")
        category_map[name] = category

    db.session.commit()
    return category_map, created_count, updated_count


def upsert_items(item_records, category_map):
    """导入垃圾物品数据。"""
    created_count = 0
    updated_count = 0
    item_map = {}

    for index, record in enumerate(item_records, start=1):
        name = (record.get("name") or "").strip()
        category_name = (record.get("category") or "").strip()
        category = category_map.get(category_name)

        if not name or category is None:
            continue

        item = GarbageItem.query.filter_by(name=name).first()
        is_created = item is None
        if is_created:
            item = GarbageItem(name=name)
            db.session.add(item)
            created_count += 1
        else:
            updated_count += 1

        alias = record.get("alias", "")
        if isinstance(alias, list):
            alias = ",".join(alias)

        item.alias = alias
        item.category = category
        item.image_url = record.get("image_url")
        item.description = record.get("description")
        item.components = record.get("components")
        item.reason = record.get("reason")
        item.tips = record.get("tips")
        item.is_active = True
        item_map[name] = item

        if index % 50 == 0:
            print(f"[seed] 已处理物品 {index}/{len(item_records)} 条")

    db.session.commit()
    return item_map, created_count, updated_count


def upsert_relations(item_records, item_map):
    """导入知识关系。"""
    created_count = 0
    updated_count = 0

    for record in item_records:
        source_name = record.get("name")
        source_item = item_map.get(source_name)
        if source_item is None:
            continue

        for relation in record.get("relations", []):
            target_name = relation.get("to")
            target_item = item_map.get(target_name)
            if target_item is None or target_item.id == source_item.id:
                continue

            relation_type = relation.get("type") or "related_to"
            entity = KnowledgeRelation.query.filter_by(
                source_item_id=source_item.id,
                target_item_id=target_item.id,
                relation_type=relation_type,
            ).first()

            if entity is None:
                entity = KnowledgeRelation(
                    source_item_id=source_item.id,
                    target_item_id=target_item.id,
                    relation_type=relation_type,
                )
                db.session.add(entity)
                created_count += 1
            else:
                updated_count += 1

            entity.description = relation.get("description")

    db.session.commit()
    return created_count, updated_count


def upsert_articles(article_records):
    """导入科普文章。"""
    created_count = 0
    updated_count = 0

    for record in article_records:
        title = (record.get("title") or "").strip()
        content = (record.get("content") or "").strip()
        if not title or not content:
            continue

        article = Article.query.filter_by(title=title).first()
        if article is None:
            article = Article(title=title)
            db.session.add(article)
            created_count += 1
        else:
            updated_count += 1

        summary = record.get("summary") or content.replace("\n", " ")[:120]
        category_name = record.get("category")
        article.summary = summary
        article.content = content
        article.cover_image = record.get("cover_image")
        article.category_tag = CATEGORY_CODE_MAP.get(category_name, category_name)
        article.is_published = True

    db.session.commit()
    return created_count, updated_count


def print_statistics():
    """打印最终统计信息。"""
    print("\n[seed] 导入完成，当前数据库统计：")
    print(f"[seed] 分类数：{Category.query.count()}")
    print(f"[seed] 物品数：{GarbageItem.query.count()}")
    print(f"[seed] 关系数：{KnowledgeRelation.query.count()}")
    print(f"[seed] 文章数：{Article.query.count()}")


def main():
    """脚本入口。"""
    app = create_app()
    payload = load_knowledge_base()

    with app.app_context():
        categories = payload.get("categories", [])
        items = payload.get("items", [])
        articles = payload.get("articles", [])

        print("[seed] 开始导入知识库数据")
        print(f"[seed] 分类记录：{len(categories)}")
        print(f"[seed] 物品记录：{len(items)}")
        print(f"[seed] 文章记录：{len(articles)}")

        category_map, category_created, category_updated = upsert_categories(categories)
        item_map, item_created, item_updated = upsert_items(items, category_map)
        relation_created, relation_updated = upsert_relations(items, item_map)
        article_created, article_updated = upsert_articles(articles)

        print("\n[seed] 本次导入结果：")
        print(f"[seed] 分类：新增 {category_created}，更新 {category_updated}")
        print(f"[seed] 物品：新增 {item_created}，更新 {item_updated}")
        print(f"[seed] 关系：新增 {relation_created}，更新 {relation_updated}")
        print(f"[seed] 文章：新增 {article_created}，更新 {article_updated}")
        print_statistics()


if __name__ == "__main__":
    main()
