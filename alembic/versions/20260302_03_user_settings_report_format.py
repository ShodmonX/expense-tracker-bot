"""Add report_format to user_settings

Revision ID: 20260302_03
Revises: 20260302_02
Create Date: 2026-03-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260302_03"
down_revision: Union[str, None] = "20260302_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "user_settings"):
        return

    if not _has_column(inspector, "user_settings", "report_format"):
        op.add_column(
            "user_settings",
            sa.Column(
                "report_format",
                sa.String(length=8),
                nullable=False,
                server_default="xlsx",
            ),
        )

    op.execute(
        sa.text(
            """
            UPDATE user_settings
            SET report_format = 'xlsx'
            WHERE report_format IS NULL OR report_format = ''
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "user_settings"):
        return

    if _has_column(inspector, "user_settings", "report_format"):
        op.drop_column("user_settings", "report_format")
