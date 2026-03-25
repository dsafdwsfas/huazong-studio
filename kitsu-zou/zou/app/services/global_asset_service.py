"""
全局资产服务

提供跨项目全局资产库的 CRUD、项目关联、使用计数、状态管理和导入功能。
"""

import logging

from sqlalchemy import or_

from zou.app import db
from zou.app.models.asset_category import AssetCategory
from zou.app.models.global_asset import (
    GlobalAsset,
    GlobalAssetProjectLink,
)
from zou.app.models.project import Project
from zou.app.services import persons_service
from zou.app.services.exception import (
    WrongParameterException,
)
from zou.app.utils import date_helpers

# Lazy import to avoid circular dependency; resolved at call-site.
_version_service = None


def _get_version_service():
    global _version_service
    if _version_service is None:
        from zou.app.services import asset_version_service

        _version_service = asset_version_service
    return _version_service

# Lazy import to avoid circular dependency; resolved at call-site.
_search_service = None


def _get_search_service():
    global _search_service
    if _search_service is None:
        from zou.app.services import asset_search_service

        _search_service = asset_search_service
    return _search_service

logger = logging.getLogger(__name__)


class GlobalAssetNotFoundException(Exception):
    pass


def _serialize_asset(asset):
    """Serialize a GlobalAsset model instance to dict."""
    if asset is None:
        return None
    result = asset.serialize()
    # ChoiceType returns tuple for status; extract the code value
    if isinstance(result.get("status"), tuple):
        result["status"] = result["status"][0]
    # Include category details if available
    if asset.category_rel:
        result["category"] = asset.category_rel.serialize()
    return result


