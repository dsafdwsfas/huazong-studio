import client from '@/store/api/client'

export default {
  /**
   * Get dashboard summary (total assets, total usage, storage, graph nodes).
   * @returns {Promise<Object>}
   */
  getDashboard() {
    return client.pget('/api/data/asset-stats/dashboard')
  },

  /**
   * Get asset count distribution by category.
   * @returns {Promise<Array<{ category: string, label: string, count: number }>>}
   */
  getCategoryDistribution() {
    return client.pget('/api/data/asset-stats/category-distribution')
  },

  /**
   * Get usage frequency over time.
   * @param {string} period - 'month' | 'week'
   * @param {number} months - Number of months to look back
   * @returns {Promise<Array<{ period: string, count: number }>>}
   */
  getUsageFrequency(period = 'month', months = 12) {
    return client.pget(
      `/api/data/asset-stats/usage-frequency?period=${period}&months=${months}`
    )
  },

  /**
   * Get storage usage stats by category.
   * @returns {Promise<Object>}
   */
  getStorageStats() {
    return client.pget('/api/data/asset-stats/storage')
  },

  /**
   * Get hotness ranking of assets.
   * @param {number} limit - Max number of results
   * @returns {Promise<Array>}
   */
  getHotnessRanking(limit = 20) {
    return client.pget(`/api/data/asset-stats/hotness?limit=${limit}`)
  },

  /**
   * Get asset growth trend over months.
   * @param {number} months - Number of months to look back
   * @returns {Promise<Array<{ month: string, count: number, cumulative: number }>>}
   */
  getGrowthTrend(months = 6) {
    return client.pget(`/api/data/asset-stats/growth?months=${months}`)
  },

  /**
   * Get top asset creators stats.
   * @param {number} limit - Max number of results
   * @returns {Promise<Array<{ person: Object, asset_count: number }>>}
   */
  getCreatorStats(limit = 10) {
    return client.pget(`/api/data/asset-stats/creators?limit=${limit}`)
  },

  /**
   * Get asset stats for a specific project.
   * @param {string} projectId
   * @returns {Promise<Object>}
   */
  getProjectAssetStats(projectId) {
    return client.pget(`/api/data/projects/${projectId}/asset-stats`)
  }
}
