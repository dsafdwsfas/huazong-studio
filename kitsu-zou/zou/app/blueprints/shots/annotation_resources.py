"""
分镜标注 API

包装现有标注系统，为分镜面板提供便捷的标注保存/加载接口。
支持图片标注和视频帧级标注。
"""

import logging
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import (
    preview_files_service,
    shots_service,
    persons_service,
)
from zou.app.utils import permissions

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "wmv", "m4v"}
AUDIO_EXTENSIONS = {"mp3", "wav"}


def _is_video_extension(extension):
    """Check if the file extension indicates a video file."""
    return (extension or "").lower() in VIDEO_EXTENSIONS


def _is_audio_extension(extension):
    """Check if the file extension indicates an audio file."""
    return (extension or "").lower() in AUDIO_EXTENSIONS


def _build_audio_info(preview_file):
    """Build audio metadata dict from a preview file."""
    extension = (preview_file.get("extension") or "").lower()
    duration = preview_file.get("duration") or 0
    return {
        "duration": duration,
        "extension": extension,
    }


def _get_audio_markers(annotations):
    """Extract audio markers from annotations list."""
    if not isinstance(annotations, list):
        return []
    return [
        ann for ann in annotations
        if isinstance(ann, dict) and "label" in ann and "time" in ann
    ]


def _build_video_info(preview_file):
    """Build video metadata dict from a preview file."""
    extension = (preview_file.get("extension") or "").lower()
    duration = preview_file.get("duration") or 0
    fps = 24  # Default fps; Kitsu normalizes videos to 24fps
    total_frames = int(duration * fps) if duration else 0
    return {
        "duration": duration,
        "fps": fps,
        "total_frames": total_frames,
        "extension": extension,
    }


def _get_annotated_frames(annotations):
    """Extract sorted list of frame numbers that have annotations."""
    frames = set()
    if not isinstance(annotations, list):
        return []
    for ann in annotations:
        if isinstance(ann, dict) and "frame" in ann:
            frames.add(ann["frame"])
    return sorted(frames)


def _get_annotations_for_frame(annotations, frame_number):
    """Filter annotations to only those matching a specific frame."""
    if not isinstance(annotations, list):
        return []
    return [
        ann for ann in annotations
        if isinstance(ann, dict) and ann.get("frame") == frame_number
    ]


def _check_shot_edit_permission(project_id):
    """Check if user has permission to edit annotations on this project."""
    if not permissions.has_manager_project_access(project_id):
        try:
            permissions.check_belong_to_project(project_id)
        except Exception:
            return False
    return True


def _get_shot_preview(shot_id):
    """Get shot and its preview file. Returns (shot, preview_file, error_response)."""
    shot = shots_service.get_shot(shot_id)
    preview_file_id = shot.get("preview_file_id")
    if not preview_file_id:
        return shot, None, None
    preview_file = preview_files_service.get_preview_file(preview_file_id)
    return shot, preview_file, None


