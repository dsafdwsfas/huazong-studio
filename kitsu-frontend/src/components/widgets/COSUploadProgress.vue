<template>
  <div class="cos-upload-progress" v-if="uploads.length > 0">
    <div class="upload-header flexrow">
      <span class="upload-title">
        {{ isResuming ? '恢复上传中' : '文件上传中' }}
        ({{ completedCount }}/{{ uploads.length }})
      </span>
      <span class="upload-actions">
        <button
          class="button is-small"
          :title="allPaused ? '全部继续' : '全部暂停'"
          @click="togglePauseAll"
          v-if="hasActiveUploads"
        >
          <play-icon class="icon" v-if="allPaused" />
          <pause-icon class="icon" v-else />
        </button>
        <button
          class="button is-small"
          title="全部取消"
          @click="cancelAll"
          v-if="hasActiveUploads"
        >
          <x-icon class="icon" />
        </button>
      </span>
    </div>

    <div class="upload-list">
      <div
        v-for="upload in uploads"
        :key="upload.id"
        class="upload-item"
        :class="{ 'is-error': upload.error, 'is-complete': upload.complete }"
      >
        <div class="upload-item-header flexrow">
          <span class="upload-file-name" :title="upload.fileName">
            {{ shortenText(upload.fileName, 35) }}
          </span>
          <span class="upload-file-size">
            {{ formatBytes(upload.loaded) }} / {{ formatBytes(upload.total) }}
          </span>
        </div>

        <div class="progress-wrapper">
          <div
            class="progress"
            :class="{
              'is-paused': upload.paused,
              'is-error': upload.error,
              'is-complete': upload.complete
            }"
            :style="{ width: upload.percent + '%' }"
          ></div>
        </div>

        <div class="upload-item-footer flexrow">
          <span class="upload-speed" v-if="!upload.complete && !upload.error">
            {{ upload.paused ? '已暂停' : formatSpeed(upload.speed) }}
            <template v-if="!upload.paused && upload.eta">
              &middot; 剩余 {{ formatDuration(upload.eta) }}
            </template>
          </span>
          <span class="upload-status" v-if="upload.complete">
            上传完成
          </span>
          <span class="upload-status is-error" v-if="upload.error">
            {{ upload.errorMessage || '上传失败' }}
          </span>
          <span
            class="upload-resume-badge"
            v-if="upload.resumed"
          >
            已恢复
          </span>
          <span class="upload-item-actions" v-if="!upload.complete && !upload.error">
            <button
              class="button is-small"
              :title="upload.paused ? '继续' : '暂停'"
              @click="$emit('toggle-pause', upload.id)"
            >
              <play-icon class="icon" v-if="upload.paused" />
              <pause-icon class="icon" v-else />
            </button>
            <button
              class="button is-small"
              title="取消"
              @click="$emit('cancel', upload.id)"
            >
              <x-icon class="icon" />
            </button>
          </span>
        </div>
      </div>
    </div>

    <div class="upload-overall" v-if="uploads.length > 1">
      <div class="progress-wrapper overall">
        <div
          class="progress"
          :style="{ width: overallPercent + '%' }"
        ></div>
      </div>
      <span class="upload-overall-text">
        总计 {{ formatBytes(overallLoaded) }} / {{ formatBytes(overallTotal) }}
        &middot; {{ formatSpeed(overallSpeed) }}
      </span>
    </div>
  </div>
</template>

<script>
import { PauseIcon, PlayIcon, XIcon } from 'lucide-vue-next'
import { formatBytes, formatDuration } from '@/lib/cos-upload'

