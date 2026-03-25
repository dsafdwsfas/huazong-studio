"""
资产导入/导出 API Resources

提供全局资产的 ZIP 导出、ZIP/JSON 导入端点。
"""

import logging
import os
import tempfile

from flask import request, send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app import app
from zou.app.services import (
    persons_service,
    projects_service,
    user_service,
)
from zou.app.services import asset_export_service
from zou.app.services import asset_import_service
from zou.app.services.exception import WrongParameterException
from zou.app.utils import permissions

logger = logging.getLogger(__name__)


class AssetExportResource(Resource):
    """
    POST /data/global-assets/export
    Body: { asset_ids: [...], include_files: false, include_versions: false }
    返回: ZIP 文件流 (Content-Type: application/zip)
    """

    @jwt_required()
    def post(self):
        data = request.json or {}
        asset_ids = data.get("asset_ids", [])
        if not asset_ids:
            raise WrongParameterException("asset_ids is required and must be non-empty.")

        include_files = data.get("include_files", False)
        include_versions = data.get("include_versions", False)

        result = asset_export_service.export_assets(
            asset_ids,
            include_files=include_files,
            include_versions=include_versions,
        )

        if not result.get("zip_path"):
            return {"message": "No assets found to export."}, 404

        return _send_zip_response(result)


class AssetExportAllResource(Resource):
    """
    POST /data/global-assets/export/all
    Body: { include_files: false }
    返回: ZIP 文件流
    """

    @jwt_required()
    def post(self):
        data = request.json or {}
        include_files = data.get("include_files", False)

        result = asset_export_service.export_all_assets(
            include_files=include_files,
        )

        if not result.get("zip_path"):
            return {"message": "No assets found to export."}, 404

        return _send_zip_response(result)


class AssetExportByCategoryResource(Resource):
    """
    POST /data/global-assets/export/category/<category_id>
    """

    @jwt_required()
    def post(self, category_id):
        data = request.json or {}
        include_files = data.get("include_files", False)

        result = asset_export_service.export_by_category(
            category_id,
            include_files=include_files,
        )

        if not result.get("zip_path"):
            return {"message": "No assets found in this category."}, 404

        return _send_zip_response(result)


class AssetExportByProjectResource(Resource):
    """
    POST /data/projects/<project_id>/export-assets
    """

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        data = request.json or {}
        include_files = data.get("include_files", False)

        result = asset_export_service.export_by_project(
            project_id,
            include_files=include_files,
        )

        if not result.get("zip_path"):
            return {"message": "No assets found for this project."}, 404

        return _send_zip_response(result)


class AssetImportValidateResource(Resource):
    """
    POST /data/global-assets/import/validate
    上传 ZIP -> 验证格式 -> 返回验证结果和预览
    """

    @jwt_required()
    def post(self):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        if "file" not in request.files:
            raise WrongParameterException("file is required (multipart/form-data).")

        uploaded = request.files["file"]
        if not uploaded.filename:
            raise WrongParameterException("Empty filename.")

        tmp_dir = app.config.get("TMP_DIR", tempfile.gettempdir())
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, uploaded.filename)

        try:
            uploaded.save(tmp_path)

            validation = asset_import_service.validate_import_zip(tmp_path)
            preview = asset_import_service.preview_import(tmp_path)

            return {
                "validation": validation,
                "preview": preview,
            }, 200
        finally:
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)


class AssetImportResource(Resource):
    """
    POST /data/global-assets/import
    上传 ZIP + mode 参数 -> 执行导入
    Body (multipart): file + mode (merge/skip/overwrite/create_new)
    返回: 导入结果统计
    """

    @jwt_required()
    def post(self):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        if "file" not in request.files:
            raise WrongParameterException("file is required (multipart/form-data).")

        uploaded = request.files["file"]
        if not uploaded.filename:
            raise WrongParameterException("Empty filename.")

        mode = request.form.get("mode", "merge")
        valid_modes = ["merge", "skip", "overwrite", "create_new"]
        if mode not in valid_modes:
            raise WrongParameterException(
                f"Invalid mode. Must be one of: {', '.join(valid_modes)}"
            )

        current_user = persons_service.get_current_user()
        author_id = current_user["id"]

        tmp_dir = app.config.get("TMP_DIR", tempfile.gettempdir())
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(tmp_dir, uploaded.filename)

        try:
            uploaded.save(tmp_path)

            result = asset_import_service.import_from_zip(
                tmp_path, mode=mode, author_id=author_id
            )

            return result, 200
        finally:
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)


class AssetImportJsonResource(Resource):
    """
    POST /data/global-assets/import/json
    Body: { assets: [...] }
    JSON 批量导入
    """

    @jwt_required()
    def post(self):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        data = request.json or {}
        assets = data.get("assets", [])
        if not assets:
            raise WrongParameterException("assets is required and must be non-empty.")

        current_user = persons_service.get_current_user()
        author_id = current_user["id"]

        result = asset_import_service.import_from_json(
            assets, author_id=author_id
        )

        return result, 200


def _send_zip_response(result):
    """
    发送 ZIP 文件流响应，发送完毕后清理临时文件。
    """
    zip_path = result["zip_path"]
    filename = result["filename"]

    response = send_file(
        zip_path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename,
    )

    # Schedule cleanup after response is sent
    @response.call_on_close
    def _cleanup():
        try:
            if os.path.isfile(zip_path):
                os.remove(zip_path)
        except Exception as e:
            logger.warning("Failed to clean up export ZIP %s: %s", zip_path, e)

    return response
