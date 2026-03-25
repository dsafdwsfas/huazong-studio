<template>
  <div class="most-used-assets">
    <div class="most-used-header flexrow">
      <h3 class="filler">热门资产排行</h3>
    </div>

    <table-info
      :is-loading="isLoading"
      v-if="isLoading"
    />
    <div
      class="empty-message"
      v-else-if="!mostUsed.length"
    >
      暂无使用数据
    </div>
    <div class="ranking-list" v-else>
      <div
        class="ranking-item"
        :key="asset.id"
        @click="goToAsset(asset)"
        v-for="(asset, index) in mostUsed"
      >
        <span class="ranking-number" :class="getRankClass(index)">
          {{ index + 1 }}
        </span>
        <div class="ranking-thumbnail">
          <img
            :src="asset.thumbnail_url || asset.preview_url"
            :alt="asset.name"
            v-if="asset.thumbnail_url || asset.preview_url"
          />
          <span class="thumbnail-placeholder-sm" v-else>📦</span>
        </div>
        <div class="ranking-info">
          <span class="ranking-name" :title="asset.name">
            {{ asset.name }}
          </span>
          <span class="ranking-category">
            {{ getCategoryLabel(asset.category) }}
          </span>
        </div>
        <span class="ranking-count">
          {{ asset.usage_count || 0 }} 次
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import TableInfo from '@/components/widgets/TableInfo.vue'

export default {
  name: 'most-used-assets',

  components: {
    TableInfo
  },

  props: {
    limit: {
      type: Number,
      default: 10
    }
  },

  mounted() {
    this.loadMostUsedAssets(this.limit)
  },

  computed: {
    ...mapGetters([
      'assetMostUsed',
      'assetUsagesIsLoading',
      'globalAssetCategories',
      'getCategoryById'
    ]),

    mostUsed() {
      return this.assetMostUsed || []
    },

    isLoading() {
      return this.assetUsagesIsLoading
    }
  },

  methods: {
    ...mapActions(['loadMostUsedAssets']),

    getRankClass(index) {
      if (index === 0) return 'rank-gold'
      if (index === 1) return 'rank-silver'
      if (index === 2) return 'rank-bronze'
      return ''
    },

    getCategoryLabel(category) {
      // Try dynamic categories
      if (this.getCategoryById) {
        const dynCat = this.getCategoryById(category)
        if (dynCat) return dynCat.name
      }
      // Fallback to hardcoded
      const cats = this.globalAssetCategories || []
      const found = cats.find((c) => c.value === category)
      return found ? found.label : category || '未分类'
    },

    goToAsset(asset) {
      this.$router.push({
        name: 'global-asset-library',
        query: { assetId: asset.id }
      })
    }
  },

  watch: {
    limit(newVal) {
      this.loadMostUsedAssets(newVal)
    }
  }
}
</script>

<style lang="scss" scoped>
.most-used-assets {
  color: var(--text);
}

.most-used-header {
  align-items: center;
  margin-bottom: 0.8em;

  h3 {
    font-size: 1em;
    font-weight: 600;
    margin: 0;
    color: var(--text-strong);
  }
}

.empty-message {
  padding: 2em;
  text-align: center;
  color: var(--text-alt);
  font-size: 0.9em;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 0.3em;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 0.6em;
  padding: 0.5em 0.6em;
  border-radius: 0.5em;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: var(--background-hover);
  }
}

.ranking-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8em;
  font-weight: 700;
  border-radius: 50%;
  background: var(--background-alt);
  color: var(--text-alt);
  flex-shrink: 0;

  &.rank-gold {
    background: #ffd700;
    color: #5a4800;
  }

  &.rank-silver {
    background: #c0c0c0;
    color: #444;
  }

  &.rank-bronze {
    background: #cd7f32;
    color: #fff;
  }
}

.ranking-thumbnail {
  width: 36px;
  height: 36px;
  border-radius: 0.4em;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--background-alt);
  display: flex;
  align-items: center;
  justify-content: center;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.thumbnail-placeholder-sm {
  font-size: 1em;
  opacity: 0.5;
}

.ranking-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.ranking-name {
  font-size: 0.85em;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ranking-category {
  font-size: 0.7em;
  color: var(--text-alt);
}

.ranking-count {
  font-size: 0.8em;
  font-weight: 600;
  color: var(--text-strong);
  flex-shrink: 0;
  white-space: nowrap;
}
</style>
