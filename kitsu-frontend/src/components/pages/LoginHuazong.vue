<template>
  <div class="login-huazong hero is-fullheight">
    <div class="container has-text-centered">
      <div
        class="box has-text-left"
        :class="{
          'xyz-out': fadeAway
        }"
        xyz="fade"
      >
        <!-- 品牌 Header -->
        <div class="has-text-centered login-header">
          <img
            src="../../assets/kitsu-text-dark.svg"
            v-if="isDarkTheme"
            class="brand-logo"
          />
          <img
            src="../../assets/kitsu-text.svg"
            v-else
            class="brand-logo"
          />
          <h1 class="title brand-title">画宗制片中枢</h1>
        </div>

        <!-- 企业微信扫码登录 -->
        <div
          class="login-method-card"
          v-if="availableProviders.wecom"
          @click="onWecomLogin"
        >
          <div class="login-method-icon wecom-icon">
            <svg
              viewBox="0 0 24 24"
              width="28"
              height="28"
              fill="currentColor"
            >
              <path
                d="M17.07 13.58c.43 0 .85.04 1.26.12-.63-2.98-3.65-5.2-7.2-5.2-4.08
                0-7.38 2.83-7.38 6.32 0 2.04 1.1 3.89 2.83 5.12l-.71
                2.12 2.46-1.23c.87.24 1.82.37 2.8.37.4 0
                .79-.02 1.18-.07-.25-.72-.38-1.49-.38-2.28
                0-3.16 2.86-5.72 6.38-5.72h-.24zm-4.79-2.4c.53
                0 .96.43.96.96s-.43.96-.96.96-.96-.43-.96-.96.43-.96.96-.96zm-4.96
                0c.53 0 .96.43.96.96s-.43.96-.96.96-.96-.43-.96-.96.43-.96.96-.96z"
              />
              <path
                d="M23.25 18.87c0-2.78-2.86-5.03-6.38-5.03s-6.38
                2.25-6.38 5.03 2.86 5.03 6.38 5.03c.74 0
                1.46-.1 2.13-.28l1.93.97-.56-1.67c1.36-.97
                2.24-2.42 2.24-4.05h.64zm-8.47-.8c-.43
                0-.77-.34-.77-.77s.34-.77.77-.77.77.34.77.77-.34.77-.77.77zm4.18
                0c-.43
                0-.77-.34-.77-.77s.34-.77.77-.77.77.34.77.77-.34.77-.77.77z"
              />
            </svg>
          </div>
          <div class="login-method-info">
            <span class="login-method-name">企业微信扫码登录</span>
            <span class="login-method-desc">使用企业微信扫码快速登录</span>
          </div>
          <span class="login-method-arrow">&rsaquo;</span>
        </div>

        <!-- 钉钉扫码登录 -->
        <div
          class="login-method-card"
          v-if="availableProviders.dingtalk"
          @click="onDingtalkLogin"
        >
          <div class="login-method-icon dingtalk-icon">
            <svg
              viewBox="0 0 24 24"
              width="28"
              height="28"
              fill="currentColor"
            >
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48
                10-10S17.52 2 12 2zm4.64
                8.8c-.03.09-1.28 2.62-1.28
                2.62l1.59.75-3.57
                1.98.67-1.71-1.42-.59s1.86-2.58
                1.95-2.71c.1-.14.14-.37-.03-.47-.17-.1-1.63-.47-1.63-.47l3.74-2.09-.02
                2.69z"
              />
            </svg>
          </div>
          <div class="login-method-info">
            <span class="login-method-name">钉钉扫码登录</span>
            <span class="login-method-desc">使用钉钉扫码快速登录</span>
          </div>
          <span class="login-method-arrow">&rsaquo;</span>
        </div>

        <!-- 分隔线 -->
        <div
          class="login-divider"
          v-if="
            availableProviders.wecom ||
            availableProviders.dingtalk
          "
        >
          <span>其他登录方式</span>
        </div>

        <!-- 手机验证码登录 -->
        <div v-if="availableProviders.sms">
          <a
            class="login-method-toggle"
            :class="{ active: showSmsForm }"
            @click="toggleSmsForm"
          >
            <span class="login-method-toggle-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path
                  d="M17 1.01L7 1c-1.1 0-2 .9-2
                  2v18c0 1.1.9 2 2
                  2h10c1.1 0 2-.9
                  2-2V3c0-1.1-.9-1.99-2-1.99zM17
                  19H7V5h10v14z"
                />
              </svg>
            </span>
            手机验证码登录
            <span class="toggle-arrow" :class="{ expanded: showSmsForm }">
              &#x25BE;
            </span>
          </a>
          <div v-if="showSmsForm" class="sms-form-container">
            <sms-login-form @login="onSmsLogin" />
          </div>
        </div>

        <!-- 密码登录（折叠/次要入口） -->
        <div class="password-login-section">
          <a
            class="login-method-toggle secondary"
            :class="{ active: showPasswordForm }"
            @click="togglePasswordForm"
          >
            <span class="login-method-toggle-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path
                  d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7
                  6v2H6c-1.1 0-2 .9-2
                  2v10c0 1.1.9 2 2
                  2h12c1.1 0 2-.9
                  2-2V10c0-1.1-.9-2-2-2zm-6
                  9c-1.1
                  0-2-.9-2-2s.9-2 2-2
                  2 .9 2 2-.9 2-2
                  2zm3.1-9H8.9V6c0-1.71
                  1.39-3.1 3.1-3.1
                  1.71 0 3.1 1.39 3.1 3.1v2z"
                />
              </svg>
            </span>
            密码登录
            <span class="toggle-arrow" :class="{ expanded: showPasswordForm }">
              &#x25BE;
            </span>
          </a>
          <div v-if="showPasswordForm" class="password-form-container">
            <form @submit.prevent="confirmLogIn">
              <div class="field">
                <p class="control has-icon">
                  <input
                    class="input is-medium email"
                    type="email"
                    autocomplete="username"
                    placeholder="邮箱"
                    @input="updateEmail"
                    @keyup.enter="confirmLogIn"
                    v-model="email"
                  />
                </p>
              </div>
              <div class="field">
                <p class="control has-icon">
                  <input
                    class="input is-medium password"
                    type="password"
                    autocomplete="current-password"
                    placeholder="密码"
                    @input="updatePassword"
                    @keyup.enter="confirmLogIn"
                    v-model="password"
                  />
                </p>
              </div>
              <p class="control">
                <a
                  class="button is-medium is-fullwidth password-login-button"
                  :class="{
                    'is-loading': isLoginLoading
                  }"
                  @click="confirmLogIn"
                >
                  登录
                </a>
              </p>
            </form>
            <p
              class="control error has-text-centered"
              v-if="isLoginError"
            >
              邮箱或密码错误
            </p>
            <p
              class="control error has-text-centered"
              v-if="isServerError"
            >
              服务器错误，请稍后重试
            </p>
            <p class="has-text-centered forgot-password">
              <router-link :to="{ name: 'reset-password' }">
                忘记密码？
              </router-link>
            </p>
          </div>
        </div>

        <!-- 底部联系信息 -->
        <div class="login-footer">
          <p>遇到问题？联系管理员</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import SmsLoginForm from '@/components/widgets/SmsLoginForm.vue'

