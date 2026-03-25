"""
开放 API Blueprint

独立于内部 API 的 Blueprint，前缀 /open-api/v1/。
资产端点使用 API Key 认证，Key 管理端点使用 JWT 认证。
"""

from flask import Blueprint
from zou.app.utils.api import configure_api_from_blueprint

from zou.app.blueprints.open_api.open_api_resources import (
    OpenAssetListResource,
    OpenAssetResource,
    OpenAssetSearchResource,
    OpenAssetSimilarResource,
    OpenAssetVersionsResource,
    OpenAssetUsagesResource,
    OpenAssetGraphResource,
    OpenCategoryListResource,
    OpenCategoryResource,
    ApiKeyListResource,
    ApiKeyResource,
)

routes = [
    # 资产端点（API Key 认证）
    ("/open-api/v1/assets", OpenAssetListResource),
    ("/open-api/v1/assets/search", OpenAssetSearchResource),
    ("/open-api/v1/assets/<asset_id>", OpenAssetResource),
    ("/open-api/v1/assets/<asset_id>/similar", OpenAssetSimilarResource),
    ("/open-api/v1/assets/<asset_id>/versions", OpenAssetVersionsResource),
    ("/open-api/v1/assets/<asset_id>/usages", OpenAssetUsagesResource),
    ("/open-api/v1/assets/<asset_id>/graph", OpenAssetGraphResource),
    # 分类端点（API Key 认证）
    ("/open-api/v1/categories", OpenCategoryListResource),
    ("/open-api/v1/categories/<category_id>", OpenCategoryResource),
    # API Key 管理（JWT 认证）
    ("/open-api/v1/keys", ApiKeyListResource),
    ("/open-api/v1/keys/<key_id>", ApiKeyResource),
]

blueprint = Blueprint("open_api", "open_api")
api = configure_api_from_blueprint(blueprint, routes)
