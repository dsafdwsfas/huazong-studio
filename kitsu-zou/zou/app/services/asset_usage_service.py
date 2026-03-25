"""
资产使用追踪服务

提供资产使用记录的 CRUD、统计、排行、时间线和跨项目分析功能。
record_usage 自动递增 GlobalAsset.usage_count，
delete_usage 自动递减。
"""

import logging
from collections import defaultdict

from sqlalchemy import func, desc

from zou.app import db
from zou.app.models.asset_usage import AssetUsage
from zou.app.models.global_asset import GlobalAsset
from zou.app.models.project import Project
from zou.app.services.exception import WrongParameterException
from zou.app.utils import date_helpers

logger = logging.getLogger(__name__)


class AssetUsageNotFoundException(Exception):
    pass


def _serialize_usage(usage):
    """Serialize an AssetUsage model instance to dict."""
    if usage is None:
        return None
    result = usage.serialize()
    # ChoiceType returns tuple; extract the code value
    if isinstance(result.get("usage_type"), tuple):
        result["usage_type"] = result["usage_type"][0]
    return result


def _get_usage_raw(usage_id):
    """Get AssetUsage ORM instance."""
    usage = AssetUsage.get(usage_id)
    if usage is None:
        raise AssetUsageNotFoundException()
    return usage


def _get_asset_raw(asset_id):
    """Get GlobalAsset ORM instance."""
    asset = GlobalAsset.get(asset_id)
    if asset is None:
        raise WrongParameterException("Asset not found.")
    return asset


def record_usage(
    asset_id,
    project_id,
    used_by_id=None,
    usage_type="direct",
    entity_id=None,
    entity_type=None,
    context=None,
):
    """
    记录一次资产使用，同时更新 GlobalAsset.usage_count += 1。

    Args:
        asset_id: 全局资产 ID
        project_id: 项目 ID
        used_by_id: 使用者 ID（可选）
        usage_type: 使用类型（direct/reference/derived/template）
        entity_id: 实体 ID（分镜/场次等，可选）
        entity_type: 实体类型（shot/sequence/scene/asset，可选）
        context: 使用上下文描述（可选）

    Returns:
        dict: 序列化后的使用记录
    """
    # Validate asset exists
    asset = _get_asset_raw(asset_id)

    # Validate usage_type
    valid_types = ["direct", "reference", "derived", "template"]
    if usage_type not in valid_types:
        raise WrongParameterException(
            f"Invalid usage_type. Must be one of: {', '.join(valid_types)}"
        )

    try:
        usage = AssetUsage.create_no_commit(
            asset_id=asset_id,
            project_id=project_id,
            used_by_id=used_by_id,
            usage_type=usage_type,
            entity_id=entity_id,
            entity_type=entity_type,
            context=context,
        )

        # Increment usage_count on the global asset
        asset.usage_count = (asset.usage_count or 0) + 1
        asset.updated_at = date_helpers.get_utc_now_datetime()

        db.session.commit()
    except BaseException:
        db.session.rollback()
        db.session.remove()
        raise

    return _serialize_usage(usage)


