"""
Asset node graph service (Phase 4.3 — Intelligent Node System).

Provides CRUD for graph nodes/links, BFS-based graph traversal,
and automatic relationship discovery for global assets.
"""

import logging
from collections import deque

from sqlalchemy import or_

from zou.app import db
from zou.app.models.asset_node import AssetNode, AssetNodeLink
from zou.app.models.global_asset import GlobalAsset, GlobalAssetProjectLink
from zou.app.services.exception import WrongParameterException

logger = logging.getLogger(__name__)


class AssetNodeNotFoundException(Exception):
    pass


class AssetNodeLinkNotFoundException(Exception):
    pass


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _serialize_node(node):
    """Serialize an AssetNode to dict."""
    if node is None:
        return None
    result = node.serialize()
    if isinstance(result.get("node_type"), tuple):
        result["node_type"] = result["node_type"][0]
    return result


def _serialize_link(link):
    """Serialize an AssetNodeLink to dict."""
    if link is None:
        return None
    result = link.serialize()
    if isinstance(result.get("link_type"), tuple):
        result["link_type"] = result["link_type"][0]
    return result


# ---------------------------------------------------------------------------
# Node CRUD
# ---------------------------------------------------------------------------

def get_or_create_node(node_type, ref_id, label=None, metadata=None):
    """
    Get an existing node or create one (idempotent).

    Returns:
        dict: serialized node
    """
    node = AssetNode.get_by(node_type=node_type, ref_id=ref_id)
    if node is not None:
        # Update label/metadata if provided and changed
        changed = False
        if label is not None and node.label != label:
            node.label = label
            changed = True
        if metadata is not None and node.metadata_ != metadata:
            node.metadata_ = metadata
            changed = True
        if changed:
            node.save()
        return _serialize_node(node)

    node = AssetNode.create(
        node_type=node_type,
        ref_id=ref_id,
        label=label or "",
        metadata_=metadata or {},
    )
    return _serialize_node(node)


def get_node(node_id):
    """
    Get a single node by ID.

    Raises:
        AssetNodeNotFoundException
    """
    node = AssetNode.get(node_id)
    if node is None:
        raise AssetNodeNotFoundException()
    return _serialize_node(node)


def get_node_raw(node_id):
    """Get the ORM instance (internal use)."""
    node = AssetNode.get(node_id)
    if node is None:
        raise AssetNodeNotFoundException()
    return node


def update_node_position(node_id, pos_x, pos_y):
    """
    Save user-adjusted graph position for a node.

    Returns:
        dict: serialized node
    """
    node = get_node_raw(node_id)
    node.pos_x = pos_x
    node.pos_y = pos_y
    node.save()
    return _serialize_node(node)


def delete_node(node_id):
    """
    Delete a node and all its connected edges.

    Returns:
        bool
    """
    node = get_node_raw(node_id)

    # Delete all links where this node is source or target
    AssetNodeLink.query.filter(
        or_(
            AssetNodeLink.source_node_id == node.id,
            AssetNodeLink.target_node_id == node.id,
        )
    ).delete(synchronize_session="fetch")

    node.delete()
    return True


# ---------------------------------------------------------------------------
# Link CRUD
# ---------------------------------------------------------------------------

def create_link(source_node_id, target_node_id, link_type,
                weight=1.0, metadata=None):
    """
    Create an edge between two nodes (idempotent: updates weight if exists).

    Returns:
        dict: serialized link
    """
    existing = AssetNodeLink.get_by(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        link_type=link_type,
    )
    if existing is not None:
        changed = False
        if existing.weight != weight:
            existing.weight = weight
            changed = True
        if metadata is not None and existing.metadata_ != metadata:
            existing.metadata_ = metadata
            changed = True
        if changed:
            existing.save()
        return _serialize_link(existing)

    # Validate both nodes exist
    if AssetNode.get(source_node_id) is None:
        raise WrongParameterException("Source node not found.")
    if AssetNode.get(target_node_id) is None:
        raise WrongParameterException("Target node not found.")

    link = AssetNodeLink.create(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        link_type=link_type,
        weight=weight,
        metadata_=metadata or {},
    )
    return _serialize_link(link)


def delete_link(link_id):
    """
    Delete an edge by ID.

    Returns:
        bool
    """
    link = AssetNodeLink.get(link_id)
    if link is None:
        raise AssetNodeLinkNotFoundException()
    link.delete()
    return True


def get_node_links(node_id):
    """
    Return all edges (inbound + outbound) for a node.

    Returns:
        list[dict]
    """
    links = AssetNodeLink.query.filter(
        or_(
            AssetNodeLink.source_node_id == node_id,
            AssetNodeLink.target_node_id == node_id,
        )
    ).all()
    return [_serialize_link(l) for l in links]


# ---------------------------------------------------------------------------
# Graph queries (BFS)
# ---------------------------------------------------------------------------

