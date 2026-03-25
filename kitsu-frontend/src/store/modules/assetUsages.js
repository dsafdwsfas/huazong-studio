import assetUsagesApi from '@/store/api/asset_usages'

const state = {
  usages: [],
  usageStats: null,
  mostUsed: [],
  timeline: [],
  crossProject: [],
  pagination: {
    page: 1,
    perPage: 20,
    total: 0
  },
  isLoading: false
}

const getters = {
  assetUsages: (state) => state.usages,
  assetUsageStats: (state) => state.usageStats,
  assetMostUsed: (state) => state.mostUsed,
  assetUsageTimeline: (state) => state.timeline,
  assetCrossProjectUsage: (state) => state.crossProject,
  assetUsagesIsLoading: (state) => state.isLoading,
  assetUsagesPagination: (state) => state.pagination,

  usageCount: (state) => {
    if (state.usageStats) return state.usageStats.total_usages || 0
    return state.usages.length
  },

  projectCount: (state) => {
    if (state.usageStats) return state.usageStats.project_count || 0
    const projectIds = new Set(
      state.usages
        .map((u) => u.project_id)
        .filter(Boolean)
    )
    return projectIds.size
  }
}

const actions = {
  async loadAssetUsages({ commit }, { assetId, page = 1, perPage = 20 }) {
    commit('SET_ASSET_USAGES_LOADING', true)
    try {
      const data = await assetUsagesApi.getAssetUsages(assetId, page, perPage)
      commit('SET_ASSET_USAGES', data.data || data)
      commit('SET_ASSET_USAGES_TOTAL', data.total || 0)
      commit('SET_ASSET_USAGES_PAGE', page)
    } catch (err) {
      console.error('Failed to load asset usages:', err)
    } finally {
      commit('SET_ASSET_USAGES_LOADING', false)
    }
  },

  async recordAssetUsage({ commit, dispatch }, { assetId, data }) {
    commit('SET_ASSET_USAGES_LOADING', true)
    try {
      const usage = await assetUsagesApi.recordUsage(assetId, data)
      commit('ADD_ASSET_USAGE', usage)
      return usage
    } catch (err) {
      console.error('Failed to record asset usage:', err)
      throw err
    } finally {
      commit('SET_ASSET_USAGES_LOADING', false)
    }
  },

  async deleteAssetUsage({ commit }, usageId) {
    try {
      await assetUsagesApi.deleteUsage(usageId)
      commit('REMOVE_ASSET_USAGE', usageId)
    } catch (err) {
      console.error('Failed to delete asset usage:', err)
      throw err
    }
  },

  async loadProjectUsages({ commit }, { projectId, page = 1, perPage = 20 }) {
    commit('SET_ASSET_USAGES_LOADING', true)
    try {
      const data = await assetUsagesApi.getProjectUsages(
        projectId,
        page,
        perPage
      )
      commit('SET_ASSET_USAGES', data.data || data)
      commit('SET_ASSET_USAGES_TOTAL', data.total || 0)
    } catch (err) {
      console.error('Failed to load project usages:', err)
    } finally {
      commit('SET_ASSET_USAGES_LOADING', false)
    }
  },

  async loadAssetUsageStats({ commit }, assetId) {
    try {
      const stats = await assetUsagesApi.getAssetUsageStats(assetId)
      commit('SET_ASSET_USAGE_STATS', stats)
      return stats
    } catch (err) {
      console.error('Failed to load asset usage stats:', err)
    }
  },

  async loadMostUsedAssets({ commit }, limit = 20) {
    commit('SET_ASSET_USAGES_LOADING', true)
    try {
      const data = await assetUsagesApi.getMostUsedAssets(limit)
      commit('SET_MOST_USED_ASSETS', data.data || data)
      return data
    } catch (err) {
      console.error('Failed to load most used assets:', err)
    } finally {
      commit('SET_ASSET_USAGES_LOADING', false)
    }
  },

  async loadUsageTimeline({ commit }, assetId) {
    try {
      const data = await assetUsagesApi.getUsageTimeline(assetId)
      commit('SET_USAGE_TIMELINE', data.data || data)
      return data
    } catch (err) {
      console.error('Failed to load usage timeline:', err)
    }
  },

  async loadCrossProjectUsage({ commit }, assetId) {
    try {
      const data = await assetUsagesApi.getCrossProjectUsage(assetId)
      commit('SET_CROSS_PROJECT_USAGE', data.data || data)
      return data
    } catch (err) {
      console.error('Failed to load cross-project usage:', err)
    }
  }
}

const mutations = {
  SET_ASSET_USAGES(state, usages) {
    state.usages = usages
  },

  SET_ASSET_USAGES_TOTAL(state, total) {
    state.pagination.total = total
  },

  SET_ASSET_USAGES_PAGE(state, page) {
    state.pagination.page = page
  },

  SET_ASSET_USAGES_LOADING(state, val) {
    state.isLoading = val
  },

  SET_ASSET_USAGE_STATS(state, stats) {
    state.usageStats = stats
  },

  SET_MOST_USED_ASSETS(state, assets) {
    state.mostUsed = assets
  },

  SET_USAGE_TIMELINE(state, timeline) {
    state.timeline = timeline
  },

  SET_CROSS_PROJECT_USAGE(state, data) {
    state.crossProject = data
  },

  ADD_ASSET_USAGE(state, usage) {
    state.usages.unshift(usage)
    state.pagination.total += 1
  },

  REMOVE_ASSET_USAGE(state, usageId) {
    const idx = state.usages.findIndex((u) => u.id === usageId)
    if (idx !== -1) {
      state.usages.splice(idx, 1)
      state.pagination.total -= 1
    }
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
