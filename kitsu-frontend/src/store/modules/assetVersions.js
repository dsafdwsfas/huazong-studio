import assetVersionsApi from '@/store/api/asset_versions'

const state = {
  versions: [],
  currentVersion: null,
  versionDiff: null,
  compareResult: null,
  pagination: {
    page: 1,
    perPage: 20,
    total: 0
  },
  isLoading: false
}

const getters = {
  assetVersions: (state) => state.versions,
  assetCurrentVersion: (state) => state.currentVersion,
  assetVersionDiff: (state) => state.versionDiff,
  assetVersionCompareResult: (state) => state.compareResult,
  assetVersionsIsLoading: (state) => state.isLoading,
  assetVersionsPagination: (state) => state.pagination,

  getVersionByNumber: (state) => (number) => {
    return state.versions.find((v) => v.version_number === number)
  },

  versionCount: (state) => state.pagination.total
}

const actions = {
  async loadAssetVersions({ commit, state }, assetId) {
    commit('SET_ASSET_VERSIONS_LOADING', true)
    try {
      const data = await assetVersionsApi.getVersions(
        assetId,
        state.pagination.page,
        state.pagination.perPage
      )
      commit('SET_ASSET_VERSIONS', data.data || data)
      commit('SET_ASSET_VERSIONS_TOTAL', data.total || 0)
    } catch (err) {
      console.error('Failed to load asset versions:', err)
    } finally {
      commit('SET_ASSET_VERSIONS_LOADING', false)
    }
  },

  async loadAssetVersion({ commit }, versionId) {
    commit('SET_ASSET_VERSIONS_LOADING', true)
    try {
      const version = await assetVersionsApi.getVersion(versionId)
      commit('SET_CURRENT_ASSET_VERSION', version)
      return version
    } catch (err) {
      console.error('Failed to load asset version:', err)
    } finally {
      commit('SET_ASSET_VERSIONS_LOADING', false)
    }
  },

  async loadAssetVersionDiff({ commit }, versionId) {
    commit('SET_ASSET_VERSIONS_LOADING', true)
    try {
      const diff = await assetVersionsApi.getVersionDiff(versionId)
      commit('SET_ASSET_VERSION_DIFF', diff)
      return diff
    } catch (err) {
      console.error('Failed to load version diff:', err)
    } finally {
      commit('SET_ASSET_VERSIONS_LOADING', false)
    }
  },

  async compareAssetVersions({ commit }, { versionA, versionB }) {
    commit('SET_ASSET_VERSIONS_LOADING', true)
    try {
      const result = await assetVersionsApi.compareVersions(versionA, versionB)
      commit('SET_ASSET_VERSION_COMPARE', result)
      return result
    } catch (err) {
      console.error('Failed to compare versions:', err)
    } finally {
      commit('SET_ASSET_VERSIONS_LOADING', false)
    }
  },

  async restoreAssetVersion({ dispatch }, { assetId, versionId }) {
    const result = await assetVersionsApi.restoreVersion(assetId, versionId)
    await dispatch('loadAssetVersions', assetId)
    return result
  },

  async loadLatestAssetVersion({ commit }, assetId) {
    try {
      const version = await assetVersionsApi.getLatestVersion(assetId)
      commit('SET_CURRENT_ASSET_VERSION', version)
      return version
    } catch (err) {
      console.error('Failed to load latest version:', err)
    }
  },

  setAssetVersionsPage({ commit, dispatch }, { assetId, page }) {
    commit('SET_ASSET_VERSIONS_PAGE', page)
    dispatch('loadAssetVersions', assetId)
  },

  clearAssetVersions({ commit }) {
    commit('SET_ASSET_VERSIONS', [])
    commit('SET_ASSET_VERSIONS_TOTAL', 0)
    commit('SET_CURRENT_ASSET_VERSION', null)
    commit('SET_ASSET_VERSION_DIFF', null)
    commit('SET_ASSET_VERSION_COMPARE', null)
    commit('SET_ASSET_VERSIONS_PAGE', 1)
  }
}

const mutations = {
  SET_ASSET_VERSIONS(state, versions) {
    state.versions = versions
  },

  SET_ASSET_VERSIONS_TOTAL(state, total) {
    state.pagination.total = total
  },

  SET_CURRENT_ASSET_VERSION(state, version) {
    state.currentVersion = version
  },

  SET_ASSET_VERSION_DIFF(state, diff) {
    state.versionDiff = diff
  },

  SET_ASSET_VERSION_COMPARE(state, result) {
    state.compareResult = result
  },

  SET_ASSET_VERSIONS_LOADING(state, val) {
    state.isLoading = val
  },

  SET_ASSET_VERSIONS_PAGE(state, page) {
    state.pagination.page = page
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
