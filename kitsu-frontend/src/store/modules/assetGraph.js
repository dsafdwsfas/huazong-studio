import assetGraphApi from '@/store/api/asset_graph'

let positionSaveTimer = null

const state = {
  graphData: { nodes: [], links: [] },
  graphStats: {},
  selectedNode: null,
  graphDepth: 2,
  isGraphLoading: false,
  graphViewMode: 'global', // 'global' | 'asset' | 'project'
  filterNodeTypes: [],
  filterLinkTypes: []
}

const getters = {
  assetGraphData: (state) => state.graphData,
  assetGraphStats: (state) => state.graphStats,
  assetGraphSelectedNode: (state) => state.selectedNode,
  assetGraphDepth: (state) => state.graphDepth,
  isAssetGraphLoading: (state) => state.isGraphLoading,
  assetGraphViewMode: (state) => state.graphViewMode,
  assetGraphFilterNodeTypes: (state) => state.filterNodeTypes,
  assetGraphFilterLinkTypes: (state) => state.filterLinkTypes,

  assetGraphNodeCount: (state) => state.graphData.nodes.length,
  assetGraphLinkCount: (state) => state.graphData.links.length,

  assetGraphNodesByType: (state) => {
    const grouped = {}
    for (const node of state.graphData.nodes) {
      const t = node.node_type || 'unknown'
      if (!grouped[t]) grouped[t] = []
      grouped[t].push(node)
    }
    return grouped
  },

  assetGraphLinksByType: (state) => {
    const grouped = {}
    for (const link of state.graphData.links) {
      const t = link.link_type || 'unknown'
      if (!grouped[t]) grouped[t] = []
      grouped[t].push(link)
    }
    return grouped
  },

  selectedNodeLinks: (state) => {
    if (!state.selectedNode) return []
    const nodeId = state.selectedNode.id
    return state.graphData.links.filter(
      (l) => l.source_node_id === nodeId || l.target_node_id === nodeId
    )
  }
}

const actions = {
  async loadGlobalGraph({ commit, state }) {
    commit('SET_GRAPH_LOADING', true)
    try {
      const params = { depth: state.graphDepth }
      if (state.filterNodeTypes.length) {
        params.nodeTypes = state.filterNodeTypes.join(',')
      }
      if (state.filterLinkTypes.length) {
        params.linkTypes = state.filterLinkTypes.join(',')
      }
      const data = await assetGraphApi.getGraph(params)
      commit('SET_GRAPH_DATA', data)
      commit('SET_GRAPH_VIEW_MODE', 'global')
    } catch (err) {
      console.error('Failed to load global graph:', err)
    } finally {
      commit('SET_GRAPH_LOADING', false)
    }
  },

  async loadAssetGraph({ commit, state }, assetId) {
    commit('SET_GRAPH_LOADING', true)
    try {
      const data = await assetGraphApi.getAssetGraph(assetId, state.graphDepth)
      commit('SET_GRAPH_DATA', data)
      commit('SET_GRAPH_VIEW_MODE', 'asset')
    } catch (err) {
      console.error('Failed to load asset graph:', err)
    } finally {
      commit('SET_GRAPH_LOADING', false)
    }
  },

  async loadProjectGraph({ commit }, projectId) {
    commit('SET_GRAPH_LOADING', true)
    try {
      const data = await assetGraphApi.getProjectGraph(projectId)
      commit('SET_GRAPH_DATA', data)
      commit('SET_GRAPH_VIEW_MODE', 'project')
    } catch (err) {
      console.error('Failed to load project graph:', err)
    } finally {
      commit('SET_GRAPH_LOADING', false)
    }
  },

  selectNode({ commit }, node) {
    commit('SET_SELECTED_NODE', node)
  },

  saveNodePosition(_context, { nodeId, x, y }) {
    if (positionSaveTimer) clearTimeout(positionSaveTimer)
    positionSaveTimer = setTimeout(async () => {
      try {
        await assetGraphApi.updateNodePosition(nodeId, x, y)
      } catch (err) {
        console.error('Failed to save node position:', err)
      }
    }, 500)
  },

  async createManualLink({ dispatch }, data) {
    try {
      await assetGraphApi.createLink(data)
      await dispatch('loadGlobalGraph')
    } catch (err) {
      console.error('Failed to create link:', err)
      throw err
    }
  },

  async deleteLink({ dispatch }, linkId) {
    try {
      await assetGraphApi.deleteLink(linkId)
      await dispatch('loadGlobalGraph')
    } catch (err) {
      console.error('Failed to delete link:', err)
      throw err
    }
  },

  async triggerAutoLink({ dispatch }, assetId) {
    try {
      const result = await assetGraphApi.autoLinkAsset(assetId)
      await dispatch('loadGlobalGraph')
      return result
    } catch (err) {
      console.error('Failed to trigger auto-link:', err)
      throw err
    }
  },

  async rebuildGraph({ dispatch }, projectId) {
    try {
      const result = await assetGraphApi.rebuildProjectGraph(projectId)
      await dispatch('loadProjectGraph', projectId)
      return result
    } catch (err) {
      console.error('Failed to rebuild graph:', err)
      throw err
    }
  },

  async loadGraphStats({ commit }) {
    try {
      const stats = await assetGraphApi.getGraphStats()
      commit('SET_GRAPH_STATS', stats)
    } catch (err) {
      console.error('Failed to load graph stats:', err)
    }
  },

  setGraphDepth({ commit, dispatch }, depth) {
    commit('SET_GRAPH_DEPTH', depth)
    dispatch('loadGlobalGraph')
  },

  setGraphFilters({ commit, dispatch }, { nodeTypes, linkTypes }) {
    if (nodeTypes !== undefined) commit('SET_FILTER_NODE_TYPES', nodeTypes)
    if (linkTypes !== undefined) commit('SET_FILTER_LINK_TYPES', linkTypes)
    dispatch('loadGlobalGraph')
  }
}

const mutations = {
  SET_GRAPH_DATA(state, data) {
    state.graphData = {
      nodes: data.nodes || [],
      links: data.links || []
    }
  },

  SET_GRAPH_STATS(state, stats) {
    state.graphStats = stats
  },

  SET_SELECTED_NODE(state, node) {
    state.selectedNode = node
  },

  SET_GRAPH_LOADING(state, val) {
    state.isGraphLoading = val
  },

  SET_GRAPH_VIEW_MODE(state, mode) {
    state.graphViewMode = mode
  },

  SET_GRAPH_DEPTH(state, depth) {
    state.graphDepth = depth
  },

  SET_FILTER_NODE_TYPES(state, types) {
    state.filterNodeTypes = types
  },

  SET_FILTER_LINK_TYPES(state, types) {
    state.filterLinkTypes = types
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
