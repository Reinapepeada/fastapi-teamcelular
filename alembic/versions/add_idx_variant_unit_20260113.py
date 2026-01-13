"""add_idx_variant_unit

Revision ID: add_idx_variant_unit_20260113
Revises: fix_color_enum_optional_20251126
Create Date: 2026-01-13

"""

from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "add_idx_variant_unit_20260113"
down_revision = "fix_color_enum_optional_20251126"
branch_labels = None
depends_on = None


def table_exists(conn, table_name: str) -> bool:
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def index_exists(conn, table_name: str, index_name: str) -> bool:
    inspector = inspect(conn)
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def unique_constraint_exists(conn, table_name: str, constraint_name: str) -> bool:
    inspector = inspect(conn)
    return constraint_name in {c["name"] for c in inspector.get_unique_constraints(table_name)}


def upgrade() -> None:
    conn = op.get_bind()

    # Índices útiles para filtros/listados (PostgreSQL no indexa FKs automáticamente)
    if table_exists(conn, "product"):
        if not index_exists(conn, "product", "ix_product_brand_id"):
            op.create_index("ix_product_brand_id", "product", ["brand_id"], unique=False)
        if not index_exists(conn, "product", "ix_product_category_id"):
            op.create_index("ix_product_category_id", "product", ["category_id"], unique=False)

    if table_exists(conn, "productvariant"):
        if not index_exists(conn, "productvariant", "ix_productvariant_product_id"):
            op.create_index(
                "ix_productvariant_product_id", "productvariant", ["product_id"], unique=False
            )
        if not index_exists(conn, "productvariant", "ix_productvariant_branch_id"):
            op.create_index(
                "ix_productvariant_branch_id", "productvariant", ["branch_id"], unique=False
            )

        # Mantener consistencia con el código: la unicidad incluye `unit`
        # (solo se altera en PostgreSQL para evitar limitaciones de SQLite con DROP CONSTRAINT).
        if conn.dialect.name == "postgresql":
            if unique_constraint_exists(conn, "productvariant", "unique_variant_constraint"):
                op.drop_constraint("unique_variant_constraint", "productvariant", type_="unique")
            op.create_unique_constraint(
                "unique_variant_constraint",
                "productvariant",
                ["product_id", "color", "size", "size_unit", "unit"],
            )

    if table_exists(conn, "productimage"):
        if not index_exists(conn, "productimage", "ix_productimage_variant_id"):
            op.create_index(
                "ix_productimage_variant_id", "productimage", ["variant_id"], unique=False
            )


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "productimage"):
        if index_exists(conn, "productimage", "ix_productimage_variant_id"):
            op.drop_index("ix_productimage_variant_id", table_name="productimage")

    if table_exists(conn, "productvariant"):
        if conn.dialect.name == "postgresql":
            if unique_constraint_exists(conn, "productvariant", "unique_variant_constraint"):
                op.drop_constraint("unique_variant_constraint", "productvariant", type_="unique")
            op.create_unique_constraint(
                "unique_variant_constraint",
                "productvariant",
                ["product_id", "color", "size", "size_unit"],
            )

        if index_exists(conn, "productvariant", "ix_productvariant_branch_id"):
            op.drop_index("ix_productvariant_branch_id", table_name="productvariant")
        if index_exists(conn, "productvariant", "ix_productvariant_product_id"):
            op.drop_index("ix_productvariant_product_id", table_name="productvariant")

    if table_exists(conn, "product"):
        if index_exists(conn, "product", "ix_product_category_id"):
            op.drop_index("ix_product_category_id", table_name="product")
        if index_exists(conn, "product", "ix_product_brand_id"):
            op.drop_index("ix_product_brand_id", table_name="product")
