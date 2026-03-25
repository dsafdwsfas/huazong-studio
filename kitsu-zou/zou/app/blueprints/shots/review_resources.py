"""
Storyboard review convenience API

Provides review history, review actions (approve/reject/submit/comment),
and review status listing for the storyboard panel.
"""

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app import db
from zou.app.models.comment import Comment
from zou.app.models.entity import Entity
from zou.app.models.person import Person
from zou.app.models.task import Task
from zou.app.models.task_status import TaskStatus

from zou.app.services import (
    comments_service,
    persons_service,
    projects_service,
    user_service,
)
from zou.app.services.exception import (
    WrongParameterException,
)


def _action_from_status(task_status):
    """Derive a review action label from a TaskStatus row."""
    if task_status is None:
        return "comment"
    if task_status.is_done:
        return "approve"
    if task_status.is_retake:
        return "reject"
    if task_status.is_feedback_request:
        return "submit"
    return "comment"


def _serialize_status(ts):
    """Serialize a TaskStatus model instance to a dict."""
    return {
        "id": str(ts.id),
        "name": ts.name,
        "short_name": ts.short_name,
        "color": ts.color or "#999999",
        "is_done": ts.is_done or False,
        "is_retake": ts.is_retake or False,
        "is_feedback_request": ts.is_feedback_request or False,
    }


class StoryboardReviewResource(Resource):
    """
    GET /api/data/projects/<project_id>/storyboard/shots/<shot_id>/reviews
        Return the review history for a shot.

    POST /api/data/projects/<project_id>/storyboard/shots/<shot_id>/reviews
        Create a review action (approve / reject / submit / comment).
    """

    @jwt_required()
    def get(self, project_id, shot_id):
        """
        Get review history for a storyboard shot
        ---
        tags:
        - Storyboard
        description: >
            Return all comments across the shot's tasks, enriched with
            review action labels derived from the linked task status.
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
        responses:
            200:
                description: Review history
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException("Shot not found in this project.")

        # All tasks belonging to this shot
        tasks = Task.query.filter_by(entity_id=shot.id).all()
        if not tasks:
            return {
                "shot_id": str(shot.id),
                "shot_name": shot.name,
                "task_id": None,
                "current_status": None,
                "reviews": [],
                "stats": {
                    "submit_count": 0,
                    "reject_count": 0,
                    "approve_count": 0,
                    "comment_count": 0,
                    "retake_count": 0,
                },
            }

        task_ids = [t.id for t in tasks]
        primary_task = tasks[0]

        # Current status of primary task
        current_ts = TaskStatus.get(primary_task.task_status_id)

        # All comments on these tasks, newest first
        comments = (
            Comment.query
            .filter(Comment.object_id.in_(task_ids))
            .filter_by(object_type="Task")
            .order_by(Comment.created_at.desc())
            .all()
        )

        # Pre-load persons and statuses referenced by comments
        person_ids = {c.person_id for c in comments}
        persons_map = {}
        if person_ids:
            for p in Person.query.filter(Person.id.in_(person_ids)).all():
                persons_map[p.id] = p

        status_ids = {c.task_status_id for c in comments if c.task_status_id}
        statuses_map = {}
        if status_ids:
            for s in TaskStatus.query.filter(
                TaskStatus.id.in_(status_ids)
            ).all():
                statuses_map[s.id] = s

        # Build reviews list and stats
        reviews = []
        stats = {
            "submit_count": 0,
            "reject_count": 0,
            "approve_count": 0,
            "comment_count": 0,
            "retake_count": 0,
        }

        for c in comments:
            ts = statuses_map.get(c.task_status_id)
            action = _action_from_status(ts)

            if action == "approve":
                stats["approve_count"] += 1
            elif action == "reject":
                stats["reject_count"] += 1
                stats["retake_count"] += 1
            elif action == "submit":
                stats["submit_count"] += 1
            else:
                stats["comment_count"] += 1

            person = persons_map.get(c.person_id)
            reviews.append(
                {
                    "id": str(c.id),
                    "author": {
                        "id": str(person.id),
                        "name": (
                            f"{person.first_name} {person.last_name}".strip()
                            if person
                            else "Unknown"
                        ),
                        "has_avatar": bool(person.has_avatar)
                        if person
                        else False,
                    },
                    "created_at": (
                        c.created_at.isoformat() if c.created_at else None
                    ),
                    "text": c.text or "",
                    "action": action,
                    "task_status": _serialize_status(ts) if ts else None,
                    "attachments": [],
                }
            )

        return {
            "shot_id": str(shot.id),
            "shot_name": shot.name,
            "task_id": str(primary_task.id),
            "current_status": (
                _serialize_status(current_ts) if current_ts else None
            ),
            "reviews": reviews,
            "stats": stats,
        }

    @jwt_required()
    def post(self, project_id, shot_id):
        """
        Create a review action on a storyboard shot
        ---
        tags:
        - Storyboard
        description: >
            Create a comment with an associated task status change.
            Wraps comments_service.create_comment() so that notifications
            and events fire correctly.
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
                  - action
                  - text
                properties:
                  action:
                    type: string
                    enum: [approve, reject, submit, comment]
                  text:
                    type: string
                  task_id:
                    type: string
                    format: uuid
        responses:
            201:
                description: Review created
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        shot = Entity.get(shot_id)
        if shot is None or str(shot.project_id) != project_id:
            raise WrongParameterException("Shot not found in this project.")

        data = request.json or {}
        action = data.get("action")
        text = data.get("text")
        task_id = data.get("task_id")

        if not action or action not in (
            "approve",
            "reject",
            "submit",
            "comment",
        ):
            raise WrongParameterException(
                "action must be one of: approve, reject, submit, comment"
            )
        if not text:
            raise WrongParameterException("text is required.")

        # Resolve task
        if task_id:
            task = Task.get(task_id)
            if task is None or str(task.entity_id) != shot_id:
                raise WrongParameterException(
                    "task_id does not belong to this shot."
                )
        else:
            task = (
                Task.query.filter_by(entity_id=shot.id)
                .first()
            )
            if task is None:
                raise WrongParameterException(
                    "No task found for this shot."
                )

        # Resolve target status based on action
        if action == "comment":
            target_status_id = str(task.task_status_id)
        else:
            status_filter = {}
            if action == "approve":
                status_filter["is_done"] = True
            elif action == "reject":
                status_filter["is_retake"] = True
            elif action == "submit":
                status_filter["is_feedback_request"] = True

            target_status = (
                TaskStatus.query.filter_by(**status_filter).first()
            )
            if target_status is None:
                raise WrongParameterException(
                    f"No task status found for action '{action}'."
                )
            target_status_id = str(target_status.id)

        current_user = persons_service.get_current_user()

        comment = comments_service.create_comment(
            person_id=current_user["id"],
            task_id=str(task.id),
            task_status_id=target_status_id,
            text=text,
        )

        return {
            "id": comment["id"],
            "action": action,
            "text": text,
            "task_id": str(task.id),
            "task_status_id": target_status_id,
            "created_at": comment.get("created_at"),
        }, 201


