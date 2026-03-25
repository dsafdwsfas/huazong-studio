/**
 * 画宗认证 API 客户端 — 企业微信/钉钉/手机验证码
 */

const oauth = {
  // 获取企业微信登录 URL（后端重定向）
  wecomLogin() {
    window.location.href = '/api/auth/oauth/wecom/login'
  },

  // 获取钉钉登录 URL（后端重定向）
  dingtalkLogin() {
    window.location.href = '/api/auth/oauth/dingtalk/login'
  },

  // 发送手机验证码
  async sendSmsCode(phone) {
    const response = await fetch('/api/auth/sms/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone })
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.message || '发送失败')
    }
    return response.json()
  },

  // 手机验证码登录
  async smsLogin(phone, code) {
    const response = await fetch('/api/auth/sms/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, code })
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.message || '登录失败')
    }
    return response.json()
  },

  // 处理 OAuth 回调（从 URL 参数获取 token）
  async handleCallback(token) {
    const response = await fetch('/api/auth/oauth/callback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.message || '登录失败')
    }
    return response.json()
  },

  // 获取可用的 OAuth 提供商（从后端配置获取）
  async getAvailableProviders() {
    const response = await fetch('/api/auth/oauth/providers')
    if (!response.ok) {
      return { wecom: false, dingtalk: false, sms: false }
    }
    return response.json()
  }
}

export default oauth
