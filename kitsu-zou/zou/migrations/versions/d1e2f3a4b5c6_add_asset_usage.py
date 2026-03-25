"""Add asset_usage table for usage tracking

Revision ID: d1e2f3a4b5c6
Revises: c9d5e7f8a1b3
Create Date: 2026-03-25 22:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "c9d5e7f8a1b3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "asset_usage",
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "asset_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            sa.ForeignKey("global_asset.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            sa.ForeignKey("project.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "entity_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            sa.ForeignKey("entity.id"),
            nullable=True,
        ),
        sa.Column(
            "entity_type",
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            "usage_type",
            sa.String(255),
            nullable=False,
            server_default="direct",
        ),
        sa.Column(
            "context",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "used_by_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            sa.ForeignKey("person.id"),
            nullable=True,
        ),
    )

    op.create_index(
        "idx_asset_usage_asset_project",
        "asset_usage",
        ["asset_id", "project_id"],
    )


def downgrade():
    op.drop_index("idx_asset_usage_asset_project", table_name="asset_usage")
    op.drop_table("asset_usage")
