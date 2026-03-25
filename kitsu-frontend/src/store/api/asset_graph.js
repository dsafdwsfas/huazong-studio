import client from '@/store/api/client'

export default {
  /**
   * Get the global asset graph.
   * @param {Object} params - { centerNodeId, depth, nodeTypes, linkTypes }
   * @returns {Promise<{ nodes: Array, links: Array }>}
   */
  getGraph(params = {}) {
    const query = new URLSearchParams()
    if (params.centerNodeId) query.set('center_node_id', params.centerNodeId)
    if (params.depth) query.set('depth', params.depth)
    if (params.nodeTypes) query.set('node_types', params.nodeTypes)
    if (params.linkTypes) query.set('link_types', params.linkTypes)
    const q = query.toString()
    return client.pget(`/api/data/asset-graph${q ? '?' + q : ''}`)
  },

  /**
   * Get the graph centered on a specific asset.
   * @param {string} assetId
   * @param {number} depth - Traversal depth (default 2)
   * @returns {Promise<{ nodes: Array, links: Array }>}
   */
  getAssetGraph(assetId, depth = 2) {
    return client.pget(`/api/data/global-assets/${assetId}/graph?depth=${depth}`)
  },

  /**
   * Get the graph for a specific project.
   * @param {string} projectId
   * @returns {Promise<{ nodes: Array, links: Array }>}
   */
  getProjectGraph(projectId) {
    return client.pget(`/api/data/projects/${projectId}/asset-graph`)
  },

  /**
   * Get details for a specific node.
   * @param {string} nodeId
   * @returns {Promise<Object>}
   */
  getNode(nodeId) {
    return client.pget(`/api/data/asset-nodes/${nodeId}`)
  },

  /**
   * Update a node's position on the canvas.
   * @param {string} nodeId
   * @param {number} posX
   * @param {number} posY
   * @returns {Promise<Object>}
   */
  updateNodePosition(nodeId, posX, posY) {
    return client.pput(`/api/data/asset-nodes/${nodeId}/position`, {
      pos_x: posX,
      pos_y: posY
    })
  },

  /**
   * Create a new link between two nodes.
   * @param {Object} data - { source_node_id, target_node_id, link_type, weight }
   * @returns {Promise<Object>}
   */
  createLink(data) {
    return client.ppost('/api/data/asset-node-links', data)
  },

  /**
   * Delete a link.
   * @param {string} linkId
   * @returns {Promise<Object>}
   */
  deleteLink(linkId) {
    return client.pdel(`/api/data/asset-node-links/${linkId}`)
  },

  /**
   * Trigger automatic linking for an asset.
   * @param {string} assetId
   * @returns {Promise<Object>}
   */
  autoLinkAsset(assetId) {
    return client.ppost(`/api/data/global-assets/${assetId}/auto-link`)
  },

  /**
   * Rebuild the graph for a project.
   * @param {string} projectId
   * @returns {Promise<Object>}
   */
  rebuildProjectGraph(projectId) {
    return client.ppost(`/api/data/projects/${projectId}/rebuild-graph`)
  },

  /**
   * Get graph statistics.
   * @returns {Promise<Object>}
   */
  getGraphStats() {
    return client.pget('/api/data/asset-graph/stats')
  }
}
