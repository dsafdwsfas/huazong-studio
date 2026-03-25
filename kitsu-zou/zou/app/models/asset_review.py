"""
资产审核记录模型

记录全局资产的审核流程：提交 → 审核通过/驳回/需修改。
"""

from sqlalchemy_utils import UUIDType, ChoiceType

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin

REVIEW_STATUSES = [
    ("pending_review", "Pending Review"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("revision_requested", "Revision Requested"),
]


class AssetReview(db.Model, BaseMixin, SerializerMixin):
    """
    资产审核记录。

    每次提交审核创建一条记录，审核人操作后更新状态。
    一个资产可以有多条审核记录（历史轨迹）。
    """

    __tablename__ = "asset_review"

    asset_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("global_asset.id"),
        nullable=False,
        index=True,
    )
    reviewer_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("person.id"),
        nullable=True,
    )
    submitter_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("person.id"),
        nullable=False,
    )

    status = db.Column(
        ChoiceType(REVIEW_STATUSES),
        nullable=False,
        default="pending_review",
    )
    comment = db.Column(db.Text())
    version_number = db.Column(db.Integer)

    reviewed_at = db.Column(db.DateTime)

    # Relationships
    asset = db.relationship(
        "GlobalAsset",
        backref=db.backref(
            "reviews",
            lazy="dynamic",
            order_by="AssetReview.created_at.desc()",
        ),
    )
    reviewer = db.relationship(
        "Person",
        foreign_keys=[reviewer_id],
    )
    submitter = db.relationship(
        "Person",
        foreign_keys=[submitter_id],
    )

    def __repr__(self):
        return "<AssetReview %s>" % self.id
