"""
资产版本管理服务

提供资产版本的创建、查询、对比和恢复功能。
每次资产变更时自动创建版本快照，支持版本回退。
"""

import copy
import logging

from zou.app import db
from zou.app.models.asset_version import AssetVersion
from zou.app.models.global_asset import GlobalAsset
from zou.app.services.exception import WrongParameterException
from zou.app.utils import date_helpers

logger = logging.getLogger(__name__)

# Fields excluded from diff comparison (audit timestamps)
_IGNORED_DIFF_FIELDS = {"created_at", "updated_at", "id", "type"}

# Fields to include in asset snapshot
_SNAPSHOT_FIELDS = [
    "name",
    "description",
    "category_id",
    "tags",
    "files",
    "metadata",
    "style_keywords",
    "prompt_text",
    "status",
    "thumbnail_preview_file_id",
    "usage_count",
    "version",
    "source_project_id",
    "creator_id",
]


class AssetVersionNotFoundException(Exception):
    pass


def create_version(
    asset_id, author_id=None, change_summary=None, change_type="update"
):
    """
    创建新版本。

    1. 获取当前资产完整数据作为 snapshot
    2. 获取上一版本的 snapshot（如果有）
    3. 计算 diff（对比两个 snapshot）
    4. version_number = 上一版本 + 1（首次为 1）
    5. 保存 AssetVersion

    Args:
        asset_id: 资产 ID
        author_id: 创建者 ID
        change_summary: 变更说明
        change_type: 变更类型

    Returns:
        dict: 序列化后的版本记录
    """
    asset = GlobalAsset.get(asset_id)
    if asset is None:
        raise WrongParameterException("Asset not found.")

    # Build snapshot from current asset state
    snapshot = _serialize_asset_snapshot(asset)
    files_snapshot = copy.deepcopy(snapshot.get("files", []))

    # Get previous version for diff and version number
    latest = _get_latest_version_record(asset_id)
    if latest is not None:
        version_number = latest.version_number + 1
        old_snapshot = latest.snapshot or {}
        diff = _compute_diff(old_snapshot, snapshot)
    else:
        version_number = 1
        diff = {}

    version = AssetVersion.create(
        asset_id=asset_id,
        version_number=version_number,
        snapshot=snapshot,
        change_summary=change_summary,
        change_type=change_type,
        diff=diff,
        author_id=author_id,
        files_snapshot=files_snapshot,
    )

    return _serialize_version(version)


