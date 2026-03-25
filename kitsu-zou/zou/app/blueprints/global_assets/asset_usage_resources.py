"""
资产使用追踪 API Resources

提供资产使用记录的 CRUD、统计、排行、时间线和跨项目分析端点。
"""

import logging

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import persons_service
from zou.app.services import asset_usage_service
from zou.app.services.exception import WrongParameterException

logger = logging.getLogger(__name__)


class AssetUsageListResource(Resource):
    """
    GET  /data/global-assets/<asset_id>/usages — 资产使用记录列表
    POST /data/global-assets/<asset_id>/usages — 记录一次使用
    """

    @jwt_required()
    def get(self, asset_id):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        if per_page > 100:
            per_page = 100

        result = asset_usage_service.get_asset_usages(
            asset_id, page=page, per_page=per_page
        )
        return result, 200

    @jwt_required()
    def post(self, asset_id):
        data = request.json or {}
        project_id = data.get("project_id")
        if not project_id:
            raise WrongParameterException("project_id is required.")

        current_user = persons_service.get_current_user()

        usage = asset_usage_service.record_usage(
            asset_id=asset_id,
            project_id=project_id,
            used_by_id=data.get("used_by_id", current_user["id"]),
            usage_type=data.get("usage_type", "direct"),
            entity_id=data.get("entity_id"),
            entity_type=data.get("entity_type"),
            context=data.get("context"),
        )
        return usage, 201


class AssetUsageResource(Resource):
    """
    GET    /data/asset-usages/<usage_id> — 使用记录详情
    DELETE /data/asset-usages/<usage_id> — 删除使用记录
    """

    @jwt_required()
    def get(self, usage_id):
        usage = asset_usage_service.get_usage(usage_id)
        return usage, 200

    @jwt_required()
    def delete(self, usage_id):
        asset_usage_service.delete_usage(usage_id)
        return {"message": "Usage record deleted."}, 200


class ProjectAssetUsagesResource(Resource):
    """
    GET /data/projects/<project_id>/asset-usages — 项目资产使用列表
    """

    @jwt_required()
    def get(self, project_id):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        if per_page > 100:
            per_page = 100

        result = asset_usage_service.get_project_usages(
            project_id, page=page, per_page=per_page
        )
        return result, 200


class AssetUsageStatsResource(Resource):
    """
    GET /data/global-assets/<asset_id>/usage-stats — 使用统计
    """

    @jwt_required()
    def get(self, asset_id):
        stats = asset_usage_service.get_asset_usage_stats(asset_id)
        return stats, 200


class MostUsedAssetsResource(Resource):
    """
    GET /data/global-assets/most-used — 最常用资产排行
    查询参数: limit (默认 20, 最大 100)
    """

    @jwt_required()
    def get(self):
        limit = request.args.get("limit", 20, type=int)
        assets = asset_usage_service.get_most_used_assets(limit=limit)
        return assets, 200


class AssetUsageTimelineResource(Resource):
    """
    GET /data/global-assets/<asset_id>/usage-timeline — 使用时间线
    """

    @jwt_required()
    def get(self, asset_id):
        timeline = asset_usage_service.get_usage_timeline(asset_id)
        return timeline, 200


class AssetCrossProjectUsageResource(Resource):
    """
    GET /data/global-assets/<asset_id>/cross-project — 跨项目使用
    """

    @jwt_required()
    def get(self, asset_id):
        cross_project = asset_usage_service.get_cross_project_usage(asset_id)
        return cross_project, 200
