<template>
  <page-layout :side="!!activeReviewId">
    <template #main>
      <div class="asset-review-queue">
        <header class="flexrow">
          <page-title class="mt1 filler" text="资产审核" />
        </header>

        <!-- Stats bar -->
        <div class="stats-bar flexrow">
          <div class="stat-card">
            <span class="stat-value pending">{{ stats.pending }}</span>
            <span class="stat-label">待审核</span>
          </div>
          <div class="stat-card">
            <span class="stat-value approved">{{ stats.approved_today }}</span>
            <span class="stat-label">今日通过</span>
          </div>
          <div class="stat-card">
            <span class="stat-value rejected">{{ stats.rejected_today }}</span>
            <span class="stat-label">今日驳回</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">{{ formattedAvgTime }}</span>
            <span class="stat-label">平均耗时</span>
          </div>
        </div>

        <!-- Filter tabs -->
        <div class="filter-bar flexrow">
          <div class="filter-tabs flexrow">
            <span
              class="filter-tab"
              :class="{ active: currentFilter === null }"
              @click="setFilter(null)"
            >
              全部
            </span>
            <span
              class="filter-tab"
              :class="{ active: currentFilter === 'pending' }"
              @click="setFilter('pending')"
            >
              待审核
            </span>
            <span
              class="filter-tab"
              :class="{ active: currentFilter === 'approved' }"
              @click="setFilter('approved')"
            >
              已通过
            </span>
            <span
              class="filter-tab"
              :class="{ active: currentFilter === 'rejected' }"
              @click="setFilter('rejected')"
            >
              已驳回
            </span>
            <span
              class="filter-tab"
              :class="{ active: currentFilter === 'revision_requested' }"
              @click="setFilter('revision_requested')"
            >
              需修改
            </span>
          </div>
          <span class="filler"></span>
          <div class="batch-actions" v-if="checkedIds.length > 0">
            <button-simple
              class="batch-approve-btn"
              text="批量通过"
              icon="check"
              @click="onBatchApprove"
            />
            <button-simple
              class="batch-reject-btn"
              text="批量驳回"
              icon="x"
              @click="onBatchReject"
            />
          </div>
        </div>

        <!-- Queue list -->
        <div class="queue-content">
          <table-info
            :is-loading="isLoading"
            :is-error="false"
            v-if="isLoading"
          />
          <div
            class="has-text-centered empty-message"
            v-else-if="!reviewQueue.length"
          >
            暂无审核记录
          </div>
          <template v-else>
            <table class="review-table">
              <thead>
                <tr>
                  <th class="col-check">
                    <label class="table-checkbox">
                      <input
                        type="checkbox"
                        :checked="allChecked"
                        @change="toggleSelectAll"
                      />
                    </label>
                  </th>
                  <th class="col-thumb">缩略图</th>
                  <th class="col-name">资产名</th>
                  <th class="col-category">分类</th>
                  <th class="col-submitter">提交者</th>
                  <th class="col-time">提交时间</th>
                  <th class="col-status">状态</th>
                  <th class="col-action">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  :key="review.id"
                  :class="{ 'row-active': activeReviewId === review.id }"
                  v-for="review in reviewQueue"
                >
                  <td class="col-check">
                    <label class="table-checkbox">
                      <input
                        type="checkbox"
                        :value="review.id"
                        v-model="checkedIds"
                      />
                    </label>
                  </td>
                  <td class="col-thumb">
                    <div class="row-thumbnail">
                      <img
                        :src="review.asset_thumbnail || review.asset_preview_url"
                        :alt="review.asset_name"
                        v-if="review.asset_thumbnail || review.asset_preview_url"
                      />
                      <span class="thumb-placeholder" v-else>📦</span>
                    </div>
                  </td>
                  <td class="col-name">{{ review.asset_name }}</td>
                  <td class="col-category">
                    <span class="category-tag">
                      {{ getCategoryLabel(review.asset_category) }}
                    </span>
                  </td>
                  <td class="col-submitter">{{ review.submitter_name }}</td>
                  <td class="col-time">{{ formatTime(review.created_at) }}</td>
                  <td class="col-status">
                    <span
                      class="review-status-badge"
                      :class="'status-' + review.status"
                    >
                      {{ getStatusLabel(review.status) }}
                    </span>
                  </td>
                  <td class="col-action">
                    <button-simple
                      class="review-btn"
                      text="审核"
                      icon="eye"
                      @click="openReviewPanel(review.id)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Select all / batch bar -->
            <div class="batch-bar flexrow" v-if="checkedIds.length > 0">
              <span class="batch-count">
                已选 {{ checkedIds.length }} 项
              </span>
              <button-simple
                class="batch-approve-btn"
                text="批量通过"
                icon="check"
                @click="onBatchApprove"
              />
              <button-simple
                class="batch-reject-btn"
                text="批量驳回"
                icon="x"
                @click="onBatchReject"
              />
              <span class="filler"></span>
              <button-simple
                text="取消选择"
                icon="x"
                @click="checkedIds = []"
              />
            </div>

            <!-- Pagination -->
            <div class="pagination flexrow" v-if="totalPages > 1">
              <button-simple
                icon="chevron-left"
                :disabled="pagination.page <= 1"
                @click="goToPage(pagination.page - 1)"
              />
              <span
                class="page-number"
                :class="{ active: pagination.page === p }"
                :key="p"
                @click="goToPage(p)"
                v-for="p in displayedPages"
              >
                {{ p }}
              </span>
              <button-simple
                icon="chevron-right"
                :disabled="pagination.page >= totalPages"
                @click="goToPage(pagination.page + 1)"
              />
              <span class="pagination-info">
                共 {{ pagination.total }} 条记录
              </span>
            </div>
          </template>
        </div>
      </div>
    </template>

    <template #side>
      <asset-review-panel
        v-if="activeReviewId"
        :review-id="activeReviewId"
        @approved="onReviewAction"
        @rejected="onReviewAction"
        @revision-requested="onReviewAction"
        @close="activeReviewId = null"
      />
    </template>
  </page-layout>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import AssetReviewPanel from '@/components/widgets/AssetReviewPanel.vue'
