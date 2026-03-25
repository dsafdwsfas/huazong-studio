<template>
  <page-layout>
    <template #main>
      <div class="asset-search-page">
        <header class="search-header">
          <page-title class="mt1" text="资产搜索" />
          <asset-search-bar
            ref="searchBar"
            :autofocus="true"
            :show-history="true"
            @search="onSearch"
            @suggestion-select="onSuggestionSelect"
          />
          <div class="search-meta flexrow" v-if="hasSearched">
            <div class="sort-controls flexrow-item">
              <span class="sort-label">排序:</span>
              <span
                class="sort-option"
                :class="{ active: searchSort === opt.value }"
                :key="opt.value"
                @click="changeSort(opt.value)"
                v-for="opt in sortOptions"
              >
                {{ opt.label }}
              </span>
            </div>
            <span class="filler"></span>
            <span class="results-info" v-if="!isSearching">
              共 {{ totalHits }} 条结果
              <span class="search-time" v-if="searchResults.processingTimeMs">
                ({{ searchResults.processingTimeMs }}ms)
              </span>
            </span>
          </div>
        </header>

        <div class="search-body flexrow" v-if="hasSearched">
          <!-- Filter sidebar -->
          <aside class="filter-sidebar">
            <div class="filter-section">
              <h4 class="filter-title">分类</h4>
              <div
                class="filter-item"
                :class="{ active: !searchFilters.categorySlug }"
                @click="setFilterCategory(null)"
              >
                <span>全部</span>
                <span class="facet-count" v-if="facets.categories">
                  {{ facetTotal('categories') }}
                </span>
              </div>
              <div
                class="filter-item"
                :class="{ active: searchFilters.categorySlug === cat.slug }"
                :key="cat.slug || cat.value"
                @click="setFilterCategory(cat.slug || cat.value)"
                v-for="cat in availableCategories"
              >
                <span>{{ cat.name || cat.label }}</span>
                <span class="facet-count" v-if="getFacetCount('categories', cat.slug || cat.value)">
                  {{ getFacetCount('categories', cat.slug || cat.value) }}
                </span>
              </div>
            </div>

            <div class="filter-section">
              <h4 class="filter-title">状态</h4>
              <div
                class="filter-item"
                :class="{ active: !searchFilters.status }"
                @click="setFilterStatus(null)"
              >
                全部
              </div>
              <div
                class="filter-item"
                :class="{ active: searchFilters.status === opt.value }"
                :key="opt.value"
                @click="setFilterStatus(opt.value)"
                v-for="opt in statusOptions"
              >
                <span>
                  <span class="status-dot" :class="'status-' + opt.value"></span>
                  {{ opt.label }}
                </span>
                <span class="facet-count" v-if="getFacetCount('statuses', opt.value)">
                  {{ getFacetCount('statuses', opt.value) }}
                </span>
              </div>
            </div>

            <div class="filter-section" v-if="facets.creators && facets.creators.length">
              <h4 class="filter-title">创建者</h4>
              <div
                class="filter-item"
                :class="{ active: !searchFilters.creatorId }"
                @click="setFilterCreator(null)"
              >
                全部
              </div>
              <div
                class="filter-item"
                :class="{ active: searchFilters.creatorId === creator.id }"
                :key="creator.id"
                @click="setFilterCreator(creator.id)"
                v-for="creator in facets.creators"
              >
                <span>{{ creator.name }}</span>
                <span class="facet-count">{{ creator.count }}</span>
              </div>
            </div>

            <div class="filter-actions" v-if="activeFilterCount > 0">
              <button-simple
                text="清除筛选"
                icon="x"
                @click="clearFilters"
              />
            </div>
          </aside>

          <!-- Search results -->
          <div class="search-results filler">
            <table-info
              :is-loading="isSearching"
              v-if="isSearching"
            />

            <div
              class="empty-results"
              v-else-if="!searchHits.length"
            >
              <div class="empty-icon">🔍</div>
              <p>未找到匹配 "<strong>{{ searchQuery }}</strong>" 的资产</p>
              <p class="empty-hint">尝试使用不同的关键词或减少筛选条件</p>
            </div>

            <template v-else>
              <div class="results-grid">
                <div
                  class="result-card"
                  :key="asset.id"
                  @click="selectAsset(asset)"
                  v-for="asset in searchHits"
                >
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
                  <div class="card-body">
                    <div
                      class="card-name"
                      :title="asset.name"
                      v-html="highlightQuery(asset.name)"
                    ></div>
                    <div class="card-meta flexrow">
                      <category-badge
                        :category="getAssetCategoryObject(asset)"
                        size="sm"
                      />
                      <span class="filler"></span>
                      <span
                        class="status-dot"
                        :class="'status-' + (asset.status || 'draft')"
                      ></span>
                    </div>
                    <div class="card-tags" v-if="asset.tags && asset.tags.length">
                      <span
                        class="tag-chip"
                        :key="tag"
                        v-for="tag in asset.tags.slice(0, 3)"
                        v-html="highlightQuery(tag)"
                      ></span>
                      <span
                        class="tag-more"
                        v-if="asset.tags.length > 3"
                      >
                        +{{ asset.tags.length - 3 }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Pagination -->
              <div class="pagination flexrow" v-if="totalPages > 1">
                <button-simple
                  icon="chevron-left"
                  :disabled="currentPage <= 1"
                  @click="goToPage(currentPage - 1)"
                />
                <span
                  class="page-number"
                  :class="{ active: currentPage === p }"
                  :key="p"
                  @click="goToPage(p)"
                  v-for="p in displayedPages"
                >
                  {{ p }}
                </span>
                <button-simple
                  icon="chevron-right"
                  :disabled="currentPage >= totalPages"
                  @click="goToPage(currentPage + 1)"
                />
              </div>
            </template>
          </div>
        </div>

        <!-- Initial state before search -->
        <div class="search-initial" v-else>
          <div class="initial-icon">🔍</div>
          <p>输入关键词搜索全局资产库</p>
          <p class="initial-hint">支持按名称、描述、标签进行全文搜索</p>
        </div>
      </div>
    </template>
  </page-layout>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import AssetSearchBar from '@/components/widgets/AssetSearchBar.vue'
import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import CategoryBadge from '@/components/widgets/CategoryBadge.vue'
import PageLayout from '@/components/layouts/PageLayout.vue'
import PageTitle from '@/components/widgets/PageTitle.vue'
import TableInfo from '@/components/widgets/TableInfo.vue'

export default {
  name: 'asset-search-page',

  components: {
    AssetSearchBar,
    ButtonSimple,
    CategoryBadge,
    PageLayout,
    PageTitle,
    TableInfo
  },

  data() {
    return {
      hasSearched: false,
      sortOptions: [
        { label: '相关性', value: 'relevance' },
        { label: '最新', value: 'newest' },
        { label: '最旧', value: 'oldest' },
        { label: '最多使用', value: 'most_used' },
        { label: '名称', value: 'name' }
      ],
      statusOptions: [
        { label: '草稿', value: 'draft' },
        { label: '已审核', value: 'approved' },
        { label: '已归档', value: 'archived' }
      ]
    }
  },

  mounted() {
    this.loadFacets()
    // Restore search from URL query params
    const q = this.$route.query.q
    if (q) {
      this.$refs.searchBar?.setQuery(q)
      this.restoreFromUrl()
    }
  },

  computed: {
    ...mapGetters([
      'assetSearchResults',
      'assetSearchHits',
      'assetSearchTotalHits',
      'assetSearchQuery',
      'assetSearchFilters',
      'assetSearchSort',
      'assetSearchIsSearching',
      'assetSearchFacets',
      'assetSearchCurrentPage',
      'assetSearchTotalPages',
      'assetSearchActiveFilterCount',
      'globalAssetCategories',
      'categoryTree',
      'getCategoryById',
      'getCategoryBySlug'
    ]),

    searchResults() {
      return this.assetSearchResults
    },
    searchHits() {
      return this.assetSearchHits
    },
    totalHits() {
      return this.assetSearchTotalHits
    },
    searchQuery() {
      return this.assetSearchQuery
    },
    searchFilters() {
      return this.assetSearchFilters
    },
    searchSort() {
      return this.assetSearchSort
    },
    isSearching() {
      return this.assetSearchIsSearching
    },
    facets() {
      return this.assetSearchFacets
    },
    currentPage() {
      return this.assetSearchCurrentPage
    },
    totalPages() {
      return this.assetSearchTotalPages
    },
    activeFilterCount() {
      return this.assetSearchActiveFilterCount
    },

    availableCategories() {
      if (this.categoryTree && this.categoryTree.length) {
        return this.categoryTree
      }
      return this.globalAssetCategories || []
    },

    displayedPages() {
      const pages = []
      const total = this.totalPages
      const current = this.currentPage
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
    }
  },

  methods: {
    ...mapActions([
      'searchAssets',
      'setAssetSearchQuery',
      'setAssetSearchFilters',
      'setAssetSearchSort',
      'setAssetSearchPage',
      'clearAssetSearch',
      'loadFacets'
    ]),

    onSearch(query) {
      this.hasSearched = true
      this.setAssetSearchQuery(query)
      this.updateUrl()
    },

    onSuggestionSelect(asset) {
      this.hasSearched = true
      this.setAssetSearchQuery(asset.name)
      this.updateUrl()
    },

    changeSort(sort) {
      this.setAssetSearchSort(sort)
      this.updateUrl()
    },

    setFilterCategory(slug) {
      this.setAssetSearchFilters({ categorySlug: slug, categoryId: null })
      this.updateUrl()
    },

    setFilterStatus(status) {
      this.setAssetSearchFilters({ status })
      this.updateUrl()
    },

    setFilterCreator(creatorId) {
      this.setAssetSearchFilters({ creatorId })
      this.updateUrl()
    },

    clearFilters() {
      this.setAssetSearchFilters({
        categoryId: null,
        categorySlug: null,
        status: null,
        creatorId: null,
        projectId: null
      })
      this.updateUrl()
    },

    goToPage(page) {
      if (page < 1 || page > this.totalPages) return
      this.setAssetSearchPage(page)
      this.updateUrl()
    },

    selectAsset(asset) {
      this.$router.push({
        name: 'global-asset-library',
        query: { assetId: asset.id }
      })
    },

    getAssetCategoryObject(asset) {
      if (!asset) return null
      if (asset.category_id && this.getCategoryById) {
        const cat = this.getCategoryById(asset.category_id)
        if (cat) return cat
      }
      if (asset.category) {
        const allCats = Object.values(this.$store.getters.categoryMap || {})
        const found = allCats.find((c) => c.slug === asset.category)
        if (found) return found
      }
      const legacy = (this.globalAssetCategories || []).find(
        (c) => c.value === asset.category
      )
      if (legacy) {
        return { name: legacy.label, icon: legacy.icon, color: null }
      }
      return { name: asset.category || '未分类', icon: 'folder', color: null }
    },

    highlightQuery(text) {
      if (!this.searchQuery || !text) return text
      const escaped = this.searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`(${escaped})`, 'gi')
      return text.replace(regex, '<mark>$1</mark>')
    },

    facetTotal(facetKey) {
      const items = this.facets[facetKey]
      if (!items) return 0
      if (Array.isArray(items)) {
        return items.reduce((sum, f) => sum + (f.count || 0), 0)
      }
      return Object.values(items).reduce((sum, c) => sum + c, 0)
    },

    getFacetCount(facetKey, value) {
      const items = this.facets[facetKey]
      if (!items) return 0
      if (Array.isArray(items)) {
        const found = items.find(
          (f) => f.slug === value || f.value === value || f.id === value
        )
        return found ? found.count : 0
      }
      return items[value] || 0
    },

    // URL sync
    updateUrl() {
      const query = {}
      if (this.searchQuery) query.q = this.searchQuery
      if (this.searchFilters.categorySlug)
        query.category = this.searchFilters.categorySlug
      if (this.searchFilters.status) query.status = this.searchFilters.status
      if (this.searchSort && this.searchSort !== 'relevance')
        query.sort = this.searchSort
      if (this.currentPage > 1) query.page = this.currentPage

      this.$router.replace({ query }).catch(() => {})
    },

    restoreFromUrl() {
      const { q, category, status, sort, page } = this.$route.query
      if (q) {
        this.hasSearched = true
        const filters = {}
        if (category) filters.categorySlug = category
        if (status) filters.status = status
        if (Object.keys(filters).length) {
          this.setAssetSearchFilters(filters)
        }
        if (sort) {
          this.setAssetSearchSort(sort)
        }
        this.setAssetSearchQuery(q)
        if (page && parseInt(page) > 1) {
          this.setAssetSearchPage(parseInt(page))
        }
      }
    }
  },

  beforeUnmount() {
    // Don't clear search state — user may navigate back
  },

  head() {
    return {
      title: this.searchQuery
        ? `搜索: ${this.searchQuery} - 资产搜索`
        : '资产搜索 - Kitsu'
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-search-page {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  padding: 4em 2em 1em 2em;
  color: var(--text);
}

.search-header {
  margin-bottom: 1.5em;
}

.search-meta {
  margin-top: 1em;
  align-items: center;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 0.3em;
}

.sort-label {
  font-size: 0.85em;
  color: var(--text-alt);
  margin-right: 0.3em;
}

.sort-option {
  font-size: 0.85em;
  padding: 0.25em 0.6em;
  border-radius: 0.4em;
  cursor: pointer;
  color: var(--text-alt);
  transition: all 0.15s;

  &:hover {
    background: var(--background-hover);
    color: var(--text);
  }

  &.active {
    background: var(--background-selected);
    color: var(--text);
    font-weight: 600;
  }
}

.results-info {
  font-size: 0.85em;
  color: var(--text-alt);
}

.search-time {
  opacity: 0.7;
}

.search-body {
  flex: 1;
  min-height: 0;
  gap: 1.5em;
  align-items: flex-start;
}

/* Filter sidebar */
.filter-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--background);
  border-radius: 0.8em;
  padding: 0.8em;
  border: 1px solid var(--border);
  max-height: calc(100vh - 260px);
  overflow-y: auto;
}

.filter-section {
  margin-bottom: 1.2em;

  &:last-child {
    margin-bottom: 0;
  }
}

.filter-title {
  font-size: 0.8em;
  font-weight: 600;
  color: var(--text-alt);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5em;
}

.filter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4em 0.6em;
  font-size: 0.85em;
  border-radius: 0.4em;
  cursor: pointer;
  color: var(--text);
  transition: background 0.15s;

  &:hover {
    background: var(--background-hover);
  }

  &.active {
    background: var(--background-selected);
    font-weight: 600;
  }
}

