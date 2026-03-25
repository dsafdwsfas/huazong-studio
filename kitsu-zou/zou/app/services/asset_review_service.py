"""
资产审核服务

提供资产审核工作流：提交审核、通过、驳回、请求修改、审核队列、批量操作。
"""

import logging

from sqlalchemy import func

from zou.app import db
from zou.app.models.asset_review import AssetReview
from zou.app.models.global_asset import GlobalAsset
from zou.app.services.exception import (
    WrongParameterException,
)
from zou.app.utils import date_helpers

logger = logging.getLogger(__name__)


class AssetReviewNotFoundException(Exception):
    pass


def _serialize_review(review):
    """Serialize an AssetReview model instance to dict."""
    if review is None:
        return None
    result = review.serialize()
    # ChoiceType returns tuple for status; extract the code value
    if isinstance(result.get("status"), tuple):
        result["status"] = result["status"][0]
    # Include submitter info
    if review.submitter:
        result["submitter"] = {
            "id": str(review.submitter.id),
            "full_name": getattr(review.submitter, "full_name", None)
            or str(review.submitter.first_name or "")
            + " "
            + str(review.submitter.last_name or ""),
        }
    # Include reviewer info
    if review.reviewer:
        result["reviewer"] = {
            "id": str(review.reviewer.id),
            "full_name": getattr(review.reviewer, "full_name", None)
            or str(review.reviewer.first_name or "")
            + " "
            + str(review.reviewer.last_name or ""),
        }
    # Include asset basic info
    if review.asset:
        result["asset"] = {
            "id": str(review.asset.id),
            "name": review.asset.name,
        }
    return result


def _get_review(review_id):
    """Get AssetReview ORM instance or raise."""
    review = AssetReview.get(review_id)
    if review is None:
        raise AssetReviewNotFoundException()
    return review


def _get_asset(asset_id):
    """Get GlobalAsset ORM instance or raise."""
    asset = GlobalAsset.get(asset_id)
    if asset is None:
        raise WrongParameterException("Asset not found.")
    return asset


def submit_for_review(asset_id, submitter_id, comment=None):
    """
    提交资产审核。

    1. 检查资产状态必须是 draft 或 rejected
    2. 更新 GlobalAsset.status = 'pending_review'
    3. 创建 AssetReview 记录

    Args:
        asset_id: 资产 ID
        submitter_id: 提交人 ID
        comment: 可选提交说明

    Returns:
        dict: 序列化后的审核记录
    """
    asset = _get_asset(asset_id)

    # Extract status code from ChoiceType
    current_status = asset.status
    if hasattr(current_status, "code"):
        current_status = current_status.code

    if current_status not in ("draft", "rejected"):
        raise WrongParameterException(
            "Asset must be in 'draft' or 'rejected' status to submit for review. "
            f"Current status: {current_status}"
        )

    # Update asset status
    asset.status = "pending_review"
    asset.updated_at = date_helpers.get_utc_now_datetime()

    # Create review record
    review = AssetReview.create(
        asset_id=asset_id,
        submitter_id=submitter_id,
        status="pending_review",
        comment=comment,
        version_number=asset.version,
    )

    return _serialize_review(review)


def approve_asset(review_id, reviewer_id, comment=None):
    """
    通过审核。

    1. 检查审核记录状态是 pending_review
    2. 更新 AssetReview.status = 'approved'
    3. 更新 GlobalAsset.status = 'reviewed'
    4. 记录 reviewed_at

    Args:
        review_id: 审核记录 ID
        reviewer_id: 审核人 ID
        comment: 可选审核意见

    Returns:
        dict: 序列化后的审核记录
    """
    review = _get_review(review_id)

    current_status = review.status
    if hasattr(current_status, "code"):
        current_status = current_status.code

    if current_status != "pending_review":
        raise WrongParameterException(
            "Review must be in 'pending_review' status to approve."
        )

    now = date_helpers.get_utc_now_datetime()

    review.status = "approved"
    review.reviewer_id = reviewer_id
    review.reviewed_at = now
    review.updated_at = now
    if comment:
        review.comment = comment

    # Update asset status to reviewed
    asset = review.asset
    asset.status = "reviewed"
    asset.updated_at = now

    db.session.commit()
    return _serialize_review(review)


def reject_asset(review_id, reviewer_id, comment=None):
    """
    驳回审核。

    1. comment 必填（驳回原因）
    2. 更新 AssetReview.status = 'rejected'
    3. 更新 GlobalAsset.status = 'draft'（退回草稿）

    Args:
        review_id: 审核记录 ID
        reviewer_id: 审核人 ID
        comment: 驳回原因（必填）

    Returns:
        dict: 序列化后的审核记录
    """
    if not comment:
        raise WrongParameterException(
            "Comment is required when rejecting an asset."
        )

    review = _get_review(review_id)

    current_status = review.status
    if hasattr(current_status, "code"):
        current_status = current_status.code

    if current_status != "pending_review":
        raise WrongParameterException(
            "Review must be in 'pending_review' status to reject."
        )

    now = date_helpers.get_utc_now_datetime()

    review.status = "rejected"
    review.reviewer_id = reviewer_id
    review.reviewed_at = now
    review.comment = comment
    review.updated_at = now

    # Return asset to draft
    asset = review.asset
    asset.status = "draft"
    asset.updated_at = now

    db.session.commit()
    return _serialize_review(review)


