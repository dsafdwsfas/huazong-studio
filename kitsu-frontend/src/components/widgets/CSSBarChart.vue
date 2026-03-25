<template>
  <div class="bar-chart" :style="{ height: height + 'px' }">
    <div class="bar-chart-area" v-if="normalizedData.length">
      <div
        class="bar-column"
        v-for="(item, index) in normalizedData"
        :key="index"
        @mouseenter="hoveredIndex = index"
        @mouseleave="hoveredIndex = -1"
      >
        <div class="bar-tooltip" v-if="hoveredIndex === index">
          {{ item.label }}: {{ item.value }}
        </div>
        <div
          class="bar-fill"
          :style="{
            height: item.percent + '%',
            backgroundColor: item.color || defaultColor
          }"
        ></div>
        <div class="bar-label">{{ item.shortLabel || item.label }}</div>
      </div>
    </div>
    <div class="bar-chart-empty" v-else>
      暂无数据
    </div>
  </div>
</template>

<script>
export default {
  name: 'css-bar-chart',

  props: {
    data: {
      type: Array,
      default: () => []
      // [{ label: string, value: number, color?: string }]
    },
    maxValue: {
      type: Number,
      default: 0
    },
    height: {
      type: Number,
      default: 200
    }
  },

  data() {
    return {
      hoveredIndex: -1,
      defaultColor: '#6366f1'
    }
  },

  computed: {
    effectiveMax() {
      if (this.maxValue > 0) return this.maxValue
      const max = Math.max(...this.data.map((d) => d.value || 0))
      return max > 0 ? max : 1
    },

    normalizedData() {
      return this.data.map((item) => ({
        ...item,
        percent: Math.max(((item.value || 0) / this.effectiveMax) * 100, 2),
        shortLabel:
          item.label && item.label.length > 6
            ? item.label.slice(0, 5) + '..'
            : item.label
      }))
    }
  }
}
</script>

<style lang="scss" scoped>
.bar-chart {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.bar-chart-area {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 6px;
  padding-bottom: 24px;
  position: relative;
}

.bar-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  position: relative;
  cursor: pointer;
}

.bar-fill {
  width: 100%;
  max-width: 40px;
  border-radius: 4px 4px 0 0;
  transition: height 0.4s ease, opacity 0.2s ease;
  min-height: 2px;

  .bar-column:hover & {
    opacity: 0.85;
  }
}

.bar-label {
  position: absolute;
  bottom: -20px;
  font-size: 0.65em;
  color: #64748b;
  white-space: nowrap;
  text-align: center;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-tooltip {
  position: absolute;
  top: -8px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 0.7em;
  padding: 0.3em 0.6em;
  border-radius: 4px;
  white-space: nowrap;
  z-index: 10;
  pointer-events: none;
  border: 1px solid rgba(255, 255, 255, 0.1);

  &::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #0f172a;
  }
}

.bar-chart-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 0.85em;
}
</style>
