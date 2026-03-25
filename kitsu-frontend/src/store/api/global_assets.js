import client from '@/store/api/client'

export default {
  /**
   * Get paginated list of global assets with filters.
   * @param {Object} params - { category, status, search, page, per_page }
   * @returns {Promise<{ data: Array, total: number, page: number }>}
   */
  getAssets(params = {}) {
    const urlParams = new URLSearchParams()
    if (params.category) urlParams.append('category', params.category)
    if (params.status) urlParams.append('status', params.status)
    if (params.search) urlParams.append('search', params.search)
    if (params.page) urlParams.append('page', params.page)
    if (params.per_page) urlParams.append('per_page', params.per_page)
    const q = urlParams.toString()
    return client.pget(`/api/data/global-assets${q ? '?' + q : ''}`)
  },

  /**
   * Get a single global asset by ID.
   * @param {string} assetId
   * @returns {Promise<Object>}
   */
  getAsset(assetId) {
    return client.pget(`/api/data/global-assets/${assetId}`)
  },

  /**
   * Create a new global asset.
   * @param {Object} data - { name, category, description, tags, metadata, files }
   * @returns {Promise<Object>}
   */
  createAsset(data) {
    return client.ppost('/api/data/global-assets', data)
  },

  /**
   * Update an existing global asset.
   * @param {string} assetId
   * @param {Object} data - Partial asset fields to update
   * @returns {Promise<Object>}
   */
  updateAsset(assetId, data) {
    return client.pput(`/api/data/global-assets/${assetId}`, data)
  },

  /**
   * Delete a global asset.
   * @param {string} assetId
   * @returns {Promise<Object>}
   */
  deleteAsset(assetId) {
    return client.pdel(`/api/data/global-assets/${assetId}`)
  },

  /**
   * Link a global asset to a project.
   * @param {string} assetId
   * @param {string} projectId
   * @returns {Promise<Object>}
   */
  linkToProject(assetId, projectId) {
    return client.ppost(
      `/api/data/global-assets/${assetId}/projects/${projectId}`
    )
  },

  /**
   * Unlink a global asset from a project.
   * @param {string} assetId
   * @param {string} projectId
   * @returns {Promise<Object>}
   */
  unlinkFromProject(assetId, projectId) {
    return client.pdel(
      `/api/data/global-assets/${assetId}/projects/${projectId}`
    )
  },

  /**
   * Get all global assets linked to a project.
   * @param {string} projectId
   * @param {Object} params - { category, status, search, page, per_page }
   * @returns {Promise<{ data: Array, total: number }>}
   */
  getProjectAssets(projectId, params = {}) {
    const urlParams = new URLSearchParams()
    if (params.category) urlParams.append('category', params.category)
    if (params.status) urlParams.append('status', params.status)
    if (params.search) urlParams.append('search', params.search)
    if (params.page) urlParams.append('page', params.page)
    if (params.per_page) urlParams.append('per_page', params.per_page)
    const q = urlParams.toString()
    return client.pget(
      `/api/data/projects/${projectId}/global-assets${q ? '?' + q : ''}`
    )
  },

  /**
   * Increment usage count for a global asset.
   * @param {string} assetId
   * @returns {Promise<Object>}
   */
  incrementUsage(assetId) {
    return client.ppost(`/api/data/global-assets/${assetId}/usage`)
  },

  /**
   * Update the status of a global asset.
   * @param {string} assetId
   * @param {string} status - 'draft' | 'active' | 'archived'
   * @returns {Promise<Object>}
   */
  updateStatus(assetId, status) {
    return client.pput(`/api/data/global-assets/${assetId}/status`, { status })
  },

  /**
   * Import assets from a project into the global asset library.
   * @param {string} projectId
   * @param {string} assetType - Category to import (e.g. 'character', 'scene')
   * @returns {Promise<{ imported: number, assets: Array }>}
   */
  importFromProject(projectId, assetType) {
    return client.ppost(`/api/data/global-assets/import/${projectId}`, {
      asset_type: assetType
    })
  }
}
