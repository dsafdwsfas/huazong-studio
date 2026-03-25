"""
开放 API Resource 类

所有资产端点使用 @api_key_required(scope) 装饰器。
API Key 管理端点使用 @jwt_required()（只能通过画宗 UI 管理 Key）。
响应格式统一: { data: ..., meta: { page, per_page, total } }
"""

import logging

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import (
    persons_service,
    global_asset_service,
    api_key_service,
)
from zou.app.services.exception import WrongParameterException
from zou.app.utils.api_key_auth import api_key_required, add_rate_limit_headers

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _paginated_response(result, status=200):
    """
    将内部服务返回的分页结果转为开放 API 统一格式。

    Input:  { data, total, page, per_page, pages }
    Output: { data, meta: { page, per_page, total, pages } }, status, headers
    """
    response = {
        "data": result.get("data", []),
        "meta": {
            "page": result.get("page", 1),
            "per_page": result.get("per_page", 20),
            "total": result.get("total", 0),
            "pages": result.get("pages", 0),
        },
    }
    return add_rate_limit_headers(response, status)


def _single_response(data, status=200):
    """单条数据响应。"""
    response = {"data": data}
    return add_rate_limit_headers(response, status)


def _error_response(message, status):
    """错误响应。"""
    return {"error": message}, status


# ---------------------------------------------------------------------------
# Asset Resources (API Key auth)
# ---------------------------------------------------------------------------


class OpenAssetListResource(Resource):
    """
    GET  /open-api/v1/assets — 资产列表（分页+筛选）
    POST /open-api/v1/assets — 创建资产
    """

    @api_key_required("assets:read")
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
        return _paginated_response(result)

    @api_key_required("assets:write")
    def post(self):
        data = request.json or {}
        name = data.get("name")
        if not name:
            return _error_response("name is required", 400)

        category_id = data.get("category_id")
        if not category_id:
            return _error_response("category_id is required", 400)

        # API Key 创建的资产使用 key owner 作为 creator
        from flask import g

        api_key = g.api_key
        creator_id = str(api_key.owner_id)

        try:
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
                thumbnail_preview_file_id=data.get(
                    "thumbnail_preview_file_id"
                ),
            )
        except WrongParameterException as e:
            return _error_response(str(e), 400)

        return _single_response(asset, 201)


class OpenAssetResource(Resource):
    """
    GET    /open-api/v1/assets/<asset_id> — 资产详情
    PUT    /open-api/v1/assets/<asset_id> — 更新资产
    DELETE /open-api/v1/assets/<asset_id> — 删除资产
    """

    @api_key_required("assets:read")
    def get(self, asset_id):
        try:
            asset = global_asset_service.get_asset(asset_id)
        except global_asset_service.GlobalAssetNotFoundException:
            return _error_response("Asset not found", 404)
        return _single_response(asset)

    @api_key_required("assets:write")
    def put(self, asset_id):
        data = request.json or {}
        try:
            asset = global_asset_service.update_asset(asset_id, data)
        except global_asset_service.GlobalAssetNotFoundException:
            return _error_response("Asset not found", 404)
        except WrongParameterException as e:
            return _error_response(str(e), 400)
        return _single_response(asset)

    @api_key_required("assets:delete")
    def delete(self, asset_id):
        try:
            global_asset_service.delete_asset(asset_id)
        except global_asset_service.GlobalAssetNotFoundException:
            return _error_response("Asset not found", 404)
        return "", 204


class OpenAssetSearchResource(Resource):
    """
    GET /open-api/v1/assets/search — 搜索资产
    """

    @api_key_required("search")
    def get(self):
        query = request.args.get("q", "")
        category_id = request.args.get("category_id")
        tags = request.args.getlist("tags")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        if per_page > 100:
            per_page = 100

        # Use the search service if available, otherwise fall back
        try:
            from zou.app.services import asset_search_service

            result = asset_search_service.search_assets(
                query=query,
                category_id=category_id,
                tags=tags,
                page=page,
                per_page=per_page,
            )
            return _paginated_response(result)
        except Exception:
            # Fallback to basic list with search
            result = global_asset_service.list_assets(
                category_id=category_id,
                search=query,
                page=page,
                per_page=per_page,
            )
            return _paginated_response(result)


class OpenAssetSimilarResource(Resource):
    """
    GET /open-api/v1/assets/<asset_id>/similar — 相似资产
    """

    @api_key_required("assets:read")
    def get(self, asset_id):
        limit = request.args.get("limit", 10, type=int)
        try:
            from zou.app.services import asset_search_service

            similar = asset_search_service.find_similar_assets(
                asset_id, limit=limit
            )
            return _single_response(similar)
        except global_asset_service.GlobalAssetNotFoundException:
            return _error_response("Asset not found", 404)
        except Exception as e:
            logger.warning("Similar assets lookup failed: %s", e)
            return _single_response([])


class OpenAssetVersionsResource(Resource):
    """
    GET /open-api/v1/assets/<asset_id>/versions — 资产版本列表
    """

    @api_key_required("assets:read")
    def get(self, asset_id):
        try:
            from zou.app.services import asset_version_service

            versions = asset_version_service.list_versions(asset_id)
            return _single_response(versions)
        except global_asset_service.GlobalAssetNotFoundException:
            return _error_response("Asset not found", 404)
        except Exception as e:
            logger.warning("Version list failed: %s", e)
            return _single_response([])


