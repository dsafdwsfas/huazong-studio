"""Add asset_node and asset_node_link tables for intelligent node system

Revision ID: b8c4d5e6f7a2
Revises: a7b3c9d2e4f1
Create Date: 2026-03-25 16:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlalchemy_utils
import uuid

# revision identifiers, used by Alembic.
revision = "b8c4d5e6f7a2"
down_revision = "a7b3c9d2e4f1"
branch_labels = None
depends_on = None


def upgrade():
    # --- asset_node table ---
    op.create_table(
        "asset_node",
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            default=uuid.uuid4,
            nullable=False,
        ),
        sa.Column(
            "node_type",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "ref_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=200), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column("pos_x", sa.Float(), nullable=True),
        sa.Column("pos_y", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "node_type", "ref_id", name="asset_node_type_ref_uc"
        ),
    )
    op.create_index(
        op.f("ix_asset_node_node_type"),
        "asset_node",
        ["node_type"],
        unique=False,
    )
    op.create_index(
        "idx_asset_node_ref",
        "asset_node",
        ["ref_id"],
        unique=False,
    )

    # --- asset_node_link table ---
    op.create_table(
        "asset_node_link",
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            default=uuid.uuid4,
            nullable=False,
        ),
        sa.Column(
            "source_node_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "target_node_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "link_type",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "weight",
            sa.Float(),
            nullable=True,
            server_default="1.0",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["source_node_id"],
            ["asset_node.id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_node_id"],
            ["asset_node.id"],
        ),
        sa.UniqueConstraint(
            "source_node_id",
            "target_node_id",
            "link_type",
            name="asset_node_link_uc",
        ),
    )
    op.create_index(
        op.f("ix_asset_node_link_source_node_id"),
        "asset_node_link",
        ["source_node_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_asset_node_link_target_node_id"),
        "asset_node_link",
        ["target_node_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_asset_node_link_link_type"),
        "asset_node_link",
        ["link_type"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_asset_node_link_link_type"),
        table_name="asset_node_link",
    )
    op.drop_index(
        op.f("ix_asset_node_link_target_node_id"),
        table_name="asset_node_link",
    )
    op.drop_index(
        op.f("ix_asset_node_link_source_node_id"),
        table_name="asset_node_link",
    )
    op.drop_table("asset_node_link")

    op.drop_index("idx_asset_node_ref", table_name="asset_node")
    op.drop_index(
        op.f("ix_asset_node_node_type"), table_name="asset_node"
    )
    op.drop_table("asset_node")
