<template>
  <div class="category-tree-browser">
    <div
      class="tree-item"
      :class="{
        selected: selectedId === null,
        'is-selectable': selectable
      }"
      @click="onSelectAll"
      v-if="selectable"
    >
      <span class="tree-item-label">
        <span class="tree-item-name">全部分类</span>
      </span>
    </div>

    <category-tree-node
      :category="cat"
      :depth="0"
      :selected-id="selectedId"
      :selectable="selectable"
      :draggable="draggable"
      :show-count="showCount"
      :show-icon="showIcon"
      :stats="stats"
      :key="cat.id"
      @select="onSelect"
      @reorder="onReorder"
      v-for="cat in categories"
    />
  </div>
</template>

<script>
import CategoryTreeNode from '@/components/widgets/CategoryTreeNode.vue'

export default {
  name: 'category-tree-browser',

  components: {
    CategoryTreeNode
  },

  props: {
    categories: {
      type: Array,
      default: () => []
    },
    selectedId: {
      type: String,
      default: null
    },
    selectable: {
      type: Boolean,
      default: true
    },
    draggable: {
      type: Boolean,
      default: false
    },
    showCount: {
      type: Boolean,
      default: false
    },
    showIcon: {
      type: Boolean,
      default: true
    },
    stats: {
      type: Object,
      default: () => ({})
    }
  },

  emits: ['select', 'reorder'],

  methods: {
    onSelectAll() {
      if (this.selectable) {
        this.$emit('select', null)
      }
    },

    onSelect(category) {
      this.$emit('select', category)
    },

    onReorder(newOrders) {
      this.$emit('reorder', newOrders)
    }
  }
}
</script>

<style lang="scss" scoped>
.category-tree-browser {
  display: flex;
  flex-direction: column;
  gap: 2px;
  user-select: none;
}

.tree-item {
  display: flex;
  align-items: center;
  padding: 0.4em 0.6em;
  border-radius: 0.4em;
  cursor: default;
  font-size: 0.9em;
  transition: background 0.15s ease;

  &.is-selectable {
    cursor: pointer;

    &:hover {
      background: var(--background-hover);
    }
  }

  &.selected {
    background: var(--background-selected);
    font-weight: 600;
  }
}

.tree-item-name {
  color: var(--text);
}
</style>
