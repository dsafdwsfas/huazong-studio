"""
全局资产 API Resources

提供全局资产库的 CRUD、项目关联、使用计数、状态管理和导入端点。
"""

import logging

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import (
    persons_service,
    projects_service,
    user_service,
)
from zou.app.services import global_asset_service
from zou.app.services import asset_node_service
from zou.app.services.exception import WrongParameterException
from zou.app.utils import permissions

logger = logging.getLogger(__name__)


class GlobalAssetListResource(Resource):
    """
    GET  /data/global-assets — 全局资产列表（分页+筛选）
    POST /data/global-assets — 创建资产
    """

    @jwt_required()
    def get(self):
        category_id = request.args.get("category_id")
        status = request.args.get("status")
        search = request.args.get("search")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        if per_page > 100:
            per_page = 100

        result = global_asset_service.list_assets(
            category_id=category_id,
            status=status,
            search=search,
            page=page,
            per_page=per_page,
        )
        return result, 200

    @jwt_required()
    def post(self):
        data = request.json or {}
        name = data.get("name")
        if not name:
            raise WrongParameterException("name is required.")

        category_id = data.get("category_id")
        if not category_id:
            raise WrongParameterException("category_id is required.")

        current_user = persons_service.get_current_user()
        creator_id = current_user["id"]

        asset = global_asset_service.create_asset(
            name=name,
            category_id=category_id,
            creator_id=creator_id,
            description=data.get("description", ""),
            tags=data.get("tags", []),
            files=data.get("files", []),
            metadata=data.get("metadata", {}),
            style_keywords=data.get("style_keywords", []),
            prompt_text=data.get("prompt_text", ""),
            source_project_id=data.get("source_project_id"),
            thumbnail_preview_file_id=data.get("thumbnail_preview_file_id"),
        )

        # Trigger auto-linking for the newly created asset
        try:
            asset_node_service.auto_link_asset(asset["id"])
        except Exception:
            logger.warning(
                "Auto-link failed for asset %s", asset["id"], exc_info=True
            )

        return asset, 201


class GlobalAssetResource(Resource):
    """
    GET    /data/global-assets/<asset_id> — 资产详情
    PUT    /data/global-assets/<asset_id> — 更新资产
    DELETE /data/global-assets/<asset_id> — 删除资产（仅 creator 或 admin）
    """

    @jwt_required()
    def get(self, asset_id):
        asset = global_asset_service.get_asset(asset_id)
        return asset, 200

    @jwt_required()
    def put(self, asset_id):
        data = request.json or {}
        asset = global_asset_service.update_asset(asset_id, data)

        # Re-trigger auto-linking after asset update
        try:
            asset_node_service.auto_link_asset(asset_id)
        except Exception:
            logger.warning(
                "Auto-link failed for asset %s", asset_id, exc_info=True
            )

        return asset, 200

    @jwt_required()
    def delete(self, asset_id):
        # Only creator or admin can delete
        current_user = persons_service.get_current_user()
        asset = global_asset_service.get_asset(asset_id)

        is_creator = asset.get("creator_id") == current_user["id"]
        is_admin = permissions.has_admin_permissions()

        if not is_creator and not is_admin:
            raise permissions.PermissionDenied

        global_asset_service.delete_asset(asset_id)
        return {"message": "Asset deleted."}, 200


class GlobalAssetLinkProjectResource(Resource):
    """
    POST /data/global-assets/<asset_id>/link-project — 关联项目
    """

    @jwt_required()
    def post(self, asset_id):
        data = request.json or {}
        project_id = data.get("project_id")
        if not project_id:
            raise WrongParameterException("project_id is required.")

        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        result = global_asset_service.link_asset_to_project(
            asset_id, project_id
        )
        return result, 200


class GlobalAssetUnlinkProjectResource(Resource):
    """
    DELETE /data/global-assets/<asset_id>/link-project/<project_id> — 解除关联
    """

    @jwt_required()
    def delete(self, asset_id, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        global_asset_service.unlink_asset_from_project(asset_id, project_id)
        return {"message": "Unlinked."}, 200


class ProjectGlobalAssetsResource(Resource):
    """
    GET /data/projects/<project_id>/global-assets — 项目关联的资产
    """

    @jwt_required()
    def get(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        category_id = request.args.get("category_id")
        assets = global_asset_service.get_assets_by_project(
            project_id, category_id=category_id
        )
        return assets, 200


class GlobalAssetUseResource(Resource):
    """
    POST /data/global-assets/<asset_id>/use — 使用计数+1
    """

    @jwt_required()
    def post(self, asset_id):
        asset = global_asset_service.increment_usage(asset_id)
        return asset, 200


class GlobalAssetStatusResource(Resource):
    """
    PUT /data/global-assets/<asset_id>/status — 状态变更（仅 manager/admin）
    """

    @jwt_required()
    def put(self, asset_id):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        data = request.json or {}
        new_status = data.get("status")
        if not new_status:
            raise WrongParameterException("status is required.")

        asset = global_asset_service.update_status(asset_id, new_status)
        return asset, 200


class GlobalAssetImportResource(Resource):
    """
    POST /data/global-assets/import/<project_id> — 从项目导入资产
    """

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        data = request.json or {}
        asset_type = data.get("asset_type")
        if not asset_type:
            raise WrongParameterException("asset_type is required.")

        result = global_asset_service.import_from_project(
            project_id, asset_type
        )
        return result, 201
