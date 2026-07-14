"""add preferred branch to repair leads

Revision ID: add_lead_branch_20260714
Revises: add_interaction_type_20260428
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = "add_lead_branch_20260714"
down_revision = "add_interaction_type_20260428"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leads_repair", sa.Column("preferred_branch", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column("leads_repair", sa.Column("branch_selection_method", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_index(op.f("ix_leads_repair_preferred_branch"), "leads_repair", ["preferred_branch"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_leads_repair_preferred_branch"), table_name="leads_repair")
    op.drop_column("leads_repair", "branch_selection_method")
    op.drop_column("leads_repair", "preferred_branch")
