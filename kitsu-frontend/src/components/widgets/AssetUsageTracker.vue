<template>
  <div class="asset-usage-tracker">
    <div class="tracker-header flexrow">
      <h3 class="filler">资产复用追踪</h3>
      <button-simple
        class="flexrow-item"
        text="记录使用"
        icon="plus"
        @click="showRecordForm = true"
      />
    </div>

    <!-- Usage stats summary -->
    <div class="usage-stats flexrow" v-if="usageStats">
      <div class="stat-item">
        <span class="stat-number">{{ usageStats.total_usages || 0 }}</span>
        <span class="stat-label">总使用</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ usageStats.project_count || 0 }}</span>
        <span class="stat-label">涉及项目</span>
      </div>
    </div>

    <!-- Cross-project distribution bar chart -->
    <div
      class="cross-project-section"
      v-if="crossProject && crossProject.length"
    >
      <h4>跨项目分布</h4>
      <div class="bar-chart">
        <div
          class="bar-row"
          :key="item.project_id"
          v-for="item in crossProject"
        >
          <span class="bar-label" :title="item.project_name">
            {{ item.project_name }}
          </span>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{ width: barWidth(item.count) + '%' }"
            ></div>
          </div>
          <span class="bar-count">{{ item.count }}</span>
        </div>
      </div>
    </div>

    <!-- Usage timeline (embedded) -->
    <asset-usage-timeline
      :asset-id="assetId"
      v-if="assetId"
    />

    <!-- Usage records list -->
    <div class="usage-list">
      <h4>使用记录</h4>
      <table-info
        :is-loading="isLoading"
        v-if="isLoading"
      />
      <div
        class="empty-message"
        v-else-if="!usages.length"
      >
        暂无使用记录
      </div>
      <div class="usage-items" v-else>
        <div
          class="usage-item"
          :key="usage.id"
          v-for="usage in usages"
        >
          <div class="usage-item-main">
            <span class="usage-project">{{ usage.project_name || '未知项目' }}</span>
            <span class="usage-type-badge">{{ getUsageTypeLabel(usage.usage_type) }}</span>
          </div>
          <div class="usage-item-meta">
            <span class="usage-user" v-if="usage.user_name">{{ usage.user_name }}</span>
            <span class="usage-time">{{ formatDate(usage.created_at) }}</span>
            <button-simple
              class="usage-delete"
              icon="x"
              @click="onDeleteUsage(usage.id)"
            />
          </div>
          <div class="usage-context" v-if="usage.context">
            {{ usage.context }}
          </div>
        </div>
      </div>
    </div>

    <!-- Record usage form (inline modal) -->
    <div class="record-form-overlay" v-if="showRecordForm">
      <div class="record-form">
        <div class="form-header flexrow">
          <h4 class="filler">记录资产使用</h4>
          <button-simple icon="x" @click="showRecordForm = false" />
        </div>
        <div class="form-body">
          <div class="form-field">
            <label>项目</label>
            <combobox
              :options="projectOptions"
              v-model="recordForm.project_id"
            />
          </div>
          <div class="form-field">
            <label>使用类型</label>
            <combobox
              :options="usageTypeOptions"
              v-model="recordForm.usage_type"
            />
          </div>
          <div class="form-field">
            <label>使用上下文（可选）</label>
            <textarea
              class="form-textarea"
              v-model="recordForm.context"
              placeholder="描述使用场景..."
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="form-actions flexrow">
          <span class="filler"></span>
          <button-simple
            text="取消"
            @click="showRecordForm = false"
          />
          <button-simple
            text="确认"
            icon="check"
            :disabled="!recordForm.project_id || !recordForm.usage_type"
            @click="onRecordUsage"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import AssetUsageTimeline from '@/components/widgets/AssetUsageTimeline.vue'
import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import Combobox from '@/components/widgets/Combobox.vue'
import TableInfo from '@/components/widgets/TableInfo.vue'

