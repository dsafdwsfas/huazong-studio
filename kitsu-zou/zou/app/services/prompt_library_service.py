"""
提示词库服务

将项目级 AI 提示词存储在 Project.data["prompt_library"] 数组中。
支持 CRUD、版本管理、收藏、使用计数、分类/标签/搜索筛选。
"""

import logging
import time
import uuid

from zou.app import db
from zou.app.models.project import Project
from zou.app.services import persons_service

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"scene", "character", "prop", "effect", "style", "other"}


def _get_prompt_library(project):
    """从 project.data 中提取提示词列表。"""
    data = project.data or {}
    return data.get("prompt_library", [])


def _save_prompt_library(project, prompts):
    """将提示词列表写回 project.data。"""
    data = dict(project.data) if project.data else {}
    data["prompt_library"] = prompts
    project.data = data
    project.save()
    db.session.commit()


def _find_prompt(prompts, prompt_id):
    """在列表中查找指定 prompt，返回 (index, prompt) 或 (None, None)。"""
    for i, p in enumerate(prompts):
        if p.get("id") == prompt_id:
            return i, p
    return None, None


def list_prompts(project_id, category=None, tag=None, search=None):
    """列出提示词，支持分类/标签/搜索筛选。"""
    project = Project.get(project_id)
    prompts = _get_prompt_library(project)

    if category:
        prompts = [p for p in prompts if p["category"] == category]
    if tag:
        prompts = [p for p in prompts if tag in (p.get("tags") or [])]
    if search:
        q = search.lower()
        prompts = [
            p
            for p in prompts
            if q in p.get("title", "").lower()
            or q in p.get("content", "").lower()
            or q in p.get("content_cn", "").lower()
        ]

    # 计算分类统计（基于未筛选数据）
    all_prompts = _get_prompt_library(project)
    categories = {}
    for p in all_prompts:
        cat = p.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "prompts": prompts,
        "total": len(prompts),
        "categories": categories,
    }


def get_prompt(project_id, prompt_id):
    """获取单个提示词详情。"""
    project = Project.get(project_id)
    prompts = _get_prompt_library(project)
    _, prompt = _find_prompt(prompts, prompt_id)
    return prompt


def create_prompt(
    project_id,
    person_id,
    title,
    content,
    content_cn=None,
    category="other",
    tags=None,
):
    """创建提示词。"""
    project = Project.get(project_id)
    person = persons_service.get_person(person_id)

    if category not in VALID_CATEGORIES:
        category = "other"

    prompts = _get_prompt_library(project)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    prompt = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "content_cn": content_cn or "",
        "category": category,
        "tags": tags or [],
        "version": 1,
        "versions": [],
        "created_at": now,
        "updated_at": now,
        "created_by": str(person_id),
        "created_by_name": person.get("full_name", ""),
        "usage_count": 0,
        "is_favorite": False,
    }
    prompts.append(prompt)
    _save_prompt_library(project, prompts)
    return prompt


def update_prompt(
    project_id,
    prompt_id,
    person_id,
    title=None,
    content=None,
    content_cn=None,
    category=None,
    tags=None,
):
    """更新提示词（内容变更时自动创建新版本）。"""
    project = Project.get(project_id)
    prompts = _get_prompt_library(project)
    idx, prompt = _find_prompt(prompts, prompt_id)
    if prompt is None:
        return None

    now = time.strftime("%Y-%m-%dT%H:%M:%S")

    # 如果 content 或 content_cn 变更，保存当前版本到 versions
    content_changed = (content is not None and content != prompt["content"]) or (
        content_cn is not None and content_cn != prompt.get("content_cn", "")
    )
    if content_changed:
        version_snapshot = {
            "version": prompt["version"],
            "content": prompt["content"],
            "content_cn": prompt.get("content_cn", ""),
            "created_at": prompt["updated_at"],
            "created_by": prompt.get("created_by", ""),
        }
        prompt.setdefault("versions", []).append(version_snapshot)
        prompt["version"] = prompt["version"] + 1

    if title is not None:
        prompt["title"] = title
    if content is not None:
        prompt["content"] = content
    if content_cn is not None:
        prompt["content_cn"] = content_cn
    if category is not None:
        prompt["category"] = category if category in VALID_CATEGORIES else "other"
    if tags is not None:
        prompt["tags"] = tags
    prompt["updated_at"] = now

    prompts[idx] = prompt
    _save_prompt_library(project, prompts)
    return prompt


def delete_prompt(project_id, prompt_id):
    """删除提示词。"""
    project = Project.get(project_id)
    prompts = _get_prompt_library(project)
    original_len = len(prompts)

    prompts = [p for p in prompts if p.get("id") != prompt_id]
    if len(prompts) == original_len:
        return False

    _save_prompt_library(project, prompts)
    return True


def get_prompt_versions(project_id, prompt_id):
    """获取提示词版本历史。"""
    prompt = get_prompt(project_id, prompt_id)
    if not prompt:
        return None
    return {
        "current_version": prompt["version"],
        "versions": prompt.get("versions", []),
    }


def revert_prompt(project_id, prompt_id, version_number):
    """回滚到指定版本。"""
    project = Project.get(project_id)
    prompts = _get_prompt_library(project)
    idx, prompt = _find_prompt(prompts, prompt_id)
    if prompt is None:
        return None

    versions = prompt.get("versions", [])
    target = None
    for v in versions:
        if v["version"] == version_number:
            target = v
            break
    if target is None:
        return None

    now = time.strftime("%Y-%m-%dT%H:%M:%S")

    # 保存当前版本到 versions
    version_snapshot = {
        "version": prompt["version"],
        "content": prompt["content"],
        "content_cn": prompt.get("content_cn", ""),
        "created_at": prompt["updated_at"],
        "created_by": prompt.get("created_by", ""),
    }
    prompt["versions"].append(version_snapshot)
    prompt["version"] = prompt["version"] + 1
    prompt["content"] = target["content"]
    prompt["content_cn"] = target.get("content_cn", "")
    prompt["updated_at"] = now

    prompts[idx] = prompt
    _save_prompt_library(project, prompts)
    return prompt


def toggle_favorite(project_id, prompt_id):
    """切换收藏状态。"""
    project = Project.get(project_id)
    prompts = _get_prompt_library(project)
    idx, prompt = _find_prompt(prompts, prompt_id)
    if prompt is None:
        return None

    prompt["is_favorite"] = not prompt.get("is_favorite", False)
    prompts[idx] = prompt
    _save_prompt_library(project, prompts)
    return prompt


def increment_usage(project_id, prompt_id):
    """增加使用次数。"""
    project = Project.get(project_id)
    prompts = _get_prompt_library(project)
    idx, prompt = _find_prompt(prompts, prompt_id)
    if prompt is None:
        return None

    prompt["usage_count"] = prompt.get("usage_count", 0) + 1
    prompts[idx] = prompt
    _save_prompt_library(project, prompts)
    return prompt
