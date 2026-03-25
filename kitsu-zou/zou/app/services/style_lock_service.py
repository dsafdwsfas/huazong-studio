"""
风格锁定服务

将风格配置保存到 Project.data JSONB 中，支持锁定/解锁/参考图管理。
"""

import logging
import time

from zou.app import db
from zou.app.models.project import Project
from zou.app.services import persons_service

logger = logging.getLogger(__name__)


def lock_style(project_id, person_id, style_data, reference_image_ids=None):
    """锁定项目风格。"""
    project = Project.get(project_id)
    person = persons_service.get_person(person_id)

    data = dict(project.data) if project.data else {}
    data["style_lock"] = {
        "locked": True,
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "locked_by": str(person_id),
        "locked_by_name": person.get("full_name", ""),
        "reference_image_ids": reference_image_ids or [],
        "style": style_data,
    }
    project.data = data
    project.save()
    db.session.commit()
    return data["style_lock"]


def unlock_style(project_id, person_id):
    """解锁项目风格。"""
    project = Project.get(project_id)
    data = dict(project.data) if project.data else {}
    data.pop("style_lock", None)
    project.data = data
    project.save()
    db.session.commit()


def get_locked_style(project_id):
    """获取已锁定的风格（或 None）。"""
    project = Project.get(project_id)
    data = project.data or {}
    return data.get("style_lock")


def add_reference_image(project_id, preview_file_id):
    """添加参考图到项目风格参考列表。"""
    project = Project.get(project_id)
    data = dict(project.data) if project.data else {}

    refs = data.get("style_references", [])
    # Avoid duplicates
    for ref in refs:
        if ref.get("preview_file_id") == str(preview_file_id):
            return refs

    refs.append({
        "preview_file_id": str(preview_file_id),
        "added_at": time.strftime("%Y-%m-%d"),
    })
    data["style_references"] = refs
    project.data = data
    project.save()
    db.session.commit()
    return refs


def remove_reference_image(project_id, preview_file_id):
    """从参考列表移除。"""
    project = Project.get(project_id)
    data = dict(project.data) if project.data else {}

    refs = data.get("style_references", [])
    refs = [r for r in refs if r.get("preview_file_id") != str(preview_file_id)]
    data["style_references"] = refs
    project.data = data
    project.save()
    db.session.commit()
    return refs


def get_reference_images(project_id):
    """获取参考图列表（含分析结果）。"""
    from zou.app.models.preview_file import PreviewFile
    from zou.app.services import ai_analysis_service

    project = Project.get(project_id)
    data = project.data or {}
    refs = data.get("style_references", [])

    result = []
    for ref in refs:
        pf_id = ref.get("preview_file_id")
        entry = {
            "preview_file_id": pf_id,
            "thumbnail_url": (
                f"/api/pictures/thumbnails-square/preview-files/{pf_id}.png"
            ),
            "original_url": (
                f"/api/pictures/originals/preview-files/{pf_id}.png"
            ),
            "added_at": ref.get("added_at"),
            "analysis": None,
        }

        # Try to find analysis from Entity.data if the preview file
        # is associated with a shot that has been analyzed
        preview_file = PreviewFile.get(pf_id)
        if preview_file and preview_file.task_id:
            from zou.app.models.entity import Entity
            from zou.app.models.task import Task

            task = Task.get(preview_file.task_id)
            if task and task.entity_id:
                entity = Entity.get(task.entity_id)
                if entity:
                    analysis = ai_analysis_service.get_analysis_from_entity(
                        entity
                    )
                    if analysis and analysis.get("status") == "success":
                        entry["analysis"] = analysis.get("result")

        result.append(entry)

    return result