export default {
  name: 'login-huazong',

  components: {
    SmsLoginForm
  },

  data() {
    return {
      email: '',
      password: '',
      isServerError: false,
      showSmsForm: false,
      showPasswordForm: false,
      fadeAway: false
    }
  },

  mounted() {
    this.fadeAway = false
    this.email = this.$store.state.login.email
    this.password = this.$store.state.login.password
    this.loadProviders()
  },

  computed: {
    ...mapGetters([
      'isDarkTheme',
      'isLoginLoading',
      'isLoginError',
      'availableProviders'
    ])
  },

  methods: {
    ...mapActions([
      'logIn',
      'smsLogin',
      'wecomLogin',
      'dingtalkLogin',
      'loadProviders'
    ]),

    toggleSmsForm() {
      this.showSmsForm = !this.showSmsForm
      if (this.showSmsForm) {
        this.showPasswordForm = false
      }
    },

    togglePasswordForm() {
      this.showPasswordForm = !this.showPasswordForm
      if (this.showPasswordForm) {
        this.showSmsForm = false
      }
    },

    onWecomLogin() {
      this.wecomLogin()
    },

    onDingtalkLogin() {
      this.dingtalkLogin()
    },

    onSmsLogin() {
      this.smsLogin((_err, success) => {
        if (success) {
          this.navigateAfterLogin()
        }
      })
    },

    updateEmail(e) {
      this.$store.dispatch('changeEmail', e.target.value)
    },

    updatePassword(e) {
      this.$store.dispatch('changePassword', e.target.value)
    },

    confirmLogIn() {
      this.isServerError = false
      this.logIn({
        twoFactorPayload: undefined,
        callback: (err, success) => {
          if (err) {
            if (err.server_error) {
              this.isServerError = true
            }
          }
          if (success) {
            this.navigateAfterLogin()
          }
        }
      })
    },

    navigateAfterLogin() {
      this.fadeAway = true
      setTimeout(() => {
        if (this.$route.query.redirect) {
          this.$router.push(this.$route.query.redirect)
        } else {
          this.$router.push('/')
        }
      }, 500)
    }
  },

  head() {
    return {
      title: '登录 - 画宗制片中枢'
    }
  }
}
</script>

