<template>
  <div class="asset-version-history" :class="{ compact }">
    <div class="version-header flexrow">
      <h3 class="filler">版本历史</h3>
      <span class="version-count" v-if="versionCount > 0">
        共 {{ versionCount }} 个版本
      </span>
    </div>

    <div class="compare-bar flexrow" v-if="compareSelection.length === 2">
      <span class="compare-label">已选择 2 个版本</span>
      <button-simple
        class="compare-button"
        text="对比版本"
        icon="columns"
        @click="onCompare"
      />
      <button-simple
        icon="x"
        @click="clearCompare"
      />
    </div>

    <table-info
      :is-loading="isLoading"
      v-if="isLoading && versions.length === 0"
    />

    <div
      class="has-text-centered empty-message"
      v-else-if="!versions.length"
    >
      暂无版本记录
    </div>

    <div class="version-timeline" v-else>
      <div
        class="version-item"
        :class="{
          'is-latest': index === 0,
          'is-selected': isCompareSelected(version.id)
        }"
        :key="version.id"
        v-for="(version, index) in versions"
      >
        <div class="timeline-marker">
          <span
            class="marker-dot"
            :class="'type-' + (version.change_type || 'update')"
          ></span>
          <span class="marker-line" v-if="index < versions.length - 1"></span>
        </div>

        <div class="version-content">
          <div class="version-top flexrow">
            <span class="version-number">
              v{{ version.version_number }}
            </span>
            <span class="version-date">
              {{ formatDate(version.created_at) }}
            </span>
            <span class="filler"></span>
            <input
              type="checkbox"
              class="compare-checkbox"
              :checked="isCompareSelected(version.id)"
              :disabled="!isCompareSelected(version.id) && compareSelection.length >= 2"
              @change="toggleCompare(version.id)"
              :title="'选择对比'"
            />
          </div>

          <div class="version-meta">
            <span class="version-author" v-if="version.author_name || version.person">
              {{ version.author_name || (version.person && version.person.full_name) || '未知' }}
            </span>
            <span class="version-type-badge" :class="'type-' + (version.change_type || 'update')">
              {{ getChangeTypeLabel(version.change_type) }}
            </span>
          </div>

          <div class="version-summary" v-if="version.comment || version.summary">
            {{ version.comment || version.summary }}
          </div>

          <div class="version-changes" v-if="version.changes && version.changes.length">
            <span
              class="change-item"
              :key="idx"
              v-for="(change, idx) in version.changes.slice(0, compact ? 2 : 5)"
            >
              {{ change }}
            </span>
            <span
              class="change-more"
              v-if="version.changes.length > (compact ? 2 : 5)"
            >
              +{{ version.changes.length - (compact ? 2 : 5) }} 项变更
            </span>
          </div>

          <div class="version-actions flexrow">
            <button-simple
              class="action-link"
              text="查看差异"
              icon="git-commit"
              @click="$emit('view-diff', version.id)"
            />
            <button-simple
              class="action-link"
              text="恢复"
              icon="rotate-ccw"
              @click="confirmRestore(version)"
              v-if="index > 0"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="load-more" v-if="hasMore">
      <button-simple
        text="加载更多"
        icon="chevrons-down"
        :is-loading="isLoading"
        @click="loadMore"
      />
    </div>

    <!-- Restore confirmation -->
    <div class="restore-overlay" v-if="restoreTarget" @click.self="restoreTarget = null">
      <div class="restore-dialog">
        <h4>确认恢复</h4>
        <p>
          确定要将资产恢复到
          <strong>v{{ restoreTarget.version_number }}</strong> 吗？
          此操作将创建一个新版本。
        </p>
        <div class="dialog-actions flexrow">
          <button-simple
            text="取消"
            @click="restoreTarget = null"
          />
          <button-simple
            class="confirm-button"
            text="确认恢复"
            icon="rotate-ccw"
            @click="doRestore"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import TableInfo from '@/components/widgets/TableInfo.vue'

