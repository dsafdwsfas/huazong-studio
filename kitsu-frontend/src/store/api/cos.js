import client from '@/store/api/client'

export default {
  /**
   * Get storage configuration from backend.
   * Returns { backend: 'cos' | 'local', cos_enabled: boolean }
   */
  getStorageConfig() {
    return client.pget('/api/config/storage')
  },

  /**
   * Get presigned URL for uploading a file to COS.
   * @param {string} bucketType - 'pictures' | 'movies' | 'files'
   * @param {string} key - Object storage key
   * @param {string} contentType - MIME type of the file
   * @returns {Promise<{url: string, key: string}>}
   */
  getUploadUrl(bucketType, key, contentType) {
    return client.pget(
      `/api/cos/presign/upload?bucket_type=${bucketType}&key=${encodeURIComponent(key)}&content_type=${encodeURIComponent(contentType)}`
    )
  },

  /**
   * Get presigned URL for downloading/viewing a file from COS.
   * @param {string} bucketType - 'pictures' | 'movies' | 'files'
   * @param {string} key - Object storage key
   * @returns {Promise<{url: string}>}
   */
  getDownloadUrl(bucketType, key) {
    return client.pget(
      `/api/cos/presign/download/${bucketType}/${encodeURIComponent(key)}`
    )
  },

  /**
   * Initialize a multipart upload.
   * @param {string} bucketType
   * @param {string} key
   * @param {string} contentType
   * @param {number} partCount - Number of parts
   * @returns {Promise<{upload_id: string, key: string, part_urls: Array}>}
   */
  initMultipartUpload(bucketType, key, contentType, partCount) {
    return client.ppost('/api/cos/multipart/init', {
      bucket_type: bucketType,
      key,
      content_type: contentType,
      part_count: partCount
    })
  },

  /**
   * Complete a multipart upload.
   * @param {string} bucketType
   * @param {string} key
   * @param {string} uploadId - COS multipart upload ID
   * @param {Array<{part_number: number, etag: string}>} parts
   * @returns {Promise<{key: string, etag: string}>}
   */
  completeMultipartUpload(bucketType, key, uploadId, parts) {
    return client.ppost('/api/cos/multipart/complete', {
      bucket_type: bucketType,
      key,
      upload_id: uploadId,
      parts
    })
  },

  /**
   * Abort a multipart upload.
   * @param {string} bucketType
   * @param {string} key
   * @param {string} uploadId
   * @returns {Promise<{status: string}>}
   */
  abortMultipartUpload(bucketType, key, uploadId) {
    return client.ppost('/api/cos/multipart/abort', {
      bucket_type: bucketType,
      key,
      upload_id: uploadId
    })
  },

  /**
   * Notify backend that an upload is complete so it can update metadata.
   * @param {string} bucketType
   * @param {string} key
   * @param {Object} metadata - { preview_id, size, content_type, original_name }
   * @returns {Promise<{status: string, key: string, bucket_type: string}>}
   */
  notifyUploadComplete(bucketType, key, metadata) {
    return client.ppost('/api/cos/upload-complete', {
      bucket_type: bucketType,
      key,
      ...metadata
    })
  }
}
