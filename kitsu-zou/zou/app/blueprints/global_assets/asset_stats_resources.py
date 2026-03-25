"""
Asset statistics API resources (Phase 4.7).

Provides dashboard overview, category distribution, usage frequency,
storage analysis, hotness ranking, growth trends, creator analytics,
and project-level asset statistics.
"""

import logging

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import asset_stats_service

logger = logging.getLogger(__name__)


class AssetDashboardResource(Resource):
    """
    GET /data/asset-stats/dashboard — Dashboard overview stats.
    """

    @jwt_required()
    def get(self):
        stats = asset_stats_service.get_dashboard_stats()
        return stats, 200


class AssetCategoryDistributionResource(Resource):
    """
    GET /data/asset-stats/category-distribution — Category distribution.
    """

    @jwt_required()
    def get(self):
        distribution = asset_stats_service.get_category_distribution()
        return distribution, 200


class AssetUsageFrequencyResource(Resource):
    """
    GET /data/asset-stats/usage-frequency — Usage frequency over time.
    Query params:
        period: 'month' (default) or 'week'
        months: number of months to look back (default 12)
    """

    @jwt_required()
    def get(self):
        period = request.args.get("period", "month")
        months = request.args.get("months", 12, type=int)
        if period not in ("month", "week"):
            period = "month"
        if months < 1 or months > 60:
            months = 12
        result = asset_stats_service.get_usage_frequency_stats(
            period=period, months=months
        )
        return result, 200


class AssetStorageStatsResource(Resource):
    """
    GET /data/asset-stats/storage — Storage usage statistics.
    """

    @jwt_required()
    def get(self):
        stats = asset_stats_service.get_storage_stats()
        return stats, 200


class AssetHotnessRankingResource(Resource):
    """
    GET /data/asset-stats/hotness — Asset hotness ranking.
    Query params:
        limit: max results (default 20, max 100)
    """

    @jwt_required()
    def get(self):
        limit = request.args.get("limit", 20, type=int)
        if limit < 1 or limit > 100:
            limit = 20
        ranking = asset_stats_service.get_hotness_ranking(limit=limit)
        return ranking, 200


class AssetGrowthTrendResource(Resource):
    """
    GET /data/asset-stats/growth — Monthly growth trend.
    Query params:
        months: number of months to look back (default 6)
    """

    @jwt_required()
    def get(self):
        months = request.args.get("months", 6, type=int)
        if months < 1 or months > 24:
            months = 6
        trend = asset_stats_service.get_growth_trend(months=months)
        return trend, 200


class AssetCreatorStatsResource(Resource):
    """
    GET /data/asset-stats/creators — Creator statistics.
    Query params:
        limit: max results (default 10, max 50)
    """

    @jwt_required()
    def get(self):
        limit = request.args.get("limit", 10, type=int)
        if limit < 1 or limit > 50:
            limit = 10
        creators = asset_stats_service.get_creator_stats(limit=limit)
        return creators, 200


class ProjectAssetStatsResource(Resource):
    """
    GET /data/projects/<project_id>/asset-stats — Project-level asset stats.
    """

    @jwt_required()
    def get(self, project_id):
        stats = asset_stats_service.get_project_asset_stats(project_id)
        return stats, 200
