"""
全局资产搜索服务

基于 MeiliSearch 提供全文搜索、分面过滤、相似资产推荐和自动补全。
当 MeiliSearch 不可用时，降级为数据库 LIKE 查询。
"""

import logging

from sqlalchemy import or_

from zou.app import db
from zou.app.indexer import indexing
from zou.app.models.global_asset import GlobalAsset

logger = logging.getLogger(__name__)

INDEX_NAME = "global_assets"

# ---------------------------------------------------------------------------
# Index management
# ---------------------------------------------------------------------------


def ensure_index():
    """
    确保 global_assets 索引存在并配置正确。
    若索引不存在则创建，同时更新 searchable / filterable / sortable 属性。
    """
    try:
        index = indexing.create_index(
            INDEX_NAME,
            searchable_fields=[
                "name",
                "description",
                "tags",
                "style_keywords",
                "prompt_text",
                "category_name",
                "creator_name",
            ],
            filterable_fields=[
                "category_id",
                "category_slug",
                "status",
                "creator_id",
                "source_project_id",
            ],
        )
        # create_index only sets filterableAttributes and a default sortable;
        # we need additional sortable + ranking rules.
        index.update_settings(
            {
                "sortableAttributes": [
                    "created_at",
                    "updated_at",
                    "usage_count",
                    "name",
                ],
                "rankingRules": [
                    "words",
                    "typo",
                    "proximity",
                    "attribute",
                    "sort",
                    "exactness",
                ],
            }
        )
        logger.info("global_assets index ensured.")
        return index
    except Exception as e:
        logger.warning("Failed to ensure global_assets index: %s", e)
        return None


# ---------------------------------------------------------------------------
# Document preparation
# ---------------------------------------------------------------------------


def _prepare_document(asset_data):
    """
    将 GlobalAsset 序列化字典转换为 MeiliSearch 文档。

    Args:
        asset_data: _serialize_asset() 返回的 dict

    Returns:
        dict: MeiliSearch 文档
    """
    tags = asset_data.get("tags") or []
    style_keywords = asset_data.get("style_keywords") or []

    category = asset_data.get("category") or {}

    return {
        "id": str(asset_data["id"]),
        "name": asset_data.get("name", ""),
        "description": asset_data.get("description", ""),
        "tags": " ".join(tags) if isinstance(tags, list) else str(tags),
        "style_keywords": (
            " ".join(style_keywords)
            if isinstance(style_keywords, list)
            else str(style_keywords)
        ),
        "prompt_text": asset_data.get("prompt_text", "") or "",
        "category_name": category.get("name", ""),
        "category_slug": category.get("slug", ""),
        "category_id": str(asset_data.get("category_id", "")),
        "creator_name": asset_data.get("creator_name", ""),
        "creator_id": str(asset_data.get("creator_id", "")),
        "source_project_id": str(
            asset_data.get("source_project_id", "") or ""
        ),
        "status": (
            asset_data["status"][0]
            if isinstance(asset_data.get("status"), tuple)
            else asset_data.get("status", "draft")
        ),
        "usage_count": asset_data.get("usage_count", 0),
        "thumbnail_preview_file_id": str(
            asset_data.get("thumbnail_preview_file_id", "") or ""
        ),
        "created_at": str(asset_data.get("created_at", "")),
        "updated_at": str(asset_data.get("updated_at", "")),
    }


# ---------------------------------------------------------------------------
# Single-document operations
# ---------------------------------------------------------------------------


def index_asset(asset_data):
    """索引单个资产（创建/更新时调用）。"""
    try:
        index = indexing.get_index(INDEX_NAME)
        document = _prepare_document(asset_data)
        indexing.index_document(index, document)
        return document
    except indexing.IndexerNotInitializedError:
        logger.debug("Indexer not initialized, skipping index_asset.")
    except Exception as e:
        logger.warning("Failed to index global asset: %s", e)
    return {}


