<template>
  <div class="batch-assign-modal" v-if="active">
    <div class="modal-backdrop" @click="$emit('close')" />
    <div class="modal-content">
      <div class="modal-header">
        <h3>批量分配负责人</h3>
        <button class="btn-close" @click="$emit('close')">
          <XIcon :size="18" />
        </button>
      </div>

      <div class="modal-body">
        <p class="selection-info">
          已选择 <strong>{{ shotIds.length }}</strong> 个分镜
        </p>

        <div class="person-search">
          <input
            ref="searchInput"
            v-model="search"
            placeholder="搜索成员..."
            class="search-input"
          />
        </div>

        <div class="person-list">
          <label
            v-for="person in filteredPersons"
            :key="person.id"
            class="person-item"
          >
            <input
              type="checkbox"
              :value="person.id"
              v-model="selectedPersonIds"
            />
            <people-avatar
              :person="person"
              :size="28"
              :font-size="12"
              :is-link="false"
            />
            <span class="person-name">{{ person.full_name }}</span>
          </label>
          <div v-if="filteredPersons.length === 0" class="empty-list">
            无匹配成员
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-submit" :disabled="isLoading" @click="submit">
          <template v-if="isLoading">分配中...</template>
          <template v-else>
            分配给 {{ selectedPersonIds.length }} 人
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { XIcon } from 'lucide-vue-next'
import PeopleAvatar from '@/components/widgets/PeopleAvatar.vue'

export default {
  name: 'BatchAssignModal',

  components: {
    XIcon,
    PeopleAvatar
  },

  props: {
    active: {
      type: Boolean,
      default: false
    },
    shotIds: {
      type: Array,
      default: () => []
    }
  },

  emits: ['close', 'confirm'],

  data() {
    return {
      search: '',
      selectedPersonIds: [],
      isLoading: false
    }
  },

  computed: {
    ...mapGetters(['currentProduction', 'personMap']),

    teamMembers() {
      if (!this.currentProduction?.team) return []
      return this.currentProduction.team
        .map(id => this.personMap.get(id))
        .filter(Boolean)
        .sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''))
    },

    filteredPersons() {
      if (!this.search) return this.teamMembers
      const q = this.search.toLowerCase()
      return this.teamMembers.filter(
        p => (p.full_name || '').toLowerCase().includes(q)
      )
    }
  },

  watch: {
    active(val) {
      if (val) {
        this.selectedPersonIds = []
        this.search = ''
        this.$nextTick(() => {
          this.$refs.searchInput?.focus()
        })
      }
    }
  },

  methods: {
    async submit() {
      this.isLoading = true
      try {
        await this.$emit('confirm', {
          shotIds: this.shotIds,
          personIds: this.selectedPersonIds
        })
      } finally {
        this.isLoading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.batch-assign-modal {
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
  max-height: 80vh;
  background: var(--background);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
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
  overflow-y: auto;
  flex: 1;
}

.selection-info {
  font-size: 0.85rem;
  color: var(--text-alt);
  margin-bottom: 12px;
}

.person-search {
  margin-bottom: 8px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.85rem;
  background: var(--background);
  color: var(--text);

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }
}

.person-list {
  max-height: 300px;
  overflow-y: auto;
}

.person-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;

  &:hover {
    background: var(--background-hover, rgba(0, 0, 0, 0.05));
  }

  input[type='checkbox'] {
    flex-shrink: 0;
  }
}

.person-name {
  flex: 1;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-list {
  padding: 20px;
  text-align: center;
  color: var(--text-alt);
  font-size: 0.85rem;
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
