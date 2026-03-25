<template>
  <div class="batch-upload-modal" v-if="active">
    <div class="modal-backdrop" @click="$emit('close')" />
    <div class="modal-content">
      <div class="modal-header">
        <h3>批量上传分镜</h3>
        <button class="btn-close" @click="$emit('close')">
          <XIcon :size="18" />
        </button>
      </div>

      <div class="modal-body">
        <p class="upload-hint">
          文件名需与分镜编号匹配（如 SH010.png → 分镜 SH010）
        </p>

        <label class="drop-zone" :class="{ dragging: isDragging }">
          <input
            ref="fileInput"
            type="file"
            multiple
            accept="image/*"
            class="file-input"
            @change="onFilesSelected"
          />
          <div
            class="drop-content"
            @dragenter.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @dragover.prevent
            @drop.prevent="onDrop"
          >
            <UploadCloudIcon :size="32" />
            <span>拖拽文件到此处，或点击选择</span>
          </div>
        </label>

        <div v-if="files.length > 0" class="file-list">
          <div
            v-for="(file, index) in files"
            :key="index"
            class="file-item"
          >
            <img
              v-if="file.preview"
              :src="file.preview"
              class="file-thumb"
            />
            <div class="file-info">
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatSize(file.size) }}</span>
            </div>
            <button class="btn-remove" @click="removeFile(index)">
              <XIcon :size="14" />
            </button>
          </div>
        </div>

        <div v-if="uploadResult" class="upload-result">
          <p class="result-success">
            ✓ 匹配 {{ uploadResult.matched_count }} 个分镜
          </p>
          <p v-if="uploadResult.skipped_count > 0" class="result-skip">
            ✗ 跳过 {{ uploadResult.skipped_count }} 个文件：
            {{ uploadResult.skipped.join(', ') }}
          </p>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">
          {{ uploadResult ? '关闭' : '取消' }}
        </button>
        <button
          v-if="!uploadResult"
          class="btn-submit"
          :disabled="files.length === 0 || isUploading"
          @click="upload"
        >
          {{ isUploading ? '上传中...' : `上传 ${files.length} 个文件` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { UploadCloudIcon, XIcon } from 'lucide-vue-next'

export default {
  name: 'BatchUploadModal',

  components: { UploadCloudIcon, XIcon },

  props: {
    active: {
      type: Boolean,
      default: false
    },
    projectId: {
      type: String,
      default: ''
    },
    sequenceId: {
      type: String,
      default: ''
    }
  },

  emits: ['close', 'uploaded'],

  data() {
    return {
      files: [],
      isDragging: false,
      isUploading: false,
      uploadResult: null
    }
  },

  watch: {
    active(val) {
      if (val) {
        this.files = []
        this.uploadResult = null
      }
    }
  },

  methods: {
    onFilesSelected(event) {
      this.addFiles(event.target.files)
      event.target.value = ''
    },

    onDrop(event) {
      this.isDragging = false
      this.addFiles(event.dataTransfer.files)
    },

    addFiles(fileList) {
      for (const file of fileList) {
        if (!file.type.startsWith('image/')) continue
        const entry = {
          file,
          name: file.name,
          size: file.size,
          preview: null
        }
        // Generate preview
        const reader = new FileReader()
        reader.onload = (e) => {
          entry.preview = e.target.result
        }
        reader.readAsDataURL(file)
        this.files.push(entry)
      }
    },

    removeFile(index) {
      this.files.splice(index, 1)
    },

    async upload() {
      this.isUploading = true
      try {
        const formData = new FormData()
        for (const entry of this.files) {
          formData.append('files', entry.file)
        }
        if (this.sequenceId) {
          formData.append('sequence_id', this.sequenceId)
        }

        const response = await fetch(
          `/api/data/projects/${this.projectId}/storyboard/batch-upload`,
          {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
          }
        )
        this.uploadResult = await response.json()
        this.$emit('uploaded', this.uploadResult)
      } catch (err) {
        console.error('Batch upload failed:', err)
      } finally {
        this.isUploading = false
      }
    },

    formatSize(bytes) {
      if (bytes < 1024) return `${bytes}B`
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
      return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
    }
  }
}
</script>

<style lang="scss" scoped>
.batch-upload-modal {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  width: 480px;
  max-height: 80vh;
  background: var(--background);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);

  h3 { margin: 0; font-size: 1rem; font-weight: 600; }
}

.btn-close {
  background: none; border: none; cursor: pointer;
  color: var(--text-alt); padding: 4px; border-radius: 4px;
  &:hover { background: var(--background-hover); }
}

.modal-body {
  padding: 16px 20px;
  overflow-y: auto;
  flex: 1;
}

.upload-hint {
  font-size: 0.8rem;
  color: var(--text-alt);
  margin-bottom: 12px;
}

.drop-zone {
  display: block;
  cursor: pointer;
  margin-bottom: 12px;
}

.file-input { display: none; }

.drop-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  border: 2px dashed var(--border);
  border-radius: 8px;
  color: var(--text-alt);
  font-size: 0.85rem;
  transition: all 0.15s;

  &:hover, .dragging & {
    border-color: var(--color-primary);
    color: var(--color-primary);
    background: rgba(0, 120, 255, 0.03);
  }
}

.file-list {
  max-height: 200px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: 4px;
  &:hover { background: var(--background-hover, rgba(0,0,0,0.03)); }
}

.file-thumb {
  width: 40px; height: 28px; object-fit: cover;
  border-radius: 3px; flex-shrink: 0;
}

.file-info {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column;
}

.file-name {
  font-size: 0.8rem; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap;
}

.file-size { font-size: 0.7rem; color: var(--text-alt); }

.btn-remove {
  width: 24px; height: 24px; display: flex;
  align-items: center; justify-content: center;
  border: none; border-radius: 4px;
  background: transparent; color: var(--text-alt); cursor: pointer;
  &:hover { background: #fce4ec; color: #e53935; }
}

.upload-result { margin-top: 12px; }
.result-success { color: #00b242; font-size: 0.85rem; }
.result-skip { color: #ff9800; font-size: 0.8rem; margin-top: 4px; }

.modal-footer {
  display: flex; justify-content: flex-end;
  gap: 8px; padding: 12px 20px;
  border-top: 1px solid var(--border);
}

.btn-cancel, .btn-submit {
  padding: 8px 16px; border-radius: 6px;
  font-size: 0.85rem; border: none; cursor: pointer;
}

.btn-cancel {
  background: var(--background-alt); color: var(--text);
  &:hover { background: var(--background-hover); }
}

.btn-submit {
  background: var(--color-primary); color: #fff;
  &:hover { opacity: 0.9; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
</style>
