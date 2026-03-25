<template>
  <div class="review-panel" v-if="active">
    <div class="panel-header">
      <div class="panel-title">
        <h4>评审面板</h4>
        <span class="shot-label">{{ shotName }} — {{ sequenceName }}</span>
      </div>
      <button class="btn-close" @click="$emit('close')">
        <XIcon :size="16" />
      </button>
    </div>

    <!-- Current status -->
    <div class="panel-section">
      <div class="section-label">当前状态</div>
      <div class="current-status" v-if="primaryTask">
        <span
          class="status-dot"
          :style="{ background: primaryTask.task_status_color || '#999' }"
        />
        <span class="status-name">{{ primaryTask.task_status_name }}</span>
      </div>
      <div class="current-status muted" v-else>
        暂无任务
      </div>
    </div>

    <!-- Quick actions -->
    <div class="panel-section" v-if="isManager || primaryTask">
      <div class="section-label">快捷操作</div>
      <div class="quick-actions">
        <button
          v-if="isManager"
          class="btn-action btn-approve"
          @click="onQuickAction('approve')"
        >
          <CheckIcon :size="14" />
          批准
        </button>
        <button
          v-if="isManager"
          class="btn-action btn-reject"
          @click="onQuickAction('reject')"
        >
          <CornerDownLeftIcon :size="14" />
          退回修改
        </button>
        <button
          v-if="showSubmitButton"
          class="btn-action btn-submit"
          @click="onQuickAction('submit')"
        >
          <SendIcon :size="14" />
          提交审阅
        </button>
      </div>
    </div>

    <!-- Review comment input -->
    <div class="panel-section">
      <div class="section-label">评审意见</div>
      <textarea
        v-model="commentText"
        class="comment-input"
        placeholder="输入评审意见..."
        rows="3"
      />
      <div class="comment-actions">
        <select v-model="selectedAction" class="action-select">
          <option value="comment">仅评论</option>
          <option v-if="isManager" value="approve">批准</option>
          <option v-if="isManager" value="reject">退回修改</option>
          <option value="submit">提交审阅</option>
        </select>
        <button
          class="btn-submit-review"
          :disabled="!commentText.trim()"
          @click="onSubmitReview"
        >
          提交评审
        </button>
      </div>
    </div>

    <!-- Review history -->
    <div class="panel-section section-history">
      <div class="section-label">评审历史</div>

      <div v-if="isLoadingReviews" class="loading">
        <spinner />
      </div>

      <div v-else-if="reviews.length === 0" class="empty">
        暂无评审记录
      </div>

      <div v-else class="review-timeline">
        <div
          v-for="review in reviews"
          :key="review.id"
          class="timeline-item"
        >
          <div class="timeline-node">
            <span
              class="node-dot"
              :class="actionClass(review.action)"
            />
            <span class="node-line" />
          </div>
          <div class="timeline-content">
            <div class="review-header">
              <span class="reviewer-name">
                {{ review.person?.name || '未知用户' }}
              </span>
              <span class="review-date">{{ formatDate(review.created_at) }}</span>
            </div>
            <span class="action-tag" :class="actionClass(review.action)">
              {{ actionLabel(review.action) }}
            </span>
            <p v-if="review.comment" class="review-comment">
              {{ review.comment }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Review stats -->
    <div class="panel-section section-stats" v-if="reviews.length > 0">
      <div class="section-label">审阅统计</div>
      <div class="stats-grid">
        <div class="stat-cell">
          <span class="stat-value">{{ stats.submitCount }}</span>
          <span class="stat-label">提交次数</span>
        </div>
        <div class="stat-cell">
          <span class="stat-value">{{ stats.rejectCount }}</span>
          <span class="stat-label">退回次数</span>
        </div>
        <div class="stat-cell">
          <span class="stat-value">{{ stats.approveCount }}/{{ stats.reviewerCount }}</span>
          <span class="stat-label">批准人数</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import {
  CheckIcon,
  CornerDownLeftIcon,
  SendIcon,
  XIcon
} from 'lucide-vue-next'

export default {
  name: 'ReviewPanel',

  components: {
    CheckIcon,
    CornerDownLeftIcon,
    SendIcon,
    XIcon
  },

  props: {
    active: {
      type: Boolean,
      default: false
    },
    projectId: {
      type: String,
      required: true
    },
    shot: {
      type: Object,
      default: null
    },
    shotName: {
      type: String,
      default: ''
    },
    sequenceName: {
      type: String,
      default: ''
    },
    taskStatuses: {
      type: Array,
      default: () => []
    },
    isManager: {
      type: Boolean,
      default: false
    }
  },

  emits: ['close', 'submit-review', 'status-changed'],

  data() {
    return {
      commentText: '',
      selectedAction: 'comment',
      reviews: [],
      isLoadingReviews: false
    }
  },

  computed: {
    primaryTask() {
      return this.shot?.primary_task || null
    },

    showSubmitButton() {
      if (!this.primaryTask) return true
      const name = (this.primaryTask.task_status_name || '').toLowerCase()
      return !name.includes('review') && !name.includes('审')
    },

    stats() {
      const result = {
        submitCount: 0,
        rejectCount: 0,
        approveCount: 0,
        reviewerCount: 0
      }
      const reviewers = new Set()
      const approvers = new Set()

      for (const r of this.reviews) {
        if (r.action === 'submit') result.submitCount++
        if (r.action === 'reject') result.rejectCount++
        if (r.action === 'approve') {
          result.approveCount++
          if (r.person?.id) approvers.add(r.person.id)
        }
        if (r.person?.id) reviewers.add(r.person.id)
      }

      result.approveCount = approvers.size
      result.reviewerCount = reviewers.size
      return result
    }
  },

  watch: {
    active(val) {
      if (val && this.shot?.id) {
        this.loadReviews()
      }
    },
    'shot.id'() {
      if (this.active && this.shot?.id) {
        this.loadReviews()
      }
    }
  },

  methods: {
    ...mapActions(['loadShotReviews']),

    async loadReviews() {
      if (!this.shot?.id) return
      this.isLoadingReviews = true
      try {
        const result = await this.loadShotReviews({
          projectId: this.projectId,
          shotId: this.shot.id
        })
        this.reviews = (result?.reviews || result || []).sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        )
      } catch (err) {
        console.error('Failed to load reviews:', err)
        this.reviews = []
      } finally {
        this.isLoadingReviews = false
      }
    },

    onQuickAction(action) {
      this.$emit('submit-review', {
        shotId: this.shot?.id,
        taskId: this.primaryTask?.id,
        comment: '',
        action,
        taskStatusId: this.findStatusIdForAction(action)
      })
      this.$emit('status-changed')
    },

    onSubmitReview() {
      if (!this.commentText.trim()) return
      this.$emit('submit-review', {
        shotId: this.shot?.id,
        taskId: this.primaryTask?.id,
        comment: this.commentText.trim(),
        action: this.selectedAction,
        taskStatusId: this.findStatusIdForAction(this.selectedAction)
      })
      this.commentText = ''
      this.selectedAction = 'comment'
      this.$emit('status-changed')
    },

    findStatusIdForAction(action) {
      if (!this.taskStatuses.length) return null
      const nameMap = {
        approve: ['approved', 'done', '已批准', '完成', '通过'],
        reject: ['retake', 'rejected', '退回', '退回修改', '需修改'],
        submit: ['review', 'waiting for review', '待审阅', '审阅中']
      }
      const candidates = nameMap[action] || []
      for (const candidate of candidates) {
        const found = this.taskStatuses.find(
          (s) => s.name.toLowerCase().includes(candidate)
        )
        if (found) return found.id
      }
      return null
    },

    actionLabel(action) {
      const labels = {
        approve: '已批准',
        reject: '退回修改',
        submit: '提交审阅',
        comment: '评论'
      }
      return labels[action] || '评论'
    },

    actionClass(action) {
      return {
        'action-approve': action === 'approve',
        'action-reject': action === 'reject',
        'action-submit': action === 'submit',
        'action-comment': action === 'comment' || !action
      }
    },

    formatDate(isoString) {
      if (!isoString) return ''
      const d = new Date(isoString)
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const h = String(d.getHours()).padStart(2, '0')
      const min = String(d.getMinutes()).padStart(2, '0')
      return `${y}-${m}-${day} ${h}:${min}`
    }
  }
}
</script>

