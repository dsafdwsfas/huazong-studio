"""
资产版本管理 API Resources

提供资产版本列表、详情、差异对比、恢复等端点。
"""

import logging

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import persons_service
from zou.app.services import asset_version_service
from zou.app.services.exception import WrongParameterException
from zou.app.utils import permissions

logger = logging.getLogger(__name__)


class AssetVersionListResource(Resource):
    """
    GET /data/global-assets/<asset_id>/versions
    查询参数: page, per_page
    返回: { versions: [...], total, page, per_page }
    """

    @jwt_required()
    def get(self, asset_id):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        if per_page > 100:
            per_page = 100

        result = asset_version_service.get_versions_for_asset(
            asset_id,
            page=page,
            per_page=per_page,
        )
        return result, 200


class AssetLatestVersionResource(Resource):
    """
    GET /data/global-assets/<asset_id>/versions/latest
    获取最新版本
    """

    @jwt_required()
    def get(self, asset_id):
        version = asset_version_service.get_latest_version(asset_id)
        return version, 200


class AssetVersionResource(Resource):
    """
    GET /data/asset-versions/<version_id>
    返回版本详情（含 snapshot 和 diff）
    """

    @jwt_required()
    def get(self, version_id):
        version = asset_version_service.get_version(version_id)
        return version, 200


class AssetVersionDiffResource(Resource):
    """
    GET /data/asset-versions/<version_id>/diff
    返回版本差异详情
    """

    @jwt_required()
    def get(self, version_id):
        diff = asset_version_service.get_version_diff(version_id)
        return diff, 200


class AssetVersionCompareResource(Resource):
    """
    GET /data/asset-versions/compare
    查询参数: version_a, version_b
    返回两个版本的差异对比
    """

    @jwt_required()
    def get(self):
        version_a = request.args.get("version_a")
        version_b = request.args.get("version_b")

        if not version_a or not version_b:
            raise WrongParameterException(
                "version_a and version_b are required."
            )

        result = asset_version_service.compare_versions(version_a, version_b)
        return result, 200


class AssetVersionRestoreResource(Resource):
    """
    POST /data/global-assets/<asset_id>/versions/<version_id>/restore
    恢复到指定版本（创建新版本）
    仅 manager/admin 可执行
    """

    @jwt_required()
    def post(self, asset_id, version_id):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        current_user = persons_service.get_current_user()
        restored = asset_version_service.restore_version(
            asset_id,
            version_id,
            restored_by=current_user["id"],
        )
        return restored, 201