class StoryboardAnnotationResource(Resource):
    """
    ``GET /api/data/shots/<shot_id>/annotations``
    ``PUT /api/data/shots/<shot_id>/annotations``

    获取或保存分镜的标注数据。从关联的 preview_file 中读取/写入。
    支持可选的 ``?frame=<int>`` 查询参数来过滤视频帧标注。
    """

    @jwt_required()
    def get(self, shot_id):
        """
        Get storyboard annotations
        ---
        tags:
        - Shots
        description: Read annotations from the preview file linked to this
          shot. Returns annotation objects plus storyboard-specific metadata
          (tool types used, marker counts). For video files, includes video
          metadata and annotated frame list. Use ``?frame=53`` to filter
          annotations for a specific frame.
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
          - in: query
            name: frame
            required: False
            type: integer
            description: Filter annotations to a specific video frame number.
        responses:
          200:
            description: Annotation data with metadata
        """
        shot = shots_service.get_shot(shot_id)

        preview_file_id = shot.get("preview_file_id")
        if not preview_file_id:
            return {
                "shot_id": shot_id,
                "preview_file_id": None,
                "is_video": False,
                "is_audio": False,
                "annotations": [],
                "metadata": {},
            }, 200

        preview_file = preview_files_service.get_preview_file(preview_file_id)
        annotations = preview_file.get("annotations") or []
        extension = (preview_file.get("extension") or "").lower()
        is_video = _is_video_extension(extension)
        is_audio = _is_audio_extension(extension)

        # Filter by frame if requested
        frame_param = request.args.get("frame")
        if frame_param is not None:
            try:
                frame_number = int(frame_param)
            except (ValueError, TypeError):
                return {"error": "frame 参数必须为整数"}, 400
            annotations = _get_annotations_for_frame(annotations, frame_number)

        metadata = _extract_annotation_metadata(annotations)
        metadata["updated_at"] = str(preview_file.get("updated_at", ""))

        result = {
            "shot_id": shot_id,
            "preview_file_id": preview_file_id,
            "is_video": is_video,
            "is_audio": is_audio,
            "annotations": annotations,
            "metadata": metadata,
        }

        if is_video:
            result["video_info"] = _build_video_info(preview_file)
            all_annotations = preview_file.get("annotations") or []
            result["annotated_frames"] = _get_annotated_frames(all_annotations)

        if is_audio:
            result["audio_info"] = _build_audio_info(preview_file)

        return result, 200

    @jwt_required()
    def put(self, shot_id):
        """
        Save storyboard annotations
        ---
        tags:
        - Shots
        description: Write annotation data to the preview file linked to this
          shot. Delegates to the existing preview_files_service which handles
          Redis locking and WebSocket notification. Supports optional ``frame``
          field in the request body to associate annotations with a video frame.
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
          - in: body
            name: body
            required: True
            schema:
              type: object
              properties:
                annotations:
                  type: object
                  description: Annotation payload (drawing objects, canvas
                    dimensions, time/frame info).
                frame:
                  type: integer
                  description: Video frame number to associate with this
                    annotation. When present, the annotation is stored with
                    frame and time metadata.
        responses:
          200:
            description: Updated preview file data
          400:
            description: Missing preview file or empty annotations
          403:
            description: Insufficient permissions
        """
        shot = shots_service.get_shot(shot_id)
        current_user = persons_service.get_current_user()
        project_id = shot["project_id"]

        if not _check_shot_edit_permission(project_id):
            return {"error": "没有权限编辑此分镜的标注"}, 403

        preview_file_id = shot.get("preview_file_id")
        if not preview_file_id:
            return {"error": "此分镜没有关联的预览文件"}, 400

        data = request.get_json(force=True) if request.is_json else {}
        annotation_data = data.get("annotations", {})

        if not annotation_data:
            return {"error": "标注数据不能为空"}, 400

        # If frame is specified, wrap annotation with frame metadata
        frame = data.get("frame")
        if frame is not None:
            try:
                frame = int(frame)
            except (ValueError, TypeError):
                return {"error": "frame 必须为整数"}, 400
            preview_file = preview_files_service.get_preview_file(
                preview_file_id
            )
            fps = 24
            time_val = round(frame / fps, 3)
            annotation_data = {
                "frame": frame,
                "time": time_val,
                "drawing": annotation_data,
            }

        try:
            result = preview_files_service.update_preview_file_annotations(
                person_id=current_user["id"],
                project_id=project_id,
                preview_file_id=preview_file_id,
                additions=[annotation_data],
                updates=[],
                deletions=[],
            )
            return result, 200
        except Exception as e:
            logger.error("保存分镜标注失败: %s", e)
            return {"error": "保存标注失败，请重试"}, 500


