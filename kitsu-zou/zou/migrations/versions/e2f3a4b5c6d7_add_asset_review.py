"""Add asset_review table and update global_asset status choices

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-25 23:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "asset_review",
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
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=True,
        ),
        sa.Column(
            "submitter_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=255),
            nullable=False,
            server_default="pending_review",
        ),
        sa.Column(
            "comment",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["global_asset.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["person.id"],
        ),
        sa.ForeignKeyConstraint(
            ["submitter_id"],
            ["person.id"],
        ),
    )
    op.create_index(
        "ix_asset_review_asset_id",
        "asset_review",
        ["asset_id"],
    )
    op.create_index(
        "ix_asset_review_status",
        "asset_review",
        ["status"],
    )


def downgrade():
    op.drop_index("ix_asset_review_status", table_name="asset_review")
    op.drop_index("ix_asset_review_asset_id", table_name="asset_review")
    op.drop_table("asset_review")