<style lang="scss" scoped>
.login-huazong {
  background: linear-gradient(
    135deg,
    $brand-primary 0%,
    $brand-secondary 50%,
    darken($brand-primary, 5%) 100%
  );
}

.box {
  border-radius: 1em;
  max-width: 420px;
  margin: 0 auto;
  padding: 2em;
}

.login-header {
  padding-bottom: 1.5em;

  .brand-logo {
    border-radius: 20%;
    padding: 0.5em;
    margin-top: 1em;
    margin-bottom: 0.5em;
    width: 140px;
  }

  .brand-title {
    color: var(--text);
    font-weight: 600;
    font-size: 1.4em;
    margin-bottom: 0;
    letter-spacing: 0.05em;
  }
}

// OAuth 登录方式卡片
.login-method-card {
  display: flex;
  align-items: center;
  padding: 0.9em 1em;
  margin-bottom: 0.75em;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition:
    border-color 0.2s,
    background-color 0.2s,
    box-shadow 0.2s;

  &:hover {
    border-color: var(--brand-accent);
    background-color: var(--background-hover);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }

  .login-method-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .wecom-icon {
    background-color: rgba(7, 193, 96, 0.1);
    color: #07c160;
  }

  .dingtalk-icon {
    background-color: rgba(0, 122, 255, 0.1);
    color: #007aff;
  }

  .login-method-info {
    flex: 1;
    margin-left: 0.8em;
    display: flex;
    flex-direction: column;
  }

  .login-method-name {
    font-weight: 500;
    font-size: 0.95em;
    color: var(--text-strong);
  }

  .login-method-desc {
    font-size: 0.78em;
    color: var(--text-alt);
    margin-top: 2px;
  }

  .login-method-arrow {
    font-size: 1.6em;
    color: var(--text-alt);
    margin-left: 0.5em;
  }
}

// 分隔线
.login-divider {
  display: flex;
  align-items: center;
  margin: 1.2em 0;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background-color: var(--border);
  }

  span {
    padding: 0 0.8em;
    color: var(--text-alt);
    font-size: 0.82em;
    white-space: nowrap;
  }
}

// 折叠式登录方式
.login-method-toggle {
  display: flex;
  align-items: center;
  padding: 0.7em 0;
  color: var(--text);
  font-size: 0.9em;
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: var(--brand-accent);
  }

  &.active {
    color: var(--brand-accent);
  }

  &.secondary {
    margin-top: 0.3em;
  }

  .login-method-toggle-icon {
    display: flex;
    align-items: center;
    margin-right: 0.5em;
    opacity: 0.7;
  }

  .toggle-arrow {
    margin-left: auto;
    font-size: 0.9em;
    transition: transform 0.2s;

    &.expanded {
      transform: rotate(180deg);
    }
  }
}

.sms-form-container,
.password-form-container {
  padding: 1em 0 0.5em;
}

// 密码登录表单
.password-login-section {
  .field {
    margin-bottom: 1em;
  }

  .input {
    height: 3em;
    padding: 1.5em;
    border-radius: 4px;

    &::placeholder {
      color: #999;
    }

    &:focus {
      border-color: var(--brand-accent);
    }
  }

  .password-login-button {
    background-color: var(--brand-accent);
    border-color: var(--brand-accent);
    color: #fff;
    font-weight: 500;

    &:hover {
      background-color: $brand-accent-dark;
      border-color: $brand-accent-dark;
    }
  }

  .forgot-password {
    margin-top: 0.8em;
    font-size: 0.85em;

    a {
      color: var(--text-alt);

      &:hover {
        color: var(--brand-accent);
      }
    }
  }
}

.error {
  color: $red;
  margin-top: 0.5em;
  font-size: 0.9em;
}

// 底部
.login-footer {
  margin-top: 1.5em;
  padding-top: 1em;
  border-top: 1px solid var(--border);
  text-align: center;

  p {
    color: var(--text-alt);
    font-size: 0.82em;
  }
}

// 响应式
@media (max-width: 1600px) {
  .box {
    margin-top: 4em;
  }
}

@media (min-width: 500px) {
  .container {
    margin: 0 auto;
  }
}

@media (max-width: 500px) {
  .login-huazong .container {
    flex: 1;
    width: 100%;
    max-width: 100%;
    display: flex;
  }

  .login-huazong .box {
    flex: 1;
    max-width: 100%;
  }

  .hero {
    display: flex;
    flex-direction: column;
  }

  .box {
    margin: 0;
    width: 100%;
    min-width: 100%;
    border-radius: 0;
  }
}
</style>
