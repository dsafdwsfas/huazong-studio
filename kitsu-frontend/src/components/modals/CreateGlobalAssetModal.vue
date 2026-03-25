<template>
  <div
    :class="{
      modal: true,
      'is-active': active
    }"
  >
    <div class="modal-background" @click="$emit('cancel')"></div>
    <div class="modal-content">
      <div class="box">
        <h2 class="subtitle">新建资产</h2>

        <text-field
          ref="name-field"
          :label="'资产名称'"
          v-model="form.name"
          @enter="confirmClicked"
          v-focus
        />

        <div class="field">
          <label class="label">分类</label>
          <div class="category-selector">
            <div class="category-search" v-if="flatCategories.length > 8">
              <input
                class="input category-search-input"
                type="text"
                placeholder="搜索分类..."
                v-model="categorySearch"
              />
            </div>
            <div class="category-options">
              <div
                class="category-option"
                :class="{ selected: form.categoryId === cat.id }"
                :key="cat.id"
                @click="selectCategory(cat)"
                v-for="cat in filteredCategories"
              >
                <span
                  class="category-option-icon"
                  v-html="getCategoryIconSvg(cat.icon)"
                ></span>
                <span class="category-option-name">{{ cat.name }}</span>
              </div>
              <div
                class="category-option-empty"
                v-if="!filteredCategories.length"
              >
                未找到匹配的分类
              </div>
            </div>
          </div>
        </div>

        <text-field
          :label="'描述'"
          v-model="form.description"
          :is-text-area="true"
        />

        <text-field
          :label="'风格关键词（逗号分隔）'"
          v-model="form.tagsRaw"
        />

        <p class="is-danger has-text-right" v-if="isError">
          创建资产失败，请重试
        </p>

        <p class="has-text-right">
          <a
            :class="{
              button: true,
              'is-primary': true,
              'is-loading': isLoading
            }"
            :disabled="!isFormValid"
            @click="confirmClicked"
          >
            创建
          </a>
          <button class="button is-link" @click="$emit('cancel')">
            取消
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import { modalMixin } from '@/components/modals/base_modal'
import { getCategoryIcon } from '@/lib/category-icons'

import TextField from '@/components/widgets/TextField.vue'

export default {
  name: 'create-global-asset-modal',

  mixins: [modalMixin],

  components: {
    TextField
  },

  props: {
    active: {
      default: false,
      type: Boolean
    },
    isLoading: {
      default: false,
      type: Boolean
    },
    isError: {
      default: false,
      type: Boolean
    }
  },

  emits: ['cancel', 'confirm'],

  data() {
    return {
      form: {
        name: '',
        categoryId: null,
        description: '',
        tagsRaw: ''
      },
      categorySearch: ''
    }
  },

  computed: {
    ...mapGetters(['categoryTree', 'categoryMap']),

    flatCategories() {
      return this.flattenTree(this.categoryTree)
    },

    filteredCategories() {
      if (!this.categorySearch) return this.flatCategories
      const term = this.categorySearch.toLowerCase()
      return this.flatCategories.filter(
        (c) =>
          (c.name && c.name.toLowerCase().includes(term)) ||
          (c.name_en && c.name_en.toLowerCase().includes(term)) ||
          (c.slug && c.slug.toLowerCase().includes(term))
      )
    },

    isFormValid() {
      return (
        this.form.name &&
        this.form.name.trim().length > 0 &&
        this.form.categoryId
      )
    }
  },

  methods: {
    getCategoryIconSvg(iconName) {
      return getCategoryIcon(iconName)
    },

    flattenTree(tree) {
      const result = []
      for (const cat of tree || []) {
        result.push(cat)
        if (cat.children && cat.children.length) {
          result.push(...this.flattenTree(cat.children))
        }
      }
      return result
    },

    selectCategory(cat) {
      this.form.categoryId = cat.id
    },

    confirmClicked() {
      if (!this.isFormValid) return
      const tags = this.form.tagsRaw
        ? this.form.tagsRaw
            .split(/[,，]/)
            .map((t) => t.trim())
            .filter(Boolean)
        : []
      const selectedCategory = this.categoryMap[this.form.categoryId]
      this.$emit('confirm', {
        name: this.form.name.trim(),
        category_id: this.form.categoryId,
        // Keep legacy category slug for backward compatibility
        category: selectedCategory ? selectedCategory.slug : null,
        description: this.form.description.trim(),
        tags
      })
    },

    resetForm() {
      this.form.name = ''
      this.form.categoryId =
        this.flatCategories.length > 0 ? this.flatCategories[0].id : null
      this.form.description = ''
      this.form.tagsRaw = ''
      this.categorySearch = ''
    }
  },

  watch: {
    active(newVal) {
      if (newVal) {
        this.resetForm()
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.modal-content .box {
  padding: 2em;
}

.subtitle {
  margin-bottom: 1em;
}

.has-text-right {
  margin-top: 1em;
}

.category-selector {
  border: 1px solid var(--border);
  border-radius: 0.5em;
  overflow: hidden;
}

.category-search {
  padding: 0.5em;
  border-bottom: 1px solid var(--border);
}

.category-search-input {
  border: 1px solid var(--border);
  border-radius: 0.3em;
  padding: 0.3em 0.5em;
  font-size: 0.9em;
  width: 100%;
  background: var(--background);
  color: var(--text);

  &:focus {
    outline: none;
    border-color: var(--background-selected);
  }
}

.category-options {
  max-height: 200px;
  overflow-y: auto;
  padding: 0.3em;
}

.category-option {
  display: flex;
  align-items: center;
  gap: 0.5em;
  padding: 0.4em 0.6em;
  border-radius: 0.3em;
  cursor: pointer;
  font-size: 0.9em;
  transition: background 0.15s ease;

  &:hover {
    background: var(--background-hover);
  }

  &.selected {
    background: var(--background-selected);
    font-weight: 600;
  }
}

.category-option-icon {
  display: inline-flex;
  align-items: center;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: var(--text-alt);

  :deep(svg) {
    width: 18px;
    height: 18px;
  }
}

.category-option-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-option-empty {
  text-align: center;
  padding: 1em;
  color: var(--text-alt);
  font-size: 0.85em;
}
</style>
