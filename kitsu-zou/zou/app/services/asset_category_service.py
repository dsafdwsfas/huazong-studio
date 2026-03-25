"""
资产分类服务

提供资产分类的 CRUD、树形结构、排序、统计和预设初始化功能。
"""

import logging

from sqlalchemy import func

from zou.app import db
from zou.app.models.asset_category import AssetCategory
from zou.app.models.global_asset import GlobalAsset
from zou.app.services.exception import (
    AssetCategoryNotFoundException,
    WrongParameterException,
)

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    {
        "name": "人物",
        "name_en": "Character",
        "slug": "character",
        "icon": "user",
        "color": "#FF6B6B",
        "sort_order": 1,
    },
    {
        "name": "场景",
        "name_en": "Scene",
        "slug": "scene",
        "icon": "image",
        "color": "#4ECDC4",
        "sort_order": 2,
    },
    {
        "name": "道具",
        "name_en": "Prop",
        "slug": "prop",
        "icon": "box",
        "color": "#45B7D1",
        "sort_order": 3,
    },
    {
        "name": "特效",
        "name_en": "VFX",
        "slug": "vfx",
        "icon": "zap",
        "color": "#FFA07A",
        "sort_order": 4,
    },
    {
        "name": "音乐",
        "name_en": "Music",
        "slug": "music",
        "icon": "music",
        "color": "#DDA0DD",
        "sort_order": 5,
    },
    {
        "name": "提示词",
        "name_en": "Prompt",
        "slug": "prompt",
        "icon": "message-square",
        "color": "#98D8C8",
        "sort_order": 6,
    },
    {
        "name": "风格",
        "name_en": "Style",
        "slug": "style",
        "icon": "palette",
        "color": "#F7DC6F",
        "sort_order": 7,
    },
    {
        "name": "镜头语言",
        "name_en": "Camera",
        "slug": "camera",
        "icon": "video",
        "color": "#BB8FCE",
        "sort_order": 8,
    },
]


def _serialize_category(category):
    """Serialize an AssetCategory model instance to dict."""
    if category is None:
        return None
    return category.serialize()


def _build_tree(categories):
    """
    Build a tree structure from a flat list of categories.
    Returns a list of root-level categories with nested children.
    """
    by_id = {}
    for cat in categories:
        data = _serialize_category(cat)
        data["children"] = []
        by_id[str(cat.id)] = data

    roots = []
    for cat in categories:
        data = by_id[str(cat.id)]
        parent_key = str(cat.parent_id) if cat.parent_id else None
        if parent_key and parent_key in by_id:
            by_id[parent_key]["children"].append(data)
        else:
            roots.append(data)

    return roots


def get_category_tree():
    """
    获取完整分类树（仅启用的分类）。

    Returns:
        list[dict]: 树形嵌套结构的分类列表
    """
    categories = (
        AssetCategory.query()
        .filter(AssetCategory.is_active == True)
        .order_by(AssetCategory.sort_order.asc(), AssetCategory.name.asc())
        .all()
    )
    return _build_tree(categories)


def get_category(category_id):
    """
    获取单个分类详情。

    Raises:
        AssetCategoryNotFoundException: 分类不存在
    """
    category = AssetCategory.get(category_id)
    if category is None:
        raise AssetCategoryNotFoundException()
    return _serialize_category(category)


def get_category_raw(category_id):
    """获取分类的 ORM 实例（内部使用）。"""
    category = AssetCategory.get(category_id)
    if category is None:
        raise AssetCategoryNotFoundException()
    return category


def create_category(name, slug, **kwargs):
    """
    创建分类。

    Args:
        name: 分类名称（中文）
        slug: URL 友好标识（唯一）
        **kwargs: name_en, description, icon, color, parent_id,
                  sort_order, is_system, metadata

    Returns:
        dict: 序列化后的分类
    """
    existing = AssetCategory.get_by(slug=slug)
    if existing:
        raise WrongParameterException(
            f"Category with slug '{slug}' already exists."
        )

    if kwargs.get("parent_id"):
        parent = AssetCategory.get(kwargs["parent_id"])
        if parent is None:
            raise WrongParameterException("Parent category not found.")

    category = AssetCategory.create(
        name=name,
        slug=slug,
        name_en=kwargs.get("name_en", ""),
        description=kwargs.get("description", ""),
        icon=kwargs.get("icon", ""),
        color=kwargs.get("color", ""),
        parent_id=kwargs.get("parent_id"),
        sort_order=kwargs.get("sort_order", 0),
        is_system=kwargs.get("is_system", False),
        is_active=True,
        metadata_=kwargs.get("metadata", {}),
    )
    return _serialize_category(category)


