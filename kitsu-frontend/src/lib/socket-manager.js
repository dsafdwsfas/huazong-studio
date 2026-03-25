/**
 * Socket 连接管理器
 *
 * 增强 Socket.IO 连接：
 * 1. 自动重连（指数退避）
 * 2. 心跳保持在线状态
 * 3. 实时事件路由到 Vuex store
 * 4. 用户房间自动加入（接收个人通知）
 */

import store from '@/store'

const HEARTBEAT_INTERVAL = 40000 // 40秒，服务端 TTL 120秒

let _heartbeatTimer = null
let _socket = null

/**
 * 初始化 Socket 管理器
 * @param {SocketIOClient.Socket} socket
 */
export function initSocketManager(socket) {
  _socket = socket

  // 连接事件
  socket.on('connect', onConnect)
  socket.on('disconnect', onDisconnect)
  socket.on('reconnect', onReconnect)

  // 实时通知事件
  socket.on('notification:new', onNotification)

  // 在线状态广播
  socket.on('presence:update', onPresenceUpdate)

  // 实体变更通知（任务状态、评论等）
  socket.on('task:update', onTaskUpdate)
  socket.on('comment:new', onCommentNew)
  socket.on('preview-file:update', onPreviewUpdate)
}

/**
 * 启动心跳
 */
function startHeartbeat() {
  stopHeartbeat()
  _heartbeatTimer = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL)
  // 立即发送一次
  sendHeartbeat()
}

function stopHeartbeat() {
  if (_heartbeatTimer) {
    clearInterval(_heartbeatTimer)
    _heartbeatTimer = null
  }
}

function sendHeartbeat() {
  const currentRoute = store.state.route
  const page = currentRoute?.name || ''
  const projectId = currentRoute?.params?.production_id || ''

  // 通过 REST API 发送心跳（比 SocketIO 更可靠）
  fetch('/api/data/heartbeat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getAccessToken()}`
    },
    body: JSON.stringify({ page, project_id: projectId })
  }).catch(() => {
    // 静默失败
  })
}

function getAccessToken() {
  try {
    return store.state.login?.accessToken ||
      localStorage.getItem('access_token') || ''
  } catch {
    return ''
  }
}

// ---- 事件处理器 ----

function onConnect() {
  console.log('[Socket] 已连接')
  startHeartbeat()

  // 加入个人通知房间
  const userId = store.state.user?.user?.id
  if (userId && _socket) {
    _socket.emit('join', { room: `user:${userId}` })
  }
}

function onDisconnect(reason) {
  console.log('[Socket] 已断开:', reason)
  stopHeartbeat()
}

function onReconnect(attempt) {
  console.log('[Socket] 重连成功，尝试次数:', attempt)
  startHeartbeat()
}

function onNotification(data) {
  store.commit('ADD_REALTIME_NOTIFICATION', data)
}

function onPresenceUpdate(data) {
  store.commit('SET_ONLINE_USERS', data.users || [])
}

function onTaskUpdate(data) {
  // 触发任务列表刷新
  store.commit('REALTIME_TASK_UPDATE', data)
}

function onCommentNew(data) {
  store.commit('REALTIME_COMMENT_NEW', data)
}

function onPreviewUpdate(data) {
  store.commit('REALTIME_PREVIEW_UPDATE', data)
}

/**
 * 断开 Socket 并清理
 */
export function destroySocketManager() {
  stopHeartbeat()
  if (_socket) {
    _socket.off('connect', onConnect)
    _socket.off('disconnect', onDisconnect)
    _socket.off('reconnect', onReconnect)
    _socket.off('notification:new', onNotification)
    _socket.off('presence:update', onPresenceUpdate)
    _socket.off('task:update', onTaskUpdate)
    _socket.off('comment:new', onCommentNew)
    _socket.off('preview-file:update', onPreviewUpdate)
  }
  _socket = null
}

export default {
  initSocketManager,
  destroySocketManager
}
