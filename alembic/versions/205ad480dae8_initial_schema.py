"""initial_schema

Revision ID: 205ad480dae8
Revises: 
Create Date: 2025-11-25 13:49:00.343163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy import text, inspect


# revision identifiers, used by Alembic.
revision: str = '205ad480dae8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def enum_exists(conn, enum_name: str) -> bool:
    """Check if an enum type exists in PostgreSQL."""
    result = conn.execute(
        text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": enum_name}
    )
    return result.scalar() is not None


def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists."""
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    conn = op.get_bind()
    
    # Create ENUM types if they don't exist — handled by sa.Enum(create_type=True)
    
    # Create admin table
    if not table_exists(conn, 'admin'):
        op.create_table('admin',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('role', sa.Enum('SUPER_ADMIN', 'ADMIN', 'EDITOR', name='adminrole', create_type=True), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_admin_email'), 'admin', ['email'], unique=True)
        op.create_index(op.f('ix_admin_username'), 'admin', ['username'], unique=True)
    
    # Create branch table
    if not table_exists(conn, 'branch'):
        op.create_table('branch',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('location', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_branch_name'), 'branch', ['name'], unique=False)
    
    # Create brand table
    if not table_exists(conn, 'brand'):
        op.create_table('brand',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_brand_name'), 'brand', ['name'], unique=True)
    
    # Create category table
    if not table_exists(conn, 'category'):
        op.create_table('category',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_category_name'), 'category', ['name'], unique=True)
    
    # Create product table
    if not table_exists(conn, 'product'):
        op.create_table('product',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('serial_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('warranty_unit', sa.Enum('DAYS', 'MONTHS', 'YEARS', name='warrantyunit', create_type=True), nullable=True),
            sa.Column('warranty_time', sa.Integer(), nullable=True),
            sa.Column('cost', sa.Float(), nullable=False),
            sa.Column('retail_price', sa.Float(), nullable=False),
            sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DISCONTINUED', name='productstatus', create_type=True), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('brand_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.CheckConstraint('cost >= 0', name='check_cost_positive'),
            sa.CheckConstraint('retail_price >= 0', name='check_retail_price_positive'),
            sa.ForeignKeyConstraint(['brand_id'], ['brand.id'], ),
            sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name', 'category_id', 'brand_id', name='unique_product_per_category_brand')
        )
        op.create_index(op.f('ix_product_name'), 'product', ['name'], unique=False)
        op.create_index(op.f('ix_product_serial_number'), 'product', ['serial_number'], unique=True)
    
    # Create discount table
    if not table_exists(conn, 'discount'):
        op.create_table('discount',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('discount_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('value', sa.Float(), nullable=False),
            sa.Column('start_date', sa.DateTime(), nullable=True),
            sa.Column('end_date', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
            sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create productvariant table
    if not table_exists(conn, 'productvariant'):
        op.create_table('productvariant',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('sku', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('color', sa.Enum('ROJO', 'AZUL', 'VERDE', 'AMARILLO', 'NARANJA', 'VIOLETA', 'ROSADO', 'MARRON', 'GRIS', 'BLANCO', 'NEGRO', 'BORDO', name='color', create_type=True), nullable=True),
            sa.Column('size', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('size_unit', sa.Enum('CLOTHING', 'DIMENSIONS', 'WEIGHT', 'OTHER', name='sizeunit', create_type=True), nullable=True),
            sa.Column('unit', sa.Enum('KG', 'G', 'LB', 'CM', 'M', 'INCH', 'XS', 'S', 'L', 'XL', 'XXL', name='unit', create_type=True), nullable=True),
            sa.Column('branch_id', sa.Integer(), nullable=True),
            sa.Column('stock', sa.Integer(), nullable=False),
            sa.Column('min_stock', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.CheckConstraint('stock >= 0', name='check_stock_positive'),
            sa.ForeignKeyConstraint(['branch_id'], ['branch.id'], ),
            sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('product_id', 'color', 'size', 'size_unit', name='unique_variant_constraint')
        )
        op.create_index(op.f('ix_productvariant_min_stock'), 'productvariant', ['min_stock'], unique=False)
        op.create_index(op.f('ix_productvariant_size'), 'productvariant', ['size'], unique=False)
        op.create_index(op.f('ix_productvariant_sku'), 'productvariant', ['sku'], unique=True)
        op.create_index(op.f('ix_productvariant_stock'), 'productvariant', ['stock'], unique=False)
    
    # Create productimage table
    if not table_exists(conn, 'productimage'):
        op.create_table('productimage',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('variant_id', sa.Integer(), nullable=False),
            sa.Column('image_url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['variant_id'], ['productvariant.id'], ),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    conn = op.get_bind()
    
    if table_exists(conn, 'productimage'):
        op.drop_table('productimage')
    if table_exists(conn, 'productvariant'):
        op.drop_index(op.f('ix_productvariant_stock'), table_name='productvariant')
        op.drop_index(op.f('ix_productvariant_sku'), table_name='productvariant')
        op.drop_index(op.f('ix_productvariant_size'), table_name='productvariant')
        op.drop_index(op.f('ix_productvariant_min_stock'), table_name='productvariant')
        op.drop_table('productvariant')
    if table_exists(conn, 'discount'):
        op.drop_table('discount')
    if table_exists(conn, 'product'):
        op.drop_index(op.f('ix_product_serial_number'), table_name='product')
        op.drop_index(op.f('ix_product_name'), table_name='product')
        op.drop_table('product')
    if table_exists(conn, 'category'):
        op.drop_index(op.f('ix_category_name'), table_name='category')
        op.drop_table('category')
    if table_exists(conn, 'brand'):
        op.drop_index(op.f('ix_brand_name'), table_name='brand')
        op.drop_table('brand')
    if table_exists(conn, 'branch'):
        op.drop_index(op.f('ix_branch_name'), table_name='branch')
        op.drop_table('branch')
    if table_exists(conn, 'admin'):
        op.drop_index(op.f('ix_admin_username'), table_name='admin')
        op.drop_index(op.f('ix_admin_email'), table_name='admin')
        op.drop_table('admin')
