<template>
  <span
    class="category-badge"
    :class="'category-badge--' + size"
    :style="{ background: bgColor, color: textColor }"
  >
    <span class="category-badge-icon" v-html="iconSvg"></span>
    <span class="category-badge-name">{{ label }}</span>
  </span>
</template>

<script>
import {
  getCategoryIcon,
  getCategoryColor,
  getCategoryLabel
} from '@/lib/category-icons'

export default {
  name: 'category-badge',

  props: {
    category: {
      default: null,
      type: Object
    },
    size: {
      default: 'sm',
      type: String,
      validator: (v) => ['sm', 'md'].includes(v)
    }
  },

  computed: {
    iconSvg() {
      const iconName = this.category?.icon
      return getCategoryIcon(iconName)
    },

    colors() {
      const color = this.category?.color
      return getCategoryColor(color)
    },

    bgColor() {
      return this.colors.bg
    },

    textColor() {
      return this.colors.text
    },

    label() {
      return getCategoryLabel(this.category)
    }
  }
}
</script>

<style lang="scss" scoped>
.category-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  border-radius: 0.5em;
  font-weight: 500;
  white-space: nowrap;
  line-height: 1;
}

.category-badge--sm {
  padding: 0.2em 0.5em;
  font-size: 0.8em;

  .category-badge-icon {
    width: 14px;
    height: 14px;

    :deep(svg) {
      width: 14px;
      height: 14px;
    }
  }
}

.category-badge--md {
  padding: 0.3em 0.7em;
  font-size: 0.9em;

  .category-badge-icon {
    width: 16px;
    height: 16px;

    :deep(svg) {
      width: 16px;
      height: 16px;
    }
  }
}

.category-badge-icon {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.category-badge-name {
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
