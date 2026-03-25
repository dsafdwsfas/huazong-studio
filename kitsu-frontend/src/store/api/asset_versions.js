import client from '@/store/api/client'

export default {
  /**
   * Get paginated list of versions for a global asset.
   * @param {string} assetId
   * @param {number} page
   * @param {number} perPage
   * @returns {Promise<{ data: Array, total: number, page: number }>}
   */
  getVersions(assetId, page = 1, perPage = 20) {
    return client.pget(
      `/api/data/global-assets/${assetId}/versions?page=${page}&per_page=${perPage}`
    )
  },

  /**
   * Get a single asset version by ID.
   * @param {string} versionId
   * @returns {Promise<Object>}
   */
  getVersion(versionId) {
    return client.pget(`/api/data/asset-versions/${versionId}`)
  },

  /**
   * Get the diff/changelog for a specific version.
   * @param {string} versionId
   * @returns {Promise<Object>}
   */
  getVersionDiff(versionId) {
    return client.pget(`/api/data/asset-versions/${versionId}/diff`)
  },

  /**
   * Compare two versions side by side.
   * @param {string} versionA
   * @param {string} versionB
   * @returns {Promise<Object>}
   */
  compareVersions(versionA, versionB) {
    return client.pget(
      `/api/data/asset-versions/compare?version_a=${versionA}&version_b=${versionB}`
    )
  },

  /**
   * Restore a global asset to a specific version.
   * @param {string} assetId
   * @param {string} versionId
   * @returns {Promise<Object>}
   */
  restoreVersion(assetId, versionId) {
    return client.ppost(
      `/api/data/global-assets/${assetId}/versions/${versionId}/restore`
    )
  },

  /**
   * Get the latest version of a global asset.
   * @param {string} assetId
   * @returns {Promise<Object>}
   */
  getLatestVersion(assetId) {
    return client.pget(`/api/data/global-assets/${assetId}/versions/latest`)
  }
}