<style lang="scss" scoped>
.review-panel {
  width: 360px;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
  flex-shrink: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.panel-title {
  flex: 1;
  min-width: 0;

  h4 {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
  }

  .shot-label {
    font-size: 0.75rem;
    color: var(--text-alt);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: block;
    margin-top: 2px;
  }
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-alt);
  padding: 4px;
  border-radius: 4px;
  flex-shrink: 0;

  &:hover {
    background: var(--background-hover);
  }
}

.panel-section {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.section-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-alt);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.current-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;

  &.muted {
    color: var(--text-alt);
  }
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-name {
  font-weight: 500;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.btn-action {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
  color: #fff;

  &:hover {
    opacity: 0.85;
  }
}

.btn-approve {
  background: #10ac84;
}

.btn-reject {
  background: #ff9f43;
}

.btn-submit {
  background: #0abde3;
}

.comment-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--background);
  color: var(--text);
  font-size: 0.85rem;
  font-family: inherit;
  resize: vertical;
  min-height: 60px;

  &::placeholder {
    color: var(--text-alt);
  }

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }
}

.comment-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  align-items: center;
}

.action-select {
  padding: 5px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--background);
  color: var(--text);
  font-size: 0.8rem;
  cursor: pointer;
  flex: 1;

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }
}

.btn-submit-review {
  padding: 5px 14px;
  border: none;
  border-radius: 4px;
  background: var(--color-primary, #0078ff);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.15s;

  &:hover:not(:disabled) {
    opacity: 0.85;
  }

  &:disabled {
    opacity: 0.4;
    cursor: default;
  }
}

.section-history {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: var(--text-alt);
  font-size: 0.85rem;
}

.review-timeline {
  flex: 1;
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  gap: 10px;
  padding-bottom: 4px;
}

.timeline-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 16px;
}

