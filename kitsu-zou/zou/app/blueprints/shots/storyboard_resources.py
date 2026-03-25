"""
分镜瀑布流 API

提供分镜瀑布流视图所需的优化查询、排序持久化、
负责人分配、任务状态流转、版本管理和批量操作。
"""

import io
import os
import tempfile
import zipfile

from flask import request, send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import aliased
from sqlalchemy import case, func

from zou.app import db
from zou.app.models.entity import Entity
from zou.app.models.preview_file import PreviewFile
from zou.app.models.project import Project
from zou.app.models.task import Task, TaskPersonLink
from zou.app.models.task_status import TaskStatus
from zou.app.models.task_type import TaskType
from zou.app.models.person import Person

from zou.app.mixin import ArgsMixin
from zou.app.services import (
    entities_service,
    files_service,
    persons_service,
    projects_service,
    shots_service,
    tasks_service,
    user_service,
)
from zou.app.stores import file_store
from zou.app.services.exception import (
    TaskNotFoundException,
    WrongParameterException,
)
from zou.app.utils import events, permissions


class StoryboardResource(Resource, ArgsMixin):
    """
    Return shots grouped by sequence, optimized for the storyboard
    waterfall panel.
    """

    @jwt_required()
    def get(self, project_id):
        """
        Get storyboard data
        ---
        tags:
        - Shots
        description: Return shots grouped by sequence with task summaries
          and assignee info, optimized for the storyboard waterfall view.
        parameters:
          - in: path
            name: project_id
            required: True
            type: string
            format: uuid
          - in: query
            name: episode_id
            required: False
            type: string
            format: uuid
          - in: query
            name: status
            required: False
            type: string
            enum: [standby, running, complete]
          - in: query
            name: assigned_to
            required: False
            type: string
            format: uuid
          - in: query
            name: sequence_id
            required: False
            type: string
            format: uuid
        responses:
            200:
                description: Storyboard data grouped by sequence
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        args = self.get_args(
            [
                ("episode_id", None),
                ("status", None),
                ("assigned_to", None),
                ("sequence_id", None),
            ]
        )

        shot_type = shots_service.get_shot_type()
        shot_type_id = shot_type["id"]

        Sequence = aliased(Entity, name="sequence")

        # Base query: shots for this project
        shot_query = (
            db.session.query(Entity)
            .filter(Entity.entity_type_id == shot_type_id)
            .filter(Entity.project_id == project_id)
            .join(Sequence, Entity.parent_id == Sequence.id)
        )

        # Filter by episode: sequences whose parent_id == episode_id
        if args["episode_id"]:
            shot_query = shot_query.filter(
                Sequence.parent_id == args["episode_id"]
            )

        # Filter by sequence
        if args["sequence_id"]:
            shot_query = shot_query.filter(
                Entity.parent_id == args["sequence_id"]
            )

        # Filter by shot status
        if args["status"]:
            shot_query = shot_query.filter(
                Entity.status == args["status"]
            )

        # Filter by assignee: shots that have at least one task assigned
        # to the given person
        if args["assigned_to"]:
            shot_query = shot_query.filter(
                Entity.id.in_(
                    db.session.query(Task.entity_id)
                    .join(
                        TaskPersonLink,
                        Task.id == TaskPersonLink.task_id,
                    )
                    .filter(
                        TaskPersonLink.person_id == args["assigned_to"]
                    )
                    .filter(Task.project_id == project_id)
                )
            )

        # Limit to assigned shots for vendor users
        if permissions.has_vendor_permissions():
            current_user = persons_service.get_current_user()
            shot_query = shot_query.filter(
                Entity.id.in_(
                    db.session.query(Task.entity_id)
                    .join(
                        TaskPersonLink,
                        Task.id == TaskPersonLink.task_id,
                    )
                    .filter(
                        TaskPersonLink.person_id == current_user["id"]
                    )
                    .filter(Task.project_id == project_id)
                )
            )

        shots = shot_query.all()

        if not shots:
            return {"sequences": [], "total_shots": 0}

        shot_ids = [shot.id for shot in shots]

        # Batch load preview file extensions for video detection
        preview_file_ids = [
            shot.preview_file_id
            for shot in shots
            if shot.preview_file_id
        ]
        pf_ext_map = {}
        if preview_file_ids:
            pf_rows = (
                db.session.query(
                    PreviewFile.id, PreviewFile.extension
                )
                .filter(PreviewFile.id.in_(preview_file_ids))
                .all()
            )
            pf_ext_map = {
                str(row.id): row.extension or "png"
                for row in pf_rows
            }

        # Batch load task counts and done counts per shot
        task_stats = (
            db.session.query(
                Task.entity_id,
                func.count(Task.id).label("task_count"),
                func.sum(
                    case(
                        (TaskStatus.is_done.is_(True), 1),
                        else_=0,
                    )
                ).label("tasks_done"),
            )
            .join(TaskStatus, Task.task_status_id == TaskStatus.id)
            .filter(Task.entity_id.in_(shot_ids))
            .group_by(Task.entity_id)
            .all()
        )
        task_stats_map = {
            str(row.entity_id): {
                "task_count": row.task_count,
                "tasks_done": int(row.tasks_done or 0),
            }
            for row in task_stats
        }

        # Batch load assignee info per shot (via tasks) — include IDs
        # and has_avatar for frontend avatar display
        assignee_rows = (
            db.session.query(
                Task.entity_id,
                Person.id.label("person_id"),
                Person.first_name,
                Person.last_name,
                Person.has_avatar,
            )
            .join(
                TaskPersonLink,
                Task.id == TaskPersonLink.task_id,
            )
            .join(Person, TaskPersonLink.person_id == Person.id)
            .filter(Task.entity_id.in_(shot_ids))
            .distinct()
            .all()
        )
        assignees_map = {}
        for row in assignee_rows:
            entity_id_str = str(row.entity_id)
            full_name = (
                f"{row.first_name} {row.last_name}".strip()
                if row.last_name
                else row.first_name
            )
            assignees_map.setdefault(entity_id_str, []).append(
                {
                    "id": str(row.person_id),
                    "name": full_name,
                    "has_avatar": row.has_avatar or False,
                }
            )

        # Batch load primary task per shot (first task by task_type name)
        # for status display on cards
        task_rows = (
            db.session.query(
                Task.entity_id,
                Task.id.label("task_id"),
                Task.task_status_id,
                Task.task_type_id,
                TaskStatus.name.label("status_name"),
                TaskStatus.short_name.label("status_short_name"),
                TaskStatus.color.label("status_color"),
                TaskStatus.is_done,
                TaskType.name.label("task_type_name"),
            )
            .join(TaskStatus, Task.task_status_id == TaskStatus.id)
            .join(TaskType, Task.task_type_id == TaskType.id)
            .filter(Task.entity_id.in_(shot_ids))
            .order_by(TaskType.name, Task.created_at)
            .all()
        )
        # Group tasks by shot — keep all for detail, pick first as primary
        tasks_by_shot = {}
        for row in task_rows:
            eid = str(row.entity_id)
            task_info = {
                "id": str(row.task_id),
                "task_type_id": str(row.task_type_id),
                "task_type_name": row.task_type_name,
                "task_status_id": str(row.task_status_id),
                "task_status_name": row.status_name,
                "task_status_short_name": row.status_short_name,
                "task_status_color": row.status_color or "#999999",
                "is_done": row.is_done or False,
            }
            tasks_by_shot.setdefault(eid, []).append(task_info)

        # Load sequences for grouping
        sequence_ids = list({shot.parent_id for shot in shots})
        sequences_raw = (
            Entity.query.filter(Entity.id.in_(sequence_ids))
            .order_by(Entity.name)
            .all()
        )
        sequence_map = {seq.id: seq for seq in sequences_raw}

        # Build response grouped by sequence
        sequences_data = {}
        for shot in shots:
            seq_id = str(shot.parent_id)
            if seq_id not in sequences_data:
                seq = sequence_map.get(shot.parent_id)
                seq_data = seq.data or {} if seq else {}
                sequences_data[seq_id] = {
                    "id": seq_id,
                    "name": seq.name if seq else "Unknown",
                    "description": (
                        seq.description or "" if seq else ""
                    ),
                    "sequence_order": seq_data.get(
                        "sequence_order", 0
                    ),
                    "shots": [],
                    # Stats will be computed after shots are added
                    "shot_count": 0,
                    "shots_done": 0,
                    "assignee_count": 0,
                }

            shot_data = shot.data or {}
            shot_id_str = str(shot.id)
            stats = task_stats_map.get(shot_id_str, {})

            shot_tasks = tasks_by_shot.get(shot_id_str, [])
            primary_task = shot_tasks[0] if shot_tasks else None

            sequences_data[seq_id]["shots"].append(
                {
                    "id": shot_id_str,
                    "name": shot.name,
                    "description": shot.description or "",
                    "preview_file_id": (
                        str(shot.preview_file_id)
                        if shot.preview_file_id
                        else None
                    ),
                    "preview_file_extension": pf_ext_map.get(
                        str(shot.preview_file_id), ""
                    ) if shot.preview_file_id else "",
                    "nb_frames": shot.nb_frames,
                    "frame_in": shot_data.get("frame_in"),
                    "frame_out": shot_data.get("frame_out"),
                    "fps": shot_data.get("fps"),
                    "status": shot.status.code
                    if hasattr(shot.status, "code")
                    else str(shot.status),
                    "canceled": shot.canceled or False,
                    "storyboard_order": shot_data.get(
                        "storyboard_order", 0
                    ),
                    "assignees": assignees_map.get(shot_id_str, []),
                    "task_count": stats.get("task_count", 0),
                    "tasks_done": stats.get("tasks_done", 0),
                    "tasks": shot_tasks,
                    "primary_task": primary_task,
                }
            )

        # Sort shots within each sequence and compute sequence stats
        for seq in sequences_data.values():
            seq["shots"].sort(
                key=lambda s: (s["storyboard_order"], s["name"])
            )
            seq["shot_count"] = len(seq["shots"])
            seq["shots_done"] = sum(
                1
                for s in seq["shots"]
                if s.get("primary_task", {})
                and s["primary_task"].get("is_done")
            )
            # Count unique assignees across all shots in sequence
            assignee_ids = set()
            for s in seq["shots"]:
                for a in s.get("assignees", []):
                    aid = a["id"] if isinstance(a, dict) else a
                    assignee_ids.add(aid)
            seq["assignee_count"] = len(assignee_ids)

        # Sort sequences by sequence_order then name
        sorted_sequences = sorted(
            sequences_data.values(),
            key=lambda s: (s["sequence_order"], s["name"]),
        )

        return {
            "sequences": sorted_sequences,
            "total_shots": len(shots),
        }


class StoryboardReorderResource(Resource):
    """
    Persist drag-and-drop sort order for the storyboard waterfall view.
    """

    @jwt_required()
    def put(self, project_id):
        """
        Reorder storyboard shots
        ---
        tags:
        - Shots
        description: Persist the drag-and-drop sort order for the
          storyboard waterfall panel. Updates each shot's data JSONB
          field with storyboard_order.
        parameters:
          - in: path
            name: project_id
            required: True
            type: string
            format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  shot_orders:
                    type: array
                    items:
                      type: object
                      properties:
                        shot_id:
                          type: string
                          format: uuid
                        order:
                          type: integer
                        sequence_id:
                          type: string
                          format: uuid
        responses:
            200:
                description: Sort order persisted
            400:
                description: Invalid body
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json
        if not data or "shot_orders" not in data:
            raise WrongParameterException(
                "Body must contain a shot_orders array."
            )

        shot_orders = data["shot_orders"]
        if not isinstance(shot_orders, list):
            raise WrongParameterException(
                "shot_orders must be an array."
            )

        updated = []
        for item in shot_orders:
            shot_id = item.get("shot_id")
            order = item.get("order")
            sequence_id = item.get("sequence_id")

            if shot_id is None or order is None:
                continue

            shot = Entity.get(shot_id)
            if shot is None:
                continue
            if str(shot.project_id) != project_id:
                continue

            shot_data = shot.data or {}
            shot_data["storyboard_order"] = order

            # Optionally update parent_id if sequence changed via drag
            update_dict = {"data": shot_data}
            if sequence_id is not None:
                update_dict["parent_id"] = sequence_id

            shot.update(update_dict)
            updated.append(shot_id)

        db.session.commit()

        return {
            "ok": True,
            "updated_count": len(updated),
        }


