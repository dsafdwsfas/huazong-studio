/**
 * Vuex store module — 在线状态 + 实时通知
 */

import client from '@/store/api/client'

const initialState = {
  onlineUsers: [],
  projectOnlineUsers: [],
  realtimeNotifications: [],
  realtimeTaskUpdates: [],
  unreadNotificationCount: 0
}

const state = { ...initialState }

const getters = {
  onlineUsers: (state) => state.onlineUsers,
  onlineUserCount: (state) => state.onlineUsers.length,
  projectOnlineUsers: (state) => state.projectOnlineUsers,
  realtimeNotifications: (state) => state.realtimeNotifications,
  unreadNotificationCount: (state) => state.unreadNotificationCount
}

const actions = {
  async loadOnlineUsers({ commit }) {
    try {
      const users = await client.pget('/api/data/online-users')
      commit('SET_ONLINE_USERS', users)
    } catch (err) {
      console.warn('Failed to load online users:', err)
    }
  },

  async loadProjectOnlineUsers({ commit }, projectId) {
    try {
      const users = await client.pget(
        `/api/data/projects/${projectId}/online-users`
      )
      commit('SET_PROJECT_ONLINE_USERS', users)
    } catch (err) {
      console.warn('Failed to load project online users:', err)
    }
  },

  async checkEntityLock({ commit }, { entityId, updatedAt }) {
    return client.ppost(`/api/data/entities/${entityId}/check-lock`, {
      updated_at: updatedAt
    })
  },

  clearRealtimeNotifications({ commit }) {
    commit('CLEAR_REALTIME_NOTIFICATIONS')
  }
}

const mutations = {
  SET_ONLINE_USERS(state, users) {
    state.onlineUsers = users
  },

  SET_PROJECT_ONLINE_USERS(state, users) {
    state.projectOnlineUsers = users
  },

  ADD_REALTIME_NOTIFICATION(state, notification) {
    state.realtimeNotifications.unshift(notification)
    state.unreadNotificationCount++
    // 最多保留 50 条
    if (state.realtimeNotifications.length > 50) {
      state.realtimeNotifications.pop()
    }
  },

  CLEAR_REALTIME_NOTIFICATIONS(state) {
    state.realtimeNotifications = []
    state.unreadNotificationCount = 0
  },

  REALTIME_TASK_UPDATE(state, data) {
    state.realtimeTaskUpdates.unshift(data)
    if (state.realtimeTaskUpdates.length > 20) {
      state.realtimeTaskUpdates.pop()
    }
  },

  REALTIME_COMMENT_NEW() {
    // 占位：触发评论列表刷新由组件自行处理
  },

  REALTIME_PREVIEW_UPDATE() {
    // 占位：触发预览刷新由组件自行处理
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
