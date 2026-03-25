<template>
  <Teleport to="body">
    <Transition name="dropzone-fade">
      <div
        v-if="isDragging"
        class="global-drop-zone"
        @drop.prevent.stop="onDrop"
        @dragover.prevent.stop
        @dragleave.prevent.stop="onDragLeave"
      >
        <div class="drop-zone-content">
          <upload-cloud-icon class="drop-icon" :size="64" />
          <p class="drop-title">释放文件以上传</p>
          <p class="drop-hint">支持拖拽文件或文件夹</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { UploadCloudIcon } from 'lucide-vue-next'

/**
 * 全局拖拽上传覆盖层
 *
 * 监听整个 document 的拖拽事件，当用户拖拽文件进入浏览器窗口时
 * 显示全屏半透明覆盖层。支持文件和文件夹拖拽。
 *
 * 使用 dragCounter 计数器而非布尔值来正确处理子元素触发的
 * dragleave 事件。
 */
export default {
  name: 'global-drop-zone',

  components: {
    UploadCloudIcon
  },

  emits: ['files-dropped'],

  data() {
    return {
      isDragging: false,
      dragCounter: 0
    }
  },

  mounted() {
    document.addEventListener('dragenter', this.onDocDragEnter)
    document.addEventListener('dragover', this.onDocDragOver)
    document.addEventListener('dragleave', this.onDocDragLeave)
    document.addEventListener('drop', this.onDocDrop)
    document.addEventListener('paste', this.onPaste)
  },

  beforeUnmount() {
    document.removeEventListener('dragenter', this.onDocDragEnter)
    document.removeEventListener('dragover', this.onDocDragOver)
    document.removeEventListener('dragleave', this.onDocDragLeave)
    document.removeEventListener('drop', this.onDocDrop)
    document.removeEventListener('paste', this.onPaste)
  },

  methods: {
    /**
     * 检查拖拽内容是否包含文件
     */
    hasFiles(event) {
      if (!event.dataTransfer) return false
      const types = event.dataTransfer.types
      return types && (types.indexOf('Files') >= 0 || types.includes('Files'))
    },

    onDocDragEnter(event) {
      event.preventDefault()
      if (!this.hasFiles(event)) return
      this.dragCounter++
      if (this.dragCounter === 1) {
        this.isDragging = true
      }
    },

    onDocDragOver(event) {
      event.preventDefault()
    },

    onDocDragLeave(event) {
      event.preventDefault()
      this.dragCounter--
      if (this.dragCounter <= 0) {
        this.dragCounter = 0
        this.isDragging = false
      }
    },

    onDocDrop(event) {
      event.preventDefault()
      this.dragCounter = 0
      this.isDragging = false
    },

    onDragLeave(event) {
      // 覆盖层自身的 dragleave
      this.dragCounter--
      if (this.dragCounter <= 0) {
        this.dragCounter = 0
        this.isDragging = false
      }
    },

    /**
     * 文件放下处理：支持文件夹递归读取
     */
    async onDrop(event) {
      this.dragCounter = 0
      this.isDragging = false

      const items = event.dataTransfer.items
      if (!items || items.length === 0) return

      const files = []
      const promises = []

      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        // 优先使用 FileSystemEntry API（支持文件夹）
        const entry =
          item.webkitGetAsEntry?.() || item.getAsEntry?.()
        if (entry) {
          promises.push(this.readEntry(entry).then(f => files.push(...f)))
        } else if (item.kind === 'file') {
          const file = item.getAsFile()
          if (file) files.push(file)
        }
      }

      await Promise.all(promises)

      if (files.length > 0) {
        this.$emit('files-dropped', files)
      }
    },

    /**
     * 递归读取 FileSystemEntry（支持文件夹）
     */
    async readEntry(entry) {
      if (entry.isFile) {
        return [await new Promise((resolve, reject) => {
          entry.file(resolve, reject)
        })]
      }
      if (entry.isDirectory) {
        const reader = entry.createReader()
        const allEntries = []
        // readEntries 可能分批返回，需要循环读取
        let batch
        do {
          batch = await new Promise((resolve, reject) => {
            reader.readEntries(resolve, reject)
          })
          allEntries.push(...batch)
        } while (batch.length > 0)

        const files = []
        for (const e of allEntries) {
          const subFiles = await this.readEntry(e)
          files.push(...subFiles)
        }
        return files
      }
      return []
    },

    /**
     * 粘贴上传：Ctrl+V 粘贴图片
     */
    onPaste(event) {
      // 如果焦点在输入框中，不拦截粘贴
      const active = document.activeElement
      if (
        active &&
        (active.tagName === 'INPUT' ||
          active.tagName === 'TEXTAREA' ||
          active.isContentEditable)
      ) {
        return
      }

      const items = event.clipboardData?.items
      if (!items) return

      const files = []
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.kind === 'file') {
          const file = item.getAsFile()
          if (file) {
            // 为粘贴的图片生成有意义的文件名
            const timestamp = new Date()
              .toISOString()
              .replace(/[:.]/g, '-')
              .slice(0, 19)
            const ext = file.type.split('/')[1] || 'png'
            const namedFile = new File(
              [file],
              `paste-${timestamp}.${ext}`,
              { type: file.type }
            )
            files.push(namedFile)
          }
        }
      }

      if (files.length > 0) {
        event.preventDefault()
        this.$emit('files-dropped', files)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.global-drop-zone {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: copy;
}

.drop-zone-content {
  text-align: center;
  padding: 3rem;
  border: 3px dashed var(--brand-accent, #00b242);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
}

.drop-icon {
  color: var(--brand-accent, #00b242);
  margin-bottom: 1rem;
}

.drop-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 0.5rem;
}

.drop-hint {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

// 过渡动画
.dropzone-fade-enter-active,
.dropzone-fade-leave-active {
  transition: opacity 0.2s ease;
}

.dropzone-fade-enter-from,
.dropzone-fade-leave-to {
  opacity: 0;
}
</style>
