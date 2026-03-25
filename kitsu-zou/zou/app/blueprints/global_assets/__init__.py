from flask import Blueprint
from zou.app.utils.api import configure_api_from_blueprint

from zou.app.blueprints.global_assets.global_asset_resources import (
    GlobalAssetListResource,
    GlobalAssetResource,
    GlobalAssetLinkProjectResource,
    GlobalAssetUnlinkProjectResource,
    ProjectGlobalAssetsResource,
    GlobalAssetUseResource,
    GlobalAssetStatusResource,
    GlobalAssetImportResource,
)

from zou.app.blueprints.global_assets.asset_category_resources import (
    AssetCategoryListResource,
    AssetCategoryResource,
    AssetCategoryReorderResource,
    AssetCategoryStatsResource,
    AssetCategoryInitResource,
)

from zou.app.blueprints.global_assets.asset_node_resources import (
    AssetGraphResource,
    AssetGraphStatsResource,
    AssetNodeGraphResource,
    AssetAutoLinkResource,
    ProjectAssetGraphResource,
    ProjectGraphRebuildResource,
    AssetNodeResource,
    AssetNodeLinkResource,
)

from zou.app.blueprints.global_assets.asset_search_resources import (
    AssetSearchResource,
    AssetSearchByTagsResource,
    AssetSearchSimilarResource,
    AssetSearchSuggestionsResource,
    AssetSearchFacetsResource,
    AssetSearchIndexResource,
)

from zou.app.blueprints.global_assets.asset_version_resources import (
    AssetVersionListResource,
    AssetVersionResource,
    AssetVersionDiffResource,
    AssetVersionCompareResource,
    AssetVersionRestoreResource,
    AssetLatestVersionResource,
)

from zou.app.blueprints.global_assets.asset_stats_resources import (
    AssetDashboardResource,
    AssetCategoryDistributionResource,
    AssetUsageFrequencyResource,
    AssetStorageStatsResource,
    AssetHotnessRankingResource,
    AssetGrowthTrendResource,
    AssetCreatorStatsResource,
    ProjectAssetStatsResource,
)

from zou.app.blueprints.global_assets.asset_export_resources import (
    AssetExportResource,
    AssetExportAllResource,
    AssetExportByCategoryResource,
    AssetExportByProjectResource,
    AssetImportValidateResource,
    AssetImportResource,
    AssetImportJsonResource,
)

from zou.app.blueprints.global_assets.asset_review_resources import (
    AssetReviewQueueResource,
    AssetReviewStatsResource,
    AssetSubmitReviewResource,
    AssetReviewApproveResource,
    AssetReviewRejectResource,
    AssetReviewRevisionResource,
    AssetReviewResource,
    AssetReviewHistoryResource,
    MySubmissionsResource,
    AssetReviewBatchApproveResource,
    AssetReviewBatchRejectResource,
)

from zou.app.blueprints.global_assets.asset_usage_resources import (
    AssetUsageListResource,
    AssetUsageResource,
    ProjectAssetUsagesResource,
    AssetUsageStatsResource,
    MostUsedAssetsResource,
    AssetUsageTimelineResource,
    AssetCrossProjectUsageResource,
)

