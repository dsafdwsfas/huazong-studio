/**
 * COS Chunked Upload with Resume capability
 *
 * Features:
 * - Splits files into chunks (default 5MB, configurable)
 * - Uploads each chunk via presigned URL from backend
 * - Tracks progress with callback
 * - Supports pause/resume via localStorage checkpoint
 * - Concurrent chunk uploads (default 3 parallel)
 * - Retry failed chunks (3 attempts with exponential backoff)
 * - Auto-detect: small files use direct upload, large files use chunked
 */

const CHECKPOINT_PREFIX = 'cos_upload_checkpoint_'
const DIRECT_UPLOAD_THRESHOLD = 20 * 1024 * 1024 // 20MB

/**
 * Generate a unique upload ID for checkpoint tracking
 */
function generateUploadId(file, key) {
  return `${file.name}_${file.size}_${file.lastModified}_${key}`
}

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i]
}

/**
 * Format seconds to human-readable duration
 */
export function formatDuration(seconds) {
  if (!seconds || seconds === Infinity) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  if (mins > 60) {
    const hours = Math.floor(mins / 60)
    const remainMins = mins % 60
    return `${hours}h ${remainMins}m`
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export class COSUploader {
  /**
   * @param {Object} options
   * @param {number} options.chunkSize - Chunk size in bytes (default 5MB)
   * @param {number} options.concurrency - Max parallel chunk uploads (default 3)
   * @param {number} options.maxRetries - Max retry attempts per chunk (default 3)
   * @param {Function} options.onProgress - Progress callback ({percent, loaded, total, speed, eta, fileName})
   * @param {Function} options.onComplete - Completion callback ({key, bucketType, size})
   * @param {Function} options.onError - Error callback (error)
   * @param {Function} options.onPause - Pause callback ()
   * @param {Function} options.onResume - Resume callback ({resumedChunks, totalChunks})
   */
  constructor(options = {}) {
    this.chunkSize = options.chunkSize || 5 * 1024 * 1024
    this.concurrency = options.concurrency || 3
    this.maxRetries = options.maxRetries || 3
    this.onProgress = options.onProgress || (() => {})
    this.onComplete = options.onComplete || (() => {})
    this.onError = options.onError || (() => {})
    this.onPause = options.onPause || (() => {})
    this.onResume = options.onResume || (() => {})

    this._paused = false
    this._cancelled = false
    this._activeRequests = []
    this._uploadId = null
    this._startTime = null
    this._loadedBytes = 0
    this._totalBytes = 0
  }

  /**
   * Get presigned upload URL from backend
   * @param {string} bucketType - 'previews' | 'originals' | 'thumbnails'
   * @param {string} key - Object storage key
   * @param {string} contentType - MIME type
   * @param {number} [partNumber] - Part number for multipart upload
   * @param {string} [uploadIdCOS] - COS multipart upload ID
   * @returns {Promise<{url: string, uploadId?: string}>}
   */
  async getPresignedUrl(bucketType, key, contentType, partNumber, uploadIdCOS) {
    const params = new URLSearchParams({
      bucket_type: bucketType,
      key,
      content_type: contentType
    })
    if (partNumber !== undefined) {
      params.set('part_number', partNumber)
    }
    if (uploadIdCOS) {
      params.set('upload_id', uploadIdCOS)
    }

    const response = await fetch(`/api/storage/cos/presigned-url?${params}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      throw new Error(`Failed to get presigned URL: ${response.status}`)
    }
    return response.json()
  }

  /**
   * Initialize a multipart upload on the backend
   * @param {string} bucketType
   * @param {string} key
   * @param {string} contentType
   * @returns {Promise<{uploadId: string}>}
   */
  async initMultipartUpload(bucketType, key, contentType) {
    const response = await fetch('/api/storage/cos/multipart/init', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bucket_type: bucketType,
        key,
        content_type: contentType
      })
    })
    if (!response.ok) {
      throw new Error(`Failed to init multipart upload: ${response.status}`)
    }
    return response.json()
  }

  /**
   * Complete a multipart upload on the backend
   * @param {string} bucketType
   * @param {string} key
   * @param {string} uploadIdCOS - COS multipart upload ID
   * @param {Array<{partNumber: number, etag: string}>} parts
   * @returns {Promise<Object>}
   */
  async completeMultipartUpload(bucketType, key, uploadIdCOS, parts) {
    const response = await fetch('/api/storage/cos/multipart/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bucket_type: bucketType,
        key,
        upload_id: uploadIdCOS,
        parts
      })
    })
    if (!response.ok) {
      throw new Error(`Failed to complete multipart upload: ${response.status}`)
    }
    return response.json()
  }

  /**
   * Abort a multipart upload on the backend
   * @param {string} bucketType
   * @param {string} key
   * @param {string} uploadIdCOS
   */
  async abortMultipartUpload(bucketType, key, uploadIdCOS) {
    try {
      await fetch('/api/storage/cos/multipart/abort', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bucket_type: bucketType,
          key,
          upload_id: uploadIdCOS
        })
      })
    } catch (err) {
      // Best effort abort, don't throw
      console.warn('Failed to abort multipart upload:', err)
    }
  }

  /**
   * Upload single file (auto-detect: direct vs chunked based on size)
   * @param {File} file - File object
   * @param {string} bucketType - 'previews' | 'originals' | 'thumbnails'
   * @param {string} key - Object storage key
   * @returns {Promise<Object>}
   */
  async upload(file, bucketType, key) {
    this._paused = false
    this._cancelled = false
    this._activeRequests = []
    this._startTime = Date.now()
    this._loadedBytes = 0
    this._totalBytes = file.size
    this._uploadId = generateUploadId(file, key)

    try {
      let result
      if (file.size <= DIRECT_UPLOAD_THRESHOLD) {
        result = await this.directUpload(file, bucketType, key)
      } else {
        result = await this.chunkedUpload(file, bucketType, key)
      }

      this.clearCheckpoint(this._uploadId)
      this.onComplete({ key, bucketType, size: file.size })
      return result
    } catch (err) {
      if (this._cancelled) {
        return null
      }
      this.onError(err)
      throw err
    }
  }

  /**
   * Small file: direct PUT to presigned URL
   * @param {File} file
   * @param {string} bucketType
   * @param {string} key
   * @returns {Promise<Object>}
   */
  async directUpload(file, bucketType, key) {
    const { url } = await this.getPresignedUrl(
      bucketType,
      key,
      file.type || 'application/octet-stream'
    )

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      this._activeRequests = [xhr]

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          this._loadedBytes = e.loaded
          this._emitProgress(file.name)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve({ key, etag: xhr.getResponseHeader('ETag') })
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`))
        }
      })

      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'))
      })

      xhr.addEventListener('abort', () => {
        if (this._cancelled) {
          reject(new Error('Upload cancelled'))
        }
      })

      xhr.open('PUT', url)
      xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream')
      xhr.send(file)
    })
  }

  /**
   * Large file: multipart upload via chunked presigned URLs
   * @param {File} file
   * @param {string} bucketType
   * @param {string} key
   * @returns {Promise<Object>}
   */
  async chunkedUpload(file, bucketType, key) {
    const totalChunks = Math.ceil(file.size / this.chunkSize)
    const contentType = file.type || 'application/octet-stream'

    // Check for existing checkpoint (resume support)
    const checkpoint = this.loadCheckpoint(this._uploadId)
    let uploadIdCOS
    let completedParts = []
    let startChunkIndex = 0

    if (checkpoint && checkpoint.uploadIdCOS) {
      uploadIdCOS = checkpoint.uploadIdCOS
      completedParts = checkpoint.completedParts || []
      startChunkIndex = completedParts.length
      this._loadedBytes = startChunkIndex * this.chunkSize
      this.onResume({
        resumedChunks: startChunkIndex,
        totalChunks
      })
    } else {
      // Initialize multipart upload
      const initResult = await this.initMultipartUpload(
        bucketType,
        key,
        contentType
      )
      uploadIdCOS = initResult.upload_id
    }

    // Save initial checkpoint
    this.saveCheckpoint(this._uploadId, {
      uploadIdCOS,
      bucketType,
      key,
      contentType,
      totalChunks,
      completedParts,
      fileName: file.name,
      fileSize: file.size
    })

    // Build chunk list (skip completed ones)
    const pendingChunks = []
    for (let i = startChunkIndex; i < totalChunks; i++) {
      pendingChunks.push(i)
    }

    // Upload chunks with concurrency control
    const uploadChunk = async (chunkIndex) => {
      if (this._cancelled) throw new Error('Upload cancelled')

      // Wait if paused
      while (this._paused) {
        await new Promise(resolve => setTimeout(resolve, 200))
        if (this._cancelled) throw new Error('Upload cancelled')
      }

      const start = chunkIndex * this.chunkSize
      const end = Math.min(start + this.chunkSize, file.size)
      const chunk = file.slice(start, end)
      const partNumber = chunkIndex + 1 // COS parts are 1-indexed

      // Get presigned URL for this part
      const { url } = await this.getPresignedUrl(
        bucketType,
        key,
        contentType,
        partNumber,
        uploadIdCOS
      )

      // Upload chunk with retry
      const etag = await this._uploadChunkWithRetry(
        chunk,
        url,
        contentType,
        partNumber,
        file.name
      )

      // Record completion
      const part = { partNumber, etag }
      completedParts.push(part)

      // Update checkpoint
      this.saveCheckpoint(this._uploadId, {
        uploadIdCOS,
        bucketType,
        key,
        contentType,
        totalChunks,
        completedParts,
        fileName: file.name,
        fileSize: file.size
      })

      return part
    }

    // Process chunks with concurrency pool
    await this._processPool(pendingChunks, uploadChunk, this.concurrency)

    if (this._cancelled) return null

    // Complete multipart upload
    completedParts.sort((a, b) => a.partNumber - b.partNumber)
    const result = await this.completeMultipartUpload(
      bucketType,
      key,
      uploadIdCOS,
      completedParts
    )

    return result
  }

  /**
   * Upload a single chunk with retry logic
   * @private
   */
  async _uploadChunkWithRetry(chunk, url, contentType, partNumber, fileName) {
    let lastError
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        return await this._uploadChunkXHR(chunk, url, contentType, partNumber, fileName)
      } catch (err) {
        lastError = err
        if (this._cancelled) throw err
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, attempt) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    throw lastError
  }

  /**
   * Upload a single chunk via XMLHttpRequest
   * @private
   */
  _uploadChunkXHR(chunk, url, contentType, partNumber, fileName) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      this._activeRequests.push(xhr)

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          // Calculate chunk-level progress contribution
          const chunkBase = (partNumber - 1) * this.chunkSize
          this._loadedBytes = chunkBase + e.loaded
          // Don't exceed total
          if (this._loadedBytes > this._totalBytes) {
            this._loadedBytes = this._totalBytes
          }
          this._emitProgress(fileName)
        }
      })

      xhr.addEventListener('load', () => {
        // Remove from active requests
        const idx = this._activeRequests.indexOf(xhr)
        if (idx > -1) this._activeRequests.splice(idx, 1)

        if (xhr.status >= 200 && xhr.status < 300) {
          const etag = xhr.getResponseHeader('ETag')
          resolve(etag)
        } else {
          reject(new Error(`Chunk ${partNumber} upload failed: ${xhr.status}`))
        }
      })

      xhr.addEventListener('error', () => {
        const idx = this._activeRequests.indexOf(xhr)
        if (idx > -1) this._activeRequests.splice(idx, 1)
        reject(new Error(`Network error on chunk ${partNumber}`))
      })

      xhr.addEventListener('abort', () => {
        const idx = this._activeRequests.indexOf(xhr)
        if (idx > -1) this._activeRequests.splice(idx, 1)
        if (this._cancelled) {
          reject(new Error('Upload cancelled'))
        }
      })

      xhr.open('PUT', url)
      xhr.setRequestHeader('Content-Type', contentType)
      xhr.send(chunk)
    })
  }

  /**
   * Process items with a concurrency pool
   * @private
   */
  async _processPool(items, fn, concurrency) {
    const results = []
    let index = 0

    const worker = async () => {
      while (index < items.length) {
        if (this._cancelled) return
        const currentIndex = index++
        results[currentIndex] = await fn(items[currentIndex])
      }
    }

    const workers = []
    for (let i = 0; i < Math.min(concurrency, items.length); i++) {
      workers.push(worker())
    }
    await Promise.all(workers)
    return results
  }

  /**
   * Emit progress event with speed and ETA calculations
   * @private
   */
  _emitProgress(fileName) {
    const elapsed = (Date.now() - this._startTime) / 1000
    const speed = elapsed > 0 ? this._loadedBytes / elapsed : 0
    const remaining = this._totalBytes - this._loadedBytes
    const eta = speed > 0 ? remaining / speed : Infinity
    const percent = this._totalBytes > 0
      ? Math.min(100, (this._loadedBytes / this._totalBytes) * 100)
      : 0

    this.onProgress({
      percent,
      loaded: this._loadedBytes,
      total: this._totalBytes,
      speed,
      eta,
      fileName
    })
  }

  /**
   * Save checkpoint to localStorage for resume
   * @param {string} uploadId
   * @param {Object} data
   */
  saveCheckpoint(uploadId, data) {
    try {
      localStorage.setItem(
        CHECKPOINT_PREFIX + uploadId,
        JSON.stringify({
          ...data,
          timestamp: Date.now()
        })
      )
    } catch (e) {
      // localStorage might be full or unavailable
      console.warn('Failed to save upload checkpoint:', e)
    }
  }

  /**
   * Load checkpoint from localStorage
   * @param {string} uploadId
   * @returns {Object|null}
   */
  loadCheckpoint(uploadId) {
    try {
      const raw = localStorage.getItem(CHECKPOINT_PREFIX + uploadId)
      if (!raw) return null
      const data = JSON.parse(raw)
      // Expire checkpoints older than 24 hours
      if (Date.now() - data.timestamp > 24 * 60 * 60 * 1000) {
        this.clearCheckpoint(uploadId)
        return null
      }
      return data
    } catch (e) {
      return null
    }
  }

  /**
   * Clear checkpoint after completion
   * @param {string} uploadId
   */
  clearCheckpoint(uploadId) {
    try {
      localStorage.removeItem(CHECKPOINT_PREFIX + uploadId)
    } catch (e) {
      // Ignore
    }
  }

  /**
   * Clear all stale checkpoints (older than 24h)
   */
  static clearStaleCheckpoints() {
    try {
      const keys = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key.startsWith(CHECKPOINT_PREFIX)) {
          keys.push(key)
        }
      }
      const now = Date.now()
      keys.forEach(key => {
        try {
          const data = JSON.parse(localStorage.getItem(key))
          if (now - data.timestamp > 24 * 60 * 60 * 1000) {
            localStorage.removeItem(key)
          }
        } catch (e) {
          localStorage.removeItem(key)
        }
      })
    } catch (e) {
      // Ignore
    }
  }

  /**
   * Pause the upload
   */
  pause() {
    this._paused = true
    this.onPause()
  }

  /**
   * Resume the upload
   */
  resume() {
    this._paused = false
  }

  /**
   * Cancel the upload and abort all active requests
   */
  cancel() {
    this._cancelled = true
    this._paused = false
    this._activeRequests.forEach(xhr => {
      try {
        xhr.abort()
      } catch (e) {
        // Ignore
      }
    })
    this._activeRequests = []
    if (this._uploadId) {
      this.clearCheckpoint(this._uploadId)
    }
  }

  /**
   * Check if the uploader is currently paused
   * @returns {boolean}
   */
  get isPaused() {
    return this._paused
  }

  /**
   * Check if the uploader was cancelled
   * @returns {boolean}
   */
  get isCancelled() {
    return this._cancelled
  }
}

export default COSUploader
