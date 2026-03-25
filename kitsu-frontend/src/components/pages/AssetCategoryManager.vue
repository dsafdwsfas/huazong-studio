<template>
  <page-layout>
    <template #main>
      <div class="asset-category-manager">
        <header class="flexrow">
          <page-title class="mt1 filler" text="资产分类管理" />
          <button-simple
            class="flexrow-item"
            :text="'初始化预设分类'"
            icon="database"
            @click="onInitDefaults"
            v-if="!categoryTree.length"
          />
        </header>

        <div class="manager-layout">
          <!-- Left: Category tree -->
          <div class="tree-panel">
            <div class="panel-header flexrow">
              <h3 class="filler">分类结构</h3>
              <button-simple
                icon="plus"
                :text="'新建根分类'"
                @click="showCreateForm(null)"
              />
            </div>

            <div class="tree-container">
              <table-info
                :is-loading="isCategoriesLoading"
                v-if="isCategoriesLoading"
              />
              <div
                class="has-text-centered empty-message"
                v-else-if="!categoryTree.length"
              >
                暂无分类，点击「初始化预设分类」创建默认分类
              </div>
              <category-tree-browser
                :categories="categoryTree"
                :selected-id="selectedCategoryId"
                :selectable="true"
                :draggable="true"
                :show-count="true"
                :show-icon="true"
                :stats="categoryStats"
                @select="onSelectCategory"
                @reorder="onReorder"
                v-else
              />
            </div>
          </div>

          <!-- Right: Detail / Edit form -->
          <div class="detail-panel">
            <template v-if="selectedCategory">
              <div class="panel-header flexrow">
                <h3 class="filler">编辑分类</h3>
                <button-simple
                  icon="plus"
                  :text="'新建子分类'"
                  @click="showCreateForm(selectedCategory.id)"
                />
              </div>

              <div class="edit-form">
                <div class="field">
                  <label>名称</label>
                  <input
                    type="text"
                    v-model="editForm.name"
                    placeholder="分类名称"
                  />
                </div>
                <div class="field">
                  <label>英文标识 (slug)</label>
                  <input
                    type="text"
                    v-model="editForm.slug"
                    placeholder="category-slug"
                  />
                </div>
                <div class="field">
                  <label>描述</label>
                  <textarea
                    v-model="editForm.description"
                    placeholder="分类描述..."
                    rows="3"
                  ></textarea>
                </div>
                <div class="field">
                  <label>图标名称 (Lucide)</label>
                  <input
                    type="text"
                    v-model="editForm.icon"
                    placeholder="例: user, image, box"
                  />
                </div>
                <div class="field">
                  <label>颜色</label>
                  <div class="color-field flexrow">
                    <input
                      type="color"
                      v-model="editForm.color"
                      class="color-input"
                    />
                    <input
                      type="text"
                      v-model="editForm.color"
                      placeholder="#666666"
                      class="color-text"
                    />
                  </div>
                </div>

                <div class="form-info" v-if="selectedCategory.is_system">
                  <span class="system-badge">🔒 系统预设分类，不可删除</span>
                </div>

                <div class="form-actions flexrow">
                  <button-simple
                    :text="'保存'"
                    icon="save"
                    @click="onSaveCategory"
                    :disabled="isSaving"
                  />
                  <span class="filler"></span>
                  <button-simple
                    class="delete-button"
                    :text="'删除'"
                    icon="trash"
                    @click="onDeleteCategory"
                    :disabled="selectedCategory.is_system || isSaving"
                    v-if="!selectedCategory.is_system"
                  />
                </div>
              </div>
            </template>

            <template v-else-if="isCreating">
              <div class="panel-header">
                <h3>
                  {{ createParentId ? '新建子分类' : '新建根分类' }}
                </h3>
              </div>

              <div class="edit-form">
                <div class="field">
                  <label>名称</label>
                  <input
                    type="text"
                    v-model="createForm.name"
                    placeholder="分类名称"
                  />
                </div>
                <div class="field">
                  <label>英文标识 (slug)</label>
                  <input
                    type="text"
                    v-model="createForm.slug"
                    placeholder="category-slug"
                  />
                </div>
                <div class="field">
                  <label>描述</label>
                  <textarea
                    v-model="createForm.description"
                    placeholder="分类描述..."
                    rows="3"
                  ></textarea>
                </div>
                <div class="field">
                  <label>图标名称 (Lucide)</label>
                  <input
                    type="text"
                    v-model="createForm.icon"
                    placeholder="例: user, image, box"
                  />
                </div>
                <div class="field">
                  <label>颜色</label>
                  <div class="color-field flexrow">
                    <input
                      type="color"
                      v-model="createForm.color"
                      class="color-input"
                    />
                    <input
                      type="text"
                      v-model="createForm.color"
                      placeholder="#666666"
                      class="color-text"
                    />
                  </div>
                </div>

                <div class="form-actions flexrow">
                  <button-simple
                    :text="'创建'"
                    icon="plus"
                    @click="onCreateCategory"
                    :disabled="isSaving || !createForm.name"
                  />
                  <button-simple
                    :text="'取消'"
                    @click="cancelCreate"
                  />
                </div>
              </div>
            </template>

            <div class="empty-detail" v-else>
              <p>请选择一个分类进行编辑，或创建新分类</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </page-layout>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import CategoryTreeBrowser from '@/components/widgets/CategoryTreeBrowser.vue'
