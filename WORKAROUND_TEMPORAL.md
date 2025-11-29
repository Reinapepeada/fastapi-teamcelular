# 🔧 Workaround Temporal - Permitir Variantes sin Color

## Problema

La base de datos no tiene aplicada la migración del enum `color`, por lo que no se pueden crear variantes.

## Solución Temporal

Modificar temporalmente el modelo `ProductVariant` para que el campo `color` acepte strings en lugar de enums.

### Cambios en `database/models/product.py`

**ANTES (línea 143):**
```python
color: Color | None = Eenum(Color, nullable=True, default=None, index=True)
```

**DESPUÉS:**
```python
color: str | None = Field(nullable=True, default=None, index=True, max_length=50)
```

### Pasos

1. Abrir `database/models/product.py`
2. Buscar la línea 143 en la clase `ProductVariant`
3. Reemplazar el campo `color` como se muestra arriba
4. Reiniciar el servidor de la API
5. Ejecutar el script `import_baterias.py`

### Revertir Después

**IMPORTANTE:** Una vez que se aplique la migración correcta en la base de datos, revertir este cambio para usar el enum `Color` nuevamente.

## Alternativa: Crear Variantes Manualmente

Si no se puede modificar el código del servidor, crear las variantes manualmente usando la interfaz web o directamente en la base de datos.

## Nota

Este es un **workaround temporal** y NO es la solución correcta. La solución correcta es aplicar la migración de Alembic como se describe en `PROBLEMA_MIGRACION.md`.
