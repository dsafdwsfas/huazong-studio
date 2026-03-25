<template>
  <div class="template-library-overlay" v-if="active" @click.self="$emit('close')">
    <div class="template-library">
      <div class="library-header">
        <h3>风格模板库</h3>
        <button class="btn-close" @click="$emit('close')">
          <XIcon :size="16" />
        </button>
      </div>

      <!-- Save current style as template -->
      <div class="library-section" v-if="currentStyle">
        <div class="section-label">保存当前风格为模板</div>
        <div class="save-form">
          <input
            v-model="newName"
            class="input-name"
            placeholder="模板名称..."
            @keyup.enter="onSaveTemplate"
          />
          <input
            v-model="newDescription"
            class="input-desc"
            placeholder="简要描述（可选）"
          />
          <div class="save-row">
            <input
              v-model="newTags"
              class="input-tags"
              placeholder="标签（逗号分隔）"
            />
            <label class="share-check">
              <input type="checkbox" v-model="newIsShared" />
              <span>共享给其他项目</span>
            </label>
            <button class="btn-save" @click="onSaveTemplate" :disabled="!newName.trim()">
              <SaveIcon :size="14" />
              保存
            </button>
          </div>
        </div>
      </div>

      <!-- Template list -->
      <div class="library-section">
        <div class="section-label">
          项目模板
          <span class="count" v-if="projectTemplates.length">({{ projectTemplates.length }})</span>
        </div>
        <div v-if="isLoading" class="loading-state">
          <div class="spinner" />
        </div>
        <div v-else-if="projectTemplates.length === 0" class="empty-state">
          暂无模板，锁定风格后可保存为模板
        </div>
        <div v-else class="template-grid">
          <div
            v-for="tpl in projectTemplates"
            :key="tpl.id"
            class="template-card"
          >
            <div class="card-preview">
              <img
                v-if="tpl.thumbnail_url"
                :src="tpl.thumbnail_url"
                :alt="tpl.name"
              />
              <div v-else class="empty-preview">
                <PaletteIcon :size="20" />
              </div>
            </div>
            <div class="card-info">
              <div class="card-name">{{ tpl.name }}</div>
              <div class="card-desc" v-if="tpl.description">{{ tpl.description }}</div>
              <div class="card-tags" v-if="tpl.tags && tpl.tags.length">
                <span
                  v-for="tag in tpl.tags"
                  :key="tag"
                  class="tag"
                >{{ tag }}</span>
              </div>
              <div class="card-meta">
                <span>{{ tpl.created_by_name }}</span>
                <span v-if="tpl.is_shared" class="shared-badge">已共享</span>
              </div>
            </div>
            <div class="card-actions">
              <button
                class="btn-apply"
                title="应用此模板"
                @click="onApply(tpl)"
              >
                应用
              </button>
              <button
                class="btn-delete"
                title="删除"
                @click="onDelete(tpl)"
              >
                <Trash2Icon :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Shared templates from other projects -->
      <div class="library-section" v-if="sharedTemplates.length">
        <div class="section-label">
          共享模板
          <span class="count">({{ sharedTemplates.length }})</span>
        </div>
        <div class="template-grid">
          <div
            v-for="tpl in sharedTemplates"
            :key="tpl.id"
            class="template-card template-shared"
          >
            <div class="card-preview">
              <img
                v-if="tpl.thumbnail_url"
                :src="tpl.thumbnail_url"
                :alt="tpl.name"
              />
              <div v-else class="empty-preview">
                <PaletteIcon :size="20" />
              </div>
            </div>
            <div class="card-info">
              <div class="card-name">{{ tpl.name }}</div>
              <div class="card-desc" v-if="tpl.description">{{ tpl.description }}</div>
              <div class="card-meta">
                <span>来自: {{ tpl.project_name }}</span>
              </div>
            </div>
            <div class="card-actions">
              <button class="btn-apply" @click="onApply(tpl)">应用</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import {
  PaletteIcon,
  SaveIcon,
  Trash2Icon,
  XIcon
} from 'lucide-vue-next'

