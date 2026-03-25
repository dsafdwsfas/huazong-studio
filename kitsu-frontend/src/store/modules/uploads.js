/**
 * Vuex store module — 上传队列状态管理
 *
 * 将 UploadQueueManager 包装为响应式 Vuex 模块，
 * 供组件层绑定 UI。
 */

import { UploadQueueManager } from '@/lib/upload-queue'

let _manager = null

function getManager(commit) {
  if (_manager) return _manager

  _manager = new UploadQueueManager({
    maxConcurrent: 3,
    onFileProgress(item) {
      commit('SYNC_ITEMS')
    },
    onFileComplete(item) {
      commit('SYNC_ITEMS')
    },
    onFileError(item, err) {
      commit('SYNC_ITEMS')
    },
    onQueueProgress(stats) {
      commit('SET_STATS', stats)
    },
    onQueueEmpty() {
      commit('SET_ACTIVE', false)
    }
  })

  return _manager
}

const initialState = {
  items: [],
  stats: {
    total: 0,
    completed: 0,
    failed: 0,
    active: 0,
    pending: 0,
    percent: 0,
    speed: 0
  },
  isActive: false
}

const state = { ...initialState }

const getters = {
  uploadItems: (state) => state.items,
  uploadStats: (state) => state.stats,
  isUploading: (state) => state.isActive,
  hasUploads: (state) => state.items.length > 0
}

const actions = {
  addFilesToQueue({ commit }, { files, meta }) {
    const manager = getManager(commit)
    manager.addFiles(files, meta)
    commit('SET_ACTIVE', true)
    commit('SYNC_ITEMS')
  },

  pauseUpload({ commit }, itemId) {
    getManager(commit).pause(itemId)
    commit('SYNC_ITEMS')
  },

  resumeUpload({ commit }, itemId) {
    getManager(commit).resume(itemId)
    commit('SYNC_ITEMS')
  },

  cancelUpload({ commit }, itemId) {
    getManager(commit).cancel(itemId)
    commit('SYNC_ITEMS')
  },

  retryUpload({ commit }, itemId) {
    getManager(commit).retry(itemId)
    commit('SYNC_ITEMS')
  },

  pauseAllUploads({ commit }) {
    getManager(commit).pauseAll()
    commit('SYNC_ITEMS')
  },

  resumeAllUploads({ commit }) {
    getManager(commit).resumeAll()
    commit('SYNC_ITEMS')
  },

  cancelAllUploads({ commit }) {
    getManager(commit).cancelAll()
    commit('SYNC_ITEMS')
  },

  clearCompletedUploads({ commit }) {
    getManager(commit).clearCompleted()
    commit('SYNC_ITEMS')
  }
}

const mutations = {
  SYNC_ITEMS(state) {
    if (_manager) {
      state.items = _manager.getItems()
      state.stats = _manager.getStats()
      state.isActive = _manager.isActive
    }
  },

  SET_STATS(state, stats) {
    state.stats = stats
  },

  SET_ACTIVE(state, isActive) {
    state.isActive = isActive
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
