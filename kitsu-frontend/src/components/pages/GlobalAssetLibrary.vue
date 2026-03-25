<template>
  <page-layout :side="!!selectedAsset">
    <template #main>
      <div class="global-asset-library">
        <header class="flexrow">
          <page-title class="mt1 filler" text="全局资产库" />
          <button-simple
            class="flexrow-item"
            :text="'导入'"
            icon="upload"
            @click="showImportModal"
            v-if="isCurrentUserManager"
          />
          <button-simple
            class="flexrow-item"
            :text="exportButtonText"
            icon="download"
            @click="showExportModal"
          />
          <button-simple
            class="flexrow-item"
            :text="'新建资产'"
            icon="plus"
            @click="showCreateModal"
            v-if="isCurrentUserManager"
          />
        </header>

        <div class="global-search-bar-wrapper">
          <asset-search-bar
            placeholder="全文搜索资产..."
            @search="onGlobalSearch"
            @suggestion-select="onSuggestionSelect"
          />
        </div>

        <div class="content-layout flexrow">
          <div class="category-sidebar">
            <category-tree-browser
              :categories="dynamicCategories"
              :selected-id="selectedCategoryId"
              :selectable="true"
              :show-count="true"
              :show-icon="true"
              :stats="categoryStats"
              @select="onCategorySelect"
            />
          </div>
          <div class="main-content filler">

        <div class="view-tabs flexrow">
          <span
            class="view-tab"
            :class="{ active: activeTab === 'grid' }"
            @click="activeTab = 'grid'"
          >
            资产网格
          </span>
          <span
            class="view-tab"
            :class="{ active: activeTab === 'ranking' }"
            @click="activeTab = 'ranking'"
          >
            热门排行
          </span>
        </div>

        <template v-if="activeTab === 'grid'">
        <div class="filters flexrow">
          <search-field
            ref="search-field"
            class="flexrow-item"
            @change="onSearchChange"
            :can-save="false"
            placeholder="搜索资产名称或标签..."
            v-focus
          />
          <combobox
            class="flexrow-item"
            :label="'状态'"
            :options="statusOptions"
            v-model="filters.status"
          />
          <span class="filler"></span>
          <combobox
            class="flexrow-item"
            :label="'排序'"
            :options="sortOptions"
            v-model="sorting"
          />
        </div>

        <div class="entities mb2">
          <table-info
            :is-loading="isLoading"
            :is-error="errors.loading"
            v-if="isLoading || errors.loading"
          />
          <div
            class="has-text-centered empty-message"
            v-else-if="!filteredAssets.length"
          >
            暂无资产数据
          </div>
          <template v-else>
            <div class="asset-grid">
              <div
                class="asset-card"
                :class="{
                  selected: selectedAsset && selectedAsset.id === asset.id,
                  checked: checkedAssetIds.includes(asset.id)
                }"
                :key="asset.id"
                @click="selectAsset(asset)"
                v-for="asset in paginatedAssets"
              >
                <label
                  class="card-checkbox"
                  @click.stop
                >
                  <input
                    type="checkbox"
                    :value="asset.id"
                    v-model="checkedAssetIds"
                  />
                  <span class="card-checkbox-mark"></span>
                </label>
                <div class="card-thumbnail">
                  <img
                    :src="asset.thumbnail_url || asset.preview_url"
                    :alt="asset.name"
                    v-if="asset.thumbnail_url || asset.preview_url"
                  />
                  <div class="thumbnail-placeholder" v-else>
                    <span class="placeholder-icon">📦</span>
                  </div>
                </div>
                <div class="card-info">
                  <div class="card-name" :title="asset.name">
                    {{ asset.name }}
                  </div>
                  <div class="card-meta flexrow">
                    <category-badge
                      :category="getAssetCategoryObject(asset)"
                      size="sm"
                    />
                    <span class="filler"></span>
                    <span
                      class="usage-count"
                      :title="'使用次数'"
                      v-if="asset.usage_count !== undefined"
                    >
                      {{ asset.usage_count }} 次
                    </span>
                  </div>
                  <div class="card-status">
                    <span
                      class="status-dot"
                      :class="'status-' + (asset.status || 'draft')"
                    ></span>
                    {{ getStatusLabel(asset.status) }}
                    <span
                      class="review-indicator pending_review"
                      v-if="asset.status === 'pending_review'"
                    >
                      审核中
                    </span>
                    <span
                      class="review-indicator reviewed"
                      v-else-if="asset.status === 'reviewed'"
                    >
                      已审核
                    </span>
                    <span
                      class="review-indicator rejected"
                      v-else-if="asset.status === 'rejected'"
                    >
                      被驳回
                    </span>
                  </div>
                </div>
              </div>
            </div>

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
                共 {{ pagination.total }} 个资产
              </span>
            </div>
          </template>
        </div>

        </template>

        <template v-if="activeTab === 'ranking'">
          <most-used-assets :limit="20" />
        </template>

          </div><!-- /main-content -->
        </div><!-- /content-layout -->

        <!-- Batch selection bar -->
        <div class="batch-bar" v-if="checkedAssetIds.length > 0">
          <span class="batch-count">
            已选 {{ checkedAssetIds.length }} 个资产
          </span>
          <button-simple
            :text="'导出选中'"
            icon="download"
            @click="showExportModal"
          />
          <span class="filler"></span>
          <button-simple
            :text="'取消选择'"
            icon="x"
            @click="checkedAssetIds = []"
          />
        </div>

        <create-global-asset-modal
          :active="modals.isCreateDisplayed"
          :is-loading="loading.create"
          :is-error="errors.create"
          @confirm="confirmCreateAsset"
          @cancel="modals.isCreateDisplayed = false"
        />

        <asset-export-modal
          :active="modals.isExportDisplayed"
          :selected-asset-ids="checkedAssetIds"
          :category-id="selectedCategoryId"
          @close="modals.isExportDisplayed = false"
        />

        <asset-import-modal
          :active="modals.isImportDisplayed"
          @close="onImportClose"
        />
      </div>
    </template>

    <template #side>
      <div class="asset-detail-panel" v-if="selectedAsset">
        <div class="panel-header flexrow">
          <h2 class="filler">资产详情</h2>
          <button-simple
            icon="x"
            @click="selectedAsset = null"
          />
        </div>

        <div class="panel-thumbnail">
          <img
            :src="selectedAsset.thumbnail_url || selectedAsset.preview_url"
            :alt="selectedAsset.name"
            v-if="selectedAsset.thumbnail_url || selectedAsset.preview_url"
          />
          <div class="thumbnail-placeholder large" v-else>
            <span class="placeholder-icon">📦</span>
          </div>
        </div>

        <div class="panel-section">
          <h3>基本信息</h3>
          <div class="info-row">
            <span class="info-label">名称</span>
            <span class="info-value">{{ selectedAsset.name }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">分类</span>
            <span class="info-value">
              <category-badge
                :category="getAssetCategoryObject(selectedAsset)"
                size="md"
              />
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">状态</span>
            <span class="info-value">
              <span
                class="status-dot"
                :class="'status-' + (selectedAsset.status || 'draft')"
              ></span>
              {{ getStatusLabel(selectedAsset.status) }}
            </span>
          </div>
          <div class="info-row" v-if="selectedAsset.usage_count !== undefined">
            <span class="info-label">使用次数</span>
            <span class="info-value">{{ selectedAsset.usage_count }}</span>
          </div>
          <div class="info-row" v-if="selectedAsset.description">
            <span class="info-label">描述</span>
            <span class="info-value">{{ selectedAsset.description }}</span>
          </div>
        </div>

        <div class="panel-section" v-if="selectedAsset.linked_projects && selectedAsset.linked_projects.length">
          <h3>关联项目</h3>
          <ul class="linked-projects">
            <li
              :key="project.id"
              v-for="project in selectedAsset.linked_projects"
            >
              {{ project.name }}
            </li>
          </ul>
        </div>

        <div class="panel-section" v-if="selectedAsset.files && selectedAsset.files.length">
          <h3>文件列表</h3>
          <ul class="file-list">
            <li
              :key="file.id || index"
              v-for="(file, index) in selectedAsset.files"
            >
              {{ file.name || file.filename }}
            </li>
          </ul>
        </div>

        <div class="panel-section" v-if="selectedAsset.tags && selectedAsset.tags.length">
          <h3>风格关键词</h3>
          <div class="tag-list">
            <span
              class="tag-chip"
              :key="tag"
              v-for="tag in selectedAsset.tags"
            >
              {{ tag }}
            </span>
          </div>
        </div>

        <div class="panel-section" v-if="similarAssets && similarAssets.length">
          <h3>相似资产</h3>
          <div class="similar-assets-list">
            <div
              class="similar-asset-item"
              :key="similar.id"
              @click="selectAsset(similar)"
              v-for="similar in similarAssets"
            >
              <div class="similar-thumbnail">
                <img
                  :src="similar.thumbnail_url || similar.preview_url"
                  :alt="similar.name"
                  v-if="similar.thumbnail_url || similar.preview_url"
                />
                <span class="placeholder-icon-sm" v-else>📦</span>
              </div>
              <span class="similar-name">{{ similar.name }}</span>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <asset-version-history
            :asset-id="selectedAsset.id"
            :compact="true"
            @view-diff="onViewVersionDiff"
            @restore="onRestoreVersion"
            @compare="onCompareVersions"
          />
        </div>

        <div class="panel-section">
          <asset-usage-tracker
            :asset-id="selectedAsset.id"
            @usage-recorded="onUsageRecorded"
            @usage-deleted="onUsageDeleted"
          />
        </div>

        <div class="panel-section">
          <h3>审核</h3>
          <asset-submit-review
            :asset="selectedAsset"
            @submitted="onReviewSubmitted"
          />
        </div>

        <div class="panel-actions">
          <button-simple
            text="查看关联图谱"
            icon="share-2"
            @click="goToAssetGraph"
          />
          <button-simple
            :text="'编辑'"
            icon="edit"
            @click="onEditAsset"
            v-if="isCurrentUserManager"
          />
          <combobox
            class="status-combobox"
            :label="'变更状态'"
            :options="statusChangeOptions"
            v-model="statusChangeValue"
            @input="onStatusChange"
            v-if="isCurrentUserManager"
          />
          <button-simple
            class="delete-button"
            :text="'删除'"
            icon="trash"
            @click="onDeleteAsset"
            v-if="isCurrentUserManager"
          />
        </div>
      </div>
    </template>
  </page-layout>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import AssetExportModal from '@/components/modals/AssetExportModal.vue'
import AssetImportModal from '@/components/modals/AssetImportModal.vue'
import AssetSearchBar from '@/components/widgets/AssetSearchBar.vue'
import AssetSubmitReview from '@/components/widgets/AssetSubmitReview.vue'
import AssetUsageTracker from '@/components/widgets/AssetUsageTracker.vue'
import AssetVersionHistory from '@/components/widgets/AssetVersionHistory.vue'
import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import CategoryBadge from '@/components/widgets/CategoryBadge.vue'
import CategoryTreeBrowser from '@/components/widgets/CategoryTreeBrowser.vue'
import Combobox from '@/components/widgets/Combobox.vue'
import CreateGlobalAssetModal from '@/components/modals/CreateGlobalAssetModal.vue'
import MostUsedAssets from '@/components/widgets/MostUsedAssets.vue'
import PageLayout from '@/components/layouts/PageLayout.vue'
import PageTitle from '@/components/widgets/PageTitle.vue'
import SearchField from '@/components/widgets/SearchField.vue'
import TableInfo from '@/components/widgets/TableInfo.vue'

export default {
  name: 'global-asset-library',

  components: {
    AssetExportModal,
    AssetImportModal,
    AssetSearchBar,
    AssetSubmitReview,
    AssetUsageTracker,
    AssetVersionHistory,
    ButtonSimple,
    CategoryBadge,
    CategoryTreeBrowser,
    Combobox,
    CreateGlobalAssetModal,
    MostUsedAssets,
    PageLayout,
    PageTitle,
    SearchField,
    TableInfo
  },

  data() {
    return {
      activeTab: 'grid',
      checkedAssetIds: [],
      selectedAsset: null,
      selectedCategoryId: null,
      sorting: 'updated_at',
      statusChangeValue: null,
      errors: {
        loading: false,
        create: false
      },
      loading: {
        create: false
      },
      modals: {
        isCreateDisplayed: false,
        isExportDisplayed: false,
        isImportDisplayed: false
      },
      sortOptions: [
        { label: '最近更新', value: 'updated_at' },
        { label: '名称', value: 'name' },
        { label: '使用次数', value: 'usage_count' },
        { label: '创建时间', value: 'created_at' }
      ],
      statusOptions: [
        { label: '全部', value: null },
        { label: '草稿', value: 'draft' },
        { label: '已审核', value: 'approved' },
        { label: '已归档', value: 'archived' }
      ],
      statusChangeOptions: [
        { label: '草稿', value: 'draft' },
        { label: '已审核', value: 'approved' },
        { label: '已归档', value: 'archived' }
      ]
    }
  },

  mounted() {
    this.loadGlobalAssets()
    this.loadCategoryTree()
    this.loadCategoryStats()
  },

  computed: {
    ...mapGetters([
      'categoryTree',
      'categoryStats',
      'getCategoryById',
      'getCategoryBySlug',
      'filteredAssets',
      'globalAssets',
      'globalAssetCategories',
      'globalAssetsIsLoading',
      'globalAssetsPagination',
      'globalAssetsFilters',
      'isCurrentUserManager',
      'assetSimilarAssets'
    ]),

    similarAssets() {
      return this.assetSimilarAssets
    },

    dynamicCategories() {
      return this.categoryTree && this.categoryTree.length
        ? this.categoryTree
        : []
    },

    assetCategories() {
      return this.globalAssetCategories
    },

    filters() {
      return this.globalAssetsFilters
    },

    isLoading() {
      return this.globalAssetsIsLoading
    },

    pagination() {
      return this.globalAssetsPagination
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

    exportButtonText() {
      if (this.checkedAssetIds.length > 0) {
        return `导出 (${this.checkedAssetIds.length})`
      }
      return '导出'
    },

    paginatedAssets() {
      const sorted = [...this.filteredAssets]
      if (this.sorting === 'name') {
        sorted.sort((a, b) =>
          (a.name || '').localeCompare(b.name || '', 'zh-CN', { numeric: true })
        )
      } else if (this.sorting === 'usage_count') {
        sorted.sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))
      } else if (this.sorting === 'created_at') {
        sorted.sort((a, b) =>
          (b.created_at || '').localeCompare(a.created_at || '')
        )
      } else {
        sorted.sort((a, b) =>
          (b.updated_at || '').localeCompare(a.updated_at || '')
        )
      }
      return sorted
    }
  },

  methods: {
    ...mapActions([
      'loadCategoryTree',
      'loadCategoryStats',
      'loadGlobalAssets',
      'loadGlobalAsset',
      'createGlobalAsset',
      'deleteGlobalAsset',
      'updateAssetStatus',
      'setGlobalAssetsFilter',
      'setGlobalAssetsPage',
      'loadSimilarAssets'
    ]),

    onGlobalSearch(query) {
      this.$router.push({ name: 'asset-search', query: { q: query } })
    },

    onSuggestionSelect(asset) {
      this.$router.push({ name: 'asset-search', query: { q: asset.name } })
    },

    onCategorySelect(category) {
      if (!category) {
        this.selectedCategoryId = null
        this.setCategory(null)
      } else {
        this.selectedCategoryId = category.id
        this.setCategory(category.slug || category.id)
      }
    },

    setCategory(category) {
      this.setGlobalAssetsFilter({ key: 'category', value: category })
    },

    onSearchChange() {
      const searchQuery = this.$refs['search-field']?.getValue() || ''
      this.setGlobalAssetsFilter({ key: 'search', value: searchQuery })
    },

    selectAsset(asset) {
      this.selectedAsset =
        this.selectedAsset && this.selectedAsset.id === asset.id ? null : asset
    },

    goToPage(page) {
      if (page < 1 || page > this.totalPages) return
      this.setGlobalAssetsPage(page)
    },

    getAssetCategoryObject(asset) {
      if (!asset) return null
      // Try category_id first (new dynamic system)
      if (asset.category_id && this.getCategoryById) {
        const cat = this.getCategoryById(asset.category_id)
        if (cat) return cat
      }
      // Fallback: look up by slug from legacy category string
      if (asset.category) {
        const allCats = Object.values(this.$store.getters.categoryMap || {})
        const found = allCats.find((c) => c.slug === asset.category)
        if (found) return found
      }
      // Final fallback: synthesize a minimal category object
      const legacy = this.assetCategories.find((c) => c.value === asset.category)
      if (legacy) {
        return { name: legacy.label, icon: legacy.icon, color: null }
      }
      return { name: asset.category || '未分类', icon: 'folder', color: null }
    },

    getCategoryLabel(value) {
      // Try dynamic categories first
      if (this.getCategoryById) {
        const dynCat = this.getCategoryById(value)
        if (dynCat) return dynCat.name
      }
      // Fallback to hardcoded categories
      const cat = this.assetCategories.find((c) => c.value === value)
      return cat ? cat.label : value || '未分类'
    },

    getStatusLabel(status) {
      const labels = {
        draft: '草稿',
        approved: '已审核',
        archived: '已归档'
      }
      return labels[status] || '草稿'
    },

    showCreateModal() {
      this.modals.isCreateDisplayed = true
    },

    showExportModal() {
      this.modals.isExportDisplayed = true
    },

    showImportModal() {
      this.modals.isImportDisplayed = true
    },

    onImportClose() {
      this.modals.isImportDisplayed = false
      this.loadGlobalAssets()
    },

    async confirmCreateAsset(data) {
      this.loading.create = true
      this.errors.create = false
      try {
        await this.createGlobalAsset(data)
        this.modals.isCreateDisplayed = false
      } catch (err) {
        console.error('Failed to create asset:', err)
        this.errors.create = true
      } finally {
        this.loading.create = false
      }
    },

    goToAssetGraph() {
      if (!this.selectedAsset) return
      this.$router.push({
        name: 'asset-node-graph',
        query: { assetId: this.selectedAsset.id }
      })
    },

    onEditAsset() {
      // TODO: Open edit modal for selectedAsset
    },

    async onStatusChange(newStatus) {
      if (!this.selectedAsset || !newStatus) return
      try {
        await this.updateAssetStatus({
          assetId: this.selectedAsset.id,
          status: newStatus
        })
        this.selectedAsset.status = newStatus
      } catch (err) {
        console.error('Failed to update asset status:', err)
      }
      this.statusChangeValue = null
    },

    onViewVersionDiff(versionId) {
      // TODO: Open diff viewer modal
      console.info('View version diff:', versionId)
    },

    onRestoreVersion(versionId) {
      // Restore is handled inside AssetVersionHistory component.
      // Reload current asset after restore completes.
      if (this.selectedAsset) {
        this.loadGlobalAsset(this.selectedAsset.id).then((asset) => {
          if (asset) this.selectedAsset = asset
        })
      }
    },

    onCompareVersions(versionA, versionB) {
      // TODO: Open version comparison modal
      console.info('Compare versions:', versionA, versionB)
    },

    onUsageRecorded(usage) {
      // Refresh the asset to update usage_count on the card
      if (this.selectedAsset) {
        this.loadGlobalAsset(this.selectedAsset.id).then((asset) => {
          if (asset) this.selectedAsset = asset
        })
      }
    },

    onUsageDeleted(usageId) {
      if (this.selectedAsset) {
        this.loadGlobalAsset(this.selectedAsset.id).then((asset) => {
          if (asset) this.selectedAsset = asset
        })
      }
    },

    onReviewSubmitted() {
      // Refresh asset to show updated review status
      if (this.selectedAsset) {
        this.loadGlobalAsset(this.selectedAsset.id).then((asset) => {
          if (asset) this.selectedAsset = asset
        })
      }
    },

    async onDeleteAsset() {
      if (!this.selectedAsset) return
      if (!confirm('确定要删除该资产吗？')) return
      try {
        await this.deleteGlobalAsset(this.selectedAsset.id)
        this.selectedAsset = null
      } catch (err) {
        console.error('Failed to delete asset:', err)
      }
    }
  },

  watch: {
    'filters.status'(value) {
      this.setGlobalAssetsFilter({ key: 'status', value })
    },
    selectedAsset(asset) {
      if (asset && asset.id) {
        this.loadSimilarAssets(asset.id)
      }
    }
  },

  head() {
    return {
      title: '全局资产库 - Kitsu'
    }
  }
}
</script>

