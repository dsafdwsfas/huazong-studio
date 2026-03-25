"""
Asset graph node and link models for the intelligent node system (Phase 4.3).

Provides a force-directed graph structure where GlobalAssets, projects,
shots, sequences, categories, persons, styles, and prompts are represented
as nodes, connected by typed, weighted edges.
"""

from sqlalchemy_utils import UUIDType, ChoiceType
from sqlalchemy.dialects.postgresql import JSONB

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


NODE_TYPES = [
    ("asset", "Asset"),
    ("project", "Project"),
    ("shot", "Shot"),
    ("sequence", "Sequence"),
    ("category", "Category"),
    ("person", "Person"),
    ("style", "Style"),
    ("prompt", "Prompt"),
]

LINK_TYPES = [
    ("contains", "Contains"),
    ("belongs_to", "Belongs To"),
    ("references", "References"),
    ("derived_from", "Derived From"),
    ("used_in", "Used In"),
    ("created_by", "Created By"),
    ("same_style", "Same Style"),
    ("similar_to", "Similar To"),
    ("co_occurs", "Co-occurs"),
]


class AssetNode(db.Model, BaseMixin, SerializerMixin):
    """
    A node in the asset graph. Each node references an external entity
    (GlobalAsset, Project, Entity, Person, etc.) by type + ref_id.
    """

    __tablename__ = "asset_node"

    node_type = db.Column(
        ChoiceType(NODE_TYPES), nullable=False, index=True
    )
    ref_id = db.Column(
        UUIDType(binary=False), nullable=False, index=True
    )
    label = db.Column(db.String(200))
    metadata_ = db.Column("metadata", JSONB, default={})

    # User-adjustable position for force-directed graph layout
    pos_x = db.Column(db.Float)
    pos_y = db.Column(db.Float)

    __table_args__ = (
        db.UniqueConstraint(
            "node_type", "ref_id", name="asset_node_type_ref_uc"
        ),
        db.Index("idx_asset_node_ref", "ref_id"),
    )

    def __repr__(self):
        return "<AssetNode %s:%s>" % (self.node_type, self.label)


class AssetNodeLink(db.Model, BaseMixin, SerializerMixin):
    """
    A directed, typed, weighted edge between two AssetNodes.
    """

    __tablename__ = "asset_node_link"

    source_node_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("asset_node.id"),
        nullable=False,
        index=True,
    )
    target_node_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("asset_node.id"),
        nullable=False,
        index=True,
    )
    link_type = db.Column(
        ChoiceType(LINK_TYPES), nullable=False, index=True
    )
    weight = db.Column(db.Float, default=1.0)
    metadata_ = db.Column("metadata", JSONB, default={})

    source_node = db.relationship(
        "AssetNode", foreign_keys=[source_node_id]
    )
    target_node = db.relationship(
        "AssetNode", foreign_keys=[target_node_id]
    )

    __table_args__ = (
        db.UniqueConstraint(
            "source_node_id",
            "target_node_id",
            "link_type",
            name="asset_node_link_uc",
        ),
    )

    def __repr__(self):
        return "<AssetNodeLink %s -[%s]-> %s>" % (
            self.source_node_id,
            self.link_type,
            self.target_node_id,
        )
