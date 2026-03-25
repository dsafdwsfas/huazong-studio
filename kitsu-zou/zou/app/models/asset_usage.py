"""
资产使用追踪模型

记录哪些项目/分镜/场次使用了哪些全局资产，支持跨项目复用分析。
"""

from sqlalchemy_utils import UUIDType, ChoiceType

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


USAGE_TYPES = [
    ("direct", "直接使用"),
    ("reference", "参考引用"),
    ("derived", "派生使用"),
    ("template", "模板使用"),
]


class AssetUsage(db.Model, BaseMixin, SerializerMixin):
    """
    资产使用追踪 — 记录哪些项目/分镜/场次用了哪些资产。
    每条记录代表一次资产在特定项目/实体中的使用。
    """

    __tablename__ = "asset_usage"

    asset_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("global_asset.id"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("project.id"),
        nullable=False,
        index=True,
    )

    # 使用位置（可选，精确到分镜/场次/资产实体）
    entity_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("entity.id"),
        nullable=True,
    )
    entity_type = db.Column(db.String(50), nullable=True)

    # 使用信息
    usage_type = db.Column(
        ChoiceType(USAGE_TYPES),
        default="direct",
        nullable=False,
    )

    context = db.Column(db.Text(), nullable=True)

    used_by_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("person.id"),
        nullable=True,
    )

    # Relationships
    asset = db.relationship("GlobalAsset", backref="usages")
    project = db.relationship("Project")
    used_by = db.relationship("Person")

    __table_args__ = (
        db.Index(
            "idx_asset_usage_asset_project",
            "asset_id",
            "project_id",
        ),
    )

    def __repr__(self):
        return "<AssetUsage %s>" % self.id