export default {
  name: 'asset-version-history',

  components: {
    ButtonSimple,
    TableInfo
  },

  props: {
    assetId: {
      type: String,
      required: true
    },
    compact: {
      type: Boolean,
      default: false
    }
  },

  emits: ['view-diff', 'restore', 'compare'],

  data() {
    return {
      compareSelection: [],
      restoreTarget: null
    }
  },

  mounted() {
    this.loadAssetVersions(this.assetId)
  },

  computed: {
    ...mapGetters([
      'assetVersions',
      'assetVersionsIsLoading',
      'assetVersionsPagination',
      'versionCount'
    ]),

    versions() {
      return this.assetVersions
    },

    isLoading() {
      return this.assetVersionsIsLoading
    },

    hasMore() {
      const { page, perPage, total } = this.assetVersionsPagination
      return page * perPage < total
    }
  },

  methods: {
    ...mapActions([
      'loadAssetVersions',
      'restoreAssetVersion',
      'setAssetVersionsPage',
      'clearAssetVersions'
    ]),

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    },

    getChangeTypeLabel(type) {
      const labels = {
        create: '创建',
        update: '更新',
        file_change: '文件变更',
        metadata_change: '信息变更',
        restore: '恢复',
        status_change: '状态变更'
      }
      return labels[type] || '更新'
    },

    isCompareSelected(versionId) {
      return this.compareSelection.includes(versionId)
    },

    toggleCompare(versionId) {
      const idx = this.compareSelection.indexOf(versionId)
      if (idx !== -1) {
        this.compareSelection.splice(idx, 1)
      } else if (this.compareSelection.length < 2) {
        this.compareSelection.push(versionId)
      }
    },

    clearCompare() {
      this.compareSelection = []
    },

    onCompare() {
      if (this.compareSelection.length === 2) {
        this.$emit('compare', this.compareSelection[0], this.compareSelection[1])
      }
    },

    confirmRestore(version) {
      this.restoreTarget = version
    },

    async doRestore() {
      if (!this.restoreTarget) return
      const versionId = this.restoreTarget.id
      this.restoreTarget = null
      this.$emit('restore', versionId)
      try {
        await this.restoreAssetVersion({
          assetId: this.assetId,
          versionId
        })
      } catch (err) {
        console.error('Failed to restore version:', err)
      }
    },

    loadMore() {
      const nextPage = this.assetVersionsPagination.page + 1
      this.setAssetVersionsPage({
        assetId: this.assetId,
        page: nextPage
      })
    }
  },

  watch: {
    assetId(newId, oldId) {
      if (newId !== oldId) {
        this.clearAssetVersions()
        this.compareSelection = []
        if (newId) {
          this.loadAssetVersions(newId)
        }
      }
    }
  },

  beforeUnmount() {
    this.clearAssetVersions()
  }
}
</script>

<style lang="scss" scoped>
.asset-version-history {
  position: relative;
}

.version-header {
  align-items: center;
  margin-bottom: 0.8em;

  h3 {
    font-size: 0.95em;
    font-weight: 600;
    margin: 0;
    color: var(--text-strong);
  }
}

.version-count {
  font-size: 0.8em;
  color: var(--text-alt);
}

.compare-bar {
  background: var(--background-alt);
  border-radius: 0.5em;
  padding: 0.4em 0.6em;
  margin-bottom: 0.8em;
  align-items: center;
  gap: 0.5em;
}

.compare-label {
  font-size: 0.8em;
  color: var(--text);
  flex: 1;
}

.compare-button {
  font-size: 0.8em;
}

.empty-message {
  padding: 2em;
  color: var(--text-alt);
  font-size: 0.9em;
}

/* Timeline layout */
.version-timeline {
  display: flex;
  flex-direction: column;
}

