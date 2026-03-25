/**
 * 中央上传队列管理器
 *
 * 功能：
 * 1. 文件排队 — 添加文件到队列，自动开始上传
 * 2. 并发控制 — 最多 N 个文件同时上传（默认 3）
 * 3. 优先级 — 小文件优先（≤5MB 优先于大文件）
 * 4. 进度追踪 — 每个文件和总体进度
 * 5. 暂停/恢复/取消 — 单个和全部
 * 6. 事件回调 — onFileProgress, onFileComplete, onFileError, onQueueEmpty
 * 7. 重试 — 失败自动重试一次
 */

import {
  isCosEnabled,
  uploadPreviewToCOS
} from '@/lib/cos-upload-integration'

const SMALL_FILE_THRESHOLD = 5 * 1024 * 1024 // 5MB

let _idCounter = 0
function generateId() {
  return `upload-${Date.now()}-${++_idCounter}`
}

/**
 * @typedef {Object} QueueItem
 * @property {string} id
 * @property {File} file
 * @property {string} fileName
 * @property {number} fileSize
 * @property {'pending'|'uploading'|'paused'|'complete'|'error'|'cancelled'} status
 * @property {number} percent
 * @property {number} loaded
 * @property {number} speed
 * @property {number} eta
 * @property {string|null} error
 * @property {number} retries
 * @property {string} previewId
 * @property {string} taskId
 * @property {string} type
 * @property {object|null} uploader
 * @property {number} createdAt
 */

export class UploadQueueManager {
  /**
   * @param {Object} options
   * @param {number} [options.maxConcurrent=3]
   * @param {Function} [options.onFileProgress]
   * @param {Function} [options.onFileComplete]
   * @param {Function} [options.onFileError]
   * @param {Function} [options.onQueueProgress]
   * @param {Function} [options.onQueueEmpty]
   */
  constructor(options = {}) {
    this.maxConcurrent = options.maxConcurrent || 3
    this.onFileProgress = options.onFileProgress || (() => {})
    this.onFileComplete = options.onFileComplete || (() => {})
    this.onFileError = options.onFileError || (() => {})
    this.onQueueProgress = options.onQueueProgress || (() => {})
    this.onQueueEmpty = options.onQueueEmpty || (() => {})

    /** @type {QueueItem[]} */
    this._items = []
    this._cosEnabled = null
  }

  /**
   * 添加文件到上传队列
   * @param {File[]} files
   * @param {Object} meta
   * @param {string} [meta.previewId]
   * @param {string} [meta.taskId]
   * @param {string} [meta.type='preview']
   * @returns {QueueItem[]} 新创建的队列项
   */
  addFiles(files, meta = {}) {
    const newItems = []
    for (const file of files) {
      const item = {
        id: generateId(),
        file,
        fileName: file.name,
        fileSize: file.size,
        status: 'pending',
        percent: 0,
        loaded: 0,
        speed: 0,
        eta: 0,
        error: null,
        retries: 0,
        previewId: meta.previewId || '',
        taskId: meta.taskId || '',
        type: meta.type || 'preview',
        uploader: null,
        createdAt: Date.now()
      }
      this._items.push(item)
      newItems.push(item)
    }

    // 按优先级排序 pending 项（小文件优先）
    this._sortPending()
    this._processQueue()
    this._emitQueueProgress()

    return newItems
  }

  /**
   * 暂停单个上传
   */
  pause(itemId) {
    const item = this._findItem(itemId)
    if (!item || item.status !== 'uploading') return
    if (item.uploader?.pause) {
      item.uploader.pause()
    }
    item.status = 'paused'
    this.onFileProgress({ ...item })
    this._emitQueueProgress()
  }

  /**
   * 恢复单个上传
   */
  resume(itemId) {
    const item = this._findItem(itemId)
    if (!item || item.status !== 'paused') return
    if (item.uploader?.resume) {
      item.uploader.resume()
    }
    item.status = 'uploading'
    this.onFileProgress({ ...item })
    this._emitQueueProgress()
  }

  /**
   * 取消单个上传
   */
  cancel(itemId) {
    const item = this._findItem(itemId)
    if (!item) return
    if (item.uploader?.cancel) {
      item.uploader.cancel()
    }
    item.status = 'cancelled'
    item.uploader = null
    this.onFileProgress({ ...item })
    this._processQueue()
    this._emitQueueProgress()
  }

  /**
   * 重试失败项
   */
  retry(itemId) {
    const item = this._findItem(itemId)
    if (!item || item.status !== 'error') return
    item.status = 'pending'
    item.percent = 0
    item.loaded = 0
    item.error = null
    item.uploader = null
    this._processQueue()
    this._emitQueueProgress()
  }

  pauseAll() {
    for (const item of this._items) {
      if (item.status === 'uploading') {
        this.pause(item.id)
      }
    }
  }

  resumeAll() {
    for (const item of this._items) {
      if (item.status === 'paused') {
        this.resume(item.id)
      }
    }
  }

