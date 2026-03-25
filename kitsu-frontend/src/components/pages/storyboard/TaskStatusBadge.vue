<template>
  <div class="task-status-badge" ref="badgeRef">
    <button
      class="status-btn"
      :style="badgeStyle"
      :disabled="disabled"
      @click="toggleDropdown"
    >
      {{ displayName }}
    </button>

    <div v-if="isOpen" class="status-dropdown">
      <div
        v-for="status in statuses"
        :key="status.id"
        class="status-option"
        :class="{ active: status.id === currentStatusId }"
        @click="selectStatus(status)"
      >
        <span class="status-dot" :style="{ background: status.color }" />
        <span class="status-label">{{ status.name }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TaskStatusBadge',

  props: {
    taskStatusId: {
      type: String,
      default: ''
    },
    taskStatusName: {
      type: String,
      default: '未分配'
    },
    taskStatusColor: {
      type: String,
      default: '#999999'
    },
    statuses: {
      type: Array,
      default: () => []
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },

  emits: ['update'],

  data() {
    return {
      isOpen: false
    }
  },

  computed: {
    currentStatusId() {
      return this.taskStatusId
    },

    displayName() {
      return this.taskStatusName || '未分配'
    },

    badgeStyle() {
      const color = this.taskStatusColor || '#999999'
      return {
        backgroundColor: `${color}20`,
        color: color,
        borderColor: `${color}40`
      }
    }
  },

  methods: {
    toggleDropdown() {
      if (this.disabled) return
      this.isOpen = !this.isOpen
    },

    selectStatus(status) {
      if (status.id !== this.currentStatusId) {
        this.$emit('update', status.id)
      }
      this.isOpen = false
    },

    onClickOutside(e) {
      if (this.$refs.badgeRef && !this.$refs.badgeRef.contains(e.target)) {
        this.isOpen = false
      }
    }
  },

  mounted() {
    document.addEventListener('mousedown', this.onClickOutside)
  },

  beforeUnmount() {
    document.removeEventListener('mousedown', this.onClickOutside)
  }
}
</script>

<style lang="scss" scoped>
.task-status-badge {
  position: relative;
  display: inline-flex;
}

.status-btn {
  font-size: 0.65rem;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid;
  cursor: pointer;
  white-space: nowrap;
  font-weight: 500;
  transition: opacity 0.15s;

  &:hover:not(:disabled) {
    opacity: 0.8;
  }

  &:disabled {
    cursor: default;
    opacity: 0.6;
  }
}

.status-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  min-width: 160px;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 4px;
  margin-top: 4px;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;

  &:hover {
    background: var(--background-hover, rgba(0, 0, 0, 0.05));
  }

  &.active {
    background: var(--background-selected, rgba(0, 120, 255, 0.08));
    font-weight: 600;
  }
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
