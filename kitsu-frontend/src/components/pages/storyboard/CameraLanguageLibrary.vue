<template>
  <div class="camera-library" v-if="active">
    <div class="library-header">
      <h3>镜头语言库</h3>
      <div class="header-actions">
        <button class="btn-init" v-if="terms.length === 0 && !isLoading" @click="onInit">
          初始化预置术语
        </button>
        <button class="btn-create" @click="showForm = true">
          <PlusIcon :size="14" />
          添加术语
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
        <input v-model="searchQuery" placeholder="搜索术语..." />
      </div>
    </div>

    <!-- Create/Edit form -->
    <div class="term-form" v-if="showForm || editingTerm">
      <div class="form-header">
        <h4>{{ editingTerm ? '编辑术语' : '添加术语' }}</h4>
        <button class="btn-close-sm" @click="closeForm"><XIcon :size="14" /></button>
      </div>
      <div class="form-row">
        <input v-model="formTermCn" class="form-input" placeholder="中文术语" />
        <input v-model="formTermEn" class="form-input" placeholder="English Term" />
      </div>
      <select v-model="formCategory" class="form-select">
        <option v-for="cat in categoryOptions.slice(1)" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
      </select>
      <textarea v-model="formDescription" class="form-textarea" placeholder="术语描述/定义" rows="2" />
      <textarea v-model="formExample" class="form-textarea" placeholder="使用示例（可选）" rows="2" />
      <input v-model="formTags" class="form-input" placeholder="标签（逗号分隔）" />
      <div class="form-actions">
        <button class="btn-cancel" @click="closeForm">取消</button>
        <button class="btn-submit" @click="onSubmit" :disabled="!formTermCn.trim()">
          {{ editingTerm ? '保存' : '添加' }}
        </button>
      </div>
    </div>

    <!-- Term list -->
    <div class="term-list" v-if="!isLoading">
      <div
        v-for="term in filteredTerms"
        :key="term.id"
        class="term-card"
      >
        <div class="card-header">
          <span class="card-category" :class="'cat-' + term.category">{{ categoryLabel(term.category) }}</span>
          <span class="card-term-cn">{{ term.term_cn }}</span>
          <span class="card-term-en">{{ term.term_en }}</span>
        </div>
        <p class="card-desc" v-if="term.description">{{ term.description }}</p>
        <p class="card-example" v-if="term.example_usage">
          <span class="example-label">示例:</span> {{ term.example_usage }}
        </p>
        <div class="card-tags" v-if="term.tags && term.tags.length">
          <span v-for="tag in term.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
        <div class="card-footer">
          <span class="meta">{{ term.created_by_name }}</span>
          <div class="card-actions">
            <button class="btn-sm" @click="onEdit(term)"><PencilIcon :size="12" /></button>
            <button class="btn-sm btn-danger" @click="onDelete(term)"><Trash2Icon :size="12" /></button>
          </div>
        </div>
      </div>
      <div v-if="filteredTerms.length === 0" class="empty-state">
        {{ searchQuery ? '没有匹配的术语' : '暂无术语' }}
      </div>
    </div>
    <div v-else class="loading-state"><div class="spinner" /></div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import { PencilIcon, PlusIcon, SearchIcon, Trash2Icon, XIcon } from 'lucide-vue-next'

const CATEGORIES = [
  { value: '', label: '全部' },
  { value: 'shot_size', label: '景别' },
  { value: 'camera_movement', label: '运镜' },
  { value: 'composition', label: '构图' },
  { value: 'angle', label: '角度' },
  { value: 'transition', label: '转场' },
  { value: 'other', label: '其他' }
]

