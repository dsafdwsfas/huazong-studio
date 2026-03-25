"""Add asset_category table and migrate global_asset.category to FK

Revision ID: a7b3c9d2e4f1
Revises: 04126958941a
Create Date: 2026-03-25 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlalchemy_utils
import uuid

# revision identifiers, used by Alembic.
revision = "a7b3c9d2e4f1"
down_revision = "04126958941a"
branch_labels = None
depends_on = None

# Slug-to-name mapping for data migration
CATEGORY_SLUG_MAP = {
    "character": ("人物", "Character", "user", "#FF6B6B", 1),
    "scene": ("场景", "Scene", "image", "#4ECDC4", 2),
    "prop": ("道具", "Prop", "box", "#45B7D1", 3),
    "effect": ("特效", "VFX", "zap", "#FFA07A", 4),
    "music": ("音乐", "Music", "music", "#DDA0DD", 5),
    "prompt": ("提示词", "Prompt", "message-square", "#98D8C8", 6),
    "style": ("风格", "Style", "palette", "#F7DC6F", 7),
    "camera_language": ("镜头语言", "Camera", "video", "#BB8FCE", 8),
}


def upgrade():
    # 1. Create asset_category table
    op.create_table(
        "asset_category",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=True),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column(
            "parent_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=True,
        ),
        sa.Column(
            "sort_order", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=True,
            server_default="false",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=True,
            server_default="true",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            default=uuid.uuid4,
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["asset_category.id"],
        ),
    )
    op.create_index(
        op.f("ix_asset_category_parent_id"),
        "asset_category",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        "ix_asset_category_parent_sort",
        "asset_category",
        ["parent_id", "sort_order"],
        unique=False,
    )

    # 2. Insert default categories
    asset_category = sa.table(
        "asset_category",
        sa.column("id", sqlalchemy_utils.types.uuid.UUIDType(binary=False)),
        sa.column("name", sa.String),
        sa.column("name_en", sa.String),
        sa.column("slug", sa.String),
        sa.column("icon", sa.String),
        sa.column("color", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_system", sa.Boolean),
        sa.column("is_active", sa.Boolean),
    )

    slug_to_uuid = {}
    for slug, (name, name_en, icon, color, sort_order) in CATEGORY_SLUG_MAP.items():
        cat_uuid = uuid.uuid4()
        slug_to_uuid[slug] = cat_uuid
        op.execute(
            asset_category.insert().values(
                id=cat_uuid,
                name=name,
                name_en=name_en,
                slug=slug,
                icon=icon,
                color=color,
                sort_order=sort_order,
                is_system=True,
                is_active=True,
            )
        )

    # 3. Add category_id column to global_asset
    op.add_column(
        "global_asset",
        sa.Column(
            "category_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=True,
        ),
    )

    # 4. Migrate data: map old category string values to new FK UUIDs
    global_asset = sa.table(
        "global_asset",
        sa.column("id", sqlalchemy_utils.types.uuid.UUIDType(binary=False)),
        sa.column("category", sa.String),
        sa.column("category_id", sqlalchemy_utils.types.uuid.UUIDType(binary=False)),
    )

    for slug, cat_uuid in slug_to_uuid.items():
        op.execute(
            global_asset.update()
            .where(global_asset.c.category == slug)
            .values(category_id=cat_uuid)
        )

    # 5. Drop old category column and its index
    op.drop_index(
        "ix_global_asset_category_status", table_name="global_asset"
    )
    op.drop_index(
        op.f("ix_global_asset_category"), table_name="global_asset"
    )
    op.drop_column("global_asset", "category")

    # 6. Add FK constraint and indexes for category_id
    op.create_foreign_key(
        "fk_global_asset_category",
        "global_asset",
        "asset_category",
        ["category_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_global_asset_category_id"),
        "global_asset",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_global_asset_category_id_status",
        "global_asset",
        ["category_id", "status"],
        unique=False,
    )


def downgrade():
    # 1. Re-add old category string column
    op.add_column(
        "global_asset",
        sa.Column("category", sa.String(length=255), nullable=True),
    )

    # 2. Migrate data back: category_id FK -> slug string
    global_asset = sa.table(
        "global_asset",
        sa.column("category", sa.String),
        sa.column("category_id", sqlalchemy_utils.types.uuid.UUIDType(binary=False)),
    )
    asset_category = sa.table(
        "asset_category",
        sa.column("id", sqlalchemy_utils.types.uuid.UUIDType(binary=False)),
        sa.column("slug", sa.String),
    )

    conn = op.get_bind()
    categories = conn.execute(
        sa.select(asset_category.c.id, asset_category.c.slug)
    ).fetchall()

    for cat_id, slug in categories:
        op.execute(
            global_asset.update()
            .where(global_asset.c.category_id == cat_id)
            .values(category=slug)
        )

    # 3. Drop new FK and indexes
    op.drop_index(
        "ix_global_asset_category_id_status", table_name="global_asset"
    )
    op.drop_index(
        op.f("ix_global_asset_category_id"), table_name="global_asset"
    )
    op.drop_constraint(
        "fk_global_asset_category", "global_asset", type_="foreignkey"
    )
    op.drop_column("global_asset", "category_id")

    # 4. Re-create old indexes
    op.create_index(
        op.f("ix_global_asset_category"),
        "global_asset",
        ["category"],
        unique=False,
    )
    op.create_index(
        "ix_global_asset_category_status",
        "global_asset",
        ["category", "status"],
        unique=False,
    )

    # Make category NOT NULL again
    op.alter_column(
        "global_asset", "category", existing_type=sa.String(255), nullable=False
    )

    # 5. Drop asset_category table
    op.drop_index(
        "ix_asset_category_parent_sort", table_name="asset_category"
    )
    op.drop_index(
        op.f("ix_asset_category_parent_id"), table_name="asset_category"
    )
    op.drop_table("asset_category")
