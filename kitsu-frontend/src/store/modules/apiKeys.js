import apiKeysApi from '@/store/api/api_keys'

const state = {
  keys: [],
  newKeySecret: null,
  isLoading: false
}

const getters = {
  apiKeys: (state) => state.keys,
  apiKeysIsLoading: (state) => state.isLoading,
  newKeySecret: (state) => state.newKeySecret
}

const actions = {
  async loadApiKeys({ commit }) {
    commit('SET_API_KEYS_LOADING', true)
    try {
      const data = await apiKeysApi.listKeys()
      commit('SET_API_KEYS', data.keys || data)
    } catch (err) {
      console.error('Failed to load API keys:', err)
    } finally {
      commit('SET_API_KEYS_LOADING', false)
    }
  },

  async createApiKey({ commit, dispatch }, data) {
    commit('SET_API_KEYS_LOADING', true)
    try {
      const result = await apiKeysApi.createKey(data)
      commit('SET_NEW_KEY_SECRET', result.secret || result.key)
      await dispatch('loadApiKeys')
      return result
    } catch (err) {
      console.error('Failed to create API key:', err)
      throw err
    } finally {
      commit('SET_API_KEYS_LOADING', false)
    }
  },

  async updateApiKey({ commit }, { keyId, data }) {
    commit('SET_API_KEYS_LOADING', true)
    try {
      const updated = await apiKeysApi.updateKey(keyId, data)
      commit('UPDATE_API_KEY', updated)
      return updated
    } catch (err) {
      console.error('Failed to update API key:', err)
      throw err
    } finally {
      commit('SET_API_KEYS_LOADING', false)
    }
  },

  async deleteApiKey({ dispatch }, keyId) {
    try {
      await apiKeysApi.deleteKey(keyId)
      await dispatch('loadApiKeys')
    } catch (err) {
      console.error('Failed to delete API key:', err)
      throw err
    }
  },

  clearNewKeySecret({ commit }) {
    commit('SET_NEW_KEY_SECRET', null)
  }
}

const mutations = {
  SET_API_KEYS(state, keys) {
    state.keys = keys
  },

  SET_API_KEYS_LOADING(state, val) {
    state.isLoading = val
  },

  SET_NEW_KEY_SECRET(state, secret) {
    state.newKeySecret = secret
  },

  UPDATE_API_KEY(state, updated) {
    const idx = state.keys.findIndex((k) => k.id === updated.id)
    if (idx !== -1) {
      state.keys.splice(idx, 1, updated)
    }
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