<style lang="scss" scoped>
.global-asset-library {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  padding: 4em 2em 1em 2em;
  color: var(--text);
  margin-left: auto;
  margin-right: auto;
}

.content-layout {
  flex: 1;
  min-height: 0;
  gap: 1.5em;
  align-items: flex-start;
}

.category-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--background);
  border-radius: 0.8em;
  padding: 0.8em;
  border: 1px solid var(--border);
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.main-content {
  min-width: 0;
}

.view-tabs {
  margin-bottom: 1em;
  gap: 0;
  border-bottom: 1px solid var(--border);
}

.view-tab {
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

.filters {
  margin-bottom: 1em;
  gap: 1em;
  align-items: flex-end;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.asset-card {
  background-color: var(--background);
  border: 3px solid transparent;
  border-radius: 1em;
  cursor: pointer;
  transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  overflow: hidden;

  &:hover {
    border-color: var(--background-selectable);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  &.selected {
    border-color: var(--background-selected);
  }
}

.card-thumbnail {
  width: 100%;
  height: 150px;
  overflow: hidden;
  background: var(--background-alt);

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.thumbnail-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: var(--background-alt);

  .placeholder-icon {
    font-size: 2em;
    opacity: 0.5;
  }

  &.large {
    height: 200px;

    .placeholder-icon {
      font-size: 3em;
    }
  }
}

.card-info {
  padding: 0.8em;
}

.card-name {
  font-weight: 600;
  font-size: 0.95em;
  margin-bottom: 0.4em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  font-size: 0.8em;
  color: var(--text-alt);
  margin-bottom: 0.3em;
}

.category-badge {
  background: var(--background-alt);
  padding: 0.15em 0.5em;
  border-radius: 0.5em;
  font-size: 0.85em;
}

.usage-count {
  color: var(--text-alt);
  font-size: 0.85em;
}

.card-status {
  font-size: 0.8em;
  color: var(--text-alt);
  display: flex;
  align-items: center;
  gap: 0.3em;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-alt);

  &.status-draft {
    background: #999;
  }

  &.status-approved {
    background: #00b242;
  }

  &.status-archived {
    background: #f57f77;
  }

  &.status-pending_review {
    background: #f0a020;
  }

  &.status-reviewed {
    background: #00b242;
  }

  &.status-rejected {
    background: #e74c3c;
  }

  &.status-revision_requested {
    background: #e67e22;
  }
}

.review-indicator {
  display: inline-block;
  padding: 0.1em 0.4em;
  border-radius: 0.5em;
  font-size: 0.75em;
  font-weight: 500;
  margin-left: 0.3em;

  &.pending_review {
    background: rgba(240, 160, 32, 0.15);
    color: #f0a020;
  }

  &.reviewed {
    background: rgba(0, 178, 66, 0.15);
    color: #00b242;
  }

  &.rejected {
    background: rgba(231, 76, 60, 0.15);
    color: #e74c3c;
  }
}

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

/* Side panel */
.asset-detail-panel {
  padding: 1em;
}

.panel-header {
  margin-bottom: 1em;
  align-items: center;

  h2 {
    margin: 0;
    font-size: 1.1em;
  }
}

.panel-thumbnail {
  margin-bottom: 1em;
  border-radius: 0.5em;
  overflow: hidden;

  img {
    width: 100%;
    max-height: 250px;
    object-fit: cover;
  }
}

.panel-section {
  margin-bottom: 1.5em;

  h3 {
    font-size: 0.95em;
    font-weight: 600;
    margin-bottom: 0.5em;
    color: var(--text-strong);
  }
}

.info-row {
  display: flex;
  margin-bottom: 0.5em;
  font-size: 0.9em;
  gap: 0.5em;
}

.info-label {
  color: var(--text-alt);
  min-width: 5em;
  flex-shrink: 0;
}

.info-value {
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 0.3em;
}

.linked-projects,
.file-list {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    padding: 0.3em 0;
    font-size: 0.9em;
    border-bottom: 1px solid var(--border);

    &:last-child {
      border-bottom: none;
    }
  }
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4em;
}

.tag-chip {
  background: var(--background-alt);
  padding: 0.2em 0.6em;
  border-radius: 1em;
  font-size: 0.8em;
  color: var(--text);
}

.panel-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5em;
  padding-top: 1em;
  border-top: 1px solid var(--border);
}