def update_category(category_id, data):
    """
    更新分类。系统分类只允许修改 description, color, icon。

    Args:
        category_id: 分类 ID
        data: 更新字段

    Returns:
        dict: 序列化后的分类
    """
    category = get_category_raw(category_id)

    if category.is_system:
        allowed = {"description", "color", "icon"}
        restricted = set(data.keys()) - allowed - {"metadata"}
        if restricted:
            raise WrongParameterException(
                f"System category only allows updating: "
                f"{', '.join(allowed)}. "
                f"Cannot update: {', '.join(restricted)}"
            )

    updatable_fields = [
        "name",
        "name_en",
        "slug",
        "description",
        "icon",
        "color",
        "parent_id",
        "sort_order",
        "is_active",
    ]

    if "slug" in data and data["slug"] != category.slug:
        existing = AssetCategory.get_by(slug=data["slug"])
        if existing:
            raise WrongParameterException(
                f"Category with slug '{data['slug']}' already exists."
            )

    if "parent_id" in data and data["parent_id"]:
        if str(data["parent_id"]) == str(category.id):
            raise WrongParameterException(
                "Category cannot be its own parent."
            )
        parent = AssetCategory.get(data["parent_id"])
        if parent is None:
            raise WrongParameterException("Parent category not found.")

    for field in updatable_fields:
        if field in data:
            setattr(category, field, data[field])

    if "metadata" in data:
        category.metadata_ = data["metadata"]

    category.save()
    return _serialize_category(category)


def delete_category(category_id):
    """
    删除分类。

    Rules:
        - 系统分类不可删
        - 有子分类不可删
        - 有关联资产不可删

    Returns:
        bool: True if deleted
    """
    category = get_category_raw(category_id)

    if category.is_system:
        raise WrongParameterException(
            "System categories cannot be deleted."
        )

    child_count = (
        AssetCategory.query()
        .filter(AssetCategory.parent_id == category.id)
        .count()
    )
    if child_count > 0:
        raise WrongParameterException(
            f"Cannot delete: category has {child_count} child categories. "
            f"Move or delete them first."
        )

    asset_count = (
        GlobalAsset.query()
        .filter(GlobalAsset.category_id == category.id)
        .count()
    )
    if asset_count > 0:
        raise WrongParameterException(
            f"Cannot delete: category has {asset_count} linked assets. "
            f"Reassign them first."
        )

    category.delete()
    return True


def reorder_categories(category_orders):
    """
    批量更新排序。

    Args:
        category_orders: list of {id, sort_order}
    """
    for item in category_orders:
        cat_id = item.get("id")
        sort_order = item.get("sort_order")
        if cat_id is None or sort_order is None:
            continue
        category = AssetCategory.get(cat_id)
        if category:
            category.sort_order = sort_order
            db.session.add(category)

    db.session.commit()
    return True


def get_category_stats():
    """
    获取每个分类的资产数量统计。

    Returns:
        list[dict]: [{id, name, slug, color, icon, asset_count}]
    """
    results = (
        db.session.query(
            AssetCategory.id,
            AssetCategory.name,
            AssetCategory.slug,
            AssetCategory.color,
            AssetCategory.icon,
            func.count(GlobalAsset.id).label("asset_count"),
        )
        .outerjoin(
            GlobalAsset,
            GlobalAsset.category_id == AssetCategory.id,
        )
        .filter(AssetCategory.is_active == True)
        .group_by(
            AssetCategory.id,
            AssetCategory.name,
            AssetCategory.slug,
            AssetCategory.color,
            AssetCategory.icon,
        )
        .order_by(AssetCategory.sort_order.asc())
        .all()
    )

    return [
        {
            "id": str(row.id),
            "name": row.name,
            "slug": row.slug,
            "color": row.color,
            "icon": row.icon,
            "asset_count": row.asset_count,
        }
        for row in results
    ]


def init_default_categories():
    """
    初始化预设分类（幂等 — 已存在则跳过）。

    Returns:
        dict: {created: int, skipped: int, categories: list}
    """
    created = []
    skipped = 0

    for default in DEFAULT_CATEGORIES:
        existing = AssetCategory.get_by(slug=default["slug"])
        if existing:
            skipped += 1
            continue

        category = AssetCategory.create(
            name=default["name"],
            name_en=default["name_en"],
            slug=default["slug"],
            icon=default["icon"],
            color=default["color"],
            sort_order=default["sort_order"],
            is_system=True,
            is_active=True,
            metadata_={},
        )
        created.append(_serialize_category(category))

    return {
        "created": len(created),
        "skipped": skipped,
        "categories": created,
    }
