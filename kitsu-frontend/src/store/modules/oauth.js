/**
 * OAuth 和 SMS 登录状态管理
 * 遵循 Kitsu 现有的 Vuex store 模式（mutations 用大写常量命名）
 */

import store from '@/store'
import oauth from '@/lib/oauth'
import {
  DATA_LOADING_START,
  USER_LOGIN,
  USER_LOGIN_FAIL
} from '@/store/mutation-types'

// Mutation types（本模块私有）
const SMS_SET_PHONE = 'SMS_SET_PHONE'
const SMS_SET_CODE = 'SMS_SET_CODE'
const SMS_SEND_CODE_START = 'SMS_SEND_CODE_START'
const SMS_SEND_CODE_END = 'SMS_SEND_CODE_END'
const SMS_SEND_CODE_ERROR = 'SMS_SEND_CODE_ERROR'
const SMS_LOGIN_START = 'SMS_LOGIN_START'
const SMS_LOGIN_END = 'SMS_LOGIN_END'
const SMS_LOGIN_ERROR = 'SMS_LOGIN_ERROR'
const SMS_SET_COOLDOWN = 'SMS_SET_COOLDOWN'
const SMS_CLEAR_ERROR = 'SMS_CLEAR_ERROR'
const OAUTH_SET_PROVIDERS = 'OAUTH_SET_PROVIDERS'
const OAUTH_RESET = 'OAUTH_RESET'

const initialState = {
  phone: '',
  smsCode: '',
  isSendingCode: false,
  isSmsLoginLoading: false,
  smsError: '',
  smsCooldown: 0,
  availableProviders: { wecom: false, dingtalk: false, sms: false }
}

let cooldownTimer = null

const state = {
  ...initialState
}

const getters = {
  smsPhone: state => state.phone,
  smsCode: state => state.smsCode,
  isSendingCode: state => state.isSendingCode,
  isSmsLoginLoading: state => state.isSmsLoginLoading,
  smsError: state => state.smsError,
  smsCooldown: state => state.smsCooldown,
  availableProviders: state => state.availableProviders,
  canSendCode: state => {
    return (
      state.phone.length === 11 &&
      !state.isSendingCode &&
      state.smsCooldown === 0
    )
  }
}

const actions = {
  setSmsPhone({ commit }, phone) {
    commit(SMS_SET_PHONE, phone)
  },

  setSmsCode({ commit }, code) {
    commit(SMS_SET_CODE, code)
  },

  clearSmsError({ commit }) {
    commit(SMS_CLEAR_ERROR)
  },

  async sendSmsCode({ commit, state }) {
    if (state.smsCooldown > 0 || state.isSendingCode) return

    commit(SMS_SEND_CODE_START)
    try {
      await oauth.sendSmsCode(state.phone)
      commit(SMS_SEND_CODE_END)
      // 启动 60s 倒计时
      commit(SMS_SET_COOLDOWN, 60)
      cooldownTimer = setInterval(() => {
        if (state.smsCooldown <= 1) {
          clearInterval(cooldownTimer)
          cooldownTimer = null
          commit(SMS_SET_COOLDOWN, 0)
        } else {
          commit(SMS_SET_COOLDOWN, state.smsCooldown - 1)
        }
      }, 1000)
    } catch (err) {
      commit(SMS_SEND_CODE_ERROR, err.message || '发送验证码失败')
    }
  },

  async smsLogin({ commit, state }, callback) {
    commit(SMS_LOGIN_START)
    try {
      const result = await oauth.smsLogin(state.phone, state.smsCode)
      if (result.login && result.user) {
        store.commit(DATA_LOADING_START)
        store.commit(USER_LOGIN, result.user)
        commit(SMS_LOGIN_END)
        callback(null, true)
      } else {
        store.commit(USER_LOGIN_FAIL)
        commit(SMS_LOGIN_ERROR, '登录失败')
        callback(new Error('登录失败'), false)
      }
    } catch (err) {
      commit(SMS_LOGIN_ERROR, err.message || '登录失败')
      callback(err, false)
    }
  },

  async loadProviders({ commit }) {
    try {
      const providers = await oauth.getAvailableProviders()
      commit(OAUTH_SET_PROVIDERS, providers)
    } catch {
      // 加载失败时默认全部启用，让用户尝试
      commit(OAUTH_SET_PROVIDERS, { wecom: true, dingtalk: true, sms: true })
    }
  },

  wecomLogin() {
    oauth.wecomLogin()
  },

  dingtalkLogin() {
    oauth.dingtalkLogin()
  },

  resetOauth({ commit }) {
    if (cooldownTimer) {
      clearInterval(cooldownTimer)
      cooldownTimer = null
    }
    commit(OAUTH_RESET)
  }
}

const mutations = {
  [SMS_SET_PHONE](state, phone) {
    state.phone = phone
  },

  [SMS_SET_CODE](state, code) {
    state.smsCode = code
  },

  [SMS_SEND_CODE_START](state) {
    state.isSendingCode = true
    state.smsError = ''
  },

  [SMS_SEND_CODE_END](state) {
    state.isSendingCode = false
  },

  [SMS_SEND_CODE_ERROR](state, error) {
    state.isSendingCode = false
    state.smsError = error
  },

  [SMS_LOGIN_START](state) {
    state.isSmsLoginLoading = true
    state.smsError = ''
  },

  [SMS_LOGIN_END](state) {
    state.isSmsLoginLoading = false
    state.smsError = ''
  },

  [SMS_LOGIN_ERROR](state, error) {
    state.isSmsLoginLoading = false
    state.smsError = error
  },

  [SMS_SET_COOLDOWN](state, seconds) {
    state.smsCooldown = seconds
  },

  [SMS_CLEAR_ERROR](state) {
    state.smsError = ''
  },

  [OAUTH_SET_PROVIDERS](state, providers) {
    state.availableProviders = providers
  },

  [OAUTH_RESET](state) {
    Object.assign(state, { ...initialState })
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