def _get_or_create_shot_task(shot, project_id):
    """
    Get the first task for a shot, or create one with the default
    task type and status if none exists.
    """
    task = (
        Task.query.filter_by(entity_id=shot.id)
        .order_by(Task.created_at)
        .first()
    )
    if task is not None:
        return task

    # Create a default task for this shot
    task_types = TaskType.query.filter_by(
        for_entity="Shot"
    ).order_by(TaskType.name).all()
    if not task_types:
        # Fallback: get any task type from the project
        project = Project.get(project_id)
        task_types = TaskType.query.order_by(TaskType.name).all()

    if not task_types:
        raise WrongParameterException(
            "No task types configured. Create a task type first."
        )

    task_type = task_types[0]
    default_status = tasks_service.get_default_status()
    task = Task.create(
        name="main",
        entity_id=shot.id,
        project_id=project_id,
        task_type_id=task_type.id,
        task_status_id=default_status["id"],
    )
    db.session.commit()
    return task


class StoryboardShotAssignResource(Resource):
    """
    Assign or remove persons from a storyboard shot's task.
    """

    @jwt_required()
    def put(self, project_id, shot_id):
        """
        Assign persons to a storyboard shot
        ---
        tags:
        - Storyboard
        description: >
            Set the assignees for a shot's primary task. Replaces all
            current assignees with the provided list. Pass an empty
            array to unassign everyone.
        parameters:
          - in: path
            name: project_id
            required: true
            type: string
            format: uuid
          - in: path
            name: shot_id
            required: true
            type: string
            format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - person_ids
                properties:
                  person_ids:
                    type: array
                    items:
                      type: string
                      format: uuid
                  task_id:
                    type: string
                    format: uuid
                    description: >
                        Optional specific task ID. If omitted, uses
                        the primary (first) task for the shot.
        responses:
            200:
                description: Assignees updated
            400:
                description: Invalid request
            404:
                description: Shot or task not found
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        person_ids = data.get("person_ids")
        if person_ids is None:
            raise WrongParameterException(
                "Body must contain a person_ids array."
            )

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException("Shot not found in project.")

        task_id = data.get("task_id")
        if task_id:
            task = Task.get(task_id)
            if task is None or str(task.entity_id) != shot_id:
                raise TaskNotFoundException
        else:
            task = _get_or_create_shot_task(shot, project_id)

        current_user = persons_service.get_current_user()

        # Replace assignees
        task.assignees = []
        for pid in person_ids:
            person = Person.get(pid)
            if person is not None:
                task.assignees.append(person)
        task.assigner_id = current_user["id"]
        task.save()
        db.session.commit()

        tasks_service.clear_task_cache(str(task.id))
        events.emit(
            "task:assign",
            {"task_id": task.id},
            project_id=project_id,
        )

        return {
            "ok": True,
            "task_id": str(task.id),
            "assignees": [
                {
                    "id": str(p.id),
                    "name": (
                        f"{p.first_name} {p.last_name}".strip()
                        if p.last_name
                        else p.first_name
                    ),
                    "has_avatar": p.has_avatar or False,
                }
                for p in task.assignees
            ],
        }


class StoryboardShotStatusResource(Resource):
    """
    Update the task status for a storyboard shot.
    """

    @jwt_required()
    def put(self, project_id, shot_id):
        """
        Update shot task status
        ---
        tags:
        - Storyboard
        description: >
            Change the status of a shot's primary task.
            Only managers or the task's assignees can change status.
        parameters:
          - in: path
            name: project_id
            required: true
            type: string
            format: uuid
          - in: path
            name: shot_id
            required: true
            type: string
            format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - task_status_id
                properties:
                  task_status_id:
                    type: string
                    format: uuid
                  task_id:
                    type: string
                    format: uuid
        responses:
            200:
                description: Status updated
            403:
                description: Not allowed to change status
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        data = request.json or {}
        new_status_id = data.get("task_status_id")
        if not new_status_id:
            raise WrongParameterException(
                "Body must contain task_status_id."
            )

        # Validate status exists
        new_status = TaskStatus.get(new_status_id)
        if new_status is None:
            raise WrongParameterException("Invalid task_status_id.")

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException("Shot not found in project.")

        task_id = data.get("task_id")
        if task_id:
            task = Task.get(task_id)
            if task is None or str(task.entity_id) != shot_id:
                raise TaskNotFoundException
        else:
            task = _get_or_create_shot_task(shot, project_id)

        # Permission: managers can always change, artists only their own
        current_user = persons_service.get_current_user()
        is_manager = permissions.has_manager_permissions()
        is_assignee = any(
            str(p.id) == current_user["id"] for p in task.assignees
        )

        if not is_manager and not is_assignee:
            raise WrongParameterException(
                "Only managers or assignees can change task status."
            )

        old_status_id = str(task.task_status_id)
        task.update({"task_status_id": new_status_id})
        task.save()
        db.session.commit()

        tasks_service.clear_task_cache(str(task.id))
        events.emit(
            "task:update",
            {"task_id": task.id},
            project_id=project_id,
        )

        return {
            "ok": True,
            "task_id": str(task.id),
            "old_status_id": old_status_id,
            "new_status_id": str(new_status_id),
            "task_status_name": new_status.name,
            "task_status_color": new_status.color or "#999999",
        }


