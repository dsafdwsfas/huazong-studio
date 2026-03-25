import client from '@/store/api/client'

export default {
  getTemplates() {
    return client.pget('/api/data/project-templates')
  },

  getTemplate(templateId) {
    return client.pget(`/api/data/project-templates/${templateId}`)
  },

  createTemplate(data) {
    return client.ppost('/api/data/project-templates', data)
  },

  updateTemplate(templateId, data) {
    return client.pput(`/api/data/project-templates/${templateId}`, data)
  },

  deleteTemplate(templateId) {
    return client.pdel(`/api/data/project-templates/${templateId}`)
  },

  createProjectFromTemplate(templateId, data) {
    return client.ppost(
      `/api/data/project-templates/${templateId}/create-project`,
      data
    )
  }
}
