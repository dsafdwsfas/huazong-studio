<template>
  <div class="asset-submit-review">
    <!-- Already approved -->
    <div class="review-badge approved" v-if="asset.status === 'reviewed' || asset.status === 'approved'">
      <check-circle-icon :size="16" />
      <span>已通过</span>
    </div>

    <!-- Pending review -->
    <div class="review-badge pending" v-else-if="asset.status === 'pending_review'">
      <clock-icon :size="16" />
      <span>审核中</span>
    </div>

    <!-- Revision requested -->
    <div class="review-badge revision" v-else-if="asset.status === 'revision_requested'">
      <alert-circle-icon :size="16" />
      <span>需修改</span>
      <button
        class="submit-link"
        @click="showForm = true"
        v-if="!showForm"
      >
        重新提交
      </button>
    </div>

    <!-- Draft or rejected: show submit button -->
    <template v-else>
      <button
        class="submit-btn"
        @click="showForm = true"
        v-if="!showForm"
      >
        <send-icon :size="16" />
        提交审核
      </button>
    </template>

    <!-- Submit form (inline) -->
    <div class="submit-form" v-if="showForm">
      <textarea
        class="submit-textarea"
        v-model="comment"
        placeholder="提交说明（可选）..."
        rows="3"
      ></textarea>
      <div class="submit-form-actions flexrow">
        <button
          class="confirm-btn"
          @click="onSubmit"
          :disabled="isSubmitting"
        >
          {{ isSubmitting ? '提交中...' : '确认提交' }}
        </button>
        <button
          class="cancel-btn"
          @click="showForm = false"
          :disabled="isSubmitting"
        >
          取消
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import {
  AlertCircleIcon,
  CheckCircleIcon,
  ClockIcon,
  SendIcon
} from 'lucide-vue-next'

export default {
  name: 'asset-submit-review',

  components: {
    AlertCircleIcon,
    CheckCircleIcon,
    ClockIcon,
    SendIcon
  },

  props: {
    asset: {
      type: Object,
      required: true
    }
  },

  emits: ['submitted'],

  data() {
    return {
      showForm: false,
      comment: '',
      isSubmitting: false
    }
  },

  methods: {
    ...mapActions(['submitForReview']),

    async onSubmit() {
      this.isSubmitting = true
      try {
        await this.submitForReview({
          assetId: this.asset.id,
          comment: this.comment
        })
        this.showForm = false
        this.comment = ''
        this.$emit('submitted')
      } catch (err) {
        console.error('Submit for review failed:', err)
      } finally {
        this.isSubmitting = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-submit-review {
  margin-top: 0.5em;
}

.review-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  padding: 0.3em 0.8em;
  border-radius: 1em;
  font-size: 0.85em;
  font-weight: 500;

  &.approved {
    background: rgba(0, 178, 66, 0.12);
    color: #00b242;
  }

  &.pending {
    background: rgba(240, 160, 32, 0.12);
    color: #f0a020;
  }

  &.revision {
    background: rgba(230, 126, 34, 0.12);
    color: #e67e22;
  }
}

.submit-link {
  background: none;
  border: none;
  color: inherit;
  text-decoration: underline;
  cursor: pointer;
  font-size: 0.9em;
  margin-left: 0.3em;

  &:hover {
    opacity: 0.8;
  }
}

.submit-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  padding: 0.4em 0.8em;
  border: 1px solid var(--border);
  border-radius: 0.5em;
  background: var(--background);
  color: var(--text);
  font-size: 0.85em;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;

  &:hover {
    background: var(--background-hover);
    border-color: var(--background-selected);
  }
}

.submit-form {
  margin-top: 0.5em;
}

.submit-textarea {
  width: 100%;
  padding: 0.5em;
  border: 1px solid var(--border);
  border-radius: 0.4em;
  background: var(--background);
  color: var(--text);
  font-size: 0.85em;
  resize: vertical;
  min-height: 60px;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: var(--background-selected);
  }
}

.submit-form-actions {
  margin-top: 0.4em;
  gap: 0.4em;
}

.confirm-btn {
  padding: 0.35em 0.8em;
  border: none;
  border-radius: 0.4em;
  background: #00b242;
  color: #fff;
  font-size: 0.85em;
  cursor: pointer;
  transition: opacity 0.15s;

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.cancel-btn {
  padding: 0.35em 0.8em;
  border: 1px solid var(--border);
  border-radius: 0.4em;
  background: var(--background);
  color: var(--text-alt);
  font-size: 0.85em;
  cursor: pointer;

  &:hover {
    background: var(--background-hover);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
</style>
