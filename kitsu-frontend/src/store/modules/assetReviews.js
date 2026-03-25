import assetReviewsApi from '@/store/api/asset_reviews'

const state = {
  reviewQueue: [],
  reviewStats: {
    pending: 0,
    approved_today: 0,
    rejected_today: 0,
    avg_review_hours: 0
  },
  currentReview: null,
  assetReviewHistory: [],
  mySubmissions: [],
  isLoading: false,
  queuePagination: {
    page: 1,
    perPage: 20,
    total: 0
  },
  queueFilter: null,
  submissionsPagination: {
    page: 1,
    perPage: 20,
    total: 0
  }
}

const getters = {
  reviewQueue: (state) => state.reviewQueue,
  reviewStats: (state) => state.reviewStats,
  reviewPendingCount: (state) => state.reviewStats.pending || 0,
  currentReview: (state) => state.currentReview,
  assetReviewHistory: (state) => state.assetReviewHistory,
  mySubmissions: (state) => state.mySubmissions,
  reviewIsLoading: (state) => state.isLoading,
  reviewQueuePagination: (state) => state.queuePagination,
  reviewQueueFilter: (state) => state.queueFilter
}

const actions = {
  async loadReviewQueue({ commit, state }) {
    commit('SET_REVIEW_LOADING', true)
    try {
      const data = await assetReviewsApi.getReviewQueue(
        state.queueFilter,
        state.queuePagination.page,
        state.queuePagination.perPage
      )
      commit('SET_REVIEW_QUEUE', data.data || data)
      commit('SET_REVIEW_QUEUE_TOTAL', data.total || 0)
    } catch (err) {
      console.error('Failed to load review queue:', err)
    } finally {
      commit('SET_REVIEW_LOADING', false)
    }
  },

  async loadReviewStats({ commit }) {
    try {
      const stats = await assetReviewsApi.getReviewStats()
      commit('SET_REVIEW_STATS', stats)
    } catch (err) {
      console.error('Failed to load review stats:', err)
    }
  },

  async submitForReview({ dispatch }, { assetId, comment }) {
    const review = await assetReviewsApi.submitForReview(assetId, comment)
    dispatch('loadReviewStats')
    return review
  },

  async approveReview({ commit, dispatch }, { reviewId, comment }) {
    const result = await assetReviewsApi.approveReview(reviewId, comment)
    commit('UPDATE_REVIEW_IN_QUEUE', { reviewId, status: 'approved' })
    dispatch('loadReviewStats')
    return result
  },

  async rejectReview({ commit, dispatch }, { reviewId, comment }) {
    const result = await assetReviewsApi.rejectReview(reviewId, comment)
    commit('UPDATE_REVIEW_IN_QUEUE', { reviewId, status: 'rejected' })
    dispatch('loadReviewStats')
    return result
  },

  async requestRevision({ commit, dispatch }, { reviewId, comment }) {
    const result = await assetReviewsApi.requestRevision(reviewId, comment)
    commit('UPDATE_REVIEW_IN_QUEUE', {
      reviewId,
      status: 'revision_requested'
    })
    dispatch('loadReviewStats')
    return result
  },

  async loadReview({ commit }, reviewId) {
    commit('SET_REVIEW_LOADING', true)
    try {
      const review = await assetReviewsApi.getReview(reviewId)
      commit('SET_CURRENT_REVIEW', review)
      return review
    } catch (err) {
      console.error('Failed to load review:', err)
    } finally {
      commit('SET_REVIEW_LOADING', false)
    }
  },

  async loadAssetReviews({ commit }, assetId) {
    try {
      const reviews = await assetReviewsApi.getAssetReviews(assetId)
      commit('SET_ASSET_REVIEW_HISTORY', reviews)
      return reviews
    } catch (err) {
      console.error('Failed to load asset reviews:', err)
    }
  },

  async loadMySubmissions({ commit, state }, status) {
    commit('SET_REVIEW_LOADING', true)
    try {
      const data = await assetReviewsApi.getMySubmissions(
        status,
        state.submissionsPagination.page,
        state.submissionsPagination.perPage
      )
      commit('SET_MY_SUBMISSIONS', data.data || data)
      commit('SET_SUBMISSIONS_TOTAL', data.total || 0)
    } catch (err) {
      console.error('Failed to load my submissions:', err)
    } finally {
      commit('SET_REVIEW_LOADING', false)
    }
  },

  async batchApproveReviews({ dispatch }, { reviewIds, comment }) {
    const result = await assetReviewsApi.batchApprove(reviewIds, comment)
    await dispatch('loadReviewQueue')
    dispatch('loadReviewStats')
    return result
  },

  async batchRejectReviews({ dispatch }, { reviewIds, comment }) {
    const result = await assetReviewsApi.batchReject(reviewIds, comment)
    await dispatch('loadReviewQueue')
    dispatch('loadReviewStats')
    return result
  },

  setReviewQueueFilter({ commit, dispatch }, status) {
    commit('SET_REVIEW_QUEUE_FILTER', status)
    commit('SET_REVIEW_QUEUE_PAGE', 1)
    dispatch('loadReviewQueue')
  },

  setReviewQueuePage({ commit, dispatch }, page) {
    commit('SET_REVIEW_QUEUE_PAGE', page)
    dispatch('loadReviewQueue')
  }
}

const mutations = {
  SET_REVIEW_QUEUE(state, reviews) {
    state.reviewQueue = reviews
  },

  SET_REVIEW_QUEUE_TOTAL(state, total) {
    state.queuePagination.total = total
  },

  SET_REVIEW_STATS(state, stats) {
    state.reviewStats = stats
  },

  SET_CURRENT_REVIEW(state, review) {
    state.currentReview = review
  },

  SET_ASSET_REVIEW_HISTORY(state, reviews) {
    state.assetReviewHistory = reviews
  },

  SET_MY_SUBMISSIONS(state, submissions) {
    state.mySubmissions = submissions
  },

  SET_SUBMISSIONS_TOTAL(state, total) {
    state.submissionsPagination.total = total
  },

  SET_REVIEW_LOADING(state, val) {
    state.isLoading = val
  },

  SET_REVIEW_QUEUE_FILTER(state, status) {
    state.queueFilter = status
  },

  SET_REVIEW_QUEUE_PAGE(state, page) {
    state.queuePagination.page = page
  },

  UPDATE_REVIEW_IN_QUEUE(state, { reviewId, status }) {
    const review = state.reviewQueue.find((r) => r.id === reviewId)
    if (review) review.status = status
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
