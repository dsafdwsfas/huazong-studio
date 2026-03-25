import globalAssetsApi from '@/store/api/global_assets'

const state = {
  assets: [],
  currentAsset: null,
  assetCategories: [
    { value: 'character', label: '人物', icon: 'user' },
    { value: 'scene', label: '场景', icon: 'image' },
    { value: 'prop', label: '道具', icon: 'box' },
    { value: 'effect', label: '特效', icon: 'zap' },
    { value: 'music', label: '音乐', icon: 'music' },
    { value: 'prompt', label: '提示词', icon: 'message-square' },
    { value: 'style', label: '风格', icon: 'palette' },
    { value: 'camera_language', label: '镜头语言', icon: 'camera' }
  ],
  filters: {
    category: null,
    status: null,
    search: ''
  },
  pagination: {
    page: 1,
    perPage: 20,
    total: 0
  },
  isLoading: false
}

const getters = {
  globalAssets: (state) => state.assets,
  globalCurrentAsset: (state) => state.currentAsset,
  globalAssetCategories: (state) => state.assetCategories,
  globalAssetsIsLoading: (state) => state.isLoading,
  globalAssetsPagination: (state) => state.pagination,
  globalAssetsFilters: (state) => state.filters,

  filteredAssets: (state) => {
    let result = state.assets
    if (state.filters.category) {
      result = result.filter((a) => a.category === state.filters.category)
    }
    if (state.filters.status) {
      result = result.filter((a) => a.status === state.filters.status)
    }
    if (state.filters.search) {
      const term = state.filters.search.toLowerCase()
      result = result.filter(
        (a) =>
          (a.name && a.name.toLowerCase().includes(term)) ||
          (a.description && a.description.toLowerCase().includes(term))
      )
    }
    return result
  },

  assetsByCategory: (state) => {
    const grouped = {}
    for (const cat of state.assetCategories) {
      grouped[cat.value] = state.assets.filter(
        (a) => a.category === cat.value
      )
    }
    return grouped
  },

  currentAssetFiles: (state) => {
    if (!state.currentAsset) return []
    return state.currentAsset.files || []
  }
}

const actions = {
  async loadGlobalAssets({ commit, state }) {
    commit('SET_GLOBAL_ASSETS_LOADING', true)
    try {
      const params = {
        page: state.pagination.page,
        per_page: state.pagination.perPage
      }
      if (state.filters.category) params.category = state.filters.category
      if (state.filters.status) params.status = state.filters.status
      if (state.filters.search) params.search = state.filters.search

      const data = await globalAssetsApi.getAssets(params)
      commit('SET_GLOBAL_ASSETS', data.data || data)
      commit('SET_GLOBAL_ASSETS_TOTAL', data.total || 0)
    } catch (err) {
      console.error('Failed to load global assets:', err)
    } finally {
      commit('SET_GLOBAL_ASSETS_LOADING', false)
    }
  },

  async loadGlobalAsset({ commit }, assetId) {
    commit('SET_GLOBAL_ASSETS_LOADING', true)
    try {
      const asset = await globalAssetsApi.getAsset(assetId)
      commit('SET_CURRENT_GLOBAL_ASSET', asset)
      return asset
    } catch (err) {
      console.error('Failed to load global asset:', err)
    } finally {
      commit('SET_GLOBAL_ASSETS_LOADING', false)
    }
  },

  async createGlobalAsset({ dispatch }, data) {
    const asset = await globalAssetsApi.createAsset(data)
    await dispatch('loadGlobalAssets')
    return asset
  },

  async updateGlobalAsset({ commit }, { assetId, data }) {
    const updated = await globalAssetsApi.updateAsset(assetId, data)
    commit('UPDATE_GLOBAL_ASSET', updated)
    return updated
  },

  async deleteGlobalAsset({ dispatch }, assetId) {
    await globalAssetsApi.deleteAsset(assetId)
    await dispatch('loadGlobalAssets')
  },

  async linkAssetToProject(_context, { assetId, projectId }) {
    return await globalAssetsApi.linkToProject(assetId, projectId)
  },

  async unlinkAssetFromProject(_context, { assetId, projectId }) {
    return await globalAssetsApi.unlinkFromProject(assetId, projectId)
  },

  async loadProjectGlobalAssets(_context, { projectId, params }) {
    return await globalAssetsApi.getProjectAssets(projectId, params)
  },

  async incrementAssetUsage({ commit }, assetId) {
    const result = await globalAssetsApi.incrementUsage(assetId)
    commit('INCREMENT_GLOBAL_ASSET_USAGE', assetId)
    return result
  },

  async updateAssetStatus({ commit }, { assetId, status }) {
    const result = await globalAssetsApi.updateStatus(assetId, status)
    commit('UPDATE_GLOBAL_ASSET_STATUS', { assetId, status })
    return result
  },

  async importAssetsFromProject({ dispatch }, { projectId, assetType }) {
    const result = await globalAssetsApi.importFromProject(
      projectId,
      assetType
    )
    await dispatch('loadGlobalAssets')
    return result
  },

  setGlobalAssetsFilter({ commit, dispatch }, { key, value }) {
    commit('SET_GLOBAL_ASSETS_FILTER', { key, value })
    commit('SET_GLOBAL_ASSETS_PAGE', 1)
    dispatch('loadGlobalAssets')
  },

  setGlobalAssetsPage({ commit, dispatch }, page) {
    commit('SET_GLOBAL_ASSETS_PAGE', page)
    dispatch('loadGlobalAssets')
  }
}

const mutations = {
  SET_GLOBAL_ASSETS(state, assets) {
    state.assets = assets
  },

  SET_GLOBAL_ASSETS_TOTAL(state, total) {
    state.pagination.total = total
  },

  SET_CURRENT_GLOBAL_ASSET(state, asset) {
    state.currentAsset = asset
  },

  SET_GLOBAL_ASSETS_LOADING(state, val) {
    state.isLoading = val
  },

  SET_GLOBAL_ASSETS_FILTER(state, { key, value }) {
    state.filters[key] = value
  },

  SET_GLOBAL_ASSETS_PAGE(state, page) {
    state.pagination.page = page
  },

  UPDATE_GLOBAL_ASSET(state, updated) {
    const idx = state.assets.findIndex((a) => a.id === updated.id)
    if (idx !== -1) {
      state.assets.splice(idx, 1, updated)
    }
    if (state.currentAsset && state.currentAsset.id === updated.id) {
      state.currentAsset = updated
    }
  },

  UPDATE_GLOBAL_ASSET_STATUS(state, { assetId, status }) {
    const asset = state.assets.find((a) => a.id === assetId)
    if (asset) asset.status = status
    if (state.currentAsset && state.currentAsset.id === assetId) {
      state.currentAsset.status = status
    }
  },

  INCREMENT_GLOBAL_ASSET_USAGE(state, assetId) {
    const asset = state.assets.find((a) => a.id === assetId)
    if (asset && asset.usage_count !== undefined) {
      asset.usage_count += 1
    }
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