routes = [
    # Asset search (must precede /data/global-assets/<asset_id>)
    ("/data/global-assets/search", AssetSearchResource),
    ("/data/global-assets/search/by-tags", AssetSearchByTagsResource),
    (
        "/data/global-assets/search/suggestions",
        AssetSearchSuggestionsResource,
    ),
    ("/data/global-assets/search/facets", AssetSearchFacetsResource),
    ("/data/global-assets/search/reindex", AssetSearchIndexResource),
    ("/data/global-assets/search/index-status", AssetSearchIndexResource, "assetsearchindexstatus"),
    # Asset stats dashboard (must precede <asset_id> routes)
    ("/data/asset-stats/dashboard", AssetDashboardResource),
    (
        "/data/asset-stats/category-distribution",
        AssetCategoryDistributionResource,
    ),
    ("/data/asset-stats/usage-frequency", AssetUsageFrequencyResource),
    ("/data/asset-stats/storage", AssetStorageStatsResource),
    ("/data/asset-stats/hotness", AssetHotnessRankingResource),
    ("/data/asset-stats/growth", AssetGrowthTrendResource),
    ("/data/asset-stats/creators", AssetCreatorStatsResource),
    # Asset review (must precede <asset_id> routes)
    ("/data/asset-reviews/queue", AssetReviewQueueResource),
    ("/data/asset-reviews/stats", AssetReviewStatsResource),
    ("/data/asset-reviews/my-submissions", MySubmissionsResource),
    ("/data/asset-reviews/batch-approve", AssetReviewBatchApproveResource),
    ("/data/asset-reviews/batch-reject", AssetReviewBatchRejectResource),
    ("/data/asset-reviews/<review_id>", AssetReviewResource),
    (
        "/data/asset-reviews/<review_id>/approve",
        AssetReviewApproveResource,
    ),
    (
        "/data/asset-reviews/<review_id>/reject",
        AssetReviewRejectResource,
    ),
    (
        "/data/asset-reviews/<review_id>/request-revision",
        AssetReviewRevisionResource,
    ),
    # Asset usage — most-used must precede <asset_id> routes
    ("/data/global-assets/most-used", MostUsedAssetsResource),
    # Asset export/import (must precede <asset_id> routes)
    ("/data/global-assets/export", AssetExportResource),
    ("/data/global-assets/export/all", AssetExportAllResource),
    (
        "/data/global-assets/export/category/<category_id>",
        AssetExportByCategoryResource,
    ),
    ("/data/global-assets/import", AssetImportResource),
    ("/data/global-assets/import/validate", AssetImportValidateResource),
    ("/data/global-assets/import/json", AssetImportJsonResource),
    # Global assets
    ("/data/global-assets", GlobalAssetListResource),
    ("/data/global-assets/<asset_id>", GlobalAssetResource),
    (
        "/data/global-assets/<asset_id>/link-project",
        GlobalAssetLinkProjectResource,
    ),
    (
        "/data/global-assets/<asset_id>/link-project/<project_id>",
        GlobalAssetUnlinkProjectResource,
    ),
    (
        "/data/projects/<project_id>/export-assets",
        AssetExportByProjectResource,
    ),
    (
        "/data/projects/<project_id>/global-assets",
        ProjectGlobalAssetsResource,
    ),
    (
        "/data/projects/<project_id>/asset-stats",
        ProjectAssetStatsResource,
    ),
    (
        "/data/global-assets/<asset_id>/submit-review",
        AssetSubmitReviewResource,
    ),
    (
        "/data/global-assets/<asset_id>/reviews",
        AssetReviewHistoryResource,
    ),
    ("/data/global-assets/<asset_id>/use", GlobalAssetUseResource),
    ("/data/global-assets/<asset_id>/status", GlobalAssetStatusResource),
    (
        "/data/global-assets/<asset_id>/similar",
        AssetSearchSimilarResource,
    ),
    (
        "/data/global-assets/import/<project_id>",
        GlobalAssetImportResource,
    ),
    # Asset usage tracking
    (
        "/data/global-assets/<asset_id>/usages",
        AssetUsageListResource,
    ),
    (
        "/data/global-assets/<asset_id>/usage-stats",
        AssetUsageStatsResource,
    ),
    (
        "/data/global-assets/<asset_id>/usage-timeline",
        AssetUsageTimelineResource,
    ),
    (
        "/data/global-assets/<asset_id>/cross-project",
        AssetCrossProjectUsageResource,
    ),
    ("/data/asset-usages/<usage_id>", AssetUsageResource),
    (
        "/data/projects/<project_id>/asset-usages",
        ProjectAssetUsagesResource,
    ),
    # Asset versions (latest before <version_id> to avoid route conflict)
    (
        "/data/global-assets/<asset_id>/versions/latest",
        AssetLatestVersionResource,
    ),
    (
        "/data/global-assets/<asset_id>/versions/<version_id>/restore",
        AssetVersionRestoreResource,
    ),
    (
        "/data/global-assets/<asset_id>/versions",
        AssetVersionListResource,
    ),
    ("/data/asset-versions/compare", AssetVersionCompareResource),
    ("/data/asset-versions/<version_id>", AssetVersionResource),
    ("/data/asset-versions/<version_id>/diff", AssetVersionDiffResource),
    # Asset categories
    ("/data/asset-categories", AssetCategoryListResource),
    ("/data/asset-categories/reorder", AssetCategoryReorderResource),
    ("/data/asset-categories/stats", AssetCategoryStatsResource),
    ("/data/asset-categories/init", AssetCategoryInitResource),
    ("/data/asset-categories/<category_id>", AssetCategoryResource),
    # Asset node graph
    ("/data/asset-graph", AssetGraphResource),
    ("/data/asset-graph/stats", AssetGraphStatsResource),
    ("/data/global-assets/<asset_id>/graph", AssetNodeGraphResource),
    ("/data/global-assets/<asset_id>/auto-link", AssetAutoLinkResource),
    (
        "/data/projects/<project_id>/asset-graph",
        ProjectAssetGraphResource,
    ),
    (
        "/data/projects/<project_id>/rebuild-graph",
        ProjectGraphRebuildResource,
    ),
    ("/data/asset-nodes/<node_id>", AssetNodeResource),
    ("/data/asset-node-links", AssetNodeLinkResource),
    ("/data/asset-node-links/<link_id>", AssetNodeLinkResource, "assetnodelinkdetail"),
]

blueprint = Blueprint("global_assets", "global_assets")
api = configure_api_from_blueprint(blueprint, routes)
