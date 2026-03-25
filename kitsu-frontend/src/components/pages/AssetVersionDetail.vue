<template>
  <div class="asset-version-detail">
    <header class="flexrow page-header">
      <button-simple
        class="flexrow-item back-button"
        icon="arrow-left"
        :text="'返回资产库'"
        @click="goBack"
      />
      <h1 class="filler page-title-text" v-if="assetName">
        {{ assetName }} &middot; 版本历史
      </h1>
    </header>

    <table-info
      :is-loading="isLoading"
      :is-error="hasError"
      v-if="isLoading || hasError"
    />

    <div class="content-layout flexrow" v-else>
      <!-- Version list sidebar -->
      <div class="version-sidebar">
        <h3>版本列表</h3>
        <div class="version-list">
          <div
            class="version-item"
            :class="{
              selected: isSelected(version.id),
              current: version.is_current
            }"
            :key="version.id"
            @click="onVersionClick(version)"
            v-for="version in versions"
          >
            <div class="version-item-header flexrow">
              <span class="version-dot" :class="{ active: isSelected(version.id) }"></span>
              <span class="version-num">v{{ version.number }}</span>
              <span class="version-current-badge" v-if="version.is_current">
                当前
              </span>
            </div>
            <div class="version-item-meta">
              {{ formatDate(version.created_at) }}
              <template v-if="version.author">
                &middot; {{ version.author }}
              </template>
            </div>
            <div class="version-item-summary" v-if="version.summary">
              {{ version.summary }}
            </div>
          </div>
        </div>

        <div class="compare-hint" v-if="versions.length >= 2">
          点击选择版本进行对比。默认显示最新版本与前一版本的差异。
        </div>
      </div>

      <!-- Diff area -->
      <div class="diff-area filler">
        <div class="diff-controls flexrow">
          <div class="compare-selector flexrow">
            <label>对比:</label>
            <select v-model="compareA" class="version-select">
              <option
                :value="v.id"
                :key="'a-' + v.id"
                v-for="v in versions"
              >
                v{{ v.number }} - {{ formatDate(v.created_at) }}
              </option>
            </select>
            <span class="compare-arrow">&rarr;</span>
            <select v-model="compareB" class="version-select">
              <option
                :value="v.id"
                :key="'b-' + v.id"
                v-for="v in versions"
              >
                v{{ v.number }} - {{ formatDate(v.created_at) }}
              </option>
            </select>
          </div>
          <span class="filler"></span>
          <button-simple
            class="restore-button"
            icon="rotate-ccw"
            :text="'恢复到 v' + getVersionNumber(compareA)"
            @click="onRestore"
            v-if="compareA && !isCurrentVersion(compareA)"
          />
        </div>

        <div class="diff-loading" v-if="isDiffLoading">
          <table-info :is-loading="true" />
        </div>

        <div class="diff-content" v-else-if="diffData">
          <asset-version-diff
            :diff="diffData"
            :version-a="getVersionInfo(compareA)"
            :version-b="getVersionInfo(compareB)"
          />
        </div>

        <div class="diff-empty" v-else>
          <p>请选择两个版本进行对比</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AssetVersionDiff from '@/components/widgets/AssetVersionDiff.vue'
import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import TableInfo from '@/components/widgets/TableInfo.vue'

import assetVersionsApi from '@/store/api/asset_versions'
import globalAssetsApi from '@/store/api/global_assets'

