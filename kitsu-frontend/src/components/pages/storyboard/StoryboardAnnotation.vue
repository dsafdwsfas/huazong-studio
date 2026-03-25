<template>
  <div class="storyboard-annotation">
    <!-- Top bar -->
    <div class="annotation-header">
      <button class="back-button" @click="$emit('close')">
        <ArrowLeftIcon :size="18" />
        <span>返回</span>
      </button>
      <h3 class="shot-title">{{ shot.name }}</h3>
      <div class="nav-buttons">
        <button @click="$emit('prev')" :disabled="!hasPrev">
          <ChevronLeftIcon :size="18" />
        </button>
        <button @click="$emit('next')" :disabled="!hasNext">
          <ChevronRightIcon :size="18" />
        </button>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="annotation-toolbar">
      <div class="tool-group">
        <button
          v-for="tool in tools"
          :key="tool.id"
          class="tool-button"
          :class="{ active: activeTool === tool.id }"
          :title="tool.label"
          @click="onToolSelect(tool.id)"
        >
          <component :is="tool.icon" :size="16" />
        </button>
      </div>

      <div class="toolbar-separator"></div>

      <!-- Color palette -->
      <div class="color-group">
        <button
          v-for="color in palette"
          :key="color"
          class="color-swatch"
          :class="{ active: pencilColor === color }"
          :style="{ backgroundColor: color }"
          @click="onColorSelect(color)"
        ></button>
      </div>

      <div class="toolbar-separator"></div>

      <!-- Actions -->
      <div class="action-group">
        <button class="tool-button" title="撤销 (Ctrl+Z)" @click="undoLastAction">
          <Undo2Icon :size="16" />
        </button>
        <button class="tool-button" title="重做 (Ctrl+Y)" @click="redoLastAction">
          <Redo2Icon :size="16" />
        </button>
        <button class="tool-button" title="清除标注" @click="clearAllAnnotations">
          <Trash2Icon :size="16" />
        </button>
        <button class="tool-button save-button" title="保存" @click="onSaveAnnotations">
          <SaveIcon :size="16" />
        </button>
      </div>
    </div>

    <!-- Main content -->
    <div class="annotation-content">
      <!-- Shot mini list (sidebar) -->
      <div class="shot-sidebar">
        <div
          v-for="s in shots"
          :key="s.id"
          class="shot-mini"
          :class="{ active: s.id === shot.id }"
          @click="$emit('select-shot', s)"
        >
          <img
            v-if="s.preview_file_id"
            :src="getThumbnailUrl(s.preview_file_id)"
            :alt="s.name"
          />
          <div v-else class="empty-mini"></div>
          <span class="mini-label">{{ s.name }}</span>
        </div>
      </div>

      <!-- Canvas area -->
      <div class="canvas-area" ref="canvasContainer">
        <!-- Audio player (shown for audio shots) -->
        <AudioAnnotationPlayer
          v-if="isAudioShot"
          ref="audioPlayer"
          :preview-file-id="shot.preview_file_id"
          :extension="shot.preview_file_extension || 'mp3'"
          :duration="shot.duration || 0"
          :markers="audioMarkers"
          @time-change="onAudioTimeChange"
          @pause="onAudioPause"
          @ready="onAudioReady"
          @marker-add="onAudioMarkerAdd"
          @marker-update="onAudioMarkerUpdate"
          @marker-delete="onAudioMarkerDelete"
          @marker-click="onAudioMarkerClick"
        />
        <!-- Video player (shown for video shots) -->
        <VideoAnnotationPlayer
          v-if="isVideoShot"
          ref="videoPlayer"
          :preview-file-id="shot.preview_file_id"
          :duration="shot.duration || 0"
          :fps="shot.fps || 24"
          :annotations="frameAnnotations"
          @frame-change="onVideoFrameChange"
          @pause="onVideoPause"
          @ready="onVideoReady"
          @annotation-click="onAnnotationMarkerClick"
        />
        <div v-if="!isAudioShot" class="canvas-wrapper" ref="canvasWrapper">
          <canvas ref="annotation-canvas"></canvas>
        </div>
        <!-- Video frame indicator -->
        <div v-if="isVideoShot" class="video-frame-info">
          <span class="frame-badge">帧 {{ currentVideoFrame }}</span>
          <button
            class="btn-capture-frame"
            title="在当前帧添加标注"
            @click="captureAndAnnotate"
          >
            标注此帧
          </button>
        </div>
        <!-- Shot info overlay -->
        <div class="shot-info-overlay">
          <span v-if="shot.nb_frames">{{ shot.nb_frames }} 帧</span>
          <span v-if="shot.fps">{{ shot.fps }} fps</span>
          <span
            class="status-badge"
            :class="shot.status"
          >{{ statusLabel }}</span>
        </div>
      </div>
    </div>

    <!-- Description -->
    <div class="shot-description" v-if="shot.description">
      <p>{{ shot.description }}</p>
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import { fabric } from 'fabric'
import { PSBrush } from 'fabricjs-psbrush'
import {
  ArrowLeftIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  MousePointerIcon,
  PencilIcon,
  EraserIcon,
  SquareIcon,
  CircleIcon,
  MoveRightIcon,
  TypeIcon,
  FlagIcon,
  RulerIcon,
  Undo2Icon,
  Redo2Icon,
  Trash2Icon,
  SaveIcon
} from 'lucide-vue-next'

