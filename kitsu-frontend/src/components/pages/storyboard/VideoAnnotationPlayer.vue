<template>
  <div class="video-annotation-player" @keydown="onKeydown" tabindex="0">
    <!-- Video display area -->
    <div class="video-container" ref="videoContainer">
      <video
        ref="videoEl"
        :src="videoSrc"
        :preload="'metadata'"
        :autoplay="autoplay"
        @loadedmetadata="onLoadedMetadata"
        @timeupdate="onTimeUpdate"
        @play="onPlay"
        @pause="onPause"
        @ended="onEnded"
        @error="onVideoError"
      ></video>
      <div v-if="isLoading" class="video-loading">
        <span class="loading-spinner"></span>
      </div>
    </div>

    <!-- Playback controls -->
    <div class="playback-controls">
      <div class="controls-left">
        <button
          class="control-button"
          :title="isPlaying ? '暂停' : '播放'"
          @click="togglePlay"
        >
          <PauseIcon v-if="isPlaying" :size="16" />
          <PlayIcon v-else :size="16" />
        </button>
        <div class="speed-control">
          <select v-model="playbackRate" @change="onSpeedChange">
            <option :value="0.25">0.25x</option>
            <option :value="0.5">0.5x</option>
            <option :value="1">1x</option>
            <option :value="1.5">1.5x</option>
            <option :value="2">2x</option>
          </select>
        </div>
      </div>

      <div class="controls-center">
        <span class="time-display">
          {{ formattedCurrentTime }} / {{ formattedDuration }}
        </span>
      </div>

      <div class="controls-right">
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

    <!-- Timeline with annotation markers -->
    <div class="timeline-section">
      <div class="annotation-markers" ref="markersBar">
        <div
          v-for="(ann, index) in annotations"
          :key="index"
          class="annotation-marker"
          :style="{ left: getAnnotationPosition(ann) + '%' }"
          :title="'帧 ' + (ann.frame || Math.round((ann.time || 0) * fps))"
          @click="onAnnotationMarkerClick(index, ann)"
        >
          <span class="marker-triangle">&#9660;</span>
        </div>
      </div>
      <div
        class="progress-bar-container"
        ref="progressBar"
        @mousedown="onProgressMouseDown"
        @mousemove="onProgressMouseMove"
        @mouseleave="onProgressMouseLeave"
      >
        <div class="progress-bar-bg">
          <div
            class="progress-bar-fill"
            :style="{ width: progressPercent + '%' }"
          ></div>
          <div
            class="progress-playhead"
            :style="{ left: progressPercent + '%' }"
          ></div>
        </div>
        <div
          v-if="hoverTime >= 0"
          class="progress-hover-tooltip"
          :style="{ left: hoverPercent + '%' }"
        >
          {{ hoverTimeFormatted }}
        </div>
      </div>
    </div>

    <!-- Frame controls -->
    <div class="frame-controls">
      <div class="frame-nav">
        <button
          class="control-button"
          title="上一帧 (←)"
          @click="prevFrame"
        >
          <ChevronLeftIcon :size="14" />
          <span>帧</span>
        </button>
        <button
          class="control-button"
          title="下一帧 (→)"
          @click="nextFrame"
        >
          <span>帧</span>
          <ChevronRightIcon :size="14" />
        </button>
      </div>
      <div class="frame-info">
        <span class="frame-number">
          帧: {{ currentFrame }} / {{ totalFrames }}
        </span>
      </div>
      <div class="fps-info">
        @{{ fps }}fps
      </div>
    </div>
  </div>
</template>

<script>
import {
  PlayIcon,
  PauseIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Volume2Icon,
  VolumeXIcon
} from 'lucide-vue-next'
import { formatTime } from '@/lib/video'

