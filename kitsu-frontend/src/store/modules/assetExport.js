import assetExportApi from '@/store/api/asset_export'

/**
 * Trigger a browser download from a Blob.
 */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function defaultFilename() {
  const d = new Date()
  const ts = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}_${String(d.getHours()).padStart(2, '0')}${String(d.getMinutes()).padStart(2, '0')}`
  return `global-assets-${ts}.zip`
}

const state = {
  exportProgress: { status: 'idle', message: '' },
  importProgress: { status: 'idle', message: '', result: null },
  importPreview: null,
  importResult: null
}

const getters = {
  assetExportProgress: (state) => state.exportProgress,
  assetImportProgress: (state) => state.importProgress,
  assetImportPreview: (state) => state.importPreview,
  assetImportResult: (state) => state.importResult
}

const actions = {
  // ── Export ────────────────────────────────────────────────

  async exportSelectedAssets({ commit }, { assetIds, options = {} }) {
    commit('SET_EXPORT_PROGRESS', { status: 'exporting', message: '正在导出选中资产...' })
    try {
      const blob = await assetExportApi.exportAssets(assetIds, options)
      downloadBlob(blob, defaultFilename())
      commit('SET_EXPORT_PROGRESS', { status: 'done', message: '导出完成' })
    } catch (err) {
      commit('SET_EXPORT_PROGRESS', {
        status: 'error',
        message: err?.body?.message || '导出失败'
      })
      throw err
    }
  },

  async exportAllAssets({ commit }, options = {}) {
    commit('SET_EXPORT_PROGRESS', { status: 'exporting', message: '正在导出全部资产...' })
    try {
      const blob = await assetExportApi.exportAll(options)
      downloadBlob(blob, defaultFilename())
      commit('SET_EXPORT_PROGRESS', { status: 'done', message: '导出完成' })
    } catch (err) {
      commit('SET_EXPORT_PROGRESS', {
        status: 'error',
        message: err?.body?.message || '导出失败'
      })
      throw err
    }
  },

  async exportByCategory({ commit }, { categoryId, options = {} }) {
    commit('SET_EXPORT_PROGRESS', { status: 'exporting', message: '正在导出分类资产...' })
    try {
      const blob = await assetExportApi.exportByCategory(categoryId, options)
      downloadBlob(blob, defaultFilename())
      commit('SET_EXPORT_PROGRESS', { status: 'done', message: '导出完成' })
    } catch (err) {
      commit('SET_EXPORT_PROGRESS', {
        status: 'error',
        message: err?.body?.message || '导出失败'
      })
      throw err
    }
  },

  async exportByProject({ commit }, { projectId, options = {} }) {
    commit('SET_EXPORT_PROGRESS', { status: 'exporting', message: '正在按项目导出资产...' })
    try {
      const blob = await assetExportApi.exportByProject(projectId, options)
      downloadBlob(blob, defaultFilename())
      commit('SET_EXPORT_PROGRESS', { status: 'done', message: '导出完成' })
    } catch (err) {
      commit('SET_EXPORT_PROGRESS', {
        status: 'error',
        message: err?.body?.message || '导出失败'
      })
      throw err
    }
  },

  // ── Import ───────────────────────────────────────────────

  async validateImportFile({ commit }, file) {
    commit('SET_IMPORT_PROGRESS', { status: 'validating', message: '正在验证文件...' })
    commit('SET_IMPORT_PREVIEW', null)
    try {
      const preview = await assetExportApi.validateImport(file)
      commit('SET_IMPORT_PREVIEW', preview)
      commit('SET_IMPORT_PROGRESS', { status: 'previewing', message: '验证通过' })
      return preview
    } catch (err) {
      commit('SET_IMPORT_PROGRESS', {
        status: 'error',
        message: err?.body?.message || '文件验证失败'
      })
      throw err
    }
  },

  async executeImport({ commit, dispatch }, { file, mode }) {
    commit('SET_IMPORT_PROGRESS', { status: 'importing', message: '正在导入...' })
    try {
      const result = await assetExportApi.importAssets(file, mode)
      commit('SET_IMPORT_RESULT', result)
      commit('SET_IMPORT_PROGRESS', { status: 'done', message: '导入完成' })
      // Refresh the asset list
      dispatch('loadGlobalAssets')
      return result
    } catch (err) {
      commit('SET_IMPORT_PROGRESS', {
        status: 'error',
        message: err?.body?.message || '导入失败'
      })
      throw err
    }
  },

  async importFromJson({ commit, dispatch }, assets) {
    commit('SET_IMPORT_PROGRESS', { status: 'importing', message: '正在导入 JSON 数据...' })
    try {
      const result = await assetExportApi.importJson(assets)
      commit('SET_IMPORT_RESULT', result)
      commit('SET_IMPORT_PROGRESS', { status: 'done', message: 'JSON 导入完成' })
      dispatch('loadGlobalAssets')
      return result
    } catch (err) {
      commit('SET_IMPORT_PROGRESS', {
        status: 'error',
        message: err?.body?.message || 'JSON 导入失败'
      })
      throw err
    }
  },

  clearImportState({ commit }) {
    commit('SET_IMPORT_PROGRESS', { status: 'idle', message: '' })
    commit('SET_IMPORT_PREVIEW', null)
    commit('SET_IMPORT_RESULT', null)
  },

  clearExportState({ commit }) {
    commit('SET_EXPORT_PROGRESS', { status: 'idle', message: '' })
  }
}

const mutations = {
  SET_EXPORT_PROGRESS(state, progress) {
    state.exportProgress = progress
  },
  SET_IMPORT_PROGRESS(state, progress) {
    state.importProgress = progress
  },
  SET_IMPORT_PREVIEW(state, preview) {
    state.importPreview = preview
  },
  SET_IMPORT_RESULT(state, result) {
    state.importResult = result
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