import { annotationMixin } from '@/components/mixins/annotation'
import AudioAnnotationPlayer from '@/components/pages/storyboard/AudioAnnotationPlayer.vue'
import VideoAnnotationPlayer from '@/components/pages/storyboard/VideoAnnotationPlayer.vue'

export default {
  name: 'storyboard-annotation',

  mixins: [annotationMixin],

  components: {
    ArrowLeftIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
    MousePointerIcon,
    PencilIcon,
    EraserIcon,
    SquareIcon,
    CircleIcon,
    MoveRightIcon,
    TypeIcon,
    FlagIcon,
    RulerIcon,
    Undo2Icon,
    Redo2Icon,
    Trash2Icon,
    SaveIcon,
    AudioAnnotationPlayer,
    VideoAnnotationPlayer
  },

  props: {
    shot: { type: Object, required: true },
    shots: { type: Array, default: () => [] },
    hasPrev: { type: Boolean, default: false },
    hasNext: { type: Boolean, default: false }
  },

  emits: ['close', 'prev', 'next', 'select-shot', 'save', 'annotation-changed'],

  data() {
    return {
      activeTool: 'select',
      toolCleanupFn: null,
      palette: [
        '#ff3860', '#ff9f43', '#ffd32a', '#0abde3',
        '#10ac84', '#ffffff', '#000000'
      ],
      currentVideoFrame: 0,
      frameAnnotations: [],
      videoReady: false,
      audioMarkers: [],
      currentAudioTime: 0,
      tools: [
        { id: 'select', label: '选择', icon: 'MousePointerIcon' },
        { id: 'pencil', label: '画笔', icon: 'PencilIcon' },
        { id: 'eraser', label: '橡皮', icon: 'EraserIcon' },
        { id: 'rectangle', label: '矩形', icon: 'SquareIcon' },
        { id: 'circle', label: '圆形', icon: 'CircleIcon' },
        { id: 'arrow', label: '箭头', icon: 'MoveRightIcon' },
        { id: 'text', label: '文字', icon: 'TypeIcon' },
        { id: 'marker', label: '标记', icon: 'FlagIcon' },
        { id: 'measure', label: '测量', icon: 'RulerIcon' }
      ]
    }
  },

  computed: {
    isVideoShot() {
      const ext = (this.shot.preview_file_extension || '').toLowerCase()
      return ['mp4', 'mov', 'avi', 'mkv', 'webm', 'wmv', 'm4v'].includes(ext)
    },

    isAudioShot() {
      const ext = (this.shot.preview_file_extension || '').toLowerCase()
      return ['mp3', 'wav'].includes(ext)
    },

    statusLabel() {
      const map = {
        standby: '待机',
        waiting: '待机',
        running: '进行中',
        complete: '完成',
        canceled: '已取消',
        cancelled: '已取消'
      }
      return map[this.shot.status] || this.shot.status
    },

    /**
     * Override from annotationMixin — ref name used for canvas element.
     */
    annotationCanvas() {
      return this.$refs['annotation-canvas']
    }
  },

  watch: {
    shot: {
      handler(newShot) {
        this.loadShotPreview(newShot)
      },
      deep: false
    }
  },

  mounted() {
    this.initCanvas()
    this.loadShotPreview(this.shot)
    window.addEventListener('keydown', this.onKeydown)
    window.addEventListener('resize', this.onResize)
  },

  beforeUnmount() {
    this.cleanupCurrentTool()
    if (this.fabricCanvas) this.fabricCanvas.dispose()
    window.removeEventListener('keydown', this.onKeydown)
    window.removeEventListener('resize', this.onResize)
  },

  methods: {
    // ---- Canvas setup ----

    initCanvas() {
      const wrapper = this.$refs.canvasWrapper
      if (!wrapper) return

      const width = wrapper.clientWidth || 800
      const height = Math.round(width * 9 / 16)

      const canvasEl = this.$refs['annotation-canvas']
      this.fabricCanvas = markRaw(new fabric.Canvas(canvasEl, {
        width,
        height,
        backgroundColor: '#1a1a1a',
        selection: true,
        preserveObjectStacking: true
      }))

      // Wire up mixin's object:added handler for undo stack
      this.fabricCanvas.on('object:added', (e) => {
        if (e.target && !this.$options.silentAnnnotation) {
          this.onObjectAdded(e)
        }
      })

      // Track modifications for persistence
      this.fabricCanvas.on('object:modified', (e) => {
        if (e.target) {
          this.addToUpdates(e.target)
        }
      })

      this.resetUndoStacks()
    },

    // ---- Shot preview loading ----

    loadShotPreview(shot) {
      if (!this.fabricCanvas) return

      // Reset undo stacks for new shot
      this.resetUndoStacks()
      this.currentVideoFrame = 0
      this.currentAudioTime = 0
      this.frameAnnotations = []
      this.audioMarkers = []

      // Clear canvas
      this.fabricCanvas.clear()
      this.fabricCanvas.backgroundColor = '#1a1a1a'

      if (!shot.preview_file_id) {
        this.fabricCanvas.renderAll()
        return
      }

      // For audio shots, AudioAnnotationPlayer handles display (no canvas)
      if (this.isAudioShot) {
        this.loadAudioMarkersList()
        return
      }

      // For video shots, VideoAnnotationPlayer handles display
      // Canvas starts empty, frame will be captured on pause
      if (this.isVideoShot) {
        this.fabricCanvas.renderAll()
        this.loadFrameAnnotationsList()
        return
      }

      const url =
        `/api/pictures/originals/preview-files/${shot.preview_file_id}.png`
      this.$options.silentAnnnotation = true
      fabric.Image.fromURL(url, (img) => {
        if (!img || !this.fabricCanvas) {
          this.$options.silentAnnnotation = false
          return
        }

        const canvas = this.fabricCanvas
        const scale = Math.min(
          canvas.width / img.width,
          canvas.height / img.height
        )

        img.set({
          scaleX: scale,
          scaleY: scale,
          left: (canvas.width - img.width * scale) / 2,
          top: (canvas.height - img.height * scale) / 2,
          selectable: false,
          evented: false
        })

        canvas.setBackgroundImage(img, () => {
          canvas.renderAll()
          this.$options.silentAnnnotation = false
          this.loadShotAnnotations(shot)
        })
      }, { crossOrigin: 'anonymous' })
    },

    loadShotAnnotations(shot) {
      // Load existing annotations from the shot's preview file annotations.
      // The annotation format matches the mixin's expected structure:
      // { time, frame, drawing: { objects: [...] } }
      if (!shot.annotations || !shot.annotations.length) return

      this.$options.silentAnnnotation = true
      const annotation = shot.annotations[0]
      if (annotation && annotation.drawing) {
        this.loadSingleAnnotation(annotation)
      }
      this.$options.silentAnnnotation = false
    },

    // ---- Tool selection ----

    cleanupCurrentTool() {
      if (this.toolCleanupFn) {
        this.toolCleanupFn()
        this.toolCleanupFn = null
      }
    },

    onToolSelect(toolId) {
      this.cleanupCurrentTool()
      this.activeTool = toolId
      const canvas = this.fabricCanvas
      if (!canvas) return

      // Reset common state
      canvas.isDrawingMode = false
      canvas.selection = true
      canvas.defaultCursor = 'default'

      switch (toolId) {
        case 'select':
          // Default state, nothing extra to do
          break

        case 'pencil':
          this.enablePencilTool(canvas)
          break

        case 'eraser':
          this.enableEraserTool(canvas)
          break

        case 'rectangle':
          this.enableRectangleTool(canvas)
          break

        case 'circle':
          this.enableCircleTool(canvas)
          break

        case 'arrow':
          this.enableArrowTool(canvas)
          break

        case 'text':
          this.enableTextTool(canvas)
          break

        case 'marker':
          this.enableMarkerTool(canvas)
          break

        case 'measure':
          this.enableMeasureTool(canvas)
          break
      }
    },

    // ---- Tool implementations ----

    enablePencilTool(canvas) {
      canvas.isDrawingMode = true
      const brush = new PSBrush(canvas)
      canvas.freeDrawingBrush = brush
      brush.pressureManager.fallback = 0.5
      canvas.freeDrawingBrush.color = this.pencilColor
      canvas.freeDrawingBrush.width = 4
    },

    enableEraserTool(canvas) {
      if (fabric.EraserBrush) {
        canvas.isDrawingMode = true
        canvas.freeDrawingBrush = new fabric.EraserBrush(canvas)
        canvas.freeDrawingBrush.width = 10
      } else {
        // Fallback: click-to-remove mode
        canvas.selection = false
        canvas.defaultCursor = 'crosshair'
        const onErase = (o) => {
          if (o.target && o.target.selectable !== false) {
            this.deleteObject(o.target)
          }
        }
        canvas.on('mouse:down', onErase)
        this.toolCleanupFn = () => {
          canvas.off('mouse:down', onErase)
          canvas.selection = true
          canvas.defaultCursor = 'default'
        }
      }
    },

    enableRectangleTool(canvas) {
      canvas.selection = false
      canvas.defaultCursor = 'crosshair'
      let isDrawing = false
      let startX = 0
      let startY = 0
      let rect = null

      const onDown = (o) => {
        const pointer = canvas.getPointer(o.e)
        isDrawing = true
        startX = pointer.x
        startY = pointer.y
        rect = markRaw(new fabric.Rect({
          left: startX,
          top: startY,
          width: 0,
          height: 0,
          fill: 'transparent',
          stroke: this.pencilColor,
          strokeWidth: 2,
          selectable: true
        }))
        this.$options.silentAnnnotation = true
        canvas.add(rect)
        this.$options.silentAnnnotation = false
      }

      const onMove = (o) => {
        if (!isDrawing || !rect) return
        const pointer = canvas.getPointer(o.e)
        const w = pointer.x - startX
        const h = pointer.y - startY
        rect.set({
          left: w >= 0 ? startX : pointer.x,
          top: h >= 0 ? startY : pointer.y,
          width: Math.abs(w),
          height: Math.abs(h)
        })
        canvas.renderAll()
      }

      const onUp = () => {
        if (!isDrawing) return
        isDrawing = false
        if (rect && (rect.width > 2 || rect.height > 2)) {
          this.setObjectData(rect)
          this.addToAdditions(rect)
          this.$options.doneActionStack.push({ type: 'add', obj: rect })
        } else if (rect) {
          canvas.remove(rect)
        }
        rect = null
        canvas.renderAll()
      }

      canvas.on('mouse:down', onDown)
      canvas.on('mouse:move', onMove)
      canvas.on('mouse:up', onUp)

      this.toolCleanupFn = () => {
        canvas.off('mouse:down', onDown)
        canvas.off('mouse:move', onMove)
        canvas.off('mouse:up', onUp)
        canvas.selection = true
        canvas.defaultCursor = 'default'
      }
    },

    enableCircleTool(canvas) {
      canvas.selection = false
      canvas.defaultCursor = 'crosshair'
      let isDrawing = false
      let startX = 0
      let startY = 0
      let ellipse = null

      const onDown = (o) => {
        const pointer = canvas.getPointer(o.e)
        isDrawing = true
        startX = pointer.x
        startY = pointer.y
        ellipse = markRaw(new fabric.Ellipse({
          left: startX,
          top: startY,
          rx: 0,
          ry: 0,
          fill: 'transparent',
          stroke: this.pencilColor,
          strokeWidth: 2,
          selectable: true
        }))
        this.$options.silentAnnnotation = true
        canvas.add(ellipse)
        this.$options.silentAnnnotation = false
      }

      const onMove = (o) => {
        if (!isDrawing || !ellipse) return
        const pointer = canvas.getPointer(o.e)
        const rx = Math.abs(pointer.x - startX) / 2
        const ry = Math.abs(pointer.y - startY) / 2
        ellipse.set({
          left: Math.min(startX, pointer.x),
          top: Math.min(startY, pointer.y),
          rx,
          ry
        })
        canvas.renderAll()
      }

      const onUp = () => {
        if (!isDrawing) return
        isDrawing = false
        if (ellipse && (ellipse.rx > 2 || ellipse.ry > 2)) {
          this.setObjectData(ellipse)
          this.addToAdditions(ellipse)
          this.$options.doneActionStack.push({ type: 'add', obj: ellipse })
        } else if (ellipse) {
          canvas.remove(ellipse)
        }
        ellipse = null
        canvas.renderAll()
      }

      canvas.on('mouse:down', onDown)
      canvas.on('mouse:move', onMove)
      canvas.on('mouse:up', onUp)

      this.toolCleanupFn = () => {
        canvas.off('mouse:down', onDown)
        canvas.off('mouse:move', onMove)
        canvas.off('mouse:up', onUp)
        canvas.selection = true
        canvas.defaultCursor = 'default'
      }
    },

    enableArrowTool(canvas) {
      canvas.selection = false
      canvas.defaultCursor = 'crosshair'
      let isDrawing = false
      let line = null
      let startX = 0
      let startY = 0

      const onDown = (o) => {
        const pointer = canvas.getPointer(o.e)
        isDrawing = true
        startX = pointer.x
        startY = pointer.y
        line = markRaw(new fabric.Line(
          [startX, startY, startX, startY],
          {
            stroke: this.pencilColor,
            strokeWidth: 2,
            selectable: true
          }
        ))
        this.$options.silentAnnnotation = true
        canvas.add(line)
        this.$options.silentAnnnotation = false
      }

      const onMove = (o) => {
        if (!isDrawing || !line) return
        const pointer = canvas.getPointer(o.e)
        line.set({ x2: pointer.x, y2: pointer.y })
        canvas.renderAll()
      }

      const onUp = () => {
        if (!isDrawing || !line) return
        isDrawing = false

        const dx = line.x2 - line.x1
        const dy = line.y2 - line.y1
        const length = Math.sqrt(dx * dx + dy * dy)

        if (length < 5) {
          canvas.remove(line)
          line = null
          return
        }

        // Add arrowhead as a triangle at the end
        const angle = Math.atan2(dy, dx)
        const headLen = 12
        const arrowHead = markRaw(new fabric.Triangle({
          left: line.x2,
          top: line.y2,
          originX: 'center',
          originY: 'center',
          width: headLen,
          height: headLen,
          angle: (angle * 180 / Math.PI) + 90,
          fill: this.pencilColor,
          selectable: false,
          evented: false
        }))

        // Group line and arrowhead
        const group = markRaw(new fabric.Group([line, arrowHead], {
          selectable: true
        }))
        canvas.remove(line)
        this.$options.silentAnnnotation = true
        canvas.remove(arrowHead)
        this.$options.silentAnnnotation = false

        canvas.add(group)
        this.setObjectData(group)
        this.addToAdditions(group)
        this.$options.doneActionStack.push({ type: 'add', obj: group })

        line = null
        canvas.renderAll()
      }

      canvas.on('mouse:down', onDown)
      canvas.on('mouse:move', onMove)
      canvas.on('mouse:up', onUp)

      this.toolCleanupFn = () => {
        canvas.off('mouse:down', onDown)
        canvas.off('mouse:move', onMove)
        canvas.off('mouse:up', onUp)
        canvas.selection = true
        canvas.defaultCursor = 'default'
      }
    },

    enableTextTool(canvas) {
      canvas.selection = false
      canvas.defaultCursor = 'text'

      const onClick = (o) => {
        if (canvas.getActiveObject()) return
        const pointer = canvas.getPointer(o.e)
        const baseHeight = 320
        let fontSize = 14
        if (canvas.getHeight() > baseHeight) {
          fontSize = fontSize * (canvas.getHeight() / baseHeight)
        }
        const text = markRaw(new fabric.IText('输入文字', {
          left: pointer.x,
          top: pointer.y,
          fontSize,
          fill: this.pencilColor,
          fontFamily: 'Arial',
          backgroundColor: 'rgba(255,255,255,0.8)',
          padding: 8
        }))

        canvas.add(text)
        this.setObjectData(text)
        this.addToAdditions(text)
        canvas.setActiveObject(text)
        text.enterEditing()
        text.selectAll()
        text.hiddenTextarea.onblur = () => {
          this.saveAnnotations()
        }
      }

      canvas.on('mouse:down', onClick)

      this.toolCleanupFn = () => {
        canvas.off('mouse:down', onClick)
        canvas.selection = true
        canvas.defaultCursor = 'default'
      }
    },

    enableMarkerTool(canvas) {
      canvas.selection = false
      canvas.defaultCursor = 'crosshair'
      let markerCount = canvas.getObjects().filter(
        o => o.objectType === 'marker'
      ).length

      const onClick = (o) => {
        const pointer = canvas.getPointer(o.e)
        markerCount++
        const radius = 14
        const circle = markRaw(new fabric.Circle({
          left: pointer.x - radius,
          top: pointer.y - radius,
          radius,
          fill: this.pencilColor,
          stroke: '#fff',
          strokeWidth: 2,
          selectable: true,
          objectType: 'marker',
          markerNumber: markerCount
        }))

        const label = markRaw(new fabric.Text(String(markerCount), {
          left: pointer.x,
          top: pointer.y,
          originX: 'center',
          originY: 'center',
          fontSize: 12,
          fontFamily: 'Arial',
          fontWeight: 'bold',
          fill: '#fff',
          selectable: false,
          evented: false
        }))

        const group = markRaw(new fabric.Group([circle, label], {
          selectable: true,
          objectType: 'marker',
          markerNumber: markerCount
        }))

        canvas.add(group)
        this.setObjectData(group)
        this.addToAdditions(group)
        this.$options.doneActionStack.push({ type: 'add', obj: group })
        canvas.renderAll()
      }

      canvas.on('mouse:down', onClick)

      this.toolCleanupFn = () => {
        canvas.off('mouse:down', onClick)
        canvas.selection = true
        canvas.defaultCursor = 'default'
      }
    },

    enableMeasureTool(canvas) {
      canvas.selection = false
      canvas.defaultCursor = 'crosshair'
      let isDrawing = false
      let line = null
      let label = null
      let startX = 0
      let startY = 0

      const onDown = (o) => {
        const pointer = canvas.getPointer(o.e)
        isDrawing = true
        startX = pointer.x
        startY = pointer.y
        line = markRaw(new fabric.Line(
          [startX, startY, startX, startY],
          {
            stroke: this.pencilColor,
            strokeWidth: 1,
            strokeDashArray: [5, 3],
            selectable: false,
            evented: false
          }
        ))
        this.$options.silentAnnnotation = true
        canvas.add(line)
        this.$options.silentAnnnotation = false
      }

      const onMove = (o) => {
        if (!isDrawing || !line) return
        const pointer = canvas.getPointer(o.e)
        line.set({ x2: pointer.x, y2: pointer.y })

        // Update distance label
        const dx = pointer.x - startX
        const dy = pointer.y - startY
        const dist = Math.round(Math.sqrt(dx * dx + dy * dy))
        if (label) canvas.remove(label)
        label = markRaw(new fabric.Text(`${dist}px`, {
          left: (startX + pointer.x) / 2,
          top: (startY + pointer.y) / 2 - 12,
          fontSize: 11,
          fill: this.pencilColor,
          fontFamily: 'Arial',
          backgroundColor: 'rgba(0,0,0,0.6)',
          padding: 3,
          selectable: false,
          evented: false
        }))
        this.$options.silentAnnnotation = true
        canvas.add(label)
        this.$options.silentAnnnotation = false
        canvas.renderAll()
      }

      const onUp = () => {
        if (!isDrawing) return
        isDrawing = false
        if (line && label) {
          const group = markRaw(new fabric.Group([line, label], {
            selectable: true,
            objectType: 'measure'
          }))
          canvas.remove(line)
          canvas.remove(label)
          canvas.add(group)
          this.setObjectData(group)
          this.addToAdditions(group)
          this.$options.doneActionStack.push({ type: 'add', obj: group })
        }
        line = null
        label = null
        canvas.renderAll()
      }

      canvas.on('mouse:down', onDown)
      canvas.on('mouse:move', onMove)
      canvas.on('mouse:up', onUp)

      this.toolCleanupFn = () => {
        canvas.off('mouse:down', onDown)
        canvas.off('mouse:move', onMove)
        canvas.off('mouse:up', onUp)
        canvas.selection = true
        canvas.defaultCursor = 'default'
      }
    },

    // ---- Color ----

    onColorSelect(color) {
      this.pencilColor = color
      this.textColor = color
      if (this.fabricCanvas && this.fabricCanvas.freeDrawingBrush) {
        this.fabricCanvas.freeDrawingBrush.color = color
      }
      // Re-apply shape tools with the new color
      const shapeTool = ['rectangle', 'circle', 'arrow', 'marker', 'measure']
      if (shapeTool.includes(this.activeTool)) {
        this.onToolSelect(this.activeTool)
      }
    },

    // ---- Actions ----

    clearAllAnnotations() {
      if (!this.fabricCanvas) return
      const objects = this.fabricCanvas.getObjects().filter(
        o => o.selectable !== false
      )
      objects.forEach(o => {
        this.fabricCanvas.remove(o)
      })
      this.resetUndoStacks()
      this.fabricCanvas.renderAll()
    },

    onSaveAnnotations() {
      if (!this.fabricCanvas) return
      const objects = this.fabricCanvas.getObjects()
        .filter(o => o.selectable !== false)
        .map(o => {
          this.setObjectData(o)
          return o.serialize ? o.serialize() : o.toJSON(['objectType', 'markerNumber'])
        })

      const fps = this.shot.fps || 24
      const frame = this.isVideoShot ? this.currentVideoFrame : 0
      const time = this.isVideoShot ? frame / fps : 0

      if (this.isVideoShot) {
        // Save per-frame annotation via dedicated API
        this.$store.dispatch('saveFrameAnnotation', {
          shotId: this.shot.id,
          frame,
          time,
          drawing: {
            objects,
            canvasWidth: this.fabricCanvas.width,
            canvasHeight: this.fabricCanvas.height
          }
        }).then(() => {
          this.loadFrameAnnotationsList()
          this.$emit('annotation-changed')
        }).catch(err => {
          console.error('Failed to save frame annotation:', err)
        })
      } else {
        this.$emit('save', {
          shotId: this.shot.id,
          previewFileId: this.shot.preview_file_id,
          annotations: {
            drawing: {
              objects,
              canvasWidth: this.fabricCanvas.width,
              canvasHeight: this.fabricCanvas.height
            },
            time: 0,
            frame: 0
          }
        })
      }
    },

    // ---- Mixin hooks ----

    /**
     * Required by annotationMixin — returns current playback time.
     * Storyboard annotations are static (single frame), so always 0.
     */
    getCurrentTime() {
      return 0
    },

    /**
     * Required by annotationMixin — returns current frame number.
     */
    getCurrentFrame() {
      return 0
    },

    /**
     * Required by annotationMixin — marks last annotation time.
     */
    markLastAnnotationTime() {
      this.lastAnnotationTime = new Date().toISOString()
    },

    /**
     * Required by annotationMixin — persist annotations.
     * For storyboard, we emit instead of directly saving to store.
     */
    saveAnnotations() {
      this.$emit('annotation-changed')
    },

    // ---- Helpers ----

    getThumbnailUrl(previewFileId) {
      return `/api/pictures/thumbnails-square/preview-files/${previewFileId}.png`
    },

    onKeydown(e) {
      // Don't intercept when typing in a text input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

      if (e.ctrlKey && e.key === 'z') {
        e.preventDefault()
        this.undoLastAction()
      } else if (e.ctrlKey && e.key === 'y') {
        e.preventDefault()
        this.redoLastAction()
      } else if (e.key === 'Delete') {
        this.deleteSelection()
      } else if (e.key === 'Escape') {
        this.onToolSelect('select')
      }
    },

    // ---- Audio mode methods ----

    onAudioTimeChange({ time }) {
      this.currentAudioTime = time
    },

    onAudioPause() {
      // Nothing extra needed for audio (no canvas frame capture)
    },

    onAudioReady({ duration }) {
      this.loadAudioMarkersList()
    },

    async loadAudioMarkersList() {
      if (!this.shot.id) return
      try {
        const data = await this.$store.dispatch('loadAudioMarkers', {
          shotId: this.shot.id
        })
        this.audioMarkers = data?.markers || []
      } catch {
        this.audioMarkers = []
      }
    },

    async onAudioMarkerAdd({ time, label }) {
      try {
        await this.$store.dispatch('addAudioMarker', {
          shotId: this.shot.id,
          time,
          label
        })
        await this.loadAudioMarkersList()
        this.$emit('annotation-changed')
      } catch (err) {
        console.error('Failed to add audio marker:', err)
      }
    },

    async onAudioMarkerUpdate({ index, time, label }) {
      try {
        await this.$store.dispatch('updateAudioMarker', {
          shotId: this.shot.id,
          markerIndex: index,
          time,
          label
        })
        await this.loadAudioMarkersList()
      } catch (err) {
        console.error('Failed to update audio marker:', err)
      }
    },

    async onAudioMarkerDelete({ index }) {
      try {
        await this.$store.dispatch('deleteAudioMarker', {
          shotId: this.shot.id,
          markerIndex: index
        })
        await this.loadAudioMarkersList()
        this.$emit('annotation-changed')
      } catch (err) {
        console.error('Failed to delete audio marker:', err)
      }
    },

    onAudioMarkerClick({ index, marker }) {
      if (this.$refs.audioPlayer && marker.time !== undefined) {
        this.$refs.audioPlayer.seekToTime(marker.time)
      }
    },

    // ---- Video mode methods ----

    onVideoFrameChange({ frame }) {
      this.currentVideoFrame = frame
    },

    onVideoPause() {
      // When video pauses, capture current frame as canvas background
      if (this.isVideoShot && this.$refs.videoPlayer) {
        this.loadVideoFrameToCanvas()
      }
    },

    onVideoReady({ duration, fps }) {
      this.videoReady = true
      this.loadFrameAnnotationsList()
    },

    onAnnotationMarkerClick({ index, annotation }) {
      // Jump to annotated frame and load its annotations on canvas
      if (this.$refs.videoPlayer && annotation.frame !== undefined) {
        this.$refs.videoPlayer.seekToFrame(annotation.frame)
        this.currentVideoFrame = annotation.frame
        this.loadVideoFrameToCanvas()
        this.loadFrameAnnotation(annotation)
      }
    },

    async loadVideoFrameToCanvas() {
      if (!this.$refs.videoPlayer || !this.fabricCanvas) return

      try {
        const bitmap = await this.$refs.videoPlayer.captureFrame()
        const canvas = this.fabricCanvas
        const wrapper = this.$refs.canvasWrapper
        const width = wrapper?.clientWidth || 800
        const height = Math.round(width * 9 / 16)

        // Create a temp canvas to convert ImageBitmap to data URL
        const tmpCanvas = document.createElement('canvas')
        tmpCanvas.width = bitmap.width
        tmpCanvas.height = bitmap.height
        const ctx = tmpCanvas.getContext('2d')
        ctx.drawImage(bitmap, 0, 0)
        const dataUrl = tmpCanvas.toDataURL('image/png')
        bitmap.close()

        this.$options.silentAnnnotation = true
        fabric.Image.fromURL(dataUrl, (img) => {
          if (!img || !this.fabricCanvas) {
            this.$options.silentAnnnotation = false
            return
          }
          const scale = Math.min(
            canvas.width / img.width,
            canvas.height / img.height
          )
          img.set({
            scaleX: scale,
            scaleY: scale,
            left: (canvas.width - img.width * scale) / 2,
            top: (canvas.height - img.height * scale) / 2,
            selectable: false,
            evented: false
          })
          canvas.setBackgroundImage(img, () => {
            canvas.renderAll()
            this.$options.silentAnnnotation = false
          })
        })
      } catch (err) {
        console.error('Failed to capture video frame:', err)
      }
    },

    captureAndAnnotate() {
      // Pause video and capture frame for annotation
      if (this.$refs.videoPlayer) {
        this.$refs.videoPlayer.pause()
        this.loadVideoFrameToCanvas()
      }
    },

    async loadFrameAnnotationsList() {
      // Load list of annotated frames from API
      if (!this.shot.id) return
      try {
        const data = await this.$store.dispatch('loadFrameAnnotations', {
          shotId: this.shot.id
        })
        this.frameAnnotations = (data?.annotated_frames || []).map((f) => ({
          frame: f.frame,
          time: f.time,
          drawing: {}
        }))
      } catch {
        this.frameAnnotations = []
      }
    },

    loadFrameAnnotation(annotation) {
      // Load a specific frame's annotation onto the canvas
      if (!annotation.drawing || !annotation.drawing.objects) return
      this.$options.silentAnnnotation = true
      this.loadSingleAnnotation(annotation)
      this.$options.silentAnnnotation = false
    },

    onResize() {
      if (!this.fabricCanvas || !this.$refs.canvasWrapper) return
      const wrapper = this.$refs.canvasWrapper
      const width = wrapper.clientWidth || 800
      const height = Math.round(width * 9 / 16)

      this.fabricCanvas.setWidth(width)
      this.fabricCanvas.setHeight(height)

      // Reload preview to recalculate image scaling
      this.loadShotPreview(this.shot)
    }
  }
}
</script>