def get_graph(center_node_id=None, depth=2,
              node_types=None, link_types=None):
    """
    BFS traversal from a center node. Returns the subgraph within *depth*
    hops.  If center_node_id is None, returns the full graph (filtered).

    Args:
        center_node_id: starting node (optional)
        depth: BFS depth limit
        node_types: list of node_type codes to include (optional filter)
        link_types: list of link_type codes to include (optional filter)

    Returns:
        dict: {nodes: [...], links: [...]}
    """
    if center_node_id is None:
        return _get_full_graph(node_types, link_types)

    visited_node_ids = set()
    collected_links = []
    queue = deque()

    visited_node_ids.add(str(center_node_id))
    queue.append((str(center_node_id), 0))

    while queue:
        current_id, current_depth = queue.popleft()
        if current_depth >= depth:
            continue

        # Fetch all edges touching the current node
        link_query = AssetNodeLink.query.filter(
            or_(
                AssetNodeLink.source_node_id == current_id,
                AssetNodeLink.target_node_id == current_id,
            )
        )
        if link_types:
            link_query = link_query.filter(
                AssetNodeLink.link_type.in_(link_types)
            )

        edges = link_query.all()
        for edge in edges:
            src = str(edge.source_node_id)
            tgt = str(edge.target_node_id)
            neighbour = tgt if src == current_id else src

            collected_links.append(edge)

            if neighbour not in visited_node_ids:
                visited_node_ids.add(neighbour)
                queue.append((neighbour, current_depth + 1))

    # Fetch all visited nodes in one query
    nodes = AssetNode.query.filter(
        AssetNode.id.in_(list(visited_node_ids))
    ).all()

    if node_types:
        nodes = [n for n in nodes if n.node_type.code in node_types]
        valid_ids = {str(n.id) for n in nodes}
        collected_links = [
            l for l in collected_links
            if str(l.source_node_id) in valid_ids
            and str(l.target_node_id) in valid_ids
        ]

    # Deduplicate links
    seen_link_ids = set()
    unique_links = []
    for l in collected_links:
        lid = str(l.id)
        if lid not in seen_link_ids:
            seen_link_ids.add(lid)
            unique_links.append(l)

    return {
        "nodes": [_serialize_node(n) for n in nodes],
        "links": [_serialize_link(l) for l in unique_links],
    }


def _get_full_graph(node_types=None, link_types=None):
    """Return the entire graph, optionally filtered by types."""
    node_query = AssetNode.query
    if node_types:
        node_query = node_query.filter(AssetNode.node_type.in_(node_types))
    nodes = node_query.all()

    link_query = AssetNodeLink.query
    if link_types:
        link_query = link_query.filter(
            AssetNodeLink.link_type.in_(link_types)
        )
    if node_types:
        node_ids = [n.id for n in nodes]
        link_query = link_query.filter(
            AssetNodeLink.source_node_id.in_(node_ids),
            AssetNodeLink.target_node_id.in_(node_ids),
        )
    links = link_query.all()

    return {
        "nodes": [_serialize_node(n) for n in nodes],
        "links": [_serialize_link(l) for l in links],
    }


def get_asset_graph(asset_id, depth=2):
    """
    Convenience: get the graph centred on a global asset.

    Returns:
        dict: {nodes, links}
    """
    node = AssetNode.get_by(node_type="asset", ref_id=asset_id)
    if node is None:
        # Auto-create node on the fly
        asset = GlobalAsset.get(asset_id)
        if asset is None:
            raise WrongParameterException("Asset not found.")
        result = get_or_create_node(
            "asset", asset_id, label=asset.name
        )
        return get_graph(center_node_id=result["id"], depth=depth)
    return get_graph(center_node_id=node.id, depth=depth)


def get_project_graph(project_id):
    """
    Get the asset graph for a specific project (all linked assets +
    their relationships).

    Returns:
        dict: {nodes, links}
    """
    node = AssetNode.get_by(node_type="project", ref_id=project_id)
    if node is None:
        return {"nodes": [], "links": []}
    return get_graph(center_node_id=node.id, depth=2)


# ---------------------------------------------------------------------------
# Automatic relationship discovery
# ---------------------------------------------------------------------------

