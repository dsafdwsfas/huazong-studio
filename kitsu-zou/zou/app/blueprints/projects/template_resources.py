from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.models.project import Project
from zou.app.models.project_template import ProjectTemplate
from zou.app.utils import permissions


class ProjectTemplatesResource(Resource):
    """
    List all project templates or create a new one from an existing project.
    """

    @jwt_required()
    def get(self):
        """List all project templates."""
        permissions.check_admin_permissions()
        templates = ProjectTemplate.query.all()
        return [t.present() for t in templates]

    @jwt_required()
    def post(self):
        """
        Create a project template.
        Body can include:
        - name (required)
        - description
        - from_project_id: copy settings from an existing project
        - Or manual fields: production_type, production_style, fps, etc.
        """
        permissions.check_admin_permissions()
        data = request.json or {}

        name = data.get("name")
        if not name:
            return {"error": "Name is required"}, 400

        existing = ProjectTemplate.query.filter_by(name=name).first()
        if existing:
            return {"error": "Template with this name already exists"}, 400

        from_project_id = data.get("from_project_id")
        if from_project_id:
            project = Project.get(from_project_id)
            if project is None:
                return {"error": "Source project not found"}, 404

            task_type_ids = [
                str(tt.id) for tt in project.task_types
            ]
            asset_type_ids = [
                str(at.id) for at in project.asset_types
            ]
            task_status_ids = [
                str(ts.id) for ts in project.task_statuses
            ]

            template = ProjectTemplate.create(
                name=name,
                description=data.get("description", ""),
                production_type=project.production_type,
                production_style=str(project.production_style),
                fps=project.fps,
                ratio=project.ratio,
                resolution=project.resolution,
                task_type_ids=task_type_ids,
                asset_type_ids=asset_type_ids,
                task_status_ids=task_status_ids,
                data={
                    "max_retakes": project.max_retakes,
                    "homepage": project.homepage,
                }
            )
        else:
            template = ProjectTemplate.create(
                name=name,
                description=data.get("description", ""),
                production_type=data.get("production_type", "short"),
                production_style=data.get("production_style", "2d3d"),
                fps=data.get("fps", "25"),
                ratio=data.get("ratio", "16:9"),
                resolution=data.get("resolution", "1920x1080"),
                task_type_ids=data.get("task_type_ids", []),
                asset_type_ids=data.get("asset_type_ids", []),
                task_status_ids=data.get("task_status_ids", []),
                data=data.get("data", {})
            )

        return template.present(), 201


class ProjectTemplateResource(Resource):
    """
    Get, update or delete a single project template.
    """

    @jwt_required()
    def get(self, template_id):
        permissions.check_admin_permissions()
        template = ProjectTemplate.get(template_id)
        if template is None:
            return {"error": "Template not found"}, 404
        return template.present()

    @jwt_required()
    def put(self, template_id):
        permissions.check_admin_permissions()
        template = ProjectTemplate.get(template_id)
        if template is None:
            return {"error": "Template not found"}, 404

        data = request.json or {}
        updatable = [
            "name", "description", "production_type", "production_style",
            "fps", "ratio", "resolution", "task_type_ids",
            "asset_type_ids", "task_status_ids", "data"
        ]
        update_data = {k: v for k, v in data.items() if k in updatable}
        template.update(update_data)
        return template.present()

    @jwt_required()
    def delete(self, template_id):
        permissions.check_admin_permissions()
        template = ProjectTemplate.get(template_id)
        if template is None:
            return {"error": "Template not found"}, 404
        template.delete()
        return "", 204


class ProjectFromTemplateResource(Resource):
    """
    Create a new project from a template.
    """

    @jwt_required()
    def post(self, template_id):
        permissions.check_admin_permissions()
        template = ProjectTemplate.get(template_id)
        if template is None:
            return {"error": "Template not found"}, 404

        data = request.json or {}
        project_name = data.get("name")
        if not project_name:
            return {"error": "Project name is required"}, 400

        from zou.app.services import projects_service

        # Create the project
        project = Project.create(
            name=project_name,
            code=data.get("code", ""),
            description=data.get("description", ""),
            production_type=template.production_type,
            production_style=template.production_style,
            fps=template.fps,
            ratio=template.ratio,
            resolution=template.resolution,
            max_retakes=template.data.get("max_retakes", 0)
            if template.data else 0,
            homepage=template.data.get("homepage", "assets")
            if template.data else "assets",
        )

        # Apply task types
        from zou.app.models.task_type import TaskType
        for tt_id in (template.task_type_ids or []):
            tt = TaskType.get(tt_id)
            if tt:
                project.task_types.append(tt)

        # Apply asset types
        from zou.app.models.entity_type import EntityType
        for at_id in (template.asset_type_ids or []):
            at = EntityType.get(at_id)
            if at:
                project.asset_types.append(at)

        # Apply task statuses
        from zou.app.models.task_status import TaskStatus
        for ts_id in (template.task_status_ids or []):
            ts = TaskStatus.get(ts_id)
            if ts:
                project.task_statuses.append(ts)

        project.save()
        projects_service.clear_project_cache("")

        return project.serialize(), 201
