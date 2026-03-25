"""
实时协作 API 端点

提供在线状态查询和乐观锁冲突检测。
"""

import logging

from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import presence_service, persons_service

logger = logging.getLogger(__name__)


class OnlineUsersResource(Resource):
    """
    ``GET /api/data/online-users``

    返回所有在线用户列表。
    """

    @jwt_required()
    def get(self):
        return presence_service.get_online_users_detail(), 200


class ProjectOnlineUsersResource(Resource):
    """
    ``GET /api/data/projects/<project_id>/online-users``

    返回项目内在线用户列表。
    """

    @jwt_required()
    def get(self, project_id):
        return presence_service.get_project_online_users(project_id), 200


class HeartbeatResource(Resource):
    """
    ``POST /api/data/heartbeat``

    客户端心跳：更新在线状态和当前页面。

    Body::

        {
            "page": "assets",
            "project_id": "uuid"
        }
    """

    @jwt_required()
    def post(self):
        current_user = persons_service.get_current_user()
        data = request.get_json(force=True) if request.is_json else {}

        presence_service.heartbeat(
            user_id=current_user["id"],
            page=data.get("page", ""),
            project_id=data.get("project_id", ""),
        )

        return {"status": "ok"}, 200


class EntityLockResource(Resource):
    """
    ``POST /api/data/entities/<entity_id>/check-lock``

    乐观锁冲突检测。客户端在保存前发送当前版本号，
    服务端检查是否有其他人正在编辑同一实体。

    Body::

        {
            "updated_at": "2026-03-23T12:00:00"
        }

    Response::

        {
            "locked": false,
            "current_updated_at": "2026-03-23T12:00:00",
            "editing_users": []
        }

        或

        {
            "locked": true,
            "current_updated_at": "2026-03-23T12:30:00",
            "editing_users": [{"user_id": "...", "user_name": "..."}]
        }
    """

    @jwt_required()
    def post(self, entity_id):
        from zou.app.models.entity import Entity

        data = request.get_json(force=True) if request.is_json else {}
        client_updated_at = data.get("updated_at")

        entity = Entity.get(entity_id)
        if not entity:
            abort(404, description="实体不存在")

        server_updated_at = str(entity.updated_at) if entity.updated_at else None

        # 检查版本冲突
        locked = False
        if client_updated_at and server_updated_at:
            locked = client_updated_at != server_updated_at

        # 检查是否有其他人在查看/编辑此实体
        editing_users = []
        online_users = presence_service.get_online_users_detail()
        current_user = persons_service.get_current_user()

        for u in online_users:
            if u["user_id"] != current_user["id"]:
                # 如果其他用户的页面包含此实体 ID，认为正在编辑
                if entity_id in (u.get("page") or ""):
                    editing_users.append({
                        "user_id": u["user_id"],
                        "user_name": u["user_name"],
                    })

        return {
            "locked": locked,
            "current_updated_at": server_updated_at,
            "editing_users": editing_users,
        }, 200
