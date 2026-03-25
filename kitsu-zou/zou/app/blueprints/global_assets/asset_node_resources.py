"""
Asset Node Graph API Resources

Provides endpoints for the intelligent node/graph system:
- Graph queries (full, per-asset, per-project)
- Node detail and position updates
- Manual link creation/deletion
- Auto-linking triggers
- Project graph rebuild
- Graph statistics
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
from zou.app.services import asset_node_service
from zou.app.services.exception import WrongParameterException
from zou.app.utils import permissions

logger = logging.getLogger(__name__)

MAX_GRAPH_DEPTH = 5
DEFAULT_GRAPH_DEPTH = 2


class AssetGraphResource(Resource):
    """
    GET /data/asset-graph
    Query the full asset graph with optional filters.

    Query params:
    - center_node_id: Center node ID (optional)
    - depth: Expansion depth (default 2, max 5)
    - node_types: Comma-separated node type filter
    - link_types: Comma-separated link type filter

    Returns: { nodes: [...], links: [...], stats: {...} }
    """

    @jwt_required()
    def get(self):
        center_node_id = request.args.get("center_node_id")
        depth = request.args.get("depth", DEFAULT_GRAPH_DEPTH, type=int)
        if depth < 1 or depth > MAX_GRAPH_DEPTH:
            raise WrongParameterException(
                f"depth must be between 1 and {MAX_GRAPH_DEPTH}."
            )

        node_types = request.args.get("node_types")
        if node_types:
            node_types = [t.strip() for t in node_types.split(",") if t.strip()]
        else:
            node_types = None

        link_types = request.args.get("link_types")
        if link_types:
            link_types = [t.strip() for t in link_types.split(",") if t.strip()]
        else:
            link_types = None

        graph = asset_node_service.get_asset_graph(
            center_node_id=center_node_id,
            depth=depth,
            node_types=node_types,
            link_types=link_types,
        )
        return graph, 200


class AssetNodeGraphResource(Resource):
    """
    GET /data/global-assets/<asset_id>/graph
    Get the relationship graph for a specific asset.

    Query params:
    - depth: Expansion depth (default 2, max 5)
    """

    @jwt_required()
    def get(self, asset_id):
        depth = request.args.get("depth", DEFAULT_GRAPH_DEPTH, type=int)
        if depth < 1 or depth > MAX_GRAPH_DEPTH:
            raise WrongParameterException(
                f"depth must be between 1 and {MAX_GRAPH_DEPTH}."
            )

        graph = asset_node_service.get_asset_node_graph(
            asset_id=asset_id,
            depth=depth,
        )
        return graph, 200


class ProjectAssetGraphResource(Resource):
    """
    GET /data/projects/<project_id>/asset-graph
    Get the asset relationship graph for a project.
    """

    @jwt_required()
    def get(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        depth = request.args.get("depth", DEFAULT_GRAPH_DEPTH, type=int)
        if depth < 1 or depth > MAX_GRAPH_DEPTH:
            raise WrongParameterException(
                f"depth must be between 1 and {MAX_GRAPH_DEPTH}."
            )

        graph = asset_node_service.get_project_asset_graph(
            project_id=project_id,
            depth=depth,
        )
        return graph, 200


class AssetNodeResource(Resource):
    """
    GET /data/asset-nodes/<node_id>
    Get node details including all connected links.

    PUT /data/asset-nodes/<node_id>/position
    Update node position (pos_x, pos_y) for personal graph layout.
    Allowed for all authenticated users.
    """

    @jwt_required()
    def get(self, node_id):
        node = asset_node_service.get_node_detail(node_id)
        return node, 200

    @jwt_required()
    def put(self, node_id):
        data = request.json or {}
        pos_x = data.get("pos_x")
        pos_y = data.get("pos_y")

        if pos_x is None and pos_y is None:
            raise WrongParameterException(
                "At least one of pos_x or pos_y is required."
            )

        current_user = persons_service.get_current_user()
        node = asset_node_service.update_node_position(
            node_id=node_id,
            user_id=current_user["id"],
            pos_x=pos_x,
            pos_y=pos_y,
        )
        return node, 200


class AssetNodeLinkResource(Resource):
    """
    POST   /data/asset-node-links
    Manually create a link between two nodes (manager/admin).
    Body: { source_node_id, target_node_id, link_type, weight }

    DELETE /data/asset-node-links/<link_id>
    Delete a link (manager/admin).
    """

    @jwt_required()
    def post(self):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        data = request.json or {}
        source_node_id = data.get("source_node_id")
        target_node_id = data.get("target_node_id")
        link_type = data.get("link_type")

        if not source_node_id:
            raise WrongParameterException("source_node_id is required.")
        if not target_node_id:
            raise WrongParameterException("target_node_id is required.")
        if not link_type:
            raise WrongParameterException("link_type is required.")

        weight = data.get("weight", 1.0)
        metadata = data.get("metadata", {})

        link = asset_node_service.create_node_link(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            link_type=link_type,
            weight=weight,
            metadata=metadata,
        )
        return link, 201

    @jwt_required()
    def delete(self, link_id):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        asset_node_service.delete_node_link(link_id)
        return {"message": "Link deleted."}, 200


class AssetAutoLinkResource(Resource):
    """
    POST /data/global-assets/<asset_id>/auto-link
    Trigger automatic relationship discovery for an asset.
    """

    @jwt_required()
    def post(self, asset_id):
        result = asset_node_service.auto_link_asset(asset_id)
        return result, 200


class ProjectGraphRebuildResource(Resource):
    """
    POST /data/projects/<project_id>/rebuild-graph
    Rebuild the entire project graph (admin/manager only).
    """

    @jwt_required()
    def post(self, project_id):
        if not permissions.has_manager_permissions():
            raise permissions.PermissionDenied

        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        result = asset_node_service.rebuild_project_graph(project_id)
        return result, 200


class AssetGraphStatsResource(Resource):
    """
    GET /data/asset-graph/stats
    Get graph-wide statistics (node counts, link counts, etc.).
    """

    @jwt_required()
    def get(self):
        project_id = request.args.get("project_id")
        stats = asset_node_service.get_graph_stats(project_id=project_id)
        return stats, 200
