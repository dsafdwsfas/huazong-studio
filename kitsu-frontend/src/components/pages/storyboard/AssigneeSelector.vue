<template>
  <div class="assignee-selector" ref="selectorRef">
    <div class="assignee-display" @click="toggleDropdown">
      <div v-if="selectedPersons.length" class="avatar-stack">
        <people-avatar
          v-for="person in selectedPersons.slice(0, 3)"
          :key="person.id"
          :person="person"
          :size="24"
          :font-size="11"
          :is-link="false"
        />
        <span v-if="selectedPersons.length > 3" class="more-badge">
          +{{ selectedPersons.length - 3 }}
        </span>
      </div>
      <span v-else class="placeholder">
        <UserPlusIcon :size="14" />
        <span>分配</span>
      </span>
    </div>

    <div v-if="isOpen" class="dropdown-panel">
      <div class="search-box">
        <input
          ref="searchInput"
          v-model="search"
          placeholder="搜索成员..."
          class="search-input"
          @keydown.esc="isOpen = false"
        />
      </div>
      <div class="person-list">
        <div
          v-for="person in filteredPersons"
          :key="person.id"
          class="person-item"
          :class="{ selected: isSelected(person.id) }"
          @click="togglePerson(person)"
        >
          <people-avatar
            :person="person"
            :size="28"
            :font-size="12"
            :is-link="false"
          />
          <span class="person-name">{{ person.full_name }}</span>
          <CheckIcon v-if="isSelected(person.id)" :size="14" class="check" />
        </div>
        <div v-if="filteredPersons.length === 0" class="empty-list">
          无匹配成员
        </div>
      </div>
      <div class="dropdown-actions">
        <button class="btn-clear" @click="clearAll">清空</button>
        <button class="btn-confirm" @click="confirm">确定</button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { CheckIcon, UserPlusIcon } from 'lucide-vue-next'
import PeopleAvatar from '@/components/widgets/PeopleAvatar.vue'

export default {
  name: 'AssigneeSelector',

  components: {
    CheckIcon,
    UserPlusIcon,
    PeopleAvatar
  },

  props: {
    assignees: {
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
      isOpen: false,
      search: '',
      localSelection: []
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
    },

    selectedPersons() {
      return this.assignees
        .map(a => {
          const id = typeof a === 'string' ? a : a.id
          const person = this.personMap.get(id)
          if (person) return person
          // Fallback for assignee objects from API
          if (typeof a === 'object' && a.name) {
            return {
              id: a.id,
              full_name: a.name,
              has_avatar: a.has_avatar || false,
              initials: a.name.slice(0, 2).toUpperCase(),
              color: '#999'
            }
          }
          return null
        })
        .filter(Boolean)
    }
  },

  methods: {
    toggleDropdown() {
      if (this.disabled) return
      this.isOpen = !this.isOpen
      if (this.isOpen) {
        this.localSelection = this.assignees.map(
          a => (typeof a === 'string' ? a : a.id)
        )
        this.search = ''
        this.$nextTick(() => {
          this.$refs.searchInput?.focus()
        })
      }
    },

    isSelected(personId) {
      return this.localSelection.includes(personId)
    },

    togglePerson(person) {
      const idx = this.localSelection.indexOf(person.id)
      if (idx >= 0) {
        this.localSelection.splice(idx, 1)
      } else {
        this.localSelection.push(person.id)
      }
    },

    clearAll() {
      this.localSelection = []
    },

    confirm() {
      this.$emit('update', [...this.localSelection])
      this.isOpen = false
    },

    onClickOutside(e) {
      if (this.$refs.selectorRef && !this.$refs.selectorRef.contains(e.target)) {
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
.assignee-selector {
  position: relative;
}

.assignee-display {
  cursor: pointer;
  display: flex;
  align-items: center;
  min-height: 28px;
  padding: 2px;
  border-radius: 4px;

  &:hover {
    background: var(--background-hover, rgba(0, 0, 0, 0.05));
  }
}

.avatar-stack {
  display: flex;
  align-items: center;

  .avatar {
    border-radius: 50%;
    margin-left: -6px;
    border: 2px solid var(--background);

    &:first-child {
      margin-left: 0;
    }
  }
}

.more-badge {
  font-size: 0.65rem;
  color: var(--text-alt);
  margin-left: 4px;
}

.placeholder {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: var(--text-alt);
  opacity: 0.6;
}

.dropdown-panel {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 100;
  min-width: 220px;
  max-height: 320px;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}

.search-box {
  padding: 8px;
  border-bottom: 1px solid var(--border);
}

.search-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 0.8rem;
  background: var(--background);
  color: var(--text);

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }
}

.person-list {
  overflow-y: auto;
  max-height: 200px;
  padding: 4px;
}

.person-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;

  &:hover {
    background: var(--background-hover, rgba(0, 0, 0, 0.05));
  }

  &.selected {
    background: var(--background-selected, rgba(0, 120, 255, 0.08));
  }
}

.person-name {
  flex: 1;
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.check {
  color: var(--color-primary);
  flex-shrink: 0;
}

.empty-list {
  padding: 12px;
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-alt);
}

.dropdown-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  padding: 8px;
  border-top: 1px solid var(--border);
}

.btn-clear,
.btn-confirm {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.75rem;
  border: none;
  cursor: pointer;
}

.btn-clear {
  background: transparent;
  color: var(--text-alt);

  &:hover {
    background: var(--background-hover);
  }
}

.btn-confirm {
  background: var(--color-primary);
  color: #fff;

  &:hover {
    opacity: 0.9;
  }
}
</style>
