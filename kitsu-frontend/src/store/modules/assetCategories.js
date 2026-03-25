import assetCategoriesApi from '@/store/api/asset_categories'

/**
 * Build a flat id→category map from a tree structure.
 */
function buildCategoryMap(tree, map = {}) {
  for (const cat of tree) {
    map[cat.id] = cat
    if (cat.children && cat.children.length) {
      buildCategoryMap(cat.children, map)
    }
  }
  return map
}

const state = {
  categoryTree: [],
  categoryMap: {},
  categoryStats: {},
  isCategoriesLoading: false
}

const getters = {
  categoryTree: (state) => state.categoryTree,
  categoryMap: (state) => state.categoryMap,
  categoryStats: (state) => state.categoryStats,
  isCategoriesLoading: (state) => state.isCategoriesLoading,

  getRootCategories: (state) => {
    return state.categoryTree.filter((c) => !c.parent_id)
  },

  getCategoryById: (state) => (id) => {
    return state.categoryMap[id] || null
  },

  getCategoryBySlug: (state) => (slug) => {
    return Object.values(state.categoryMap).find((c) => c.slug === slug) || null
  },

  getChildCategories: (state) => (parentId) => {
    if (!parentId) return state.categoryTree
    const parent = state.categoryMap[parentId]
    return parent && parent.children ? parent.children : []
  }
}

const actions = {
  async loadCategoryTree({ commit }) {
    commit('SET_CATEGORIES_LOADING', true)
    try {
      const tree = await assetCategoriesApi.getCategoryTree()
      const data = Array.isArray(tree) ? tree : tree.data || []
      commit('SET_CATEGORY_TREE', data)
      commit('SET_CATEGORY_MAP', buildCategoryMap(data))
    } catch (err) {
      console.error('Failed to load category tree:', err)
    } finally {
      commit('SET_CATEGORIES_LOADING', false)
    }
  },

  async createCategory({ dispatch }, data) {
    const category = await assetCategoriesApi.createCategory(data)
    await dispatch('loadCategoryTree')
    return category
  },

  async updateCategory({ dispatch }, { categoryId, data }) {
    const updated = await assetCategoriesApi.updateCategory(categoryId, data)
    await dispatch('loadCategoryTree')
    return updated
  },

  async deleteCategory({ dispatch }, categoryId) {
    await assetCategoriesApi.deleteCategory(categoryId)
    await dispatch('loadCategoryTree')
  },

  async reorderCategories({ dispatch }, orders) {
    await assetCategoriesApi.reorderCategories(orders)
    await dispatch('loadCategoryTree')
  },

  async loadCategoryStats({ commit }) {
    try {
      const stats = await assetCategoriesApi.getCategoryStats()
      commit('SET_CATEGORY_STATS', stats)
    } catch (err) {
      console.error('Failed to load category stats:', err)
    }
  },

  async initDefaults({ dispatch }) {
    await assetCategoriesApi.initDefaultCategories()
    await dispatch('loadCategoryTree')
  }
}

const mutations = {
  SET_CATEGORY_TREE(state, tree) {
    state.categoryTree = tree
  },

  SET_CATEGORY_MAP(state, map) {
    state.categoryMap = map
  },

  SET_CATEGORY_STATS(state, stats) {
    state.categoryStats = stats
  },

  SET_CATEGORIES_LOADING(state, val) {
    state.isCategoriesLoading = val
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
