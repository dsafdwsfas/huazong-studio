import superagent from 'superagent'
import client from '@/store/api/client'

/**
 * Handle raw blob responses (superagent does not go through client.request
 * because handleResponse would strip the binary body).
 */
function blobPost(path, data) {
  return superagent
    .post(path)
    .send(data)
    .responseType('blob')
    .then((res) => res.body)
    .catch((err) => {
      if (err?.response?.status === 401) {
        // delegate to global 401 handler
        throw err
      }
      err.body = err?.response?.body || ''
      throw err
    })
}

export default {
  // ── Export ────────────────────────────────────────────────

  /**
   * Export selected assets as a ZIP blob.
   * @param {string[]} assetIds
   * @param {Object}   options - { include_files, include_versions }
   * @returns {Promise<Blob>}
   */
  exportAssets(assetIds, options = {}) {
    return blobPost('/api/data/global-assets/export', {
      asset_ids: assetIds,
      ...options
    })
  },

  /**
   * Export every asset in the library.
   * @param {Object} options
   * @returns {Promise<Blob>}
   */
  exportAll(options = {}) {
    return blobPost('/api/data/global-assets/export/all', options)
  },

  /**
   * Export all assets belonging to a category.
   * @param {string} categoryId
   * @param {Object} options
   * @returns {Promise<Blob>}
   */
  exportByCategory(categoryId, options = {}) {
    return blobPost(
      `/api/data/global-assets/export/category/${categoryId}`,
      options
    )
  },

  /**
   * Export all global assets linked to a project.
   * @param {string} projectId
   * @param {Object} options
   * @returns {Promise<Blob>}
   */
  exportByProject(projectId, options = {}) {
    return blobPost(
      `/api/data/projects/${projectId}/export-assets`,
      options
    )
  },

  // ── Import ───────────────────────────────────────────────

  /**
   * Validate an import ZIP without actually importing.
   * @param {File} file
   * @returns {Promise<Object>} - preview / validation result
   */
  validateImport(file) {
    const formData = new FormData()
    formData.append('file', file)
    return client.ppost('/api/data/global-assets/import/validate', formData)
  },

  /**
   * Execute the import.
   * @param {File}   file
   * @param {string} mode - 'merge' | 'skip' | 'overwrite' | 'create_new'
   * @returns {Promise<Object>} - import result stats
   */
  importAssets(file, mode = 'merge') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('mode', mode)
    return client.ppost('/api/data/global-assets/import', formData)
  },

  /**
   * Bulk-import assets from a JSON payload (no file upload).
   * @param {Array} assets
   * @returns {Promise<Object>}
   */
  importJson(assets) {
    return client.ppost('/api/data/global-assets/import/json', { assets })
  }
}
