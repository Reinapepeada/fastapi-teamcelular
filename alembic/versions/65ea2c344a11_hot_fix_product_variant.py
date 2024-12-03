"""HOT FIX PRODUCT VARIANT

Revision ID: 65ea2c344a11
Revises: 350da6752ee9
Create Date: 2024-12-02 14:08:52.945717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65ea2c344a11'
down_revision: Union[str, None] = '350da6752ee9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('productvariant', sa.Column('created_at', sa.DateTime()))
    op.add_column('productvariant', sa.Column('updated_at', sa.DateTime()))
    op.drop_index('ix_productvariant_sku', table_name='productvariant')
    op.create_index(op.f('ix_productvariant_sku'), 'productvariant', ['sku'], unique=True)
    # Actualizar las columnas created_at que son NULL con la fecha y hora actual
    op.execute(
        sa.text("UPDATE productvariant SET created_at = NOW() WHERE created_at IS NULL")
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_productvariant_sku'), table_name='productvariant')
    op.create_index('ix_productvariant_sku', 'productvariant', ['sku'], unique=False)
    op.drop_column('productvariant', 'updated_at')
    op.drop_column('productvariant', 'created_at')
    # ### end Alembic commands ###