import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import PageLayout from '@/components/layouts/PageLayout.vue'
import PageTitle from '@/components/widgets/PageTitle.vue'
import TableInfo from '@/components/widgets/TableInfo.vue'

export default {
  name: 'asset-review-queue',

  components: {
    AssetReviewPanel,
    ButtonSimple,
    PageLayout,
    PageTitle,
    TableInfo
  },

  data() {
    return {
      activeReviewId: null,
      checkedIds: [],
      currentFilter: null
    }
  },

  mounted() {
    this.loadReviewQueue()
    this.loadReviewStats()
  },

  computed: {
    ...mapGetters([
      'reviewQueue',
      'reviewStats',
      'reviewIsLoading',
      'reviewQueuePagination',
      'globalAssetCategories'
    ]),

    stats() {
      return this.reviewStats
    },

    isLoading() {
      return this.reviewIsLoading
    },

    pagination() {
      return this.reviewQueuePagination
    },

    totalPages() {
      if (!this.pagination.total || !this.pagination.perPage) return 1
      return Math.ceil(this.pagination.total / this.pagination.perPage)
    },

    displayedPages() {
      const pages = []
      const total = this.totalPages
      const current = this.pagination.page
      const range = 2
      for (let i = 1; i <= total; i++) {
        if (
          i === 1 ||
          i === total ||
          (i >= current - range && i <= current + range)
        ) {
          pages.push(i)
        }
      }
      return pages
    },

    allChecked() {
      return (
        this.reviewQueue.length > 0 &&
        this.checkedIds.length === this.reviewQueue.length
      )
    },

    formattedAvgTime() {
      const hours = this.stats.avg_review_hours || 0
      if (hours < 1) return `${Math.round(hours * 60)}m`
      return `${Math.round(hours)}h`
    }
  },

  methods: {
    ...mapActions([
      'loadReviewQueue',
      'loadReviewStats',
      'setReviewQueueFilter',
      'setReviewQueuePage',
      'batchApproveReviews',
      'batchRejectReviews'
    ]),

    setFilter(status) {
      this.currentFilter = status
      this.checkedIds = []
      this.setReviewQueueFilter(status)
    },

    goToPage(page) {
      if (page < 1 || page > this.totalPages) return
      this.setReviewQueuePage(page)
    },

    openReviewPanel(reviewId) {
      this.activeReviewId = reviewId
    },

    toggleSelectAll() {
      if (this.allChecked) {
        this.checkedIds = []
      } else {
        this.checkedIds = this.reviewQueue.map((r) => r.id)
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
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 60) return `${diffMins}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`
      if (diffDays < 7) return `${diffDays}天前`
      return date.toLocaleDateString('zh-CN')
    },

    async onBatchApprove() {
      if (!this.checkedIds.length) return
      if (!confirm(`确定批量通过 ${this.checkedIds.length} 项审核？`)) return
      try {
        await this.batchApproveReviews({
          reviewIds: this.checkedIds,
          comment: '批量通过'
        })
        this.checkedIds = []
      } catch (err) {
        console.error('Batch approve failed:', err)
      }
    },

    async onBatchReject() {
      if (!this.checkedIds.length) return
      if (!confirm(`确定批量驳回 ${this.checkedIds.length} 项审核？`)) return
      try {
        await this.batchRejectReviews({
          reviewIds: this.checkedIds,
          comment: '批量驳回'
        })
        this.checkedIds = []
      } catch (err) {
        console.error('Batch reject failed:', err)
      }
    },

    onReviewAction() {
      this.activeReviewId = null
      this.loadReviewQueue()
      this.loadReviewStats()
    }
  },

  head() {
    return {
      title: '资产审核 - Kitsu'
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-review-queue {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  padding: 4em 2em 1em 2em;
  color: var(--text);
}

/* Stats bar */
.stats-bar {
  gap: 1em;
  margin-bottom: 1.5em;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.8em 1.5em;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 0.8em;
  min-width: 100px;
}

.stat-value {
  font-size: 1.6em;
  font-weight: 700;
  line-height: 1.2;

  &.pending {
    color: #f0a020;
  }

  &.approved {
    color: #00b242;
  }

  &.rejected {
    color: #e74c3c;
  }
}

.stat-label {
  font-size: 0.8em;
  color: var(--text-alt);
  margin-top: 0.2em;
}

/* Filter bar */
.filter-bar {
  margin-bottom: 1em;
  align-items: center;
  gap: 1em;
}

.filter-tabs {
  gap: 0;
  border-bottom: 1px solid var(--border);
}

.filter-tab {
  padding: 0.5em 1.2em;
  font-size: 0.9em;
  cursor: pointer;
  color: var(--text-alt);
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;

  &:hover {
    color: var(--text);
  }

  &.active {
    color: var(--text-strong);
    font-weight: 600;
    border-bottom-color: var(--background-selected);
  }
}

.batch-actions {
  display: flex;
  gap: 0.5em;
}

/* Table */
.queue-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.review-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;

  th,
  td {
    padding: 0.7em 0.8em;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }

  th {
    font-weight: 600;
    color: var(--text-alt);
    font-size: 0.85em;
    text-transform: uppercase;
    background: var(--background);
    position: sticky;
    top: 0;
    z-index: 1;
  }

  tbody tr {
    transition: background 0.15s;

    &:hover {
      background: var(--background-hover);
    }

    &.row-active {
      background: var(--background-selectable);
    }
  }
}

.col-check {
  width: 40px;
}

.col-thumb {
  width: 60px;
}

.col-action {
  width: 80px;
}

.table-checkbox {
  cursor: pointer;

  input[type='checkbox'] {
    cursor: pointer;
    width: 16px;
    height: 16px;
  }
}

.row-thumbnail {
  width: 44px;
  height: 44px;
  border-radius: 0.4em;
  overflow: hidden;
  background: var(--background-alt);
  display: flex;
  align-items: center;
  justify-content: center;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.thumb-placeholder {
  font-size: 1.2em;
  opacity: 0.5;
}

.category-tag {
  background: var(--background-alt);
  padding: 0.15em 0.5em;
  border-radius: 0.5em;
  font-size: 0.85em;
}

.review-status-badge {
  display: inline-block;
  padding: 0.15em 0.6em;
  border-radius: 1em;
  font-size: 0.8em;
  font-weight: 500;

  &.status-pending {
    background: rgba(240, 160, 32, 0.15);
    color: #f0a020;
  }

  &.status-approved {
    background: rgba(0, 178, 66, 0.15);
    color: #00b242;
  }

  &.status-rejected {
    background: rgba(231, 76, 60, 0.15);
    color: #e74c3c;
  }

  &.status-revision_requested {
    background: rgba(230, 126, 34, 0.15);
    color: #e67e22;
  }
}

.review-btn {
  font-size: 0.85em;
}

/* Batch bar */
.batch-bar {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 1em;
  padding: 0.8em 1.2em;
  background: var(--background);
  border: 1px solid var(--background-selected);
  border-radius: 0.8em;
  margin-top: 1em;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.batch-count {
  font-size: 0.9em;
  font-weight: 600;
  color: var(--text-strong);
}

.batch-approve-btn {
  color: #00b242;
}

.batch-reject-btn {
  color: #e74c3c;
}

/* Pagination */
.pagination {
  margin-top: 2em;
  justify-content: center;
  align-items: center;
  gap: 0.5em;
}

.page-number {
  padding: 0.3em 0.7em;
  border-radius: 0.5em;
  cursor: pointer;
  font-size: 0.9em;

  &:hover {
    background: var(--background-hover);
  }

  &.active {
    background: var(--background-selected);
    font-weight: bold;
  }
}

.pagination-info {
  margin-left: 1em;
  font-size: 0.85em;
  color: var(--text-alt);
}

.empty-message {
  padding: 4em;
  color: var(--text-alt);
}
</style>
