<template>
  <div class="stat-card" :style="cardStyle">
    <div class="stat-card-icon" :style="iconStyle">
      <component :is="iconComponent" :size="20" v-if="iconComponent" />
      <span v-else class="stat-card-icon-fallback">{{ iconFallback }}</span>
    </div>
    <div class="stat-card-body">
      <div class="stat-card-value">
        {{ formattedValue }}<span class="stat-card-suffix" v-if="suffix">{{ suffix }}</span>
      </div>
      <div class="stat-card-title">{{ title }}</div>
    </div>
  </div>
</template>

<script>
import {
  PackageIcon,
  MousePointerClickIcon,
  HardDriveIcon,
  NetworkIcon,
  BarChart3Icon,
  UsersIcon,
  TrendingUpIcon,
  DatabaseIcon
} from 'lucide-vue-next'

const ICON_MAP = {
  package: PackageIcon,
  click: MousePointerClickIcon,
  'hard-drive': HardDriveIcon,
  network: NetworkIcon,
  'bar-chart': BarChart3Icon,
  users: UsersIcon,
  'trending-up': TrendingUpIcon,
  database: DatabaseIcon
}

export default {
  name: 'stat-card',

  props: {
    title: {
      type: String,
      required: true
    },
    value: {
      type: [Number, String],
      default: 0
    },
    icon: {
      type: String,
      default: 'package'
    },
    color: {
      type: String,
      default: '#6366f1'
    },
    suffix: {
      type: String,
      default: ''
    }
  },

  computed: {
    iconComponent() {
      return ICON_MAP[this.icon] || null
    },

    iconFallback() {
      return this.title ? this.title.charAt(0) : '#'
    },

    formattedValue() {
      const num = Number(this.value)
      if (isNaN(num)) return this.value
      if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
      if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
      return num.toLocaleString()
    },

    cardStyle() {
      return {
        '--accent-color': this.color,
        '--accent-color-dim': this.color + '20'
      }
    },

    iconStyle() {
      return {
        backgroundColor: this.color + '20',
        color: this.color
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.stat-card {
  background: #16213e;
  border-radius: 1em;
  padding: 1.2em 1.4em;
  display: flex;
  align-items: center;
  gap: 1em;
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }
}

.stat-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 0.75em;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card-icon-fallback {
  font-size: 1.2em;
  font-weight: 700;
}

.stat-card-body {
  min-width: 0;
}

.stat-card-value {
  font-size: 1.6em;
  font-weight: 700;
  color: #e2e8f0;
  line-height: 1.2;
}

.stat-card-suffix {
  font-size: 0.55em;
  font-weight: 400;
  color: #94a3b8;
  margin-left: 0.25em;
}

.stat-card-title {
  font-size: 0.8em;
  color: #94a3b8;
  margin-top: 0.15em;
}
</style>
