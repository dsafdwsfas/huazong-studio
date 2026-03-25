"""
资产审核 API Resources

提供审核队列、提交审核、通过/驳回/请求修改、批量操作等端点。
"""

import logging

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from zou.app.services import persons_service
from zou.app.services import asset_review_service
from zou.app.services.exception import WrongParameterException
from zou.app.utils import permissions

logger = logging.getLogger(__name__)


class AssetReviewQueueResource(Resource):
    """
    GET /data/asset-reviews/queue?status=pending_review&page=1&per_page=20

    获取审核队列。需要 manager/admin 权限。
    """

    @jwt_required()
    def get(self):
        permissions.check_manager_permissions()
        status = request.args.get("status")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        if per_page > 100:
            per_page = 100
        return asset_review_service.get_review_queue(
            status=status, page=page, per_page=per_page
        ), 200


class AssetReviewStatsResource(Resource):
    """
    GET /data/asset-reviews/stats

    审核统计。需要 manager/admin 权限。
    """

    @jwt_required()
    def get(self):
        permissions.check_manager_permissions()
        return asset_review_service.get_review_stats(), 200


class AssetSubmitReviewResource(Resource):
    """
    POST /data/global-assets/<asset_id>/submit-review

    提交资产审核。普通用户可操作。
    Body: {comment?: string}
    """

    @jwt_required()
    def post(self, asset_id):
        data = request.json or {}
        current_user = persons_service.get_current_user()
        review = asset_review_service.submit_for_review(
            asset_id=asset_id,
            submitter_id=current_user["id"],
            comment=data.get("comment"),
        )
        return review, 201


class AssetReviewApproveResource(Resource):
    """
    PUT /data/asset-reviews/<review_id>/approve

    通过审核。需要 manager/admin 权限。
    Body: {comment?: string}
    """

    @jwt_required()
    def put(self, review_id):
        permissions.check_manager_permissions()
        data = request.json or {}
        current_user = persons_service.get_current_user()
        review = asset_review_service.approve_asset(
            review_id=review_id,
            reviewer_id=current_user["id"],
            comment=data.get("comment"),
        )
        return review, 200


class AssetReviewRejectResource(Resource):
    """
    PUT /data/asset-reviews/<review_id>/reject

    驳回审核。需要 manager/admin 权限。
    Body: {comment: string}  (必填)
    """

    @jwt_required()
    def put(self, review_id):
        permissions.check_manager_permissions()
        data = request.json or {}
        current_user = persons_service.get_current_user()
        review = asset_review_service.reject_asset(
            review_id=review_id,
            reviewer_id=current_user["id"],
            comment=data.get("comment"),
        )
        return review, 200


class AssetReviewRevisionResource(Resource):
    """
    PUT /data/asset-reviews/<review_id>/request-revision

    请求修改。需要 manager/admin 权限。
    Body: {comment: string}  (必填)
    """

    @jwt_required()
    def put(self, review_id):
        permissions.check_manager_permissions()
        data = request.json or {}
        current_user = persons_service.get_current_user()
        review = asset_review_service.request_revision(
            review_id=review_id,
            reviewer_id=current_user["id"],
            comment=data.get("comment"),
        )
        return review, 200


class AssetReviewResource(Resource):
    """
    GET /data/asset-reviews/<review_id>

    获取审核详情。
    """

    @jwt_required()
    def get(self, review_id):
        return asset_review_service.get_review(review_id), 200


class AssetReviewHistoryResource(Resource):
    """
    GET /data/global-assets/<asset_id>/reviews

    获取资产的审核历史。
    """

    @jwt_required()
    def get(self, asset_id):
        return asset_review_service.get_asset_reviews(asset_id), 200


class MySubmissionsResource(Resource):
    """
    GET /data/asset-reviews/my-submissions?status=&page=1&per_page=20

    获取当前用户提交的审核列表。
    """

    @jwt_required()
    def get(self):
        current_user = persons_service.get_current_user()
        status = request.args.get("status")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        if per_page > 100:
            per_page = 100
        return asset_review_service.get_my_submissions(
            person_id=current_user["id"],
            status=status,
            page=page,
            per_page=per_page,
        ), 200


class AssetReviewBatchApproveResource(Resource):
    """
    POST /data/asset-reviews/batch-approve

    批量通过审核。需要 manager/admin 权限。
    Body: {review_ids: string[], comment?: string}
    """

    @jwt_required()
    def post(self):
        permissions.check_manager_permissions()
        data = request.json or {}
        review_ids = data.get("review_ids", [])
        if not review_ids:
            raise WrongParameterException("review_ids is required.")
        current_user = persons_service.get_current_user()
        result = asset_review_service.batch_approve(
            review_ids=review_ids,
            reviewer_id=current_user["id"],
            comment=data.get("comment"),
        )
        return result, 200


class AssetReviewBatchRejectResource(Resource):
    """
    POST /data/asset-reviews/batch-reject

    批量驳回审核。需要 manager/admin 权限。
    Body: {review_ids: string[], comment: string}  (comment 必填)
    """

    @jwt_required()
    def post(self):
        permissions.check_manager_permissions()
        data = request.json or {}
        review_ids = data.get("review_ids", [])
        if not review_ids:
            raise WrongParameterException("review_ids is required.")
        current_user = persons_service.get_current_user()
        result = asset_review_service.batch_reject(
            review_ids=review_ids,
            reviewer_id=current_user["id"],
            comment=data.get("comment"),
        )
        return result, 200
