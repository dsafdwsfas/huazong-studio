import assetStatsApi from '@/store/api/asset_stats'

const state = {
  dashboard: null,
  categoryDistribution: [],
  usageFrequency: [],
  storageStats: null,
  hotnessRanking: [],
  growthTrend: [],
  creatorStats: [],
  isLoading: false
}

const getters = {
  assetStatsDashboard: (state) => state.dashboard,
  assetStatsCategoryDistribution: (state) => state.categoryDistribution,
  assetStatsUsageFrequency: (state) => state.usageFrequency,
  assetStatsStorage: (state) => state.storageStats,
  assetStatsHotnessRanking: (state) => state.hotnessRanking,
  assetStatsGrowthTrend: (state) => state.growthTrend,
  assetStatsCreatorStats: (state) => state.creatorStats,
  assetStatsIsLoading: (state) => state.isLoading
}

const actions = {
  async loadAssetStatsDashboard({ commit }) {
    commit('SET_ASSET_STATS_LOADING', true)
    try {
      const data = await assetStatsApi.getDashboard()
      commit('SET_ASSET_STATS_DASHBOARD', data)
    } catch (err) {
      console.error('Failed to load asset stats dashboard:', err)
    } finally {
      commit('SET_ASSET_STATS_LOADING', false)
    }
  },

  async loadAssetStatsCategoryDistribution({ commit }) {
    try {
      const data = await assetStatsApi.getCategoryDistribution()
      commit('SET_ASSET_STATS_CATEGORY_DISTRIBUTION', data)
    } catch (err) {
      console.error('Failed to load category distribution:', err)
    }
  },

  async loadAssetStatsUsageFrequency({ commit }, { period, months } = {}) {
    try {
      const data = await assetStatsApi.getUsageFrequency(period, months)
      commit('SET_ASSET_STATS_USAGE_FREQUENCY', data)
    } catch (err) {
      console.error('Failed to load usage frequency:', err)
    }
  },

  async loadAssetStatsStorage({ commit }) {
    try {
      const data = await assetStatsApi.getStorageStats()
      commit('SET_ASSET_STATS_STORAGE', data)
    } catch (err) {
      console.error('Failed to load storage stats:', err)
    }
  },

  async loadAssetStatsHotnessRanking({ commit }, limit) {
    try {
      const data = await assetStatsApi.getHotnessRanking(limit)
      commit('SET_ASSET_STATS_HOTNESS_RANKING', data)
    } catch (err) {
      console.error('Failed to load hotness ranking:', err)
    }
  },

  async loadAssetStatsGrowthTrend({ commit }, months) {
    try {
      const data = await assetStatsApi.getGrowthTrend(months)
      commit('SET_ASSET_STATS_GROWTH_TREND', data)
    } catch (err) {
      console.error('Failed to load growth trend:', err)
    }
  },

  async loadAssetStatsCreatorStats({ commit }, limit) {
    try {
      const data = await assetStatsApi.getCreatorStats(limit)
      commit('SET_ASSET_STATS_CREATOR_STATS', data)
    } catch (err) {
      console.error('Failed to load creator stats:', err)
    }
  },

  async loadAllAssetStats({ dispatch }) {
    await Promise.all([
      dispatch('loadAssetStatsDashboard'),
      dispatch('loadAssetStatsCategoryDistribution'),
      dispatch('loadAssetStatsUsageFrequency'),
      dispatch('loadAssetStatsStorage'),
      dispatch('loadAssetStatsHotnessRanking'),
      dispatch('loadAssetStatsGrowthTrend'),
      dispatch('loadAssetStatsCreatorStats')
    ])
  }
}

const mutations = {
  SET_ASSET_STATS_LOADING(state, val) {
    state.isLoading = val
  },

  SET_ASSET_STATS_DASHBOARD(state, data) {
    state.dashboard = data
  },

  SET_ASSET_STATS_CATEGORY_DISTRIBUTION(state, data) {
    state.categoryDistribution = data
  },

  SET_ASSET_STATS_USAGE_FREQUENCY(state, data) {
    state.usageFrequency = data
  },

  SET_ASSET_STATS_STORAGE(state, data) {
    state.storageStats = data
  },

  SET_ASSET_STATS_HOTNESS_RANKING(state, data) {
    state.hotnessRanking = data
  },

  SET_ASSET_STATS_GROWTH_TREND(state, data) {
    state.growthTrend = data
  },

  SET_ASSET_STATS_CREATOR_STATS(state, data) {
    state.creatorStats = data
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