export default {
  name: 'asset-version-detail',

  components: {
    AssetVersionDiff,
    ButtonSimple,
    TableInfo
  },

  data() {
    return {
      assetId: null,
      assetName: '',
      versions: [],
      compareA: null,
      compareB: null,
      diffData: null,
      isLoading: false,
      isDiffLoading: false,
      hasError: false
    }
  },

  mounted() {
    this.assetId = this.$route.params.assetId
    this.init()
  },

  methods: {
    async init() {
      this.isLoading = true
      this.hasError = false
      try {
        // Load asset info
        const assetRes = await globalAssetsApi.getAsset(this.assetId)
        this.assetName = assetRes.name || '未知资产'

        // Load versions
        const versionsRes = await assetVersionsApi.getVersions(this.assetId, 1, 100)
        this.versions = versionsRes.data || versionsRes || []

        // Set initial comparison from query params or defaults
        this.initComparison()
      } catch (err) {
        console.error('Failed to load asset versions:', err)
        this.hasError = true
      } finally {
        this.isLoading = false
      }
    },

    initComparison() {
      const queryV = this.$route.query.v
      const queryCompare = this.$route.query.compare

      if (queryV && queryCompare) {
        this.compareA = queryV
        this.compareB = queryCompare
      } else if (this.versions.length >= 2) {
        // Default: compare latest two versions
        this.compareA = this.versions[1].id
        this.compareB = this.versions[0].id
      } else if (this.versions.length === 1) {
        this.compareA = this.versions[0].id
        this.compareB = this.versions[0].id
      }

      if (this.compareA && this.compareB) {
        this.loadDiff()
      }
    },

    async loadDiff() {
      if (!this.compareA || !this.compareB) return
      if (this.compareA === this.compareB) {
        this.diffData = {}
        return
      }

      this.isDiffLoading = true
      try {
        const res = await assetVersionsApi.compareVersions(
          this.compareA,
          this.compareB
        )
        this.diffData = res.diff || res || {}
      } catch (err) {
        console.error('Failed to load version diff:', err)
        this.diffData = null
      } finally {
        this.isDiffLoading = false
      }
    },

    onVersionClick(version) {
      // If no compareA set, set it. Otherwise swap into compareB.
      if (!this.compareA) {
        this.compareA = version.id
      } else if (this.compareA === version.id) {
        // Clicking same version — do nothing
        return
      } else {
        this.compareA = this.compareB
        this.compareB = version.id
      }
      this.updateQueryParams()
      this.loadDiff()
    },

    isSelected(versionId) {
      return versionId === this.compareA || versionId === this.compareB
    },

    isCurrentVersion(versionId) {
      const v = this.versions.find((ver) => ver.id === versionId)
      return v && v.is_current
    },

    getVersionNumber(versionId) {
      const v = this.versions.find((ver) => ver.id === versionId)
      return v ? v.number : '?'
    },

    getVersionInfo(versionId) {
      const v = this.versions.find((ver) => ver.id === versionId)
      if (!v) return { number: 0, created_at: '', author: '' }
      return {
        number: v.number,
        created_at: v.created_at,
        author: v.author
      }
    },

    async onRestore() {
      if (!this.compareA) return
      const vNum = this.getVersionNumber(this.compareA)
      if (!confirm(`确定要恢复到版本 v${vNum} 吗？此操作将创建一个新版本。`)) {
        return
      }

      try {
        await assetVersionsApi.restoreVersion(this.assetId, this.compareA)
        // Reload versions to see the newly created version
        const versionsRes = await assetVersionsApi.getVersions(this.assetId, 1, 100)
        this.versions = versionsRes.data || versionsRes || []
        this.initComparison()
      } catch (err) {
        console.error('Failed to restore version:', err)
      }
    },

    updateQueryParams() {
      const query = {}
      if (this.compareA) query.v = this.compareA
      if (this.compareB) query.compare = this.compareB
      this.$router.replace({ query }).catch(() => {})
    },

    goBack() {
      this.$router.push({ name: 'global-asset-library' })
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      const year = d.getFullYear()
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const hours = String(d.getHours()).padStart(2, '0')
      const minutes = String(d.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}`
    }
  },

  watch: {
    compareA() {
      this.updateQueryParams()
      this.loadDiff()
    },
    compareB() {
      this.updateQueryParams()
      this.loadDiff()
    }
  },

  head() {
    return {
      title: `${this.assetName || '资产'} · 版本历史 - Kitsu`
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-version-detail {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  padding: 4em 2em 1em 2em;
  color: var(--text);
}

.page-header {
  align-items: center;
  margin-bottom: 1.5em;
  gap: 1em;
}

.back-button {
  flex-shrink: 0;
}

.page-title-text {
  margin: 0;
  font-size: 1.2em;
  font-weight: 600;
  color: var(--text-strong);
}

.content-layout {
  flex: 1;
  min-height: 0;
  gap: 1.5em;
  align-items: flex-start;
}

// Version sidebar
.version-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--background);
  border-radius: 0.8em;
  padding: 1em;
  border: 1px solid var(--border);
  max-height: calc(100vh - 200px);
  overflow-y: auto;

  h3 {
    font-size: 0.95em;
    font-weight: 600;
    margin: 0 0 0.8em 0;
    color: var(--text-strong);
  }
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 0.3em;
}

.version-item {
  padding: 0.6em 0.8em;
  border-radius: 0.5em;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.15s;

  &:hover {
    background: var(--background-hover);
  }

  &.selected {
    border-color: var(--background-selected);
    background: var(--background-selectable);
  }

  &.current .version-num {
    font-weight: 700;
  }
}

.version-item-header {
  align-items: center;
  gap: 0.4em;
  margin-bottom: 0.2em;
}

.version-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-alt);
  flex-shrink: 0;

  &.active {
    background: var(--background-selected);
  }
}

.version-num {
  font-size: 0.95em;
  font-weight: 600;
  color: var(--text-strong);
}

.version-current-badge {
  font-size: 0.7em;
  padding: 0.1em 0.4em;
  border-radius: 0.3em;
  background: #2d5a3d;
  color: #a3d9b1;
  font-weight: 500;
}

.version-item-meta {
  font-size: 0.8em;
  color: var(--text-alt);
}

.version-item-summary {
  font-size: 0.8em;
  color: var(--text);
  margin-top: 0.2em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compare-hint {
  margin-top: 1em;
  font-size: 0.75em;
  color: var(--text-alt);
  line-height: 1.4;
}

// Diff area
.diff-area {
  min-width: 0;
}

.diff-controls {
  margin-bottom: 1em;
  align-items: center;
  gap: 1em;
  flex-wrap: wrap;
}

.compare-selector {
  align-items: center;
  gap: 0.5em;

  label {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--text-strong);
    white-space: nowrap;
  }
}

.version-select {
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 0.5em;
  padding: 0.4em 0.8em;
  color: var(--text);
  font-size: 0.85em;
  cursor: pointer;
  max-width: 250px;

  &:focus {
    outline: none;
    border-color: var(--background-selected);
  }
}

.compare-arrow {
  font-size: 1.2em;
  color: var(--text-alt);
}

.restore-button {
  flex-shrink: 0;
  color: #e8a948;
}

.diff-loading,
.diff-empty {
  padding: 3em;
  text-align: center;
  color: var(--text-alt);
}

.diff-content {
  min-width: 0;
}
</style>
