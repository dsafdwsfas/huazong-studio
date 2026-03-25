"""
Global Asset Search API Resources

Provides full-text search, tag-based search, similar asset discovery,
autocomplete suggestions, facet statistics, and index management endpoints.

All search is backed by MeiliSearch via asset_search_service.
"""

import logging
import time

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services.exception import WrongParameterException
from zou.app.utils import permissions

logger = logging.getLogger(__name__)

VALID_SORT_OPTIONS = {
    "relevance",
    "newest",
    "oldest",
    "most_used",
    "name_asc",
    "name_desc",
}

VALID_STATUS_VALUES = {"draft", "reviewed", "archived"}

SORT_TO_MEILI = {
    "newest": ["created_at:desc"],
    "oldest": ["created_at:asc"],
    "most_used": ["usage_count:desc"],
    "name_asc": ["name:asc"],
    "name_desc": ["name:desc"],
}


def _build_filters(args):
    """
    Convert query parameters into a MeiliSearch filter expression string.
    Multiple conditions are joined with AND.
    """
    clauses = []

    category_id = args.get("category_id")
    if category_id:
        clauses.append(f"category_id = '{category_id}'")

    category_slug = args.get("category_slug")
    if category_slug:
        clauses.append(f"category_slug = '{category_slug}'")

    status = args.get("status")
    if status:
        if status not in VALID_STATUS_VALUES:
            raise WrongParameterException(
                f"Invalid status '{status}'. "
                f"Must be one of: {', '.join(sorted(VALID_STATUS_VALUES))}"
            )
        clauses.append(f"status = '{status}'")

    creator_id = args.get("creator_id")
    if creator_id:
        clauses.append(f"creator_id = '{creator_id}'")

    project_id = args.get("project_id")
    if project_id:
        clauses.append(f"project_id = '{project_id}'")

    if not clauses:
        return None
    return " AND ".join(clauses)


def _parse_pagination(args):
    """
    Extract and validate page / per_page from query arguments.
    """
    page = args.get("page", 1, type=int)
    per_page = args.get("per_page", 20, type=int)

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    if per_page > 100:
        per_page = 100

    return page, per_page


class AssetSearchResource(Resource):
    """
    GET /data/global-assets/search

    Full-text search across the global asset library.

    Query parameters:
        q           — search keyword (required, min 1 char)
        category_id — filter by category UUID
        category_slug — filter by category slug
        status      — filter by status (draft / reviewed / archived)
        creator_id  — filter by creator UUID
        project_id  — filter by source project UUID
        sort        — relevance / newest / oldest / most_used / name_asc / name_desc
        page        — page number (default 1)
        per_page    — results per page (default 20, max 100)

    Returns:
        {
            hits: [...],
            total_hits: int,
            page: int,
            per_page: int,
            processing_time_ms: int,
            facets: { categories: {...}, statuses: {...} }
        }
    """

    @jwt_required()
    def get(self):
        from zou.app.services import asset_search_service

        q = request.args.get("q", "").strip()
        if not q:
            raise WrongParameterException("q (search query) is required.")

        sort_param = request.args.get("sort", "relevance")
        if sort_param not in VALID_SORT_OPTIONS:
            raise WrongParameterException(
                f"Invalid sort '{sort_param}'. "
                f"Must be one of: {', '.join(sorted(VALID_SORT_OPTIONS))}"
            )

        page, per_page = _parse_pagination(request.args)
        filter_expr = _build_filters(request.args)
        sort_rules = SORT_TO_MEILI.get(sort_param)  # None for relevance

        start = time.time()

        result = asset_search_service.search(
            query=q,
            filter_expr=filter_expr,
            sort=sort_rules,
            page=page,
            per_page=per_page,
        )

        elapsed_ms = int((time.time() - start) * 1000)
        result["processing_time_ms"] = elapsed_ms

        return result, 200


class AssetSearchByTagsResource(Resource):
    """
    GET /data/global-assets/search/by-tags

    Search assets that match ALL provided tags.

    Query parameters:
        tags     — comma-separated tag list (required)
        page     — page number (default 1)
        per_page — results per page (default 20, max 100)
    """

    @jwt_required()
    def get(self):
        from zou.app.services import asset_search_service

        tags_raw = request.args.get("tags", "").strip()
        if not tags_raw:
            raise WrongParameterException(
                "tags parameter is required (comma-separated)."
            )

        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        if not tags:
            raise WrongParameterException(
                "At least one non-empty tag is required."
            )

        page, per_page = _parse_pagination(request.args)

        result = asset_search_service.search_by_tags(
            tags=tags,
            page=page,
            per_page=per_page,
        )
        return result, 200


class AssetSearchSimilarResource(Resource):
    """
    GET /data/global-assets/<asset_id>/similar

    Find assets similar to the given asset (same category, overlapping tags,
    similar style keywords).

    Query parameters:
        limit — max results (default 10, max 50)
    """

    @jwt_required()
    def get(self, asset_id):
        from zou.app.services import asset_search_service

        limit = request.args.get("limit", 10, type=int)
        if limit < 1:
            limit = 1
        if limit > 50:
            limit = 50

        result = asset_search_service.find_similar(
            asset_id=asset_id,
            limit=limit,
        )
        return result, 200


class AssetSearchSuggestionsResource(Resource):
    """
    GET /data/global-assets/search/suggestions

    Autocomplete suggestions for partial input.

    Query parameters:
        q     — partial input (required, min 2 chars)
        limit — number of suggestions (default 5, max 20)
    """

    @jwt_required()
    def get(self):
        from zou.app.services import asset_search_service

        q = request.args.get("q", "").strip()
        if len(q) < 2:
            raise WrongParameterException(
                "q must be at least 2 characters for suggestions."
            )

        limit = request.args.get("limit", 5, type=int)
        if limit < 1:
            limit = 1
        if limit > 20:
            limit = 20

        suggestions = asset_search_service.get_suggestions(
            query=q,
            limit=limit,
        )
        return suggestions, 200


class AssetSearchFacetsResource(Resource):
    """
    GET /data/global-assets/search/facets

    Return faceted counts for categories and statuses across
    the entire global asset index.
    """

    @jwt_required()
    def get(self):
        from zou.app.services import asset_search_service

        facets = asset_search_service.get_facets()
        return facets, 200


class AssetSearchIndexResource(Resource):
    """
    POST /data/global-assets/search/reindex
        Trigger a full rebuild of the global-assets search index.
        Admin only.

    GET /data/global-assets/search/index-status
        Return current index statistics (document count, last update, etc.).
        Admin only.
    """

    @jwt_required()
    def post(self):
        if not permissions.has_admin_permissions():
            raise permissions.PermissionDenied

        from zou.app.services import asset_search_service

        asset_search_service.reindex()

        return {
            "status": "started",
            "message": "Global asset search index rebuild initiated.",
        }, 202

    @jwt_required()
    def get(self):
        if not permissions.has_admin_permissions():
            raise permissions.PermissionDenied

        from zou.app.services import asset_search_service

        status = asset_search_service.get_index_status()
        return status, 200
