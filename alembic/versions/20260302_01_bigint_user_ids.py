"""Promote telegram/user IDs to BIGINT

Revision ID: 20260302_01
Revises:
Create Date: 2026-03-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260302_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_bigint(column_type: object) -> bool:
    return isinstance(column_type, sa.BigInteger) or column_type.__class__.__name__.upper() in {
        "BIGINT",
        "BIGINTEGER",
    }


def _alter_to_bigint_if_needed(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if table_name not in table_names:
        return

    columns = {col["name"]: col for col in inspector.get_columns(table_name)}
    if column_name not in columns:
        return

    if _is_bigint(columns[column_name]["type"]):
        return

    op.execute(
        sa.text(
            f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE BIGINT'
        )
    )


def _alter_to_integer_if_needed(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if table_name not in table_names:
        return

    columns = {col["name"]: col for col in inspector.get_columns(table_name)}
    if column_name not in columns:
        return

    if not _is_bigint(columns[column_name]["type"]):
        return

    op.execute(
        sa.text(
            f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE INTEGER'
        )
    )


def upgrade() -> None:
    _alter_to_bigint_if_needed("users", "telegram_id")
    _alter_to_bigint_if_needed("expenses", "user_id")
    _alter_to_bigint_if_needed("payments", "user_id")
    _alter_to_bigint_if_needed("income", "user_id")


def downgrade() -> None:
    _alter_to_integer_if_needed("income", "user_id")
    _alter_to_integer_if_needed("payments", "user_id")
    _alter_to_integer_if_needed("expenses", "user_id")
    _alter_to_integer_if_needed("users", "telegram_id")
