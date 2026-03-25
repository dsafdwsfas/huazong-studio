<template>
  <div class="asset-search-bar" :class="{ focused: isFocused }">
    <div class="search-input-wrapper">
      <icon class="search-icon" name="search" :size="18" />
      <input
        ref="searchInput"
        class="search-input"
        type="text"
        :placeholder="placeholder"
        v-model="query"
        @input="onInput"
        @keydown.enter="onEnter"
        @keydown.escape="closeSuggestions"
        @keydown.down.prevent="onArrowDown"
        @keydown.up.prevent="onArrowUp"
        @focus="onFocus"
        @blur="onBlur"
      />
      <button
        class="clear-button"
        @mousedown.prevent="clearQuery"
        v-if="query"
      >
        <icon name="x" :size="16" />
      </button>
    </div>

    <div
      class="suggestions-dropdown"
      v-if="showDropdown"
    >
      <!-- Search history -->
      <div
        class="suggestions-section"
        v-if="showHistory && !query && searchHistory.length"
      >
        <div class="section-header">
          <span>最近搜索</span>
          <button class="clear-history" @mousedown.prevent="clearHistory">
            清除
          </button>
        </div>
        <div
          class="suggestion-item history-item"
          :class="{ highlighted: highlightedIndex === index }"
          :key="'h-' + item"
          @mousedown.prevent="selectHistory(item)"
          v-for="(item, index) in searchHistory"
        >
          <icon name="clock" :size="14" />
          <span>{{ item }}</span>
        </div>
      </div>

      <!-- Autocomplete suggestions -->
      <div
        class="suggestions-section"
        v-if="query && suggestions.length"
      >
        <div class="section-header">
          <span>建议</span>
        </div>
        <div
          class="suggestion-item"
          :class="{ highlighted: highlightedIndex === getSuggestionIndex(index) }"
          :key="'s-' + suggestion.id"
          @mousedown.prevent="selectSuggestion(suggestion)"
          v-for="(suggestion, index) in suggestions"
        >
          <div class="suggestion-thumbnail" v-if="suggestion.thumbnail_url">
            <img :src="suggestion.thumbnail_url" :alt="suggestion.name" />
          </div>
          <div class="suggestion-thumbnail placeholder" v-else>
            <icon name="box" :size="14" />
          </div>
          <div class="suggestion-info">
            <span class="suggestion-name" v-html="highlightMatch(suggestion.name)"></span>
            <span class="suggestion-category" v-if="suggestion.category">
              {{ suggestion.category }}
            </span>
          </div>
        </div>
      </div>

      <!-- No results -->
      <div
        class="no-suggestions"
        v-if="query && query.length >= 2 && !suggestions.length && !isLoadingSuggestions"
      >
        无匹配建议，按回车搜索
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import Icon from '@/components/widgets/Icon.vue'

const HISTORY_KEY = 'asset-search-history'
const MAX_HISTORY = 5

