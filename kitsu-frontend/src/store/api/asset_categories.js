import client from '@/store/api/client'

export default {
  /**
   * Get the full category tree (hierarchical).
   * @returns {Promise<Array>}
   */
  getCategoryTree() {
    return client.pget('/api/data/asset-categories')
  },

  /**
   * Get a single category by ID.
   * @param {string} id
   * @returns {Promise<Object>}
   */
  getCategory(id) {
    return client.pget(`/api/data/asset-categories/${id}`)
  },

  /**
   * Create a new category.
   * @param {Object} data - { name, slug, description, icon, color, parent_id }
   * @returns {Promise<Object>}
   */
  createCategory(data) {
    return client.ppost('/api/data/asset-categories', data)
  },

  /**
   * Update an existing category.
   * @param {string} id
   * @param {Object} data - Partial category fields to update
   * @returns {Promise<Object>}
   */
  updateCategory(id, data) {
    return client.pput(`/api/data/asset-categories/${id}`, data)
  },

  /**
   * Delete a category.
   * @param {string} id
   * @returns {Promise<Object>}
   */
  deleteCategory(id) {
    return client.pdel(`/api/data/asset-categories/${id}`)
  },

  /**
   * Batch reorder categories.
   * @param {Array} orders - [{ id, sort_order }]
   * @returns {Promise<Object>}
   */
  reorderCategories(orders) {
    return client.pput('/api/data/asset-categories/reorder', { orders })
  },

  /**
   * Get asset count statistics per category.
   * @returns {Promise<Object>}
   */
  getCategoryStats() {
    return client.pget('/api/data/asset-categories/stats')
  },

  /**
   * Initialize default preset categories.
   * @returns {Promise<Object>}
   */
  initDefaultCategories() {
    return client.ppost('/api/data/asset-categories/init')
  }
}