export default {
  name: 'asset-usage-tracker',

  components: {
    AssetUsageTimeline,
    ButtonSimple,
    Combobox,
    TableInfo
  },

  props: {
    assetId: {
      type: String,
      required: true
    }
  },

  emits: ['usage-recorded', 'usage-deleted'],

  data() {
    return {
      showRecordForm: false,
      recordForm: {
        project_id: null,
        usage_type: null,
        context: ''
      },
      usageTypeOptions: [
        { label: '直接引用', value: 'reference' },
        { label: '修改复用', value: 'derivative' },
        { label: '灵感参考', value: 'inspiration' },
        { label: '素材使用', value: 'material' },
        { label: '模板使用', value: 'template' }
      ]
    }
  },

  mounted() {
    this.refresh()
  },

  computed: {
    ...mapGetters([
      'assetUsages',
      'assetUsageStats',
      'assetCrossProjectUsage',
      'assetUsagesIsLoading',
      'openProductions'
    ]),

    usages() {
      return this.assetUsages
    },

    usageStats() {
      return this.assetUsageStats
    },

    crossProject() {
      return this.assetCrossProjectUsage
    },

    isLoading() {
      return this.assetUsagesIsLoading
    },

    maxCrossProjectCount() {
      if (!this.crossProject || !this.crossProject.length) return 1
      return Math.max(...this.crossProject.map((c) => c.count), 1)
    },

    projectOptions() {
      const productions = this.openProductions || []
      return productions.map((p) => ({
        label: p.name,
        value: p.id
      }))
    }
  },

  methods: {
    ...mapActions([
      'loadAssetUsages',
      'loadAssetUsageStats',
      'loadCrossProjectUsage',
      'recordAssetUsage',
      'deleteAssetUsage'
    ]),

    refresh() {
      if (!this.assetId) return
      this.loadAssetUsages({ assetId: this.assetId })
      this.loadAssetUsageStats(this.assetId)
      this.loadCrossProjectUsage(this.assetId)
    },

    barWidth(count) {
      return Math.round((count / this.maxCrossProjectCount) * 100)
    },

    getUsageTypeLabel(type) {
      const found = this.usageTypeOptions.find((o) => o.value === type)
      return found ? found.label : type || '未知'
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    },

    async onRecordUsage() {
      if (!this.recordForm.project_id || !this.recordForm.usage_type) return
      try {
        const usage = await this.recordAssetUsage({
          assetId: this.assetId,
          data: {
            project_id: this.recordForm.project_id,
            usage_type: this.recordForm.usage_type,
            context: this.recordForm.context || undefined
          }
        })
        this.showRecordForm = false
        this.recordForm = { project_id: null, usage_type: null, context: '' }
        this.$emit('usage-recorded', usage)
        // Refresh stats after recording
        this.loadAssetUsageStats(this.assetId)
        this.loadCrossProjectUsage(this.assetId)
      } catch (err) {
        console.error('Failed to record usage:', err)
      }
    },

    async onDeleteUsage(usageId) {
      if (!confirm('确定要删除该使用记录吗？')) return
      try {
        await this.deleteAssetUsage(usageId)
        this.$emit('usage-deleted', usageId)
        this.loadAssetUsageStats(this.assetId)
        this.loadCrossProjectUsage(this.assetId)
      } catch (err) {
        console.error('Failed to delete usage:', err)
      }
    }
  },

  watch: {
    assetId() {
      this.refresh()
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-usage-tracker {
  position: relative;
}

.tracker-header {
  align-items: center;
  margin-bottom: 0.8em;

  h3 {
    font-size: 0.95em;
    font-weight: 600;
    margin: 0;
    color: var(--text-strong);
  }
}

/* Stats summary */
.usage-stats {
  gap: 1em;
  margin-bottom: 1em;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--background-alt);
  border-radius: 0.6em;
  padding: 0.6em 1em;
  flex: 1;
}

.stat-number {
  font-size: 1.4em;
  font-weight: 700;
  color: var(--text-strong);
}

.stat-label {
  font-size: 0.75em;
  color: var(--text-alt);
  margin-top: 0.15em;
}

/* Cross-project bar chart */
.cross-project-section {
  margin-bottom: 1em;

  h4 {
    font-size: 0.85em;
    font-weight: 600;
    margin: 0 0 0.5em;
    color: var(--text-strong);
  }
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 0.4em;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 0.5em;
}

.bar-label {
  width: 80px;
  font-size: 0.8em;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.bar-track {
  flex: 1;
  height: 14px;
  background: var(--background-alt);
  border-radius: 7px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--background-selected);
  border-radius: 7px;
  transition: width 0.3s ease;
  min-width: 4px;
}

.bar-count {
  font-size: 0.75em;
  color: var(--text-alt);
  width: 28px;
  text-align: right;
  flex-shrink: 0;
}

/* Usage list */
.usage-list {
  margin-top: 1em;

  h4 {
    font-size: 0.85em;
    font-weight: 600;
    margin: 0 0 0.5em;
    color: var(--text-strong);
  }
}

.empty-message {
  padding: 1.5em;
  text-align: center;
  color: var(--text-alt);
  font-size: 0.85em;
}

.usage-items {
  display: flex;
  flex-direction: column;
  gap: 0.3em;
  max-height: 300px;
  overflow-y: auto;
}

.usage-item {
  background: var(--background-alt);
  border-radius: 0.5em;
  padding: 0.5em 0.7em;
}

.usage-item-main {
  display: flex;
  align-items: center;
  gap: 0.5em;
  margin-bottom: 0.2em;
}

.usage-project {
  font-size: 0.85em;
  font-weight: 500;
  color: var(--text);
}

.usage-type-badge {
  background: var(--background);
  padding: 0.1em 0.4em;
  border-radius: 0.3em;
  font-size: 0.7em;
  color: var(--text-alt);
}

.usage-item-meta {
  display: flex;
  align-items: center;
  gap: 0.5em;
  font-size: 0.75em;
  color: var(--text-alt);
}

.usage-delete {
  margin-left: auto;
  opacity: 0.5;
  cursor: pointer;

  &:hover {
    opacity: 1;
    color: var(--error);
  }
}

.usage-context {
  font-size: 0.8em;
  color: var(--text-alt);
  margin-top: 0.3em;
  padding-top: 0.3em;
  border-top: 1px solid var(--border);
}

/* Record form overlay */
.record-form-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 2em;
  z-index: 10;
  border-radius: 0.5em;
}

.record-form {
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 0.8em;
  padding: 1em;
  width: 90%;
  max-width: 320px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.form-header {
  align-items: center;
  margin-bottom: 0.8em;

  h4 {
    font-size: 0.9em;
    font-weight: 600;
    margin: 0;
  }
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 0.7em;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.3em;

  label {
    font-size: 0.8em;
    color: var(--text-alt);
  }
}

.form-textarea {
  background: var(--background-alt);
  border: 1px solid var(--border);
  border-radius: 0.4em;
  padding: 0.5em;
  font-size: 0.85em;
  color: var(--text);
  resize: vertical;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: var(--background-selected);
  }
}

.form-actions {
  margin-top: 0.8em;
  gap: 0.5em;
}
</style>
