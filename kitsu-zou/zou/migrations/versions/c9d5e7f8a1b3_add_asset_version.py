"""Add asset_version table for version history tracking

Revision ID: c9d5e7f8a1b3
Revises: b8c4d5e6f7a2
Create Date: 2026-03-25 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = "c9d5e7f8a1b3"
down_revision = "b8c4d5e6f7a2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "asset_version",
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
            "version_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "change_summary",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "change_type",
            sa.String(length=20),
            default="update",
            nullable=True,
        ),
        sa.Column(
            "diff",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "author_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            sa.ForeignKey("person.id"),
            nullable=True,
        ),
        sa.Column(
            "files_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "asset_id",
            "version_number",
            name="asset_version_uc",
        ),
        sa.Index(
            "idx_asset_version_asset",
            "asset_id",
            "version_number",
        ),
    )


def downgrade():
    op.drop_table("asset_version")
