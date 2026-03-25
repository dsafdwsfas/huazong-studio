<template>
  <div
    :class="{
      modal: true,
      'is-active': active
    }"
  >
    <div class="modal-background" @click="close"></div>
    <div class="modal-content">
      <div class="box asset-export-box">
        <h2 class="subtitle">导出资产</h2>

        <!-- Export scope -->
        <div class="field">
          <label class="label">导出范围</label>
          <div class="scope-options">
            <label
              class="scope-option"
              :class="{ active: scope === 'selected' }"
              v-if="selectedCount > 0"
            >
              <input
                type="radio"
                name="export-scope"
                value="selected"
                v-model="scope"
              />
              <span class="scope-radio"></span>
              <span>选中的 {{ selectedCount }} 个资产</span>
            </label>
            <label
              class="scope-option"
              :class="{ active: scope === 'category' }"
              v-if="categoryId"
            >
              <input
                type="radio"
                name="export-scope"
                value="category"
                v-model="scope"
              />
              <span class="scope-radio"></span>
              <span>当前分类的所有资产</span>
            </label>
            <label
              class="scope-option"
              :class="{ active: scope === 'all' }"
            >
              <input
                type="radio"
                name="export-scope"
                value="all"
                v-model="scope"
              />
              <span class="scope-radio"></span>
              <span>全部资产</span>
            </label>
          </div>
        </div>

        <!-- Export options -->
        <div class="field">
          <label class="label">导出选项</label>
          <div class="export-options">
            <label class="checkbox-option">
              <input type="checkbox" v-model="options.includeFiles" />
              <span class="checkbox-mark"></span>
              <span>包含关联文件</span>
            </label>
            <label class="checkbox-option">
              <input type="checkbox" v-model="options.includeVersions" />
              <span class="checkbox-mark"></span>
              <span>包含版本历史</span>
            </label>
          </div>
        </div>

        <!-- Progress bar -->
        <div class="export-progress" v-if="isExporting || isDone || isError">
          <div class="progress-bar-wrapper">
            <div
              class="progress-bar"
              :class="{
                exporting: isExporting,
                done: isDone,
                error: isError
              }"
              :style="{ width: progressWidth }"
            ></div>
          </div>
          <p class="progress-message" :class="{ error: isError }">
            {{ exportProgress.message }}
          </p>
        </div>

        <!-- Error detail -->
        <p class="error-message" v-if="isError">
          {{ exportProgress.message }}
        </p>

        <!-- Buttons -->
        <div class="modal-footer">
          <button class="button is-link" @click="close">
            取消
          </button>
          <button
            class="button is-primary"
            :class="{ 'is-loading': isExporting }"
            :disabled="isExporting"
            @click="startExport"
          >
            {{ isDone ? '重新导出' : '开始导出' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'asset-export-modal',

  props: {
    active: { type: Boolean, default: false },
    selectedAssetIds: { type: Array, default: () => [] },
    categoryId: { type: String, default: null }
  },

  data() {
    return {
      scope: this.selectedAssetIds.length > 0 ? 'selected' : 'all',
      options: {
        includeFiles: false,
        includeVersions: false
      }
    }
  },

  computed: {
    ...mapGetters(['assetExportProgress']),

    exportProgress() {
      return this.assetExportProgress
    },

    selectedCount() {
      return this.selectedAssetIds.length
    },

    isExporting() {
      return this.exportProgress.status === 'exporting'
    },

    isDone() {
      return this.exportProgress.status === 'done'
    },

    isError() {
      return this.exportProgress.status === 'error'
    },

    progressWidth() {
      if (this.isExporting) return '80%'
      if (this.isDone) return '100%'
      if (this.isError) return '100%'
      return '0%'
    }
  },

  watch: {
    active(val) {
      if (val) {
        this.scope =
          this.selectedAssetIds.length > 0 ? 'selected' : this.categoryId ? 'category' : 'all'
        this.clearExportState()
      }
    },
    selectedAssetIds(val) {
      if (val.length > 0 && this.scope !== 'selected') {
        this.scope = 'selected'
      }
    }
  },

  methods: {
    ...mapActions([
      'exportSelectedAssets',
      'exportAllAssets',
      'exportByCategory',
      'clearExportState'
    ]),

    buildOptions() {
      return {
        include_files: this.options.includeFiles,
        include_versions: this.options.includeVersions
      }
    },

    async startExport() {
      try {
        const opts = this.buildOptions()
        if (this.scope === 'selected') {
          await this.exportSelectedAssets({
            assetIds: this.selectedAssetIds,
            options: opts
          })
        } else if (this.scope === 'category') {
          await this.exportByCategory({
            categoryId: this.categoryId,
            options: opts
          })
        } else {
          await this.exportAllAssets(opts)
        }
      } catch {
        // Error state is managed in store
      }
    },

    close() {
      this.clearExportState()
      this.$emit('close')
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-export-box {
  max-width: 520px;
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

/* Scope radio options */
.scope-options {
  display: flex;
  flex-direction: column;
  gap: 0.5em;
}

.scope-option {
  display: flex;
  align-items: center;
  gap: 0.6em;
  padding: 0.6em 0.8em;
  border-radius: 0.5em;
  border: 1px solid var(--border);
  cursor: pointer;
  font-size: 0.9em;
  color: var(--text);
  transition: border-color 0.15s, background 0.15s;

  input[type='radio'] {
    display: none;
  }

  &:hover {
    background: var(--background-hover);
  }

  &.active {
    border-color: var(--background-selected);
    background: var(--background-selectable);
  }
}

.scope-radio {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid var(--text-alt);
  flex-shrink: 0;
  position: relative;

  .scope-option.active & {
    border-color: var(--background-selected);

    &::after {
      content: '';
      position: absolute;
      top: 3px;
      left: 3px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--background-selected);
    }
  }
}

/* Checkbox options */
.export-options {
  display: flex;
  flex-direction: column;
  gap: 0.5em;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.6em;
  cursor: pointer;
  font-size: 0.9em;
  color: var(--text);

  input[type='checkbox'] {
    display: none;
  }
}

.checkbox-mark {
  width: 16px;
  height: 16px;
  border: 2px solid var(--text-alt);
  border-radius: 3px;
  flex-shrink: 0;
  position: relative;
  transition: border-color 0.15s, background 0.15s;

  input:checked + & {
    border-color: var(--background-selected);
    background: var(--background-selected);

    &::after {
      content: '';
      position: absolute;
      top: 1px;
      left: 4px;
      width: 4px;
      height: 8px;
      border: solid #fff;
      border-width: 0 2px 2px 0;
      transform: rotate(45deg);
    }
  }
}

/* Progress bar */
.export-progress {
  margin-top: 1.2em;
}

.progress-bar-wrapper {
  height: 8px;
  background: var(--background-alt);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;

  &.exporting {
    background: var(--background-selected);
    animation: pulse-bar 1.5s ease-in-out infinite;
  }

  &.done {
    background: #00b242;
  }

  &.error {
    background: var(--error);
  }
}

@keyframes pulse-bar {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.progress-message {
  font-size: 0.85em;
  color: var(--text-alt);
  margin-top: 0.4em;

  &.error {
    color: var(--error);
  }
}

.error-message {
  color: var(--error);
  font-size: 0.85em;
  margin-top: 0.5em;
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
