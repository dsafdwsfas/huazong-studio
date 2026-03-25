from sqlalchemy_utils import UUIDType, ChoiceType

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin

from sqlalchemy.dialects.postgresql import JSONB

ASSET_VERSION_CHANGE_TYPES = [
    ("create", "创建"),
    ("update", "更新"),
    ("metadata", "元数据变更"),
    ("files", "文件变更"),
    ("status", "状态变更"),
    ("restore", "版本恢复"),
]


class AssetVersion(db.Model, BaseMixin, SerializerMixin):
    """
    Asset version history. Each version stores a full snapshot of the asset
    state at creation time, along with a diff from the previous version.
    """

    __tablename__ = "asset_version"

    asset_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("global_asset.id"),
        nullable=False,
        index=True,
    )

    version_number = db.Column(db.Integer, nullable=False)

    # Full asset data snapshot at version creation time
    snapshot = db.Column(JSONB, nullable=False)

    # Change information
    change_summary = db.Column(db.Text)
    change_type = db.Column(
        ChoiceType(ASSET_VERSION_CHANGE_TYPES),
        default="update",
    )

    # Diff from previous version: {field: {old: ..., new: ...}}
    diff = db.Column(JSONB, default={})

    # Author of this version
    author_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("person.id"),
        nullable=True,
    )

    # File list snapshot at version creation time
    files_snapshot = db.Column(JSONB, default=[])

    # Relationships
    asset = db.relationship(
        "GlobalAsset",
        backref=db.backref(
            "versions",
            lazy="dynamic",
            order_by="AssetVersion.version_number.desc()",
        ),
    )
    author = db.relationship("Person")

    __table_args__ = (
        db.UniqueConstraint(
            "asset_id",
            "version_number",
            name="asset_version_uc",
        ),
        db.Index(
            "idx_asset_version_asset",
            "asset_id",
            "version_number",
        ),
    )

    def __repr__(self):
        return "<AssetVersion %s v%s>" % (self.asset_id, self.version_number)
