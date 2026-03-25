<template>
  <div class="asset-review-panel">
    <div class="panel-header flexrow">
      <h2 class="filler">
        审核资产{{ currentReview ? ': ' + currentReview.asset_name : '' }}
      </h2>
      <button-simple icon="x" @click="$emit('close')" />
    </div>

    <div class="panel-loading" v-if="isLoading">
      <spinner />
    </div>

    <template v-else-if="currentReview">
      <!-- Asset preview -->
      <div class="panel-thumbnail">
        <img
          :src="currentReview.asset_thumbnail || currentReview.asset_preview_url"
          :alt="currentReview.asset_name"
          v-if="currentReview.asset_thumbnail || currentReview.asset_preview_url"
        />
        <div class="thumbnail-placeholder" v-else>
          <span class="placeholder-icon">📦</span>
        </div>
      </div>

      <!-- Asset info -->
      <div class="panel-section">
        <div class="info-row">
          <span class="info-label">名称</span>
          <span class="info-value">{{ currentReview.asset_name }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">分类</span>
          <span class="info-value">
            <span class="category-tag">
              {{ getCategoryLabel(currentReview.asset_category) }}
            </span>
          </span>
        </div>
        <div class="info-row" v-if="currentReview.asset_description">
          <span class="info-label">描述</span>
          <span class="info-value">{{ currentReview.asset_description }}</span>
        </div>
        <div class="info-row" v-if="currentReview.asset_tags && currentReview.asset_tags.length">
          <span class="info-label">标签</span>
          <span class="info-value">
            <span
              class="tag-chip"
              :key="tag"
              v-for="tag in currentReview.asset_tags"
            >
              {{ tag }}
            </span>
          </span>
        </div>
        <div class="info-row">
          <span class="info-label">提交者</span>
          <span class="info-value">{{ currentReview.submitter_name }}</span>
        </div>
        <div class="info-row" v-if="currentReview.version">
          <span class="info-label">提交版本</span>
          <span class="info-value">v{{ currentReview.version }}</span>
        </div>
        <div class="info-row" v-if="currentReview.comment">
          <span class="info-label">提交说明</span>
          <span class="info-value comment-text">
            "{{ currentReview.comment }}"
          </span>
        </div>
      </div>

      <!-- Review history -->
      <div class="panel-section" v-if="reviewHistory.length">
        <h3>审核历史</h3>
        <div class="history-list">
          <div
            class="history-item"
            :key="item.id"
            v-for="item in reviewHistory"
          >
            <span
              class="history-status"
              :class="'status-' + item.status"
            >
              {{ getStatusLabel(item.status) }}
            </span>
            <span class="history-reviewer">{{ item.reviewer_name }}</span>
            <span class="history-comment" v-if="item.reviewer_comment">
              "{{ item.reviewer_comment }}"
            </span>
            <span class="history-time">{{ formatTime(item.reviewed_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Review action form -->
      <div
        class="panel-section review-form"
        v-if="currentReview.status === 'pending' || currentReview.status === 'revision_requested'"
      >
        <h3>审核意见</h3>
        <textarea
          class="review-textarea"
          v-model="reviewComment"
          placeholder="输入审核意见..."
          rows="4"
        ></textarea>

        <div class="review-actions flexrow">
          <button
            class="action-btn approve-btn"
            @click="onApprove"
            :disabled="actionLoading"
          >
            <check-icon :size="16" />
            通过
          </button>
          <button
            class="action-btn revision-btn"
            @click="onRequestRevision"
            :disabled="actionLoading"
          >
            <refresh-cw-icon :size="16" />
            需修改
          </button>
          <button
            class="action-btn reject-btn"
            @click="onReject"
            :disabled="actionLoading"
          >
            <x-icon :size="16" />
            驳回
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import { CheckIcon, RefreshCwIcon, XIcon } from 'lucide-vue-next'

import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import Spinner from '@/components/widgets/Spinner.vue'

export default {
  name: 'asset-review-panel',

  components: {
    ButtonSimple,
    CheckIcon,
    RefreshCwIcon,
    Spinner,
    XIcon
  },

  props: {
    reviewId: {
      type: String,
      required: true
    }
  },

  emits: ['approved', 'rejected', 'revision-requested', 'close'],

  data() {
    return {
      reviewComment: '',
      reviewHistory: [],
      actionLoading: false
    }
  },

  mounted() {
    this.fetchReview()
  },

  computed: {
    ...mapGetters([
      'currentReview',
      'reviewIsLoading',
      'globalAssetCategories'
    ]),

    isLoading() {
      return this.reviewIsLoading
    }
  },

  methods: {
    ...mapActions([
      'loadReview',
      'loadAssetReviews',
      'approveReview',
      'rejectReview',
      'requestRevision'
    ]),

    async fetchReview() {
      const review = await this.loadReview(this.reviewId)
      if (review && review.asset_id) {
        const history = await this.loadAssetReviews(review.asset_id)
        this.reviewHistory = (history || []).filter(
          (h) => h.id !== this.reviewId
        )
      }
    },

    getCategoryLabel(category) {
      const cat = this.globalAssetCategories.find(
        (c) => c.value === category
      )
      return cat ? cat.label : category || '未分类'
    },

    getStatusLabel(status) {
      const labels = {
        pending: '待审核',
        approved: '已通过',
        rejected: '已驳回',
        revision_requested: '需修改'
      }
      return labels[status] || status
    },

    formatTime(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    async onApprove() {
      this.actionLoading = true
      try {
        await this.approveReview({
          reviewId: this.reviewId,
          comment: this.reviewComment
        })
        this.$emit('approved')
      } catch (err) {
        console.error('Approve failed:', err)
      } finally {
        this.actionLoading = false
      }
    },

    async onReject() {
      if (!this.reviewComment.trim()) {
        alert('驳回时必须填写审核意见')
        return
      }
      this.actionLoading = true
      try {
        await this.rejectReview({
          reviewId: this.reviewId,
          comment: this.reviewComment
        })
        this.$emit('rejected')
      } catch (err) {
        console.error('Reject failed:', err)
      } finally {
        this.actionLoading = false
      }
    },

    async onRequestRevision() {
      if (!this.reviewComment.trim()) {
        alert('请求修改时必须填写审核意见')
        return
      }
      this.actionLoading = true
      try {
        await this.requestRevision({
          reviewId: this.reviewId,
          comment: this.reviewComment
        })
        this.$emit('revision-requested')
      } catch (err) {
        console.error('Request revision failed:', err)
      } finally {
        this.actionLoading = false
      }
    }
  },

  watch: {
    reviewId() {
      this.reviewComment = ''
      this.reviewHistory = []
      this.fetchReview()
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-review-panel {
  padding: 1em;
}

.panel-header {
  margin-bottom: 1em;
  align-items: center;

  h2 {
    margin: 0;
    font-size: 1.1em;
  }
}

.panel-loading {
  display: flex;
  justify-content: center;
  padding: 3em;
}

.panel-thumbnail {
  margin-bottom: 1em;
  border-radius: 0.5em;
  overflow: hidden;

  img {
    width: 100%;
    max-height: 250px;
    object-fit: cover;
  }
}

.thumbnail-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 180px;
  background: var(--background-alt);

  .placeholder-icon {
    font-size: 3em;
    opacity: 0.5;
  }
}

.panel-section {
  margin-bottom: 1.5em;

  h3 {
    font-size: 0.95em;
    font-weight: 600;
    margin-bottom: 0.5em;
    color: var(--text-strong);
  }
}

.info-row {
  display: flex;
  margin-bottom: 0.5em;
  font-size: 0.9em;
  gap: 0.5em;
}

.info-label {
  color: var(--text-alt);
  min-width: 5em;
  flex-shrink: 0;
}

.info-value {
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 0.3em;
  flex-wrap: wrap;
}

.category-tag {
  background: var(--background-alt);
  padding: 0.15em 0.5em;
  border-radius: 0.5em;
  font-size: 0.85em;
}

.tag-chip {
  background: var(--background-alt);
  padding: 0.2em 0.6em;
  border-radius: 1em;
  font-size: 0.8em;
}

.comment-text {
  font-style: italic;
  color: var(--text-alt);
}

/* History */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.6em;
}

.history-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5em;
  padding: 0.5em;
  background: var(--background);
  border-radius: 0.4em;
  border-left: 3px solid var(--border);
  font-size: 0.85em;
}

.history-status {
  font-weight: 600;
  font-size: 0.8em;
  padding: 0.1em 0.5em;
  border-radius: 0.5em;

  &.status-approved {
    color: #00b242;
    background: rgba(0, 178, 66, 0.1);
  }

  &.status-rejected {
    color: #e74c3c;
    background: rgba(231, 76, 60, 0.1);
  }

  &.status-revision_requested {
    color: #e67e22;
    background: rgba(230, 126, 34, 0.1);
  }

  &.status-pending {
    color: #f0a020;
    background: rgba(240, 160, 32, 0.1);
  }
}

.history-reviewer {
  font-weight: 500;
}

.history-comment {
  color: var(--text-alt);
  font-style: italic;
}

.history-time {
  color: var(--text-alt);
  font-size: 0.85em;
  margin-left: auto;
}

/* Review form */
.review-form {
  border-top: 1px solid var(--border);
  padding-top: 1em;
}

.review-textarea {
  width: 100%;
  padding: 0.7em;
  border: 1px solid var(--border);
  border-radius: 0.5em;
  background: var(--background);
  color: var(--text);
  font-size: 0.9em;
  resize: vertical;
  min-height: 80px;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: var(--background-selected);
  }
}

.review-actions {
  margin-top: 0.8em;
  gap: 0.5em;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  padding: 0.5em 1em;
  border: none;
  border-radius: 0.5em;
  font-size: 0.9em;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;

  &:hover {
    opacity: 0.9;
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
}

.approve-btn {
  background: #00b242;
  color: #fff;
}

.revision-btn {
  background: #e67e22;
  color: #fff;
}

.reject-btn {
  background: #e74c3c;
  color: #fff;
}
</style>
