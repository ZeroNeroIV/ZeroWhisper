"""Initial schema — creates user, exchangerate, and transaction tables.

Revision ID: 001
Revises:
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)

    op.create_table(
        "exchangerate",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Text(), nullable=False),
        sa.Column("jod_per_usd", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exchangerate_date"), "exchangerate", ["date"], unique=False)

    op.create_table(
        "transaction",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("amount_original", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("currency_original", sa.String(), nullable=False),
        sa.Column("amount_base", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transaction_category"), "transaction", ["category"], unique=False)
    op.create_index(op.f("ix_transaction_transaction_date"), "transaction", ["transaction_date"], unique=False)
    op.create_index(op.f("ix_transaction_user_id"), "transaction", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transaction_user_id"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_transaction_date"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_category"), table_name="transaction")
    op.drop_table("transaction")

    op.drop_index(op.f("ix_exchangerate_date"), table_name="exchangerate")
    op.drop_table("exchangerate")

    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
