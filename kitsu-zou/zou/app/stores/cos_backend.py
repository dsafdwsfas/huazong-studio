"""
COS (Tencent Cloud Object Storage) backend for Kitsu-Zou file storage.

Provides COSBackend (low-level SDK wrapper) and COSStorage (drop-in
replacement for flask_fs.Storage) so that file_store.py can switch
transparently between local and COS storage via FS_BACKEND config.
"""

import logging

from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError, CosClientError

logger = logging.getLogger(__name__)


class COSBackend:
    """Low-level wrapper around cos-python-sdk-v5."""

    def __init__(self, bucket_name, region, secret_id, secret_key):
        self.bucket_name = bucket_name
        self.region = region
        cos_config = CosConfig(
            Region=region,
            SecretId=secret_id,
            SecretKey=secret_key,
            Scheme="https",
        )
        self.client = CosS3Client(cos_config)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(self, key, file_obj):
        """Upload *file_obj* (binary file-like) under *key*. Returns key."""
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Body=file_obj,
                Key=key,
            )
            return key
        except (CosServiceError, CosClientError):
            logger.exception("COS write failed for key=%s", key)
            raise

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self, key):
        """Download object into memory and return bytes."""
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return response["Body"].get_raw_stream().read()
        except CosServiceError as exc:
            if exc.get_error_code() == "NoSuchKey":
                from flask_fs.errors import FileNotFound

                raise FileNotFound(key) from exc
            raise
        except CosClientError:
            logger.exception("COS read failed for key=%s", key)
            raise

    def read_chunks(self, key, chunk_size=8192):
        """Generator that yields *chunk_size* byte chunks."""
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            stream = response["Body"].get_raw_stream()
            try:
                while True:
                    chunk = stream.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            finally:
                stream.close()
        except CosServiceError as exc:
            if exc.get_error_code() == "NoSuchKey":
                from flask_fs.errors import FileNotFound

                raise FileNotFound(key) from exc
            raise

    def download_to_file(self, key, local_path):
        """Stream object directly to a local file (efficient for large files)."""
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            response["Body"].get_stream_to_file(local_path)
        except CosServiceError as exc:
            if exc.get_error_code() == "NoSuchKey":
                from flask_fs.errors import FileNotFound

                raise FileNotFound(key) from exc
            raise

    # ------------------------------------------------------------------
    # Existence / metadata
    # ------------------------------------------------------------------

    def exists(self, key):
        """Return True if *key* exists in the bucket."""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except CosServiceError:
            return False

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, key):
        """Delete object. Silently succeeds if key does not exist."""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )
        except CosServiceError:
            logger.exception("COS delete failed for key=%s", key)
            raise

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def copy(self, source_key, dest_key):
        """Server-side copy within the same bucket."""
        try:
            copy_source = {
                "Bucket": self.bucket_name,
                "Key": source_key,
                "Region": self.region,
            }
            self.client.copy_object(
                Bucket=self.bucket_name,
                Key=dest_key,
                CopySource=copy_source,
            )
            return dest_key
        except (CosServiceError, CosClientError):
            logger.exception(
                "COS copy failed %s -> %s", source_key, dest_key
            )
            raise

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_files(self, prefix=""):
        """Return a list of object keys matching *prefix*."""
        keys = []
        marker = ""
        while True:
            try:
                response = self.client.list_objects(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    Marker=marker,
                    MaxKeys=1000,
                )
            except (CosServiceError, CosClientError):
                logger.exception("COS list_files failed prefix=%s", prefix)
                raise

            contents = response.get("Contents", [])
            for obj in contents:
                keys.append(obj["Key"])

            if response.get("IsTruncated") == "true":
                marker = response.get("NextMarker", "")
            else:
                break
        return keys

    # ------------------------------------------------------------------
    # Presigned URLs
    # ------------------------------------------------------------------

    def get_presigned_url(self, key, method="GET", expired=3600):
        """Generate a presigned URL for GET or PUT."""
        try:
            url = self.client.get_presigned_url(
                Method=method,
                Bucket=self.bucket_name,
                Key=key,
                Expired=expired,
            )
            return url
        except (CosServiceError, CosClientError):
            logger.exception("COS presign failed key=%s method=%s", key, method)
            raise


class COSStorage:
    """
    Drop-in replacement for ``flask_fs.Storage`` backed by Tencent COS.

    Exposes the same public API surface consumed by ``file_store.py``:
    ``write``, ``read``, ``read_chunks``, ``exists``, ``delete``,
    ``copy``, ``list_files``.
    """

    def __init__(self, bucket_name, cos_config):
        """
        Parameters
        ----------
        bucket_name : str
            Full COS bucket name (e.g. ``"pictures-1250000000"``).
        cos_config : dict
            Must contain ``region``, ``secret_id``, ``secret_key``.
        """
        self.name = bucket_name
        self.backend = COSBackend(
            bucket_name=bucket_name,
            region=cos_config["region"],
            secret_id=cos_config["secret_id"],
            secret_key=cos_config["secret_key"],
        )

    # Delegate everything to the backend ---------------------------------

    def write(self, key, file_obj):
        return self.backend.write(key, file_obj)

    def read(self, key):
        return self.backend.read(key)

    def read_chunks(self, key, chunk_size=8192):
        return self.backend.read_chunks(key, chunk_size)

    def exists(self, key):
        return self.backend.exists(key)

    def delete(self, key):
        return self.backend.delete(key)

    def copy(self, source_key, dest_key):
        return self.backend.copy(source_key, dest_key)

    def list_files(self, prefix=""):
        return self.backend.list_files(prefix)

    def get_presigned_url(self, key, method="GET", expired=3600):
        return self.backend.get_presigned_url(key, method, expired)

    def download_to_file(self, key, local_path):
        return self.backend.download_to_file(key, local_path)
