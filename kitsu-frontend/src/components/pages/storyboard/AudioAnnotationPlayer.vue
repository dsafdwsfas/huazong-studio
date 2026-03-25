<template>
  <div class="audio-annotation-player" @keydown="onKeydown" tabindex="0">
    <!-- Playback controls -->
    <div class="playback-controls">
      <div class="controls-left">
        <button
          class="control-button"
          title="后退 1s"
          @click="skipBackward"
        >
          <SkipBackIcon :size="14" />
        </button>
        <button
          class="control-button play-button"
          :title="isPlaying ? '暂停' : '播放'"
          @click="togglePlay"
        >
          <PauseIcon v-if="isPlaying" :size="18" />
          <PlayIcon v-else :size="18" />
        </button>
        <button
          class="control-button"
          title="前进 1s"
          @click="skipForward"
        >
          <SkipForwardIcon :size="14" />
        </button>
      </div>

      <div class="controls-center">
        <span class="time-display">
          {{ formattedCurrentTime }} / {{ formattedDuration }}
        </span>
      </div>

      <div class="controls-right">
        <div class="speed-control">
          <select v-model="playbackRate" @change="onSpeedChange">
            <option :value="0.5">0.5x</option>
            <option :value="0.75">0.75x</option>
            <option :value="1">1x</option>
            <option :value="1.25">1.25x</option>
            <option :value="1.5">1.5x</option>
            <option :value="2">2x</option>
          </select>
        </div>
        <button
          class="control-button"
          :title="isMuted ? '取消静音' : '静音'"
          @click="toggleMute"
        >
          <VolumeXIcon v-if="isMuted" :size="16" />
          <Volume2Icon v-else :size="16" />
        </button>
        <input
          type="range"
          class="volume-slider"
          min="0"
          max="1"
          step="0.05"
          :value="volume"
          @input="onVolumeChange"
        />
      </div>
    </div>

    <!-- Marker layer + Waveform -->
    <div class="waveform-section">
      <div class="marker-layer" ref="markerLayer">
        <div
          v-for="(marker, index) in internalMarkers"
          :key="'m-' + index"
          class="marker-flag"
          :class="{ active: activeMarkerIndex === index }"
          :style="{ left: getMarkerPosition(marker) + '%' }"
          :title="marker.label + ' (' + formatSeconds(marker.time) + ')'"
          @click.stop="onMarkerClick(index)"
          @contextmenu.prevent="onMarkerContextMenu($event, index)"
          @mousedown.stop="onMarkerDragStart($event, index)"
        >
          <span class="marker-triangle">&#9660;</span>
          <div class="marker-line"></div>
        </div>
      </div>
      <div class="waveform-container" ref="waveform">
        <div v-if="isLoading" class="waveform-loading">
          <span class="loading-spinner"></span>
        </div>
      </div>
    </div>

    <!-- Marker management -->
    <div class="marker-controls">
      <div class="marker-actions">
        <button class="control-button add-marker-btn" @click="addMarker">
          <PlusIcon :size="14" />
          <span>添加标记</span>
        </button>
      </div>
      <div class="marker-list" v-if="internalMarkers.length > 0">
        <button
          v-for="(marker, index) in internalMarkers"
          :key="'ml-' + index"
          class="marker-chip"
          :class="{ active: activeMarkerIndex === index }"
          :title="marker.label"
          @click="onMarkerClick(index)"
          @contextmenu.prevent="onMarkerContextMenu($event, index)"
        >
          <span class="chip-dot"></span>
          <span class="chip-label">{{ marker.label }}</span>
          <span class="chip-time">{{ formatSeconds(marker.time) }}</span>
        </button>
      </div>
    </div>

    <!-- Context menu for markers -->
    <div
      v-if="contextMenu.visible"
      class="marker-context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      @click.stop
    >
      <button @click="editMarkerLabel(contextMenu.index)">编辑标签</button>
      <button @click="deleteMarker(contextMenu.index)">删除标记</button>
    </div>

    <!-- Inline label editor -->
    <div
      v-if="editingMarker !== null"
      class="marker-label-editor"
      @click.stop
    >
      <input
        ref="labelInput"
        v-model="editingLabel"
        @keydown.enter="confirmEditLabel"
        @keydown.escape="cancelEditLabel"
        @blur="confirmEditLabel"
        placeholder="标记名称"
      />
    </div>
  </div>