def request_revision(review_id, reviewer_id, comment):
    """
    请求修改。

    1. comment 必填
    2. 更新 AssetReview.status = 'revision_requested'
    3. 资产状态不变（仍可编辑）

    Args:
        review_id: 审核记录 ID
        reviewer_id: 审核人 ID
        comment: 修改意见（必填）

    Returns:
        dict: 序列化后的审核记录
    """
    if not comment:
        raise WrongParameterException(
            "Comment is required when requesting revision."
        )

    review = _get_review(review_id)

    current_status = review.status
    if hasattr(current_status, "code"):
        current_status = current_status.code

    if current_status != "pending_review":
        raise WrongParameterException(
            "Review must be in 'pending_review' status to request revision."
        )

    now = date_helpers.get_utc_now_datetime()

    review.status = "revision_requested"
    review.reviewer_id = reviewer_id
    review.reviewed_at = now
    review.comment = comment
    review.updated_at = now

    db.session.commit()
    return _serialize_review(review)


def get_review_queue(status=None, page=1, per_page=20):
    """
    获取审核队列。

    Args:
        status: 筛选状态（默认只看 pending_review）
        page: 页码
        per_page: 每页数量

    Returns:
        dict: {data, total, page, per_page, pages}
    """
    query = AssetReview.query()

    if status:
        query = query.filter(AssetReview.status == status)
    else:
        query = query.filter(AssetReview.status == "pending_review")

    query = query.order_by(AssetReview.created_at.asc())

    total = query.count()
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    reviews = query.offset(offset).limit(per_page).all()

    return {
        "data": [_serialize_review(r) for r in reviews],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def get_asset_reviews(asset_id):
    """
    获取资产的审核历史。

    Args:
        asset_id: 资产 ID

    Returns:
        list[dict]: 审核记录列表（按创建时间倒序）
    """
    _get_asset(asset_id)  # validate asset exists
    reviews = (
        AssetReview.query()
        .filter(AssetReview.asset_id == asset_id)
        .order_by(AssetReview.created_at.desc())
        .all()
    )
    return [_serialize_review(r) for r in reviews]


def get_review(review_id):
    """
    获取审核详情。

    Args:
        review_id: 审核记录 ID

    Returns:
        dict: 序列化后的审核记录
    """
    review = _get_review(review_id)
    return _serialize_review(review)


def get_my_submissions(person_id, status=None, page=1, per_page=20):
    """
    获取我提交的审核。

    Args:
        person_id: 当前用户 ID
        status: 可选状态筛选
        page: 页码
        per_page: 每页数量

    Returns:
        dict: {data, total, page, per_page, pages}
    """
    query = AssetReview.query().filter(
        AssetReview.submitter_id == person_id
    )

    if status:
        query = query.filter(AssetReview.status == status)

    query = query.order_by(AssetReview.created_at.desc())

    total = query.count()
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    reviews = query.offset(offset).limit(per_page).all()

    return {
        "data": [_serialize_review(r) for r in reviews],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def get_review_stats():
    """
    审核统计。

    Returns:
        dict: {pending_count, approved_today, rejected_today, avg_review_time_hours}
    """
    today_start = date_helpers.get_utc_now_datetime().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    pending_count = (
        AssetReview.query()
        .filter(AssetReview.status == "pending_review")
        .count()
    )

    approved_today = (
        AssetReview.query()
        .filter(
            AssetReview.status == "approved",
            AssetReview.reviewed_at >= today_start,
        )
        .count()
    )

    rejected_today = (
        AssetReview.query()
        .filter(
            AssetReview.status == "rejected",
            AssetReview.reviewed_at >= today_start,
        )
        .count()
    )

    # Average review time (from creation to reviewed_at) for completed reviews
    avg_result = (
        db.session.query(
            func.avg(
                func.extract(
                    "epoch",
                    AssetReview.reviewed_at - AssetReview.created_at,
                )
            )
        )
        .filter(AssetReview.reviewed_at.isnot(None))
        .scalar()
    )

    avg_review_time_hours = round(avg_result / 3600, 1) if avg_result else 0

    return {
        "pending_count": pending_count,
        "approved_today": approved_today,
        "rejected_today": rejected_today,
        "avg_review_time_hours": avg_review_time_hours,
    }


def batch_approve(review_ids, reviewer_id, comment=None):
    """
    批量通过审核。

    Args:
        review_ids: 审核记录 ID 列表
        reviewer_id: 审核人 ID
        comment: 可选审核意见

    Returns:
        dict: {approved: int, failed: list}
    """
    approved = 0
    failed = []

    for review_id in review_ids:
        try:
            approve_asset(review_id, reviewer_id, comment)
            approved += 1
        except Exception as e:
            failed.append({
                "review_id": str(review_id),
                "error": str(e),
            })

    return {"approved": approved, "failed": failed}


def batch_reject(review_ids, reviewer_id, comment):
    """
    批量驳回审核。

    Args:
        review_ids: 审核记录 ID 列表
        reviewer_id: 审核人 ID
        comment: 驳回原因（必填）

    Returns:
        dict: {rejected: int, failed: list}
    """
    if not comment:
        raise WrongParameterException(
            "Comment is required for batch rejection."
        )

    rejected = 0
    failed = []

    for review_id in review_ids:
        try:
            reject_asset(review_id, reviewer_id, comment)
            rejected += 1
        except Exception as e:
            failed.append({
                "review_id": str(review_id),
                "error": str(e),
            })

    return {"rejected": rejected, "failed": failed}
