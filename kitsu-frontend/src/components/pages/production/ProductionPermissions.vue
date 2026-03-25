<template>
  <div class="production-permissions page">
    <div class="page-header flexrow">
      <h2 class="title">权限管理</h2>
    </div>

    <div class="permissions-content" v-if="!isLoading">
      <!-- 团队成员角色管理 -->
      <section class="section-block">
        <h3 class="section-title">项目角色分配</h3>
        <p class="section-description">
          为团队成员分配项目内角色，不同角色拥有不同的编辑权限。
        </p>

        <table class="datatable">
          <thead>
            <tr>
              <th>成员</th>
              <th>全局角色</th>
              <th>项目角色</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="member in teamMembers"
              :key="member.id"
            >
              <td class="name-cell">
                <people-avatar
                  :person="member"
                  :size="30"
                  :font-size="14"
                />
                <span class="ml05">{{ member.full_name }}</span>
              </td>
              <td>
                <span class="tag" :class="'role-' + member.role">
                  {{ getRoleName(member.role) }}
                </span>
              </td>
              <td>
                <select
                  class="select-input"
                  :value="getProjectRole(member.id)"
                  @change="onRoleChange(member.id, $event.target.value)"
                  :disabled="!canManageRoles"
                >
                  <option
                    v-for="role in projectRoleTypes"
                    :key="role.id"
                    :value="role.id"
                  >
                    {{ role.name }}
                  </option>
                </select>
              </td>
              <td>
                <span
                  v-if="savingMemberId === member.id"
                  class="saving-indicator"
                >
                  保存中...
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- 角色权限说明 -->
      <section class="section-block">
        <h3 class="section-title">角色权限说明</h3>

        <table class="datatable permission-matrix">
          <thead>
            <tr>
              <th>权限</th>
              <th>导演</th>
              <th>制片</th>
              <th>美术</th>
              <th>观察者</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>查看所有资产/镜头</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
            </tr>
            <tr>
              <td>编辑资产/镜头</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
              <td class="perm-no">✗</td>
            </tr>
            <tr>
              <td>添加评论/预览</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
              <td class="perm-no">✗</td>
            </tr>
            <tr>
              <td>管理项目设置</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
              <td class="perm-no">✗</td>
              <td class="perm-no">✗</td>
            </tr>
            <tr>
              <td>分配角色</td>
              <td class="perm-yes">✓</td>
              <td class="perm-yes">✓</td>
              <td class="perm-no">✗</td>
              <td class="perm-no">✗</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <spinner v-if="isLoading" />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import PeopleAvatar from '@/components/widgets/PeopleAvatar.vue'
import Spinner from '@/components/widgets/Spinner.vue'

const GLOBAL_ROLE_NAMES = {
  user: '艺术家',
  admin: '管理员',
  supervisor: '督导',
  manager: '制片经理',
  client: '客户',
  vendor: '供应商'
}

export default {
  name: 'production-permissions',

  components: {
    PeopleAvatar,
    Spinner
  },

  data() {
    return {
      isLoading: false,
      savingMemberId: null,
      teamRolesMap: {},
      projectRoleTypes: [
        { id: 'director', name: '导演' },
        { id: 'producer', name: '制片' },
        { id: 'artist', name: '美术' },
        { id: 'observer', name: '观察者' }
      ]
    }
  },

  computed: {
    ...mapGetters([
      'currentProduction',
      'isCurrentUserAdmin',
      'isCurrentUserManager'
    ]),

    teamMembers() {
      if (!this.currentProduction?.team) return []
      return this.currentProduction.team
    },

    canManageRoles() {
      if (this.isCurrentUserAdmin || this.isCurrentUserManager) return true
      const myRole = this.teamRolesMap[this.$store.state.user.user?.id]
      return myRole === 'director' || myRole === 'producer'
    }
  },

  async mounted() {
    await this.loadTeamRoles()
  },

  methods: {
    ...mapActions([
      'setMemberProjectRole'
    ]),

    async loadTeamRoles() {
      if (!this.currentProduction) return
      this.isLoading = true
      try {
        const permissionsApi = (await import('@/store/api/permissions')).default
        const roles = await permissionsApi.getProjectTeamRoles(
          this.currentProduction.id
        )
        const map = {}
        for (const r of roles) {
          map[r.person_id] = r.project_role
        }
        this.teamRolesMap = map
      } catch (err) {
        console.error('Failed to load team roles:', err)
      }
      this.isLoading = false
    },

    getRoleName(role) {
      return GLOBAL_ROLE_NAMES[role] || role
    },

    getProjectRole(personId) {
      return this.teamRolesMap[personId] || 'artist'
    },

    async onRoleChange(personId, newRole) {
      this.savingMemberId = personId
      try {
        await this.setMemberProjectRole({
          projectId: this.currentProduction.id,
          personId,
          projectRole: newRole
        })
        this.teamRolesMap = {
          ...this.teamRolesMap,
          [personId]: newRole
        }
      } catch (err) {
        console.error('Failed to update role:', err)
      }
      this.savingMemberId = null
    }
  }
}
</script>

<style lang="scss" scoped>
.production-permissions {
  padding: 2rem;
}

.page-header {
  margin-bottom: 1.5rem;

  .title {
    font-size: 1.3rem;
    font-weight: 600;
    color: var(--text-strong);
  }
}

.section-block {
  margin-bottom: 2rem;
  background: var(--background-block);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
}

.section-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-strong);
  margin-bottom: 0.3rem;
}

.section-description {
  font-size: 0.85rem;
  color: var(--text-alt);
  margin-bottom: 1rem;
}

.datatable {
  width: 100%;
  border-collapse: collapse;

  th,
  td {
    padding: 0.6rem 0.8rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
    font-size: 0.85rem;
  }

  th {
    font-weight: 600;
    color: var(--text-alt);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
}

.name-cell {
  display: flex;
  align-items: center;
}

.ml05 {
  margin-left: 0.5rem;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;

  &.role-admin {
    background: rgba(255, 77, 77, 0.15);
    color: #ff4d4d;
  }

  &.role-manager {
    background: rgba(255, 165, 0, 0.15);
    color: #ffa500;
  }

  &.role-user,
  &.role-vendor {
    background: rgba(0, 178, 66, 0.15);
    color: #00b242;
  }

  &.role-supervisor {
    background: rgba(100, 149, 237, 0.15);
    color: cornflowerblue;
  }

  &.role-client {
    background: rgba(147, 112, 219, 0.15);
    color: mediumpurple;
  }
}

.select-input {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--background);
  color: var(--text);
  font-size: 0.85rem;
  cursor: pointer;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.saving-indicator {
  font-size: 0.75rem;
  color: var(--text-alt);
  font-style: italic;
}

.permission-matrix {
  .perm-yes {
    color: #00b242;
    font-weight: 600;
    text-align: center;
  }

  .perm-no {
    color: #ff4d4d;
    font-weight: 600;
    text-align: center;
  }
}
</style>
