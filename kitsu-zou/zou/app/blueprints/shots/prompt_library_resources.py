"""
提示词库 API

提供项目级 AI 提示词的 CRUD、版本管理、收藏和使用计数端点。
"""

import logging

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import (
    persons_service,
    projects_service,
    user_service,
)
from zou.app.services import prompt_library_service
from zou.app.services.exception import WrongParameterException

logger = logging.getLogger(__name__)


class PromptLibraryListResource(Resource):
    """
    GET  /projects/<pid>/storyboard/prompts — 列表（支持 ?category=&tag=&search=）
    POST /projects/<pid>/storyboard/prompts — 创建
    """

    @jwt_required()
    def get(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        category = request.args.get("category")
        tag = request.args.get("tag")
        search = request.args.get("search")

        result = prompt_library_service.list_prompts(
            project_id, category=category, tag=tag, search=search
        )
        return result, 200

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        title = data.get("title")
        if not title:
            raise WrongParameterException("title is required.")

        content = data.get("content")
        if not content:
            raise WrongParameterException("content is required.")

        current_user = persons_service.get_current_user()
        person_id = current_user["id"]

        prompt = prompt_library_service.create_prompt(
            project_id,
            person_id,
            title=title,
            content=content,
            content_cn=data.get("content_cn"),
            category=data.get("category", "other"),
            tags=data.get("tags", []),
        )
        return prompt, 201


class PromptLibraryResource(Resource):
    """
    GET    /projects/<pid>/storyboard/prompts/<prompt_id> — 详情+版本历史
    PUT    /projects/<pid>/storyboard/prompts/<prompt_id> — 更新（自动版本）
    DELETE /projects/<pid>/storyboard/prompts/<prompt_id> — 删除
    """

    @jwt_required()
    def get(self, project_id, prompt_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        prompt = prompt_library_service.get_prompt(project_id, prompt_id)
        if not prompt:
            return {"message": "Prompt not found."}, 404
        return prompt, 200

    @jwt_required()
    def put(self, project_id, prompt_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        current_user = persons_service.get_current_user()
        person_id = current_user["id"]

        prompt = prompt_library_service.update_prompt(
            project_id,
            prompt_id,
            person_id,
            title=data.get("title"),
            content=data.get("content"),
            content_cn=data.get("content_cn"),
            category=data.get("category"),
            tags=data.get("tags"),
        )
        if not prompt:
            return {"message": "Prompt not found."}, 404
        return prompt, 200

    @jwt_required()
    def delete(self, project_id, prompt_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        deleted = prompt_library_service.delete_prompt(project_id, prompt_id)
        if not deleted:
            return {"message": "Prompt not found."}, 404
        return {"message": "Prompt deleted."}, 200


class PromptLibraryFavoriteResource(Resource):
    """
    POST /projects/<pid>/storyboard/prompts/<prompt_id>/favorite — 切换收藏
    """

    @jwt_required()
    def post(self, project_id, prompt_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        prompt = prompt_library_service.toggle_favorite(project_id, prompt_id)
        if not prompt:
            return {"message": "Prompt not found."}, 404
        return prompt, 200


class PromptLibraryRevertResource(Resource):
    """
    POST /projects/<pid>/storyboard/prompts/<prompt_id>/revert — 回滚版本
    """

    @jwt_required()
    def post(self, project_id, prompt_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        version = data.get("version")
        if version is None:
            raise WrongParameterException("version is required.")

        prompt = prompt_library_service.revert_prompt(
            project_id, prompt_id, version
        )
        if not prompt:
            return {"message": "Prompt or version not found."}, 404
        return prompt, 200


class PromptLibraryUseResource(Resource):
    """
    POST /projects/<pid>/storyboard/prompts/<prompt_id>/use — 增加使用次数
    """

    @jwt_required()
    def post(self, project_id, prompt_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        prompt = prompt_library_service.increment_usage(project_id, prompt_id)
        if not prompt:
            return {"message": "Prompt not found."}, 404
        return prompt, 200