class VideoFrameAnnotationResource(Resource):
    """
    ``GET  /api/data/shots/<shot_id>/annotations/frames``
    ``PUT  /api/data/shots/<shot_id>/annotations/frames/<frame_number>``
    ``DELETE /api/data/shots/<shot_id>/annotations/frames/<frame_number>``

    帧级标注 CRUD 端点，用于视频预览文件的逐帧标注管理。
    """

    @jwt_required()
    def get(self, shot_id, frame_number=None):
        """
        Get annotated frames summary
        ---
        tags:
        - Shots
        description: Return a list of all frames that have annotations,
          along with per-frame summary (object count, tool types).
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
        responses:
          200:
            description: Annotated frames summary
        """
        shot = shots_service.get_shot(shot_id)
        preview_file_id = shot.get("preview_file_id")
        if not preview_file_id:
            return {
                "shot_id": shot_id,
                "annotated_frames": [],
            }, 200

        preview_file = preview_files_service.get_preview_file(preview_file_id)
        annotations = preview_file.get("annotations") or []

        # Group annotations by frame
        frames_map = {}
        for ann in annotations:
            if not isinstance(ann, dict) or "frame" not in ann:
                continue
            frame = ann["frame"]
            if frame not in frames_map:
                frames_map[frame] = {
                    "frame": frame,
                    "time": ann.get("time", 0.0),
                    "object_count": 0,
                    "tool_types": set(),
                }
            drawing = ann.get("drawing", {})
            objects = drawing.get("objects", []) if isinstance(drawing, dict) else []
            frames_map[frame]["object_count"] += len(objects)
            for obj in objects:
                obj_type = obj.get("objectType", obj.get("type", ""))
                if obj_type:
                    frames_map[frame]["tool_types"].add(obj_type)

        # Convert sets to lists and sort by frame number
        annotated_frames = []
        for frame in sorted(frames_map.keys()):
            entry = frames_map[frame]
            entry["tool_types"] = list(entry["tool_types"])
            annotated_frames.append(entry)

        return {
            "shot_id": shot_id,
            "annotated_frames": annotated_frames,
        }, 200

    @jwt_required()
    def put(self, shot_id, frame_number):
        """
        Save annotation for a specific frame
        ---
        tags:
        - Shots
        description: Save or replace annotation data for a specific video
          frame. The annotation is stored in the preview file's JSONB
          annotations array with frame and time metadata.
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
          - in: path
            name: frame_number
            required: True
            type: integer
          - in: body
            name: body
            required: True
            schema:
              type: object
              properties:
                drawing:
                  type: object
                  description: Drawing data (fabric.js canvas objects).
                time:
                  type: number
                  description: Time in seconds corresponding to the frame.
                    If omitted, computed from frame_number / 24 fps.
        responses:
          200:
            description: Updated preview file data
          400:
            description: Missing preview file or empty drawing
          403:
            description: Insufficient permissions
        """
        shot = shots_service.get_shot(shot_id)
        current_user = persons_service.get_current_user()
        project_id = shot["project_id"]

        if not _check_shot_edit_permission(project_id):
            return {"error": "没有权限编辑此分镜的标注"}, 403

        preview_file_id = shot.get("preview_file_id")
        if not preview_file_id:
            return {"error": "此分镜没有关联的预览文件"}, 400

        data = request.get_json(force=True) if request.is_json else {}
        drawing = data.get("drawing", {})

        if not drawing:
            return {"error": "drawing 数据不能为空"}, 400

        fps = 24
        time_val = data.get("time", round(frame_number / fps, 3))

        # Build the frame annotation entry
        frame_annotation = {
            "frame": frame_number,
            "time": time_val,
            "drawing": drawing,
        }

        # Remove existing annotations for this frame, then add the new one.
        # We do this via deletions + additions through the service layer.
        preview_file = preview_files_service.get_preview_file(preview_file_id)
        existing = preview_file.get("annotations") or []
        deletions = [
            ann for ann in existing
            if isinstance(ann, dict) and ann.get("frame") == frame_number
        ]

        try:
            result = preview_files_service.update_preview_file_annotations(
                person_id=current_user["id"],
                project_id=project_id,
                preview_file_id=preview_file_id,
                additions=[frame_annotation],
                updates=[],
                deletions=deletions,
            )
            return result, 200
        except Exception as e:
            logger.error("保存帧标注失败 (frame=%d): %s", frame_number, e)
            return {"error": "保存帧标注失败，请重试"}, 500

    @jwt_required()
    def delete(self, shot_id, frame_number):
        """
        Delete annotation for a specific frame
        ---
        tags:
        - Shots
        description: Remove all annotation data for a specific video frame.
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
          - in: path
            name: frame_number
            required: True
            type: integer
        responses:
          200:
            description: Updated preview file data
          400:
            description: Missing preview file
          403:
            description: Insufficient permissions
        """
        shot = shots_service.get_shot(shot_id)
        current_user = persons_service.get_current_user()
        project_id = shot["project_id"]

        if not _check_shot_edit_permission(project_id):
            return {"error": "没有权限编辑此分镜的标注"}, 403

        preview_file_id = shot.get("preview_file_id")
        if not preview_file_id:
            return {"error": "此分镜没有关联的预览文件"}, 400

        preview_file = preview_files_service.get_preview_file(preview_file_id)
        existing = preview_file.get("annotations") or []
        deletions = [
            ann for ann in existing
            if isinstance(ann, dict) and ann.get("frame") == frame_number
        ]

        if not deletions:
            return {"message": "该帧没有标注数据"}, 200

        try:
            result = preview_files_service.update_preview_file_annotations(
                person_id=current_user["id"],
                project_id=project_id,
                preview_file_id=preview_file_id,
                additions=[],
                updates=[],
                deletions=deletions,
            )
            return result, 200
        except Exception as e:
            logger.error("删除帧标注失败 (frame=%d): %s", frame_number, e)
            return {"error": "删除帧标注失败，请重试"}, 500


