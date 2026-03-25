<template>
  <div class="online-users" v-if="users.length > 0">
    <div class="online-header">
      <span class="online-dot"></span>
      <span class="online-count">{{ users.length }} 人在线</span>
    </div>
    <div class="online-list">
      <div
        v-for="user in displayedUsers"
        :key="user.user_id"
        class="online-user"
        :title="getUserTooltip(user)"
      >
        <people-avatar
          v-if="getPersonData(user.user_id)"
          :person="getPersonData(user.user_id)"
          :size="24"
          :font-size="11"
        />
        <span v-else class="avatar-placeholder">
          {{ (user.user_name || '?')[0] }}
        </span>
      </div>
      <span
        v-if="users.length > maxDisplay"
        class="online-more"
      >
        +{{ users.length - maxDisplay }}
      </span>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import PeopleAvatar from '@/components/widgets/PeopleAvatar.vue'

export default {
  name: 'online-users',

  components: {
    PeopleAvatar
  },

  props: {
    maxDisplay: {
      type: Number,
      default: 8
    },
    projectId: {
      type: String,
      default: ''
    }
  },

  computed: {
    ...mapGetters(['onlineUsers', 'projectOnlineUsers', 'personMap']),

    users() {
      if (this.projectId) {
        return this.projectOnlineUsers
      }
      return this.onlineUsers
    },

    displayedUsers() {
      return this.users.slice(0, this.maxDisplay)
    }
  },

  watch: {
    projectId: {
      immediate: true,
      handler(id) {
        if (id) {
          this.loadProjectOnlineUsers(id)
        } else {
          this.loadOnlineUsers()
        }
      }
    }
  },

  mounted() {
    // 每 60 秒刷新在线列表
    this._refreshTimer = setInterval(() => {
      if (this.projectId) {
        this.loadProjectOnlineUsers(this.projectId)
      } else {
        this.loadOnlineUsers()
      }
    }, 60000)
  },

  beforeUnmount() {
    if (this._refreshTimer) {
      clearInterval(this._refreshTimer)
    }
  },

  methods: {
    ...mapActions(['loadOnlineUsers', 'loadProjectOnlineUsers']),

    getPersonData(userId) {
      return this.personMap?.get?.(userId) || null
    },

    getUserTooltip(user) {
      const name = user.user_name || '未知用户'
      const page = user.page ? ` — ${user.page}` : ''
      return `${name}${page}`
    }
  }
}
</script>

<style lang="scss" scoped>
.online-users {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.online-header {
  display: flex;
  align-items: center;
  gap: 4px;
}

.online-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00b242;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.online-count {
  font-size: 0.75rem;
  color: var(--text-alt);
  white-space: nowrap;
}

.online-list {
  display: flex;
  align-items: center;
  gap: -4px; // 头像重叠

  > * {
    margin-left: -4px;

    &:first-child {
      margin-left: 0;
    }
  }
}

.online-user {
  position: relative;
  border: 2px solid var(--background);
  border-radius: 50%;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--background-selectable);
  color: var(--text);
  font-size: 11px;
  font-weight: 600;
}

.online-more {
  font-size: 0.7rem;
  color: var(--text-alt);
  margin-left: 4px;
}
</style>
