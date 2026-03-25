from flask_restful import Resource
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from zou.app.models.entity import Entity
from zou.app.models.task import Task
from zou.app.models.task_status import TaskStatus
from zou.app.models.project import Project
from zou.app.services import user_service


class ProductionDashboardResource(Resource):
    """
    Return dashboard statistics for a given project:
    - Total/completed tasks and completion rate
    - Asset counts by type
    - Shot/sequence counts
    - Task status breakdown
    - Team size
    """

    @jwt_required()
    def get(self, project_id):
        user_service.check_project_access(project_id)
        project = Project.get(project_id)
        if project is None:
            return {"error": "Project not found"}, 404

        # Task stats
        total_tasks = Task.query.filter(
            Task.project_id == project_id
        ).count()

        done_statuses = TaskStatus.query.filter(
            TaskStatus.is_done == True
        ).all()
        done_status_ids = [s.id for s in done_statuses]

        completed_tasks = Task.query.filter(
            Task.project_id == project_id,
            Task.task_status_id.in_(done_status_ids)
        ).count() if done_status_ids else 0

        # Task status breakdown
        status_breakdown = (
            Task.query
            .with_entities(
                TaskStatus.short_name,
                TaskStatus.color,
                TaskStatus.is_done,
                func.count(Task.id).label("count")
            )
            .filter(Task.project_id == project_id)
            .join(TaskStatus, TaskStatus.id == Task.task_status_id)
            .group_by(
                TaskStatus.short_name,
                TaskStatus.color,
                TaskStatus.is_done
            )
            .all()
        )

        task_statuses = [
            {
                "name": row.short_name,
                "color": row.color,
                "is_done": row.is_done,
                "count": row.count
            }
            for row in status_breakdown
        ]

        # Entity counts by type
        from zou.app.models.entity_type import EntityType
        shot_type_obj = EntityType.query.filter(
            EntityType.name == "Shot"
        ).first()
        sequence_type_obj = EntityType.query.filter(
            EntityType.name == "Sequence"
        ).first()
        episode_type_obj = EntityType.query.filter(
            EntityType.name == "Episode"
        ).first()

        # Exclude Shot/Sequence/Episode types for asset count
        excluded_type_ids = [
            t.id for t in [shot_type_obj, sequence_type_obj, episode_type_obj]
            if t is not None
        ]
        total_assets = Entity.query.filter(
            Entity.project_id == project_id,
            Entity.canceled == False,
            ~Entity.entity_type_id.in_(excluded_type_ids)
            if excluded_type_ids else True
        ).count()

        total_shots = 0
        total_sequences = 0
        if shot_type_obj:
            total_shots = Entity.query.filter(
                Entity.project_id == project_id,
                Entity.entity_type_id == shot_type_obj.id,
                Entity.canceled == False
            ).count()
        if sequence_type_obj:
            total_sequences = Entity.query.filter(
                Entity.project_id == project_id,
                Entity.entity_type_id == sequence_type_obj.id,
                Entity.canceled == False
            ).count()

        # Team size
        team_size = len(project.team) if project.team else 0

        # Completion rate
        completion_rate = 0
        if total_tasks > 0:
            completion_rate = round(
                (completed_tasks / total_tasks) * 100, 1
            )

        return {
            "project_id": str(project_id),
            "project_name": project.name,
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "completion_rate": completion_rate,
                "statuses": task_statuses
            },
            "assets": {
                "total": total_assets
            },
            "shots": {
                "total": total_shots,
                "sequences": total_sequences
            },
            "team": {
                "size": team_size
            }
        }