class StoryboardBatchAssignResource(Resource):
    """
    Batch-assign persons to multiple storyboard shots at once.
    """

    @jwt_required()
    def put(self, project_id):
        """
        Batch assign shots
        ---
        tags:
        - Storyboard
        description: >
            Assign the same set of persons to multiple shots at once.
            Requires manager permissions.
        parameters:
          - in: path
            name: project_id
            required: true
            type: string
            format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - shot_ids
                  - person_ids
                properties:
                  shot_ids:
                    type: array
                    items:
                      type: string
                      format: uuid
                  person_ids:
                    type: array
                    items:
                      type: string
                      format: uuid
        responses:
            200:
                description: Batch assignment complete
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        shot_ids = data.get("shot_ids", [])
        person_ids = data.get("person_ids", [])

        if not shot_ids:
            raise WrongParameterException("shot_ids must not be empty.")

        # Resolve persons once
        persons = []
        for pid in person_ids:
            person = Person.get(pid)
            if person is not None:
                persons.append(person)

        current_user = persons_service.get_current_user()
        updated = []

        for sid in shot_ids:
            shot = Entity.get(sid)
            if shot is None or str(shot.project_id) != project_id:
                continue

            task = _get_or_create_shot_task(shot, project_id)
            task.assignees = list(persons)
            task.assigner_id = current_user["id"]
            task.save()
            tasks_service.clear_task_cache(str(task.id))
            updated.append(str(sid))

        db.session.commit()

        for sid in updated:
            events.emit(
                "task:assign",
                {"shot_id": sid},
                project_id=project_id,
            )

        return {
            "ok": True,
            "updated_count": len(updated),
        }


class StoryboardTaskStatusesResource(Resource):
    """
    Return all task statuses available for the storyboard view.
    """

    @jwt_required()
    def get(self, project_id):
        """
        Get task statuses for storyboard
        ---
        tags:
        - Storyboard
        description: >
            Return all task statuses available in this project,
            ordered by name, for the storyboard status selector.
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        statuses = (
            TaskStatus.query
            .order_by(TaskStatus.priority.desc(), TaskStatus.name)
            .all()
        )

        return [
            {
                "id": str(s.id),
                "name": s.name,
                "short_name": s.short_name,
                "color": s.color or "#999999",
                "is_done": s.is_done or False,
                "is_default": s.is_default or False,
                "is_retake": s.is_retake or False,
            }
            for s in statuses
        ]


