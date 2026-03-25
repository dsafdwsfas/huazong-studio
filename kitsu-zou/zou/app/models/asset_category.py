from sqlalchemy_utils import UUIDType
from sqlalchemy.dialects.postgresql import JSONB

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class AssetCategory(db.Model, BaseMixin, SerializerMixin):
    """
    Extensible tree-structured asset category for the global asset library.
    Supports hierarchical nesting via parent_id self-reference.
    System-preset categories (is_system=True) cannot be deleted.
    """

    __tablename__ = "asset_category"

    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text())
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7))
    parent_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("asset_category.id"),
        nullable=True,
        index=True,
    )
    sort_order = db.Column(db.Integer, default=0)
    is_system = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    metadata_ = db.Column("metadata", JSONB, default={})

    parent = db.relationship(
        "AssetCategory",
        remote_side="AssetCategory.id",
        backref="children",
    )

    __table_args__ = (
        db.Index("ix_asset_category_parent_sort", "parent_id", "sort_order"),
    )

    def __repr__(self):
        return "<AssetCategory %s (%s)>" % (self.name, self.slug)