def auto_link_asset(asset_id):
    """
    Automatically discover and create graph relationships for a
    GlobalAsset.  Idempotent — safe to call repeatedly.

    Creates:
        1. asset -> category  (belongs_to)
        2. project -> asset   (contains) via GlobalAssetProjectLink
        3. asset -> creator   (created_by)
        4. co-occurrence edges for assets in the same project+category
        5. same_style edges for assets sharing style_keywords
    """
    asset = GlobalAsset.get(asset_id)
    if asset is None:
        raise WrongParameterException("Asset not found.")

    # 1. Ensure asset node
    asset_node = _ensure_node("asset", asset.id, asset.name)

    # 2. belongs_to category
    if asset.category_id:
        cat_node = _ensure_node(
            "category", asset.category_id,
            label=asset.category_rel.name if asset.category_rel else None,
        )
        _ensure_link(asset_node["id"], cat_node["id"], "belongs_to")

    # 3. contains (project -> asset)
    project_links = GlobalAssetProjectLink.query.filter_by(
        global_asset_id=asset.id
    ).all()
    for pl in project_links:
        from zou.app.models.project import Project
        project = Project.get(pl.project_id)
        if project:
            proj_node = _ensure_node("project", project.id, project.name)
            _ensure_link(proj_node["id"], asset_node["id"], "contains")

    # 4. created_by
    if asset.creator_id:
        from zou.app.models.person import Person
        person = Person.get(asset.creator_id)
        person_label = ""
        if person:
            person_label = (
                f"{person.first_name} {person.last_name}".strip()
                or str(person.id)
            )
        creator_node = _ensure_node(
            "person", asset.creator_id, label=person_label
        )
        _ensure_link(asset_node["id"], creator_node["id"], "created_by")

    # 5. co_occurs — same category + same project
    if asset.category_id and project_links:
        project_ids = [pl.project_id for pl in project_links]
        sibling_assets = (
            GlobalAsset.query()
            .join(
                GlobalAssetProjectLink,
                GlobalAsset.id == GlobalAssetProjectLink.global_asset_id,
            )
            .filter(
                GlobalAssetProjectLink.project_id.in_(project_ids),
                GlobalAsset.category_id == asset.category_id,
                GlobalAsset.id != asset.id,
            )
            .all()
        )
        for sibling in sibling_assets:
            sib_node = _ensure_node("asset", sibling.id, sibling.name)
            _ensure_link(
                asset_node["id"], sib_node["id"], "co_occurs", weight=0.5
            )

    # 6. same_style — shared style_keywords
    asset_keywords = set(asset.style_keywords or [])
    if asset_keywords:
        candidates = (
            GlobalAsset.query()
            .filter(
                GlobalAsset.id != asset.id,
                GlobalAsset.style_keywords != None,  # noqa: E711
                GlobalAsset.style_keywords != [],
            )
            .all()
        )
        for candidate in candidates:
            cand_keywords = set(candidate.style_keywords or [])
            overlap = asset_keywords & cand_keywords
            if overlap:
                cand_node = _ensure_node(
                    "asset", candidate.id, candidate.name
                )
                # Weight proportional to overlap
                w = len(overlap) / max(
                    len(asset_keywords | cand_keywords), 1
                )
                _ensure_link(
                    asset_node["id"],
                    cand_node["id"],
                    "same_style",
                    weight=round(w, 3),
                )

    db.session.commit()
    return get_asset_graph(asset_id)


def rebuild_project_graph(project_id):
    """
    Rebuild the complete graph for a project by running auto_link_asset
    on every linked asset.

    Returns:
        dict: {nodes, links} — the project graph
    """
    project_links = GlobalAssetProjectLink.query.filter_by(
        project_id=project_id
    ).all()

    for pl in project_links:
        try:
            auto_link_asset(pl.global_asset_id)
        except Exception:
            logger.warning(
                "Failed to auto-link asset %s", pl.global_asset_id,
                exc_info=True,
            )

    return get_project_graph(project_id)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def get_graph_stats():
    """
    Return aggregate statistics about the graph.

    Returns:
        dict: {total_nodes, total_links, nodes_by_type, links_by_type}
    """
    total_nodes = AssetNode.query.count()
    total_links = AssetNodeLink.query.count()

    nodes_by_type = {}
    for row in (
        db.session.query(AssetNode.node_type, db.func.count(AssetNode.id))
        .group_by(AssetNode.node_type)
        .all()
    ):
        key = row[0].code if hasattr(row[0], "code") else row[0]
        nodes_by_type[key] = row[1]

    links_by_type = {}
    for row in (
        db.session.query(
            AssetNodeLink.link_type, db.func.count(AssetNodeLink.id)
        )
        .group_by(AssetNodeLink.link_type)
        .all()
    ):
        key = row[0].code if hasattr(row[0], "code") else row[0]
        links_by_type[key] = row[1]

    return {
        "total_nodes": total_nodes,
        "total_links": total_links,
        "nodes_by_type": nodes_by_type,
        "links_by_type": links_by_type,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_node(node_type, ref_id, label=None):
    """Get or create a node without committing (batch-friendly)."""
    node = AssetNode.get_by(node_type=node_type, ref_id=ref_id)
    if node is not None:
        if label and node.label != label:
            node.label = label
            db.session.add(node)
        return _serialize_node(node)

    node = AssetNode.create_no_commit(
        node_type=node_type,
        ref_id=ref_id,
        label=label or "",
        metadata_={},
    )
    db.session.flush()
    return _serialize_node(node)


def _ensure_link(source_id, target_id, link_type, weight=1.0):
    """Get or create a link without committing (batch-friendly)."""
    existing = AssetNodeLink.get_by(
        source_node_id=source_id,
        target_node_id=target_id,
        link_type=link_type,
    )
    if existing is not None:
        if existing.weight != weight:
            existing.weight = weight
            db.session.add(existing)
        return _serialize_link(existing)

    link = AssetNodeLink.create_no_commit(
        source_node_id=source_id,
        target_node_id=target_id,
        link_type=link_type,
        weight=weight,
        metadata_={},
    )
    db.session.flush()
    return _serialize_link(link)
