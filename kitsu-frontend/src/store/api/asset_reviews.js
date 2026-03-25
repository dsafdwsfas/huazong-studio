import client from '@/store/api/client'

export default {
  /**
   * Get paginated review queue with optional status filter.
   * @param {string|null} status - 'pending' | 'approved' | 'rejected' | 'revision_requested' | null
   * @param {number} page
   * @param {number} perPage
   * @returns {Promise<{ data: Array, total: number, page: number }>}
   */
  getReviewQueue(status, page = 1, perPage = 20) {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (page) params.append('page', page)
    if (perPage) params.append('per_page', perPage)
    const q = params.toString()
    return client.pget(`/api/data/asset-reviews/queue${q ? '?' + q : ''}`)
  },

  /**
   * Get review statistics (pending count, today approved/rejected, avg time).
   * @returns {Promise<{ pending: number, approved_today: number, rejected_today: number, avg_review_hours: number }>}
   */
  getReviewStats() {
    return client.pget('/api/data/asset-reviews/stats')
  },

  /**
   * Submit an asset for review.
   * @param {string} assetId
   * @param {string} comment - Submission note
   * @returns {Promise<Object>} The created review object
   */
  submitForReview(assetId, comment) {
    return client.ppost('/api/data/asset-reviews', {
      asset_id: assetId,
      comment
    })
  },

  /**
   * Approve a review.
   * @param {string} reviewId
   * @param {string} comment
   * @returns {Promise<Object>}
   */
  approveReview(reviewId, comment) {
    return client.pput(`/api/data/asset-reviews/${reviewId}/approve`, {
      comment
    })
  },

  /**
   * Reject a review.
   * @param {string} reviewId
   * @param {string} comment
   * @returns {Promise<Object>}
   */
  rejectReview(reviewId, comment) {
    return client.pput(`/api/data/asset-reviews/${reviewId}/reject`, {
      comment
    })
  },

  /**
   * Request revision for a review.
   * @param {string} reviewId
   * @param {string} comment
   * @returns {Promise<Object>}
   */
  requestRevision(reviewId, comment) {
    return client.pput(`/api/data/asset-reviews/${reviewId}/revision`, {
      comment
    })
  },

  /**
   * Get a single review by ID.
   * @param {string} reviewId
   * @returns {Promise<Object>}
   */
  getReview(reviewId) {
    return client.pget(`/api/data/asset-reviews/${reviewId}`)
  },

  /**
   * Get all reviews for a specific asset.
   * @param {string} assetId
   * @returns {Promise<Array>}
   */
  getAssetReviews(assetId) {
    return client.pget(`/api/data/global-assets/${assetId}/reviews`)
  },

  /**
   * Get current user's submissions with optional status filter.
   * @param {string|null} status
   * @param {number} page
   * @param {number} perPage
   * @returns {Promise<{ data: Array, total: number, page: number }>}
   */
  getMySubmissions(status, page = 1, perPage = 20) {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (page) params.append('page', page)
    if (perPage) params.append('per_page', perPage)
    const q = params.toString()
    return client.pget(`/api/data/asset-reviews/my-submissions${q ? '?' + q : ''}`)
  },

  /**
   * Batch approve multiple reviews.
   * @param {Array<string>} reviewIds
   * @param {string} comment
   * @returns {Promise<Object>}
   */
  batchApprove(reviewIds, comment) {
    return client.ppost('/api/data/asset-reviews/batch-approve', {
      review_ids: reviewIds,
      comment
    })
  },

  /**
   * Batch reject multiple reviews.
   * @param {Array<string>} reviewIds
   * @param {string} comment
   * @returns {Promise<Object>}
   */
  batchReject(reviewIds, comment) {
    return client.ppost('/api/data/asset-reviews/batch-reject', {
      review_ids: reviewIds,
      comment
    })
  }
}
