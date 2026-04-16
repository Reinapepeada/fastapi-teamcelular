"""add_repair_leads

Revision ID: add_repair_leads_20260416
Revises: add_idx_variant_unit_20260113
Create Date: 2026-04-16

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "add_repair_leads_20260416"
down_revision = "add_idx_variant_unit_20260113"
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

    if not table_exists(conn, "leads_repair"):
        op.create_table(
            "leads_repair",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("brand", sa.String(length=80), nullable=False),
            sa.Column("model", sa.String(length=80), nullable=False),
            sa.Column("repair_type", sa.String(length=120), nullable=False),
            sa.Column("urgency", sa.String(length=20), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("contact_channel", sa.String(length=20), nullable=False),
            sa.Column("contact", sa.String(length=120), nullable=False),
            sa.Column("wizard_source", sa.String(length=120), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("duplicate_of", sa.String(length=36), nullable=True),
            sa.Column("fingerprint_hash", sa.String(length=64), nullable=False),
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
            sa.Column("payload_hash", sa.String(length=64), nullable=True),
            sa.Column("utm_source", sa.String(length=120), nullable=True),
            sa.Column("utm_medium", sa.String(length=120), nullable=True),
            sa.Column("utm_campaign", sa.String(length=120), nullable=True),
            sa.Column("utm_content", sa.String(length=120), nullable=True),
            sa.Column("utm_term", sa.String(length=120), nullable=True),
            sa.Column("ip", sa.String(length=80), nullable=True),
            sa.Column("user_agent", sa.String(length=400), nullable=True),
            sa.Column("referrer", sa.String(length=400), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint(
                "urgency IN ('hoy', 'esta_semana', 'sin_urgencia')",
                name="ck_leads_repair_urgency",
            ),
            sa.CheckConstraint(
                "contact_channel IN ('whatsapp', 'llamada', 'email')",
                name="ck_leads_repair_contact_channel",
            ),
            sa.CheckConstraint(
                "status IN ('new', 'contacted', 'qualified', 'discarded', 'converted', 'duplicated')",
                name="ck_leads_repair_status",
            ),
            sa.ForeignKeyConstraint(["duplicate_of"], ["leads_repair.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idempotency_key", name="uq_leads_repair_idempotency_key"),
        )

    if table_exists(conn, "leads_repair"):
        if not index_exists(conn, "leads_repair", "ix_leads_repair_created_at"):
            op.create_index("ix_leads_repair_created_at", "leads_repair", ["created_at"], unique=False)
        if not index_exists(conn, "leads_repair", "ix_leads_repair_status"):
            op.create_index("ix_leads_repair_status", "leads_repair", ["status"], unique=False)
        if not index_exists(conn, "leads_repair", "ix_leads_repair_repair_type"):
            op.create_index("ix_leads_repair_repair_type", "leads_repair", ["repair_type"], unique=False)
        if not index_exists(conn, "leads_repair", "ix_leads_repair_urgency"):
            op.create_index("ix_leads_repair_urgency", "leads_repair", ["urgency"], unique=False)
        if not index_exists(conn, "leads_repair", "ix_leads_repair_contact_channel"):
            op.create_index(
                "ix_leads_repair_contact_channel",
                "leads_repair",
                ["contact_channel"],
                unique=False,
            )
        if not index_exists(conn, "leads_repair", "ix_leads_repair_fingerprint_hash"):
            op.create_index(
                "ix_leads_repair_fingerprint_hash",
                "leads_repair",
                ["fingerprint_hash"],
                unique=False,
            )
        if not index_exists(conn, "leads_repair", "ix_leads_repair_duplicate_of"):
            op.create_index(
                "ix_leads_repair_duplicate_of", "leads_repair", ["duplicate_of"], unique=False
            )
        if not index_exists(conn, "leads_repair", "ix_leads_repair_idempotency_key"):
            op.create_index(
                "ix_leads_repair_idempotency_key",
                "leads_repair",
                ["idempotency_key"],
                unique=True,
            )

    if not table_exists(conn, "lead_status_history"):
        op.create_table(
            "lead_status_history",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lead_id", sa.String(length=36), nullable=False),
            sa.Column("old_status", sa.String(length=20), nullable=True),
            sa.Column("new_status", sa.String(length=20), nullable=False),
            sa.Column("changed_by", sa.String(length=80), nullable=False),
            sa.Column("changed_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint(
                "new_status IN ('new', 'contacted', 'qualified', 'discarded', 'converted', 'duplicated')",
                name="ck_lead_status_history_new_status",
            ),
            sa.ForeignKeyConstraint(["lead_id"], ["leads_repair.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if table_exists(conn, "lead_status_history"):
        if not index_exists(conn, "lead_status_history", "ix_lead_status_history_lead_id"):
            op.create_index(
                "ix_lead_status_history_lead_id",
                "lead_status_history",
                ["lead_id"],
                unique=False,
            )
        if not index_exists(conn, "lead_status_history", "ix_lead_status_history_changed_at"):
            op.create_index(
                "ix_lead_status_history_changed_at",
                "lead_status_history",
                ["changed_at"],
                unique=False,
            )

    if not table_exists(conn, "lead_notes"):
        op.create_table(
            "lead_notes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lead_id", sa.String(length=36), nullable=False),
            sa.Column("note", sa.Text(), nullable=False),
            sa.Column("created_by", sa.String(length=80), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["lead_id"], ["leads_repair.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if table_exists(conn, "lead_notes"):
        if not index_exists(conn, "lead_notes", "ix_lead_notes_lead_id"):
            op.create_index("ix_lead_notes_lead_id", "lead_notes", ["lead_id"], unique=False)
        if not index_exists(conn, "lead_notes", "ix_lead_notes_created_at"):
            op.create_index(
                "ix_lead_notes_created_at", "lead_notes", ["created_at"], unique=False
            )


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "lead_notes"):
        if index_exists(conn, "lead_notes", "ix_lead_notes_created_at"):
            op.drop_index("ix_lead_notes_created_at", table_name="lead_notes")
        if index_exists(conn, "lead_notes", "ix_lead_notes_lead_id"):
            op.drop_index("ix_lead_notes_lead_id", table_name="lead_notes")
        op.drop_table("lead_notes")

    if table_exists(conn, "lead_status_history"):
        if index_exists(conn, "lead_status_history", "ix_lead_status_history_changed_at"):
            op.drop_index("ix_lead_status_history_changed_at", table_name="lead_status_history")
        if index_exists(conn, "lead_status_history", "ix_lead_status_history_lead_id"):
            op.drop_index("ix_lead_status_history_lead_id", table_name="lead_status_history")
        op.drop_table("lead_status_history")

    if table_exists(conn, "leads_repair"):
        if index_exists(conn, "leads_repair", "ix_leads_repair_idempotency_key"):
            op.drop_index("ix_leads_repair_idempotency_key", table_name="leads_repair")
        if index_exists(conn, "leads_repair", "ix_leads_repair_duplicate_of"):
            op.drop_index("ix_leads_repair_duplicate_of", table_name="leads_repair")
        if index_exists(conn, "leads_repair", "ix_leads_repair_fingerprint_hash"):
            op.drop_index("ix_leads_repair_fingerprint_hash", table_name="leads_repair")
        if index_exists(conn, "leads_repair", "ix_leads_repair_contact_channel"):
            op.drop_index("ix_leads_repair_contact_channel", table_name="leads_repair")
        if index_exists(conn, "leads_repair", "ix_leads_repair_urgency"):
            op.drop_index("ix_leads_repair_urgency", table_name="leads_repair")
        if index_exists(conn, "leads_repair", "ix_leads_repair_repair_type"):
            op.drop_index("ix_leads_repair_repair_type", table_name="leads_repair")
        if index_exists(conn, "leads_repair", "ix_leads_repair_status"):
            op.drop_index("ix_leads_repair_status", table_name="leads_repair")
        if index_exists(conn, "leads_repair", "ix_leads_repair_created_at"):
            op.drop_index("ix_leads_repair_created_at", table_name="leads_repair")
        op.drop_table("leads_repair")
