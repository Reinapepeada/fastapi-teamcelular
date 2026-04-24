"""add lead interactions

Revision ID: add_lead_interactions_20260424
Revises: make_leads_repair_contact_optional_20260421
Create Date: 2026-04-24

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "add_lead_interactions_20260424"
down_revision = "make_leads_repair_contact_optional_20260421"
branch_labels = None
depends_on = None


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def index_exists(conn, table_name: str, index_name: str) -> bool:
    inspector = inspect(conn)
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    conn = op.get_bind()

    if not table_exists(conn, "lead_interactions"):
        op.create_table(
            "lead_interactions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_name", sa.String(length=80), nullable=False),
            sa.Column("cta_name", sa.String(length=120), nullable=False),
            sa.Column("cta_location", sa.String(length=120), nullable=False),
            sa.Column("cta_variant", sa.String(length=40), nullable=False),
            sa.Column("destination", sa.String(length=400), nullable=True),
            sa.Column("page_path", sa.String(length=400), nullable=False),
            sa.Column("page_title", sa.String(length=200), nullable=True),
            sa.Column("lead_id", sa.String(length=36), nullable=True),
            sa.Column("lead_attempt_id", sa.String(length=120), nullable=True),
            sa.Column("form_name", sa.String(length=80), nullable=True),
            sa.Column("form_location", sa.String(length=120), nullable=True),
            sa.Column("form_version", sa.String(length=40), nullable=True),
            sa.Column("step_index", sa.Integer(), nullable=True),
            sa.Column("step_id", sa.String(length=80), nullable=True),
            sa.Column("step_label", sa.String(length=80), nullable=True),
            sa.Column("total_steps", sa.Integer(), nullable=True),
            sa.Column("brand", sa.String(length=80), nullable=True),
            sa.Column("model", sa.String(length=80), nullable=True),
            sa.Column("repair_type", sa.String(length=120), nullable=True),
            sa.Column("urgency", sa.String(length=40), nullable=True),
            sa.Column("contact_channel", sa.String(length=40), nullable=True),
            sa.Column("contact", sa.String(length=120), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("ip", sa.String(length=80), nullable=True),
            sa.Column("user_agent", sa.String(length=400), nullable=True),
            sa.Column("referrer", sa.String(length=400), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint(
                "event_name <> ''",
                name="ck_lead_interactions_event_name",
            ),
            sa.ForeignKeyConstraint(["lead_id"], ["leads_repair.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if table_exists(conn, "lead_interactions"):
        if not index_exists(conn, "lead_interactions", "ix_lead_interactions_created_at"):
            op.create_index(
                "ix_lead_interactions_created_at",
                "lead_interactions",
                ["created_at"],
                unique=False,
            )
        if not index_exists(conn, "lead_interactions", "ix_lead_interactions_event_name"):
            op.create_index(
                "ix_lead_interactions_event_name",
                "lead_interactions",
                ["event_name"],
                unique=False,
            )
        if not index_exists(conn, "lead_interactions", "ix_lead_interactions_cta_name"):
            op.create_index(
                "ix_lead_interactions_cta_name",
                "lead_interactions",
                ["cta_name"],
                unique=False,
            )
        if not index_exists(conn, "lead_interactions", "ix_lead_interactions_page_path"):
            op.create_index(
                "ix_lead_interactions_page_path",
                "lead_interactions",
                ["page_path"],
                unique=False,
            )
        if not index_exists(conn, "lead_interactions", "ix_lead_interactions_lead_id"):
            op.create_index(
                "ix_lead_interactions_lead_id",
                "lead_interactions",
                ["lead_id"],
                unique=False,
            )
        if not index_exists(conn, "lead_interactions", "ix_lead_interactions_lead_attempt_id"):
            op.create_index(
                "ix_lead_interactions_lead_attempt_id",
                "lead_interactions",
                ["lead_attempt_id"],
                unique=False,
            )
        if not index_exists(conn, "lead_interactions", "ix_lead_interactions_form_name"):
            op.create_index(
                "ix_lead_interactions_form_name",
                "lead_interactions",
                ["form_name"],
                unique=False,
            )


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "lead_interactions"):
        if index_exists(conn, "lead_interactions", "ix_lead_interactions_form_name"):
            op.drop_index("ix_lead_interactions_form_name", table_name="lead_interactions")
        if index_exists(conn, "lead_interactions", "ix_lead_interactions_lead_attempt_id"):
            op.drop_index("ix_lead_interactions_lead_attempt_id", table_name="lead_interactions")
        if index_exists(conn, "lead_interactions", "ix_lead_interactions_lead_id"):
            op.drop_index("ix_lead_interactions_lead_id", table_name="lead_interactions")
        if index_exists(conn, "lead_interactions", "ix_lead_interactions_page_path"):
            op.drop_index("ix_lead_interactions_page_path", table_name="lead_interactions")
        if index_exists(conn, "lead_interactions", "ix_lead_interactions_cta_name"):
            op.drop_index("ix_lead_interactions_cta_name", table_name="lead_interactions")
        if index_exists(conn, "lead_interactions", "ix_lead_interactions_event_name"):
            op.drop_index("ix_lead_interactions_event_name", table_name="lead_interactions")
        if index_exists(conn, "lead_interactions", "ix_lead_interactions_created_at"):
            op.drop_index("ix_lead_interactions_created_at", table_name="lead_interactions")
        op.drop_table("lead_interactions")