def get_asset_usages(asset_id, page=1, per_page=20):
    """
    获取资产的所有使用记录（按时间倒序）。

    Args:
        asset_id: 全局资产 ID
        page: 页码
        per_page: 每页数量

    Returns:
        dict: {data, total, page, per_page, pages}
    """
    _get_asset_raw(asset_id)  # validate exists

    query = (
        AssetUsage.query()
        .filter(AssetUsage.asset_id == asset_id)
        .order_by(AssetUsage.created_at.desc())
    )

    total = query.count()
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    offset = (page - 1) * per_page
    usages = query.offset(offset).limit(per_page).all()

    return {
        "data": [_serialize_usage(u) for u in usages],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def get_project_usages(project_id, page=1, per_page=20):
    """
    获取项目中使用的所有资产记录。

    Args:
        project_id: 项目 ID
        page: 页码
        per_page: 每页数量

    Returns:
        dict: {data, total, page, per_page, pages}
    """
    query = (
        AssetUsage.query()
        .filter(AssetUsage.project_id == project_id)
        .order_by(AssetUsage.created_at.desc())
    )

    total = query.count()
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    offset = (page - 1) * per_page
    usages = query.offset(offset).limit(per_page).all()

    return {
        "data": [_serialize_usage(u) for u in usages],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def get_usage(usage_id):
    """
    获取单条使用记录。

    Returns:
        dict: 序列化后的使用记录
    """
    usage = _get_usage_raw(usage_id)
    return _serialize_usage(usage)


def delete_usage(usage_id):
    """
    删除使用记录，同时 GlobalAsset.usage_count -= 1。

    Returns:
        bool: True if deleted
    """
    usage = _get_usage_raw(usage_id)
    asset_id = usage.asset_id

    try:
        db.session.delete(usage)

        # Decrement usage_count on the global asset
        asset = GlobalAsset.get(asset_id)
        if asset is not None:
            asset.usage_count = max((asset.usage_count or 0) - 1, 0)
            asset.updated_at = date_helpers.get_utc_now_datetime()

        db.session.commit()
    except BaseException:
        db.session.rollback()
        db.session.remove()
        raise

    return True


def get_asset_usage_stats(asset_id):
    """
    资产使用统计。

    Returns:
        dict: {
            total_usages, projects_count,
            usage_by_type: {direct: N, ...},
            usage_by_project: [{project_id, project_name, count}, ...],
            recent_usages: [...]
        }
    """
    _get_asset_raw(asset_id)  # validate

    # Total usages
    total_usages = (
        AssetUsage.query()
        .filter(AssetUsage.asset_id == asset_id)
        .count()
    )

    # Distinct projects count
    projects_count = (
        db.session.query(func.count(func.distinct(AssetUsage.project_id)))
        .filter(AssetUsage.asset_id == asset_id)
        .scalar()
    ) or 0

    # Usage by type
    type_rows = (
        db.session.query(
            AssetUsage.usage_type,
            func.count(AssetUsage.id),
        )
        .filter(AssetUsage.asset_id == asset_id)
        .group_by(AssetUsage.usage_type)
        .all()
    )
    usage_by_type = {}
    for usage_type, count in type_rows:
        key = usage_type[0] if isinstance(usage_type, tuple) else str(usage_type)
        usage_by_type[key] = count

    # Usage by project
    project_rows = (
        db.session.query(
            AssetUsage.project_id,
            func.count(AssetUsage.id).label("count"),
        )
        .filter(AssetUsage.asset_id == asset_id)
        .group_by(AssetUsage.project_id)
        .order_by(desc("count"))
        .all()
    )
    usage_by_project = []
    for project_id, count in project_rows:
        project = Project.get(project_id)
        usage_by_project.append({
            "project_id": str(project_id),
            "project_name": project.name if project else "Unknown",
            "count": count,
        })

    # Recent usages (last 10)
    recent = (
        AssetUsage.query()
        .filter(AssetUsage.asset_id == asset_id)
        .order_by(AssetUsage.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_usages": total_usages,
        "projects_count": projects_count,
        "usage_by_type": usage_by_type,
        "usage_by_project": usage_by_project,
        "recent_usages": [_serialize_usage(u) for u in recent],
    }


def get_most_used_assets(limit=20):
    """
    获取最常用资产排行（按 usage_count 降序）。

    Args:
        limit: 返回数量（默认 20）

    Returns:
        list[dict]: 资产列表（含 usage_count）
    """
    if limit > 100:
        limit = 100

    assets = (
        GlobalAsset.query()
        .filter(GlobalAsset.usage_count > 0)
        .order_by(GlobalAsset.usage_count.desc())
        .limit(limit)
        .all()
    )

    results = []
    for asset in assets:
        data = asset.serialize()
        if isinstance(data.get("status"), tuple):
            data["status"] = data["status"][0]
        if asset.category_rel:
            data["category"] = asset.category_rel.serialize()
        results.append(data)

    return results


def get_usage_timeline(asset_id):
    """
    获取资产使用时间线（按月聚合）。

    Returns:
        list[dict]: [{month: "2026-03", count: N}, ...]
    """
    _get_asset_raw(asset_id)  # validate

    rows = (
        db.session.query(
            func.to_char(AssetUsage.created_at, "YYYY-MM").label("month"),
            func.count(AssetUsage.id).label("count"),
        )
        .filter(AssetUsage.asset_id == asset_id)
        .group_by("month")
        .order_by("month")
        .all()
    )

    return [{"month": row.month, "count": row.count} for row in rows]


def get_cross_project_usage(asset_id):
    """
    获取跨项目使用情况。

    Returns:
        list[dict]: [{
            project_id, project_name, usage_count,
            last_used, usage_types
        }]
    """
    _get_asset_raw(asset_id)  # validate

    # Get per-project aggregated data
    project_rows = (
        db.session.query(
            AssetUsage.project_id,
            func.count(AssetUsage.id).label("usage_count"),
            func.max(AssetUsage.created_at).label("last_used"),
        )
        .filter(AssetUsage.asset_id == asset_id)
        .group_by(AssetUsage.project_id)
        .order_by(desc("usage_count"))
        .all()
    )

    # Get usage types per project
    type_rows = (
        db.session.query(
            AssetUsage.project_id,
            AssetUsage.usage_type,
        )
        .filter(AssetUsage.asset_id == asset_id)
        .distinct()
        .all()
    )
    project_types = defaultdict(set)
    for project_id, usage_type in type_rows:
        key = usage_type[0] if isinstance(usage_type, tuple) else str(usage_type)
        project_types[str(project_id)].add(key)

    results = []
    for project_id, usage_count, last_used in project_rows:
        project = Project.get(project_id)
        results.append({
            "project_id": str(project_id),
            "project_name": project.name if project else "Unknown",
            "usage_count": usage_count,
            "last_used": str(last_used) if last_used else None,
            "usage_types": sorted(project_types.get(str(project_id), [])),
        })

    return results


def batch_record_usage(usages):
    """
    批量记录使用（导入用）。

    Args:
        usages: list[dict] — 每个 dict 包含:
            asset_id, project_id, 以及可选的
            used_by_id, usage_type, entity_id, entity_type, context

    Returns:
        dict: {recorded: int, errors: list}
    """
    recorded = 0
    errors = []

    # Collect asset_id -> increment count
    asset_increments = defaultdict(int)

    try:
        for i, usage_data in enumerate(usages):
            asset_id = usage_data.get("asset_id")
            project_id = usage_data.get("project_id")

            if not asset_id or not project_id:
                errors.append({
                    "index": i,
                    "error": "asset_id and project_id are required.",
                })
                continue

            usage = AssetUsage.create_no_commit(
                asset_id=asset_id,
                project_id=project_id,
                used_by_id=usage_data.get("used_by_id"),
                usage_type=usage_data.get("usage_type", "direct"),
                entity_id=usage_data.get("entity_id"),
                entity_type=usage_data.get("entity_type"),
                context=usage_data.get("context"),
            )
            asset_increments[asset_id] += 1
            recorded += 1

        # Batch update usage_count for all affected assets
        for asset_id, increment in asset_increments.items():
            asset = GlobalAsset.get(asset_id)
            if asset is not None:
                asset.usage_count = (asset.usage_count or 0) + increment
                asset.updated_at = date_helpers.get_utc_now_datetime()

        db.session.commit()
    except BaseException:
        db.session.rollback()
        db.session.remove()
        raise

    return {
        "recorded": recorded,
        "errors": errors,
    }
