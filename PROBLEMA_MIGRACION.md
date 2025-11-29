# ⚠️ Problema: Base de Datos Necesita Migración

## Error Actual

```
'VARCHAR(8)' is not among the defined enum values. Enum name: color
```

## Causa

La base de datos en el servidor **no tiene aplicada la migración** que convierte el campo `color` de `VARCHAR` a `ENUM`.

## Solución

El administrador del servidor debe ejecutar la migración de Alembic:

### Opción 1: Ejecutar Migración Específica

```bash
# Conectarse al servidor donde está desplegada la API
ssh usuario@servidor

# Ir al directorio del proyecto
cd /ruta/al/proyecto

# Ejecutar la migración
alembic upgrade fix_color_enum_optional_20251126
```

### Opción 2: Ejecutar Todas las Migraciones Pendientes

```bash
alembic upgrade head
```

### Opción 3: Ejecutar Migración Manualmente en PostgreSQL

Si no se puede usar Alembic, conectarse directamente a PostgreSQL:

```sql
-- 1. Crear el tipo ENUM si no existe
DO $
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'color') THEN
        CREATE TYPE color AS ENUM (
            'ROJO','AZUL','VERDE','AMARILLO','NARANJA','VIOLETA',
            'ROSADO','MARRON','GRIS','BLANCO','NEGRO','BORDO'
        );
    END IF;
END$;

-- 2. Limpiar valores inválidos
UPDATE productvariant
SET color = NULL
WHERE color IS NOT NULL
  AND color::text NOT IN (
    'ROJO','AZUL','VERDE','AMARILLO','NARANJA','VIOLETA',
    'ROSADO','MARRON','GRIS','BLANCO','NEGRO','BORDO'
  );

-- 3. Convertir columna a ENUM
ALTER TABLE productvariant
ALTER COLUMN color TYPE color USING (
    CASE 
        WHEN color IS NULL THEN NULL
        ELSE color::text::color
    END
);

-- 4. Hacer la columna nullable
ALTER TABLE productvariant
ALTER COLUMN color DROP NOT NULL;
```

## Verificar que la Migración se Aplicó

```bash
# Ver el estado de las migraciones
alembic current

# Debería mostrar:
# fix_color_enum_optional_20251126 (head)
```

## Después de Aplicar la Migración

Una vez aplicada la migración, el script `import_baterias.py` funcionará correctamente y podrá crear variantes con sus imágenes.

## Workaround Temporal (NO RECOMENDADO)

Si no se puede aplicar la migración inmediatamente, se podría:

1. Modificar el modelo para que `color` sea `str | None` en lugar de `Color | None`
2. Esto permitiría insertar valores NULL sin problemas
3. Pero NO es la solución correcta a largo plazo

## Archivos Relacionados

- Migración: `alembic/versions/fix_color_enum_optional_20251126.py`
- Modelo: `database/models/product.py` (línea 143)
- Servicio: `services/product_s.py`

## Contacto

Si eres el administrador del servidor y necesitas ayuda para aplicar la migración, contacta al equipo de desarrollo.
