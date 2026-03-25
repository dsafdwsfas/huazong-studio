from sqlalchemy_utils import UUIDType, ChoiceType

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin

from sqlalchemy.dialects.postgresql import JSONB

GLOBAL_ASSET_STATUSES = [
    ("draft", "Draft"),
    ("pending_review", "Pending Review"),
    ("reviewed", "Reviewed"),
    ("rejected", "Rejected"),
    ("archived", "Archived"),
]


class GlobalAssetProjectLink(db.Model):
    """
    Link table between global assets and projects (many-to-many).
    Tracks which projects reference a given global asset.
    """

    __tablename__ = "global_asset_project_link"
    global_asset_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("global_asset.id"),
        primary_key=True,
    )
    project_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("project.id"),
        primary_key=True,
    )
    linked_at = db.Column(db.DateTime)


class GlobalAsset(db.Model, BaseMixin, SerializerMixin):
    """
    A reusable asset in the global asset library. Global assets can be
    shared across projects and include characters, scenes, props, effects,
    music, prompts, styles, and camera language presets.
    """

    __tablename__ = "global_asset"

    name = db.Column(db.String(200), nullable=False, index=True)

    category_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("asset_category.id"),
        nullable=True,
        index=True,
    )

    description = db.Column(db.Text())

    tags = db.Column(JSONB, default=[])
    files = db.Column(JSONB, default=[])
    metadata_ = db.Column("metadata", JSONB, default={})
    style_keywords = db.Column(JSONB, default=[])

    prompt_text = db.Column(db.Text())

    source_project_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("project.id"),
        nullable=True,
        index=True,
    )

    creator_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("person.id"),
        nullable=False,
        index=True,
    )

    version = db.Column(db.Integer, default=1, nullable=False)

    status = db.Column(
        ChoiceType(GLOBAL_ASSET_STATUSES),
        default="draft",
        nullable=False,
        index=True,
    )

    thumbnail_preview_file_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("preview_file.id", name="fk_global_asset_thumbnail"),
        nullable=True,
    )

    usage_count = db.Column(db.Integer, default=0, nullable=False)

    category_rel = db.relationship("AssetCategory", backref="assets")

    projects = db.relationship(
        "Project",
        secondary="global_asset_project_link",
        backref="global_assets",
    )

    __table_args__ = (
        db.Index(
            "ix_global_asset_category_id_status",
            "category_id",
            "status",
        ),
    )