<style lang="scss" scoped>
.storyboard-annotation {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
}

.annotation-header {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--border);
  gap: 1rem;

  .back-button {
    display: flex;
    align-items: center;
    gap: 4px;
    background: none;
    border: none;
    color: var(--text);
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;

    &:hover {
      background: var(--background-selectable);
    }
  }

  .shot-title {
    flex: 1;
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
  }

  .nav-buttons {
    display: flex;
    gap: 4px;

    button {
      background: none;
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 4px 8px;
      cursor: pointer;
      color: var(--text);

      &:hover:not(:disabled) {
        background: var(--background-selectable);
      }

      &:disabled {
        opacity: 0.3;
        cursor: default;
      }
    }
  }
}

.annotation-toolbar {
  display: flex;
  align-items: center;
  padding: 0.35rem 1rem;
  border-bottom: 1px solid var(--border);
  gap: 0.5rem;
  background: var(--background-alt);
}

.tool-group,
.action-group {
  display: flex;
  gap: 2px;
}

.tool-button {
  background: none;
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 5px 7px;
  cursor: pointer;
  color: var(--text);
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: var(--background-selectable);
  }

  &.active {
    background: var(--background-selected);
    border-color: var(--border);
  }

  &.save-button {
    color: var(--color-green);
  }
}

