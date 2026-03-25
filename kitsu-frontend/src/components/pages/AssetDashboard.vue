<template>
  <div class="asset-dashboard" ref="dashboard">
    <header class="dashboard-header">
      <h1 class="dashboard-title">资产统计看板</h1>
      <button class="refresh-btn" @click="refreshAll" :disabled="isLoading">
        <refresh-cw-icon :size="16" :class="{ spinning: isLoading }" />
        <span>刷新</span>
      </button>
    </header>

    <!-- KPI Cards -->
    <section class="kpi-row">
      <stat-card
        title="总资产数"
        :value="dashboardData.total_assets || 0"
        icon="package"
        color="#6366f1"
        suffix="个"
      />
      <stat-card
        title="总使用次数"
        :value="dashboardData.total_usage || 0"
        icon="click"
        color="#06b6d4"
        suffix="次"
      />
      <stat-card
        title="存储占用"
        :value="formatStorage(dashboardData.total_storage || 0)"
        icon="hard-drive"
        color="#f59e0b"
        :suffix="storageUnit"
      />
      <stat-card
        title="图谱节点数"
        :value="dashboardData.graph_nodes || 0"
        icon="network"
        color="#10b981"
        suffix="个"
      />
    </section>

    <!-- Charts Row 1: Category Distribution + Growth Trend -->
    <section class="chart-row">
      <div class="chart-panel">
        <h3 class="panel-title">分类分布</h3>
        <css-donut-chart :data="categoryChartData" />
      </div>
      <div class="chart-panel chart-panel-wide">
        <h3 class="panel-title">增长趋势</h3>
        <div class="line-chart-container">
          <svg
            class="line-chart-svg"
            :viewBox="`0 0 ${lineChartWidth} ${lineChartHeight}`"
            preserveAspectRatio="none"
            v-if="growthTrend.length"
          >
            <defs>
              <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#6366f1" stop-opacity="0.3" />
                <stop offset="100%" stop-color="#6366f1" stop-opacity="0.02" />
              </linearGradient>
            </defs>
            <polygon
              :points="areaPoints"
              fill="url(#lineGrad)"
            />
            <polyline
              :points="linePoints"
              fill="none"
              stroke="#6366f1"
              stroke-width="2.5"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            <circle
              v-for="(pt, i) in pointCoords"
              :key="i"
              :cx="pt.x"
              :cy="pt.y"
              r="3.5"
              fill="#6366f1"
              stroke="#1a1a2e"
              stroke-width="2"
            />
          </svg>
          <div class="line-chart-labels" v-if="growthTrend.length">
            <span
              v-for="(item, i) in growthTrend"
              :key="i"
              class="line-label"
            >{{ item.month || item.period }}</span>
          </div>
          <div class="chart-empty" v-else>暂无数据</div>
        </div>
      </div>
    </section>

    <!-- Charts Row 2: Usage Frequency + Storage Stats -->
    <section class="chart-row">
      <div class="chart-panel chart-panel-wide">
        <h3 class="panel-title">使用频率（按月）</h3>
        <css-bar-chart
          :data="usageBarData"
          :height="200"
        />
      </div>
      <div class="chart-panel chart-panel-wide">
        <h3 class="panel-title">存储占用（按分类）</h3>
        <css-bar-chart
          :data="storageBarData"
          :height="200"
        />
      </div>
    </section>

    <!-- Hotness Ranking -->
    <section class="chart-panel full-width">
      <h3 class="panel-title">热度排行 Top 10</h3>
      <div class="ranking-table-wrapper" v-if="hotnessRanking.length">
        <table class="ranking-table">
          <thead>
            <tr>
              <th class="col-rank">#</th>
              <th class="col-thumb">缩略图</th>
              <th class="col-name">名称</th>
              <th class="col-category">分类</th>
              <th class="col-hotness">热度分</th>
              <th class="col-bar">热度</th>
              <th class="col-meta">使用 / 版本 / 关联</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in hotnessRanking.slice(0, 10)" :key="item.id || index">
              <td class="col-rank">
                <span :class="['rank-badge', rankClass(index)]">{{ index + 1 }}</span>
              </td>
              <td class="col-thumb">
                <div class="thumb-box">
                  <img
                    :src="getThumbnailUrl(item)"
                    v-if="item.preview_file_id"
                    @error="onThumbError"
                  />
                  <span v-else class="thumb-placeholder">{{ (item.name || '?').charAt(0) }}</span>
                </div>
              </td>
              <td class="col-name">{{ item.name || '-' }}</td>
              <td class="col-category">
                <span class="category-tag">{{ item.category_label || item.category || '-' }}</span>
              </td>
              <td class="col-hotness">{{ item.hotness_score || 0 }}</td>
              <td class="col-bar">
                <div class="hotness-bar-bg">
                  <div
                    class="hotness-bar-fill"
                    :style="{ width: getHotnessPercent(item) + '%' }"
                  ></div>
                </div>
              </td>
              <td class="col-meta">
                {{ item.usage_count || 0 }} /
                {{ item.version_count || 0 }} /
                {{ item.relation_count || 0 }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="chart-empty" v-else>暂无排行数据</div>
    </section>

    <!-- Bottom Row: Creator Stats + Recent Assets -->
    <section class="chart-row">
      <div class="chart-panel">
        <h3 class="panel-title">创建者排行</h3>
        <div class="creator-list" v-if="creatorStats.length">
          <div
            class="creator-item"
            v-for="(creator, index) in creatorStats"
            :key="index"
          >
            <span class="creator-rank">{{ index + 1 }}</span>
            <div class="creator-avatar">
              <img
                :src="getAvatarUrl(creator.person)"
                v-if="creator.person && creator.person.has_avatar"
                @error="onThumbError"
              />
              <span v-else class="avatar-placeholder">
                {{ getInitials(creator.person) }}
              </span>
            </div>
            <span class="creator-name">{{ getPersonName(creator.person) }}</span>
            <span class="creator-count">{{ creator.asset_count || 0 }} 个</span>
          </div>
        </div>
        <div class="chart-empty" v-else>暂无数据</div>
      </div>
      <div class="chart-panel chart-panel-wide">
        <h3 class="panel-title">最近新增资产</h3>
        <div class="recent-list" v-if="recentAssets.length">
          <div
            class="recent-item"
            v-for="asset in recentAssets"
            :key="asset.id"
          >
            <div class="recent-dot"></div>
            <div class="recent-info">
              <span class="recent-name">{{ asset.name }}</span>
              <span class="recent-category">{{ asset.category_label || asset.category }}</span>
            </div>
            <span class="recent-time">{{ formatDate(asset.created_at) }}</span>
          </div>
        </div>
        <div class="chart-empty" v-else>暂无数据</div>
      </div>
    </section>
  </div>
</template>

<script>
import { RefreshCwIcon } from 'lucide-vue-next'
import { mapGetters, mapActions } from 'vuex'

import StatCard from '@/components/widgets/StatCard.vue'
import CSSDonutChart from '@/components/widgets/CSSDonutChart.vue'
import CSSBarChart from '@/components/widgets/CSSBarChart.vue'

const CATEGORY_COLORS = [
  '#6366f1', '#06b6d4', '#10b981', '#f59e0b',
  '#ef4444', '#ec4899', '#8b5cf6', '#14b8a6',
  '#f97316', '#84cc16', '#a855f7', '#0ea5e9'
]

const STORAGE_COLORS = [
  '#6366f1', '#06b6d4', '#10b981', '#f59e0b',
  '#ef4444', '#ec4899', '#8b5cf6', '#14b8a6'
]

export default {
  name: 'asset-dashboard',

  components: {
    RefreshCwIcon,
    StatCard,
    CSSDonutChart,
    CSSBarChart
  },

  data() {
    return {
      lineChartWidth: 500,
      lineChartHeight: 180,
      lineChartPadding: 30
    }
  },

  created() {
    this.refreshAll()
  },

  computed: {
    ...mapGetters([
      'assetStatsDashboard',
      'assetStatsCategoryDistribution',
      'assetStatsUsageFrequency',
      'assetStatsStorage',
      'assetStatsHotnessRanking',
      'assetStatsGrowthTrend',
      'assetStatsCreatorStats',
      'assetStatsIsLoading'
    ]),

    isLoading() {
      return this.assetStatsIsLoading
    },

    dashboardData() {
      return this.assetStatsDashboard || {}
    },

    categoryDistribution() {
      return this.assetStatsCategoryDistribution || []
    },

    usageFrequency() {
      return this.assetStatsUsageFrequency || []
    },

    storageStats() {
      return this.assetStatsStorage || {}
    },

    hotnessRanking() {
      return this.assetStatsHotnessRanking || []
    },

    growthTrend() {
      return this.assetStatsGrowthTrend || []
    },

    creatorStats() {
      return this.assetStatsCreatorStats || []
    },

    recentAssets() {
      // Extract from dashboard or use growth data as fallback
      return this.dashboardData.recent_assets || []
    },

    storageUnit() {
      const bytes = this.dashboardData.total_storage || 0
      if (bytes >= 1073741824) return 'GB'
      if (bytes >= 1048576) return 'MB'
      if (bytes >= 1024) return 'KB'
      return 'B'
    },

    categoryChartData() {
      return this.categoryDistribution.map((item, index) => ({
        label: item.label || item.category,
        value: item.count || 0,
        color: CATEGORY_COLORS[index % CATEGORY_COLORS.length]
      }))
    },

    usageBarData() {
      return this.usageFrequency.map((item, index) => ({
        label: item.period || item.month || `${index + 1}`,
        value: item.count || 0,
        color: '#06b6d4'
      }))
    },

    storageBarData() {
      const categories = this.storageStats.by_category || []
      return categories.map((item, index) => ({
        label: item.label || item.category,
        value: item.size_mb || 0,
        color: STORAGE_COLORS[index % STORAGE_COLORS.length]
      }))
    },

    maxHotness() {
      if (!this.hotnessRanking.length) return 1
      return Math.max(...this.hotnessRanking.map((i) => i.hotness_score || 0)) || 1
    },

    // Line chart coordinates
    pointCoords() {
      if (!this.growthTrend.length) return []
      const w = this.lineChartWidth
      const h = this.lineChartHeight
      const p = this.lineChartPadding
      const values = this.growthTrend.map((d) => d.count || d.cumulative || 0)
      const maxVal = Math.max(...values) || 1
      const step = (w - p * 2) / Math.max(values.length - 1, 1)

      return values.map((val, i) => ({
        x: p + i * step,
        y: h - p - ((val / maxVal) * (h - p * 2))
      }))
    },

    linePoints() {
      return this.pointCoords.map((pt) => `${pt.x},${pt.y}`).join(' ')
    },

    areaPoints() {
      if (!this.pointCoords.length) return ''
      const pts = [...this.pointCoords]
      const first = pts[0]
      const last = pts[pts.length - 1]
      const bottom = this.lineChartHeight - this.lineChartPadding
      return `${first.x},${bottom} ` +
        pts.map((pt) => `${pt.x},${pt.y}`).join(' ') +
        ` ${last.x},${bottom}`
    }
  },

  methods: {
    ...mapActions(['loadAllAssetStats']),

    refreshAll() {
      this.loadAllAssetStats()
    },

    formatStorage(bytes) {
      if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1)
      if (bytes >= 1048576) return (bytes / 1048576).toFixed(1)
      if (bytes >= 1024) return (bytes / 1024).toFixed(1)
      return bytes
    },

    formatDate(dateStr) {
      if (!dateStr) return '-'
      const d = new Date(dateStr)
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${month}-${day}`
    },

    rankClass(index) {
      if (index === 0) return 'rank-gold'
      if (index === 1) return 'rank-silver'
      if (index === 2) return 'rank-bronze'
      return ''
    },

    getThumbnailUrl(item) {
      if (item.preview_file_id) {
        return `/api/pictures/previews/preview-files/${item.preview_file_id}.png`
      }
      return ''
    },

    getAvatarUrl(person) {
      if (person && person.id) {
        return `/api/pictures/thumbnails/persons/${person.id}.png`
      }
      return ''
    },

    getInitials(person) {
      if (!person) return '?'
      const name = person.full_name || person.first_name || ''
      return name.charAt(0).toUpperCase() || '?'
    },

    getPersonName(person) {
      if (!person) return '-'
      return person.full_name || `${person.first_name || ''} ${person.last_name || ''}`.trim() || '-'
    },

    getHotnessPercent(item) {
      return Math.min(((item.hotness_score || 0) / this.maxHotness) * 100, 100)
    },

    onThumbError(e) {
      e.target.style.display = 'none'
    }
  },

  head() {
    return {
      title: '资产统计看板 - Kitsu'
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5em;
  padding: 4em 2em 2em 2em;
  background: #1a1a2e;
  min-height: 100vh;
  color: #e2e8f0;
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dashboard-title {
  font-size: 1.5em;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.4em;
  padding: 0.5em 1em;
  border-radius: 0.5em;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #16213e;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.85em;
  transition: background 0.2s, color 0.2s;

  &:hover {
    background: #1e293b;
    color: #e2e8f0;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinning {
  animation: spin 1s linear infinite;
}

/* KPI Row */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1em;
}

@media screen and (max-width: 900px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media screen and (max-width: 500px) {
  .kpi-row {
    grid-template-columns: 1fr;
  }
}

/* Chart Row */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 1em;
}

@media screen and (max-width: 768px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
}

.chart-panel {
  background: #16213e;
  border-radius: 1em;
  padding: 1.2em 1.4em;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.chart-panel-wide {
  /* Same styling, just semantic marker for grid */
}

.full-width {
  grid-column: 1 / -1;
}

.panel-title {
  font-size: 0.95em;
  font-weight: 600;
  color: #cbd5e1;
  margin: 0 0 1em 0;
  padding-bottom: 0.5em;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.chart-empty {
  color: #64748b;
  font-size: 0.85em;
  text-align: center;
  padding: 2em 0;
}

/* Line Chart */
.line-chart-container {
  width: 100%;
}

.line-chart-svg {
  width: 100%;
  height: 180px;
}

.line-chart-labels {
  display: flex;
  justify-content: space-between;
  padding: 0.3em 1.8em;
}

.line-label {
  font-size: 0.65em;
  color: #64748b;
}

/* Ranking Table */
.ranking-table-wrapper {
  overflow-x: auto;
}

.ranking-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85em;

  th {
    text-align: left;
    color: #64748b;
    font-weight: 500;
    padding: 0.6em 0.8em;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    white-space: nowrap;
  }

  td {
    padding: 0.6em 0.8em;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    color: #cbd5e1;
  }

  tr:hover td {
    background: rgba(255, 255, 255, 0.02);
  }
}

.col-rank { width: 40px; text-align: center; }
.col-thumb { width: 44px; }
.col-name { min-width: 120px; }
.col-category { width: 80px; }
.col-hotness { width: 60px; text-align: right; }
.col-bar { width: 150px; }
.col-meta { width: 120px; text-align: center; color: #94a3b8 !important; }

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.8em;
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
}

.rank-gold { background: #f59e0b30; color: #f59e0b; }
.rank-silver { background: #94a3b830; color: #94a3b8; }
.rank-bronze { background: #d9764030; color: #d97640; }

.thumb-box {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  overflow: hidden;
  background: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.thumb-placeholder {
  font-size: 0.9em;
  font-weight: 600;
  color: #64748b;
}

.category-tag {
  display: inline-block;
  padding: 0.15em 0.5em;
  border-radius: 4px;
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  font-size: 0.85em;
}

.hotness-bar-bg {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.hotness-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #6366f1, #06b6d4);
  transition: width 0.4s ease;
}

/* Creator List */
.creator-list {
  display: flex;
  flex-direction: column;
  gap: 0.6em;
}

.creator-item {
  display: flex;
  align-items: center;
  gap: 0.6em;
  padding: 0.4em 0;
}

.creator-rank {
  width: 20px;
  text-align: center;
  font-size: 0.8em;
  font-weight: 600;
  color: #64748b;
}

.creator-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.avatar-placeholder {
  font-size: 0.8em;
  font-weight: 600;
  color: #64748b;
}

.creator-name {
  flex: 1;
  font-size: 0.85em;
  color: #cbd5e1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.creator-count {
  font-size: 0.8em;
  color: #94a3b8;
  font-weight: 600;
}

/* Recent Assets */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 0.5em;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 0.8em;
  padding: 0.4em 0;
}

.recent-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6366f1;
  flex-shrink: 0;
}

.recent-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.recent-name {
  font-size: 0.85em;
  color: #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-category {
  font-size: 0.7em;
  color: #64748b;
}

.recent-time {
  font-size: 0.75em;
  color: #64748b;
  white-space: nowrap;
}
</style>