.node-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
  background: #999;

  &.action-approve {
    background: #10ac84;
  }

  &.action-reject {
    background: #ff9f43;
  }

  &.action-submit {
    background: #0abde3;
  }

  &.action-comment {
    background: #999;
  }
}

.node-line {
  flex: 1;
  width: 2px;
  background: var(--border);
  margin-top: 4px;
}

.timeline-item:last-child .node-line {
  display: none;
}

.timeline-content {
  flex: 1;
  min-width: 0;
  padding-bottom: 12px;
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 4px;
}

.reviewer-name {
  font-size: 0.8rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.review-date {
  font-size: 0.7rem;
  color: var(--text-alt);
  white-space: nowrap;
  flex-shrink: 0;
}

.action-tag {
  display: inline-block;
  font-size: 0.65rem;
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 500;
  margin-bottom: 4px;

  &.action-approve {
    background: rgba(16, 172, 132, 0.15);
    color: #10ac84;
  }

  &.action-reject {
    background: rgba(255, 159, 67, 0.15);
    color: #ff9f43;
  }

  &.action-submit {
    background: rgba(10, 189, 227, 0.15);
    color: #0abde3;
  }

  &.action-comment {
    background: rgba(153, 153, 153, 0.15);
    color: #999;
  }
}

.review-comment {
  font-size: 0.8rem;
  color: var(--text);
  margin: 0;
  line-height: 1.4;
  word-break: break-word;
}

.section-stats {
  flex-shrink: 0;
}

.stats-grid {
  display: flex;
  gap: 12px;
}

.stat-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-value {
  font-size: 1rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.65rem;
  color: var(--text-alt);
  margin-top: 2px;
}
</style>