.toolbar-separator {
  width: 1px;
  height: 24px;
  background: var(--border);
  margin: 0 4px;
}

.color-group {
  display: flex;
  gap: 4px;
  align-items: center;
}

.color-swatch {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;

  &.active {
    border-color: var(--text);
    box-shadow: 0 0 0 1px var(--background);
  }

  &:hover {
    transform: scale(1.15);
  }
}

.annotation-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.shot-sidebar {
  width: 100px;
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 8px 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;

  .shot-mini {
    cursor: pointer;
    border-radius: 4px;
    overflow: hidden;
    border: 2px solid transparent;
    transition: border-color 0.15s;

    &.active {
      border-color: var(--color-primary);
    }

    &:hover {
      border-color: var(--border-strong);
    }

    img {
      width: 100%;
      aspect-ratio: 16 / 9;
      object-fit: cover;
      display: block;
    }

    .empty-mini {
      width: 100%;
      aspect-ratio: 16 / 9;
      background: var(--background-alt);
    }

    .mini-label {
      display: block;
      text-align: center;
      font-size: 0.7rem;
      padding: 2px;
      color: var(--text-alt);
    }
  }
}

.canvas-area {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111;
  overflow: hidden;
}

.canvas-wrapper {
  position: relative;
  max-width: 100%;
  max-height: 100%;
}

.video-frame-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: var(--background-alt, #2a2a2a);
  border-top: 1px solid var(--border);

  .frame-badge {
    font-size: 0.75rem;
    color: var(--text-alt);
    font-variant-numeric: tabular-nums;
  }

  .btn-capture-frame {
    padding: 2px 10px;
    font-size: 0.75rem;
    border: 1px solid var(--color-primary);
    border-radius: 4px;
    background: transparent;
    color: var(--color-primary);
    cursor: pointer;

    &:hover {
      background: var(--color-primary);
      color: #fff;
    }
  }
}

.shot-info-overlay {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  gap: 8px;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);

  .status-badge {
    padding: 1px 6px;
    border-radius: 3px;

    &.complete {
      background: rgba(0, 178, 66, 0.3);
    }

    &.running {
      background: rgba(255, 152, 0, 0.3);
    }

    &.standby,
    &.waiting {
      background: rgba(100, 100, 100, 0.3);
    }
  }
}

.shot-description {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.85rem;
  color: var(--text-alt);
  max-height: 60px;
  overflow-y: auto;

  p {
    margin: 0;
  }
}
</style>
