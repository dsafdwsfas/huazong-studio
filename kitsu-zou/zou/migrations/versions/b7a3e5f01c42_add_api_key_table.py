"""Add api_key table for Open API authentication

Revision ID: b7a3e5f01c42
Revises: 04126958941a
Create Date: 2026-03-25 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlalchemy_utils
import uuid

# revision identifiers, used by Alembic.
revision = "b7a3e5f01c42"
down_revision = "04126958941a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_key",
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            default=uuid.uuid4,
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("key_prefix", sa.String(length=16), nullable=False),
        sa.Column("key_hash", sa.String(length=256), nullable=False),
        sa.Column(
            "owner_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default='["assets:read"]',
        ),
        sa.Column(
            "rate_limit",
            sa.Integer(),
            nullable=False,
            server_default="100",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column(
            "total_requests",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["person.id"],
        ),
        sa.UniqueConstraint("key_hash", name="uq_api_key_key_hash"),
    )
    op.create_index(
        op.f("ix_api_key_owner_id"),
        "api_key",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_api_key_key_hash"),
        "api_key",
        ["key_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_api_key_is_active"),
        "api_key",
        ["is_active"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_api_key_is_active"), table_name="api_key")
    op.drop_index(op.f("ix_api_key_key_hash"), table_name="api_key")
    op.drop_index(op.f("ix_api_key_owner_id"), table_name="api_key")
    op.drop_table("api_key")