class AudioMarkerResource(Resource):
    """
    ``GET    /api/data/shots/<shot_id>/annotations/audio-markers``
    ``POST   /api/data/shots/<shot_id>/annotations/audio-markers``
    ``PUT    /api/data/shots/<shot_id>/annotations/audio-markers/<marker_index>``
    ``DELETE /api/data/shots/<shot_id>/annotations/audio-markers/<marker_index>``

    音频时间标记 CRUD。标记存储在 preview_file.annotations JSONB 中，
    通过 ``label`` + ``time`` 字段与视频帧标注区分。
    """

    @jwt_required()
    def get(self, shot_id, marker_index=None):
        """
        Get audio markers
        ---
        tags:
        - Shots
        description: Return all audio markers for this shot's preview file.
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
        responses:
          200:
            description: Audio markers list with metadata
        """
        shot, preview_file, _ = _get_shot_preview(shot_id)
        preview_file_id = shot.get("preview_file_id")

        if not preview_file:
            return {
                "shot_id": shot_id,
                "preview_file_id": None,
                "is_audio": False,
                "markers": [],
            }, 200

        extension = (preview_file.get("extension") or "").lower()
        is_audio = _is_audio_extension(extension)
        annotations = preview_file.get("annotations") or []
        markers = _get_audio_markers(annotations)

        # Add index to each marker
        indexed_markers = []
        for i, marker in enumerate(markers):
            entry = dict(marker)
            entry["index"] = i
            indexed_markers.append(entry)

        result = {
            "shot_id": shot_id,
            "preview_file_id": preview_file_id,
            "is_audio": is_audio,
            "markers": indexed_markers,
        }

        if is_audio:
            result["audio_info"] = _build_audio_info(preview_file)

        return result, 200

    @jwt_required()
    def post(self, shot_id, marker_index=None):
        """
        Create audio marker
        ---
        tags:
        - Shots
        description: Add a new audio time marker to this shot's preview file.
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
          - in: body
            name: body
            required: True
            schema:
              type: object
              properties:
                time:
                  type: number
                  description: Time in seconds (required)
                label:
                  type: string
                  description: Marker label (optional)
                type:
                  type: string
                  description: "marker", "cue", or "section"
                color:
                  type: string
                  description: Hex color code
                duration:
                  type: number
                  description: Duration in seconds (for type=section)
        responses:
          200:
            description: Created marker with index
          400:
            description: Missing time or preview file
          403:
            description: Insufficient permissions
        """
        shot = shots_service.get_shot(shot_id)
        current_user = persons_service.get_current_user()
        project_id = shot["project_id"]

        if not _check_shot_edit_permission(project_id):
            return {"error": "没有权限编辑此分镜的标注"}, 403

        preview_file_id = shot.get("preview_file_id")
        if not preview_file_id:
            return {"error": "此分镜没有关联的预览文件"}, 400

        data = request.get_json(force=True) if request.is_json else {}
        time_val = data.get("time")
        if time_val is None:
            return {"error": "time 字段为必填"}, 400

        try:
            time_val = float(time_val)
        except (ValueError, TypeError):
            return {"error": "time 必须为数字"}, 400

        # Build new marker
        existing_markers = _get_audio_markers(
            preview_files_service.get_preview_file(preview_file_id)
            .get("annotations") or []
        )
        marker_label = data.get("label", "标记%d" % (len(existing_markers) + 1))
        new_marker = {
            "time": time_val,
            "label": marker_label,
            "type": data.get("type", "marker"),
            "color": data.get("color", "#ff3860"),
        }
        if "duration" in data:
            new_marker["duration"] = data["duration"]

        try:
            result = preview_files_service.update_preview_file_annotations(
                person_id=current_user["id"],
                project_id=project_id,
                preview_file_id=preview_file_id,
                additions=[new_marker],
                updates=[],
                deletions=[],
            )
        except Exception as e:
            logger.error("创建音频标记失败: %s", e)
            return {"error": "创建音频标记失败，请重试"}, 500

        # Re-read to get sorted markers with indices
        preview_file = preview_files_service.get_preview_file(preview_file_id)
        annotations = preview_file.get("annotations") or []
        markers = _get_audio_markers(annotations)

        # Sort markers by time in storage
        markers.sort(key=lambda m: m.get("time", 0))

        # Find the index of the newly added marker
        new_index = None
        for i, m in enumerate(markers):
            if (
                m.get("time") == time_val
                and m.get("label") == marker_label
            ):
                new_index = i
                break

        created = dict(new_marker)
        created["index"] = new_index if new_index is not None else len(markers) - 1

        return {"marker": created}, 200

    @jwt_required()
    def put(self, shot_id, marker_index):
        """
        Update audio marker
        ---
        tags:
        - Shots
        description: Update an audio marker by index.
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
          - in: path
            name: marker_index
            required: True
            type: integer
          - in: body
            name: body
            required: True
            schema:
              type: object
              properties:
                time:
                  type: number
                label:
                  type: string
                type:
                  type: string
                color:
                  type: string
                duration:
                  type: number
        responses:
          200:
            description: Updated marker
          400:
            description: Missing preview file
          403:
            description: Insufficient permissions
          404:
            description: Marker index out of range
        """
        shot = shots_service.get_shot(shot_id)
        current_user = persons_service.get_current_user()
        project_id = shot["project_id"]

        if not _check_shot_edit_permission(project_id):
            return {"error": "没有权限编辑此分镜的标注"}, 403

        preview_file_id = shot.get("preview_file_id")
        if not preview_file_id:
            return {"error": "此分镜没有关联的预览文件"}, 400

        preview_file = preview_files_service.get_preview_file(preview_file_id)
        annotations = preview_file.get("annotations") or []
        markers = _get_audio_markers(annotations)

        if marker_index < 0 or marker_index >= len(markers):
            return {"error": "标记索引超出范围"}, 404

        old_marker = markers[marker_index]
        data = request.get_json(force=True) if request.is_json else {}

        # Build updated marker — only update provided fields
        updated_marker = dict(old_marker)
        for field in ("time", "label", "type", "color", "duration"):
            if field in data:
                updated_marker[field] = data[field]

        try:
            result = preview_files_service.update_preview_file_annotations(
                person_id=current_user["id"],
                project_id=project_id,
                preview_file_id=preview_file_id,
                additions=[updated_marker],
                updates=[],
                deletions=[old_marker],
            )
        except Exception as e:
            logger.error("更新音频标记失败: %s", e)
            return {"error": "更新音频标记失败，请重试"}, 500

        # Re-read to return updated markers with indices
        preview_file = preview_files_service.get_preview_file(preview_file_id)
        all_markers = _get_audio_markers(
            preview_file.get("annotations") or []
        )
        all_markers.sort(key=lambda m: m.get("time", 0))

        indexed = []
        for i, m in enumerate(all_markers):
            entry = dict(m)
            entry["index"] = i
            indexed.append(entry)

        return {"markers": indexed}, 200

    @jwt_required()
    def delete(self, shot_id, marker_index):
        """
        Delete audio marker
        ---
        tags:
        - Shots
        description: Delete an audio marker by index.
        parameters:
          - in: path
            name: shot_id
            required: True
            type: string
            format: uuid
          - in: path
            name: marker_index
            required: True
            type: integer
        responses:
          200:
            description: Remaining markers
          400:
            description: Missing preview file
          403:
            description: Insufficient permissions
          404:
            description: Marker index out of range
        """
        shot = shots_service.get_shot(shot_id)
        current_user = persons_service.get_current_user()
        project_id = shot["project_id"]

        if not _check_shot_edit_permission(project_id):
            return {"error": "没有权限编辑此分镜的标注"}, 403

        preview_file_id = shot.get("preview_file_id")
        if not preview_file_id:
            return {"error": "此分镜没有关联的预览文件"}, 400

        preview_file = preview_files_service.get_preview_file(preview_file_id)
        annotations = preview_file.get("annotations") or []
        markers = _get_audio_markers(annotations)

        if marker_index < 0 or marker_index >= len(markers):
            return {"error": "标记索引超出范围"}, 404

        target_marker = markers[marker_index]

        try:
            result = preview_files_service.update_preview_file_annotations(
                person_id=current_user["id"],
                project_id=project_id,
                preview_file_id=preview_file_id,
                additions=[],
                updates=[],
                deletions=[target_marker],
            )
        except Exception as e:
            logger.error("删除音频标记失败: %s", e)
            return {"error": "删除音频标记失败，请重试"}, 500

        # Re-read to return remaining markers with indices
        preview_file = preview_files_service.get_preview_file(preview_file_id)
        remaining = _get_audio_markers(
            preview_file.get("annotations") or []
        )
        remaining.sort(key=lambda m: m.get("time", 0))

        indexed = []
        for i, m in enumerate(remaining):
            entry = dict(m)
            entry["index"] = i
            indexed.append(entry)

        return {"markers": indexed}, 200


def _extract_annotation_metadata(annotations):
    """从标注数据中提取元数据统计（工具类型、标记数量）。"""
    tool_types = set()
    marker_count = 0

    if not isinstance(annotations, list):
        return {"tool_types": [], "marker_count": 0}

    for ann in annotations:
        drawing = ann.get("drawing", {}) if isinstance(ann, dict) else {}
        objects = drawing.get("objects", []) if isinstance(drawing, dict) else []
        for obj in objects:
            obj_type = obj.get("objectType", obj.get("type", ""))
            if obj_type:
                tool_types.add(obj_type)
            if obj_type == "marker":
                marker_count += 1

    return {
        "tool_types": list(tool_types),
        "marker_count": marker_count,
    }