class StoryboardReorderSequencesResource(Resource):
    """
    Persist drag-and-drop sort order for sequences in the storyboard view.
    """

    @jwt_required()
    def put(self, project_id):
        """
        Reorder storyboard sequences
        ---
        tags:
        - Storyboard
        description: >
            Persist the drag-and-drop sort order for sequences.
            Updates each sequence's data JSONB field with
            sequence_order.
        parameters:
          - in: path
            name: project_id
            required: true
            type: string
            format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  sequence_orders:
                    type: array
                    items:
                      type: object
                      properties:
                        sequence_id:
                          type: string
                          format: uuid
                        order:
                          type: integer
        responses:
            200:
                description: Sort order persisted
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json
        if not data or "sequence_orders" not in data:
            raise WrongParameterException(
                "Body must contain a sequence_orders array."
            )

        sequence_orders = data["sequence_orders"]
        if not isinstance(sequence_orders, list):
            raise WrongParameterException(
                "sequence_orders must be an array."
            )

        updated = []
        for item in sequence_orders:
            seq_id = item.get("sequence_id")
            order = item.get("order")
            if seq_id is None or order is None:
                continue

            seq = Entity.get(seq_id)
            if seq is None:
                continue
            if str(seq.project_id) != project_id:
                continue

            seq_data = seq.data or {}
            seq_data["sequence_order"] = order
            seq.update({"data": seq_data})
            updated.append(seq_id)

        db.session.commit()

        return {
            "ok": True,
            "updated_count": len(updated),
        }


class StoryboardSequenceResource(Resource):
    """
    Create, update, or delete a sequence from the storyboard view.
    """

    @jwt_required()
    def post(self, project_id):
        """
        Create a sequence from storyboard
        ---
        tags:
        - Storyboard
        description: >
            Create a new sequence for the storyboard view.
        parameters:
          - in: path
            name: project_id
            required: true
            type: string
            format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - name
                properties:
                  name:
                    type: string
                  description:
                    type: string
                  episode_id:
                    type: string
                    format: uuid
        responses:
            201:
                description: Sequence created
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        name = data.get("name")
        if not name:
            raise WrongParameterException("name is required.")

        description = data.get("description", "")
        episode_id = data.get("episode_id")

        current_user = persons_service.get_current_user()
        sequence = shots_service.create_sequence(
            project_id,
            episode_id,
            name,
            description=description,
            created_by=current_user["id"],
        )
        return sequence, 201

    @jwt_required()
    def put(self, project_id, sequence_id=None):
        """
        Update a sequence
        ---
        tags:
        - Storyboard
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        if not sequence_id:
            raise WrongParameterException("sequence_id is required.")

        seq = Entity.get(sequence_id)
        if seq is None or str(seq.project_id) != project_id:
            raise WrongParameterException(
                "Sequence not found in project."
            )

        data = request.json or {}
        update_dict = {}
        if "name" in data:
            update_dict["name"] = data["name"]
        if "description" in data:
            update_dict["description"] = data["description"]

        if update_dict:
            seq.update(update_dict)
            db.session.commit()

        return {
            "id": str(seq.id),
            "name": seq.name,
            "description": seq.description or "",
        }

    @jwt_required()
    def delete(self, project_id, sequence_id=None):
        """
        Delete a sequence (only if empty)
        ---
        tags:
        - Storyboard
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        if not sequence_id:
            raise WrongParameterException("sequence_id is required.")

        seq = Entity.get(sequence_id)
        if seq is None or str(seq.project_id) != project_id:
            raise WrongParameterException(
                "Sequence not found in project."
            )

        # Check if sequence has shots
        shot_type = shots_service.get_shot_type()
        child_count = (
            Entity.query.filter_by(
                parent_id=seq.id,
                entity_type_id=shot_type["id"],
            )
            .count()
        )
        if child_count > 0:
            raise WrongParameterException(
                f"无法删除：该场景下还有 {child_count} 个分镜。"
                "请先移动或删除所有分镜。"
            )

        seq.delete()
        db.session.commit()

        events.emit(
            "sequence:delete",
            {"sequence_id": sequence_id},
            project_id=project_id,
        )

        return {"ok": True}


