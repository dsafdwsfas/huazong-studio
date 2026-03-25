<template>
  <div
    class="timeline-view"
    @wheel="onWheel"
  >
    <!-- Zoom control bar -->
    <div class="timeline-toolbar">
      <span class="toolbar-label">Zoom</span>
      <input
        type="range"
        class="zoom-slider"
        :min="minPxPerFrame"
        :max="maxPxPerFrame"
        step="0.5"
        :value="pxPerFrame"
        @input="onZoomInput"
      />
      <span class="zoom-value">{{ pxPerFrame.toFixed(1) }}px/f</span>
      <span class="toolbar-separator" />
      <span class="toolbar-label">{{ totalFrames }}f</span>
      <span class="toolbar-label">({{ totalDuration }})</span>
    </div>

    <div class="timeline-body" ref="timelineBody">
      <!-- Fixed sequence label column -->
      <div class="sequence-labels">
        <div class="label-header" />
        <div
          v-for="row in timelineRows"
          :key="row.sequence.id"
          class="label-cell"
          :title="row.sequence.name"
        >
          {{ row.sequence.name }}
        </div>
      </div>

      <!-- Scrollable timeline area -->
      <div
        class="timeline-scroll"
        ref="timelineScroll"
        @scroll="onScroll"
        @mousedown="onTimelineMouseDown"
      >
        <div
          class="timeline-canvas"
          :style="{ width: canvasWidth + 'px' }"
        >
          <!-- Time ruler -->
          <div class="time-ruler" :style="{ width: canvasWidth + 'px' }">
            <canvas
              ref="rulerCanvas"
              class="ruler-canvas"
              :width="canvasWidth"
              :height="rulerHeight"
            />
          </div>

          <!-- Sequence rows -->
          <div
            v-for="row in timelineRows"
            :key="row.sequence.id"
            class="sequence-row"
            :data-sequence-id="row.sequence.id"
            @dragover.prevent="onRowDragOver($event, row.sequence.id)"
            @drop="onRowDrop($event, row.sequence.id)"
          >
            <div
              v-for="shot in row.shots"
              :key="shot.id"
              class="shot-bar"
              :class="{
                selected: isSelected(shot.id),
                dragging: dragState.shotId === shot.id
              }"
              :style="shotBarStyle(shot)"
              :title="shotTooltipText(shot)"
              @mousedown.stop="onShotMouseDown($event, shot, row.sequence.id)"
              @click.stop="onShotClick($event, shot)"
              @dblclick.stop="onShotDblClick(shot)"
            >
              <img
                v-if="shot.preview_file_id && shotBarWidth(shot) > 60"
                class="shot-thumb"
                :src="thumbnailUrl(shot)"
                loading="lazy"
              />
              <span
                v-if="shotBarWidth(shot) > 40"
                class="shot-label"
              >
                {{ shot.name }}
              </span>
              <!-- Left resize handle -->
              <div
                class="resize-handle resize-left"
                @mousedown.stop="onResizeMouseDown($event, shot, 'left', row.sequence.id)"
              />
              <!-- Right resize handle -->
              <div
                class="resize-handle resize-right"
                @mousedown.stop="onResizeMouseDown($event, shot, 'right', row.sequence.id)"
              />
            </div>
          </div>

          <!-- Playhead -->
          <div
            class="playhead"
            :style="{ left: playheadX + 'px' }"
          >
            <div
              class="playhead-handle"
              @mousedown.stop="onPlayheadMouseDown"
            >
              <svg width="12" height="10" viewBox="0 0 12 10">
                <polygon points="0,0 12,0 6,10" fill="#ff4444" />
              </svg>
            </div>
            <div class="playhead-line" />
            <span class="playhead-label">{{ currentFrame }}f</span>
          </div>

          <!-- Snap guide line -->
          <div
            v-if="snapGuide !== null"
            class="snap-guide"
            :style="{ left: snapGuide + 'px' }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TimelineView',

  props: {
    sequences: {
      type: Array,
      required: true
    },
    taskStatuses: {
      type: Array,
      default: () => []
    },
    selectedShotIds: {
      type: Array,
      default: () => []
    },
    projectFps: {
      type: Number,
      default: 24
    }
  },

  emits: [
    'select-shot',
    'open-annotation',
    'update-timing',
    'batch-update-timing',
    'move-shot'
  ],

  data() {
    return {
      pxPerFrame: 4,
      minPxPerFrame: 1,
      maxPxPerFrame: 20,
      rulerHeight: 28,
      currentFrame: 0,
      scrollLeft: 0,
      dragState: {
        active: false,
        type: null, // 'move' | 'resize-left' | 'resize-right' | 'playhead'
        shotId: null,
        sequenceId: null,
        startX: 0,
        startFrame: 0,
        startFrameIn: 0,
        startNbFrames: 0,
        moved: false
      },
      snapGuide: null,
      viewportWidth: 0
    }
  },

  computed: {
    timelineRows() {
      return this.sequences.map(seq => {
        const shots = this.computeTimeline(seq)
        return { sequence: seq, shots }
      })
    },

    allComputedShots() {
      const shots = []
      for (const row of this.timelineRows) {
        shots.push(...row.shots)
      }
      return shots
    },

    totalFrames() {
      let max = 0
      for (const shot of this.allComputedShots) {
        const end = shot.computedFrameIn + (shot.computedNbFrames || 48)
        if (end > max) max = end
      }
      return Math.max(max, this.projectFps * 10)
    },

    totalDuration() {
      const secs = this.totalFrames / this.projectFps
      const m = Math.floor(secs / 60)
      const s = Math.round(secs % 60)
      return m > 0 ? `${m}m${s}s` : `${s}s`
    },

    canvasWidth() {
      const contentWidth = (this.totalFrames + 48) * this.pxPerFrame
      return Math.max(contentWidth, this.viewportWidth)
    },

    playheadX() {
      return this.currentFrame * this.pxPerFrame
    },

    snapPoints() {
      const points = [0]
      for (const shot of this.allComputedShots) {
        points.push(shot.computedFrameIn)
        points.push(shot.computedFrameIn + shot.computedNbFrames)
      }
      return [...new Set(points)].sort((a, b) => a - b)
    }
  },

  watch: {
    pxPerFrame() {
      this.$nextTick(() => this.drawRuler())
    },
    canvasWidth() {
      this.$nextTick(() => this.drawRuler())
    },
    sequences: {
      handler() {
        this.$nextTick(() => this.drawRuler())
      },
      deep: true
    }
  },

  mounted() {
    this.updateViewportWidth()
    this.$nextTick(() => this.drawRuler())
    this._resizeObserver = new ResizeObserver(() => {
      this.updateViewportWidth()
      this.drawRuler()
    })
    if (this.$refs.timelineScroll) {
      this._resizeObserver.observe(this.$refs.timelineScroll)
    }
  },

  beforeUnmount() {
    if (this._resizeObserver) {
      this._resizeObserver.disconnect()
    }
    this.removeGlobalListeners()
  },

  methods: {
    // --- Data computation ---

    computeTimeline(sequence) {
      const shots = [...(sequence.shots || [])].sort(
        (a, b) => (a.storyboard_order || 0) - (b.storyboard_order || 0)
      )
      let currentFrame = 0
      return shots.map(shot => {
        const frameIn = shot.frame_in != null ? shot.frame_in : currentFrame
        const nbFrames = shot.nb_frames || 48
        const frameOut = shot.frame_out != null
          ? shot.frame_out
          : frameIn + nbFrames - 1
        const computedNbFrames = frameOut - frameIn + 1
        currentFrame = frameOut + 1
        return {
          ...shot,
          computedFrameIn: frameIn,
          computedFrameOut: frameOut,
          computedNbFrames
        }
      })
    },

    // --- Styling helpers ---

    shotBarStyle(shot) {
      const left = shot.computedFrameIn * this.pxPerFrame
      const width = shot.computedNbFrames * this.pxPerFrame
      const color = this.getShotColor(shot)
      return {
        left: left + 'px',
        width: Math.max(width, 4) + 'px',
        backgroundColor: color
      }
    },

    shotBarWidth(shot) {
      return shot.computedNbFrames * this.pxPerFrame
    },

    getShotColor(shot) {
      if (shot.primary_task && shot.primary_task.task_status_color) {
        return '#' + shot.primary_task.task_status_color
      }
      // Default color based on status
      const statusColors = {
        waiting: '#78909c',
        running: '#42a5f5',
        complete: '#66bb6a',
        cancelled: '#bdbdbd'
      }
      return statusColors[shot.status] || '#78909c'
    },

    thumbnailUrl(shot) {
      return `/api/pictures/thumbnails-square/preview-files/${shot.preview_file_id}.png`
    },

    shotTooltipText(shot) {
      const frames = shot.computedNbFrames
      const secs = (frames / this.projectFps).toFixed(2)
      let text = `${shot.name}\n${frames} frames (${secs}s)`
      if (shot.primary_task) {
        text += `\nStatus: ${shot.primary_task.task_status_name || 'N/A'}`
      }
      if (shot.assignees && shot.assignees.length > 0) {
        const names = shot.assignees
          .map(a => (typeof a === 'object' ? a.name : a))
          .join(', ')
        text += `\nAssigned: ${names}`
      }
      return text
    },

    isSelected(shotId) {
      return this.selectedShotIds.includes(shotId)
    },

    // --- Ruler drawing ---

    drawRuler() {
      const canvas = this.$refs.rulerCanvas
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      const w = canvas.width
      const h = canvas.height
      const dpr = window.devicePixelRatio || 1

      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = w / dpr + 'px'
      canvas.style.height = h / dpr + 'px'

      // Actually we want logical size matching canvasWidth
      canvas.width = this.canvasWidth
      canvas.height = this.rulerHeight
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const ppf = this.pxPerFrame
      const fps = this.projectFps

      // Determine tick intervals based on zoom
      let majorInterval, minorInterval
      if (ppf >= 8) {
        majorInterval = fps       // every second
        minorInterval = 1         // every frame
      } else if (ppf >= 4) {
        majorInterval = fps       // every second
        minorInterval = fps / 4   // every quarter-second
      } else if (ppf >= 2) {
        majorInterval = fps * 2   // every 2 seconds
        minorInterval = fps / 2   // every half-second
      } else {
        majorInterval = fps * 5   // every 5 seconds
        minorInterval = fps       // every second
      }

      const maxFrame = this.totalFrames + 48

      // Minor ticks
      ctx.strokeStyle = 'rgba(128, 128, 128, 0.3)'
      ctx.lineWidth = 1
      for (let f = 0; f <= maxFrame; f += minorInterval) {
        const x = Math.round(f * ppf) + 0.5
        ctx.beginPath()
        ctx.moveTo(x, h - 6)
        ctx.lineTo(x, h)
        ctx.stroke()
      }

      // Major ticks + labels
      ctx.strokeStyle = 'rgba(128, 128, 128, 0.6)'
      ctx.fillStyle = getComputedStyle(this.$el)
        .getPropertyValue('--text-alt')
        .trim() || '#999'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'

      for (let f = 0; f <= maxFrame; f += majorInterval) {
        const x = Math.round(f * ppf) + 0.5
        ctx.beginPath()
        ctx.moveTo(x, h - 14)
        ctx.lineTo(x, h)
        ctx.stroke()

        const secs = f / fps
        const label = secs >= 60
          ? `${Math.floor(secs / 60)}:${String(Math.round(secs % 60)).padStart(2, '0')}`
          : `${secs.toFixed(secs % 1 === 0 ? 0 : 1)}s`
        ctx.fillText(label, x, h - 16)
      }
    },

    updateViewportWidth() {
      if (this.$refs.timelineScroll) {
        this.viewportWidth = this.$refs.timelineScroll.clientWidth
      }
    },

    // --- Scroll / zoom ---

    onScroll() {
      if (this.$refs.timelineScroll) {
        this.scrollLeft = this.$refs.timelineScroll.scrollLeft
      }
    },

    onWheel(event) {
      if (!event.ctrlKey && !event.metaKey) return
      event.preventDefault()

      const scroll = this.$refs.timelineScroll
      if (!scroll) return

      const rect = scroll.getBoundingClientRect()
      const mouseX = event.clientX - rect.left + scroll.scrollLeft
      const frameAtMouse = mouseX / this.pxPerFrame

      const delta = event.deltaY > 0 ? -0.5 : 0.5
      const oldPx = this.pxPerFrame
      this.pxPerFrame = Math.max(
        this.minPxPerFrame,
        Math.min(this.maxPxPerFrame, oldPx + delta)
      )

      // Keep frame under cursor stable
      this.$nextTick(() => {
        const newMouseX = frameAtMouse * this.pxPerFrame
        scroll.scrollLeft = newMouseX - (event.clientX - rect.left)
      })
    },

    onZoomInput(event) {
      this.pxPerFrame = parseFloat(event.target.value)
    },

    // --- Shot click / selection ---

    onShotClick(event, shot) {
      this.$emit('select-shot', {
        shotId: shot.id,
        ctrlKey: event.ctrlKey || event.metaKey
      })
    },

    onShotDblClick(shot) {
      this.$emit('open-annotation', { shotId: shot.id })
    },

    // --- Playhead ---

    onTimelineMouseDown(event) {
      // Click on empty area moves playhead
      if (event.target === this.$refs.timelineScroll ||
          event.target.classList.contains('timeline-canvas') ||
          event.target.classList.contains('sequence-row') ||
          event.target.classList.contains('time-ruler') ||
          event.target.tagName === 'CANVAS') {
        const scroll = this.$refs.timelineScroll
        const rect = scroll.getBoundingClientRect()
        const x = event.clientX - rect.left + scroll.scrollLeft
        this.currentFrame = Math.max(0, Math.round(x / this.pxPerFrame))
      }
    },

    onPlayheadMouseDown(event) {
      event.preventDefault()
      this.dragState = {
        active: true,
        type: 'playhead',
        shotId: null,
        sequenceId: null,
        startX: event.clientX,
        startFrame: this.currentFrame,
        startFrameIn: 0,
        startNbFrames: 0,
        moved: false
      }
      this.addGlobalListeners()
    },

    // --- Shot drag (move) ---

    onShotMouseDown(event, shot, sequenceId) {
      // Ignore if clicking resize handles
      if (event.target.classList.contains('resize-handle')) return
      event.preventDefault()

      this.dragState = {
        active: true,
        type: 'move',
        shotId: shot.id,
        sequenceId,
        startX: event.clientX,
        startFrame: 0,
        startFrameIn: shot.computedFrameIn,
        startNbFrames: shot.computedNbFrames,
        moved: false
      }
      this.addGlobalListeners()
    },

    // --- Resize ---

    onResizeMouseDown(event, shot, side, sequenceId) {
      event.preventDefault()
      this.dragState = {
        active: true,
        type: 'resize-' + side,
        shotId: shot.id,
        sequenceId,
        startX: event.clientX,
        startFrame: 0,
        startFrameIn: shot.computedFrameIn,
        startNbFrames: shot.computedNbFrames,
        moved: false
      }
      this.addGlobalListeners()
    },

    // --- Cross-sequence drag ---

    onRowDragOver(event, sequenceId) {
      if (this.dragState.active && this.dragState.type === 'move') {
        event.dataTransfer.dropEffect = 'move'
      }
    },

    onRowDrop(event, targetSequenceId) {
      if (!this.dragState.active || this.dragState.type !== 'move') return
      const { shotId, sequenceId } = this.dragState
      if (sequenceId !== targetSequenceId) {
        this.$emit('move-shot', {
          shotId,
          targetSequenceId,
          position: -1
        })
      }
    },

    // --- Global mouse handlers ---

    addGlobalListeners() {
      window.addEventListener('mousemove', this.onGlobalMouseMove)
      window.addEventListener('mouseup', this.onGlobalMouseUp)
    },

    removeGlobalListeners() {
      window.removeEventListener('mousemove', this.onGlobalMouseMove)
      window.removeEventListener('mouseup', this.onGlobalMouseUp)
    },

    onGlobalMouseMove(event) {
      if (!this.dragState.active) return
      const dx = event.clientX - this.dragState.startX
      const dFrames = Math.round(dx / this.pxPerFrame)

      if (Math.abs(dx) > 2) {
        this.dragState.moved = true
      }

      if (this.dragState.type === 'playhead') {
        const newFrame = Math.max(0, this.dragState.startFrame + dFrames)
        const snapped = this.snapToNearest(newFrame, 4)
        this.currentFrame = snapped.frame
        this.snapGuide = snapped.snapped ? snapped.frame * this.pxPerFrame : null
        return
      }

      if (this.dragState.type === 'move') {
        const newFrameIn = Math.max(0, this.dragState.startFrameIn + dFrames)
        const snapped = this.snapToNearest(newFrameIn, 4)
        // Update shot position visually via direct DOM for performance
        this.updateDragPreview(snapped.frame, this.dragState.startNbFrames)
        this.snapGuide = snapped.snapped ? snapped.frame * this.pxPerFrame : null
        return
      }

      if (this.dragState.type === 'resize-right') {
        const newNbFrames = Math.max(1, this.dragState.startNbFrames + dFrames)
        const endFrame = this.dragState.startFrameIn + newNbFrames
        const snapped = this.snapToNearest(endFrame, 4)
        const finalNb = Math.max(1, snapped.frame - this.dragState.startFrameIn)
        this.updateDragPreview(this.dragState.startFrameIn, finalNb)
        this.snapGuide = snapped.snapped ? snapped.frame * this.pxPerFrame : null
        return
      }

      if (this.dragState.type === 'resize-left') {
        const newFrameIn = Math.max(0, this.dragState.startFrameIn + dFrames)
        const snapped = this.snapToNearest(newFrameIn, 4)
        const endFrame = this.dragState.startFrameIn + this.dragState.startNbFrames
        const finalNb = Math.max(1, endFrame - snapped.frame)
        this.updateDragPreview(snapped.frame, finalNb)
        this.snapGuide = snapped.snapped ? snapped.frame * this.pxPerFrame : null
        return
      }
    },

    onGlobalMouseUp() {
      this.removeGlobalListeners()
      this.snapGuide = null

      if (!this.dragState.active) return
      const state = { ...this.dragState }
      this.dragState = {
        active: false,
        type: null,
        shotId: null,
        sequenceId: null,
        startX: 0,
        startFrame: 0,
        startFrameIn: 0,
        startNbFrames: 0,
        moved: false
      }

      if (!state.moved) return
      if (state.type === 'playhead') return

      // Calculate final values from the drag preview element
      const shotEl = this.$el.querySelector(
        `.shot-bar[data-drag-id="${state.shotId}"]`
      )
      if (!shotEl) {
        // Fallback: recalculate from mouse delta
        this.emitTimingFromState(state)
        return
      }

      const left = parseFloat(shotEl.style.left)
      const width = parseFloat(shotEl.style.width)
      const frameIn = Math.round(left / this.pxPerFrame)
      const nbFrames = Math.max(1, Math.round(width / this.pxPerFrame))
      const frameOut = frameIn + nbFrames - 1

      this.$emit('update-timing', {
        shotId: state.shotId,
        frameIn,
        frameOut,
        nbFrames
      })
    },

    emitTimingFromState(state) {
      const dx = 0 // already handled, fallback
      const frameIn = state.startFrameIn
      const nbFrames = state.startNbFrames
      this.$emit('update-timing', {
        shotId: state.shotId,
        frameIn,
        frameOut: frameIn + nbFrames - 1,
        nbFrames
      })
    },

    updateDragPreview(frameIn, nbFrames) {
      // Use requestAnimationFrame for smooth dragging
      if (this._rafId) cancelAnimationFrame(this._rafId)
      this._rafId = requestAnimationFrame(() => {
        const shotId = this.dragState.shotId
        if (!shotId) return
        // Find the shot bar DOM element
        const bars = this.$el.querySelectorAll('.shot-bar')
        for (const bar of bars) {
          // Match by checking the shot id stored as data attribute
          const shot = this.findShotById(shotId)
          if (!shot) return
          if (bar.getAttribute('title') === this.shotTooltipText(shot)) {
            bar.style.left = (frameIn * this.pxPerFrame) + 'px'
            bar.style.width = Math.max(nbFrames * this.pxPerFrame, 4) + 'px'
            bar.setAttribute('data-drag-id', shotId)
            break
          }
        }
      })
    },

    findShotById(shotId) {
      for (const row of this.timelineRows) {
        const shot = row.shots.find(s => s.id === shotId)
        if (shot) return shot
      }
      return null
    },

    // --- Snap logic ---

    snapToNearest(frame, threshold) {
      const snapThreshold = threshold / this.pxPerFrame
      let nearest = frame
      let minDist = Infinity
      for (const point of this.snapPoints) {
        const dist = Math.abs(frame - point)
        if (dist < minDist && dist < snapThreshold) {
          minDist = dist
          nearest = point
        }
      }
      return {
        frame: nearest,
        snapped: nearest !== frame
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.timeline-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--background);
  user-select: none;
}

.timeline-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  font-size: 0.8rem;
  color: var(--text-alt);
}

