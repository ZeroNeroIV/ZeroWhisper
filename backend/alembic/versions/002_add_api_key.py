"""add apikey table

Revision ID: 002
Revises: 001
Create Date: 2026-05-12

"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apikey",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("prefix", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_apikey_user_id", "apikey", ["user_id"])
    op.create_index("ix_apikey_key_hash", "apikey", ["key_hash"])


def downgrade() -> None:
    op.drop_table("apikey")