def remove_asset_from_index(asset_id):
    """从索引中删除资产。"""
    try:
        index = indexing.get_index(INDEX_NAME)
        indexing.remove_document(index, str(asset_id))
    except indexing.IndexerNotInitializedError:
        logger.debug("Indexer not initialized, skipping remove.")
    except Exception as e:
        logger.warning("Failed to remove global asset from index: %s", e)


# ---------------------------------------------------------------------------
# Bulk indexing
# ---------------------------------------------------------------------------


def bulk_index_assets(batch_size=500, progress_callback=None):
    """
    全量重建索引（从数据库批量导入）。

    Args:
        batch_size: 每批文档数量，默认 500
        progress_callback: 可选回调 fn(indexed_so_far, total)

    Returns:
        dict: { indexed: int, errors: list[str] }
    """
    from zou.app.services import global_asset_service

    errors = []
    indexed = 0

    try:
        index = ensure_index()
        if index is None:
            return {"indexed": 0, "errors": ["Failed to ensure index."]}

        # Clear existing documents
        indexing.clear_index(INDEX_NAME)
    except Exception as e:
        return {"indexed": 0, "errors": [f"Index setup failed: {e}"]}

    # Stream assets in batches
    offset = 0
    total = GlobalAsset.query().count()

    while offset < total:
        assets = (
            GlobalAsset.query()
            .order_by(GlobalAsset.created_at.asc())
            .offset(offset)
            .limit(batch_size)
            .all()
        )
        if not assets:
            break

        documents = []
        for asset in assets:
            try:
                serialized = global_asset_service._serialize_asset(asset)
                if serialized:
                    documents.append(_prepare_document(serialized))
            except Exception as e:
                errors.append(f"Asset {asset.id}: {e}")

        if documents:
            try:
                indexing.index_documents(index, documents)
                indexed += len(documents)
            except Exception as e:
                errors.append(f"Batch at offset {offset}: {e}")

        offset += batch_size

        if progress_callback:
            progress_callback(indexed, total)

    logger.info(
        "Bulk index complete: %d indexed, %d errors.", indexed, len(errors)
    )
    return {"indexed": indexed, "errors": errors}


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_assets(query, filters=None, sort=None, page=1, per_page=20):
    """
    搜索全局资产。

    Args:
        query: 搜索关键词
        filters: MeiliSearch 过滤表达式
            (e.g. "category_slug = 'character' AND status = 'reviewed'")
        sort: 排序字段列表 (e.g. ["usage_count:desc"])
        page: 页码（从 1 开始）
        per_page: 每页数量

    Returns:
        dict: { hits, query, total_hits, page, per_page, processing_time_ms }
    """
    try:
        index = indexing.get_index(INDEX_NAME)
        search_options = {
            "limit": per_page,
            "offset": (page - 1) * per_page,
        }
        if filters:
            search_options["filter"] = filters
        if sort:
            search_options["sort"] = sort

        result = index.search(query, search_options)

        return {
            "hits": result.get("hits", []),
            "query": result.get("query", query),
            "total_hits": result.get("estimatedTotalHits", 0),
            "page": page,
            "per_page": per_page,
            "processing_time_ms": result.get("processingTimeMs", 0),
        }
    except indexing.IndexerNotInitializedError:
        logger.debug("Indexer not initialized, falling back to DB search.")
        return _fallback_db_search(query, filters, page, per_page)
    except Exception as e:
        logger.warning("MeiliSearch query failed, falling back to DB: %s", e)
        return _fallback_db_search(query, filters, page, per_page)


def search_by_tags(tags, page=1, per_page=20):
    """
    按标签搜索（将标签列表合并为搜索词）。

    Args:
        tags: 标签列表
        page: 页码
        per_page: 每页数量
    """
    query = " ".join(tags) if isinstance(tags, list) else str(tags)
    return search_assets(query, page=page, per_page=per_page)


