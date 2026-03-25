import client from '@/store/api/client'

export default {
  /**
   * Full-text search across global assets via MeiliSearch.
   * @param {Object} params - Search parameters
   * @param {string} params.q - Search query
   * @param {string} params.categoryId - Filter by category ID
   * @param {string} params.categorySlug - Filter by category slug
   * @param {string} params.status - Filter by status (draft|approved|archived)
   * @param {string} params.creatorId - Filter by creator
   * @param {string} params.projectId - Filter by linked project
   * @param {string} params.sort - Sort field (relevance|newest|oldest|most_used|name)
   * @param {number} params.page - Page number
   * @param {number} params.perPage - Results per page
   * @returns {Promise<{ hits, totalHits, page, perPage, processingTimeMs }>}
   */
  search(params) {
    const query = new URLSearchParams()
    if (params.q) query.set('q', params.q)
    if (params.categoryId) query.set('category_id', params.categoryId)
    if (params.categorySlug) query.set('category_slug', params.categorySlug)
    if (params.status) query.set('status', params.status)
    if (params.creatorId) query.set('creator_id', params.creatorId)
    if (params.projectId) query.set('project_id', params.projectId)
    if (params.sort) query.set('sort', params.sort)
    if (params.page) query.set('page', params.page)
    if (params.perPage) query.set('per_page', params.perPage)
    return client.pget(`/api/data/global-assets/search?${query}`)
  },

  /**
   * Search assets by multiple tags (intersection).
   * @param {string[]} tags - Array of tag strings
   * @param {number} page
   * @param {number} perPage
   * @returns {Promise<{ hits, totalHits, page, perPage }>}
   */
  searchByTags(tags, page = 1, perPage = 20) {
    return client.pget(
      `/api/data/global-assets/search/by-tags?tags=${tags.join(',')}&page=${page}&per_page=${perPage}`
    )
  },

  /**
   * Get similar assets based on tags and metadata.
   * @param {string} assetId
   * @param {number} limit
   * @returns {Promise<Array>}
   */
  getSimilar(assetId, limit = 10) {
    return client.pget(
      `/api/data/global-assets/${assetId}/similar?limit=${limit}`
    )
  },

  /**
   * Get search suggestions (autocomplete) for partial query.
   * @param {string} q - Partial query string
   * @param {number} limit
   * @returns {Promise<Array<{ name, category, thumbnail_url }>>}
   */
  getSuggestions(q, limit = 5) {
    return client.pget(
      `/api/data/global-assets/search/suggestions?q=${encodeURIComponent(q)}&limit=${limit}`
    )
  },

  /**
   * Get facet counts for search filtering sidebar.
   * @returns {Promise<{ categories, statuses, creators }>}
   */
  getFacets() {
    return client.pget('/api/data/global-assets/search/facets')
  },

  /**
   * Trigger a full reindex of the search engine.
   * @returns {Promise<{ task_id, status }>}
   */
  reindex() {
    return client.ppost('/api/data/global-assets/search/reindex')
  },

  /**
   * Get the current status of the search index.
   * @returns {Promise<{ indexed_count, pending_count, last_indexed_at }>}
   */
  getIndexStatus() {
    return client.pget('/api/data/global-assets/search/index-status')
  }
}