def get_versions(asset_id, page=1, per_page=20):
    """
    获取资产的版本历史（分页，倒序）。

    Returns:
        dict: {data, total, page, per_page, pages}
    """
    query = (
        AssetVersion.query()
        .filter(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version_number.desc())
    )

    total = query.count()
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    offset = (page - 1) * per_page
    versions = query.offset(offset).limit(per_page).all()

    return {
        "data": [_serialize_version(v) for v in versions],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def get_version(version_id):
    """
    获取版本详情。

    Raises:
        AssetVersionNotFoundException: 版本不存在
    """
    version = AssetVersion.get(version_id)
    if version is None:
        raise AssetVersionNotFoundException()
    return _serialize_version(version)


def get_version_diff(version_id):
    """
    获取版本差异详情。

    Returns:
        dict: {
            fields_changed: [...],
            diff: {field: {old, new}},
            files_added: [],
            files_removed: [],
        }
    """
    version = AssetVersion.get(version_id)
    if version is None:
        raise AssetVersionNotFoundException()

    diff = version.diff or {}
    fields_changed = list(diff.keys())

    # Extract file changes if present
    files_diff = diff.get("files", {})
    files_added = files_diff.get("added", []) if isinstance(files_diff, dict) else []
    files_removed = (
        files_diff.get("removed", []) if isinstance(files_diff, dict) else []
    )

    return {
        "version_id": str(version.id),
        "version_number": version.version_number,
        "fields_changed": fields_changed,
        "diff": diff,
        "files_added": files_added,
        "files_removed": files_removed,
    }


def compare_versions(version_id_a, version_id_b):
    """
    对比两个版本。

    Returns:
        dict: {
            version_a: {version_number, snapshot, ...},
            version_b: {version_number, snapshot, ...},
            diff: {field: {a: ..., b: ...}},
        }
    """
    va = AssetVersion.get(version_id_a)
    vb = AssetVersion.get(version_id_b)
    if va is None or vb is None:
        raise AssetVersionNotFoundException()

    snapshot_a = va.snapshot or {}
    snapshot_b = vb.snapshot or {}

    diff = {}
    all_keys = set(snapshot_a.keys()) | set(snapshot_b.keys())
    for key in all_keys:
        if key in _IGNORED_DIFF_FIELDS:
            continue
        val_a = snapshot_a.get(key)
        val_b = snapshot_b.get(key)
        if val_a != val_b:
            diff[key] = {"a": val_a, "b": val_b}

    return {
        "version_a": _serialize_version(va),
        "version_b": _serialize_version(vb),
        "diff": diff,
    }


def restore_version(asset_id, version_id, author_id=None):
    """
    恢复到指定版本。

    1. 获取目标版本的 snapshot
    2. 用 snapshot 更新当前资产
    3. 创建新版本（change_type='restore'）

    Returns:
        dict: 新创建的恢复版本
    """
    target_version = AssetVersion.get(version_id)
    if target_version is None:
        raise AssetVersionNotFoundException()

    if str(target_version.asset_id) != str(asset_id):
        raise WrongParameterException(
            "Version does not belong to the specified asset."
        )

    asset = GlobalAsset.get(asset_id)
    if asset is None:
        raise WrongParameterException("Asset not found.")

    snapshot = target_version.snapshot or {}

    # Restore asset fields from snapshot
    restorable_fields = [
        "name",
        "description",
        "category_id",
        "tags",
        "files",
        "style_keywords",
        "prompt_text",
        "status",
        "thumbnail_preview_file_id",
    ]

    for field in restorable_fields:
        if field in snapshot:
            if field == "status":
                # ChoiceType needs the code string
                setattr(asset, field, snapshot[field])
            else:
                setattr(asset, field, snapshot[field])

    # Handle metadata_ mapping
    if "metadata" in snapshot:
        asset.metadata_ = snapshot["metadata"]

    asset.updated_at = date_helpers.get_utc_now_datetime()
    db.session.commit()

    # Create a new version recording the restore
    change_summary = (
        f"恢复到版本 v{target_version.version_number}"
    )
    return create_version(
        asset_id,
        author_id=author_id,
        change_summary=change_summary,
        change_type="restore",
    )


def get_latest_version(asset_id):
    """获取最新版本。"""
    version = _get_latest_version_record(asset_id)
    if version is None:
        return None
    return _serialize_version(version)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_latest_version_record(asset_id):
    """Get the latest AssetVersion ORM instance for an asset."""
    return (
        AssetVersion.query()
        .filter(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version_number.desc())
        .first()
    )


def _serialize_asset_snapshot(asset):
    """
    将资产序列化为快照 JSON。
    只保存资产自身字段，不包含关联数据（避免膨胀）。
    """
    snapshot = {}
    for field in _SNAPSHOT_FIELDS:
        if field == "metadata":
            # metadata_ is the actual column attribute
            val = asset.metadata_
        elif field == "status":
            val = asset.status
            # ChoiceType returns tuple; extract code
            if isinstance(val, tuple):
                val = val[0]
            elif hasattr(val, "value"):
                val = val.value
        else:
            val = getattr(asset, field, None)

        # Convert UUID to string for JSON serialization
        if hasattr(val, "hex"):
            val = str(val)

        snapshot[field] = val

    return snapshot


def _compute_diff(old_snapshot, new_snapshot):
    """
    计算两个快照的差异。

    比较所有字段，忽略 updated_at/created_at。
    特殊处理：
    - tags/style_keywords: 数组差异（added/removed）
    - files: 文件列表差异
    - metadata: JSON 深度差异
    """
    diff = {}
    all_keys = set(old_snapshot.keys()) | set(new_snapshot.keys())

    for key in all_keys:
        if key in _IGNORED_DIFF_FIELDS:
            continue

        old_val = old_snapshot.get(key)
        new_val = new_snapshot.get(key)

        if old_val == new_val:
            continue

        # Array fields: compute added/removed
        if key in ("tags", "style_keywords"):
            old_set = set(old_val) if isinstance(old_val, list) else set()
            new_set = set(new_val) if isinstance(new_val, list) else set()
            diff[key] = {
                "old": old_val,
                "new": new_val,
                "added": list(new_set - old_set),
                "removed": list(old_set - new_set),
            }
        elif key == "files":
            diff[key] = _compute_files_diff(old_val, new_val)
        elif key == "metadata":
            diff[key] = _compute_deep_diff(old_val, new_val)
        else:
            diff[key] = {"old": old_val, "new": new_val}

    return diff


def _compute_files_diff(old_files, new_files):
    """Compute diff for file lists."""
    old_list = old_files if isinstance(old_files, list) else []
    new_list = new_files if isinstance(new_files, list) else []

    # Extract file identifiers for comparison
    def _file_key(f):
        if isinstance(f, dict):
            return f.get("id") or f.get("name") or str(f)
        return str(f)

    old_keys = {_file_key(f) for f in old_list}
    new_keys = {_file_key(f) for f in new_list}

    added = [f for f in new_list if _file_key(f) not in old_keys]
    removed = [f for f in old_list if _file_key(f) not in new_keys]

    return {
        "old": old_list,
        "new": new_list,
        "added": added,
        "removed": removed,
    }


def _compute_deep_diff(old_val, new_val):
    """
    Compute a deep diff for nested dicts (metadata).
    Returns {old, new, changed_keys: {key: {old, new}}}.
    """
    result = {"old": old_val, "new": new_val}

    if isinstance(old_val, dict) and isinstance(new_val, dict):
        changed_keys = {}
        all_keys = set(old_val.keys()) | set(new_val.keys())
        for k in all_keys:
            ov = old_val.get(k)
            nv = new_val.get(k)
            if ov != nv:
                changed_keys[k] = {"old": ov, "new": nv}
        if changed_keys:
            result["changed_keys"] = changed_keys

    return result


def _serialize_version(version):
    """Serialize an AssetVersion model instance to dict."""
    if version is None:
        return None
    result = version.serialize()
    # ChoiceType returns tuple for change_type; extract code
    if isinstance(result.get("change_type"), tuple):
        result["change_type"] = result["change_type"][0]
    return result