class StoryboardShotVersionsResource(Resource):
    """
    List all preview file versions for a storyboard shot.
    """

    @jwt_required()
    def get(self, project_id, shot_id):
        """
        Get shot preview versions
        ---
        tags:
        - Storyboard
        description: >
            Return all preview file revisions for a shot, ordered by
            revision descending. Includes thumbnail URLs, upload date,
            uploader info, and whether each is the current active
            preview.
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException(
                "Shot not found in project."
            )

        # Get all preview files for this shot's tasks
        tasks = Task.query.filter_by(entity_id=shot_id).all()
        task_ids = [t.id for t in tasks]

        if not task_ids:
            return {"versions": [], "current_preview_file_id": None}

        previews = (
            PreviewFile.query.filter(
                PreviewFile.task_id.in_(task_ids)
            )
            .order_by(PreviewFile.revision.desc())
            .all()
        )

        current_id = (
            str(shot.preview_file_id) if shot.preview_file_id else None
        )

        versions = []
        for pf in previews:
            uploader = None
            if pf.person_id:
                try:
                    person = Person.get(pf.person_id)
                    if person:
                        uploader = {
                            "id": str(person.id),
                            "name": (
                                f"{person.first_name} "
                                f"{person.last_name}".strip()
                                if person.last_name
                                else person.first_name
                            ),
                        }
                except Exception:
                    pass

            versions.append(
                {
                    "id": str(pf.id),
                    "revision": pf.revision,
                    "status": pf.status or "ready",
                    "extension": pf.extension,
                    "original_name": pf.original_name,
                    "file_size": pf.file_size,
                    "width": pf.width,
                    "height": pf.height,
                    "created_at": (
                        pf.created_at.isoformat()
                        if pf.created_at
                        else None
                    ),
                    "is_current": str(pf.id) == current_id,
                    "uploader": uploader,
                    "thumbnail_url": (
                        f"/api/pictures/thumbnails-square/"
                        f"preview-files/{pf.id}.png"
                    ),
                }
            )

        return {
            "versions": versions,
            "current_preview_file_id": current_id,
        }


class StoryboardShotVersionUploadResource(Resource):
    """
    Create a new preview file revision for a storyboard shot.
    The actual file upload is a two-step process:
    1. This endpoint creates the PreviewFile record (returns its ID)
    2. Client uploads the file to POST /api/data/preview-files/<id>
    """

    @jwt_required()
    def post(self, project_id, shot_id):
        """
        Create a new version for a shot
        ---
        tags:
        - Storyboard
        description: >
            Create a new PreviewFile record for the shot's primary
            task with the next revision number. After creation, upload
            the actual file to POST /api/data/preview-files/<id>.
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  name:
                    type: string
                    description: Display name (defaults to shot name)
                  extension:
                    type: string
                    default: png
                  set_as_current:
                    type: boolean
                    default: true
        responses:
            201:
                description: PreviewFile record created
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException(
                "Shot not found in project."
            )

        task = _get_or_create_shot_task(shot, project_id)

        data = request.json or {}
        name = data.get("name", shot.name)
        extension = data.get("extension", "png")
        set_as_current = data.get("set_as_current", True)

        current_user = persons_service.get_current_user()
        next_revision = tasks_service.get_next_preview_revision(
            str(task.id)
        )

        preview_file = files_service.create_preview_file_raw(
            name=name,
            revision=next_revision,
            task_id=str(task.id),
            person_id=current_user["id"],
            source="webgui",
            extension=extension,
            position=1,
        )
        db.session.commit()

        if set_as_current:
            entities_service.update_entity_preview(
                shot_id, str(preview_file.id)
            )

        return {
            "id": str(preview_file.id),
            "revision": preview_file.revision,
            "upload_url": (
                f"/api/data/preview-files/{preview_file.id}"
            ),
        }, 201


