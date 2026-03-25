"""
风格锁定 API

提供项目级风格锁定/解锁和参考图管理端点。
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
from zou.app.services import style_lock_service
from zou.app.utils.api import WrongParameterException

logger = logging.getLogger(__name__)


class StyleLockResource(Resource):
    """
    GET    /projects/<pid>/storyboard/style-lock — 获取锁定状态
    POST   /projects/<pid>/storyboard/style-lock — 锁定风格
    DELETE /projects/<pid>/storyboard/style-lock — 解锁
    """

    @jwt_required()
    def get(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        style_lock = style_lock_service.get_locked_style(project_id)
        if not style_lock:
            return {
                "locked": False,
                "locked_at": None,
                "locked_by": None,
                "style": None,
                "reference_count": 0,
            }, 200

        return {
            "locked": True,
            "locked_at": style_lock.get("locked_at"),
            "locked_by": {
                "id": style_lock.get("locked_by"),
                "name": style_lock.get("locked_by_name"),
            },
            "style": style_lock.get("style"),
            "reference_count": len(
                style_lock.get("reference_image_ids", [])
            ),
        }, 200

    @jwt_required()
    def post(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        style_data = data.get("style")
        if not style_data:
            raise WrongParameterException("style data required.")

        reference_image_ids = data.get("reference_image_ids", [])
        current_user = persons_service.get_current_user()
        person_id = current_user["id"]

        result = style_lock_service.lock_style(
            project_id, person_id, style_data, reference_image_ids
        )
        return result, 201

    @jwt_required()
    def delete(self, project_id):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        current_user = persons_service.get_current_user()
        person_id = current_user["id"]

        style_lock_service.unlock_style(project_id, person_id)
        return {"message": "Style unlocked."}, 200


class StyleReferenceResource(Resource):
    """
    GET    /projects/<pid>/storyboard/style-references — 参考图列表
    POST   /projects/<pid>/storyboard/style-references — 添加参考图
    DELETE /projects/<pid>/storyboard/style-references/<pf_id> — 删除参考图
    """

    @jwt_required()
    def get(self, project_id, preview_file_id=None):
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        references = style_lock_service.get_reference_images(project_id)
        return {"references": references}, 200

    @jwt_required()
    def post(self, project_id, preview_file_id=None):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        pf_id = data.get("preview_file_id")
        if not pf_id:
            raise WrongParameterException("preview_file_id required.")

        refs = style_lock_service.add_reference_image(project_id, pf_id)
        return {"references": refs}, 201

    @jwt_required()
    def delete(self, project_id, preview_file_id=None):
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        if not preview_file_id:
            raise WrongParameterException("preview_file_id required in URL.")

        refs = style_lock_service.remove_reference_image(
            project_id, preview_file_id
        )
        return {"references": refs}, 200