.toolbar-label {
  white-space: nowrap;
}

.toolbar-separator {
  width: 1px;
  height: 16px;
  background: var(--border);
}

.zoom-slider {
  width: 120px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.zoom-value {
  min-width: 55px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.timeline-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// Fixed left column for sequence names
.sequence-labels {
  width: 120px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  overflow: hidden;
}

.label-header {
  height: 28px;
  border-bottom: 1px solid var(--border);
  background: var(--background-alt);
}

.label-cell {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
  border-bottom: 1px solid var(--border);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: var(--background-alt);
}

// Scrollable right area
.timeline-scroll {
  flex: 1;
  overflow-x: auto;
  overflow-y: auto;
  position: relative;
}

.timeline-canvas {
  position: relative;
  min-height: 100%;
}

// Ruler
.time-ruler {
  height: 28px;
  position: sticky;
  top: 0;
  z-index: 3;
  background: var(--background-alt);
  border-bottom: 1px solid var(--border);
}

.ruler-canvas {
  display: block;
}

// Sequence row
.sequence-row {
  position: relative;
  height: 56px;
  border-bottom: 1px solid var(--border);
}

// Shot bar
.shot-bar {
  position: absolute;
  top: 6px;
  height: 44px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 6px;
  cursor: grab;
  overflow: hidden;
  transition: box-shadow 0.1s;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    z-index: 2;
  }

  &.selected {
    outline: 2px solid var(--color-primary);
    outline-offset: -1px;
    z-index: 2;
  }

  &.dragging {
    opacity: 0.85;
    cursor: grabbing;
    z-index: 10;
  }
}

.shot-thumb {
  width: 28px;
  height: 28px;
  border-radius: 3px;
  object-fit: cover;
  flex-shrink: 0;
}

.shot-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
}

// Resize handles
.resize-handle {
  position: absolute;
  top: 0;
  width: 6px;
  height: 100%;
  cursor: col-resize;
  z-index: 1;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
}

.resize-left {
  left: 0;
  border-radius: 4px 0 0 4px;
}

.resize-right {
  right: 0;
  border-radius: 0 4px 4px 0;
}

// Playhead
.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  z-index: 5;
  pointer-events: none;
}

.playhead-handle {
  position: absolute;
  top: 0;
  left: -6px;
  width: 12px;
  cursor: ew-resize;
  pointer-events: auto;
  z-index: 6;
}

.playhead-line {
  position: absolute;
  top: 10px;
  bottom: 0;
  left: 0;
  width: 1px;
  background: #ff4444;
}

.playhead-label {
  position: absolute;
  top: 10px;
  left: 4px;
  font-size: 0.65rem;
  color: #ff4444;
  white-space: nowrap;
  font-weight: 600;
  pointer-events: none;
}

// Snap guide
.snap-guide {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(255, 200, 0, 0.6);
  z-index: 4;
  pointer-events: none;
}
</style>
