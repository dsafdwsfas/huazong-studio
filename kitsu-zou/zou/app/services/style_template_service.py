"""
风格模板服务

将可复用的风格配置存储在 Project.data["style_templates"] 数组中。
支持创建/列表/更新/删除/应用模板，以及跨项目共享。
"""

import logging
import time
import uuid

from zou.app import db
from zou.app.models.project import Project
from zou.app.services import persons_service

logger = logging.getLogger(__name__)


def _get_templates(project):
    """从 project.data 中提取模板列表。"""
    data = project.data or {}
    return data.get("style_templates", [])


def _save_templates(project, templates):
    """将模板列表写回 project.data。"""
    data = dict(project.data) if project.data else {}
    data["style_templates"] = templates
    project.data = data
    project.save()
    db.session.commit()


def create_template(
    project_id,
    person_id,
    name,
    description,
    style_data,
    thumbnail_preview_file_id=None,
    tags=None,
    is_shared=False,
):
    """从风格数据创建模板。"""
    project = Project.get(project_id)
    person = persons_service.get_person(person_id)

    templates = _get_templates(project)
    template = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description or "",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "created_by": str(person_id),
        "created_by_name": person.get("full_name", ""),
        "style": style_data,
        "thumbnail_preview_file_id": (
            str(thumbnail_preview_file_id) if thumbnail_preview_file_id else None
        ),
        "is_shared": is_shared,
        "tags": tags or [],
    }
    templates.append(template)
    _save_templates(project, templates)
    return template


def list_templates(project_id, include_shared=True):
    """列出项目模板，可选包含其他项目的共享模板。"""
    project = Project.get(project_id)
    project_templates = _get_templates(project)

    shared_templates = []
    if include_shared:
        all_projects = Project.query.filter(
            Project.id != project.id
        ).all()
        for p in all_projects:
            p_data = p.data or {}
            for t in p_data.get("style_templates", []):
                if t.get("is_shared"):
                    entry = dict(t)
                    entry["project_id"] = str(p.id)
                    entry["project_name"] = p.name
                    shared_templates.append(entry)

    return {
        "templates": project_templates,
        "shared_templates": shared_templates,
    }


def get_template(project_id, template_id):
    """获取单个模板，先查本项目再查共享。"""
    project = Project.get(project_id)
    for t in _get_templates(project):
        if t.get("id") == template_id:
            return t

    # Check shared templates from other projects
    all_projects = Project.query.filter(
        Project.id != project.id
    ).all()
    for p in all_projects:
        p_data = p.data or {}
        for t in p_data.get("style_templates", []):
            if t.get("id") == template_id and t.get("is_shared"):
                entry = dict(t)
                entry["project_id"] = str(p.id)
                entry["project_name"] = p.name
                return entry

    return None


def update_template(
    project_id,
    template_id,
    name=None,
    description=None,
    tags=None,
    is_shared=None,
):
    """更新模板元信息（不更新 style 数据）。"""
    project = Project.get(project_id)
    templates = _get_templates(project)

    for t in templates:
        if t.get("id") == template_id:
            if name is not None:
                t["name"] = name
            if description is not None:
                t["description"] = description
            if tags is not None:
                t["tags"] = tags
            if is_shared is not None:
                t["is_shared"] = is_shared
            _save_templates(project, templates)
            return t

    return None


def delete_template(project_id, template_id):
    """删除模板。"""
    project = Project.get(project_id)
    templates = _get_templates(project)
    original_len = len(templates)

    templates = [t for t in templates if t.get("id") != template_id]
    if len(templates) == original_len:
        return False

    _save_templates(project, templates)
    return True


def apply_template(project_id, template_id, person_id):
    """将模板的 style 数据应用为项目的锁定风格。"""
    from zou.app.services import style_lock_service

    template = get_template(project_id, template_id)
    if not template:
        return None

    style_data = template.get("style")
    if not style_data:
        return None

    reference_image_ids = []
    if template.get("thumbnail_preview_file_id"):
        reference_image_ids.append(template["thumbnail_preview_file_id"])

    return style_lock_service.lock_style(
        project_id, person_id, style_data, reference_image_ids
    )