</template>

<script>
import WaveSurfer from 'wavesurfer.js'
import {
  PlayIcon,
  PauseIcon,
  SkipBackIcon,
  SkipForwardIcon,
  Volume2Icon,
  VolumeXIcon,
  PlusIcon
} from 'lucide-vue-next'

export default {
  name: 'audio-annotation-player',

  components: {
    PlayIcon,
    PauseIcon,
    SkipBackIcon,
    SkipForwardIcon,
    Volume2Icon,
    VolumeXIcon,
    PlusIcon
  },

  props: {
    previewFileId: { type: String, required: true },
    extension: { type: String, default: 'mp3' },
    duration: { type: Number, default: 0 },
    markers: { type: Array, default: () => [] },
    autoplay: { type: Boolean, default: false }
  },

  emits: [
    'time-change',
    'play',
    'pause',
    'ready',
    'seek',
    'marker-add',
    'marker-update',
    'marker-delete',
    'marker-click'
  ],

  data() {
    return {
      wavesurfer: null,
      isLoading: true,
      isPlaying: false,
      isMuted: false,
      volume: 1,
      playbackRate: 1,
      currentTime: 0,
      audioDuration: 0,
      internalMarkers: [],
      activeMarkerIndex: -1,
      markerCounter: 0,
      // Marker dragging
      draggingMarkerIndex: -1,
      dragStartX: 0,
      dragStartTime: 0,
      // Context menu
      contextMenu: {
        visible: false,
        x: 0,
        y: 0,
        index: -1
      },
      // Label editing
      editingMarker: null,
      editingLabel: '',
      // Throttle
      timeChangeThrottleId: null
    }
  },

  computed: {
    audioSrc() {
      return `/api/movies/originals/preview-files/${this.previewFileId}.${this.extension}`
    },

    effectiveDuration() {
      return this.audioDuration || this.duration || 0
    },

    formattedCurrentTime() {
      return this.formatSeconds(this.currentTime)
    },

    formattedDuration() {
      return this.formatSeconds(this.effectiveDuration)
    }
  },

  watch: {
    previewFileId() {
      this.loadAudio()
    },

    markers: {
      handler(newMarkers) {
        if (newMarkers && newMarkers.length > 0) {
          this.internalMarkers = newMarkers.map((m, i) => ({
            time: m.time || 0,
            label: m.label || `标记${i + 1}`,
            type: m.type || 'marker'
          }))
          this.markerCounter = this.internalMarkers.length
        }
      },
      immediate: true
    }
  },

  mounted() {
    this.initWaveSurfer()
    document.addEventListener('click', this.hideContextMenu)
  },

  beforeUnmount() {
    if (this.wavesurfer) {
      this.wavesurfer.destroy()
      this.wavesurfer = null
    }
    if (this.timeChangeThrottleId) {
      clearTimeout(this.timeChangeThrottleId)
    }
    document.removeEventListener('click', this.hideContextMenu)
    document.removeEventListener('mousemove', this.onMarkerDragMove)
    document.removeEventListener('mouseup', this.onMarkerDragEnd)
  },

  methods: {
    // ---- WaveSurfer initialization ----

    initWaveSurfer() {
      this.isLoading = true
      this.wavesurfer = WaveSurfer.create({
        container: this.$refs.waveform,
        waveColor: 'rgba(10, 189, 227, 0.3)',
        progressColor: '#0abde3',
        cursorColor: '#ff4444',
        cursorWidth: 2,
        barWidth: 2,
        barGap: 1,
        height: 128,
        normalize: true,
        url: this.audioSrc
      })

      this.wavesurfer.on('ready', () => {
        this.isLoading = false
        this.audioDuration = this.wavesurfer.getDuration()
        this.$emit('ready', { duration: this.audioDuration })
        if (this.autoplay) {
          this.wavesurfer.play()
        }
      })

      this.wavesurfer.on('timeupdate', (time) => {
        this.currentTime = time
        this.throttledTimeChange(time)
      })

      this.wavesurfer.on('play', () => {
        this.isPlaying = true
        this.$emit('play')
      })

      this.wavesurfer.on('pause', () => {
        this.isPlaying = false
        this.$emit('pause')
      })

      this.wavesurfer.on('finish', () => {
        this.isPlaying = false
        this.$emit('pause')
      })

      this.wavesurfer.on('seeking', (time) => {
        this.currentTime = time
        this.$emit('seek', { time })
      })

      this.wavesurfer.on('error', (err) => {
        console.error('[AudioAnnotationPlayer] WaveSurfer error:', err)
        if (this.extension === 'mp3') {
          this.tryFallbackExtension()
        } else {
          this.isLoading = false
        }
      })
    },

    tryFallbackExtension() {
      const fallback = this.extension === 'mp3' ? 'wav' : 'mp3'
      const fallbackUrl = `/api/movies/originals/preview-files/${this.previewFileId}.${fallback}`
      if (this.wavesurfer) {
        this.wavesurfer.load(fallbackUrl)
      }
    },

    loadAudio() {
      if (!this.wavesurfer) return
      this.isLoading = true
      this.currentTime = 0
      this.audioDuration = 0
      this.wavesurfer.load(this.audioSrc)
    },

    // ---- Playback controls ----

    play() {
      if (this.wavesurfer) this.wavesurfer.play()
    },

    pause() {
      if (this.wavesurfer) this.wavesurfer.pause()
    },

    togglePlay() {
      if (this.wavesurfer) this.wavesurfer.playPause()
    },

    skipForward() {
      if (!this.wavesurfer) return
      const newTime = Math.min(
        this.currentTime + 1,
        this.effectiveDuration
      )
      this.wavesurfer.setTime(newTime)
      this.currentTime = newTime
    },

    skipBackward() {
      if (!this.wavesurfer) return
      const newTime = Math.max(this.currentTime - 1, 0)
      this.wavesurfer.setTime(newTime)
      this.currentTime = newTime
    },

    onSpeedChange() {
      if (this.wavesurfer) {
        this.wavesurfer.setPlaybackRate(this.playbackRate)
      }
    },

    // ---- Volume ----

    toggleMute() {
      this.isMuted = !this.isMuted
      if (this.wavesurfer) {
        this.wavesurfer.setVolume(this.isMuted ? 0 : this.volume)
      }
    },

    onVolumeChange(e) {
      this.volume = parseFloat(e.target.value)
      if (this.wavesurfer) {
        this.wavesurfer.setVolume(this.volume)
      }
      if (this.volume > 0 && this.isMuted) {
        this.isMuted = false
      }
    },

    // ---- Time helpers ----

    seekToTime(seconds) {
      if (!this.wavesurfer) return
      const clamped = Math.max(0, Math.min(seconds, this.effectiveDuration))
      this.wavesurfer.setTime(clamped)
      this.currentTime = clamped
    },

    getCurrentTime() {
      return this.currentTime
    },

    throttledTimeChange(time) {
      if (this.timeChangeThrottleId) return
      this.timeChangeThrottleId = setTimeout(() => {
        this.$emit('time-change', { time })
        this.timeChangeThrottleId = null
      }, 100)
    },

    formatSeconds(totalSeconds) {
      if (!totalSeconds || totalSeconds < 0) return '00:00.00'
      const mins = Math.floor(totalSeconds / 60)
      const secs = Math.floor(totalSeconds % 60)
      const cs = Math.floor((totalSeconds % 1) * 100)
      return (
        String(mins).padStart(2, '0') +
        ':' +
        String(secs).padStart(2, '0') +
        '.' +
        String(cs).padStart(2, '0')
      )
    },

    // ---- Marker system ----

    addMarker() {
      this.markerCounter++
      const marker = {
        time: this.currentTime,
        label: `标记${this.markerCounter}`,
        type: 'marker'
      }
      this.internalMarkers.push(marker)
      this.internalMarkers.sort((a, b) => a.time - b.time)
      const index = this.internalMarkers.indexOf(marker)
      this.activeMarkerIndex = index
      this.$emit('marker-add', { time: marker.time, label: marker.label })
    },

    deleteMarker(index) {
      if (index < 0 || index >= this.internalMarkers.length) return
      this.internalMarkers.splice(index, 1)
      this.hideContextMenu()
      if (this.activeMarkerIndex === index) {
        this.activeMarkerIndex = -1
      } else if (this.activeMarkerIndex > index) {
        this.activeMarkerIndex--
      }
      this.$emit('marker-delete', { index })
    },

    onMarkerClick(index) {
      this.activeMarkerIndex = index
      const marker = this.internalMarkers[index]
      this.seekToTime(marker.time)
      this.$emit('marker-click', { index, marker })
    },

    getMarkerPosition(marker) {
      if (this.effectiveDuration <= 0) return 0
      return (marker.time / this.effectiveDuration) * 100
    },

    // ---- Marker dragging ----

    onMarkerDragStart(e, index) {
      if (e.button !== 0) return
      this.draggingMarkerIndex = index
      this.dragStartX = e.clientX
      this.dragStartTime = this.internalMarkers[index].time
      document.addEventListener('mousemove', this.onMarkerDragMove)
      document.addEventListener('mouseup', this.onMarkerDragEnd)
      e.preventDefault()
    },

    onMarkerDragMove(e) {
      if (this.draggingMarkerIndex < 0) return
      const layer = this.$refs.markerLayer
      if (!layer) return
      const rect = layer.getBoundingClientRect()
      const deltaX = e.clientX - this.dragStartX
      const deltaRatio = deltaX / rect.width
      const deltaTime = deltaRatio * this.effectiveDuration
      let newTime = this.dragStartTime + deltaTime
      newTime = Math.max(0, Math.min(newTime, this.effectiveDuration))
      this.internalMarkers[this.draggingMarkerIndex].time = newTime
    },

    onMarkerDragEnd() {
      if (this.draggingMarkerIndex >= 0) {
        const index = this.draggingMarkerIndex
        const marker = this.internalMarkers[index]
        this.$emit('marker-update', {
          index,
          time: marker.time,
          label: marker.label
        })
        this.internalMarkers.sort((a, b) => a.time - b.time)
      }
      this.draggingMarkerIndex = -1
      document.removeEventListener('mousemove', this.onMarkerDragMove)
      document.removeEventListener('mouseup', this.onMarkerDragEnd)
    },

    // ---- Context menu ----

    onMarkerContextMenu(e, index) {
      this.contextMenu = {
        visible: true,
        x: e.clientX,
        y: e.clientY,
        index
      }
    },

    hideContextMenu() {
      this.contextMenu.visible = false
    },

    // ---- Label editing ----

    editMarkerLabel(index) {
      this.hideContextMenu()
      this.editingMarker = index
      this.editingLabel = this.internalMarkers[index].label
      this.$nextTick(() => {
        if (this.$refs.labelInput) {
          this.$refs.labelInput.focus()
          this.$refs.labelInput.select()
        }
      })
    },

    confirmEditLabel() {
      if (this.editingMarker === null) return
      const index = this.editingMarker
      const label = this.editingLabel.trim() || this.internalMarkers[index].label
      this.internalMarkers[index].label = label
      this.$emit('marker-update', {
        index,
        time: this.internalMarkers[index].time,
        label
      })
      this.editingMarker = null
      this.editingLabel = ''
    },

    cancelEditLabel() {
      this.editingMarker = null
      this.editingLabel = ''
    },

    // ---- Keyboard shortcuts ----

    onKeydown(e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return
      }
      switch (e.key) {
        case ' ':
          e.preventDefault()
          this.togglePlay()
          break
        case 'ArrowLeft':
          e.preventDefault()
          this.skipBackward()
          break
        case 'ArrowRight':
          e.preventDefault()
          this.skipForward()
          break
        case 'm':
          e.preventDefault()
          this.addMarker()
          break
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.audio-annotation-player {
  display: flex;
  flex-direction: column;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  outline: none;
}

// ---- Playback controls ----

.playback-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--background-alt);
  border-bottom: 1px solid var(--border);
  gap: 8px;
}

.controls-left,
.controls-center,
.controls-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.control-button {
  display: flex;
  align-items: center;
  gap: 3px;
  background: none;
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 4px 6px;
  cursor: pointer;
  color: var(--text);
  font-size: 0.75rem;

  &:hover {
    background: var(--background-selectable);
  }
}

.play-button {
  padding: 4px 8px;
}

.speed-control {
  select {
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text);
    font-size: 0.7rem;
    padding: 2px 4px;
    cursor: pointer;
  }
}

