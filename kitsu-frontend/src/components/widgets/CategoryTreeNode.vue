<template>
  <div class="category-tree-node">
    <div
      class="tree-item"
      :class="{
        selected: selectedId === category.id,
        'is-selectable': selectable,
        'is-draggable': draggable,
        'drag-over': isDragOver
      }"
      :style="{ paddingLeft: depth * 1.2 + 0.6 + 'em' }"
      :draggable="draggable"
      @click="onSelect"
      @dragstart="onDragStart"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <span
        class="tree-expand"
        :class="{ expanded: isExpanded, invisible: !hasChildren }"
        @click.stop="toggleExpand"
      >
        <chevron-right-icon :size="14" />
      </span>

      <span
        class="tree-icon"
        :style="{ backgroundColor: category.color || '#666' }"
        v-if="showIcon"
      >
        <component
          :is="iconComponent"
          :size="12"
          color="#fff"
          v-if="iconComponent"
        />
        <span v-else class="icon-letter">
          {{ (category.name || '?').charAt(0) }}
        </span>
      </span>

      <span class="tree-item-label">
        <span class="tree-item-name" :title="category.name">
          {{ category.name }}
        </span>
        <span
          class="tree-lock"
          title="系统预设"
          v-if="category.is_system"
        >
          🔒
        </span>
      </span>

      <span class="filler"></span>

      <span
        class="tree-count"
        v-if="showCount && assetCount !== undefined"
      >
        {{ assetCount }}
      </span>
    </div>

    <div class="tree-children" v-if="hasChildren && isExpanded">
      <category-tree-node
        :category="child"
        :depth="depth + 1"
        :selected-id="selectedId"
        :selectable="selectable"
        :draggable="draggable"
        :show-count="showCount"
        :show-icon="showIcon"
        :stats="stats"
        :key="child.id"
        @select="$emit('select', $event)"
        @reorder="$emit('reorder', $event)"
        v-for="child in category.children"
      />
    </div>
  </div>
</template>

<script>
import { ChevronRightIcon } from 'lucide-vue-next'

export default {
  name: 'category-tree-node',

  components: {
    ChevronRightIcon
  },

  props: {
    category: {
      type: Object,
      required: true
    },
    depth: {
      type: Number,
      default: 0
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

  data() {
    return {
      isExpanded: this.depth < 1,
      isDragOver: false
    }
  },

  computed: {
    hasChildren() {
      return this.category.children && this.category.children.length > 0
    },

    assetCount() {
      return this.stats[this.category.id] ?? undefined
    },

    iconComponent() {
      // Could map category.icon to lucide components in the future
      return null
    }
  },

  methods: {
    toggleExpand() {
      if (this.hasChildren) {
        this.isExpanded = !this.isExpanded
      }
    },

    onSelect() {
      if (this.selectable) {
        this.$emit('select', this.category)
      }
    },

    onDragStart(e) {
      if (!this.draggable) return
      e.dataTransfer.setData('text/plain', this.category.id)
      e.dataTransfer.effectAllowed = 'move'
    },

    onDragOver(e) {
      if (!this.draggable) return
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
      this.isDragOver = true
    },

    onDragLeave() {
      this.isDragOver = false
    },

    onDrop(e) {
      if (!this.draggable) return
      e.preventDefault()
      this.isDragOver = false
      const draggedId = e.dataTransfer.getData('text/plain')
      if (draggedId && draggedId !== this.category.id) {
        this.$emit('reorder', {
          draggedId,
          targetId: this.category.id,
          targetParentId: this.category.parent_id
        })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.category-tree-node {
  display: flex;
  flex-direction: column;
}

.tree-item {
  display: flex;
  align-items: center;
  padding: 0.4em 0.6em;
  border-radius: 0.4em;
  cursor: default;
  font-size: 0.9em;
  gap: 0.4em;
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

  &.is-draggable {
    cursor: grab;
  }

  &.drag-over {
    background: var(--background-selectable);
    outline: 2px dashed var(--text-alt);
    outline-offset: -2px;
  }
}

.tree-expand {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  transition: transform 0.15s ease;

  &.expanded {
    transform: rotate(90deg);
  }

  &.invisible {
    visibility: hidden;
  }
}

.tree-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  flex-shrink: 0;
  font-size: 0.7em;
}

.icon-letter {
  color: #fff;
  font-weight: 700;
  font-size: 0.85em;
  text-transform: uppercase;
}

.tree-item-label {
  display: flex;
  align-items: center;
  gap: 0.3em;
  overflow: hidden;
}

.tree-item-name {
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-lock {
  font-size: 0.75em;
  flex-shrink: 0;
}

.filler {
  flex: 1;
}

.tree-count {
  font-size: 0.75em;
  color: var(--text-alt);
  background: var(--background-alt);
  padding: 0.1em 0.5em;
  border-radius: 0.8em;
  flex-shrink: 0;
}

.tree-children {
  display: flex;
  flex-direction: column;
}
</style>
