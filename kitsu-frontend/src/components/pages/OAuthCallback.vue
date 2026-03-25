<template>
  <div class="oauth-callback hero is-fullheight">
    <div class="container has-text-centered">
      <div class="box">
        <div class="callback-content" v-if="!error">
          <div class="spinner-wrapper">
            <spinner />
          </div>
          <p class="callback-message">正在登录...</p>
          <p class="callback-sub">请稍候，正在完成身份验证</p>
        </div>
        <div class="callback-content" v-else>
          <p class="callback-error-icon">&#x26A0;</p>
          <p class="callback-message error-text">登录失败</p>
          <p class="callback-sub">{{ error }}</p>
          <p class="control mt2">
            <router-link
              class="button main-button is-fullwidth"
              :to="{ name: 'login-huazong' }"
            >
              返回登录
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import Spinner from '@/components/widgets/Spinner.vue'
import oauth from '@/lib/oauth'
import auth from '@/lib/auth'
import store from '@/store'
import {
  DATA_LOADING_START,
  USER_LOGIN,
  USER_LOGIN_FAIL
} from '@/store/mutation-types'

export default {
  name: 'oauth-callback',

  components: {
    Spinner
  },

  data() {
    return {
      error: ''
    }
  },

  computed: {
    ...mapGetters(['isDarkTheme'])
  },

  mounted() {
    this.handleCallback()
  },

  methods: {
    async handleCallback() {
      try {
        // 方式1：从 URL query params 获取 token
        const token = this.$route.query.token
        if (token) {
          const result = await oauth.handleCallback(token)
          if (result.login && result.user) {
            store.commit(DATA_LOADING_START)
            store.commit(USER_LOGIN, result.user)
            this.navigateAfterLogin()
            return
          }
        }

        // 方式2：检查后端是否通过 cookie 已经设置了认证状态
        // （某些 OAuth 流程后端直接设置 session cookie）
        auth.isServerLoggedIn(err => {
          if (err) {
            this.error = '认证失败，请重试'
            return
          }
          if (store.state.user.isAuthenticated) {
            this.navigateAfterLogin()
          } else {
            this.error = '认证失败，请重试'
          }
        })
      } catch (err) {
        this.error = err.message || '认证过程中发生错误'
      }
    },

    navigateAfterLogin() {
      setTimeout(() => {
        const redirect = this.$route.query.redirect
        if (redirect) {
          this.$router.push(redirect)
        } else {
          this.$router.push('/')
        }
      }, 500)
    }
  },

  head() {
    return {
      title: '正在登录...'
    }
  }
}
</script>

<style lang="scss" scoped>
.oauth-callback {
  background: linear-gradient(
    135deg,
    $brand-primary 0%,
    $brand-secondary 50%,
    darken($brand-primary, 5%) 100%
  );
}

.box {
  border-radius: 1em;
  max-width: 400px;
  margin: 0 auto;
  padding: 3em 2em;
}

.callback-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.spinner-wrapper {
  margin-bottom: 1.5em;
}

.callback-message {
  font-size: 1.2em;
  font-weight: 500;
  color: var(--text-strong);
  margin-bottom: 0.3em;
}

.callback-sub {
  font-size: 0.9em;
  color: var(--text-alt);
}

.callback-error-icon {
  font-size: 3em;
  margin-bottom: 0.3em;
}

.error-text {
  color: $red;
}

.main-button {
  background-color: var(--brand-accent);
  border-color: var(--brand-accent);
  color: #fff;
  font-weight: 500;
  margin-top: 1em;

  &:hover {
    background-color: $brand-accent-dark;
    border-color: $brand-accent-dark;
    color: #fff;
  }
}

@media (max-width: 500px) {
  .oauth-callback .container {
    flex: 1;
    width: 100%;
    max-width: 100%;
    display: flex;
  }

  .box {
    flex: 1;
    margin: 0;
    width: 100%;
    min-width: 100%;
    border-radius: 0;
  }
}
</style>
