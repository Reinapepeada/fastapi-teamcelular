"""make leads_repair contact optional

Revision ID: leads_repair_contact_opt_260421
Revises: add_repair_leads_20260416
Create Date: 2026-04-21

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision = "leads_repair_contact_opt_260421"
down_revision = "add_repair_leads_20260416"
branch_labels = None
depends_on = None


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(conn, table_name: str, column_name: str) -> bool:
    inspector = inspect(conn)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "leads_repair") and column_exists(conn, "leads_repair", "contact"):
        conn.execute(text("UPDATE leads_repair SET contact = NULL WHERE contact = ''"))
        with op.batch_alter_table("leads_repair") as batch_op:
            batch_op.alter_column(
                "contact",
                existing_type=sa.String(length=120),
                nullable=True,
            )


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "leads_repair") and column_exists(conn, "leads_repair", "contact"):
        conn.execute(text("UPDATE leads_repair SET contact = '' WHERE contact IS NULL"))
        with op.batch_alter_table("leads_repair") as batch_op:
            batch_op.alter_column(
                "contact",
                existing_type=sa.String(length=120),
                nullable=False,
            )