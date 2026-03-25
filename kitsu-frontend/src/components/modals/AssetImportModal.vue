<template>
  <div
    :class="{
      modal: true,
      'is-active': active
    }"
  >
    <div class="modal-background" @click="close"></div>
    <div class="modal-content">
      <div class="box asset-import-box">
        <h2 class="subtitle">导入资产</h2>

        <!-- Step indicator -->
        <div class="step-indicator">
          <span
            class="step"
            :class="{ active: step === 1, done: step > 1 }"
          >
            1. 上传文件
          </span>
          <span class="step-divider"></span>
          <span
            class="step"
            :class="{ active: step === 2, done: step > 2 }"
          >
            2. 预览确认
          </span>
          <span class="step-divider"></span>
          <span
            class="step"
            :class="{ active: step === 3 }"
          >
            3. 导入结果
          </span>
        </div>

        <!-- Step 1: Upload -->
        <div class="step-content" v-if="step === 1">
          <div
            class="drop-zone"
            :class="{ dragging: isDragging, 'has-file': !!selectedFile }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
            @click="triggerFileInput"
          >
            <input
              ref="file-input"
              type="file"
              accept=".zip"
              class="hidden-input"
              @change="onFileSelect"
            />
            <template v-if="!selectedFile">
              <div class="drop-icon">
                <svg
                  width="48"
                  height="48"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <p class="drop-text">拖拽 ZIP 文件到此处或点击选择</p>
              <p class="drop-hint">支持 .zip 格式，最大 500MB</p>
            </template>
            <template v-else>
              <div class="file-info">
                <span class="file-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </span>
                <span class="file-name">{{ selectedFile.name }}</span>
                <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
                <button class="remove-file" @click.stop="removeFile">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            </template>
          </div>

          <!-- Validating spinner -->
          <div class="validating-info" v-if="isValidating">
            <span class="spinner"></span>
            <span>正在验证文件...</span>
          </div>

          <!-- Validation error -->
          <p class="error-message" v-if="isError">
            {{ importProgress.message }}
          </p>
        </div>

        <!-- Step 2: Preview -->
        <div class="step-content" v-if="step === 2">
          <div class="preview-header">
            <span class="preview-badge success">验证通过</span>
            <span class="preview-count">
              共 {{ previewAssets.length }} 个资产
            </span>
          </div>

          <div class="preview-table-wrapper">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>分类</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  :key="asset.name + '-' + index"
                  v-for="(asset, index) in previewAssets"
                >
                  <td class="cell-name" :title="asset.name">{{ asset.name }}</td>
                  <td>{{ asset.category || '-' }}</td>
                  <td>
                    <span
                      class="status-dot"
                      :class="'status-' + (asset.status || 'draft')"
                    ></span>
                    {{ getStatusLabel(asset.status) }}
                  </td>
                  <td>
                    <span
                      class="action-badge"
                      :class="asset.action || 'create'"
                    >
                      {{ getActionLabel(asset.action) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="import-mode-field">
            <label class="label">导入模式</label>
            <select class="mode-select" v-model="importMode">
              <option value="merge">合并（更新已有，创建新资产）</option>
              <option value="skip">跳过（仅创建新资产）</option>
              <option value="overwrite">覆盖（替换已有资产）</option>
              <option value="create_new">全新创建（全部作为新资产）</option>
            </select>
          </div>
        </div>

        <!-- Step 3: Result -->
        <div class="step-content" v-if="step === 3">
          <template v-if="isImporting">
            <div class="importing-info">
              <span class="spinner"></span>
              <span>正在导入...</span>
            </div>
          </template>
          <template v-else-if="importResult">
            <div class="result-header">
              <span class="preview-badge success">导入完成</span>
            </div>
            <div class="result-stats">
              <div class="stat-item">
                <span class="stat-number created">{{ importResult.created || 0 }}</span>
                <span class="stat-label">新建</span>
              </div>
              <div class="stat-item">
                <span class="stat-number updated">{{ importResult.updated || 0 }}</span>
                <span class="stat-label">更新</span>
              </div>
              <div class="stat-item">
                <span class="stat-number skipped">{{ importResult.skipped || 0 }}</span>
                <span class="stat-label">跳过</span>
              </div>
              <div class="stat-item">
                <span class="stat-number errors">{{ importResult.errors || 0 }}</span>
                <span class="stat-label">错误</span>
              </div>
            </div>
            <div
              class="result-errors"
              v-if="importResult.error_details && importResult.error_details.length"
            >
              <h4>错误详情</h4>
              <ul>
                <li
                  :key="index"
                  v-for="(err, index) in importResult.error_details"
                >
                  {{ err.name || err.asset }}: {{ err.message || err.reason }}
                </li>
              </ul>
            </div>
          </template>
          <template v-else-if="isError">
            <p class="error-message">{{ importProgress.message }}</p>
          </template>
        </div>

        <!-- Footer buttons -->
        <div class="modal-footer">
          <button class="button is-link" @click="close">
            {{ step === 3 ? '关闭' : '取消' }}
          </button>
          <button
            class="button is-link"
            @click="goBack"
            v-if="step === 2"
          >
            上一步
          </button>
          <button
            class="button is-primary"
            :disabled="!canProceed"
            :class="{ 'is-loading': isValidating || isImporting }"
            @click="proceed"
            v-if="step < 3"
          >
            {{ step === 1 ? '验证并预览' : '开始导入' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'asset-import-modal',

  props: {
    active: { type: Boolean, default: false }
  },

  data() {
    return {
      step: 1,
      selectedFile: null,
      isDragging: false,
      importMode: 'merge'
    }
  },

  computed: {
    ...mapGetters([
      'assetImportProgress',
      'assetImportPreview',
      'assetImportResult'
    ]),

    importProgress() {
      return this.assetImportProgress
    },

    importPreview() {
      return this.assetImportPreview
    },

    importResult() {
      return this.assetImportResult
    },

    previewAssets() {
      if (!this.importPreview) return []
      return this.importPreview.assets || this.importPreview.data || []
    },

    isValidating() {
      return this.importProgress.status === 'validating'
    },

    isImporting() {
      return this.importProgress.status === 'importing'
    },

    isError() {
      return this.importProgress.status === 'error'
    },

    canProceed() {
      if (this.step === 1) return !!this.selectedFile && !this.isValidating
      if (this.step === 2) return !this.isImporting
      return false
    }
  },

  watch: {
    active(val) {
      if (val) {
        this.reset()
      }
    }
  },

  methods: {
    ...mapActions([
      'validateImportFile',
      'executeImport',
      'clearImportState'
    ]),

    reset() {
      this.step = 1
      this.selectedFile = null
      this.isDragging = false
      this.importMode = 'merge'
      this.clearImportState()
    },

    triggerFileInput() {
      this.$refs['file-input']?.click()
    },

    onFileSelect(e) {
      const file = e.target.files?.[0]
      if (file) this.selectedFile = file
    },

    onDrop(e) {
      this.isDragging = false
      const file = e.dataTransfer?.files?.[0]
      if (file && file.name.endsWith('.zip')) {
        this.selectedFile = file
      }
    },

    removeFile() {
      this.selectedFile = null
      if (this.$refs['file-input']) {
        this.$refs['file-input'].value = ''
      }
    },

    formatFileSize(bytes) {
      if (!bytes) return '0 B'
      const units = ['B', 'KB', 'MB', 'GB']
      let i = 0
      let size = bytes
      while (size >= 1024 && i < units.length - 1) {
        size /= 1024
        i++
      }
      return `${size.toFixed(i > 0 ? 1 : 0)} ${units[i]}`
    },

    getStatusLabel(status) {
      const labels = {
        draft: '草稿',
        approved: '已审核',
        active: '已审核',
        archived: '已归档'
      }
      return labels[status] || '草稿'
    },

    getActionLabel(action) {
      const labels = {
        create: '新建',
        update: '更新',
        skip: '跳过',
        overwrite: '覆盖'
      }
      return labels[action] || '新建'
    },

    async proceed() {
      if (this.step === 1) {
        try {
          await this.validateImportFile(this.selectedFile)
          this.step = 2
        } catch {
          // Error state handled in store
        }
      } else if (this.step === 2) {
        this.step = 3
        try {
          await this.executeImport({
            file: this.selectedFile,
            mode: this.importMode
          })
        } catch {
          // Error state handled in store
        }
      }
    },

    goBack() {
      if (this.step > 1) {
        this.step--
      }
    },

    close() {
      this.clearImportState()
      this.$emit('close')
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-import-box {
  max-width: 600px;
  margin: 0 auto;
}

.subtitle {
  font-size: 1.15em;
  font-weight: 600;
  margin-bottom: 1.2em;
  color: var(--text-strong);
}

.label {
  font-size: 0.9em;
  font-weight: 600;
  color: var(--text-strong);
  margin-bottom: 0.5em;
  display: block;
}

/* Step indicator */
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.8em;
  margin-bottom: 1.5em;
  padding-bottom: 1em;
  border-bottom: 1px solid var(--border);
}

.step {
  font-size: 0.85em;
  color: var(--text-alt);
  padding: 0.3em 0.7em;
  border-radius: 1em;
  transition: color 0.15s, background 0.15s;

  &.active {
    color: var(--text-strong);
    font-weight: 600;
    background: var(--background-selectable);
  }

  &.done {
    color: #00b242;
  }
}

.step-divider {
  width: 24px;
  height: 1px;
  background: var(--border);
}

/* Drop zone */
.drop-zone {
  border: 2px dashed var(--border);
  border-radius: 0.8em;
  padding: 2.5em 1.5em;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  background: var(--background);

  &:hover,
  &.dragging {
    border-color: var(--background-selected);
    background: var(--background-selectable);
  }

  &.has-file {
    border-style: solid;
    border-color: var(--background-selected);
    padding: 1.2em 1.5em;
  }
}

.hidden-input {
  display: none;
}

.drop-icon {
  color: var(--text-alt);
  margin-bottom: 0.8em;
}

.drop-text {
  font-size: 0.95em;
  color: var(--text);
  margin-bottom: 0.3em;
}

.drop-hint {
  font-size: 0.8em;
  color: var(--text-alt);
}

/* File info */
.file-info {
  display: flex;
  align-items: center;
  gap: 0.6em;
}

.file-icon {
  color: var(--text-alt);
  flex-shrink: 0;
}

.file-name {
  font-weight: 500;
  font-size: 0.9em;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.file-size {
  font-size: 0.8em;
  color: var(--text-alt);
  flex-shrink: 0;
}

.remove-file {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-alt);
  padding: 0.2em;
  border-radius: 0.3em;
  flex-shrink: 0;

  &:hover {
    color: var(--error);
    background: var(--background-hover);
  }
}

/* Validating / Importing spinners */
.validating-info,
.importing-info {
  display: flex;
  align-items: center;
  gap: 0.6em;
  margin-top: 1em;
  font-size: 0.9em;
  color: var(--text-alt);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--background-selected);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  color: var(--error);
  font-size: 0.85em;
  margin-top: 0.8em;
}

/* Preview */
.preview-header {
  display: flex;
  align-items: center;
  gap: 0.8em;
  margin-bottom: 1em;
}

.preview-badge {
  padding: 0.2em 0.6em;
  border-radius: 0.4em;
  font-size: 0.8em;
  font-weight: 600;

  &.success {
    background: rgba(0, 178, 66, 0.15);
    color: #00b242;
  }
}

.preview-count {
  font-size: 0.85em;
  color: var(--text-alt);
}

.preview-table-wrapper {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 0.5em;
  margin-bottom: 1em;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85em;

  th {
    background: var(--background-alt);
    font-weight: 600;
    color: var(--text-strong);
    padding: 0.6em 0.8em;
    text-align: left;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  td {
    padding: 0.5em 0.8em;
    border-top: 1px solid var(--border);
    color: var(--text);
  }

  tr:hover td {
    background: var(--background-hover);
  }
}

.cell-name {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 0.3em;
  vertical-align: middle;

  &.status-draft {
    background: #999;
  }

  &.status-approved,
  &.status-active {
    background: #00b242;
  }

  &.status-archived {
    background: #f57f77;
  }
}

.action-badge {
  padding: 0.15em 0.5em;
  border-radius: 0.3em;
  font-size: 0.85em;
  font-weight: 500;

  &.create {
    background: rgba(0, 178, 66, 0.15);
    color: #00b242;
  }

  &.update {
    background: rgba(59, 130, 246, 0.15);
    color: #3b82f6;
  }

  &.skip {
    background: var(--background-alt);
    color: var(--text-alt);
  }

  &.overwrite {
    background: rgba(245, 127, 119, 0.15);
    color: #f57f77;
  }
}

/* Import mode */
.import-mode-field {
  margin-top: 0.5em;
}

.mode-select {
  width: 100%;
  padding: 0.6em 0.8em;
  border: 1px solid var(--border);
  border-radius: 0.5em;
  background: var(--background);
  color: var(--text);
  font-size: 0.9em;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: var(--background-selected);
  }
}

/* Result stats */
.result-header {
  margin-bottom: 1em;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1em;
  margin-bottom: 1em;
}

.stat-item {
  text-align: center;
  padding: 1em 0.5em;
  border-radius: 0.5em;
  background: var(--background);
  border: 1px solid var(--border);
}

.stat-number {
  display: block;
  font-size: 1.5em;
  font-weight: 700;
  margin-bottom: 0.2em;

  &.created {
    color: #00b242;
  }

  &.updated {
    color: #3b82f6;
  }

  &.skipped {
    color: var(--text-alt);
  }

  &.errors {
    color: var(--error);
  }
}

.stat-label {
  font-size: 0.8em;
  color: var(--text-alt);
}

/* Error details */
.result-errors {
  margin-top: 1em;

  h4 {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--error);
    margin-bottom: 0.5em;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  li {
    font-size: 0.85em;
    color: var(--text);
    padding: 0.3em 0;
    border-bottom: 1px solid var(--border);

    &:last-child {
      border-bottom: none;
    }
  }
}

/* Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.8em;
  margin-top: 1.5em;
  padding-top: 1em;
  border-top: 1px solid var(--border);
}
</style>
