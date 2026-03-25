"""
镜头语言库 API

提供项目级镜头语言术语的 CRUD 和预置术语初始化端点。
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
from zou.app.services import camera_language_service
from zou.app.utils.api import WrongParameterException

logger = logging.getLogger(__name__)


class CameraLanguageListResource(Resource):
    """
    GET  /projects/<pid>/storyboard/camera-language — 列表
    POST /projects/<pid>/storyboard/camera-language — 创建
    """

    @jwt_required()
    def get(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        category = request.args.get("category")
        search = request.args.get("search")

        result = camera_language_service.list_terms(
            project_id, category=category, search=search
        )
        return result, 200

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        term_cn = data.get("term_cn")
        if not term_cn:
            raise WrongParameterException("term_cn is required.")

        term_en = data.get("term_en")
        if not term_en:
            raise WrongParameterException("term_en is required.")

        current_user = persons_service.get_current_user()
        person_id = current_user["id"]

        term = camera_language_service.create_term(
            project_id,
            person_id,
            term_cn=term_cn,
            term_en=term_en,
            category=data.get("category", "other"),
            description=data.get("description", ""),
            example_usage=data.get("example_usage", ""),
            tags=data.get("tags", []),
        )
        return term, 201


class CameraLanguageResource(Resource):
    """
    PUT    /projects/<pid>/storyboard/camera-language/<term_id> — 更新
    DELETE /projects/<pid>/storyboard/camera-language/<term_id> — 删除
    """

    @jwt_required()
    def put(self, project_id, term_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}

        term = camera_language_service.update_term(
            project_id,
            term_id,
            term_cn=data.get("term_cn"),
            term_en=data.get("term_en"),
            category=data.get("category"),
            description=data.get("description"),
            example_usage=data.get("example_usage"),
            tags=data.get("tags"),
        )
        if not term:
            return {"message": "Term not found."}, 404
        return term, 200

    @jwt_required()
    def delete(self, project_id, term_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        deleted = camera_language_service.delete_term(project_id, term_id)
        if not deleted:
            return {"message": "Term not found."}, 404
        return {"message": "Term deleted."}, 200


class CameraLanguageInitResource(Resource):
    """
    POST /projects/<pid>/storyboard/camera-language/init — 初始化预置术语
    """

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        current_user = persons_service.get_current_user()
        person_id = current_user["id"]

        result = camera_language_service.init_default_terms(
            project_id, person_id
        )
        return result, 200
