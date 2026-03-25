<template>
  <div class="sequence-edit-modal" v-if="active">
    <div class="modal-backdrop" @click="$emit('close')" />
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ isNew ? '新建场景' : '编辑场景' }}</h3>
        <button class="btn-close" @click="$emit('close')">
          <XIcon :size="18" />
        </button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>场景名称</label>
          <input
            ref="nameInput"
            v-model="form.name"
            placeholder="例如：SEQ010"
            class="form-input"
            @keydown.enter="submit"
          />
        </div>
        <div class="form-group">
          <label>描述（可选）</label>
          <textarea
            v-model="form.description"
            placeholder="场景描述..."
            class="form-textarea"
            rows="3"
          />
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button
          class="btn-submit"
          :disabled="!form.name.trim() || isLoading"
          @click="submit"
        >
          {{ isLoading ? '保存中...' : (isNew ? '创建' : '保存') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { XIcon } from 'lucide-vue-next'

export default {
  name: 'SequenceEditModal',

  components: { XIcon },

  props: {
    active: {
      type: Boolean,
      default: false
    },
    sequence: {
      type: Object,
      default: null
    }
  },

  emits: ['close', 'confirm'],

  data() {
    return {
      form: {
        name: '',
        description: ''
      },
      isLoading: false
    }
  },

  computed: {
    isNew() {
      return !this.sequence
    }
  },

  watch: {
    active(val) {
      if (val) {
        if (this.sequence) {
          this.form.name = this.sequence.name || ''
          this.form.description = this.sequence.description || ''
        } else {
          this.form.name = ''
          this.form.description = ''
        }
        this.$nextTick(() => {
          this.$refs.nameInput?.focus()
        })
      }
    }
  },

  methods: {
    async submit() {
      if (!this.form.name.trim()) return
      this.isLoading = true
      try {
        await this.$emit('confirm', {
          id: this.sequence?.id,
          name: this.form.name.trim(),
          description: this.form.description.trim()
        })
      } finally {
        this.isLoading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.sequence-edit-modal {
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
  width: 400px;
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

  h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
  }
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-alt);
  padding: 4px;
  border-radius: 4px;

  &:hover {
    background: var(--background-hover);
  }
}

.modal-body {
  padding: 16px 20px;
}

.form-group {
  margin-bottom: 12px;

  label {
    display: block;
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 4px;
    color: var(--text);
  }
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.85rem;
  background: var(--background);
  color: var(--text);
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }
}

.form-textarea {
  resize: vertical;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border);
}

.btn-cancel,
.btn-submit {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.85rem;
  border: none;
  cursor: pointer;
}

.btn-cancel {
  background: var(--background-alt);
  color: var(--text);

  &:hover {
    background: var(--background-hover);
  }
}

.btn-submit {
  background: var(--color-primary);
  color: #fff;

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
</style>
