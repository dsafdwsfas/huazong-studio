"""
项目权限管理 API 端点

提供项目角色管理和实体级访问控制 CRUD。
"""

import logging

from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app import db
from zou.app.models.project import (
    ProjectPersonLink,
    EntityAccessControl,
    PROJECT_ROLE_TYPES,
)
from zou.app.utils.permissions import (
    check_manager_permissions,
    has_admin_permissions,
    has_project_role,
)
from zou.app.services import persons_service

logger = logging.getLogger(__name__)


def _require_project_admin(project_id):
    """要求全局 admin/manager 或项目 director/producer"""
    if has_admin_permissions():
        return
    current_user = persons_service.get_current_user()
    if not has_project_role(
        project_id, current_user["id"], ["director", "producer"]
    ):
        abort(403, description="需要项目导演或制片权限")


class ProjectTeamRolesResource(Resource):
    """
    ``GET /api/data/projects/<project_id>/team-roles``

    返回项目团队成员及其项目角色。
    """

    @jwt_required()
    def get(self, project_id):
        members = ProjectPersonLink.query.filter_by(
            project_id=project_id
        ).all()

        result = []
        for m in members:
            role = m.project_role
            if hasattr(role, "value"):
                role = role.value
            result.append({
                "person_id": str(m.person_id),
                "project_id": str(m.project_id),
                "project_role": role or "artist",
            })

        return result, 200


class ProjectMemberRoleResource(Resource):
    """
    ``PUT /api/data/projects/<project_id>/team/<person_id>/role``

    设置项目成员的角色。

    Body: ``{"project_role": "director"}``
    """

    @jwt_required()
    def put(self, project_id, person_id):
        _require_project_admin(project_id)

        data = request.get_json(force=True)
        new_role = data.get("project_role")

        valid_roles = [r[0] for r in PROJECT_ROLE_TYPES]
        if new_role not in valid_roles:
            abort(400, description=f"无效角色: {new_role}，可选: {valid_roles}")

        link = ProjectPersonLink.query.filter_by(
            project_id=project_id,
            person_id=person_id,
        ).first()

        if not link:
            abort(404, description="该成员不在项目团队中")

        link.project_role = new_role
        db.session.commit()

        logger.info(
            "项目角色更新: project=%s person=%s role=%s",
            project_id,
            person_id,
            new_role,
        )

        return {
            "person_id": str(person_id),
            "project_id": str(project_id),
            "project_role": new_role,
        }, 200


class EntityAccessControlListResource(Resource):
    """
    ``GET /api/data/projects/<project_id>/access-controls``

    列出项目的所有实体级访问控制规则。

    ``POST /api/data/projects/<project_id>/access-controls``

    创建或更新实体级访问控制规则。

    Body::

        {
            "entity_id": "uuid",
            "project_role": "observer",
            "can_view": true,
            "can_edit": false,
            "can_comment": true
        }
    """

    @jwt_required()
    def get(self, project_id):
        acls = EntityAccessControl.query.filter_by(
            project_id=project_id
        ).all()

        result = []
        for acl in acls:
            role = acl.project_role
            if hasattr(role, "value"):
                role = role.value
            result.append({
                "id": str(acl.id),
                "entity_id": str(acl.entity_id),
                "project_id": str(acl.project_id),
                "project_role": role,
                "can_view": acl.can_view,
                "can_edit": acl.can_edit,
                "can_comment": acl.can_comment,
            })

        return result, 200

    @jwt_required()
    def post(self, project_id):
        _require_project_admin(project_id)

        data = request.get_json(force=True)
        entity_id = data.get("entity_id")
        project_role = data.get("project_role")

        if not entity_id or not project_role:
            abort(400, description="entity_id 和 project_role 必填")

        valid_roles = [r[0] for r in PROJECT_ROLE_TYPES]
        if project_role not in valid_roles:
            abort(400, description=f"无效角色: {project_role}")

        # upsert: 存在则更新，不存在则创建
        acl = EntityAccessControl.query.filter_by(
            entity_id=entity_id,
            project_id=project_id,
            project_role=project_role,
        ).first()

        if acl:
            acl.can_view = data.get("can_view", acl.can_view)
            acl.can_edit = data.get("can_edit", acl.can_edit)
            acl.can_comment = data.get("can_comment", acl.can_comment)
        else:
            acl = EntityAccessControl(
                entity_id=entity_id,
                project_id=project_id,
                project_role=project_role,
                can_view=data.get("can_view", True),
                can_edit=data.get("can_edit", True),
                can_comment=data.get("can_comment", True),
            )
            db.session.add(acl)

        db.session.commit()

        role = acl.project_role
        if hasattr(role, "value"):
            role = role.value

        return {
            "id": str(acl.id),
            "entity_id": str(acl.entity_id),
            "project_id": str(acl.project_id),
            "project_role": role,
            "can_view": acl.can_view,
            "can_edit": acl.can_edit,
            "can_comment": acl.can_comment,
        }, 200


class EntityAccessControlResource(Resource):
    """
    ``DELETE /api/data/projects/<project_id>/access-controls/<acl_id>``

    删除一条访问控制规则。
    """

    @jwt_required()
    def delete(self, project_id, acl_id):
        _require_project_admin(project_id)

        acl = EntityAccessControl.get(acl_id)
        if not acl or str(acl.project_id) != project_id:
            abort(404, description="访问控制规则不存在")

        db.session.delete(acl)
        db.session.commit()

        return {"status": "deleted"}, 200


class ProjectRoleTypesResource(Resource):
    """
    ``GET /api/data/project-role-types``

    返回所有可用的项目角色类型。
    """

    @jwt_required()
    def get(self):
        return [
            {"id": r[0], "name": r[1]} for r in PROJECT_ROLE_TYPES
        ], 200