def search_similar(asset_id, limit=10):
    """
    搜索相似资产（基于相同标签和关键词）。

    1. 获取目标资产的 tags + style_keywords
    2. 用这些词做搜索查询
    3. 排除自身

    Args:
        asset_id: 资产 ID
        limit: 返回数量

    Returns:
        dict: 搜索结果（同 search_assets 格式）
    """
    from zou.app.services import global_asset_service

    asset = global_asset_service.get_asset(asset_id)
    tags = asset.get("tags") or []
    keywords = asset.get("style_keywords") or []
    name = asset.get("name", "")

    # Build query from tags + keywords + name
    terms = tags + keywords + [name]
    query = " ".join(t for t in terms if t)

    if not query.strip():
        return {
            "hits": [],
            "query": "",
            "total_hits": 0,
            "page": 1,
            "per_page": limit,
            "processing_time_ms": 0,
        }

    # Fetch limit+1 and filter out self
    result = search_assets(query, page=1, per_page=limit + 1)
    result["hits"] = [
        h for h in result["hits"] if h.get("id") != str(asset_id)
    ][:limit]
    result["per_page"] = limit
    return result


def get_search_suggestions(partial_query, limit=5):
    """
    搜索建议 / 自动补全。

    Args:
        partial_query: 部分输入
        limit: 返回数量

    Returns:
        list[str]: 建议的搜索词（从 hits 的 name 字段提取）
    """
    result = search_assets(partial_query, per_page=limit)
    return [h.get("name", "") for h in result.get("hits", [])]


def get_facet_stats():
    """
    获取分面统计（各分类/状态的资产数量分布）。

    Returns:
        dict: { category_slug: { ... }, status: { ... } }
    """
    try:
        index = indexing.get_index(INDEX_NAME)
        # MeiliSearch facet search
        result = index.search(
            "",
            {
                "facets": ["category_slug", "status"],
                "limit": 0,
            },
        )
        return result.get("facetDistribution", {})
    except indexing.IndexerNotInitializedError:
        logger.debug("Indexer not initialized for facet_stats.")
        return {}
    except Exception as e:
        logger.warning("Failed to get facet stats: %s", e)
        return {}


# ---------------------------------------------------------------------------
# Index sync hooks (fire-and-forget, never block CRUD)
# ---------------------------------------------------------------------------


def on_asset_created(asset_data):
    """资产创建后同步索引。"""
    try:
        index_asset(asset_data)
    except Exception as e:
        logger.warning("on_asset_created index sync failed: %s", e)


def on_asset_updated(asset_data):
    """资产更新后同步索引。"""
    try:
        index_asset(asset_data)
    except Exception as e:
        logger.warning("on_asset_updated index sync failed: %s", e)


def on_asset_deleted(asset_id):
    """资产删除后清除索引。"""
    try:
        remove_asset_from_index(asset_id)
    except Exception as e:
        logger.warning("on_asset_deleted index sync failed: %s", e)


# ---------------------------------------------------------------------------
# Fallback: database LIKE search when MeiliSearch is unavailable
# ---------------------------------------------------------------------------


def _fallback_db_search(query, filters=None, page=1, per_page=20):
    """
    MeiliSearch 不可用时的降级搜索（数据库 LIKE 查询）。
    仅支持 name/description 关键词搜索，不支持复杂过滤。
    """
    from zou.app.services.global_asset_service import _serialize_asset

    db_query = GlobalAsset.query()

    if query:
        pattern = f"%{query}%"
        db_query = db_query.filter(
            or_(
                GlobalAsset.name.ilike(pattern),
                GlobalAsset.description.ilike(pattern),
            )
        )

    db_query = db_query.order_by(GlobalAsset.updated_at.desc())

    total = db_query.count()
    offset = (page - 1) * per_page
    assets = db_query.offset(offset).limit(per_page).all()

    return {
        "hits": [_serialize_asset(a) for a in assets],
        "query": query or "",
        "total_hits": total,
        "page": page,
        "per_page": per_page,
        "processing_time_ms": 0,
    }
