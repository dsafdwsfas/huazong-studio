"""
风格模板 API

提供项目级风格模板的 CRUD 和应用端点。
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
from zou.app.services import style_template_service
from zou.app.services.exception import WrongParameterException

logger = logging.getLogger(__name__)


class StyleTemplateListResource(Resource):
    """
    GET  /projects/<pid>/storyboard/style-templates — 列表（含共享）
    POST /projects/<pid>/storyboard/style-templates — 创建模板
    """

    @jwt_required()
    def get(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        include_shared = request.args.get("include_shared", "true")
        include_shared = include_shared.lower() != "false"

        result = style_template_service.list_templates(
            project_id, include_shared=include_shared
        )
        return result, 200

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        name = data.get("name")
        if not name:
            raise WrongParameterException("name is required.")

        style_data = data.get("style")
        if not style_data:
            raise WrongParameterException("style data is required.")

        current_user = persons_service.get_current_user()
        person_id = current_user["id"]

        template = style_template_service.create_template(
            project_id,
            person_id,
            name=name,
            description=data.get("description", ""),
            style_data=style_data,
            thumbnail_preview_file_id=data.get("thumbnail_preview_file_id"),
            tags=data.get("tags", []),
            is_shared=data.get("is_shared", False),
        )
        return template, 201


class StyleTemplateResource(Resource):
    """
    GET    /projects/<pid>/storyboard/style-templates/<tid> — 详情
    PUT    /projects/<pid>/storyboard/style-templates/<tid> — 更新
    DELETE /projects/<pid>/storyboard/style-templates/<tid> — 删除
    """

    @jwt_required()
    def get(self, project_id, template_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        template = style_template_service.get_template(
            project_id, template_id
        )
        if not template:
            return {"message": "Template not found."}, 404
        return template, 200

    @jwt_required()
    def put(self, project_id, template_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        template = style_template_service.update_template(
            project_id,
            template_id,
            name=data.get("name"),
            description=data.get("description"),
            tags=data.get("tags"),
            is_shared=data.get("is_shared"),
        )
        if not template:
            return {"message": "Template not found."}, 404
        return template, 200

    @jwt_required()
    def delete(self, project_id, template_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        deleted = style_template_service.delete_template(
            project_id, template_id
        )
        if not deleted:
            return {"message": "Template not found."}, 404
        return {"message": "Template deleted."}, 200


class StyleTemplateApplyResource(Resource):
    """
    POST /projects/<pid>/storyboard/style-templates/<tid>/apply — 应用到项目
    """

    @jwt_required()
    def post(self, project_id, template_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        current_user = persons_service.get_current_user()
        person_id = current_user["id"]

        result = style_template_service.apply_template(
            project_id, template_id, person_id
        )
        if not result:
            return {"message": "Template not found or has no style data."}, 404
        return result, 200
