"""
Asset statistics aggregation service (Phase 4.7).

Provides dashboard-level statistics, category distribution, usage frequency,
storage analysis, hotness ranking, growth trends, and creator analytics.
All queries use SQL aggregation (GROUP BY / COUNT / SUM) to avoid N+1.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, desc, cast, Integer, extract, case, text
from sqlalchemy.dialects.postgresql import JSONB

from zou.app import db
from zou.app.models.global_asset import GlobalAsset, GlobalAssetProjectLink
from zou.app.models.asset_category import AssetCategory
from zou.app.models.asset_usage import AssetUsage
from zou.app.models.asset_version import AssetVersion
from zou.app.models.asset_node import AssetNode, AssetNodeLink
from zou.app.models.person import Person

logger = logging.getLogger(__name__)


def get_dashboard_stats():
    """
    Dashboard overview stats: totals, status breakdown, recent assets,
    and most active creators.
    """
    total_assets = db.session.query(func.count(GlobalAsset.id)).scalar() or 0
    total_categories = (
        db.session.query(func.count(AssetCategory.id)).scalar() or 0
    )
    total_usages = (
        db.session.query(func.count(AssetUsage.id)).scalar() or 0
    )
    total_versions = (
        db.session.query(func.count(AssetVersion.id)).scalar() or 0
    )
    total_graph_nodes = (
        db.session.query(func.count(AssetNode.id)).scalar() or 0
    )
    total_graph_links = (
        db.session.query(func.count(AssetNodeLink.id)).scalar() or 0
    )

    # Assets by status
    status_rows = (
        db.session.query(
            GlobalAsset.status,
            func.count(GlobalAsset.id),
        )
        .group_by(GlobalAsset.status)
        .all()
    )
    assets_by_status = {"draft": 0, "reviewed": 0, "archived": 0}
    for row in status_rows:
        status_val = row[0]
        # ChoiceType may return a tuple (code, label)
        if isinstance(status_val, tuple):
            status_val = status_val[0]
        elif hasattr(status_val, "value"):
            status_val = status_val.value
        if status_val in assets_by_status:
            assets_by_status[status_val] = row[1]

    # Recent assets (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_rows = (
        db.session.query(
            GlobalAsset.id,
            GlobalAsset.name,
            GlobalAsset.status,
            GlobalAsset.created_at,
            AssetCategory.name.label("category_name"),
        )
        .outerjoin(AssetCategory, GlobalAsset.category_id == AssetCategory.id)
        .filter(GlobalAsset.created_at >= seven_days_ago)
        .order_by(desc(GlobalAsset.created_at))
        .limit(10)
        .all()
    )
    recent_assets = []
    for r in recent_rows:
        status_val = r.status
        if isinstance(status_val, tuple):
            status_val = status_val[0]
        elif hasattr(status_val, "value"):
            status_val = status_val.value
        recent_assets.append(
            {
                "id": str(r.id),
                "name": r.name,
                "status": status_val,
                "category_name": r.category_name,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )

    # Active creators (top 5)
    creator_rows = (
        db.session.query(
            GlobalAsset.creator_id,
            Person.first_name,
            Person.last_name,
            func.count(GlobalAsset.id).label("asset_count"),
        )
        .join(Person, GlobalAsset.creator_id == Person.id)
        .group_by(
            GlobalAsset.creator_id,
            Person.first_name,
            Person.last_name,
        )
        .order_by(desc("asset_count"))
        .limit(5)
        .all()
    )
    active_creators = [
        {
            "person_id": str(row.creator_id),
            "name": f"{row.first_name} {row.last_name}".strip(),
            "asset_count": row.asset_count,
        }
        for row in creator_rows
    ]

    return {
        "total_assets": total_assets,
        "total_categories": total_categories,
        "total_usages": total_usages,
        "total_versions": total_versions,
        "total_graph_nodes": total_graph_nodes,
        "total_graph_links": total_graph_links,
        "assets_by_status": assets_by_status,
        "recent_assets": recent_assets,
        "active_creators": active_creators,
    }


def get_category_distribution():
    """
    Category distribution: asset count and percentage per category,
    ordered by count descending.
    """
    rows = (
        db.session.query(
            AssetCategory.id,
            AssetCategory.name,
            AssetCategory.slug,
            AssetCategory.color,
            AssetCategory.icon,
            func.count(GlobalAsset.id).label("asset_count"),
        )
        .outerjoin(GlobalAsset, GlobalAsset.category_id == AssetCategory.id)
        .group_by(
            AssetCategory.id,
            AssetCategory.name,
            AssetCategory.slug,
            AssetCategory.color,
            AssetCategory.icon,
        )
        .order_by(desc("asset_count"))
        .all()
    )

    total = sum(r.asset_count for r in rows) or 1
    return [
        {
            "category_id": str(r.id),
            "category_name": r.name,
            "slug": r.slug,
            "color": r.color,
            "icon": r.icon,
            "asset_count": r.asset_count,
            "percentage": round(r.asset_count / total * 100, 2),
        }
        for r in rows
    ]


def get_usage_frequency_stats(period="month", months=12):
    """
    Usage frequency aggregated by month or week over the given number
    of months.
    """
    cutoff = datetime.utcnow() - timedelta(days=months * 30)

    if period == "week":
        period_expr = func.to_char(AssetUsage.created_at, "IYYY-IW")
    else:
        period_expr = func.to_char(AssetUsage.created_at, "YYYY-MM")

    rows = (
        db.session.query(
            period_expr.label("period"),
            func.count(AssetUsage.id).label("count"),
        )
        .filter(AssetUsage.created_at >= cutoff)
        .group_by(period_expr)
        .order_by(period_expr)
        .all()
    )

    return [{"period": r.period, "count": r.count} for r in rows]


def get_storage_stats():
    """
    Storage statistics derived from the JSONB `files` column on GlobalAsset.
    Each entry in `files` is expected to have optional `size` and `name` fields.
    """
    # Use a lateral JSONB unnest to extract file-level info
    # Fallback: iterate in Python for simplicity and portability
    assets = (
        db.session.query(
            GlobalAsset.id,
            GlobalAsset.name,
            GlobalAsset.files,
            GlobalAsset.category_id,
            AssetCategory.name.label("category_name"),
        )
        .outerjoin(AssetCategory, GlobalAsset.category_id == AssetCategory.id)
        .filter(GlobalAsset.files.isnot(None))
        .all()
    )

    total_files = 0
    total_size = 0
    size_by_category = {}
    size_by_type = {}
    asset_sizes = []

    for asset in assets:
        files = asset.files or []
        if not isinstance(files, list):
            continue
        asset_total = 0
        for f in files:
            if not isinstance(f, dict):
                continue
            size = f.get("size", 0) or 0
            total_files += 1
            total_size += size
            asset_total += size

            # Category aggregation
            cat_name = asset.category_name or "Uncategorized"
            size_by_category[cat_name] = (
                size_by_category.get(cat_name, 0) + size
            )

            # File type aggregation
            name = f.get("name", "") or ""
            ext = ""
            if "." in name:
                ext = name.rsplit(".", 1)[-1].lower()
            if not ext:
                ext = "unknown"
            entry = size_by_type.setdefault(ext, {"count": 0, "size_bytes": 0})
            entry["count"] += 1
            entry["size_bytes"] += size

        asset_sizes.append(
            {
                "asset_id": str(asset.id),
                "name": asset.name,
                "total_size": asset_total,
            }
        )

    # Top 10 largest assets
    asset_sizes.sort(key=lambda x: x["total_size"], reverse=True)
    largest_assets = asset_sizes[:10]

    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "size_by_category": [
            {"category": cat, "size_bytes": s}
            for cat, s in sorted(
                size_by_category.items(), key=lambda x: x[1], reverse=True
            )
        ],
        "size_by_type": [
            {"file_type": ext, "count": v["count"], "size_bytes": v["size_bytes"]}
            for ext, v in sorted(
                size_by_type.items(),
                key=lambda x: x[1]["size_bytes"],
                reverse=True,
            )
        ],
        "largest_assets": largest_assets,
    }


def get_hotness_ranking(limit=20):
    """
    Hotness ranking: usage_count * 3 + version_count * 2 + link_count * 1.
    Uses subqueries to avoid N+1.
    """
    version_sub = (
        db.session.query(
            AssetVersion.asset_id,
            func.count(AssetVersion.id).label("version_count"),
        )
        .group_by(AssetVersion.asset_id)
        .subquery()
    )

    # Count links where the asset's node is either source or target
    node_sub = (
        db.session.query(AssetNode.id, AssetNode.ref_id)
        .filter(AssetNode.node_type == "asset")
        .subquery()
    )
    link_count_sub = (
        db.session.query(
            node_sub.c.ref_id.label("asset_id"),
            func.count(AssetNodeLink.id).label("link_count"),
        )
        .outerjoin(
            AssetNodeLink,
            (AssetNodeLink.source_node_id == node_sub.c.id)
            | (AssetNodeLink.target_node_id == node_sub.c.id),
        )
        .group_by(node_sub.c.ref_id)
        .subquery()
    )

    rows = (
        db.session.query(
            GlobalAsset.id,
            GlobalAsset.name,
            GlobalAsset.usage_count,
            AssetCategory.name.label("category"),
            func.coalesce(version_sub.c.version_count, 0).label(
                "version_count"
            ),
            func.coalesce(link_count_sub.c.link_count, 0).label("link_count"),
        )
        .outerjoin(AssetCategory, GlobalAsset.category_id == AssetCategory.id)
        .outerjoin(version_sub, version_sub.c.asset_id == GlobalAsset.id)
        .outerjoin(
            link_count_sub, link_count_sub.c.asset_id == GlobalAsset.id
        )
        .order_by(
            desc(
                GlobalAsset.usage_count * 3
                + func.coalesce(version_sub.c.version_count, 0) * 2
                + func.coalesce(link_count_sub.c.link_count, 0)
            )
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "asset_id": str(r.id),
            "name": r.name,
            "category": r.category,
            "hotness_score": (
                r.usage_count * 3 + r.version_count * 2 + r.link_count
            ),
            "usage_count": r.usage_count,
            "version_count": r.version_count,
            "link_count": r.link_count,
        }
        for r in rows
    ]


def get_growth_trend(months=6):
    """
    Monthly growth trend: new assets, new usages, new versions per month.
    """
    cutoff = datetime.utcnow() - timedelta(days=months * 30)

    month_expr_asset = func.to_char(GlobalAsset.created_at, "YYYY-MM")
    month_expr_usage = func.to_char(AssetUsage.created_at, "YYYY-MM")
    month_expr_version = func.to_char(AssetVersion.created_at, "YYYY-MM")

    asset_rows = dict(
        db.session.query(
            month_expr_asset,
            func.count(GlobalAsset.id),
        )
        .filter(GlobalAsset.created_at >= cutoff)
        .group_by(month_expr_asset)
        .all()
    )

    usage_rows = dict(
        db.session.query(
            month_expr_usage,
            func.count(AssetUsage.id),
        )
        .filter(AssetUsage.created_at >= cutoff)
        .group_by(month_expr_usage)
        .all()
    )

    version_rows = dict(
        db.session.query(
            month_expr_version,
            func.count(AssetVersion.id),
        )
        .filter(AssetVersion.created_at >= cutoff)
        .group_by(month_expr_version)
        .all()
    )

    # Merge all months
    all_months = sorted(
        set(asset_rows.keys()) | set(usage_rows.keys()) | set(version_rows.keys())
    )

    return [
        {
            "month": m,
            "new_assets": asset_rows.get(m, 0),
            "new_usages": usage_rows.get(m, 0),
            "new_versions": version_rows.get(m, 0),
        }
        for m in all_months
    ]


def get_creator_stats(limit=10):
    """
    Creator statistics: asset count, usage count, and categories per creator.
    """
    # Base: creator asset counts
    creator_rows = (
        db.session.query(
            GlobalAsset.creator_id,
            Person.first_name,
            Person.last_name,
            Person.has_avatar,
            func.count(GlobalAsset.id).label("asset_count"),
        )
        .join(Person, GlobalAsset.creator_id == Person.id)
        .group_by(
            GlobalAsset.creator_id,
            Person.first_name,
            Person.last_name,
            Person.has_avatar,
        )
        .order_by(desc("asset_count"))
        .limit(limit)
        .all()
    )

    # Build lookup for usage counts per creator's assets
    creator_ids = [str(r.creator_id) for r in creator_rows]
    if creator_ids:
        usage_sub = (
            db.session.query(
                GlobalAsset.creator_id,
                func.count(AssetUsage.id).label("usage_count"),
            )
            .join(AssetUsage, AssetUsage.asset_id == GlobalAsset.id)
            .filter(GlobalAsset.creator_id.in_(creator_ids))
            .group_by(GlobalAsset.creator_id)
            .all()
        )
        usage_map = {str(r.creator_id): r.usage_count for r in usage_sub}

        # Categories per creator
        cat_sub = (
            db.session.query(
                GlobalAsset.creator_id,
                AssetCategory.name,
            )
            .join(AssetCategory, GlobalAsset.category_id == AssetCategory.id)
            .filter(GlobalAsset.creator_id.in_(creator_ids))
            .distinct()
            .all()
        )
        cat_map = {}
        for row in cat_sub:
            cid = str(row.creator_id)
            cat_map.setdefault(cid, []).append(row.name)
    else:
        usage_map = {}
        cat_map = {}

    return [
        {
            "person_id": str(r.creator_id),
            "name": f"{r.first_name} {r.last_name}".strip(),
            "has_avatar": r.has_avatar,
            "asset_count": r.asset_count,
            "usage_count": usage_map.get(str(r.creator_id), 0),
            "categories": cat_map.get(str(r.creator_id), []),
        }
        for r in creator_rows
    ]


def get_project_asset_stats(project_id):
    """
    Project-level asset statistics.
    """
    # Total assets linked to this project
    total_assets = (
        db.session.query(func.count(GlobalAssetProjectLink.global_asset_id))
        .filter(GlobalAssetProjectLink.project_id == project_id)
        .scalar()
        or 0
    )

    # By category
    by_category = (
        db.session.query(
            AssetCategory.name.label("category_name"),
            func.count(GlobalAsset.id).label("count"),
        )
        .join(
            GlobalAssetProjectLink,
            GlobalAssetProjectLink.global_asset_id == GlobalAsset.id,
        )
        .outerjoin(AssetCategory, GlobalAsset.category_id == AssetCategory.id)
        .filter(GlobalAssetProjectLink.project_id == project_id)
        .group_by(AssetCategory.name)
        .order_by(desc("count"))
        .all()
    )

    # Most used assets in this project (by AssetUsage count)
    most_used = (
        db.session.query(
            GlobalAsset.id,
            GlobalAsset.name,
            func.count(AssetUsage.id).label("usage_count"),
        )
        .join(AssetUsage, AssetUsage.asset_id == GlobalAsset.id)
        .filter(AssetUsage.project_id == project_id)
        .group_by(GlobalAsset.id, GlobalAsset.name)
        .order_by(desc("usage_count"))
        .limit(10)
        .all()
    )

    # Recent additions (last 10 linked)
    recent_additions = (
        db.session.query(
            GlobalAsset.id,
            GlobalAsset.name,
            GlobalAssetProjectLink.linked_at,
        )
        .join(
            GlobalAssetProjectLink,
            GlobalAssetProjectLink.global_asset_id == GlobalAsset.id,
        )
        .filter(GlobalAssetProjectLink.project_id == project_id)
        .order_by(desc(GlobalAssetProjectLink.linked_at))
        .limit(10)
        .all()
    )

    return {
        "total_assets": total_assets,
        "by_category": [
            {"category_name": r.category_name or "Uncategorized", "count": r.count}
            for r in by_category
        ],
        "most_used": [
            {
                "asset_id": str(r.id),
                "name": r.name,
                "usage_count": r.usage_count,
            }
            for r in most_used
        ],
        "recent_additions": [
            {
                "asset_id": str(r.id),
                "name": r.name,
                "linked_at": r.linked_at.isoformat() if r.linked_at else None,
            }
            for r in recent_additions
        ],
    }
