/**
 * 权限管理 API
 *
 * 项目角色和实体级访问控制的 CRUD 操作。
 */

import client from '@/store/api/client'

export default {
  /**
   * 获取所有可用的项目角色类型
   */
  getProjectRoleTypes() {
    return client.pget('/api/data/project-role-types')
  },

  /**
   * 获取项目团队成员及其项目角色
   */
  getProjectTeamRoles(projectId) {
    return client.pget(`/api/data/projects/${projectId}/team-roles`)
  },

  /**
   * 设置项目成员的角色
   */
  setMemberRole(projectId, personId, projectRole) {
    return client.pput(
      `/api/data/projects/${projectId}/team/${personId}/role`,
      { project_role: projectRole }
    )
  },

  /**
   * 获取项目的实体级访问控制规则
   */
  getAccessControls(projectId) {
    return client.pget(
      `/api/data/projects/${projectId}/access-controls`
    )
  },

  /**
   * 创建或更新实体级访问控制规则
   */
  setAccessControl(projectId, data) {
    return client.ppost(
      `/api/data/projects/${projectId}/access-controls`,
      data
    )
  },

  /**
   * 删除实体级访问控制规则
   */
  deleteAccessControl(projectId, aclId) {
    return client.pdel(
      `/api/data/projects/${projectId}/access-controls/${aclId}`
    )
  }
}