.time-display {
  font-size: 0.75rem;
  color: var(--text-alt);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.volume-slider {
  width: 60px;
  height: 4px;
  accent-color: var(--color-primary);
  cursor: pointer;
}

// ---- Waveform section ----

.waveform-section {
  position: relative;
  padding: 0 8px;
  background: var(--background-alt);
}

.marker-layer {
  position: relative;
  height: 16px;

  .marker-flag {
    position: absolute;
    top: 0;
    transform: translateX(-50%);
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    z-index: 2;

    &:hover,
    &.active {
      .marker-triangle {
        color: #ff1443;
        transform: scale(1.3);
      }

      .marker-line {
        background: #ff1443;
      }
    }
  }

  .marker-triangle {
    display: block;
    color: #ff3860;
    font-size: 10px;
    line-height: 1;
    transition: transform 0.15s, color 0.15s;
    user-select: none;
  }

  .marker-line {
    width: 1px;
    height: 128px;
    background: #ff3860;
    opacity: 0.6;
    pointer-events: none;
  }
}

.waveform-container {
  position: relative;
  border-radius: 4px;
  border: 1px solid var(--border);
  overflow: hidden;
  min-height: 128px;
}

.waveform-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  z-index: 3;
}

.loading-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

// ---- Marker controls ----