class StoryboardShotVersionSetActiveResource(Resource):
    """
    Set a specific preview file version as the active one for a shot.
    """

    @jwt_required()
    def put(self, project_id, shot_id):
        """
        Set active preview version (rollback)
        ---
        tags:
        - Storyboard
        description: >
            Change the shot's active preview to a specific version.
            This is the "rollback" operation.
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - preview_file_id
                properties:
                  preview_file_id:
                    type: string
                    format: uuid
        responses:
            200:
                description: Active preview updated
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException(
                "Shot not found in project."
            )

        data = request.json or {}
        preview_file_id = data.get("preview_file_id")
        if not preview_file_id:
            raise WrongParameterException(
                "preview_file_id is required."
            )

        # Verify the preview file belongs to this shot's tasks
        pf = PreviewFile.get(preview_file_id)
        if pf is None:
            raise WrongParameterException(
                "Preview file not found."
            )

        task = Task.get(pf.task_id)
        if task is None or str(task.entity_id) != shot_id:
            raise WrongParameterException(
                "Preview file does not belong to this shot."
            )

        entities_service.update_entity_preview(
            shot_id, preview_file_id
        )

        return {
            "ok": True,
            "preview_file_id": preview_file_id,
            "revision": pf.revision,
        }


class StoryboardBatchStatusResource(Resource):
    """
    Batch-update the task status for multiple storyboard shots.
    """

    @jwt_required()
    def put(self, project_id):
        """
        Batch update shot task statuses
        ---
        tags:
        - Storyboard
        description: >
            Set the same task status for multiple shots at once.
            Requires manager permissions.
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        shot_ids = data.get("shot_ids", [])
        task_status_id = data.get("task_status_id")

        if not shot_ids:
            raise WrongParameterException("shot_ids must not be empty.")
        if not task_status_id:
            raise WrongParameterException("task_status_id is required.")

        new_status = TaskStatus.get(task_status_id)
        if new_status is None:
            raise WrongParameterException("Invalid task_status_id.")

        updated = []
        for sid in shot_ids:
            shot = Entity.get(sid)
            if shot is None or str(shot.project_id) != project_id:
                continue

            task = _get_or_create_shot_task(shot, project_id)
            task.update({"task_status_id": task_status_id})
            task.save()
            tasks_service.clear_task_cache(str(task.id))
            updated.append(sid)

        db.session.commit()

        return {
            "ok": True,
            "updated_count": len(updated),
            "task_status_name": new_status.name,
        }


