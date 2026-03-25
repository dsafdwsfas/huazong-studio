"""
REST resources for COS presigned URL generation, multipart upload
management, and storage configuration.

These endpoints allow the frontend to upload/download files directly
to/from Tencent COS without proxying through the backend.  They are
only active when ``FS_BACKEND=cos``.
"""

import logging
import os
import tempfile
import threading

from flask import abort, current_app, request
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from zou.app import config, db
from zou.app.stores import file_store
from zou.app.utils.thumbnail_pro import create_thumbnail, detect_format

logger = logging.getLogger(__name__)

VALID_BUCKET_TYPES = ("pictures", "movies", "files")


def _require_cos():
    """Abort 400 if COS backend is not active."""
    if not file_store.is_cos():
        abort(
            400,
            description="COS backend is not enabled. "
            "Set FS_BACKEND=cos to use this endpoint.",
        )


def _get_bucket(bucket_type):
    """Return the COSStorage instance for the given bucket type."""
    if bucket_type == "pictures":
        return file_store.pictures
    elif bucket_type == "movies":
        return file_store.movies
    elif bucket_type == "files":
        return file_store.files
    else:
        abort(400, description=f"Invalid bucket_type: {bucket_type}")


# ------------------------------------------------------------------
# Storage configuration (tells frontend which backend is active)
# ------------------------------------------------------------------


class StorageConfigResource(Resource):
    """
    ``GET /api/config/storage``

    Returns the active storage backend so the frontend can decide
    whether to use COS direct upload or traditional Flask upload.
    """

    @jwt_required()
    def get(self):
        return {
            "backend": config.FS_BACKEND,
            "cos_enabled": file_store.is_cos(),
        }, 200


# ------------------------------------------------------------------
# Presigned URLs
# ------------------------------------------------------------------


class COSPresignUploadResource(Resource):
    """
    Generate a presigned PUT URL so that the client can upload directly
    to COS.

    ``GET /api/cos/presign/upload?bucket_type=pictures&key=...&content_type=...``
    """

    @jwt_required()
    def get(self):
        _require_cos()

        parser = reqparse.RequestParser()
        parser.add_argument(
            "bucket_type",
            type=str,
            required=True,
            choices=VALID_BUCKET_TYPES,
            help="Must be one of: pictures, movies, files",
        )
        parser.add_argument("key", type=str, required=True)
        parser.add_argument("content_type", type=str, default="")
        args = parser.parse_args()

        bucket = _get_bucket(args["bucket_type"])
        expired = config.COS_PRESIGN_EXPIRED

        url = bucket.get_presigned_url(
            key=args["key"],
            method="PUT",
            expired=expired,
        )

        return {"url": url, "key": args["key"]}, 200


class COSPresignDownloadResource(Resource):
    """
    Generate a presigned GET URL for downloading a file from COS.

    ``GET /api/cos/presign/download/<bucket_type>/<key>``

    If ``COS_CDN_DOMAIN`` is configured, returns a CDN URL instead.
    """

    @jwt_required()
    def get(self, bucket_type, key):
        _require_cos()

        if bucket_type not in VALID_BUCKET_TYPES:
            abort(400, description=f"Invalid bucket_type: {bucket_type}")

        # If a CDN domain is configured, return a CDN URL directly
        if config.COS_CDN_DOMAIN:
            cdn_url = f"https://{config.COS_CDN_DOMAIN}/{key}"
            return {"url": cdn_url}, 200

        bucket = _get_bucket(bucket_type)
        expired = config.COS_PRESIGN_EXPIRED

        url = bucket.get_presigned_url(
            key=key,
            method="GET",
            expired=expired,
        )

        return {"url": url}, 200


# ------------------------------------------------------------------
# Multipart upload management
# ------------------------------------------------------------------


class COSMultipartInitResource(Resource):
    """
    ``POST /api/cos/multipart/init``

    Initialize a COS multipart upload and return the upload_id plus
    presigned URLs for each part.
    """

    @jwt_required()
    def post(self):
        _require_cos()

        data = request.get_json(force=True)
        bucket_type = data.get("bucket_type")
        key = data.get("key")
        content_type = data.get("content_type", "application/octet-stream")
        part_count = data.get("part_count", 1)

        if bucket_type not in VALID_BUCKET_TYPES or not key:
            abort(400, description="bucket_type and key are required")

        bucket = _get_bucket(bucket_type)
        client = bucket.backend.client
        bucket_name = bucket.backend.bucket_name

        # Initiate multipart upload
        response = client.create_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            ContentType=content_type,
        )
        upload_id = response["UploadId"]

        # Generate presigned URLs for each part
        part_urls = []
        for i in range(1, part_count + 1):
            url = client.get_presigned_url(
                Method="PUT",
                Bucket=bucket_name,
                Key=key,
                Expired=config.COS_PRESIGN_EXPIRED,
                Params={"uploadId": upload_id, "partNumber": str(i)},
            )
            part_urls.append({"part_number": i, "url": url})

        return {
            "upload_id": upload_id,
            "key": key,
            "part_urls": part_urls,
        }, 200


class COSMultipartCompleteResource(Resource):
    """
    ``POST /api/cos/multipart/complete``

    Complete a multipart upload by assembling the parts.
    """

    @jwt_required()
    def post(self):
        _require_cos()

        data = request.get_json(force=True)
        bucket_type = data.get("bucket_type")
        key = data.get("key")
        upload_id = data.get("upload_id")
        parts = data.get("parts", [])

        if not all([bucket_type, key, upload_id, parts]):
            abort(400, description="bucket_type, key, upload_id, parts required")

        bucket = _get_bucket(bucket_type)
        client = bucket.backend.client
        bucket_name = bucket.backend.bucket_name

        # Format parts for COS API
        multipart_upload = {
            "Part": [
                {
                    "PartNumber": p["part_number"],
                    "ETag": p["etag"],
                }
                for p in parts
            ]
        }

        response = client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            UploadId=upload_id,
            MultipartUpload=multipart_upload,
        )

        return {
            "key": key,
            "etag": response.get("ETag", ""),
        }, 200