export default {
  name: 'asset-search-bar',

  components: { Icon },

  props: {
    placeholder: {
      type: String,
      default: '搜索资产...'
    },
    autofocus: {
      type: Boolean,
      default: false
    },
    showHistory: {
      type: Boolean,
      default: true
    }
  },

  emits: ['search', 'suggestion-select'],

  data() {
    return {
      query: '',
      isFocused: false,
      highlightedIndex: -1,
      searchHistory: [],
      showDropdown: false
    }
  },

  mounted() {
    this.loadHistory()
    if (this.autofocus) {
      this.$nextTick(() => {
        this.$refs.searchInput?.focus()
      })
    }
  },

  computed: {
    ...mapGetters({
      suggestions: 'assetSearchSuggestions',
      isSearching: 'assetSearchIsSearching'
    }),

    isLoadingSuggestions() {
      return false // Suggestions load asynchronously via debounce
    },

    totalItems() {
      if (!this.query && this.showHistory) {
        return this.searchHistory.length
      }
      return this.suggestions.length
    }
  },

  methods: {
    ...mapActions(['loadSuggestions']),

    onInput() {
      this.highlightedIndex = -1
      this.showDropdown = true
      this.loadSuggestions(this.query)
    },

    onEnter() {
      if (
        this.highlightedIndex >= 0 &&
        this.query &&
        this.suggestions[this.highlightedIndex]
      ) {
        this.selectSuggestion(this.suggestions[this.highlightedIndex])
      } else if (
        this.highlightedIndex >= 0 &&
        !this.query &&
        this.searchHistory[this.highlightedIndex]
      ) {
        this.selectHistory(this.searchHistory[this.highlightedIndex])
      } else {
        this.executeSearch()
      }
    },

    onFocus() {
      this.isFocused = true
      this.showDropdown = true
    },

    onBlur() {
      this.isFocused = false
      // Delay to allow click events on suggestions
      setTimeout(() => {
        this.showDropdown = false
      }, 200)
    },

    onArrowDown() {
      if (this.highlightedIndex < this.totalItems - 1) {
        this.highlightedIndex++
      }
    },

    onArrowUp() {
      if (this.highlightedIndex > 0) {
        this.highlightedIndex--
      }
    },

    getSuggestionIndex(index) {
      return index
    },

    closeSuggestions() {
      this.showDropdown = false
      this.highlightedIndex = -1
    },

    executeSearch() {
      const q = this.query.trim()
      if (!q) return
      this.addToHistory(q)
      this.closeSuggestions()
      this.$emit('search', q)
    },

    selectSuggestion(suggestion) {
      this.query = suggestion.name
      this.addToHistory(suggestion.name)
      this.closeSuggestions()
      this.$emit('suggestion-select', suggestion)
      this.$emit('search', suggestion.name)
    },

    selectHistory(item) {
      this.query = item
      this.closeSuggestions()
      this.$emit('search', item)
    },

    clearQuery() {
      this.query = ''
      this.highlightedIndex = -1
      this.loadSuggestions('')
      this.$refs.searchInput?.focus()
    },

    highlightMatch(text) {
      if (!this.query || !text) return text
      const escaped = this.query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`(${escaped})`, 'gi')
      return text.replace(regex, '<mark>$1</mark>')
    },

    // History management
    loadHistory() {
      try {
        const stored = localStorage.getItem(HISTORY_KEY)
        this.searchHistory = stored ? JSON.parse(stored) : []
      } catch {
        this.searchHistory = []
      }
    },

    addToHistory(term) {
      this.searchHistory = this.searchHistory.filter((h) => h !== term)
      this.searchHistory.unshift(term)
      if (this.searchHistory.length > MAX_HISTORY) {
        this.searchHistory = this.searchHistory.slice(0, MAX_HISTORY)
      }
      try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(this.searchHistory))
      } catch {
        // localStorage full or unavailable
      }
    },

    clearHistory() {
      this.searchHistory = []
      try {
        localStorage.removeItem(HISTORY_KEY)
      } catch {
        // ignore
      }
    },

    // Public method: set query from outside
    setQuery(q) {
      this.query = q
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-search-bar {
  position: relative;
  width: 100%;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  height: 42px;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 0.6em;
  padding: 0 0.8em;
  transition: border-color 0.2s, box-shadow 0.2s;

  .asset-search-bar.focused & {
    border-color: var(--background-selected);
    box-shadow: 0 0 0 2px rgba(var(--background-selected-rgb, 64, 153, 255), 0.15);
  }
}

.search-icon {
  color: var(--text-alt);
  flex-shrink: 0;
  margin-right: 0.5em;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text);
  font-size: 0.95em;
  outline: none;
  height: 100%;

  &::placeholder {
    color: var(--text-alt);
    opacity: 0.7;
  }
}

.clear-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--text-alt);
  cursor: pointer;
  padding: 0.2em;
  border-radius: 0.3em;
  flex-shrink: 0;

  &:hover {
    color: var(--text);
    background: var(--background-hover);
  }
}

.suggestions-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 0.6em;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  max-height: 320px;
  overflow-y: auto;
}

.suggestions-section {
  padding: 0.3em 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4em 0.8em;
  font-size: 0.75em;
  color: var(--text-alt);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.clear-history {
  background: none;
  border: none;
  color: var(--text-alt);
  cursor: pointer;
  font-size: 1em;
  padding: 0;

  &:hover {
    color: var(--text);
  }
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.6em;
  padding: 0.5em 0.8em;
  cursor: pointer;
  font-size: 0.9em;
  color: var(--text);

  &:hover,
  &.highlighted {
    background: var(--background-hover);
  }
}

.history-item {
  color: var(--text-alt);
}

.suggestion-thumbnail {
  width: 32px;
  height: 32px;
  border-radius: 0.3em;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--background-alt);
  display: flex;
  align-items: center;
  justify-content: center;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &.placeholder {
    color: var(--text-alt);
    opacity: 0.6;
  }
}

.suggestion-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.suggestion-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  :deep(mark) {
    background: rgba(var(--background-selected-rgb, 64, 153, 255), 0.25);
    color: inherit;
    border-radius: 2px;
    padding: 0 1px;
  }
}

.suggestion-category {
  font-size: 0.8em;
  color: var(--text-alt);
}

.no-suggestions {
  padding: 1em;
  text-align: center;
  font-size: 0.85em;
  color: var(--text-alt);
}
</style>
