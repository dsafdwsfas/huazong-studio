<template>
  <div class="version-panel" v-if="active">
    <div class="panel-header">
      <h4>版本管理</h4>
      <span class="shot-name">{{ shotName }}</span>
      <button class="btn-close" @click="$emit('close')">
        <XIcon :size="16" />
      </button>
    </div>

    <div class="panel-actions">
      <label class="btn-upload">
        <UploadIcon :size="14" />
        上传新版本
        <input
          type="file"
          accept="image/*"
          class="file-input"
          @change="onFileSelected"
        />
      </label>
    </div>

    <div v-if="isLoading" class="loading">
      <spinner />
    </div>

    <div v-else-if="versions.length === 0" class="empty">
      暂无版本
    </div>

    <div v-else class="version-list">
      <div
        v-for="version in versions"
        :key="version.id"
        class="version-item"
        :class="{ current: version.is_current }"
      >
        <div class="version-thumb">
          <img
            :src="version.thumbnail_url"
            :alt="`v${version.revision}`"
            loading="lazy"
          />
        </div>
        <div class="version-info">
          <div class="version-header">
            <span class="version-num">v{{ version.revision }}</span>
            <span v-if="version.is_current" class="current-badge">当前</span>
          </div>
          <div class="version-meta">
            <span v-if="version.uploader" class="uploader">
              {{ version.uploader.name }}
            </span>
            <span v-if="version.created_at" class="date">
              {{ formatDate(version.created_at) }}
            </span>
          </div>
          <div class="version-detail">
            <span v-if="version.width && version.height" class="dimensions">
              {{ version.width }}×{{ version.height }}
            </span>
            <span v-if="version.file_size" class="size">
              {{ formatSize(version.file_size) }}
            </span>
          </div>
        </div>
        <div class="version-actions">
          <button
            v-if="!version.is_current"
            class="btn-set-active"
            title="设为当前版本"
            @click="setActive(version)"
          >
            <CheckCircleIcon :size="16" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import {
  CheckCircleIcon,
  UploadIcon,
  XIcon
} from 'lucide-vue-next'

export default {
  name: 'VersionPanel',

  components: {
    CheckCircleIcon,
    UploadIcon,
    XIcon
  },

  props: {
    active: {
      type: Boolean,
      default: false
    },
    projectId: {
      type: String,
      default: ''
    },
    shotId: {
      type: String,
      default: ''
    },
    shotName: {
      type: String,
      default: ''
    }
  },

  emits: ['close', 'version-changed'],

  data() {
    return {
      versions: [],
      isLoading: false
    }
  },

  watch: {
    active(val) {
      if (val && this.shotId) {
        this.loadVersions()
      }
    },
    shotId() {
      if (this.active && this.shotId) {
        this.loadVersions()
      }
    }
  },

  methods: {
    ...mapActions([
      'loadShotVersions',
      'createShotVersion',
      'setShotVersionActive'
    ]),

    async loadVersions() {
      this.isLoading = true
      try {
        const result = await this.loadShotVersions({
          projectId: this.projectId,
          shotId: this.shotId
        })
        this.versions = result.versions || []
      } catch (err) {
        console.error('Failed to load versions:', err)
        this.versions = []
      } finally {
        this.isLoading = false
      }
    },

    async onFileSelected(event) {
      const file = event.target.files?.[0]
      if (!file) return
      event.target.value = ''

      try {
        const ext = file.name.split('.').pop()?.toLowerCase() || 'png'
        // Step 1: Create PreviewFile record
        const result = await this.createShotVersion({
          projectId: this.projectId,
          shotId: this.shotId,
          name: file.name,
          extension: ext
        })

        // Step 2: Upload actual file
        const formData = new FormData()
        formData.append('file', file)
        await fetch(`/api/data/preview-files/${result.id}`, {
          method: 'POST',
          body: formData,
          credentials: 'same-origin'
        })

        // Reload versions
        await this.loadVersions()
        this.$emit('version-changed')
      } catch (err) {
        console.error('Failed to upload version:', err)
      }
    },

    async setActive(version) {
      try {
        await this.setShotVersionActive({
          projectId: this.projectId,
          shotId: this.shotId,
          previewFileId: version.id
        })

        // Update local state
        for (const v of this.versions) {
          v.is_current = v.id === version.id
        }
        this.$emit('version-changed')
      } catch (err) {
        console.error('Failed to set active version:', err)
      }
    },

    formatDate(isoString) {
      if (!isoString) return ''
      const d = new Date(isoString)
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const h = String(d.getHours()).padStart(2, '0')
      const min = String(d.getMinutes()).padStart(2, '0')
      return `${m}-${day} ${h}:${min}`
    },

    formatSize(bytes) {
      if (!bytes) return ''
      if (bytes < 1024) return `${bytes}B`
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
      return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
    }
  }
}
</script>

<style lang="scss" scoped>
.version-panel {
  width: 280px;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
  flex-shrink: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);

  h4 {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
  }

  .shot-name {
    flex: 1;
    font-size: 0.8rem;
    color: var(--text-alt);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-alt);
  padding: 4px;
  border-radius: 4px;

  &:hover {
    background: var(--background-hover);
  }
}

.panel-actions {
  padding: 8px 16px;
  border-bottom: 1px solid var(--border);
}

.btn-upload {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px dashed var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  font-size: 0.8rem;
  cursor: pointer;
  width: 100%;
  justify-content: center;
  transition: all 0.15s;

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }
}

.file-input {
  display: none;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: var(--text-alt);
  font-size: 0.85rem;
}

.version-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.version-item {
  display: flex;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 4px;
  transition: background 0.15s;

  &:hover {
    background: var(--background-hover, rgba(0, 0, 0, 0.03));
  }

  &.current {
    background: var(--background-selected, rgba(0, 120, 255, 0.06));
    border: 1px solid var(--color-primary, #0078ff);
    border-radius: 8px;
  }
}

.version-thumb {
  width: 64px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background: var(--background-alt);

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.version-info {
  flex: 1;
  min-width: 0;
}

.version-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.version-num {
  font-weight: 600;
  font-size: 0.8rem;
}

.current-badge {
  font-size: 0.6rem;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--color-primary);
  color: #fff;
}

.version-meta {
  display: flex;
  gap: 6px;
  font-size: 0.7rem;
  color: var(--text-alt);
  margin-top: 2px;
}

.version-detail {
  display: flex;
  gap: 6px;
  font-size: 0.65rem;
  color: var(--text-alt);
  margin-top: 1px;
}

.version-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.btn-set-active {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-alt);
  cursor: pointer;

  &:hover {
    background: var(--background-hover);
    color: var(--color-primary);
  }
}
</style>