class COSMultipartAbortResource(Resource):
    """
    ``POST /api/cos/multipart/abort``

    Abort a multipart upload and clean up uploaded parts.
    """

    @jwt_required()
    def post(self):
        _require_cos()

        data = request.get_json(force=True)
        bucket_type = data.get("bucket_type")
        key = data.get("key")
        upload_id = data.get("upload_id")

        if not all([bucket_type, key, upload_id]):
            abort(400, description="bucket_type, key, upload_id required")

        bucket = _get_bucket(bucket_type)
        client = bucket.backend.client
        bucket_name = bucket.backend.bucket_name

        client.abort_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            UploadId=upload_id,
        )

        return {"status": "aborted"}, 200


# ------------------------------------------------------------------
# Upload completion notification
# ------------------------------------------------------------------


class COSUploadCompleteResource(Resource):
    """
    ``POST /api/cos/upload-complete``

    Notify backend that a direct-to-COS upload has finished so it can
    update metadata in the database (file size, content type, etc.).
    """

    @jwt_required()
    def post(self):
        _require_cos()

        data = request.get_json(force=True)
        bucket_type = data.get("bucket_type")
        key = data.get("key")
        preview_id = data.get("preview_id")
        size = data.get("size")
        content_type = data.get("content_type", "application/octet-stream")
        original_name = data.get("original_name", "")

        if not all([bucket_type, key]):
            abort(400, description="bucket_type and key required")

        logger.info(
            "COS upload complete: bucket=%s key=%s preview=%s size=%s",
            bucket_type,
            key,
            preview_id,
            size,
        )

        # 更新 PreviewFile 数据库记录
        thumbnail_generating = False
        if preview_id:
            try:
                from zou.app.models.preview_file import PreviewFile

                preview_file = PreviewFile.get(preview_id)
                if preview_file:
                    ext = ""
                    if original_name and "." in original_name:
                        ext = original_name.rsplit(".", 1)[-1].lower()
                    update_data = {
                        "file_size": size or 0,
                        "status": "ready",
                    }
                    if ext:
                        update_data["extension"] = ext
                    if original_name:
                        update_data["original_name"] = original_name
                    preview_file.update(update_data)
                    db.session.commit()
                    logger.info(
                        "PreviewFile %s updated: size=%s ext=%s",
                        preview_id,
                        size,
                        ext,
                    )

                    # 异步生成缩略图（如果是专业格式）
                    if original_name and detect_format(original_name):
                        thumbnail_generating = True
                        app = current_app._get_current_object()
                        thread = threading.Thread(
                            target=_generate_thumbnail_async,
                            args=(app, preview_id, bucket_type, key,
                                  content_type, original_name),
                            daemon=True,
                        )
                        thread.start()
            except Exception as e:
                logger.error(
                    "Failed to update PreviewFile %s: %s",
                    preview_id,
                    e,
                )

        return {
            "status": "ok",
            "key": key,
            "bucket_type": bucket_type,
            "thumbnail_generating": thumbnail_generating,
        }, 200


def _generate_thumbnail_async(app, preview_id, bucket_type, key,
                               content_type, original_name):
    """
    在后台线程中生成缩略图：
    1. 从 COS 下载原文件到临时目录
    2. 调用 thumbnail_pro.create_thumbnail() 生成缩略图
    3. 上传缩略图回 COS
    4. 更新 PreviewFile 记录
    """
    with app.app_context():
        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp(prefix="huazong_thumb_")
            ext = ""
            if original_name and "." in original_name:
                ext = "." + original_name.rsplit(".", 1)[-1].lower()

            src_path = os.path.join(tmp_dir, f"source{ext}")
            thumb_path = os.path.join(tmp_dir, "thumbnail.png")

            # 1. 从 COS 下载原文件
            bucket = _get_bucket(bucket_type)
            if hasattr(bucket, "download_file"):
                bucket.download_file(key, src_path)
            else:
                logger.warning("COS bucket 不支持 download_file，跳过缩略图生成")
                return

            # 2. 生成缩略图
            result = create_thumbnail(src_path, thumb_path, size=(300, 200))
            if not result or not os.path.exists(thumb_path):
                logger.info("缩略图生成跳过/失败: %s", original_name)
                return

            # 3. 上传缩略图到 COS
            thumb_key = f"previews/{preview_id}/thumbnail.png"
            if hasattr(bucket, "upload_file"):
                bucket.upload_file(thumb_path, thumb_key,
                                   content_type="image/png")
                logger.info("缩略图已上传到 COS: %s", thumb_key)

            # 4. 更新数据库（存储缩略图 key 到 data 字段）
            from zou.app.models.preview_file import PreviewFile

            preview_file = PreviewFile.get(preview_id)
            if preview_file:
                data = preview_file.data or {}
                data["thumbnail_cos_key"] = thumb_key
                preview_file.update({"data": data})
                db.session.commit()

        except Exception as e:
            logger.error(
                "异步缩略图生成失败 (preview=%s): %s",
                preview_id,
                e,
                exc_info=True,
            )
        finally:
            # 清理临时目录
            if tmp_dir and os.path.exists(tmp_dir):
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