def list_assets(
    category=None,
    category_id=None,
    status=None,
    search=None,
    page=1,
    per_page=20,
):
    """
    列出全局资产，支持分页、分类筛选和关键词搜索。

    Args:
        category: 按分类 slug 筛选（向后兼容，查 AssetCategory.slug）
        category_id: 按分类 ID 筛选（UUID，优先于 category）
        status: 按状态筛选（draft, reviewed, archived）
        search: 搜索关键词（匹配 name 和 description）
        page: 页码（从 1 开始）
        per_page: 每页数量

    Returns:
        dict: {data, total, page, per_page, pages}
    """
    query = GlobalAsset.query()

    if category_id:
        query = query.filter(GlobalAsset.category_id == category_id)
    elif category:
        # Backward compatibility: resolve slug to category_id
        cat = AssetCategory.query.filter_by(slug=category).first()
        if cat:
            query = query.filter(GlobalAsset.category_id == cat.id)
        else:
            # No matching category — return empty result
            return {
                "data": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "pages": 0,
            }
    if status:
        query = query.filter(GlobalAsset.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                GlobalAsset.name.ilike(search_pattern),
                GlobalAsset.description.ilike(search_pattern),
            )
        )

    query = query.order_by(GlobalAsset.updated_at.desc())

    total = query.count()
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    assets = query.offset(offset).limit(per_page).all()

    return {
        "data": [_serialize_asset(a) for a in assets],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def get_asset(asset_id):
    """
    获取单个资产详情。

    Raises:
        GlobalAssetNotFoundException: 资产不存在
    """
    asset = GlobalAsset.get(asset_id)
    if asset is None:
        raise GlobalAssetNotFoundException()
    return _serialize_asset(asset)


def get_asset_raw(asset_id):
    """获取资产的 ORM 实例（内部使用）。"""
    asset = GlobalAsset.get(asset_id)
    if asset is None:
        raise GlobalAssetNotFoundException()
    return asset


def create_asset(name, category_id=None, creator_id=None, **kwargs):
    """
    创建全局资产。

    Args:
        name: 资产名称
        category_id: 资产分类 ID（UUID）
        creator_id: 创建者 ID
        **kwargs: 可选字段 — category (slug, 向后兼容),
                  description, tags, files, metadata_,
                  style_keywords, prompt_text, source_project_id,
                  thumbnail_preview_file_id

    Returns:
        dict: 序列化后的资产
    """
    # Backward compatibility: resolve category slug to category_id
    if not category_id and kwargs.get("category"):
        cat = AssetCategory.query.filter_by(
            slug=kwargs.pop("category")
        ).first()
        if cat:
            category_id = cat.id
        else:
            raise WrongParameterException(
                "Category not found for the given slug."
            )

    if not category_id:
        raise WrongParameterException("category_id is required.")

    # Validate that the category exists
    cat_obj = AssetCategory.get(category_id)
    if cat_obj is None:
        raise WrongParameterException("Category not found.")

    asset = GlobalAsset.create(
        name=name,
        category_id=category_id,
        creator_id=creator_id,
        description=kwargs.get("description", ""),
        tags=kwargs.get("tags", []),
        files=kwargs.get("files", []),
        metadata_=kwargs.get("metadata", {}),
        style_keywords=kwargs.get("style_keywords", []),
        prompt_text=kwargs.get("prompt_text", ""),
        source_project_id=kwargs.get("source_project_id"),
        thumbnail_preview_file_id=kwargs.get("thumbnail_preview_file_id"),
        version=1,
        status="draft",
        usage_count=0,
    )
    serialized = _serialize_asset(asset)

    # Sync to search index (fire-and-forget)
    try:
        _get_search_service().on_asset_created(serialized)
    except Exception as e:
        logger.warning("Search index sync failed on create: %s", e)

    # Create initial version snapshot (fire-and-forget)
    try:
        _get_version_service().create_version(
            asset.id, author_id=creator_id,
            change_summary="初始创建", change_type="create",
        )
    except Exception as e:
        logger.warning("Version creation failed on asset create: %s", e)

    return serialized


def update_asset(asset_id, data):
    """
    更新资产字段。

    Args:
        asset_id: 资产 ID
        data: dict — 允许的字段: name, description, tags, files,
              metadata, style_keywords, prompt_text,
              thumbnail_preview_file_id

    Returns:
        dict: 序列化后的资产
    """
    asset = get_asset_raw(asset_id)

    updatable_fields = [
        "name",
        "category_id",
        "description",
        "tags",
        "files",
        "style_keywords",
        "prompt_text",
        "thumbnail_preview_file_id",
    ]

    for field in updatable_fields:
        if field in data:
            setattr(asset, field, data[field])

    # metadata uses metadata_ in the model
    if "metadata" in data:
        asset.metadata_ = data["metadata"]

    asset.updated_at = date_helpers.get_utc_now_datetime()
    db.session.commit()
    serialized = _serialize_asset(asset)

    # Sync to search index (fire-and-forget)
    try:
        _get_search_service().on_asset_updated(serialized)
    except Exception as e:
        logger.warning("Search index sync failed on update: %s", e)

    # Create version snapshot (fire-and-forget)
    try:
        updater_id = data.get("updater_id")
        change_summary = data.get("change_summary")
        _get_version_service().create_version(
            asset_id, author_id=updater_id,
            change_summary=change_summary, change_type="update",
        )
    except Exception as e:
        logger.warning("Version creation failed on asset update: %s", e)

    return serialized


def delete_asset(asset_id):
    """
    删除资产及其项目关联。

    Returns:
        bool: True 如果成功删除
    """
    asset = get_asset_raw(asset_id)

    # Remove from search index before deleting from DB (fire-and-forget)
    try:
        _get_search_service().on_asset_deleted(asset.id)
    except Exception as e:
        logger.warning("Search index sync failed on delete: %s", e)

    # Remove project links
    GlobalAssetProjectLink.query.filter_by(
        global_asset_id=asset.id
    ).delete()

    db.session.delete(asset)
    db.session.commit()
    return True


def link_asset_to_project(asset_id, project_id):
    """
    将资产关联到项目。

    Returns:
        dict: {asset_id, project_id, linked_at}
    """
    asset = get_asset_raw(asset_id)
    project = Project.get(project_id)
    if project is None:
        raise WrongParameterException("Project not found.")

    existing = db.session.get(
        GlobalAssetProjectLink,
        (str(asset.id), str(project.id)),
    )
    if existing:
        return {
            "asset_id": str(asset.id),
            "project_id": str(project.id),
            "linked_at": str(existing.linked_at) if existing.linked_at else None,
            "message": "Already linked.",
        }

    link = GlobalAssetProjectLink(
        global_asset_id=asset.id,
        project_id=project.id,
        linked_at=date_helpers.get_utc_now_datetime(),
    )
    db.session.add(link)
    db.session.commit()

    return {
        "asset_id": str(asset.id),
        "project_id": str(project.id),
        "linked_at": str(link.linked_at),
    }


def unlink_asset_from_project(asset_id, project_id):
    """
    解除资产与项目的关联。

    Returns:
        bool: True 如果成功解除
    """
    get_asset_raw(asset_id)  # validate asset exists

    deleted = (
        GlobalAssetProjectLink.query.filter_by(
            global_asset_id=asset_id,
            project_id=project_id,
        ).delete()
    )
    db.session.commit()

    if not deleted:
        raise WrongParameterException("Link not found.")
    return True


def get_assets_by_project(project_id, category_id=None):
    """
    获取项目关联的全局资产列表。

    Args:
        project_id: 项目 ID
        category_id: 可选分类 ID 筛选

    Returns:
        list[dict]: 资产列表
    """
    query = (
        GlobalAsset.query()
        .join(
            GlobalAssetProjectLink,
            GlobalAsset.id == GlobalAssetProjectLink.global_asset_id,
        )
        .filter(GlobalAssetProjectLink.project_id == project_id)
    )

    if category_id:
        query = query.filter(GlobalAsset.category_id == category_id)

    query = query.order_by(GlobalAsset.name.asc())
    assets = query.all()
    return [_serialize_asset(a) for a in assets]


def increment_usage(asset_id):
    """
    使用计数 +1。

    Returns:
        dict: 包含更新后的 usage_count
    """
    asset = get_asset_raw(asset_id)
    asset.usage_count = (asset.usage_count or 0) + 1
    asset.updated_at = date_helpers.get_utc_now_datetime()
    db.session.commit()
    return _serialize_asset(asset)


def update_status(asset_id, new_status):
    """
    更新资产状态。

    Args:
        asset_id: 资产 ID
        new_status: 新状态（draft, reviewed, archived）

    Returns:
        dict: 序列化后的资产
    """
    valid_statuses = [
        "draft", "pending_review", "reviewed", "rejected", "archived",
    ]
    if new_status not in valid_statuses:
        raise WrongParameterException(
            f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    asset = get_asset_raw(asset_id)
    asset.status = new_status
    asset.updated_at = date_helpers.get_utc_now_datetime()
    db.session.commit()
    return _serialize_asset(asset)


def _resolve_category_id(slug):
    """Resolve a category slug to its ID. Returns None if not found."""
    category = AssetCategory.get_by(slug=slug)
    return category.id if category else None


def import_from_project(project_id, asset_type):
    """
    从项目的 Phase 3 数据中导入资产到全局库。

    支持的 asset_type:
    - prompt: 从 project.data["prompt_library"] 导入
    - style_template: 从 project.data["style_templates"] 导入
    - camera_language: 从 project.data["camera_language"] 导入

    Returns:
        dict: {imported: int, skipped: int, assets: list}
    """
    project = Project.get(project_id)
    if project is None:
        raise WrongParameterException("Project not found.")

    data = project.data or {}
    current_user = persons_service.get_current_user()
    creator_id = current_user["id"]

    imported = []
    skipped = 0

    # Map asset_type to category slug
    type_to_slug = {
        "prompt": "prompt",
        "style_template": "style",
        "camera_language": "camera",
    }

    if asset_type not in type_to_slug:
        raise WrongParameterException(
            "Invalid asset_type. Must be one of: prompt, style_template, camera_language"
        )

    cat_id = _resolve_category_id(type_to_slug[asset_type])

    if asset_type == "prompt":
        items = data.get("prompt_library", [])
        for item in items:
            name = item.get("name") or item.get("title", "Untitled Prompt")
            asset = GlobalAsset.create(
                name=name,
                category_id=cat_id,
                creator_id=creator_id,
                description=item.get("description", ""),
                tags=item.get("tags", []),
                prompt_text=item.get("text", item.get("prompt_text", "")),
                source_project_id=project_id,
                metadata_=item.get("metadata", {}),
                style_keywords=item.get("style_keywords", []),
                version=1,
                status="draft",
                usage_count=item.get("use_count", 0),
            )
            imported.append(_serialize_asset(asset))

    elif asset_type == "style_template":
        items = data.get("style_templates", [])
        for item in items:
            name = item.get("name", "Untitled Template")
            asset = GlobalAsset.create(
                name=name,
                category_id=cat_id,
                creator_id=creator_id,
                description=item.get("description", ""),
                tags=item.get("tags", []),
                metadata_={"style": item.get("style", {})},
                thumbnail_preview_file_id=item.get(
                    "thumbnail_preview_file_id"
                ),
                source_project_id=project_id,
                version=1,
                status="draft",
                usage_count=0,
            )
            imported.append(_serialize_asset(asset))

    elif asset_type == "camera_language":
        items = data.get("camera_language", {}).get("terms", [])
        for item in items:
            name = item.get("name_en") or item.get("name", "Untitled Term")
            asset = GlobalAsset.create(
                name=name,
                category_id=cat_id,
                creator_id=creator_id,
                description=item.get("description", ""),
                tags=item.get("tags", []),
                metadata_={
                    "name_zh": item.get("name_zh", ""),
                    "category": item.get("category", ""),
                    "example": item.get("example", ""),
                },
                prompt_text=item.get("prompt_snippet", ""),
                source_project_id=project_id,
                version=1,
                status="draft",
                usage_count=0,
            )
            imported.append(_serialize_asset(asset))

    return {
        "imported": len(imported),
        "skipped": skipped,
        "assets": imported,
    }
