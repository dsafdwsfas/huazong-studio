<template>
  <div class="production-dashboard page fixed-page">
    <div class="flexrow page-header">
      <page-title class="filler" :text="pageTitle" />
      <button-simple
        class="flexrow-item"
        :text="$t('main.reload')"
        :is-loading="loading"
        icon="refresh"
        @click="loadDashboard"
      />
    </div>

    <div class="dashboard-content" v-if="!loading && dashboardData">
      <!-- Stats Cards -->
      <div class="stats-cards">
        <div class="stats-card">
          <div class="stats-card-value">{{ dashboardData.tasks.total }}</div>
          <div class="stats-card-label">总任务数</div>
        </div>
        <div class="stats-card completion">
          <div class="stats-card-value">
            {{ dashboardData.tasks.completion_rate }}%
          </div>
          <div class="stats-card-label">完成率</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">{{ dashboardData.assets.total }}</div>
          <div class="stats-card-label">资产数量</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">{{ dashboardData.shots.total }}</div>
          <div class="stats-card-label">镜头数量</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">
            {{ dashboardData.shots.sequences }}
          </div>
          <div class="stats-card-label">场次数量</div>
        </div>
        <div class="stats-card">
          <div class="stats-card-value">{{ dashboardData.team.size }}</div>
          <div class="stats-card-label">团队人数</div>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="progress-section" v-if="dashboardData.tasks.total > 0">
        <h3 class="section-title">任务进度</h3>
        <div class="progress-bar-container">
          <div class="progress-bar">
            <div
              class="progress-segment"
              v-for="status in dashboardData.tasks.statuses"
              :key="status.name"
              :style="{
                backgroundColor: status.color,
                width: segmentWidth(status.count) + '%'
              }"
              :title="`${status.name}: ${status.count} 个任务`"
            ></div>
          </div>
          <div class="progress-legend">
            <span
              class="legend-item"
              v-for="status in dashboardData.tasks.statuses"
              :key="status.name"
            >
              <span
                class="legend-color"
                :style="{ backgroundColor: status.color }"
              ></span>
              {{ status.name }} ({{ status.count }})
            </span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div class="empty-state" v-if="dashboardData.tasks.total === 0">
        <p>该项目暂无任务数据。请先创建资产和镜头任务。</p>
      </div>
    </div>

    <spinner full v-if="loading" />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import PageTitle from '@/components/widgets/PageTitle.vue'
import Spinner from '@/components/widgets/Spinner.vue'
import productionsApi from '@/store/api/productions'

export default {
  name: 'production-dashboard',

  components: {
    ButtonSimple,
    PageTitle,
    Spinner
  },

  data() {
    return {
      loading: false,
      dashboardData: null
    }
  },

  computed: {
    ...mapGetters(['currentProduction']),

    pageTitle() {
      const name = this.currentProduction?.name || ''
      return `${name} — 项目仪表盘`
    }
  },

  mounted() {
    this.loadDashboard()
  },

  methods: {
    async loadDashboard() {
      if (!this.currentProduction?.id) return
      this.loading = true
      try {
        this.dashboardData = await productionsApi.getProductionDashboard(
          this.currentProduction.id
        )
      } catch (err) {
        console.error('Failed to load dashboard:', err)
      }
      this.loading = false
    },

    segmentWidth(count) {
      if (!this.dashboardData || this.dashboardData.tasks.total === 0) return 0
      return (count / this.dashboardData.tasks.total) * 100
    }
  },

  watch: {
    currentProduction() {
      this.loadDashboard()
    }
  },

  metaInfo() {
    return { title: `${this.currentProduction?.name || ''} - 仪表盘` }
  }
}
</script>

<style lang="scss" scoped>
.production-dashboard {
  padding: 20px;
}

.dashboard-content {
  margin-top: 20px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stats-card {
  background: var(--background-alt, #f8f8f8);
  border: 1px solid var(--border, #eee);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  &.completion {
    border-color: var(--green, #22d160);
  }
}

.stats-card-value {
  font-size: 2em;
  font-weight: 700;
  color: var(--text, #333);
  line-height: 1.2;
}

.stats-card-label {
  font-size: 0.85em;
  color: var(--text-alt, #999);
  margin-top: 4px;
}

.section-title {
  font-size: 1.1em;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text, #333);
}

.progress-section {
  margin-bottom: 32px;
}

.progress-bar-container {
  background: var(--background-alt, #f8f8f8);
  border: 1px solid var(--border, #eee);
  border-radius: 8px;
  padding: 20px;
}

.progress-bar {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--border, #eee);
}

.progress-segment {
  height: 100%;
  min-width: 2px;
  transition: width 0.3s ease;
}

.progress-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85em;
  color: var(--text-alt, #666);
}

.legend-color {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-alt, #999);
  font-size: 1.1em;
}
</style>