import PageLayout from '@/components/layouts/PageLayout.vue'
import PageTitle from '@/components/widgets/PageTitle.vue'
import TableInfo from '@/components/widgets/TableInfo.vue'

export default {
  name: 'asset-category-manager',

  components: {
    ButtonSimple,
    CategoryTreeBrowser,
    PageLayout,
    PageTitle,
    TableInfo
  },

  data() {
    return {
      selectedCategoryId: null,
      isCreating: false,
      createParentId: null,
      isSaving: false,
      editForm: {
        name: '',
        slug: '',
        description: '',
        icon: '',
        color: '#666666'
      },
      createForm: {
        name: '',
        slug: '',
        description: '',
        icon: '',
        color: '#666666'
      }
    }
  },

  mounted() {
    this.loadCategoryTree()
    this.loadCategoryStats()
  },

  computed: {
    ...mapGetters([
      'categoryTree',
      'categoryMap',
      'categoryStats',
      'isCategoriesLoading',
      'getCategoryById'
    ]),

    selectedCategory() {
      if (!this.selectedCategoryId) return null
      return this.getCategoryById(this.selectedCategoryId)
    }
  },

  methods: {
    ...mapActions([
      'loadCategoryTree',
      'loadCategoryStats',
      'createCategory',
      'updateCategory',
      'deleteCategory',
      'reorderCategories',
      'initDefaults'
    ]),

    onSelectCategory(category) {
      this.isCreating = false
      if (!category) {
        this.selectedCategoryId = null
        return
      }
      this.selectedCategoryId = category.id
      this.editForm = {
        name: category.name || '',
        slug: category.slug || '',
        description: category.description || '',
        icon: category.icon || '',
        color: category.color || '#666666'
      }
    },

    showCreateForm(parentId) {
      this.selectedCategoryId = null
      this.isCreating = true
      this.createParentId = parentId
      this.createForm = {
        name: '',
        slug: '',
        description: '',
        icon: '',
        color: '#666666'
      }
    },

    cancelCreate() {
      this.isCreating = false
      this.createParentId = null
    },

    async onCreateCategory() {
      if (!this.createForm.name) return
      this.isSaving = true
      try {
        const data = { ...this.createForm }
        if (this.createParentId) {
          data.parent_id = this.createParentId
        }
        await this.createCategory(data)
        this.isCreating = false
        this.createParentId = null
        await this.loadCategoryStats()
      } catch (err) {
        console.error('Failed to create category:', err)
      } finally {
        this.isSaving = false
      }
    },

    async onSaveCategory() {
      if (!this.selectedCategoryId) return
      this.isSaving = true
      try {
        await this.updateCategory({
          categoryId: this.selectedCategoryId,
          data: { ...this.editForm }
        })
      } catch (err) {
        console.error('Failed to update category:', err)
      } finally {
        this.isSaving = false
      }
    },

    async onDeleteCategory() {
      if (!this.selectedCategory) return
      if (this.selectedCategory.is_system) return

      const hasChildren =
        this.selectedCategory.children &&
        this.selectedCategory.children.length > 0
      const count = this.categoryStats[this.selectedCategoryId]

      let msg = '确定要删除该分类吗？'
      if (hasChildren) {
        msg = '该分类含有子分类，不可删除。请先移除所有子分类。'
        alert(msg)
        return
      }
      if (count && count > 0) {
        msg = `该分类下有 ${count} 个资产，不可删除。请先转移或移除关联资产。`
        alert(msg)
        return
      }
      if (!confirm(msg)) return

      this.isSaving = true
      try {
        await this.deleteCategory(this.selectedCategoryId)
        this.selectedCategoryId = null
        await this.loadCategoryStats()
      } catch (err) {
        console.error('Failed to delete category:', err)
      } finally {
        this.isSaving = false
      }
    },

    async onReorder(reorderInfo) {
      try {
        await this.reorderCategories([
          {
            id: reorderInfo.draggedId,
            parent_id: reorderInfo.targetParentId,
            after_id: reorderInfo.targetId
          }
        ])
      } catch (err) {
        console.error('Failed to reorder categories:', err)
      }
    },

    async onInitDefaults() {
      if (!confirm('将创建默认分类结构，确定继续？')) return
      try {
        await this.initDefaults()
        await this.loadCategoryStats()
      } catch (err) {
        console.error('Failed to init default categories:', err)
      }
    }
  },

  watch: {
    selectedCategory(cat) {
      if (cat) {
        this.editForm = {
          name: cat.name || '',
          slug: cat.slug || '',
          description: cat.description || '',
          icon: cat.icon || '',
          color: cat.color || '#666666'
        }
      }
    }
  },

  head() {
    return {
      title: '分类管理 - Kitsu'
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-category-manager {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  padding: 4em 2em 1em 2em;
  color: var(--text);
}

.manager-layout {
  display: flex;
  gap: 2em;
  flex: 1;
  min-height: 0;
}

.tree-panel {
  width: 360px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--background);
  border-radius: 1em;
  padding: 1em;
  border: 1px solid var(--border);
}

.tree-container {
  flex: 1;
  overflow-y: auto;
  padding-top: 0.5em;
}

.detail-panel {
  flex: 1;
  background: var(--background);
  border-radius: 1em;
  padding: 1.5em;
  border: 1px solid var(--border);
  overflow-y: auto;
}

.panel-header {
  margin-bottom: 1em;
  align-items: center;

  h3 {
    margin: 0;
    font-size: 1em;
    font-weight: 600;
    color: var(--text-strong);
  }
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 1em;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3em;

  label {
    font-size: 0.85em;
    font-weight: 600;
    color: var(--text-alt);
  }

  input[type='text'],
  textarea {
    padding: 0.5em 0.7em;
    border: 1px solid var(--border);
    border-radius: 0.4em;
    background: var(--background-alt);
    color: var(--text);
    font-size: 0.9em;
    font-family: inherit;

    &:focus {
      outline: none;
      border-color: var(--background-selected);
    }
  }

  textarea {
    resize: vertical;
  }
}

.color-field {
  gap: 0.5em;
  align-items: center;
}

.color-input {
  width: 36px;
  height: 36px;
  padding: 2px;
  border: 1px solid var(--border);
  border-radius: 0.4em;
  cursor: pointer;
  background: transparent;
}

.color-text {
  flex: 1;
}

.form-info {
  padding: 0.5em 0;
}

.system-badge {
  font-size: 0.85em;
  color: var(--text-alt);
}

.form-actions {
  padding-top: 0.5em;
  gap: 0.5em;
  align-items: center;
}

.delete-button {
  color: var(--error);
}

.empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-alt);
  font-size: 0.95em;
}

.empty-message {
  padding: 2em;
  color: var(--text-alt);
}
</style>