.facet-count {
  font-size: 0.8em;
  color: var(--text-alt);
  background: var(--background-alt);
  padding: 0.1em 0.4em;
  border-radius: 0.5em;
  min-width: 1.4em;
  text-align: center;
}

.filter-actions {
  padding-top: 0.8em;
  border-top: 1px solid var(--border);
}

/* Search results */
.search-results {
  min-width: 0;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.result-card {
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
}

.card-body {
  padding: 0.8em;
}

.card-name {
  font-weight: 600;
  font-size: 0.95em;
  margin-bottom: 0.4em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  :deep(mark) {
    background: rgba(var(--background-selected-rgb, 64, 153, 255), 0.25);
    color: inherit;
    border-radius: 2px;
    padding: 0 1px;
  }
}

.card-meta {
  font-size: 0.8em;
  color: var(--text-alt);
  margin-bottom: 0.3em;
  align-items: center;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3em;
  margin-top: 0.4em;
}

.tag-chip {
  background: var(--background-alt);
  padding: 0.1em 0.5em;
  border-radius: 0.8em;
  font-size: 0.75em;
  color: var(--text-alt);

  :deep(mark) {
    background: rgba(var(--background-selected-rgb, 64, 153, 255), 0.25);
    color: inherit;
    border-radius: 2px;
  }
}

.tag-more {
  font-size: 0.75em;
  color: var(--text-alt);
  padding: 0.1em 0.3em;
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
}

/* Pagination */
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

/* Empty / initial states */
.empty-results,
.search-initial {
  text-align: center;
  padding: 4em 2em;
  color: var(--text-alt);
}

.empty-icon,
.initial-icon {
  font-size: 3em;
  margin-bottom: 0.5em;
  opacity: 0.6;
}

.empty-hint,
.initial-hint {
  font-size: 0.85em;
  opacity: 0.7;
  margin-top: 0.3em;
}
</style>
