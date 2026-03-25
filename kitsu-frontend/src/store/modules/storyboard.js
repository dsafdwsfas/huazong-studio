import client from '@/store/api/client'

const state = {
  sequences: [],
  totalShots: 0,
  isLoading: false,
  taskStatuses: [],
  filters: {
    status: '',
    assignee: '',
    sequenceId: '',
    episodeId: ''
  }
}

const getters = {
  storyboardSequences: (state) => state.sequences,
  storyboardTotalShots: (state) => state.totalShots,
  storyboardIsLoading: (state) => state.isLoading,
  storyboardTaskStatuses: (state) => state.taskStatuses
}

const actions = {
  async loadStoryboard({ commit, state }, { projectId, episodeId }) {
    commit('SET_STORYBOARD_LOADING', true)
    try {
      let url = `/api/data/projects/${projectId}/storyboard`
      const params = new URLSearchParams()
      if (episodeId) params.append('episode_id', episodeId)
      if (state.filters.status) params.append('status', state.filters.status)
      if (state.filters.assignee) {
        params.append('assigned_to', state.filters.assignee)
      }
      if (state.filters.sequenceId) {
        params.append('sequence_id', state.filters.sequenceId)
      }
      const query = params.toString()
      if (query) url += `?${query}`

      const data = await client.pget(url)
      commit('SET_STORYBOARD_DATA', data)
    } catch (err) {
      console.error('Failed to load storyboard:', err)
    } finally {
      commit('SET_STORYBOARD_LOADING', false)
    }
  },

  async loadTaskStatuses({ commit }, { projectId }) {
    try {
      const statuses = await client.pget(
        `/api/data/projects/${projectId}/storyboard/task-statuses`
      )
      commit('SET_STORYBOARD_TASK_STATUSES', statuses)
    } catch (err) {
      console.error('Failed to load task statuses:', err)
    }
  },

  async assignShot({ commit }, { projectId, shotId, personIds, taskId }) {
    const payload = { person_ids: personIds }
    if (taskId) payload.task_id = taskId
    const result = await client.pput(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/assign`,
      payload
    )
    commit('UPDATE_SHOT_ASSIGNEES', {
      shotId,
      assignees: result.assignees
    })
    return result
  },

  async updateShotStatus(
    { commit },
    { projectId, shotId, taskStatusId, taskId }
  ) {
    const payload = { task_status_id: taskStatusId }
    if (taskId) payload.task_id = taskId
    const result = await client.pput(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/status`,
      payload
    )
    commit('UPDATE_SHOT_TASK_STATUS', {
      shotId,
      taskStatusId: result.new_status_id,
      taskStatusName: result.task_status_name,
      taskStatusColor: result.task_status_color
    })
    return result
  },

  async batchAssignShots(_context, { projectId, shotIds, personIds }) {
    return await client.pput(
      `/api/data/projects/${projectId}/storyboard/batch-assign`,
      { shot_ids: shotIds, person_ids: personIds }
    )
  },

  async reorderShots(_context, { projectId, shotOrders }) {
    await client.pput(`/api/data/projects/${projectId}/storyboard/reorder`, {
      shot_orders: shotOrders
    })
  },

  async batchUpdateStatus(_context, { projectId, shotIds, taskStatusId }) {
    return await client.pput(
      `/api/data/projects/${projectId}/storyboard/batch-status`,
      { shot_ids: shotIds, task_status_id: taskStatusId }
    )
  },

  async batchDeleteShots(_context, { projectId, shotIds, hardDelete }) {
    return await client.pput(
      `/api/data/projects/${projectId}/storyboard/batch-delete`,
      { shot_ids: shotIds, hard_delete: hardDelete || false }
    )
  },

  async reorderSequences(_context, { projectId, sequenceOrders }) {
    await client.pput(
      `/api/data/projects/${projectId}/storyboard/reorder-sequences`,
      { sequence_orders: sequenceOrders }
    )
  },

  async createSequence({ dispatch }, { projectId, episodeId, name, description }) {
    const result = await client.ppost(
      `/api/data/projects/${projectId}/storyboard/sequences`,
      { name, description: description || '', episode_id: episodeId || null }
    )
    // Reload to get the new sequence in context
    await dispatch('loadStoryboard', { projectId, episodeId })
    return result
  },

  async updateSequence({ commit }, { projectId, sequenceId, name, description }) {
    const result = await client.pput(
      `/api/data/projects/${projectId}/storyboard/sequences/${sequenceId}`,
      { name, description }
    )
    commit('UPDATE_SEQUENCE_INFO', { sequenceId, name: result.name, description: result.description })
    return result
  },

  async deleteSequence({ dispatch }, { projectId, episodeId, sequenceId }) {
    await client.pdel(
      `/api/data/projects/${projectId}/storyboard/sequences/${sequenceId}`
    )
    await dispatch('loadStoryboard', { projectId, episodeId })
  },

  async loadShotVersions(_context, { projectId, shotId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/versions`
    )
  },

  async createShotVersion(_context, { projectId, shotId, name, extension }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/versions/upload`,
      { name, extension: extension || 'png', set_as_current: true }
    )
  },

  async setShotVersionActive(
    { commit },
    { projectId, shotId, previewFileId }
  ) {
    const result = await client.pput(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/versions/set-active`,
      { preview_file_id: previewFileId }
    )
    commit('UPDATE_SHOT_PREVIEW', { shotId, previewFileId })
    return result
  },

  async updateShotTiming({ commit }, { projectId, shotId, timing }) {
    const result = await client.pput(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/timing`,
      timing
    )
    commit('UPDATE_SHOT_TIMING', { shotId, ...timing })
    return result
  },

  async batchUpdateTiming({ commit }, { projectId, shots }) {
    const result = await client.pput(
      `/api/data/projects/${projectId}/storyboard/batch-timing`,
      { shots }
    )
    for (const s of shots) {
      commit('UPDATE_SHOT_TIMING', {
        shotId: s.shot_id,
        nb_frames: s.nb_frames,
        frame_in: s.frame_in,
        frame_out: s.frame_out
      })
    }
    return result
  },

  async loadFrameAnnotations(_context, { shotId }) {
    return await client.pget(
      `/api/data/shots/${shotId}/annotations/frames`
    )
  },

  async saveFrameAnnotation(_context, { shotId, frame, time, drawing }) {
    return await client.pput(
      `/api/data/shots/${shotId}/annotations/frames/${frame}`,
      { drawing, time }
    )
  },

  async deleteFrameAnnotation(_context, { shotId, frame }) {
    return await client.pdel(
      `/api/data/shots/${shotId}/annotations/frames/${frame}`
    )
  },

  async loadAudioMarkers(_context, { shotId }) {
    return await client.pget(
      `/api/data/shots/${shotId}/annotations/audio-markers`
    )
  },

  async addAudioMarker(_context, { shotId, time, label, type, color }) {
    return await client.ppost(
      `/api/data/shots/${shotId}/annotations/audio-markers`,
      { time, label, type: type || 'marker', color }
    )
  },

  async updateAudioMarker(_context, { shotId, markerIndex, time, label, type, color }) {
    const payload = {}
    if (time !== undefined) payload.time = time
    if (label !== undefined) payload.label = label
    if (type !== undefined) payload.type = type
    if (color !== undefined) payload.color = color
    return await client.pput(
      `/api/data/shots/${shotId}/annotations/audio-markers/${markerIndex}`,
      payload
    )
  },

  async deleteAudioMarker(_context, { shotId, markerIndex }) {
    return await client.pdel(
      `/api/data/shots/${shotId}/annotations/audio-markers/${markerIndex}`
    )
  },

  async loadShotReviews(_context, { projectId, shotId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/reviews`
    )
  },

  async submitReview(_context, { projectId, shotId, action, text, taskId }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/reviews`,
      { action, text, task_id: taskId }
    )
  },

  async loadReviewStatuses(_context, { projectId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/review-statuses`
    )
  },

  async analyzeShot({ commit }, { projectId, shotId }) {
    commit('SET_SHOT_ANALYSIS_STATUS', { shotId, status: 'pending' })
    try {
      const result = await client.ppost(
        `/api/data/projects/${projectId}/storyboard/shots/${shotId}/analyze`
      )
      commit('SET_SHOT_ANALYSIS', { shotId, analysis: result })
      return result
    } catch (err) {
      commit('SET_SHOT_ANALYSIS_STATUS', { shotId, status: 'error' })
      throw err
    }
  },

  async loadShotAnalysis(_context, { projectId, shotId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/analysis`
    )
  },

  // Style lock (3.4)
  async getStyleLock(_context, { projectId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/style-lock`
    )
  },

  async lockStyle(_context, { projectId, style, referenceImageIds }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/style-lock`,
      { style, reference_image_ids: referenceImageIds }
    )
  },

  async unlockStyle(_context, { projectId }) {
    return await client.pdel(
      `/api/data/projects/${projectId}/storyboard/style-lock`
    )
  },

  async getStyleReferences(_context, { projectId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/style-references`
    )
  },

  async addStyleReference(_context, { projectId, previewFileId }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/style-references`,
      { preview_file_id: previewFileId }
    )
  },

  // Style templates (3.5)
  async listStyleTemplates(_context, { projectId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/style-templates`
    )
  },

  async createStyleTemplate(_context, { projectId, name, description, style, thumbnailId, tags, isShared }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/style-templates`,
      { name, description, style, thumbnail_preview_file_id: thumbnailId, tags, is_shared: isShared || false }
    )
  },

  async updateStyleTemplate(_context, { projectId, templateId, name, description, tags, isShared }) {
    const payload = {}
    if (name !== undefined) payload.name = name
    if (description !== undefined) payload.description = description
    if (tags !== undefined) payload.tags = tags
    if (isShared !== undefined) payload.is_shared = isShared
    return await client.pput(
      `/api/data/projects/${projectId}/storyboard/style-templates/${templateId}`,
      payload
    )
  },

  async deleteStyleTemplate(_context, { projectId, templateId }) {
    return await client.pdel(
      `/api/data/projects/${projectId}/storyboard/style-templates/${templateId}`
    )
  },

  // Prompt library (3.6)
  async listPrompts(_context, { projectId, category, tag, search }) {
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (tag) params.append('tag', tag)
    if (search) params.append('search', search)
    const q = params.toString()
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/prompts${q ? '?' + q : ''}`
    )
  },

  async createPrompt(_context, { projectId, title, content, contentCn, category, tags }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/prompts`,
      { title, content, content_cn: contentCn, category, tags }
    )
  },

  async updatePrompt(_context, { projectId, promptId, title, content, contentCn, category, tags }) {
    const payload = {}
    if (title !== undefined) payload.title = title
    if (content !== undefined) payload.content = content
    if (contentCn !== undefined) payload.content_cn = contentCn
    if (category !== undefined) payload.category = category
    if (tags !== undefined) payload.tags = tags
    return await client.pput(
      `/api/data/projects/${projectId}/storyboard/prompts/${promptId}`,
      payload
    )
  },

  async deletePrompt(_context, { projectId, promptId }) {
    return await client.pdel(
      `/api/data/projects/${projectId}/storyboard/prompts/${promptId}`
    )
  },

  async getPromptDetail(_context, { projectId, promptId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/prompts/${promptId}`
    )
  },

  async togglePromptFavorite(_context, { projectId, promptId }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/prompts/${promptId}/favorite`
    )
  },

  async revertPrompt(_context, { projectId, promptId, version }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/prompts/${promptId}/revert`,
      { version }
    )
  },

  // Camera language (3.7)
  async listCameraTerms(_context, { projectId, category, search }) {
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (search) params.append('search', search)
    const q = params.toString()
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/camera-language${q ? '?' + q : ''}`
    )
  },

  async createCameraTerm(_context, { projectId, termCn, termEn, category, description, exampleUsage, tags }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/camera-language`,
      { term_cn: termCn, term_en: termEn, category, description, example_usage: exampleUsage, tags }
    )
  },

  async updateCameraTerm(_context, { projectId, termId, ...data }) {
    return await client.pput(
      `/api/data/projects/${projectId}/storyboard/camera-language/${termId}`,
      data
    )
  },

  async deleteCameraTerm(_context, { projectId, termId }) {
    return await client.pdel(
      `/api/data/projects/${projectId}/storyboard/camera-language/${termId}`
    )
  },

  async initCameraTerms(_context, { projectId }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/camera-language/init`
    )
  },

  async applyStyleTemplate(_context, { projectId, templateId }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/style-templates/${templateId}/apply`
    )
  },

  async removeStyleReference(_context, { projectId, previewFileId }) {
    return await client.pdel(
      `/api/data/projects/${projectId}/storyboard/style-references/${previewFileId}`
    )
  },

  async translateKeywords(_context, { projectId, keywords, direction }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/translate-keywords`,
      { keywords, direction: direction || 'en_to_cn' }
    )
  },

  async exportStyleReport(_context, { projectId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/style-report`
    )
  },

  async checkStyleConsistency(_context, { projectId, shotId }) {
    return await client.pget(
      `/api/data/projects/${projectId}/storyboard/shots/${shotId}/consistency`
    )
  },

  async batchAnalyzeShots(_context, { projectId, shotIds }) {
    return await client.ppost(
      `/api/data/projects/${projectId}/storyboard/batch-analyze`,
      { shot_ids: shotIds }
    )
  },

  setStoryboardFilter({ commit }, { key, value }) {
    commit('SET_STORYBOARD_FILTER', { key, value })
  }
}

const mutations = {
  SET_STORYBOARD_DATA(state, data) {
    state.sequences = data.sequences || []
    state.totalShots = data.total_shots || 0
  },

  SET_STORYBOARD_LOADING(state, val) {
    state.isLoading = val
  },

  SET_STORYBOARD_FILTER(state, { key, value }) {
    state.filters[key] = value
  },

  SET_STORYBOARD_TASK_STATUSES(state, statuses) {
    state.taskStatuses = statuses || []
  },

  UPDATE_SHOT_ASSIGNEES(state, { shotId, assignees }) {
    for (const seq of state.sequences) {
      const shot = seq.shots.find((s) => s.id === shotId)
      if (shot) {
        shot.assignees = assignees
        break
      }
    }
  },

  UPDATE_SHOT_PREVIEW(state, { shotId, previewFileId }) {
    for (const seq of state.sequences) {
      const shot = seq.shots.find((s) => s.id === shotId)
      if (shot) {
        shot.preview_file_id = previewFileId
        break
      }
    }
  },

  UPDATE_SEQUENCE_INFO(state, { sequenceId, name, description }) {
    const seq = state.sequences.find((s) => s.id === sequenceId)
    if (seq) {
      if (name !== undefined) seq.name = name
      if (description !== undefined) seq.description = description
    }
  },

  REORDER_SEQUENCES(state, sequenceOrders) {
    const orderMap = {}
    for (const item of sequenceOrders) {
      orderMap[item.sequence_id] = item.order
    }
    for (const seq of state.sequences) {
      if (orderMap[seq.id] !== undefined) {
        seq.sequence_order = orderMap[seq.id]
      }
    }
    state.sequences.sort(
      (a, b) => (a.sequence_order || 0) - (b.sequence_order || 0) || a.name.localeCompare(b.name)
    )
  },

  UPDATE_SHOT_TASK_STATUS(
    state,
    { shotId, taskStatusId, taskStatusName, taskStatusColor }
  ) {
    for (const seq of state.sequences) {
      const shot = seq.shots.find((s) => s.id === shotId)
      if (shot && shot.primary_task) {
        shot.primary_task.task_status_id = taskStatusId
        shot.primary_task.task_status_name = taskStatusName
        shot.primary_task.task_status_color = taskStatusColor
        break
      }
    }
  },

  SET_SHOT_ANALYSIS_STATUS(state, { shotId, status }) {
    for (const seq of state.sequences) {
      const shot = seq.shots.find((s) => s.id === shotId)
      if (shot) {
        if (!shot.ai_analysis) shot.ai_analysis = {}
        shot.ai_analysis.status = status
        break
      }
    }
  },

  SET_SHOT_ANALYSIS(state, { shotId, analysis }) {
    for (const seq of state.sequences) {
      const shot = seq.shots.find((s) => s.id === shotId)
      if (shot) {
        shot.ai_analysis = analysis
        break
      }
    }
  },

  UPDATE_SHOT_TIMING(state, { shotId, nb_frames, frame_in, frame_out }) {
    for (const seq of state.sequences) {
      const shot = seq.shots.find((s) => s.id === shotId)
      if (shot) {
        if (nb_frames !== undefined) shot.nb_frames = nb_frames
        if (frame_in !== undefined) shot.frame_in = frame_in
        if (frame_out !== undefined) shot.frame_out = frame_out
        break
      }
    }
  }
}

export default {
  state,
  getters,
  actions,
  mutations
}
