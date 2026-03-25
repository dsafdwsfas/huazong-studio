<template>
  <div class="prompt-library" v-if="active">
    <div class="library-header">
      <h3>提示词库</h3>
      <div class="header-actions">
        <button class="btn-create" @click="showCreateForm = true">
          <PlusIcon :size="14" />
          新建提示词
        </button>
        <button class="btn-close" @click="$emit('close')">
          <XIcon :size="16" />
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="library-filters">
      <div class="filter-categories">
        <button
          v-for="cat in categoryOptions"
          :key="cat.value"
          class="cat-btn"
          :class="{ active: filterCategory === cat.value }"
          @click="filterCategory = cat.value"
        >
          {{ cat.label }}
          <span class="cat-count" v-if="categoryCounts[cat.value]">{{ categoryCounts[cat.value] }}</span>
        </button>
      </div>
      <div class="filter-search">
        <SearchIcon :size="14" />
        <input
          v-model="searchQuery"
          placeholder="搜索提示词..."
          @input="onSearch"
        />
      </div>
    </div>

    <!-- Create/Edit form -->
    <div class="prompt-form" v-if="showCreateForm || editingPrompt">
      <div class="form-header">
        <h4>{{ editingPrompt ? '编辑提示词' : '新建提示词' }}</h4>
        <button class="btn-close-sm" @click="closeForm">
          <XIcon :size="14" />
        </button>
      </div>
      <input
        v-model="formTitle"
        class="form-input"
        placeholder="标题"
      />
      <textarea
        v-model="formContent"
        class="form-textarea"
        placeholder="英文提示词内容..."
        rows="3"
      />
      <textarea
        v-model="formContentCn"
        class="form-textarea"
        placeholder="中文提示词（可选）"
        rows="2"
      />
      <div class="form-row">
        <select v-model="formCategory" class="form-select">
          <option v-for="cat in categoryOptions.slice(1)" :key="cat.value" :value="cat.value">
            {{ cat.label }}
          </option>
        </select>
        <input v-model="formTags" class="form-input" placeholder="标签（逗号分隔）" />
      </div>
      <div class="form-actions">
        <button class="btn-cancel" @click="closeForm">取消</button>
        <button class="btn-submit" @click="onSubmitForm" :disabled="!formTitle.trim() || !formContent.trim()">
          {{ editingPrompt ? '保存' : '创建' }}
        </button>
      </div>
    </div>

    <!-- Prompt list -->
    <div class="prompt-list" v-if="!isLoading">
      <div
        v-for="prompt in filteredPrompts"
        :key="prompt.id"
        class="prompt-card"
        :class="{ favorite: prompt.is_favorite }"
      >
        <div class="card-header">
          <span class="card-category" :class="'cat-' + prompt.category">
            {{ categoryLabel(prompt.category) }}
          </span>
          <span class="card-title">{{ prompt.title }}</span>
          <button
            class="btn-fav"
            :class="{ active: prompt.is_favorite }"
            @click="onToggleFavorite(prompt)"
            title="收藏"
          >
            <StarIcon :size="14" />
          </button>
        </div>
        <div class="card-content">
          <p class="content-en">{{ prompt.content }}</p>
          <p class="content-cn" v-if="prompt.content_cn">{{ prompt.content_cn }}</p>
        </div>
        <div class="card-tags" v-if="prompt.tags && prompt.tags.length">
          <span v-for="tag in prompt.tags" :key="tag" class="tag" @click="filterByTag(tag)">
            {{ tag }}
          </span>
        </div>
        <div class="card-footer">
          <span class="meta">v{{ prompt.version }} · {{ prompt.created_by_name }}</span>
          <span class="meta" v-if="prompt.usage_count">使用 {{ prompt.usage_count }} 次</span>
          <div class="card-actions">
            <button class="btn-sm" @click="onCopy(prompt)" title="复制">
              <CopyIcon :size="12" />
            </button>
            <button class="btn-sm" @click="onEdit(prompt)" title="编辑">
              <PencilIcon :size="12" />
            </button>
            <button class="btn-sm" @click="onShowVersions(prompt)" title="版本历史">
              <HistoryIcon :size="12" />
            </button>
            <button class="btn-sm btn-danger" @click="onDelete(prompt)" title="删除">
              <Trash2Icon :size="12" />
            </button>
          </div>
        </div>
      </div>
      <div v-if="filteredPrompts.length === 0" class="empty-state">
        {{ searchQuery ? '没有匹配的提示词' : '暂无提示词，点击右上角创建' }}
      </div>
    </div>
    <div v-else class="loading-state"><div class="spinner" /></div>

    <!-- Version history modal -->
    <div class="version-overlay" v-if="showVersions" @click.self="showVersions = false">
      <div class="version-modal">
        <div class="modal-header">
          <h4>版本历史 — {{ versionPromptTitle }}</h4>
          <button class="btn-close-sm" @click="showVersions = false">
            <XIcon :size="14" />
          </button>
        </div>
        <div class="version-list">
          <div
            v-for="ver in versionList"
            :key="ver.version"
            class="version-item"
          >
            <div class="ver-header">
              <span class="ver-num">v{{ ver.version }}</span>
              <span class="ver-date">{{ ver.created_at }}</span>
              <span class="ver-by">{{ ver.created_by_name || '' }}</span>
              <button class="btn-sm" @click="onRevert(ver.version)" title="回滚到此版本">
                回滚
              </button>
            </div>
            <p class="ver-content">{{ ver.content }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import {
  CopyIcon,
  HistoryIcon,
  PencilIcon,
  PlusIcon,
  SearchIcon,
  StarIcon,
  Trash2Icon,
  XIcon
} from 'lucide-vue-next'

const CATEGORIES = [
  { value: '', label: '全部' },
  { value: 'scene', label: '场景' },
  { value: 'character', label: '人物' },
  { value: 'prop', label: '道具' },
  { value: 'effect', label: '特效' },
  { value: 'style', label: '风格' },
  { value: 'other', label: '其他' }
]

export default {
  name: 'PromptLibrary',

  components: {
    CopyIcon, HistoryIcon, PencilIcon, PlusIcon,
    SearchIcon, StarIcon, Trash2Icon, XIcon
  },

  props: {
    active: { type: Boolean, default: false },
    projectId: { type: String, required: true }
  },

  emits: ['close'],

  data() {
    return {
      isLoading: false,
      prompts: [],
      categoryCounts: {},
      filterCategory: '',
      searchQuery: '',
      showCreateForm: false,
      editingPrompt: null,
      formTitle: '',
      formContent: '',
      formContentCn: '',
      formCategory: 'other',
      formTags: '',
      showVersions: false,
      versionPromptId: null,
      versionPromptTitle: '',
      versionList: [],
      categoryOptions: CATEGORIES
    }
  },

  computed: {
    filteredPrompts() {
      let list = this.prompts
      if (this.filterCategory) {
        list = list.filter(p => p.category === this.filterCategory)
      }
      if (this.searchQuery) {
        const q = this.searchQuery.toLowerCase()
        list = list.filter(p =>
          p.title.toLowerCase().includes(q) ||
          (p.content || '').toLowerCase().includes(q) ||
          (p.content_cn || '').toLowerCase().includes(q)
        )
      }
      return list
    }
  },

  watch: {
    active(val) {
      if (val) this.loadData()
    }
  },

  methods: {
    ...mapActions([
      'listPrompts', 'createPrompt', 'updatePrompt',
      'deletePrompt', 'getPromptDetail', 'togglePromptFavorite', 'revertPrompt'
    ]),

    categoryLabel(cat) {
      const found = CATEGORIES.find(c => c.value === cat)
      return found ? found.label : cat
    },

    async loadData() {
      this.isLoading = true
      try {
        const data = await this.listPrompts({ projectId: this.projectId })
        this.prompts = data.prompts || []
        this.categoryCounts = data.categories || {}
      } catch (err) {
        console.error('Failed to load prompts:', err)
      } finally {
        this.isLoading = false
      }
    },

    onSearch() { /* reactive via computed */ },

    filterByTag(tag) {
      this.searchQuery = tag
    },

    closeForm() {
      this.showCreateForm = false
      this.editingPrompt = null
      this.formTitle = ''
      this.formContent = ''
      this.formContentCn = ''
      this.formCategory = 'other'
      this.formTags = ''
    },

    onEdit(prompt) {
      this.editingPrompt = prompt
      this.formTitle = prompt.title
      this.formContent = prompt.content
      this.formContentCn = prompt.content_cn || ''
      this.formCategory = prompt.category || 'other'
      this.formTags = (prompt.tags || []).join(', ')
      this.showCreateForm = false
    },

    async onSubmitForm() {
      const tags = this.formTags ? this.formTags.split(',').map(t => t.trim()).filter(Boolean) : []
      try {
        if (this.editingPrompt) {
          await this.updatePrompt({
            projectId: this.projectId,
            promptId: this.editingPrompt.id,
            title: this.formTitle.trim(),
            content: this.formContent.trim(),
            contentCn: this.formContentCn.trim(),
            category: this.formCategory,
            tags
          })
        } else {
          await this.createPrompt({
            projectId: this.projectId,
            title: this.formTitle.trim(),
            content: this.formContent.trim(),
            contentCn: this.formContentCn.trim(),
            category: this.formCategory,
            tags
          })
        }
        this.closeForm()
        await this.loadData()
      } catch (err) {
        console.error('Failed to save prompt:', err)
      }
    },

    async onDelete(prompt) {
      if (!confirm(`确定删除提示词 "${prompt.title}"？`)) return
      try {
        await this.deletePrompt({ projectId: this.projectId, promptId: prompt.id })
        await this.loadData()
      } catch (err) {
        console.error('Failed to delete:', err)
      }
    },

    async onToggleFavorite(prompt) {
      try {
        await this.togglePromptFavorite({ projectId: this.projectId, promptId: prompt.id })
        prompt.is_favorite = !prompt.is_favorite
      } catch (err) {
        console.error('Failed to toggle favorite:', err)
      }
    },

    onCopy(prompt) {
      const text = prompt.content_cn || prompt.content
      navigator.clipboard.writeText(text).catch(() => {})
    },

    async onShowVersions(prompt) {
      this.versionPromptId = prompt.id
      this.versionPromptTitle = prompt.title
      try {
        const data = await this.getPromptDetail({
          projectId: this.projectId,
          promptId: prompt.id
        })
        this.versionList = data.versions || []
        this.showVersions = true
      } catch (err) {
        console.error('Failed to load versions:', err)
      }
    },

    async onRevert(version) {
      if (!confirm(`回滚到 v${version}？`)) return
      try {
        await this.revertPrompt({
          projectId: this.projectId,
          promptId: this.versionPromptId,
          version
        })
        this.showVersions = false
        await this.loadData()
      } catch (err) {
        console.error('Failed to revert:', err)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.prompt-library {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
}

.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);

  h3 { margin: 0; font-size: 1rem; }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: none;
  border-radius: 6px;
  background: var(--color-primary);
  color: #fff;
  font-size: 0.8rem;
  cursor: pointer;
  &:hover { filter: brightness(1.1); }
}

.btn-close {
  background: none;
  border: none;
  color: var(--text-alt);
  cursor: pointer;
  padding: 4px;
  &:hover { color: var(--text); }
}

.library-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--border);
}

.filter-categories {
  display: flex;
  gap: 4px;
}

.cat-btn {
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: transparent;
  color: var(--text-alt);
  font-size: 0.75rem;
  cursor: pointer;

  &.active {
    background: var(--color-primary);
    color: #fff;
    border-color: var(--color-primary);
  }
}

.cat-count {
  font-size: 0.65rem;
  opacity: 0.7;
  margin-left: 2px;
}

.filter-search {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-alt);

  input {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--text);
    font-size: 0.8rem;
    outline: none;
  }
}

