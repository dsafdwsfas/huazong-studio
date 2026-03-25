/**
 * COS Upload Integration for Kitsu
 *
 * Bridges COSUploader with Kitsu's Vuex store and existing upload flow.
 * Feature-flagged: only activates when backend reports COS is enabled.
 */

import { COSUploader } from '@/lib/cos-upload'
import cosApi from '@/store/api/cos'

let _cosEnabled = null
let _storageConfig = null

// Clean up stale upload checkpoints on module load
COSUploader.clearStaleCheckpoints()

/**
 * Check if COS storage is enabled (cached after first call).
 * @returns {Promise<boolean>}
 */
export async function isCosEnabled() {
  if (_cosEnabled !== null) return _cosEnabled
  try {
    _storageConfig = await cosApi.getStorageConfig()
    _cosEnabled = _storageConfig?.cos_enabled === true
  } catch (err) {
    console.warn('Failed to fetch storage config, falling back to local:', err)
    _cosEnabled = false
  }
  return _cosEnabled
}

/**
 * Reset the cached COS enabled state (for testing or config reload).
 */
export function resetCosEnabledCache() {
  _cosEnabled = null
  _storageConfig = null
}

/**
 * Generate a COS object key for a preview file.
 * @param {string} previewId
 * @param {string} fileName
 * @returns {string}
 */
export function generatePreviewKey(previewId, fileName) {
  const ext = fileName.lastIndexOf('.') > 0
    ? fileName.slice(fileName.lastIndexOf('.'))
    : ''
  return `previews/${previewId}/original${ext}`
}

/**
 * Upload a preview file to COS with progress tracking.
 * This replaces the existing superagent-based upload when COS is enabled.
 *
 * @param {string} previewId - The preview file ID from the backend
 * @param {FormData} formData - FormData containing the file (key: 'file')
 * @param {Object} callbacks
 * @param {Function} callbacks.onProgress - ({previewId, percent, name})
 * @returns {{uploader: COSUploader, promise: Promise}}
 */
export function uploadPreviewToCOS(previewId, formData, callbacks = {}) {
  const file = formData.get('file')
  if (!file) {
    throw new Error('No file found in FormData')
  }

  const key = generatePreviewKey(previewId, file.name)
  const bucketType = 'previews'

  const uploader = new COSUploader({
    onProgress: (progress) => {
      if (callbacks.onProgress) {
        callbacks.onProgress({
          previewId,
          percent: progress.percent,
          name: file.name,
          loaded: progress.loaded,
          total: progress.total,
          speed: progress.speed,
          eta: progress.eta
        })
      }
    },
    onComplete: async () => {
      // Notify backend that the upload is complete
      try {
        await cosApi.notifyUploadComplete(bucketType, key, {
          preview_id: previewId,
          size: file.size,
          content_type: file.type || 'application/octet-stream',
          original_name: file.name
        })
      } catch (err) {
        console.error('Failed to notify upload completion:', err)
      }
    },
    onError: (err) => {
      if (callbacks.onError) {
        callbacks.onError(err)
      }
    }
  })

  const promise = uploader.upload(file, bucketType, key).then(() => {
    // Return a response structure compatible with the existing flow.
    // The existing code expects the response from uploadPreview to be
    // the preview object. We return a minimal compatible object.
    return { id: previewId, cos_key: key }
  })

  return { uploader, promise }
}

/**
 * Create a COS-compatible wrapper that mimics the superagent request interface.
 * This allows the existing task store code to work with minimal changes.
 *
 * The existing code does:
 *   const { request, promise } = tasksApi.uploadPreview(preview.id, form)
 *   request.on('progress', e => { ... })
 *
 * This function returns the same shape, but backed by COSUploader.
 *
 * @param {string} previewId
 * @param {FormData} formData
 * @returns {{request: EventEmitter-like, promise: Promise}}
 */
export function createCOSUploadCompat(previewId, formData) {
  const listeners = {}

  const request = {
    on(event, handler) {
      if (!listeners[event]) listeners[event] = []
      listeners[event].push(handler)
      return request
    },
    _emit(event, data) {
      if (listeners[event]) {
        listeners[event].forEach(fn => fn(data))
      }
    },
    // Expose the uploader for pause/resume/cancel
    _uploader: null,
    abort() {
      if (this._uploader) {
        this._uploader.cancel()
      }
    }
  }

  const { uploader, promise } = uploadPreviewToCOS(previewId, formData, {
    onProgress: (progress) => {
      // Emit in the same format as superagent progress events
      request._emit('progress', {
        percent: progress.percent,
        loaded: progress.loaded,
        total: progress.total,
        // Extra fields for COS progress component
        speed: progress.speed,
        eta: progress.eta
      })
    }
  })

  request._uploader = uploader

  return { request, promise }
}

export default {
  isCosEnabled,
  resetCosEnabledCache,
  generatePreviewKey,
  uploadPreviewToCOS,
  createCOSUploadCompat
}
