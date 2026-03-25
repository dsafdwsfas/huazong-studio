import assetSearchApi from '@/store/api/asset_search'

let suggestionsTimeout = null

const state = {
  searchResults: {
    hits: [],
    totalHits: 0,
    page: 1,
    perPage: 20,
    processingTimeMs: 0
  },
  searchQuery: '',
  searchFilters: {
    categoryId: null,
    categorySlug: null,
    status: null,
    creatorId: null,
    projectId: null
  },
  searchSort: 'relevance',
  suggestions: [],
  facets: {},
  isSearching: false,
  similarAssets: []
}

const getters = {
  assetSearchResults: (state) => state.searchResults,
  assetSearchHits: (state) => state.searchResults.hits,
  assetSearchTotalHits: (state) => state.searchResults.totalHits,
  assetSearchQuery: (state) => state.searchQuery,
  assetSearchFilters: (state) => state.searchFilters,
  assetSearchSort: (state) => state.searchSort,
  assetSearchSuggestions: (state) => state.suggestions,
  assetSearchFacets: (state) => state.facets,
  assetSearchIsSearching: (state) => state.isSearching,
  assetSimilarAssets: (state) => state.similarAssets,

  assetSearchCurrentPage: (state) => state.searchResults.page,
  assetSearchTotalPages: (state) => {
    const { totalHits, perPage } = state.searchResults
    if (!totalHits || !perPage) return 1
    return Math.ceil(totalHits / perPage)
  },

  assetSearchHasResults: (state) => state.searchResults.hits.length > 0,

  assetSearchActiveFilterCount: (state) => {
    let count = 0
    if (state.searchFilters.categoryId || state.searchFilters.categorySlug)
      count++
    if (state.searchFilters.status) count++
    if (state.searchFilters.creatorId) count++
    if (state.searchFilters.projectId) count++
    return count
  }
}

const actions = {
  async searchAssets({ commit, state }) {
    commit('SET_ASSET_SEARCH_LOADING', true)
    try {
      const params = {
        q: state.searchQuery,
        categoryId: state.searchFilters.categoryId,
        categorySlug: state.searchFilters.categorySlug,
        status: state.searchFilters.status,
        creatorId: state.searchFilters.creatorId,
        projectId: state.searchFilters.projectId,
        sort: state.searchSort,
        page: state.searchResults.page,
        perPage: state.searchResults.perPage
      }
      const data = await assetSearchApi.search(params)
      commit('SET_ASSET_SEARCH_RESULTS', data)
    } catch (err) {
      console.error('Asset search failed:', err)
      commit('SET_ASSET_SEARCH_RESULTS', {
        hits: [],
        total_hits: 0,
        page: 1,
        per_page: 20,
        processing_time_ms: 0
      })
    } finally {
      commit('SET_ASSET_SEARCH_LOADING', false)
    }
  },

  loadSuggestions({ commit }, partialQuery) {
    if (suggestionsTimeout) {
      clearTimeout(suggestionsTimeout)
    }
    if (!partialQuery || partialQuery.length < 2) {
      commit('SET_ASSET_SEARCH_SUGGESTIONS', [])
      return
    }
    suggestionsTimeout = setTimeout(async () => {
      try {
        const data = await assetSearchApi.getSuggestions(partialQuery)
        commit('SET_ASSET_SEARCH_SUGGESTIONS', data)
      } catch (err) {
        console.error('Failed to load suggestions:', err)
        commit('SET_ASSET_SEARCH_SUGGESTIONS', [])
      }
    }, 300)
  },

  async loadFacets({ commit }) {
    try {
      const data = await assetSearchApi.getFacets()
      commit('SET_ASSET_SEARCH_FACETS', data)
    } catch (err) {
      console.error('Failed to load facets:', err)
    }
  },

  async loadSimilarAssets({ commit }, assetId) {
    try {
      const data = await assetSearchApi.getSimilar(assetId)
      commit('SET_SIMILAR_ASSETS', data)
    } catch (err) {
      console.error('Failed to load similar assets:', err)
      commit('SET_SIMILAR_ASSETS', [])
    }
  },

  setAssetSearchQuery({ commit, dispatch }, q) {
    commit('SET_ASSET_SEARCH_QUERY', q)
    commit('SET_ASSET_SEARCH_PAGE', 1)
    if (q) {
      dispatch('searchAssets')
    }
  },

  setAssetSearchFilters({ commit, dispatch }, filters) {
    commit('SET_ASSET_SEARCH_FILTERS', filters)
    commit('SET_ASSET_SEARCH_PAGE', 1)
    dispatch('searchAssets')
  },

  setAssetSearchSort({ commit, dispatch }, sort) {
    commit('SET_ASSET_SEARCH_SORT', sort)
    commit('SET_ASSET_SEARCH_PAGE', 1)
    dispatch('searchAssets')
  },

  setAssetSearchPage({ commit, dispatch }, page) {
    commit('SET_ASSET_SEARCH_PAGE', page)
    dispatch('searchAssets')
  },

  clearAssetSearch({ commit }) {
    commit('SET_ASSET_SEARCH_QUERY', '')
    commit('SET_ASSET_SEARCH_FILTERS', {
      categoryId: null,
      categorySlug: null,
      status: null,
      creatorId: null,
      projectId: null
    })
    commit('SET_ASSET_SEARCH_SORT', 'relevance')
    commit('SET_ASSET_SEARCH_RESULTS', {
      hits: [],
      total_hits: 0,
      page: 1,
      per_page: 20,
      processing_time_ms: 0
    })
    commit('SET_ASSET_SEARCH_SUGGESTIONS', [])
    commit('SET_SIMILAR_ASSETS', [])
  }
}

const mutations = {
  SET_ASSET_SEARCH_RESULTS(state, data) {
    state.searchResults = {
      hits: data.hits || data.data || [],
      totalHits: data.total_hits ?? data.totalHits ?? 0,
      page: data.page || 1,
      perPage: data.per_page ?? data.perPage ?? 20,
      processingTimeMs: data.processing_time_ms ?? data.processingTimeMs ?? 0
    }
  },

  SET_ASSET_SEARCH_QUERY(state, q) {
    state.searchQuery = q
  },

  SET_ASSET_SEARCH_FILTERS(state, filters) {
    state.searchFilters = { ...state.searchFilters, ...filters }
  },

  SET_ASSET_SEARCH_SORT(state, sort) {
    state.searchSort = sort
  },

  SET_ASSET_SEARCH_PAGE(state, page) {
    state.searchResults.page = page
  },

  SET_ASSET_SEARCH_LOADING(state, val) {
    state.isSearching = val
  },

  SET_ASSET_SEARCH_SUGGESTIONS(state, suggestions) {
    state.suggestions = suggestions || []
  },

  SET_ASSET_SEARCH_FACETS(state, facets) {
    state.facets = facets || {}
  },

  SET_SIMILAR_ASSETS(state, assets) {
    state.similarAssets = assets || []
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
