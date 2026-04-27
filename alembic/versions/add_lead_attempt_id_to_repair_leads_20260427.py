"""add lead_attempt_id to leads_repair

Revision ID: add_lead_attempt_id_20260427
Revises: add_lead_interactions_20260424
Create Date: 2026-04-27

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "add_lead_attempt_id_20260427"
down_revision = "add_lead_interactions_20260424"
branch_labels = None
depends_on = None


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(conn, table_name: str, column_name: str) -> bool:
    inspector = inspect(conn)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def index_exists(conn, table_name: str, index_name: str) -> bool:
    inspector = inspect(conn)
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "leads_repair") and not column_exists(conn, "leads_repair", "lead_attempt_id"):
        with op.batch_alter_table("leads_repair") as batch_op:
            batch_op.add_column(sa.Column("lead_attempt_id", sa.String(length=120), nullable=True))

    if table_exists(conn, "leads_repair") and not index_exists(conn, "leads_repair", "ix_leads_repair_lead_attempt_id"):
        op.create_index(
            "ix_leads_repair_lead_attempt_id",
            "leads_repair",
            ["lead_attempt_id"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "leads_repair") and index_exists(conn, "leads_repair", "ix_leads_repair_lead_attempt_id"):
        op.drop_index("ix_leads_repair_lead_attempt_id", table_name="leads_repair")

    if table_exists(conn, "leads_repair") and column_exists(conn, "leads_repair", "lead_attempt_id"):
        with op.batch_alter_table("leads_repair") as batch_op:
            batch_op.drop_column("lead_attempt_id")