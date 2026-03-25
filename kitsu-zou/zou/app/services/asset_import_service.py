"""
资产导入服务

提供全局资产的 ZIP/JSON 批量导入功能，支持合并、跳过、覆盖、新建模式。
"""

import json
import logging
import os
import tempfile
import zipfile

from zou.app import db, app
from zou.app.models.asset_category import AssetCategory
from zou.app.models.global_asset import GlobalAsset
from zou.app.utils import date_helpers

logger = logging.getLogger(__name__)

SUPPORTED_EXPORT_VERSIONS = ["1.0"]


def validate_import_zip(zip_path):
    """
    验证 ZIP 包格式。

    检查: manifest.json 存在、版本兼容、assets/ 目录存在、JSON 格式正确。

    Returns:
        dict: { valid, errors, asset_count, manifest }
    """
    errors = []
    manifest = None
    asset_count = 0

    if not os.path.isfile(zip_path):
        return {"valid": False, "errors": ["File not found."], "asset_count": 0, "manifest": None}

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()

            # Check manifest.json
            if "manifest.json" not in names:
                errors.append("Missing manifest.json in ZIP root.")
            else:
                try:
                    manifest_data = zf.read("manifest.json")
                    manifest = json.loads(manifest_data)
                    export_version = manifest.get("export_version")
                    if export_version not in SUPPORTED_EXPORT_VERSIONS:
                        errors.append(
                            f"Unsupported export version: {export_version}. "
                            f"Supported: {', '.join(SUPPORTED_EXPORT_VERSIONS)}"
                        )
                except (json.JSONDecodeError, ValueError) as e:
                    errors.append(f"Invalid manifest.json: {e}")

            # Check assets/ directory
            asset_files = [n for n in names if n.startswith("assets/") and n.endswith(".json")]
            if not asset_files:
                errors.append("No asset JSON files found in assets/ directory.")
            else:
                asset_count = len(asset_files)
                # Validate each asset JSON
                for af in asset_files:
                    try:
                        data = zf.read(af)
                        asset_data = json.loads(data)
                        if not asset_data.get("name"):
                            errors.append(f"{af}: missing 'name' field.")
                    except (json.JSONDecodeError, ValueError) as e:
                        errors.append(f"{af}: invalid JSON — {e}")

    except zipfile.BadZipFile:
        errors.append("File is not a valid ZIP archive.")
        return {"valid": False, "errors": errors, "asset_count": 0, "manifest": None}

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "asset_count": asset_count,
        "manifest": manifest,
    }


def preview_import(zip_path):
    """
    预览导入内容（不实际执行）。

    Returns:
        dict: { assets: [{ name, category, status, action }], categories: [...] }
    """
    validation = validate_import_zip(zip_path)
    if not validation["valid"]:
        return {"assets": [], "categories": [], "errors": validation["errors"]}

    preview_assets = []
    preview_categories = set()

    with zipfile.ZipFile(zip_path, "r") as zf:
        asset_files = [n for n in zf.namelist() if n.startswith("assets/") and n.endswith(".json")]

        for af in asset_files:
            try:
                data = json.loads(zf.read(af))
                name = data.get("name", "")
                category_slug = data.get("category_slug", "")
                category_name = data.get("category_name", "")

                # Determine action by checking existing match
                existing = _find_existing_asset(name, category_slug)
                action = "update" if existing else "create"

                preview_assets.append({
                    "name": name,
                    "category": category_name or category_slug,
                    "status": data.get("status", "draft"),
                    "action": action,
                })

                if category_slug:
                    preview_categories.add(category_slug)
            except Exception as e:
                logger.warning("Failed to preview %s: %s", af, e)

    # Check which categories need creation
    new_categories = []
    for slug in preview_categories:
        cat = AssetCategory.query.filter_by(slug=slug).first()
        if not cat:
            new_categories.append(slug)

    return {
        "assets": preview_assets,
        "categories": list(preview_categories),
        "new_categories": new_categories,
    }