.prompt-form {
  padding: 1rem;
  border-bottom: 1px solid var(--border);
  background: var(--background-alt, rgba(255,255,255,0.02));
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  h4 { margin: 0; font-size: 0.9rem; }
}

.btn-close-sm {
  background: none;
  border: none;
  color: var(--text-alt);
  cursor: pointer;
  &:hover { color: var(--text); }
}

.form-input, .form-textarea, .form-select {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--background);
  color: var(--text);
  font-size: 0.8rem;
  margin-bottom: 6px;
  &:focus { outline: none; border-color: var(--color-primary); }
}

.form-textarea { resize: vertical; font-family: monospace; }
.form-row { display: flex; gap: 8px; }
.form-select { width: auto; }

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.btn-cancel {
  padding: 5px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  cursor: pointer;
}

.btn-submit {
  padding: 5px 14px;
  border: none;
  border-radius: 6px;
  background: var(--color-primary);
  color: #fff;
  cursor: pointer;
  &:disabled { opacity: 0.5; }
}

.prompt-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 1rem;
}

.prompt-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  transition: border-color 0.15s;

  &:hover { border-color: var(--color-primary); }
  &.favorite { border-left: 3px solid #ffd32a; }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-category {
  padding: 1px 6px;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 600;

  &.cat-scene { background: rgba(10, 189, 227, 0.15); color: #0abde3; }
  &.cat-character { background: rgba(255, 56, 96, 0.15); color: #ff3860; }
  &.cat-prop { background: rgba(16, 172, 132, 0.15); color: #10ac84; }
  &.cat-effect { background: rgba(255, 159, 67, 0.15); color: #ff9f43; }
  &.cat-style { background: rgba(156, 39, 176, 0.15); color: #9c27b0; }
  &.cat-other { background: rgba(128, 128, 128, 0.15); color: #888; }
}

.card-title {
  flex: 1;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text);
}

.btn-fav {
  background: none;
  border: none;
  color: var(--text-alt);
  cursor: pointer;
  padding: 2px;
  opacity: 0.4;
  &.active { color: #ffd32a; opacity: 1; }
  &:hover { opacity: 1; }
}

.card-content {
  margin: 6px 0;
}

.content-en {
  font-size: 0.8rem;
  color: var(--text);
  font-family: monospace;
  line-height: 1.4;
  margin: 0 0 4px;
  white-space: pre-wrap;
  word-break: break-all;
}

.content-cn {
  font-size: 0.75rem;
  color: var(--text-alt);
  margin: 0;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 6px 0;
}

.tag {
  padding: 1px 6px;
  border-radius: 8px;
  background: var(--background-alt, #2a2a2a);
  font-size: 0.65rem;
  color: var(--text-alt);
  cursor: pointer;
  &:hover { color: var(--color-primary); }
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.65rem;
  color: var(--text-alt);
}

.card-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.btn-sm {
  background: none;
  border: none;
  color: var(--text-alt);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  &:hover { background: var(--background-alt); color: var(--text); }
}

.btn-danger:hover { color: #ff3860; }

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-alt);
  font-size: 0.85rem;
}

.loading-state {
  text-align: center;
  padding: 3rem;
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

@keyframes spin { to { transform: rotate(360deg); } }

// Version history modal
.version-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
}

.version-modal {
  width: 560px;
  max-height: 60vh;
  background: var(--background);
  border-radius: 12px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  h4 { margin: 0; font-size: 0.9rem; }
}

.version-list {
  overflow-y: auto;
  padding: 0.75rem 1rem;
}

.version-item {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 6px;
}

.ver-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  margin-bottom: 4px;
}

.ver-num { font-weight: 600; color: var(--color-primary); }
.ver-date { color: var(--text-alt); }
.ver-by { color: var(--text-alt); }

.ver-content {
  font-size: 0.75rem;
  color: var(--text);
  font-family: monospace;
  white-space: pre-wrap;
  margin: 0;
}
</style>
