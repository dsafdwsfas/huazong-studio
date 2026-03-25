"""
资产导出服务

提供全局资产的 ZIP 打包导出功能，支持按选择、分类、项目导出。
"""

import json
import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime

from zou.app import db, app
from zou.app.models.asset_category import AssetCategory
from zou.app.models.global_asset import (
    GlobalAsset,
    GlobalAssetProjectLink,
)

logger = logging.getLogger(__name__)

EXPORT_VERSION = "1.0"


def export_assets(asset_ids, include_files=False, include_versions=False):
    """
    导出选中的资产为 ZIP 包。

    ZIP 结构:
    export_YYYYMMDD_HHMMSS.zip
    ├── manifest.json          # 导出清单
    ├── assets/
    │   └── {asset_id}.json    # 每个资产的完整数据
    ├── categories/
    │   └── categories.json    # 涉及的分类数据
    └── versions/              # (可选) 版本历史
        └── {asset_id}_versions.json

    Args:
        asset_ids: 要导出的资产 ID 列表
        include_files: 是否包含关联文件（预留，暂不实现 COS 下载）
        include_versions: 是否包含版本历史

    Returns:
        dict: { zip_path, filename, size_bytes, asset_count }
    """
    if not asset_ids:
        return {"zip_path": None, "filename": None, "size_bytes": 0, "asset_count": 0}

    assets = GlobalAsset.query().filter(GlobalAsset.id.in_(asset_ids)).all()
    if not assets:
        return {"zip_path": None, "filename": None, "size_bytes": 0, "asset_count": 0}

    return _build_export_zip(assets, include_files, include_versions)


def export_all_assets(include_files=False):
    """导出全部资产。"""
    assets = GlobalAsset.query().order_by(GlobalAsset.name.asc()).all()
    return _build_export_zip(assets, include_files, include_versions=False)


def export_by_category(category_id, include_files=False):
    """按分类导出。"""
    assets = (
        GlobalAsset.query()
        .filter(GlobalAsset.category_id == category_id)
        .order_by(GlobalAsset.name.asc())
        .all()
    )
    return _build_export_zip(assets, include_files, include_versions=False)


def export_by_project(project_id, include_files=False):
    """按项目导出关联资产。"""
    assets = (
        GlobalAsset.query()
        .join(
            GlobalAssetProjectLink,
            GlobalAsset.id == GlobalAssetProjectLink.global_asset_id,
        )
        .filter(GlobalAssetProjectLink.project_id == project_id)
        .order_by(GlobalAsset.name.asc())
        .all()
    )
    return _build_export_zip(assets, include_files, include_versions=False)


def _build_export_zip(assets, include_files=False, include_versions=False):
    """
    构建导出 ZIP 文件。

    Returns:
        dict: { zip_path, filename, size_bytes, asset_count }
    """
    tmp_dir = app.config.get("TMP_DIR", tempfile.gettempdir())
    os.makedirs(tmp_dir, exist_ok=True)
    export_dir = tempfile.mkdtemp(dir=tmp_dir, prefix="asset_export_")

    try:
        # Collect category IDs from assets
        category_ids = set()
        asset_data_list = []
        for asset in assets:
            serialized = _serialize_asset_for_export(asset)
            asset_data_list.append(serialized)
            if asset.category_id:
                category_ids.add(str(asset.category_id))

        # Write asset JSON files
        assets_dir = os.path.join(export_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        for data in asset_data_list:
            asset_path = os.path.join(assets_dir, f"{data['id']}.json")
            with open(asset_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        # Write categories
        categories_dir = os.path.join(export_dir, "categories")
        os.makedirs(categories_dir, exist_ok=True)
        categories_data = _export_categories(category_ids)
        cat_path = os.path.join(categories_dir, "categories.json")
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(categories_data, f, ensure_ascii=False, indent=2, default=str)

        # Write version histories (optional)
        if include_versions:
            versions_dir = os.path.join(export_dir, "versions")
            os.makedirs(versions_dir, exist_ok=True)
            _export_versions(assets, versions_dir)

        # Create manifest
        manifest = _create_manifest(
            asset_count=len(assets),
            categories=categories_data,
            options={
                "include_files": include_files,
                "include_versions": include_versions,
            },
        )
        manifest_path = os.path.join(export_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)

        # Create ZIP
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.zip"
        zip_path = os.path.join(tmp_dir, filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zf.write(file_path, arcname)

        size_bytes = os.path.getsize(zip_path)

        return {
            "zip_path": zip_path,
            "filename": filename,
            "size_bytes": size_bytes,
            "asset_count": len(assets),
        }
    finally:
        # Clean up the temporary export directory (not the zip)
        shutil.rmtree(export_dir, ignore_errors=True)


def _serialize_asset_for_export(asset):
    """
    将资产序列化为导出 JSON，包含冗余信息便于导入。
    """
    result = asset.serialize()

    # ChoiceType returns tuple for status; extract the code value
    if isinstance(result.get("status"), tuple):
        result["status"] = result["status"][0]

    # Include category details for import resolution
    if asset.category_rel:
        cat = asset.category_rel
        result["category_name"] = cat.name
        result["category_slug"] = cat.slug
        result["category_name_en"] = cat.name_en

    # Include creator info if available
    if asset.creator_id:
        try:
            from zou.app.services import persons_service

            person = persons_service.get_person(str(asset.creator_id))
            result["creator_name"] = (
                f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
            )
        except Exception:
            result["creator_name"] = None

    # Include linked project IDs
    links = GlobalAssetProjectLink.query.filter_by(
        global_asset_id=asset.id
    ).all()
    result["linked_project_ids"] = [str(l.project_id) for l in links]

    return result


def _export_categories(category_ids):
    """导出涉及的分类数据。"""
    if not category_ids:
        return []
    categories = AssetCategory.query.filter(
        AssetCategory.id.in_(list(category_ids))
    ).all()
    return [cat.serialize() for cat in categories]


def _export_versions(assets, versions_dir):
    """导出资产版本历史。"""
    try:
        from zou.app.services import asset_version_service

        for asset in assets:
            versions = asset_version_service.get_versions_for_asset(
                str(asset.id)
            )
            if versions:
                version_path = os.path.join(
                    versions_dir, f"{asset.id}_versions.json"
                )
                with open(version_path, "w", encoding="utf-8") as f:
                    json.dump(
                        versions, f, ensure_ascii=False, indent=2, default=str
                    )
    except Exception as e:
        logger.warning("Failed to export versions: %s", e)


def _create_manifest(asset_count, categories, options):
    """创建导出清单。"""
    return {
        "export_version": EXPORT_VERSION,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "source": "huazong-studio",
        "asset_count": asset_count,
        "category_count": len(categories),
        "options": options,
    }
