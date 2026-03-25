"""
资产分类 API Resources

提供分类树、CRUD、排序、统计和预设初始化端点。
"""

import logging

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import asset_category_service
from zou.app.services.exception import WrongParameterException
from zou.app.utils import permissions

logger = logging.getLogger(__name__)


class AssetCategoryListResource(Resource):
    """
    GET  /data/asset-categories — 获取分类树
    POST /data/asset-categories — 创建分类（admin/manager）
    """

    @jwt_required()
    def get(self):
        tree = asset_category_service.get_category_tree()
        return tree, 200

    @jwt_required()
    def post(self):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        data = request.json or {}
        name = data.get("name")
        if not name:
            raise WrongParameterException("name is required.")

        slug = data.get("slug")
        if not slug:
            raise WrongParameterException("slug is required.")

        category = asset_category_service.create_category(
            name=name,
            slug=slug,
            name_en=data.get("name_en", ""),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            color=data.get("color", ""),
            parent_id=data.get("parent_id"),
            sort_order=data.get("sort_order", 0),
            is_system=data.get("is_system", False),
            metadata=data.get("metadata", {}),
        )
        return category, 201


class AssetCategoryResource(Resource):
    """
    GET    /data/asset-categories/<category_id> — 分类详情
    PUT    /data/asset-categories/<category_id> — 更新分类
    DELETE /data/asset-categories/<category_id> — 删除分类
    """

    @jwt_required()
    def get(self, category_id):
        category = asset_category_service.get_category(category_id)
        return category, 200

    @jwt_required()
    def put(self, category_id):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        data = request.json or {}
        category = asset_category_service.update_category(category_id, data)
        return category, 200

    @jwt_required()
    def delete(self, category_id):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        asset_category_service.delete_category(category_id)
        return {"message": "Category deleted."}, 200


class AssetCategoryReorderResource(Resource):
    """
    PUT /data/asset-categories/reorder — 批量排序
    """

    @jwt_required()
    def put(self):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        data = request.json or {}
        orders = data.get("orders", [])
        if not orders:
            raise WrongParameterException(
                "orders is required (list of {id, sort_order})."
            )

        asset_category_service.reorder_categories(orders)
        return {"message": "Reorder successful."}, 200


class AssetCategoryStatsResource(Resource):
    """
    GET /data/asset-categories/stats — 分类统计
    """

    @jwt_required()
    def get(self):
        stats = asset_category_service.get_category_stats()
        return stats, 200


class AssetCategoryInitResource(Resource):
    """
    POST /data/asset-categories/init — 初始化预设分类
    """

    @jwt_required()
    def post(self):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        result = asset_category_service.init_default_categories()
        return result, 201
