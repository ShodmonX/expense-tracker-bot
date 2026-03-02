"""Create user_settings table

Revision ID: 20260302_02
Revises: 20260302_01
Create Date: 2026-03-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260302_02"
down_revision: Union[str, None] = "20260302_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_settings" in set(inspector.get_table_names()):
        return

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Tashkent"),
        sa.Column("daily_reminder_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("overdue_reminder_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("daily_summary_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_settings_id", "user_settings", ["id"], unique=False)
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_settings" not in set(inspector.get_table_names()):
        return

    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_index("ix_user_settings_id", table_name="user_settings")
    op.drop_table("user_settings")
