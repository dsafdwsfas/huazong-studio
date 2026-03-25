<template>
  <div class="donut-chart">
    <div class="donut-visual">
      <div class="donut-ring" :style="donutStyle"></div>
      <div class="donut-center">
        <span class="donut-total">{{ total }}</span>
        <span class="donut-label">总计</span>
      </div>
    </div>
    <div class="donut-legend" v-if="data.length">
      <div
        class="legend-item"
        v-for="(item, index) in data"
        :key="index"
      >
        <span class="legend-dot" :style="{ backgroundColor: item.color }"></span>
        <span class="legend-label">{{ item.label }}</span>
        <span class="legend-value">{{ item.value }}</span>
        <span class="legend-percent">{{ getPercent(item.value) }}%</span>
      </div>
    </div>
    <div class="donut-empty" v-else>
      暂无数据
    </div>
  </div>
</template>

<script>
export default {
  name: 'css-donut-chart',

  props: {
    data: {
      type: Array,
      default: () => []
      // [{ label: string, value: number, color: string }]
    }
  },

  computed: {
    total() {
      return this.data.reduce((sum, item) => sum + (item.value || 0), 0)
    },

    donutStyle() {
      if (!this.data.length || this.total === 0) {
        return {
          background: 'conic-gradient(#2a2a4a 0deg 360deg)'
        }
      }

      const segments = []
      let cumulative = 0

      for (const item of this.data) {
        const percent = (item.value / this.total) * 100
        const start = cumulative
        cumulative += percent
        segments.push(`${item.color} ${start}% ${cumulative}%`)
      }

      return {
        background: `conic-gradient(${segments.join(', ')})`
      }
    }
  },

  methods: {
    getPercent(value) {
      if (this.total === 0) return 0
      return ((value / this.total) * 100).toFixed(1)
    }
  }
}
</script>

<style lang="scss" scoped>
.donut-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.2em;
}

.donut-visual {
  position: relative;
  width: 160px;
  height: 160px;
}

.donut-ring {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  mask: radial-gradient(transparent 55%, black 56%);
  -webkit-mask: radial-gradient(transparent 55%, black 56%);
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  display: flex;
  flex-direction: column;
}

.donut-total {
  font-size: 1.5em;
  font-weight: 700;
  color: #e2e8f0;
}

.donut-label {
  font-size: 0.75em;
  color: #94a3b8;
}

.donut-legend {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.4em;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5em;
  font-size: 0.8em;
  color: #cbd5e1;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.legend-value {
  font-weight: 600;
  color: #e2e8f0;
}

.legend-percent {
  color: #64748b;
  min-width: 40px;
  text-align: right;
}

.donut-empty {
  color: #64748b;
  font-size: 0.85em;
  padding: 2em 0;
}
</style>
