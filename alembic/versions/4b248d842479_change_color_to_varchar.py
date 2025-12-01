"""change_color_to_varchar

Revision ID: 4b248d842479
Revises: fix_color_enum_optional_20251126
Create Date: 2025-11-29 19:28:48.362065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '4b248d842479'
down_revision: Union[str, None] = 'fix_color_enum_optional_20251126'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cambiar el campo color de ENUM a VARCHAR(50) para mayor flexibilidad"""
    conn = op.get_bind()
    
    # 1. Verificar el tipo actual de la columna
    udt = conn.execute(text("""
        SELECT udt_name
        FROM information_schema.columns
        WHERE table_name = 'productvariant' AND column_name = 'color'
    """)).scalar()
    
    # 2. Si es un enum, convertir a varchar
    if udt == 'color':
        # Convertir enum a varchar
        conn.execute(text("""
            ALTER TABLE productvariant
            ALTER COLUMN color TYPE varchar(50) USING (color::text);
        """))
        
        # Opcional: Eliminar el tipo enum si no se usa en ningún otro lugar
        # Verificar si hay otras columnas usando el tipo 'color'
        other_uses = conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE udt_name = 'color' AND table_name != 'productvariant'
        """)).scalar()
        
        if other_uses == 0:
            # Eliminar el tipo enum ya que no se usa en ningún otro lugar
            conn.execute(text("DROP TYPE IF EXISTS color;"))
    
    # 3. Asegurar que la columna sea nullable
    conn.execute(text("""
        ALTER TABLE productvariant
        ALTER COLUMN color DROP NOT NULL;
    """))


def downgrade() -> None:
    """Revertir: cambiar color de VARCHAR a ENUM"""
    conn = op.get_bind()
    
    # 1. Recrear el tipo enum si no existe
    conn.execute(text("""
        DO $
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'color') THEN
                CREATE TYPE color AS ENUM (
                    'ROJO','AZUL','VERDE','AMARILLO','NARANJA','VIOLETA',
                    'ROSADO','MARRON','GRIS','BLANCO','NEGRO','BORDO'
                );
            END IF;
        END$;
    """))
    
    # 2. Limpiar valores que no sean válidos para el enum
    conn.execute(text("""
        UPDATE productvariant
        SET color = NULL
        WHERE color IS NOT NULL
          AND color NOT IN (
            'ROJO','AZUL','VERDE','AMARILLO','NARANJA','VIOLETA',
            'ROSADO','MARRON','GRIS','BLANCO','NEGRO','BORDO'
          );
    """))
    
    # 3. Convertir la columna de varchar a enum
    conn.execute(text("""
        ALTER TABLE productvariant
        ALTER COLUMN color TYPE color USING (
            CASE 
                WHEN color IS NULL THEN NULL
                ELSE color::color
            END
        );
    """))