  cancelAll() {
    for (const item of this._items) {
      if (item.status === 'uploading' || item.status === 'paused' || item.status === 'pending') {
        this.cancel(item.id)
      }
    }
  }

  /**
   * 获取所有队列项的快照
   */
  getItems() {
    return this._items.map(item => ({ ...item, uploader: undefined }))
  }

  /**
   * 获取队列统计
   */
  getStats() {
    const total = this._items.length
    const completed = this._items.filter(i => i.status === 'complete').length
    const failed = this._items.filter(i => i.status === 'error').length
    const active = this._items.filter(i => i.status === 'uploading').length
    const pending = this._items.filter(i => i.status === 'pending').length
    const totalBytes = this._items.reduce((s, i) => s + i.fileSize, 0)
    const loadedBytes = this._items.reduce((s, i) => s + i.loaded, 0)
    const percent = totalBytes > 0 ? (loadedBytes / totalBytes) * 100 : 0
    const speed = this._items
      .filter(i => i.status === 'uploading')
      .reduce((s, i) => s + i.speed, 0)

    return { total, completed, failed, active, pending, percent, speed }
  }

  get isActive() {
    return this._items.some(
      i => i.status === 'uploading' || i.status === 'pending'
    )
  }

  /**
   * 清除已完成和已取消的项
   */
  clearCompleted() {
    this._items = this._items.filter(
      i => i.status !== 'complete' && i.status !== 'cancelled'
    )
    this._emitQueueProgress()
  }

  // ---- 内部方法 ----

  _findItem(id) {
    return this._items.find(i => i.id === id)
  }

  _sortPending() {
    // 稳定排序：pending 项按文件大小升序（小文件优先）
    const pending = this._items.filter(i => i.status === 'pending')
    const rest = this._items.filter(i => i.status !== 'pending')
    pending.sort((a, b) => a.fileSize - b.fileSize)
    this._items = [...rest, ...pending]
  }

  _getActiveCount() {
    return this._items.filter(i => i.status === 'uploading').length
  }

  async _processQueue() {
    const slots = this.maxConcurrent - this._getActiveCount()
    if (slots <= 0) return

    const pendingItems = this._items.filter(i => i.status === 'pending')
    const toStart = pendingItems.slice(0, slots)

    for (const item of toStart) {
      item.status = 'uploading'
      this._startUpload(item)
    }
  }

  async _startUpload(item) {
    try {
      if (this._cosEnabled === null) {
        this._cosEnabled = await isCosEnabled()
      }

      if (this._cosEnabled && item.previewId) {
        await this._uploadWithCOS(item)
      } else {
        // 非 COS 模式或无 previewId：直接标记完成
        // （实际场景由 Vuex store 层处理非 COS 上传）
        await this._uploadFallback(item)
      }
    } catch (err) {
      this._handleError(item, err)
    }
  }

  async _uploadWithCOS(item) {
    const formData = new FormData()
    formData.append('file', item.file, item.fileName)

    const { uploader, promise } = uploadPreviewToCOS(
      item.previewId,
      formData,
      {
        onProgress: (progress) => {
          item.percent = progress.percent
          item.loaded = progress.loaded || 0
          item.speed = progress.speed || 0
          item.eta = progress.eta || 0
          this.onFileProgress({ ...item, uploader: undefined })
          this._emitQueueProgress()
        },
        onError: (err) => {
          this._handleError(item, err)
        }
      }
    )

    item.uploader = uploader

    await promise
    item.status = 'complete'
    item.percent = 100
    item.loaded = item.fileSize
    item.speed = 0
    item.eta = 0
    item.uploader = null
    this.onFileComplete({ ...item, uploader: undefined })
    this._processQueue()
    this._emitQueueProgress()
    this._checkQueueEmpty()
  }

  async _uploadFallback(item) {
    // 模拟完成 — 实际由外部 Vuex store 处理
    item.status = 'complete'
    item.percent = 100
    item.loaded = item.fileSize
    item.uploader = null
    this.onFileComplete({ ...item, uploader: undefined })
    this._processQueue()
    this._emitQueueProgress()
    this._checkQueueEmpty()
  }

  _handleError(item, err) {
    // 自动重试一次
    if (item.retries < 1) {
      item.retries++
      item.status = 'pending'
      item.percent = 0
      item.loaded = 0
      item.uploader = null
      console.warn(`上传失败，自动重试 (${item.retries}/1):`, item.fileName, err)
      this._processQueue()
      return
    }

    item.status = 'error'
    item.error = err?.message || '上传失败'
    item.uploader = null
    this.onFileError({ ...item, uploader: undefined }, err)
    this._processQueue()
    this._emitQueueProgress()
    this._checkQueueEmpty()
  }

  _emitQueueProgress() {
    this.onQueueProgress(this.getStats())
  }

  _checkQueueEmpty() {
    if (!this.isActive) {
      this.onQueueEmpty()
    }
  }
}

export default UploadQueueManager