export default {
  name: 'video-annotation-player',

  components: {
    PlayIcon,
    PauseIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
    Volume2Icon,
    VolumeXIcon
  },

  props: {
    previewFileId: { type: String, required: true },
    duration: { type: Number, default: 0 },
    fps: { type: Number, default: 24 },
    annotations: { type: Array, default: () => [] },
    autoplay: { type: Boolean, default: false }
  },

  emits: [
    'frame-change',
    'play',
    'pause',
    'ready',
    'seek',
    'annotation-click'
  ],

  data() {
    return {
      isPlaying: false,
      isLoading: true,
      isMuted: false,
      volume: 1,
      playbackRate: 1,
      currentTimeRaw: 0,
      videoDuration: 0,
      videoWidth: 0,
      videoHeight: 0,
      isDragging: false,
      hoverTime: -1,
      hoverPercent: 0,
      animFrameId: null,
      useFallback: false
    }
  },

  computed: {
    videoSrc() {
      const quality = this.useFallback ? 'low' : 'originals'
      return `/api/movies/${quality}/preview-files/${this.previewFileId}.mp4`
    },

    frameDuration() {
      return 1 / this.fps
    },

    currentFrame() {
      return Math.round(this.currentTimeRaw * this.fps)
    },

    totalFrames() {
      return Math.round(this.effectiveDuration * this.fps)
    },

    effectiveDuration() {
      return this.videoDuration || this.duration || 0
    },

    progressPercent() {
      if (this.effectiveDuration <= 0) return 0
      return (this.currentTimeRaw / this.effectiveDuration) * 100
    },

    formattedCurrentTime() {
      return formatTime(this.currentTimeRaw, this.fps)
    },

    formattedDuration() {
      return formatTime(this.effectiveDuration, this.fps)
    },

    hoverTimeFormatted() {
      if (this.hoverTime < 0) return ''
      return formatTime(this.hoverTime, this.fps)
    }
  },

  watch: {
    previewFileId() {
      this.isLoading = true
      this.useFallback = false
      this.currentTimeRaw = 0
    }
  },

  mounted() {
    this.startFrameLoop()
  },

  beforeUnmount() {
    this.stopFrameLoop()
    if (this.isDragging) {
      document.removeEventListener('mousemove', this.onDocumentMouseMove)
      document.removeEventListener('mouseup', this.onDocumentMouseUp)
    }
  },

  methods: {
    // ---- Video element access ----

    getVideo() {
      return this.$refs.videoEl
    },

    // ---- Playback ----

    play() {
      const video = this.getVideo()
      if (video) video.play()
    },

    pause() {
      const video = this.getVideo()
      if (video) video.pause()
    },

    togglePlay() {
      if (this.isPlaying) {
        this.pause()
      } else {
        this.play()
      }
    },

    onPlay() {
      this.isPlaying = true
      this.$emit('play')
    },

    onPause() {
      this.isPlaying = false
      this.$emit('pause')
    },

    onEnded() {
      this.isPlaying = false
      this.$emit('pause')
    },

    onSpeedChange() {
      const video = this.getVideo()
      if (video) video.playbackRate = this.playbackRate
    },

    // ---- Volume ----

    toggleMute() {
      const video = this.getVideo()
      if (!video) return
      this.isMuted = !this.isMuted
      video.muted = this.isMuted
    },

    onVolumeChange(e) {
      const video = this.getVideo()
      if (!video) return
      this.volume = parseFloat(e.target.value)
      video.volume = this.volume
      if (this.volume > 0 && this.isMuted) {
        this.isMuted = false
        video.muted = false
      }
    },

    // ---- Time / frame ----

    onLoadedMetadata() {
      const video = this.getVideo()
      if (!video) return
      this.videoDuration = video.duration
      this.videoWidth = video.videoWidth
      this.videoHeight = video.videoHeight
      this.isLoading = false
      this.$emit('ready', {
        duration: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
        fps: this.fps
      })
    },

    onTimeUpdate() {
      const video = this.getVideo()
      if (!video) return
      this.currentTimeRaw = video.currentTime
    },

    onVideoError() {
      if (!this.useFallback) {
        this.useFallback = true
      } else {
        this.isLoading = false
      }
    },

    // ---- Frame-accurate loop via rAF ----

    startFrameLoop() {
      let lastFrame = -1
      const tick = () => {
        const video = this.getVideo()
        if (video && !video.paused) {
          this.currentTimeRaw = video.currentTime
          const frame = this.currentFrame
          if (frame !== lastFrame) {
            lastFrame = frame
            this.$emit('frame-change', {
              frame,
              time: video.currentTime
            })
          }
        }
        this.animFrameId = requestAnimationFrame(tick)
      }
      this.animFrameId = requestAnimationFrame(tick)
    },

    stopFrameLoop() {
      if (this.animFrameId) {
        cancelAnimationFrame(this.animFrameId)
        this.animFrameId = null
      }
    },

    // ---- Frame navigation ----

    seekToFrame(frameNumber) {
      const video = this.getVideo()
      if (!video) return
      const time = frameNumber / this.fps
      video.currentTime = time
      this.currentTimeRaw = time
      this.$emit('frame-change', { frame: frameNumber, time })
    },

    getCurrentFrame() {
      return this.currentFrame
    },

    nextFrame() {
      const video = this.getVideo()
      if (!video) return
      if (this.isPlaying) this.pause()
      const newFrame = Math.min(this.currentFrame + 1, this.totalFrames)
      this.seekToFrame(newFrame)
    },

    prevFrame() {
      const video = this.getVideo()
      if (!video) return
      if (this.isPlaying) this.pause()
      const newFrame = Math.max(this.currentFrame - 1, 0)
      this.seekToFrame(newFrame)
    },

    // ---- Capture current frame ----

    async captureFrame() {
      const video = this.getVideo()
      if (!video) return null
      return await createImageBitmap(video)
    },

    // ---- Progress bar interaction ----

    getTimeFromProgressEvent(e) {
      const bar = this.$refs.progressBar
      if (!bar) return 0
      const rect = bar.getBoundingClientRect()
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
      const ratio = x / rect.width
      return ratio * this.effectiveDuration
    },

    onProgressMouseDown(e) {
      this.isDragging = true
      const time = this.getTimeFromProgressEvent(e)
      const video = this.getVideo()
      if (video) {
        video.currentTime = time
        this.currentTimeRaw = time
      }
      document.addEventListener('mousemove', this.onDocumentMouseMove)
      document.addEventListener('mouseup', this.onDocumentMouseUp)
    },

    onDocumentMouseMove(e) {
      if (!this.isDragging) return
      const time = this.getTimeFromProgressEvent(e)
      const video = this.getVideo()
      if (video) {
        video.currentTime = time
        this.currentTimeRaw = time
      }
    },

    onDocumentMouseUp(e) {
      if (!this.isDragging) return
      this.isDragging = false
      const time = this.getTimeFromProgressEvent(e)
      const frame = Math.round(time * this.fps)
      this.$emit('seek', { frame, time })
      document.removeEventListener('mousemove', this.onDocumentMouseMove)
      document.removeEventListener('mouseup', this.onDocumentMouseUp)
    },

    onProgressMouseMove(e) {
      if (this.isDragging) return
      const time = this.getTimeFromProgressEvent(e)
      this.hoverTime = time
      const bar = this.$refs.progressBar
      if (bar) {
        const rect = bar.getBoundingClientRect()
        this.hoverPercent =
          ((e.clientX - rect.left) / rect.width) * 100
      }
    },

    onProgressMouseLeave() {
      if (!this.isDragging) {
        this.hoverTime = -1
      }
    },

    // ---- Annotation markers ----

    getAnnotationPosition(annotation) {
      if (this.effectiveDuration <= 0) return 0
      const time =
        annotation.time != null
          ? annotation.time
          : (annotation.frame || 0) / this.fps
      return (time / this.effectiveDuration) * 100
    },

    onAnnotationMarkerClick(index, annotation) {
      const frame =
        annotation.frame != null
          ? annotation.frame
          : Math.round((annotation.time || 0) * this.fps)
      this.seekToFrame(frame)
      this.$emit('annotation-click', { index, annotation })
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
          this.prevFrame()
          break
        case 'ArrowRight':
          e.preventDefault()
          this.nextFrame()
          break
        case 'j':
          e.preventDefault()
          this.playbackRate = Math.max(0.25, this.playbackRate - 0.25)
          this.onSpeedChange()
          break
        case 'k':
          e.preventDefault()
          this.togglePlay()
          break
        case 'l':
          e.preventDefault()
          this.playbackRate = Math.min(2, this.playbackRate + 0.25)
          this.onSpeedChange()
          break
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.video-annotation-player {
  display: flex;
  flex-direction: column;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  outline: none;
}

.video-container {
  position: relative;
  background: #111;
  display: flex;
  align-items: center;
  justify-content: center;

  video {
    width: 100%;
    display: block;
  }
}

.video-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
}

.loading-spinner {
  width: 32px;
  height: 32px;
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

// ---- Playback controls ----

.playback-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-top: 1px solid var(--border);
  background: var(--background-alt);
  gap: 8px;
}

.controls-left,
.controls-center,
.controls-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.control-button {
  display: flex;
  align-items: center;
  gap: 2px;
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

// ---- Timeline section ----

.timeline-section {
  position: relative;
  padding: 0 8px;
  background: var(--background-alt);
}

.annotation-markers {
  position: relative;
  height: 14px;

  .annotation-marker {
    position: absolute;
    top: 0;
    transform: translateX(-50%);
    cursor: pointer;
    color: #ff3860;
    font-size: 8px;
    line-height: 1;

    &:hover {
      color: #ff1443;
      transform: translateX(-50%) scale(1.3);
    }
  }

  .marker-triangle {
    display: block;
  }
}

.progress-bar-container {
  position: relative;
  height: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 4px 0;
}

.progress-bar-bg {
  position: relative;
  width: 100%;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: visible;
}

.progress-bar-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 2px;
  transition: none;
}

.progress-playhead {
  position: absolute;
  top: 50%;
  width: 10px;
  height: 10px;
  background: #ff4444;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.4);
  pointer-events: none;
}

.progress-hover-tooltip {
  position: absolute;
  bottom: 18px;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 3px;
  white-space: nowrap;
  pointer-events: none;
}

// ---- Frame controls ----

.frame-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-top: 1px solid var(--border);
  background: var(--background-alt);
  font-size: 0.75rem;
  color: var(--text-alt);
}

.frame-nav {
  display: flex;
  gap: 4px;
}

.frame-number {
  font-variant-numeric: tabular-nums;
}

.fps-info {
  font-variant-numeric: tabular-nums;
  opacity: 0.7;
}
</style>