export default {
  name: 'cos-upload-progress',

  components: {
    PauseIcon,
    PlayIcon,
    XIcon
  },

  props: {
    /**
     * Array of upload state objects:
     * {
     *   id: string,
     *   fileName: string,
     *   percent: number,
     *   loaded: number,
     *   total: number,
     *   speed: number,       // bytes/sec
     *   eta: number,         // seconds
     *   paused: boolean,
     *   complete: boolean,
     *   error: boolean,
     *   errorMessage: string,
     *   resumed: boolean
     * }
     */
    uploads: {
      type: Array,
      default: () => []
    },
    isResuming: {
      type: Boolean,
      default: false
    }
  },

  emits: ['toggle-pause', 'cancel', 'toggle-pause-all', 'cancel-all'],

  computed: {
    completedCount() {
      return this.uploads.filter(u => u.complete).length
    },

    hasActiveUploads() {
      return this.uploads.some(u => !u.complete && !u.error)
    },

    allPaused() {
      const active = this.uploads.filter(u => !u.complete && !u.error)
      return active.length > 0 && active.every(u => u.paused)
    },

    overallLoaded() {
      return this.uploads.reduce((sum, u) => sum + (u.loaded || 0), 0)
    },

    overallTotal() {
      return this.uploads.reduce((sum, u) => sum + (u.total || 0), 0)
    },

    overallPercent() {
      if (this.overallTotal === 0) return 0
      return Math.min(100, (this.overallLoaded / this.overallTotal) * 100)
    },

    overallSpeed() {
      return this.uploads
        .filter(u => !u.complete && !u.error && !u.paused)
        .reduce((sum, u) => sum + (u.speed || 0), 0)
    }
  },

  methods: {
    formatBytes,
    formatDuration,

    formatSpeed(bytesPerSec) {
      if (!bytesPerSec || bytesPerSec === 0) return '0 B/s'
      return formatBytes(bytesPerSec) + '/s'
    },

    shortenText(text, maxLength) {
      if (!text) return ''
      if (text.length <= maxLength) return text
      const ext = text.lastIndexOf('.')
      if (ext > 0 && text.length - ext < 8) {
        const extension = text.slice(ext)
        const name = text.slice(0, maxLength - extension.length - 3)
        return name + '...' + extension
      }
      return text.slice(0, maxLength - 3) + '...'
    },

    togglePauseAll() {
      this.$emit('toggle-pause-all')
    },

    cancelAll() {
      this.$emit('cancel-all')
    }
  }
}
</script>

<style lang="scss" scoped>
.cos-upload-progress {
  background: var(--background-block);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem;
  margin-top: 0.5rem;
}

.upload-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.upload-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-strong);
}

.upload-actions {
  display: flex;
  gap: 4px;

  .button.is-small {
    padding: 2px 6px;
    border-radius: 4px;
    min-width: unset;
    height: 24px;

    .icon {
      width: 14px;
      height: 14px;
    }
  }
}

.upload-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.upload-item {
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--border);

  &:last-child {
    border-bottom: none;
  }

  &.is-complete {
    opacity: 0.7;
  }

  &.is-error {
    .upload-file-name {
      color: var(--brand-accent);
    }
  }
}

.upload-item-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.upload-file-name {
  font-size: 0.8rem;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 60%;
}

.upload-file-size {
  font-size: 0.75rem;
  color: var(--text-alt);
  white-space: nowrap;
}

.progress-wrapper {
  height: 4px;
  background: var(--background-alt);
  border-radius: 2px;
  overflow: hidden;
  margin: 4px 0;

  &.overall {
    height: 6px;
    border-radius: 3px;
    margin-top: 0.5rem;
  }
}

.progress {
  height: 100%;
  background: var(--brand-accent);
  border-radius: 2px;
  transition: width 0.3s ease;

  &.is-paused {
    background: var(--text-alt);
  }

  &.is-error {
    background: var(--brand-accent);
  }

  &.is-complete {
    background: $green;
  }
}

.upload-item-footer {
  justify-content: space-between;
  align-items: center;
  margin-top: 2px;
}

.upload-speed {
  font-size: 0.7rem;
  color: var(--text-alt);
}

.upload-status {
  font-size: 0.7rem;
  color: $green;

  &.is-error {
    color: var(--brand-accent);
  }
}

.upload-resume-badge {
  font-size: 0.65rem;
  background: var(--background-selectable);
  color: var(--text-selectable);
  padding: 1px 6px;
  border-radius: 3px;
  margin-left: 4px;
}

.upload-item-actions {
  display: flex;
  gap: 4px;

  .button.is-small {
    padding: 2px 6px;
    border-radius: 4px;
    min-width: unset;
    height: 22px;

    .icon {
      width: 12px;
      height: 12px;
    }
  }
}

.upload-overall {
  border-top: 1px solid var(--border);
  padding-top: 0.5rem;
  margin-top: 0.25rem;
}

.upload-overall-text {
  font-size: 0.7rem;
  color: var(--text-alt);
  display: block;
  margin-top: 4px;
}
</style>
