<template>
  <div class="sms-login-form">
    <div class="field">
      <div class="control has-icons-left">
        <div class="phone-input-wrapper">
          <span class="phone-prefix">+86</span>
          <input
            class="input is-medium phone-input"
            type="tel"
            maxlength="11"
            placeholder="请输入手机号"
            :value="phone"
            @input="onPhoneInput"
            @keyup.enter="onSendCode"
          />
        </div>
      </div>
    </div>

    <div class="field has-addons sms-code-field">
      <div class="control is-expanded">
        <input
          class="input is-medium"
          type="text"
          maxlength="6"
          placeholder="请输入6位验证码"
          :value="smsCode"
          @input="onCodeInput"
          @keyup.enter="onLogin"
        />
      </div>
      <div class="control">
        <a
          class="button is-medium send-code-button"
          :class="{
            'is-loading': isSendingCode
          }"
          :disabled="!canSendCode"
          @click="onSendCode"
        >
          {{ sendCodeText }}
        </a>
      </div>
    </div>

    <p class="control">
      <a
        class="button is-medium is-fullwidth login-button"
        :class="{
          'is-loading': isSmsLoginLoading
        }"
        :disabled="!canLogin"
        @click="onLogin"
      >
        登录
      </a>
    </p>

    <p class="control error has-text-centered" v-if="smsError">
      {{ smsError }}
    </p>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'sms-login-form',

  computed: {
    ...mapGetters([
      'smsPhone',
      'smsCode',
      'isSendingCode',
      'isSmsLoginLoading',
      'smsError',
      'smsCooldown',
      'canSendCode'
    ]),

    phone() {
      return this.smsPhone
    },

    sendCodeText() {
      if (this.smsCooldown > 0) {
        return `${this.smsCooldown}s`
      }
      return '发送验证码'
    },

    canLogin() {
      return (
        this.phone.length === 11 &&
        this.smsCode.length === 6 &&
        !this.isSmsLoginLoading
      )
    }
  },

  methods: {
    ...mapActions([
      'setSmsPhone',
      'setSmsCode',
      'sendSmsCode',
      'smsLogin',
      'clearSmsError'
    ]),

    onPhoneInput(e) {
      const value = e.target.value.replace(/\D/g, '').slice(0, 11)
      e.target.value = value
      this.setSmsPhone(value)
      if (this.smsError) this.clearSmsError()
    },

    onCodeInput(e) {
      const value = e.target.value.replace(/\D/g, '').slice(0, 6)
      e.target.value = value
      this.setSmsCode(value)
      if (this.smsError) this.clearSmsError()
    },

    onSendCode() {
      if (this.canSendCode) {
        this.sendSmsCode()
      }
    },

    onLogin() {
      if (!this.canLogin) return
      this.$emit('login')
    }
  }
}
</script>

<style lang="scss" scoped>
.sms-login-form {
  .field {
    margin-bottom: 1em;
  }

  .phone-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;

    .phone-prefix {
      position: absolute;
      left: 12px;
      color: var(--text);
      font-size: 1em;
      font-weight: 500;
      z-index: 1;
      pointer-events: none;
    }

    .phone-input {
      padding-left: 50px;
    }
  }

  .sms-code-field {
    .input {
      height: 3em;
      border-radius: 4px 0 0 4px;
    }

    .send-code-button {
      background-color: var(--brand-accent);
      border-color: var(--brand-accent);
      color: #fff;
      white-space: nowrap;
      min-width: 120px;
      border-radius: 0 4px 4px 0;

      &:hover:not([disabled]) {
        background-color: $brand-accent-dark;
        border-color: $brand-accent-dark;
      }

      &[disabled] {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }
  }

  .login-button {
    background-color: var(--brand-accent);
    border-color: var(--brand-accent);
    color: #fff;
    font-weight: 500;

    &:hover:not([disabled]) {
      background-color: $brand-accent-dark;
      border-color: $brand-accent-dark;
    }

    &[disabled] {
      opacity: 0.6;
      cursor: not-allowed;
    }
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

  .error {
    color: $red;
    margin-top: 0.5em;
    font-size: 0.9em;
  }
}
</style>