class OpenAssetUsagesResource(Resource):
    """
    GET  /open-api/v1/assets/<asset_id>/usages — 使用记录列表
    POST /open-api/v1/assets/<asset_id>/usages — 记录使用
    """

    @api_key_required("assets:read")
    def get(self, asset_id):
        try:
            from zou.app.services import asset_usage_service

            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 20, type=int)
            usages = asset_usage_service.list_usages_for_asset(
                asset_id, page=page, per_page=per_page
            )
            return _paginated_response(usages)
        except global_asset_service.GlobalAssetNotFoundException:
            return _error_response("Asset not found", 404)
        except Exception as e:
            logger.warning("Usage list failed: %s", e)
            return _paginated_response(
                {"data": [], "total": 0, "page": 1, "per_page": 20, "pages": 0}
            )

    @api_key_required("assets:write")
    def post(self, asset_id):
        data = request.json or {}

        from flask import g

        api_key = g.api_key

        try:
            from zou.app.services import asset_usage_service

            usage = asset_usage_service.create_usage(
                asset_id=asset_id,
                project_id=data.get("project_id"),
                used_by=str(api_key.owner_id),
                context=data.get("context", ""),
                software=data.get("software", ""),
            )
            # Also increment usage count
            global_asset_service.increment_usage(asset_id)
            return _single_response(usage, 201)
        except global_asset_service.GlobalAssetNotFoundException:
            return _error_response("Asset not found", 404)
        except WrongParameterException as e:
            return _error_response(str(e), 400)
        except Exception as e:
            logger.warning("Usage creation failed: %s", e)
            return _error_response("Failed to record usage", 500)


class OpenAssetGraphResource(Resource):
    """
    GET /open-api/v1/assets/<asset_id>/graph — 资产关系图谱
    """

    @api_key_required("graph:read")
    def get(self, asset_id):
        try:
            from zou.app.services import asset_node_service

            depth = request.args.get("depth", 2, type=int)
            graph = asset_node_service.get_asset_graph(
                asset_id, depth=depth
            )
            return _single_response(graph)
        except global_asset_service.GlobalAssetNotFoundException:
            return _error_response("Asset not found", 404)
        except Exception as e:
            logger.warning("Graph lookup failed: %s", e)
            return _single_response({"nodes": [], "edges": []})


# ---------------------------------------------------------------------------
# Category Resources (API Key auth)
# ---------------------------------------------------------------------------


class OpenCategoryListResource(Resource):
    """
    GET /open-api/v1/categories — 分类树
    """

    @api_key_required("categories:read")
    def get(self):
        try:
            from zou.app.services import asset_category_service

            categories = asset_category_service.get_category_tree()
            return _single_response(categories)
        except Exception as e:
            logger.warning("Category tree fetch failed: %s", e)
            return _single_response([])


class OpenCategoryResource(Resource):
    """
    GET /open-api/v1/categories/<category_id> — 分类详情
    """

    @api_key_required("categories:read")
    def get(self, category_id):
        try:
            from zou.app.services import asset_category_service

            category = asset_category_service.get_category(category_id)
            if category is None:
                return _error_response("Category not found", 404)
            return _single_response(category)
        except Exception:
            return _error_response("Category not found", 404)


# ---------------------------------------------------------------------------
# API Key Management Resources (JWT auth)
# ---------------------------------------------------------------------------


class ApiKeyListResource(Resource):
    """
    GET  /open-api/v1/keys — 列出当前用户的 API Keys
    POST /open-api/v1/keys — 创建 API Key
    """

    @jwt_required()
    def get(self):
        current_user = persons_service.get_current_user()
        keys = api_key_service.list_api_keys(current_user["id"])
        return {"data": keys}, 200

    @jwt_required()
    def post(self):
        current_user = persons_service.get_current_user()
        data = request.json or {}

        name = data.get("name")
        if not name:
            return _error_response("name is required", 400)

        scopes = data.get("scopes", ["assets:read"])
        # Validate scopes
        invalid = set(scopes) - api_key_service.VALID_SCOPES - {"*"}
        if invalid:
            return _error_response(
                f"Invalid scopes: {', '.join(invalid)}", 400
            )

        rate_limit = data.get("rate_limit", 100)
        if not isinstance(rate_limit, int) or rate_limit < 1:
            return _error_response("rate_limit must be a positive integer", 400)
        if rate_limit > 10000:
            rate_limit = 10000

        expires_at = data.get("expires_at")

        result = api_key_service.create_api_key(
            owner_id=current_user["id"],
            name=name,
            scopes=scopes,
            rate_limit=rate_limit,
            expires_at=expires_at,
        )
        return {"data": result}, 201


class ApiKeyResource(Resource):
    """
    GET    /open-api/v1/keys/<key_id> — Key 详情
    PUT    /open-api/v1/keys/<key_id> — 更新 Key
    DELETE /open-api/v1/keys/<key_id> — 删除 Key
    """

    @jwt_required()
    def get(self, key_id):
        current_user = persons_service.get_current_user()
        key = api_key_service.get_api_key(key_id, current_user["id"])
        if key is None:
            return _error_response("API key not found", 404)
        return {"data": key}, 200

    @jwt_required()
    def put(self, key_id):
        current_user = persons_service.get_current_user()
        data = request.json or {}

        # Validate scopes if provided
        if "scopes" in data:
            invalid = set(data["scopes"]) - api_key_service.VALID_SCOPES - {"*"}
            if invalid:
                return _error_response(
                    f"Invalid scopes: {', '.join(invalid)}", 400
                )

        result = api_key_service.update_api_key(
            key_id, current_user["id"], data
        )
        if result is None:
            return _error_response("API key not found", 404)
        return {"data": result}, 200

    @jwt_required()
    def delete(self, key_id):
        current_user = persons_service.get_current_user()
        deleted = api_key_service.delete_api_key(key_id, current_user["id"])
        if not deleted:
            return _error_response("API key not found", 404)
        return "", 204