.status-combobox {
  width: 100%;
}

.delete-button {
  color: var(--error);
}

/* Global search bar */
.global-search-bar-wrapper {
  margin-bottom: 1em;
  max-width: 480px;
}

/* Similar assets */
.similar-assets-list {
  display: flex;
  flex-direction: column;
  gap: 0.4em;
}

.similar-asset-item {
  display: flex;
  align-items: center;
  gap: 0.5em;
  padding: 0.4em;
  border-radius: 0.4em;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: var(--background-hover);
  }
}

.similar-thumbnail {
  width: 36px;
  height: 36px;
  border-radius: 0.3em;
  overflow: hidden;
  flex-shrink: 0;
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

.placeholder-icon-sm {
  font-size: 1em;
  opacity: 0.5;
}

.similar-name {
  font-size: 0.85em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Card checkbox */
.asset-card {
  position: relative;
}

.card-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;

  .asset-card:hover &,
  .asset-card.checked & {
    opacity: 1;
  }

  input[type='checkbox'] {
    display: none;
  }
}

.card-checkbox-mark {
  display: block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.3);
  transition: background 0.15s, border-color 0.15s;

  input:checked + & {
    background: var(--background-selected);
    border-color: var(--background-selected);

    &::after {
      content: '';
      display: block;
      width: 5px;
      height: 9px;
      border: solid #fff;
      border-width: 0 2px 2px 0;
      transform: rotate(45deg);
      margin: 2px auto 0;
    }
  }
}

.asset-card.checked {
  border-color: var(--background-selected);
}

/* Batch selection bar */
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
</style>
