<template>
  <div class="conflict-alert" v-if="visible">
    <div class="conflict-icon">
      <alert-triangle-icon :size="20" />
    </div>
    <div class="conflict-content">
      <p class="conflict-title">编辑冲突</p>
      <p class="conflict-message">
        {{ message }}
      </p>
      <div class="conflict-users" v-if="editingUsers.length > 0">
        <span
          v-for="user in editingUsers"
          :key="user.user_id"
          class="editing-user"
        >
          {{ user.user_name }}
        </span>
        正在编辑此内容
      </div>
    </div>
    <div class="conflict-actions">
      <button class="button is-small" @click="$emit('force-save')">
        强制保存
      </button>
      <button class="button is-small" @click="$emit('reload')">
        刷新数据
      </button>
      <button class="button is-small" @click="$emit('dismiss')">
        忽略
      </button>
    </div>
  </div>
</template>

<script>
import { AlertTriangleIcon } from 'lucide-vue-next'

export default {
  name: 'conflict-alert',

  components: {
    AlertTriangleIcon
  },

  props: {
    visible: {
      type: Boolean,
      default: false
    },
    message: {
      type: String,
      default: '此内容已被其他人修改，你的修改可能会覆盖他人的更改。'
    },
    editingUsers: {
      type: Array,
      default: () => []
    }
  },

  emits: ['force-save', 'reload', 'dismiss']
}
</script>

<style lang="scss" scoped>
.conflict-alert {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 165, 0, 0.1);
  border: 1px solid rgba(255, 165, 0, 0.3);
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.conflict-icon {
  color: #ffa500;
  flex-shrink: 0;
  margin-top: 2px;
}

.conflict-content {
  flex: 1;
  min-width: 0;
}

.conflict-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #ffa500;
  margin-bottom: 2px;
}

.conflict-message {
  font-size: 0.8rem;
  color: var(--text);
  margin-bottom: 4px;
}

.conflict-users {
  font-size: 0.75rem;
  color: var(--text-alt);
}

.editing-user {
  font-weight: 600;
  color: var(--text-strong);
}

.conflict-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;

  .button.is-small {
    font-size: 0.7rem;
    padding: 2px 8px;
    min-width: 70px;
  }
}
</style>