class StoryboardReviewStatusesResource(Resource):
    """
    GET /api/data/projects/<project_id>/storyboard/review-statuses

    Return task statuses grouped by review action type.
    """

    @jwt_required()
    def get(self, project_id):
        """
        Get review-related task statuses
        ---
        tags:
        - Storyboard
        description: >
            Return all task statuses categorised into approve, reject,
            submit, and a full list — for building review action buttons.
        parameters:
          - in: path
            name: project_id
            required: true
            type: string
            format: uuid
        responses:
            200:
                description: Review statuses
        """
        projects_service.get_project(project_id)
        user_service.check_project_access(project_id)

        statuses = (
            TaskStatus.query
            .order_by(TaskStatus.priority.desc(), TaskStatus.name)
            .all()
        )

        approve_statuses = []
        reject_statuses = []
        submit_statuses = []
        all_statuses = []

        for s in statuses:
            serialized = _serialize_status(s)
            all_statuses.append(serialized)
            if s.is_done:
                approve_statuses.append(serialized)
            if s.is_retake:
                reject_statuses.append(serialized)
            if s.is_feedback_request:
                submit_statuses.append(serialized)

        return {
            "approve_statuses": approve_statuses,
            "reject_statuses": reject_statuses,
            "submit_statuses": submit_statuses,
            "all_statuses": all_statuses,
        }
