"""fix_color_enum_optional

Revision ID: fix_color_enum_optional_20251126
Revises: 205ad480dae8
Create Date: 2025-11-26 18:50:00.000000

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'fix_color_enum_optional_20251126'
down_revision = '205ad480dae8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Create enum type `color` if it doesn't exist
    conn.execute(text("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'color') THEN
            CREATE TYPE color AS ENUM (
                'ROJO','AZUL','VERDE','AMARILLO','NARANJA','VIOLETA','ROSADO','MARRON','GRIS','BLANCO','NEGRO','BORDO'
            );
        END IF;
    END$$;
    """))

    # 2) Clean invalid values in productvariant.color (set to NULL)
    #    This works whether the column is currently varchar or enum.
    conn.execute(text("""
    UPDATE productvariant
    SET color = NULL
    WHERE color IS NOT NULL
      AND color::text NOT IN (
        'ROJO','AZUL','VERDE','AMARILLO','NARANJA','VIOLETA','ROSADO','MARRON','GRIS','BLANCO','NEGRO','BORDO'
      );
    """))

    # 3) Alter column type to the enum `color` if not already of that type
    #    Use information_schema to check current udt_name.
    udt = conn.execute(text("""
        SELECT udt_name
        FROM information_schema.columns
        WHERE table_name = 'productvariant' AND column_name = 'color'
    """ )).scalar()

    if udt != 'color':
        # Cast existing textual values (now cleaned) to the enum type
        conn.execute(text("""
        ALTER TABLE productvariant
        ALTER COLUMN color TYPE color USING (color::text::color);
        """))

    # 4) Ensure the column is nullable (optional)
    conn.execute(text("""
    ALTER TABLE productvariant
    ALTER COLUMN color DROP NOT NULL;
    """))


def downgrade() -> None:
    conn = op.get_bind()

    # Downgrade: convert enum back to varchar and drop type if desired
    udt = conn.execute(text("""
        SELECT udt_name
        FROM information_schema.columns
        WHERE table_name = 'productvariant' AND column_name = 'color'
    """ )).scalar()

    if udt == 'color':
        conn.execute(text("""
        ALTER TABLE productvariant
        ALTER COLUMN color TYPE varchar(50) USING (color::text);
        """))

    # Optionally drop the type if no longer used (commented out to be safe)
    # conn.execute(text("DROP TYPE IF EXISTS color;"))