class StoryboardBatchDeleteResource(Resource):
    """
    Batch-delete storyboard shots (soft-cancel or hard-delete).
    """

    @jwt_required()
    def put(self, project_id):
        """
        Batch delete/cancel shots
        ---
        tags:
        - Storyboard
        description: >
            Mark multiple shots as canceled. Uses soft-cancel by
            default (sets canceled=True). Pass hard_delete=true to
            permanently remove (manager only).
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        data = request.json or {}
        shot_ids = data.get("shot_ids", [])
        hard_delete = data.get("hard_delete", False)

        if not shot_ids:
            raise WrongParameterException("shot_ids must not be empty.")

        deleted = []
        for sid in shot_ids:
            shot = Entity.get(sid)
            if shot is None or str(shot.project_id) != project_id:
                continue

            if hard_delete:
                # Delete tasks first
                tasks = Task.query.filter_by(entity_id=shot.id).all()
                for t in tasks:
                    t.delete()
                shot.delete()
            else:
                shot.update({"canceled": True})

            deleted.append(sid)

        db.session.commit()

        return {
            "ok": True,
            "deleted_count": len(deleted),
            "hard_delete": hard_delete,
        }


class StoryboardBatchDownloadResource(Resource):
    """
    Download preview images for selected shots as a ZIP archive.
    """

    @jwt_required()
    def post(self, project_id):
        """
        Batch download shot previews as ZIP
        ---
        tags:
        - Storyboard
        description: >
            Package original preview files for selected shots into
            a ZIP archive. Returns the ZIP file directly.
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        data = request.json or {}
        shot_ids = data.get("shot_ids", [])

        if not shot_ids:
            raise WrongParameterException("shot_ids must not be empty.")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for sid in shot_ids:
                shot = Entity.get(sid)
                if shot is None or str(shot.project_id) != project_id:
                    continue
                if not shot.preview_file_id:
                    continue

                pf = PreviewFile.get(shot.preview_file_id)
                if pf is None:
                    continue

                ext = pf.extension or "png"
                prefix = "originals"
                try:
                    file_data = file_store.read_picture(
                        prefix, str(pf.id)
                    )
                    filename = f"{shot.name}.{ext}"
                    zf.writestr(filename, file_data)
                except Exception:
                    # Skip files that can't be read
                    pass

        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name="storyboard-export.zip",
        )


