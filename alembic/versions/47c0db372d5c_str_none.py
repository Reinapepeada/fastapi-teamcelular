"""str|none

Revision ID: 47c0db372d5c
Revises: b6797a0d08f0
Create Date: 2024-12-02 12:25:07.853401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47c0db372d5c'
down_revision: Union[str, None] = 'b6797a0d08f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('product_serial_number_key', 'product', type_='unique')
    op.create_index(op.f('ix_product_serial_number'), 'product', ['serial_number'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_product_serial_number'), table_name='product')
    op.create_unique_constraint('product_serial_number_key', 'product', ['serial_number'])
    # ### end Alembic commands ###
