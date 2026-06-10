"""add wallet, category, bankconnection tables; transaction type/wallet/transfer columns

Revision ID: 003
Revises: 002
Create Date: 2026-06-10

"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "category",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, default=False),
        sa.Column("parent_id", sa.String(), sa.ForeignKey("category.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name"),
    )
    op.create_index("ix_category_user_id", "category", ["user_id"])

    op.create_table(
        "wallet",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(), nullable=False, server_default="cash"),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("balance", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("initial_balance", sa.Numeric(precision=18, scale=6), nullable=False, server_default="0"),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallet_user_id", "wallet", ["user_id"])
    op.create_index("ix_wallet_type", "wallet", ["type"])

    op.create_table(
        "bankconnection",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("bank_name", sa.String(), nullable=False),
        sa.Column("auth_type", sa.String(), nullable=False),
        sa.Column("credentials", sa.String(), nullable=False),
        sa.Column("account_number", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bankconnection_user_id", "bankconnection", ["user_id"])

    with op.batch_alter_table("transaction") as batch:
        batch.add_column(sa.Column("wallet_id", sa.String(), sa.ForeignKey("wallet.id"), nullable=True))
        batch.add_column(sa.Column("type", sa.String(), nullable=False, server_default="expense"))
        batch.add_column(sa.Column("transfer_id", sa.String(), nullable=True))
    op.create_index("ix_transaction_wallet_id", "transaction", ["wallet_id"])
    op.create_index("ix_transaction_type", "transaction", ["type"])
    op.create_index("ix_transaction_transfer_id", "transaction", ["transfer_id"])

    # Backfill type from each user's income categories
    op.execute(
        'UPDATE "transaction" SET type=\'income\' WHERE EXISTS ('
        "  SELECT 1 FROM category c"
        '  WHERE c.user_id = "transaction".user_id'
        '    AND c.name = "transaction".category'
        "    AND c.type = 'income'"
        ")"
    )


def downgrade() -> None:
    op.drop_index("ix_transaction_transfer_id", table_name="transaction")
    op.drop_index("ix_transaction_type", table_name="transaction")
    op.drop_index("ix_transaction_wallet_id", table_name="transaction")
    with op.batch_alter_table("transaction") as batch:
        batch.drop_column("transfer_id")
        batch.drop_column("type")
        batch.drop_column("wallet_id")

    op.drop_index("ix_bankconnection_user_id", table_name="bankconnection")
    op.drop_table("bankconnection")
    op.drop_index("ix_wallet_type", table_name="wallet")
    op.drop_index("ix_wallet_user_id", table_name="wallet")
    op.drop_table("wallet")
    op.drop_index("ix_category_user_id", table_name="category")
    op.drop_table("category")
