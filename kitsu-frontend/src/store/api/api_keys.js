import client from '@/store/api/client'

export default {
  /**
   * List all API keys for the current user/organization.
   * @returns {Promise<Array>}
   */
  listKeys() {
    return client.pget('/api/open-api/v1/keys')
  },

  /**
   * Create a new API key.
   * @param {Object} data - { name, scopes, rate_limit, expires_at }
   * @returns {Promise<Object>} - Includes plaintext secret (shown only once)
   */
  createKey(data) {
    return client.ppost('/api/open-api/v1/keys', data)
  },

  /**
   * Get a single API key by ID.
   * @param {string} keyId
   * @returns {Promise<Object>}
   */
  getKey(keyId) {
    return client.pget(`/api/open-api/v1/keys/${keyId}`)
  },

  /**
   * Update an existing API key.
   * @param {string} keyId
   * @param {Object} data - Partial fields to update
   * @returns {Promise<Object>}
   */
  updateKey(keyId, data) {
    return client.pput(`/api/open-api/v1/keys/${keyId}`, data)
  },

  /**
   * Delete (revoke) an API key.
   * @param {string} keyId
   * @returns {Promise<Object>}
   */
  deleteKey(keyId) {
    return client.pdel(`/api/open-api/v1/keys/${keyId}`)
  }
}
