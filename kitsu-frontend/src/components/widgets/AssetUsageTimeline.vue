<template>
  <div class="asset-usage-timeline" v-if="timelineData.length">
    <h4>使用频率趋势</h4>
    <div class="timeline-chart">
      <div class="chart-bars">
        <div
          class="chart-col"
          :key="item.month"
          :title="`${item.month}: ${item.count} 次`"
          v-for="item in timelineData"
        >
          <div class="chart-bar-wrapper">
            <div
              class="chart-bar"
              :style="{ height: barHeight(item.count) + '%' }"
            ></div>
          </div>
          <span class="chart-label">{{ formatMonth(item.month) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'asset-usage-timeline',

  props: {
    assetId: {
      type: String,
      required: true
    }
  },

  mounted() {
    this.loadTimeline()
  },

  computed: {
    ...mapGetters(['assetUsageTimeline']),

    timelineData() {
      const raw = this.assetUsageTimeline || []
      // Show at most 12 months, most recent last
      return raw.slice(-12)
    },

    maxCount() {
      if (!this.timelineData.length) return 1
      return Math.max(...this.timelineData.map((d) => d.count), 1)
    }
  },

  methods: {
    ...mapActions(['loadUsageTimeline']),

    loadTimeline() {
      if (this.assetId) {
        this.loadUsageTimeline(this.assetId)
      }
    },

    barHeight(count) {
      return Math.round((count / this.maxCount) * 100)
    },

    formatMonth(monthStr) {
      if (!monthStr) return ''
      // Expected format: "2025-03" or "2025-03-01"
      const parts = monthStr.split('-')
      if (parts.length >= 2) {
        return `${parts[1]}月`
      }
      return monthStr
    }
  },

  watch: {
    assetId() {
      this.loadTimeline()
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-usage-timeline {
  margin-top: 1em;
  margin-bottom: 0.5em;

  h4 {
    font-size: 0.85em;
    font-weight: 600;
    margin: 0 0 0.5em;
    color: var(--text-strong);
  }
}

.timeline-chart {
  background: var(--background-alt);
  border-radius: 0.6em;
  padding: 0.8em 0.5em 0.3em;
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 80px;
}

.chart-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
}

.chart-bar-wrapper {
  width: 100%;
  height: 60px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.chart-bar {
  width: 70%;
  max-width: 20px;
  min-height: 2px;
  background: var(--background-selected);
  border-radius: 3px 3px 0 0;
  transition: height 0.3s ease;
}

.chart-label {
  font-size: 0.6em;
  color: var(--text-alt);
  margin-top: 0.3em;
  white-space: nowrap;
}
</style>