def import_from_zip(zip_path, mode="merge", author_id=None):
    """
    从 ZIP 包导入资产。

    Args:
        zip_path: ZIP 文件路径
        mode:
            'merge' — 同名资产更新，新资产创建
            'skip' — 同名资产跳过，只创建新的
            'overwrite' — 同名资产覆盖
            'create_new' — 全部作为新资产创建（忽略 ID）
        author_id: 导入者 ID

    Returns:
        dict: { total, created, updated, skipped, errors, categories_created }
    """
    valid_modes = ["merge", "skip", "overwrite", "create_new"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode. Must be one of: {', '.join(valid_modes)}")

    validation = validate_import_zip(zip_path)
    if not validation["valid"]:
        return {
            "total": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [{"asset_name": "ZIP", "error": e} for e in validation["errors"]],
            "categories_created": 0,
        }

    created = 0
    updated = 0
    skipped = 0
    errors = []
    categories_created = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Load categories first
        categories_data = []
        if "categories/categories.json" in zf.namelist():
            try:
                categories_data = json.loads(zf.read("categories/categories.json"))
            except Exception as e:
                logger.warning("Failed to load categories: %s", e)

        # Ensure categories exist
        for cat_data in categories_data:
            cat, was_created = _resolve_category(cat_data)
            if was_created:
                categories_created += 1

        # Process assets
        asset_files = [
            n for n in zf.namelist()
            if n.startswith("assets/") and n.endswith(".json")
        ]

        for af in asset_files:
            try:
                asset_data = json.loads(zf.read(af))
                name = asset_data.get("name", "")
                result = _import_single_asset(asset_data, mode, author_id)

                if result == "created":
                    created += 1
                elif result == "updated":
                    updated += 1
                elif result == "skipped":
                    skipped += 1
            except Exception as e:
                asset_name = asset_data.get("name", af) if "asset_data" in dir() else af
                errors.append({"asset_name": str(asset_name), "error": str(e)})
                logger.warning("Failed to import %s: %s", af, e)

    db.session.commit()

    total = created + updated + skipped + len(errors)
    return {
        "total": total,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "categories_created": categories_created,
    }


def import_from_json(json_data, author_id=None):
    """
    从 JSON 数据直接导入单个/多个资产（API 批量创建用）。

    Args:
        json_data: list of asset dicts, or single asset dict
        author_id: 导入者 ID

    Returns:
        dict: { total, created, updated, skipped, errors, categories_created }
    """
    if isinstance(json_data, dict):
        json_data = [json_data]

    created = 0
    updated = 0
    skipped = 0
    errors = []
    categories_created = 0

    for asset_data in json_data:
        try:
            # Resolve category if provided
            if asset_data.get("category_slug"):
                cat_info = {
                    "slug": asset_data["category_slug"],
                    "name": asset_data.get("category_name", asset_data["category_slug"]),
                }
                cat, was_created = _resolve_category(cat_info)
                if was_created:
                    categories_created += 1
                asset_data["category_id"] = str(cat.id)

            result = _import_single_asset(asset_data, mode="merge", author_id=author_id)
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
            elif result == "skipped":
                skipped += 1
        except Exception as e:
            errors.append({
                "asset_name": asset_data.get("name", "unknown"),
                "error": str(e),
            })

    db.session.commit()

    return {
        "total": created + updated + skipped + len(errors),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "categories_created": categories_created,
    }


def _import_single_asset(asset_data, mode, author_id=None):
    """
    导入单个资产，根据 mode 决定行为。

    Returns:
        str: 'created' | 'updated' | 'skipped'
    """
    name = asset_data.get("name", "")
    category_slug = asset_data.get("category_slug")
    category_id = asset_data.get("category_id")

    # Resolve category_id from slug if not directly provided
    if not category_id and category_slug:
        cat = AssetCategory.query.filter_by(slug=category_slug).first()
        if cat:
            category_id = str(cat.id)

    if not category_id:
        raise ValueError(f"No category found for asset '{name}'.")

    existing = _match_existing_asset(asset_data, mode)

    if mode == "create_new" or existing is None:
        # Create new asset
        asset = GlobalAsset.create(
            name=name,
            category_id=category_id,
            creator_id=author_id,
            description=asset_data.get("description", ""),
            tags=asset_data.get("tags", []),
            files=asset_data.get("files", []),
            metadata_=asset_data.get("metadata", asset_data.get("metadata_", {})),
            style_keywords=asset_data.get("style_keywords", []),
            prompt_text=asset_data.get("prompt_text", ""),
            source_project_id=asset_data.get("source_project_id"),
            thumbnail_preview_file_id=asset_data.get("thumbnail_preview_file_id"),
            version=1,
            status="draft",
            usage_count=0,
        )
        return "created"

    if mode == "skip":
        return "skipped"

    # mode == 'merge' or 'overwrite': update existing
    _update_asset_from_data(existing, asset_data, mode)
    return "updated"


def _update_asset_from_data(asset, data, mode):
    """
    从导入数据更新现有资产。

    merge: 只更新非空字段
    overwrite: 覆盖所有字段
    """
    updatable_fields = {
        "description": "description",
        "tags": "tags",
        "files": "files",
        "style_keywords": "style_keywords",
        "prompt_text": "prompt_text",
    }

    for data_key, model_attr in updatable_fields.items():
        value = data.get(data_key)
        if mode == "overwrite":
            setattr(asset, model_attr, value if value is not None else getattr(asset, model_attr))
        elif mode == "merge":
            if value:  # Only update non-empty values
                setattr(asset, model_attr, value)

    # Handle metadata separately (uses metadata_ in model)
    metadata_val = data.get("metadata", data.get("metadata_"))
    if mode == "overwrite" and metadata_val is not None:
        asset.metadata_ = metadata_val
    elif mode == "merge" and metadata_val:
        asset.metadata_ = metadata_val

    asset.updated_at = date_helpers.get_utc_now_datetime()


def _resolve_category(category_data):
    """
    解析分类：按 slug 匹配现有分类，不存在则创建。

    Returns:
        tuple: (AssetCategory, was_created: bool)
    """
    slug = category_data.get("slug")
    if not slug:
        raise ValueError("Category slug is required.")

    existing = AssetCategory.query.filter_by(slug=slug).first()
    if existing:
        return existing, False

    # Create the category
    cat = AssetCategory.create(
        name=category_data.get("name", slug),
        name_en=category_data.get("name_en"),
        slug=slug,
        description=category_data.get("description", ""),
        icon=category_data.get("icon"),
        color=category_data.get("color"),
        parent_id=category_data.get("parent_id"),
        sort_order=category_data.get("sort_order", 0),
        is_system=False,
        is_active=True,
    )
    logger.info("Created category '%s' (%s) during import.", cat.name, cat.slug)
    return cat, True


def _match_existing_asset(asset_data, mode):
    """
    匹配现有资产：按 name + category_slug 或 name + category_id 匹配。

    Returns:
        GlobalAsset or None
    """
    if mode == "create_new":
        return None

    name = asset_data.get("name")
    category_slug = asset_data.get("category_slug")
    category_id = asset_data.get("category_id")

    query = GlobalAsset.query().filter(GlobalAsset.name == name)

    if category_id:
        query = query.filter(GlobalAsset.category_id == category_id)
    elif category_slug:
        cat = AssetCategory.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter(GlobalAsset.category_id == cat.id)

    return query.first()


def _find_existing_asset(name, category_slug):
    """
    查找现有资产（用于预览）。

    Returns:
        GlobalAsset or None
    """
    if not name:
        return None

    query = GlobalAsset.query().filter(GlobalAsset.name == name)
    if category_slug:
        cat = AssetCategory.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter(GlobalAsset.category_id == cat.id)

    return query.first()
