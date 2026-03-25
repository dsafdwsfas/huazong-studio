"""
AI 风格分析 API

提供图片风格分析的触发、结果查询和批量分析端点。
"""

import logging
import os
import tempfile

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app import db
from zou.app.models.entity import Entity
from zou.app.models.preview_file import PreviewFile
from zou.app.services import (
    projects_service,
    shots_service,
    user_service,
)
from zou.app.services import ai_analysis_service
from zou.app.services import style_metadata_service
from zou.app.services import style_consistency_service
from zou.app.services import style_lock_service
from zou.app.services import style_report_service
from zou.app.services import style_translation_service
from zou.app.stores import file_store
from zou.app.utils.api import WrongParameterException

logger = logging.getLogger(__name__)


class StyleAnalysisResource(Resource):
    """
    POST /api/data/projects/<project_id>/storyboard/shots/<shot_id>/analyze

    触发 AI 风格分析。同步调用 Gemini API（约 5-15s），返回结果。
    """

    @jwt_required()
    def post(self, project_id, shot_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException("Shot not found in project.")

        if not shot.preview_file_id:
            return {"error": "此分镜没有关联的预览文件"}, 400

        preview_file = PreviewFile.get(shot.preview_file_id)
        if preview_file is None:
            return {"error": "预览文件不存在"}, 404

        # Get local file path for the preview image
        image_path = _get_preview_image_path(preview_file)
        if not image_path:
            return {"error": "无法获取预览文件路径"}, 500

        try:
            # Call Gemini API
            result = ai_analysis_service.analyze_image(
                image_path, project_id=project_id
            )
            result["preview_file_id"] = str(shot.preview_file_id)

            # Normalize + merge technical metadata
            if result.get("status") == "success":
                complete = style_metadata_service.build_complete_metadata(
                    result, image_path
                )
                result["normalized"] = complete["style"]
                result["technical"] = complete["technical"]
                result["metadata_version"] = complete["version"]

            # Enrich with bilingual keyword pairs (3.3)
            style_translation_service.enrich_analysis_with_translations(result)

            # Cache in Entity.data
            ai_analysis_service.save_analysis_to_entity(
                shot, result, shot.preview_file_id
            )

            return result, 200
        except Exception as e:
            logger.error("Analysis failed for shot %s: %s", shot_id, e)
            return {"status": "error", "error": str(e)}, 500
        finally:
            # Clean up temp file if created
            if image_path and image_path.startswith(tempfile.gettempdir()):
                try:
                    os.unlink(image_path)
                except OSError:
                    pass


class StyleAnalysisResultResource(Resource):
    """
    GET /api/data/projects/<project_id>/storyboard/shots/<shot_id>/analysis

    获取已缓存的分析结果（从 Entity.data 读取）。
    """

    @jwt_required()
    def get(self, project_id, shot_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException("Shot not found in project.")

        analysis = ai_analysis_service.get_analysis_from_entity(shot)
        if not analysis:
            return {
                "shot_id": shot_id,
                "status": "not_analyzed",
                "result": None,
            }, 200

        # Ensure cached results also have normalized data
        if analysis.get("status") == "success" and "normalized" not in analysis:
            complete = style_metadata_service.build_complete_metadata(analysis)
            analysis["normalized"] = complete["style"]
            analysis["metadata_version"] = complete["version"]

        return {
            "shot_id": shot_id,
            **analysis,
        }, 200


class BatchStyleAnalysisResource(Resource):
    """
    POST /api/data/projects/<project_id>/storyboard/batch-analyze

    批量分析多个 shot。逐个调用 Gemini API。
    """

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        data = request.json or {}
        shot_ids = data.get("shot_ids", [])
        if not shot_ids:
            raise WrongParameterException("shot_ids array required.")

        results = []
        errors = []

        for sid in shot_ids:
            shot = Entity.get(sid)
            if shot is None or str(shot.project_id) != project_id:
                errors.append({"shot_id": sid, "error": "Shot not found."})
                continue

            if not shot.preview_file_id:
                errors.append(
                    {"shot_id": sid, "error": "No preview file."}
                )
                continue

            preview_file = PreviewFile.get(shot.preview_file_id)
            if preview_file is None:
                errors.append(
                    {"shot_id": sid, "error": "Preview file not found."}
                )
                continue

            image_path = _get_preview_image_path(preview_file)
            if not image_path:
                errors.append(
                    {"shot_id": sid, "error": "Cannot get file path."}
                )
                continue

            try:
                result = ai_analysis_service.analyze_image(
                    image_path, project_id=project_id
                )
                result["preview_file_id"] = str(shot.preview_file_id)

                # Normalize + merge technical metadata
                if result.get("status") == "success":
                    complete = style_metadata_service.build_complete_metadata(
                        result, image_path
                    )
                    result["normalized"] = complete["style"]
                    result["technical"] = complete["technical"]
                    result["metadata_version"] = complete["version"]

                ai_analysis_service.save_analysis_to_entity(
                    shot, result, shot.preview_file_id
                )
                results.append(
                    {"shot_id": sid, "status": result.get("status", "error")}
                )
            except Exception as e:
                errors.append({"shot_id": sid, "error": str(e)})
            finally:
                if image_path and image_path.startswith(tempfile.gettempdir()):
                    try:
                        os.unlink(image_path)
                    except OSError:
                        pass

        return {
            "analyzed_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors,
        }, 200


class StyleKeywordTranslateResource(Resource):
    """
    POST /api/data/projects/<project_id>/storyboard/translate-keywords

    翻译英文风格关键词为中文（或反向）。
    """

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        data = request.json or {}
        keywords = data.get("keywords", [])
        direction = data.get("direction", "en_to_cn")

        if not keywords:
            return {"translations": [], "glossary_size": len(style_translation_service.STYLE_GLOSSARY)}, 200

        if direction == "cn_to_en":
            translations = style_translation_service.translate_keywords_cn_to_en(keywords)
        else:
            translations = style_translation_service.translate_keywords(keywords)

        return {
            "translations": translations,
            "glossary_size": len(style_translation_service.STYLE_GLOSSARY),
        }, 200


class StyleReportExportResource(Resource):
    """
    GET /api/data/projects/<project_id>/storyboard/style-report

    导出项目风格报告（Markdown 格式）。
    """

    @jwt_required()
    def get(self, project_id):
        from zou.app.models.project import Project

        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        project = Project.get(project_id)
        project_name = project.name if project else "Unknown"

        locked = style_lock_service.get_locked_style(project_id)

        report = style_report_service.generate_report(
            project_name, locked
        )

        return {
            "report": report,
            "format": "markdown",
            "project_name": project_name,
        }, 200


class StyleConsistencyCheckResource(Resource):
    """
    GET /api/data/projects/<project_id>/storyboard/shots/<shot_id>/consistency

    检查 shot 与项目锁定风格的一致性。
    """

    @jwt_required()
    def get(self, project_id, shot_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException("Shot not found in project.")

        analysis = ai_analysis_service.get_analysis_from_entity(shot)
        if not analysis or analysis.get("status") != "success":
            return {"score": -1, "message": "Shot 尚未分析"}, 200

        result = style_consistency_service.check_consistency(
            project_id, analysis.get("result", {})
        )
        return {"shot_id": shot_id, **result}, 200


def _get_preview_image_path(preview_file):
    """
    获取预览文件的本地路径。
    尝试从 file_store 获取，失败则下载到临时文件。
    """
    try:
        pf_id = str(preview_file.id)
        extension = preview_file.extension or "png"

        # Try to get from local file store
        local_path = file_store.get_local_picture_path(
            "originals", pf_id
        )
        if local_path and os.path.exists(local_path):
            return local_path

        # Fallback: try thumbnails
        local_path = file_store.get_local_picture_path(
            "thumbnails-square", pf_id
        )
        if local_path and os.path.exists(local_path):
            return local_path

        # Fallback: download from file store to temp file
        tmp = tempfile.NamedTemporaryFile(
            suffix=f".{extension}", delete=False
        )
        tmp_path = tmp.name
        tmp.close()

        file_store.open_picture("originals", pf_id, tmp_path)
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            return tmp_path

        return None
    except Exception as e:
        logger.error("Failed to get preview file path: %s", e)
        return None
