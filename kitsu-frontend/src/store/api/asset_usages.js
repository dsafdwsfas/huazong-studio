import client from '@/store/api/client'

export default {
  /**
   * Get usage records for a specific asset.
   * @param {string} assetId
   * @param {number} page
   * @param {number} perPage
   * @returns {Promise<{ data: Array, total: number, page: number }>}
   */
  getAssetUsages(assetId, page = 1, perPage = 20) {
    const params = new URLSearchParams({ page, per_page: perPage })
    return client.pget(
      `/api/data/global-assets/${assetId}/usages?${params.toString()}`
    )
  },

  /**
   * Record a new usage of a global asset.
   * @param {string} assetId
   * @param {Object} data - { project_id, usage_type, entity_id, entity_type, context }
   * @returns {Promise<Object>}
   */
  recordUsage(assetId, data) {
    return client.ppost(`/api/data/global-assets/${assetId}/usages`, data)
  },

  /**
   * Get a single usage record by ID.
   * @param {string} usageId
   * @returns {Promise<Object>}
   */
  getUsage(usageId) {
    return client.pget(`/api/data/asset-usages/${usageId}`)
  },

  /**
   * Delete a usage record.
   * @param {string} usageId
   * @returns {Promise<Object>}
   */
  deleteUsage(usageId) {
    return client.pdel(`/api/data/asset-usages/${usageId}`)
  },

  /**
   * Get all usage records for a specific project.
   * @param {string} projectId
   * @param {number} page
   * @param {number} perPage
   * @returns {Promise<{ data: Array, total: number, page: number }>}
   */
  getProjectUsages(projectId, page = 1, perPage = 20) {
    const params = new URLSearchParams({ page, per_page: perPage })
    return client.pget(
      `/api/data/projects/${projectId}/asset-usages?${params.toString()}`
    )
  },

  /**
   * Get usage statistics for a specific asset.
   * @param {string} assetId
   * @returns {Promise<{ total_usages: number, project_count: number, by_type: Object }>}
   */
  getAssetUsageStats(assetId) {
    return client.pget(`/api/data/global-assets/${assetId}/usage-stats`)
  },

  /**
   * Get the most used assets globally.
   * @param {number} limit
   * @returns {Promise<Array>}
   */
  getMostUsedAssets(limit = 20) {
    return client.pget(`/api/data/global-assets/most-used?limit=${limit}`)
  },

  /**
   * Get usage timeline for an asset (monthly aggregation).
   * @param {string} assetId
   * @returns {Promise<Array<{ month: string, count: number }>>}
   */
  getUsageTimeline(assetId) {
    return client.pget(`/api/data/global-assets/${assetId}/usage-timeline`)
  },

  /**
   * Get cross-project usage distribution for an asset.
   * @param {string} assetId
   * @returns {Promise<Array<{ project_id: string, project_name: string, count: number }>>}
   */
  getCrossProjectUsage(assetId) {
    return client.pget(
      `/api/data/global-assets/${assetId}/cross-project-usage`
    )
  }
}