class StoryboardBatchUploadResource(Resource):
    """
    Batch-upload preview images for multiple shots.
    Files are matched to shots by filename (e.g., SH010.png → shot
    named SH010) or by order if no name match is found.
    """

    @jwt_required()
    def post(self, project_id):
        """
        Batch upload shot previews
        ---
        tags:
        - Storyboard
        description: >
            Upload multiple image files. Each file is matched to a
            shot by filename (stem must match shot name). Unmatched
            files are skipped. Returns a report of matched/skipped.
        """
        projects_service.get_project(project_id)
        user_service.check_manager_project_access(project_id)

        files = request.files.getlist("files")
        if not files:
            raise WrongParameterException(
                "No files uploaded. Use multipart field 'files'."
            )

        # Optional: restrict to specific sequence
        sequence_id = request.form.get("sequence_id")

        # Load all shots for this project
        shot_type = shots_service.get_shot_type()
        shot_query = Entity.query.filter_by(
            entity_type_id=shot_type["id"],
            project_id=project_id,
        )
        if sequence_id:
            shot_query = shot_query.filter_by(parent_id=sequence_id)

        all_shots = shot_query.all()
        shot_name_map = {s.name.lower(): s for s in all_shots}

        current_user = persons_service.get_current_user()
        matched = []
        skipped = []

        for f in files:
            # Extract stem from filename
            original_name = f.filename or ""
            stem = original_name.rsplit(".", 1)[0] if "." in original_name else original_name
            ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else "png"

            shot = shot_name_map.get(stem.lower())
            if shot is None:
                skipped.append(original_name)
                continue

            # Create preview file record
            task = _get_or_create_shot_task(shot, project_id)
            next_rev = tasks_service.get_next_preview_revision(
                str(task.id)
            )
            pf = files_service.create_preview_file_raw(
                name=shot.name,
                revision=next_rev,
                task_id=str(task.id),
                person_id=current_user["id"],
                source="webgui",
                extension=ext,
                position=1,
            )
            db.session.flush()

            # Save file to temp, then store via add_picture
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=f".{ext}")
            try:
                with os.fdopen(tmp_fd, "wb") as tmp_file:
                    tmp_file.write(f.read())
                file_store.add_picture("originals", str(pf.id), tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            # Update preview status and entity
            pf.update({"status": "ready"})
            entities_service.update_entity_preview(
                str(shot.id), str(pf.id)
            )

            matched.append(
                {
                    "filename": original_name,
                    "shot_name": shot.name,
                    "shot_id": str(shot.id),
                    "preview_file_id": str(pf.id),
                    "revision": pf.revision,
                }
            )

        db.session.commit()

        return {
            "ok": True,
            "matched_count": len(matched),
            "skipped_count": len(skipped),
            "matched": matched,
            "skipped": skipped,
        }


class StoryboardShotTimingResource(Resource):
    """
    Update timing data (nb_frames, frame_in, frame_out, fps)
    for a single storyboard shot.
    """

    @jwt_required()
    def put(self, project_id, shot_id):
        """
        Update shot timing
        ---
        tags:
        - Storyboard
        description: >
            Update the timing information for a shot. nb_frames is stored
            as a direct Entity column; frame_in, frame_out, and fps are
            stored in Entity.data (JSONB).
        parameters:
          - in: path
            name: project_id
            required: true
            type: string
            format: uuid
          - in: path
            name: shot_id
            required: true
            type: string
            format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  nb_frames:
                    type: integer
                  frame_in:
                    type: integer
                  frame_out:
                    type: integer
                  fps:
                    type: number
        responses:
            200:
                description: Timing updated
            404:
                description: Shot not found
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException("Shot not found in project.")

        data = request.json or {}

        # Update nb_frames (direct column)
        if "nb_frames" in data:
            shot.nb_frames = data["nb_frames"]

        # Update frame_in, frame_out, fps in Entity.data JSONB
        shot_data = dict(shot.data) if shot.data else {}
        for key in ("frame_in", "frame_out", "fps"):
            if key in data:
                shot_data[key] = data[key]
        shot.data = shot_data

        shot.save()
        db.session.commit()

        return {
            "ok": True,
            "shot_id": str(shot.id),
            "nb_frames": shot.nb_frames,
            "frame_in": shot_data.get("frame_in"),
            "frame_out": shot_data.get("frame_out"),
            "fps": shot_data.get("fps"),
        }


class StoryboardBatchTimingResource(Resource):
    """
    Batch-update timing data for multiple storyboard shots at once.
    Useful for saving positions after timeline drag operations.
    """

    @jwt_required()
    def put(self, project_id):
        """
        Batch update shot timing
        ---
        tags:
        - Storyboard
        description: >
            Update timing data for multiple shots in a single request.
            Each entry may include nb_frames, frame_in, frame_out.
        parameters:
          - in: path
            name: project_id
            required: true
            type: string
            format: uuid
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - shots
                properties:
                  shots:
                    type: array
                    items:
                      type: object
                      required:
                        - shot_id
                      properties:
                        shot_id:
                          type: string
                          format: uuid
                        nb_frames:
                          type: integer
                        frame_in:
                          type: integer
                        frame_out:
                          type: integer
        responses:
            200:
                description: Batch timing updated
            400:
                description: Invalid request
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        data = request.json or {}
        shots_data = data.get("shots")
        if not shots_data or not isinstance(shots_data, list):
            raise WrongParameterException(
                "Body must contain a shots array."
            )

        updated = []
        errors = []

        for entry in shots_data:
            sid = entry.get("shot_id")
            if not sid:
                errors.append({"error": "Missing shot_id in entry."})
                continue

            shot = Entity.get(sid)
            if shot is None or str(shot.project_id) != project_id:
                errors.append(
                    {"shot_id": sid, "error": "Shot not found in project."}
                )
                continue

            if "nb_frames" in entry:
                shot.nb_frames = entry["nb_frames"]

            shot_data = dict(shot.data) if shot.data else {}
            for key in ("frame_in", "frame_out"):
                if key in entry:
                    shot_data[key] = entry[key]
            shot.data = shot_data

            shot.save()

            updated.append(
                {
                    "shot_id": str(shot.id),
                    "nb_frames": shot.nb_frames,
                    "frame_in": shot_data.get("frame_in"),
                    "frame_out": shot_data.get("frame_out"),
                }
            )

        db.session.commit()

        return {
            "ok": True,
            "updated_count": len(updated),
            "error_count": len(errors),
            "updated": updated,
            "errors": errors,
        }