.version-item {
  display: flex;
  gap: 0.8em;
  position: relative;

  &.is-selected {
    .version-content {
      background: var(--background-selectable);
    }
  }
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 16px;
  flex-shrink: 0;
  padding-top: 0.4em;
}

.marker-dot {
  display: block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--text-alt);
  flex-shrink: 0;

  &.type-create {
    background: #00b242;
  }

  &.type-update {
    background: #3d96ff;
  }

  &.type-file_change {
    background: #f5a623;
  }

  &.type-metadata_change {
    background: #9b59b6;
  }

  &.type-restore {
    background: #e74c3c;
  }

  &.type-status_change {
    background: #1abc9c;
  }
}

.marker-line {
  width: 2px;
  flex: 1;
  background: var(--border);
  min-height: 12px;
}

.version-content {
  flex: 1;
  padding: 0.5em 0.6em;
  margin-bottom: 0.4em;
  border-radius: 0.4em;
  border: 1px solid var(--border);
  background: var(--background);
  transition: background 0.15s;
}

.version-top {
  align-items: center;
  gap: 0.5em;
  margin-bottom: 0.3em;
}

.version-number {
  font-weight: 600;
  font-size: 0.9em;
  color: var(--text-strong);
}

.version-date {
  font-size: 0.8em;
  color: var(--text-alt);
}

.compare-checkbox {
  cursor: pointer;
  accent-color: var(--background-selected);
}

.version-meta {
  display: flex;
  align-items: center;
  gap: 0.5em;
  margin-bottom: 0.3em;
}

.version-author {
  font-size: 0.8em;
  color: var(--text-alt);
}

.version-type-badge {
  font-size: 0.75em;
  padding: 0.1em 0.4em;
  border-radius: 0.3em;
  background: var(--background-alt);
  color: var(--text);

  &.type-create {
    background: rgba(0, 178, 66, 0.15);
    color: #00b242;
  }

  &.type-update {
    background: rgba(61, 150, 255, 0.15);
    color: #3d96ff;
  }

  &.type-file_change {
    background: rgba(245, 166, 35, 0.15);
    color: #f5a623;
  }

  &.type-metadata_change {
    background: rgba(155, 89, 182, 0.15);
    color: #9b59b6;
  }

  &.type-restore {
    background: rgba(231, 76, 60, 0.15);
    color: #e74c3c;
  }

  &.type-status_change {
    background: rgba(26, 188, 156, 0.15);
    color: #1abc9c;
  }
}

.version-summary {
  font-size: 0.85em;
  color: var(--text);
  margin-bottom: 0.3em;
}

.version-changes {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3em;
  margin-bottom: 0.3em;
}

.change-item {
  font-size: 0.75em;
  background: var(--background-alt);
  padding: 0.15em 0.4em;
  border-radius: 0.3em;
  color: var(--text-alt);
}

.change-more {
  font-size: 0.75em;
  color: var(--text-alt);
  font-style: italic;
}

.version-actions {
  gap: 0.5em;
  margin-top: 0.3em;
}

.action-link {
  font-size: 0.8em;
  color: var(--text-alt);
  cursor: pointer;

  &:hover {
    color: var(--text);
  }
}

.load-more {
  text-align: center;
  margin-top: 0.8em;
}

/* Restore confirmation overlay */
.restore-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.restore-dialog {
  background: var(--background);
  border-radius: 0.8em;
  padding: 1.5em;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);

  h4 {
    margin: 0 0 0.8em;
    font-size: 1em;
  }

  p {
    font-size: 0.9em;
    color: var(--text);
    margin-bottom: 1.2em;
    line-height: 1.5;
  }
}

.dialog-actions {
  justify-content: flex-end;
  gap: 0.5em;
}

.confirm-button {
  background: var(--background-selected);
  color: white;
}

/* Compact mode adjustments */
.compact {
  .version-content {
    padding: 0.3em 0.5em;
  }

  .version-actions {
    .action-link {
      font-size: 0.75em;
    }
  }

  .version-summary {
    font-size: 0.8em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