export default {
  name: 'StyleTemplateLibrary',

  components: {
    PaletteIcon,
    SaveIcon,
    Trash2Icon,
    XIcon
  },

  props: {
    active: { type: Boolean, default: false },
    projectId: { type: String, required: true },
    currentStyle: { type: Object, default: null }
  },

  emits: ['close', 'apply', 'saved'],

  data() {
    return {
      isLoading: false,
      projectTemplates: [],
      sharedTemplates: [],
      newName: '',
      newDescription: '',
      newTags: '',
      newIsShared: false
    }
  },

  watch: {
    active(val) {
      if (val) this.loadTemplates()
    }
  },

  methods: {
    ...mapActions([
      'listStyleTemplates',
      'createStyleTemplate',
      'deleteStyleTemplate',
      'applyStyleTemplate'
    ]),

    async loadTemplates() {
      this.isLoading = true
      try {
        const data = await this.listStyleTemplates({ projectId: this.projectId })
        this.projectTemplates = data.templates || []
        this.sharedTemplates = data.shared_templates || []
      } catch (err) {
        console.error('Failed to load templates:', err)
      } finally {
        this.isLoading = false
      }
    },

    async onSaveTemplate() {
      if (!this.newName.trim() || !this.currentStyle) return
      try {
        await this.createStyleTemplate({
          projectId: this.projectId,
          name: this.newName.trim(),
          description: this.newDescription.trim(),
          style: this.currentStyle,
          tags: this.newTags ? this.newTags.split(',').map(t => t.trim()).filter(Boolean) : [],
          isShared: this.newIsShared
        })
        this.newName = ''
        this.newDescription = ''
        this.newTags = ''
        this.newIsShared = false
        await this.loadTemplates()
        this.$emit('saved')
      } catch (err) {
        console.error('Failed to save template:', err)
      }
    },

    async onApply(tpl) {
      if (!confirm(`应用模板 "${tpl.name}" 将覆盖当前项目风格锁定，确定？`)) return
      try {
        await this.applyStyleTemplate({
          projectId: this.projectId,
          templateId: tpl.id
        })
        this.$emit('apply', tpl)
        this.$emit('close')
      } catch (err) {
        console.error('Failed to apply template:', err)
      }
    },

    async onDelete(tpl) {
      if (!confirm(`确定删除模板 "${tpl.name}"？`)) return
      try {
        await this.deleteStyleTemplate({
          projectId: this.projectId,
          templateId: tpl.id
        })
        await this.loadTemplates()
      } catch (err) {
        console.error('Failed to delete template:', err)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.template-library-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.template-library {
  width: 720px;
  max-height: 80vh;
  background: var(--background);
  border-radius: 12px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);

  h3 {
    margin: 0;
    font-size: 1rem;
  }

  .btn-close {
    background: none;
    border: none;
    color: var(--text-alt);
    cursor: pointer;
    padding: 4px;

    &:hover { color: var(--text); }
  }
}

.library-section {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  overflow-y: auto;

  &:last-child { border-bottom: none; }
}

.section-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-alt);
  margin-bottom: 0.75rem;

  .count {
    font-weight: 400;
    color: var(--text-alt);
    opacity: 0.7;
  }
}

.save-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-name,
.input-desc,
.input-tags {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--background);
  color: var(--text);
  font-size: 0.8rem;

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }
}

.save-row {
  display: flex;
  align-items: center;
  gap: 8px;

  .input-tags { flex: 1; }
}

.share-check {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: var(--text-alt);
  cursor: pointer;
  white-space: nowrap;

  input { cursor: pointer; }
}

.btn-save {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  background: var(--color-primary);
  color: #fff;
  font-size: 0.8rem;
  cursor: pointer;
  white-space: nowrap;

  &:disabled { opacity: 0.5; cursor: not-allowed; }
  &:hover:not(:disabled) { filter: brightness(1.1); }
}

.loading-state {
  text-align: center;
  padding: 2rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  color: var(--text-alt);
  font-size: 0.8rem;
  padding: 1.5rem;
}

.template-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.template-card {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--background);
  transition: border-color 0.15s;

  &:hover { border-color: var(--color-primary); }
}

.template-shared {
  border-style: dashed;
}

.card-preview {
  width: 80px;
  min-height: 80px;
  flex-shrink: 0;
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.empty-preview {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-alt, #2a2a2a);
  color: var(--text-alt);
}

.card-info {
  flex: 1;
  padding: 8px 10px;
  min-width: 0;
}

.card-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-desc {
  font-size: 0.7rem;
  color: var(--text-alt);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 4px;
}

.tag {
  padding: 1px 6px;
  border-radius: 8px;
  background: var(--background-alt, #2a2a2a);
  font-size: 0.6rem;
  color: var(--text-alt);
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 0.65rem;
  color: var(--text-alt);
}

.shared-badge {
  padding: 1px 5px;
  border-radius: 6px;
  background: rgba(16, 172, 132, 0.15);
  color: #10ac84;
  font-size: 0.6rem;
}

.card-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  padding: 8px;
}

.btn-apply {
  padding: 4px 10px;
  border: 1px solid var(--color-primary);
  border-radius: 4px;
  background: transparent;
  color: var(--color-primary);
  font-size: 0.7rem;
  cursor: pointer;

  &:hover {
    background: var(--color-primary);
    color: #fff;
  }
}

.btn-delete {
  padding: 4px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-alt);
  cursor: pointer;

  &:hover {
    background: rgba(255, 56, 96, 0.1);
    color: #ff3860;
  }
}
</style>
