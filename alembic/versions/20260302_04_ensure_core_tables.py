"""Ensure core tables exist

Revision ID: 20260302_04
Revises: 20260302_03
Create Date: 2026-03-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260302_04"
down_revision: Union[str, None] = "20260302_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def _ensure_index(table_name: str, index_name: str, columns: list[str], unique: bool = False) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_table(inspector, table_name):
        return
    if _has_index(inspector, table_name, index_name):
        return
    op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    expense_type_enum = postgresql.ENUM(
        "DAILY",
        "WEEKLY",
        "MONTHLY",
        "YEARLY",
        "ONCE",
        name="expensetype",
    )
    payment_frequency_enum = postgresql.ENUM(
        "WEEKLY",
        "BIWEEKLY",
        "MONTHLY",
        "YEARLY",
        "QUARTERLY",
        "ONCE",
        name="paymentfrequency",
    )
    expense_type_enum.create(bind, checkfirst=True)
    payment_frequency_enum.create(bind, checkfirst=True)
    expense_type_enum_col = postgresql.ENUM(
        "DAILY",
        "WEEKLY",
        "MONTHLY",
        "YEARLY",
        "ONCE",
        name="expensetype",
        create_type=False,
    )
    payment_frequency_enum_col = postgresql.ENUM(
        "WEEKLY",
        "BIWEEKLY",
        "MONTHLY",
        "YEARLY",
        "QUARTERLY",
        "ONCE",
        name="paymentfrequency",
        create_type=False,
    )

    if not _has_table(inspector, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("telegram_id", sa.BigInteger(), nullable=False),
            sa.Column("username", sa.String(length=100), nullable=True),
            sa.Column("full_name", sa.String(length=200), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
        )

    if not _has_table(inspector, "expenses"):
        op.create_table(
            "expenses",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column(
                "expense_type",
                expense_type_enum_col,
                nullable=False,
                server_default="ONCE",
            ),
            sa.Column(
                "is_future",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
        )

    if not _has_table(inspector, "payments"):
        op.create_table(
            "payments",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("due_date", sa.Date(), nullable=False),
            sa.Column("weekday", sa.Integer(), nullable=True),
            sa.Column("day_of_month", sa.Integer(), nullable=True),
            sa.Column("payment_date", sa.Date(), nullable=True),
            sa.Column(
                "is_paid",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.Column(
                "is_skipped",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.Column("occurrences_left", sa.Integer(), nullable=True),
            sa.Column(
                "frequency",
                payment_frequency_enum_col,
                nullable=False,
                server_default="ONCE",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "reminder_sent",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.Column("overdue_last_sent_at", sa.DateTime(), nullable=True),
        )

    if not _has_table(inspector, "income"):
        op.create_table(
            "income",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("description", sa.String(length=200), nullable=False),
            sa.Column(
                "category",
                sa.String(length=50),
                nullable=False,
                server_default="Kirim",
            ),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
        )

    _ensure_index("users", "ix_users_id", ["id"], unique=False)
    _ensure_index("users", "ix_users_telegram_id", ["telegram_id"], unique=True)

    _ensure_index("expenses", "ix_expenses_id", ["id"], unique=False)
    _ensure_index("expenses", "ix_expenses_user_id", ["user_id"], unique=False)

    _ensure_index("payments", "ix_payments_id", ["id"], unique=False)
    _ensure_index("payments", "ix_payments_user_id", ["user_id"], unique=False)

    _ensure_index("income", "ix_income_id", ["id"], unique=False)
    _ensure_index("income", "ix_income_user_id", ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "income"):
        if _has_index(inspector, "income", "ix_income_user_id"):
            op.drop_index("ix_income_user_id", table_name="income")
        if _has_index(inspector, "income", "ix_income_id"):
            op.drop_index("ix_income_id", table_name="income")
        op.drop_table("income")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "payments"):
        if _has_index(inspector, "payments", "ix_payments_user_id"):
            op.drop_index("ix_payments_user_id", table_name="payments")
        if _has_index(inspector, "payments", "ix_payments_id"):
            op.drop_index("ix_payments_id", table_name="payments")
        op.drop_table("payments")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "expenses"):
        if _has_index(inspector, "expenses", "ix_expenses_user_id"):
            op.drop_index("ix_expenses_user_id", table_name="expenses")
        if _has_index(inspector, "expenses", "ix_expenses_id"):
            op.drop_index("ix_expenses_id", table_name="expenses")
        op.drop_table("expenses")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "users"):
        if _has_index(inspector, "users", "ix_users_telegram_id"):
            op.drop_index("ix_users_telegram_id", table_name="users")
        if _has_index(inspector, "users", "ix_users_id"):
            op.drop_index("ix_users_id", table_name="users")
        op.drop_table("users")

    payment_frequency_enum = postgresql.ENUM(
        "WEEKLY",
        "BIWEEKLY",
        "MONTHLY",
        "YEARLY",
        "QUARTERLY",
        "ONCE",
        name="paymentfrequency",
    )
    expense_type_enum = postgresql.ENUM(
        "DAILY",
        "WEEKLY",
        "MONTHLY",
        "YEARLY",
        "ONCE",
        name="expensetype",
    )
    payment_frequency_enum.drop(bind, checkfirst=True)
    expense_type_enum.drop(bind, checkfirst=True)