.marker-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-top: 1px solid var(--border);
  background: var(--background-alt);
  flex-wrap: wrap;
}

.add-marker-btn {
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 0.72rem;
  white-space: nowrap;

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }
}

.marker-list {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  overflow-x: auto;
}

.marker-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2px 8px;
  cursor: pointer;
  font-size: 0.68rem;
  color: var(--text);
  white-space: nowrap;
  transition: border-color 0.15s;

  &:hover,
  &.active {
    border-color: #ff3860;
  }

  &.active {
    background: rgba(255, 56, 96, 0.1);
  }
}

.chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff3860;
  flex-shrink: 0;
}

.chip-label {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-time {
  color: var(--text-alt);
  opacity: 0.7;
}

// ---- Context menu ----

.marker-context-menu {
  position: fixed;
  z-index: 100;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  padding: 4px 0;
  min-width: 120px;

  button {
    display: block;
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    padding: 6px 12px;
    cursor: pointer;
    font-size: 0.75rem;
    color: var(--text);

    &:hover {
      background: var(--background-selectable);
    }
  }
}

// ---- Label editor ----

.marker-label-editor {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 101;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);

  input {
    background: var(--background-alt);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text);
    padding: 4px 8px;
    font-size: 0.8rem;
    outline: none;
    width: 160px;

    &:focus {
      border-color: var(--color-primary);
    }
  }
}
</style>
