<template>
  <div class="annotation-toolbar">
    <div class="tool-group">
      <button
        v-for="tool in tools"
        :key="tool.id"
        class="tool-button"
        :class="{ active: activeTool === tool.id }"
        :title="tool.label"
        @click="selectTool(tool.id)"
      >
        <component :is="tool.icon" :size="18" />
      </button>
    </div>

    <div class="separator" />

    <div class="color-group">
      <button
        v-for="c in colors"
        :key="c"
        class="color-swatch"
        :class="{ active: activeColor === c }"
        :style="{ backgroundColor: c }"
        :title="c"
        @click="selectColor(c)"
      />
    </div>

    <div class="separator" />

    <div class="action-group">
      <button
        class="tool-button"
        title="撤销 (Ctrl+Z)"
        @click="$emit('undo')"
      >
        <Undo2Icon :size="18" />
      </button>
      <button
        class="tool-button"
        title="重做 (Ctrl+Y)"
        @click="$emit('redo')"
      >
        <Redo2Icon :size="18" />
      </button>
      <button
        class="tool-button"
        title="清除全部"
        @click="$emit('clear')"
      >
        <Trash2Icon :size="18" />
      </button>
    </div>

    <div class="separator" />

    <div class="action-group">
      <button
        class="tool-button save-button"
        title="保存标注"
        @click="$emit('save')"
      >
        <SaveIcon :size="18" />
        <span>保存</span>
      </button>
    </div>
  </div>
</template>

<script>
import {
  MousePointerIcon,
  PenToolIcon,
  EraserIcon,
  SquareIcon,
  CircleIcon,
  ArrowUpRightIcon,
  TypeIcon,
  MapPinIcon,
  RulerIcon,
  Undo2Icon,
  Redo2Icon,
  Trash2Icon,
  SaveIcon
} from 'lucide-vue-next'

export default {
  name: 'AnnotationToolbar',

  components: {
    MousePointerIcon,
    PenToolIcon,
    EraserIcon,
    SquareIcon,
    CircleIcon,
    ArrowUpRightIcon,
    TypeIcon,
    MapPinIcon,
    RulerIcon,
    Undo2Icon,
    Redo2Icon,
    Trash2Icon,
    SaveIcon
  },

  props: {
    activeTool: {
      type: String,
      default: 'select'
    },
    activeColor: {
      type: String,
      default: '#ff3860'
    }
  },

  emits: ['select-tool', 'select-color', 'undo', 'redo', 'clear', 'save'],

  data() {
    return {
      tools: [
        { id: 'select', label: '选择', icon: 'MousePointerIcon' },
        { id: 'pencil', label: '画笔', icon: 'PenToolIcon' },
        { id: 'eraser', label: '橡皮擦', icon: 'EraserIcon' },
        { id: 'rectangle', label: '矩形', icon: 'SquareIcon' },
        { id: 'circle', label: '圆形', icon: 'CircleIcon' },
        { id: 'arrow', label: '箭头', icon: 'ArrowUpRightIcon' },
        { id: 'text', label: '文字', icon: 'TypeIcon' },
        { id: 'marker', label: '标记点', icon: 'MapPinIcon' },
        { id: 'measure', label: '测量', icon: 'RulerIcon' }
      ],
      colors: [
        '#ff3860',
        '#23d160',
        '#209cee',
        '#ffdd57',
        '#ffffff',
        '#000000'
      ]
    }
  },

  methods: {
    selectTool(toolId) {
      this.$emit('select-tool', toolId)
    },
    selectColor(color) {
      this.$emit('select-color', color)
    }
  }
}
</script>

<style lang="scss" scoped>
.annotation-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #2d2d2d;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  user-select: none;
}

.tool-group,
.color-group,
.action-group {
  display: flex;
  align-items: center;
  gap: 2px;
}

.separator {
  width: 1px;
  height: 24px;
  margin: 0 4px;
  background: #4a4a4a;
}

.tool-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #b0b0b0;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease;

  &:hover {
    background: #3d3d3d;
    color: #e0e0e0;
  }

  &.active {
    background: #209cee;
    color: #ffffff;
  }

  &:focus-visible {
    outline: 2px solid #209cee;
    outline-offset: -2px;
  }
}

.save-button {
  width: auto;
  padding: 0 10px;
  gap: 4px;

  span {
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
  }
}

.color-swatch {
  width: 22px;
  height: 22px;
  padding: 0;
  border: 2px solid transparent;
  border-radius: 50%;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    transform 0.15s ease;

  &:hover {
    transform: scale(1.15);
  }

  &.active {
    border-color: #209cee;
    box-shadow: 0 0 0 1px #2d2d2d;
  }

  &:focus-visible {
    outline: 2px solid #209cee;
    outline-offset: 2px;
  }
}
</style>
