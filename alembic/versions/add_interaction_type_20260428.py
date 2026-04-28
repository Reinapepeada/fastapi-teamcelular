"""add interaction_type and occurred_at to lead_interactions

Revision ID: add_interaction_type_20260428
Revises: add_lead_attempt_id_20260427
Create Date: 2026-04-28

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'add_interaction_type_20260428'
down_revision = 'add_lead_attempt_id_20260427'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('lead_interactions', sa.Column('interaction_type', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_index(op.f('ix_lead_interactions_interaction_type'), 'lead_interactions', ['interaction_type'], unique=False)
    
    op.add_column('lead_interactions', sa.Column('occurred_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_lead_interactions_occurred_at'), 'lead_interactions', ['occurred_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_lead_interactions_occurred_at'), table_name='lead_interactions')
    op.drop_column('lead_interactions', 'occurred_at')
    
    op.drop_index(op.f('ix_lead_interactions_interaction_type'), table_name='lead_interactions')
    op.drop_column('lead_interactions', 'interaction_type')