export default {
  name: 'CameraLanguageLibrary',
  components: { PencilIcon, PlusIcon, SearchIcon, Trash2Icon, XIcon },

  props: {
    active: { type: Boolean, default: false },
    projectId: { type: String, required: true }
  },

  emits: ['close'],

  data() {
    return {
      isLoading: false,
      terms: [],
      categoryCounts: {},
      filterCategory: '',
      searchQuery: '',
      showForm: false,
      editingTerm: null,
      formTermCn: '', formTermEn: '', formCategory: 'shot_size',
      formDescription: '', formExample: '', formTags: '',
      categoryOptions: CATEGORIES
    }
  },

  computed: {
    filteredTerms() {
      let list = this.terms
      if (this.filterCategory) list = list.filter(t => t.category === this.filterCategory)
      if (this.searchQuery) {
        const q = this.searchQuery.toLowerCase()
        list = list.filter(t =>
          t.term_cn.toLowerCase().includes(q) ||
          (t.term_en || '').toLowerCase().includes(q) ||
          (t.description || '').toLowerCase().includes(q)
        )
      }
      return list
    }
  },

  watch: {
    active(val) { if (val) this.loadData() }
  },

  methods: {
    ...mapActions(['listCameraTerms', 'createCameraTerm', 'updateCameraTerm', 'deleteCameraTerm', 'initCameraTerms']),

    categoryLabel(cat) {
      return CATEGORIES.find(c => c.value === cat)?.label || cat
    },

    async loadData() {
      this.isLoading = true
      try {
        const data = await this.listCameraTerms({ projectId: this.projectId })
        this.terms = data.terms || []
        this.categoryCounts = data.categories || {}
      } catch (err) {
        console.error('Failed to load camera terms:', err)
      } finally {
        this.isLoading = false
      }
    },

    async onInit() {
      try {
        await this.initCameraTerms({ projectId: this.projectId })
        await this.loadData()
      } catch (err) {
        console.error('Failed to init:', err)
      }
    },

    closeForm() {
      this.showForm = false
      this.editingTerm = null
      this.formTermCn = ''; this.formTermEn = ''; this.formCategory = 'shot_size'
      this.formDescription = ''; this.formExample = ''; this.formTags = ''
    },

    onEdit(term) {
      this.editingTerm = term
      this.formTermCn = term.term_cn; this.formTermEn = term.term_en || ''
      this.formCategory = term.category || 'other'
      this.formDescription = term.description || ''; this.formExample = term.example_usage || ''
      this.formTags = (term.tags || []).join(', ')
      this.showForm = false
    },

    async onSubmit() {
      const tags = this.formTags ? this.formTags.split(',').map(t => t.trim()).filter(Boolean) : []
      try {
        if (this.editingTerm) {
          await this.updateCameraTerm({
            projectId: this.projectId, termId: this.editingTerm.id,
            term_cn: this.formTermCn.trim(), term_en: this.formTermEn.trim(),
            category: this.formCategory, description: this.formDescription.trim(),
            example_usage: this.formExample.trim(), tags
          })
        } else {
          await this.createCameraTerm({
            projectId: this.projectId,
            termCn: this.formTermCn.trim(), termEn: this.formTermEn.trim(),
            category: this.formCategory, description: this.formDescription.trim(),
            exampleUsage: this.formExample.trim(), tags
          })
        }
        this.closeForm()
        await this.loadData()
      } catch (err) {
        console.error('Failed to save term:', err)
      }
    },

    async onDelete(term) {
      if (!confirm(`删除术语 "${term.term_cn}"？`)) return
      try {
        await this.deleteCameraTerm({ projectId: this.projectId, termId: term.id })
        await this.loadData()
      } catch (err) {
        console.error('Failed to delete:', err)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.camera-library {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
}

.library-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 1rem; border-bottom: 1px solid var(--border);
  h3 { margin: 0; font-size: 1rem; }
}

.header-actions { display: flex; align-items: center; gap: 8px; }

.btn-init {
  padding: 5px 12px; border: 1px solid #10ac84; border-radius: 6px;
  background: transparent; color: #10ac84; font-size: 0.8rem; cursor: pointer;
  &:hover { background: #10ac84; color: #fff; }
}

.btn-create {
  display: flex; align-items: center; gap: 4px;
  padding: 5px 12px; border: none; border-radius: 6px;
  background: var(--color-primary); color: #fff; font-size: 0.8rem; cursor: pointer;
}

.btn-close {
  background: none; border: none; color: var(--text-alt); cursor: pointer; padding: 4px;
  &:hover { color: var(--text); }
}

.library-filters {
  display: flex; align-items: center; gap: 12px;
  padding: 0.5rem 1rem; border-bottom: 1px solid var(--border);
}

.filter-categories { display: flex; gap: 4px; }

.cat-btn {
  padding: 3px 10px; border: 1px solid var(--border); border-radius: 12px;
  background: transparent; color: var(--text-alt); font-size: 0.75rem; cursor: pointer;
  &.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
}

.cat-count { font-size: 0.65rem; opacity: 0.7; margin-left: 2px; }

.filter-search {
  display: flex; align-items: center; gap: 6px; flex: 1;
  padding: 4px 8px; border: 1px solid var(--border); border-radius: 6px; color: var(--text-alt);
  input { flex: 1; border: none; background: transparent; color: var(--text); font-size: 0.8rem; outline: none; }
}

.term-form {
  padding: 1rem; border-bottom: 1px solid var(--border);
  background: var(--background-alt, rgba(255,255,255,0.02));
}

.form-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
  h4 { margin: 0; font-size: 0.9rem; }
}

.btn-close-sm { background: none; border: none; color: var(--text-alt); cursor: pointer; }

.form-input, .form-textarea, .form-select {
  width: 100%; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px;
  background: var(--background); color: var(--text); font-size: 0.8rem; margin-bottom: 6px;
  &:focus { outline: none; border-color: var(--color-primary); }
}

.form-textarea { resize: vertical; }
.form-row { display: flex; gap: 8px; }
.form-select { width: auto; }
.form-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }

.btn-cancel {
  padding: 5px 14px; border: 1px solid var(--border); border-radius: 6px;
  background: transparent; color: var(--text); cursor: pointer;
}

.btn-submit {
  padding: 5px 14px; border: none; border-radius: 6px;
  background: var(--color-primary); color: #fff; cursor: pointer;
  &:disabled { opacity: 0.5; }
}

.term-list { flex: 1; overflow-y: auto; padding: 0.75rem 1rem; }

.term-card {
  border: 1px solid var(--border); border-radius: 8px;
  padding: 10px 12px; margin-bottom: 8px;
  &:hover { border-color: var(--color-primary); }
}

.card-header { display: flex; align-items: center; gap: 8px; }

.card-category {
  padding: 1px 6px; border-radius: 6px; font-size: 0.65rem; font-weight: 600;
  &.cat-shot_size { background: rgba(10, 189, 227, 0.15); color: #0abde3; }
  &.cat-camera_movement { background: rgba(255, 56, 96, 0.15); color: #ff3860; }
  &.cat-composition { background: rgba(16, 172, 132, 0.15); color: #10ac84; }
  &.cat-angle { background: rgba(255, 159, 67, 0.15); color: #ff9f43; }
  &.cat-transition { background: rgba(156, 39, 176, 0.15); color: #9c27b0; }
  &.cat-other { background: rgba(128, 128, 128, 0.15); color: #888; }
}

.card-term-cn { font-size: 0.85rem; font-weight: 600; color: var(--text); }
.card-term-en { font-size: 0.75rem; color: var(--text-alt); }

.card-desc { font-size: 0.8rem; color: var(--text); margin: 6px 0 0; line-height: 1.4; }

.card-example {
  font-size: 0.75rem; color: var(--text-alt); margin: 4px 0 0; font-style: italic;
  .example-label { font-weight: 600; font-style: normal; }
}

.card-tags { display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 0; }
.tag {
  padding: 1px 6px; border-radius: 8px; background: var(--background-alt, #2a2a2a);
  font-size: 0.65rem; color: var(--text-alt);
}

.card-footer {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.65rem; color: var(--text-alt);
}
.card-actions { margin-left: auto; display: flex; gap: 4px; }

.btn-sm {
  background: none; border: none; color: var(--text-alt); cursor: pointer;
  padding: 2px 4px; border-radius: 3px;
  &:hover { background: var(--background-alt); color: var(--text); }
}
.btn-danger:hover { color: #ff3860; }

.empty-state { text-align: center; padding: 3rem; color: var(--text-alt); font-size: 0.85rem; }
.loading-state { text-align: center; padding: 3rem; }
.spinner {
  width: 20px; height: 20px; border: 2px solid var(--border);
  border-top-color: var(--color-primary); border-radius: 50%;
  animation: spin 0.8s linear infinite; margin: 0 auto;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
