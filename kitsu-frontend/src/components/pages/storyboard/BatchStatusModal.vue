<template>
  <div class="batch-status-modal" v-if="active">
    <div class="modal-backdrop" @click="$emit('close')" />
    <div class="modal-content">
      <div class="modal-header">
        <h3>批量修改状态</h3>
        <button class="btn-close" @click="$emit('close')">
          <XIcon :size="18" />
        </button>
      </div>

      <div class="modal-body">
        <p class="selection-info">
          已选择 <strong>{{ shotIds.length }}</strong> 个分镜
        </p>

        <div class="status-list">
          <div
            v-for="status in statuses"
            :key="status.id"
            class="status-option"
            :class="{ selected: selectedStatusId === status.id }"
            @click="selectedStatusId = status.id"
          >
            <span
              class="status-dot"
              :style="{ background: status.color }"
            />
            <span class="status-name">{{ status.name }}</span>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button
          class="btn-submit"
          :disabled="!selectedStatusId || isLoading"
          @click="submit"
        >
          {{ isLoading ? '更新中...' : '确定' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { XIcon } from 'lucide-vue-next'

export default {
  name: 'BatchStatusModal',

  components: { XIcon },

  props: {
    active: {
      type: Boolean,
      default: false
    },
    shotIds: {
      type: Array,
      default: () => []
    },
    statuses: {
      type: Array,
      default: () => []
    }
  },

  emits: ['close', 'confirm'],

  data() {
    return {
      selectedStatusId: '',
      isLoading: false
    }
  },

  watch: {
    active(val) {
      if (val) {
        this.selectedStatusId = ''
      }
    }
  },

  methods: {
    async submit() {
      if (!this.selectedStatusId) return
      this.isLoading = true
      try {
        await this.$emit('confirm', {
          shotIds: this.shotIds,
          taskStatusId: this.selectedStatusId
        })
      } finally {
        this.isLoading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.batch-status-modal {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  width: 360px;
  background: var(--background);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  h3 { margin: 0; font-size: 1rem; font-weight: 600; }
}

.btn-close {
  background: none; border: none; cursor: pointer;
  color: var(--text-alt); padding: 4px; border-radius: 4px;
  &:hover { background: var(--background-hover); }
}

.modal-body { padding: 16px 20px; }

.selection-info {
  font-size: 0.85rem;
  color: var(--text-alt);
  margin-bottom: 12px;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: var(--background-hover, rgba(0, 0, 0, 0.05));
  }

  &.selected {
    background: var(--background-selected, rgba(0, 120, 255, 0.08));
    font-weight: 600;
  }
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-name {
  font-size: 0.9rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border);
}

.btn-cancel, .btn-submit {
  padding: 8px 16px; border-radius: 6px;
  font-size: 0.85rem; border: none; cursor: pointer;
}

.btn-cancel {
  background: var(--background-alt); color: var(--text);
  &:hover { background: var(--background-hover); }
}

.btn-submit {
  background: var(--color-primary); color: #fff;
  &:hover { opacity: 0.9; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
</style>
