# 🔄 Lógica de Upsert Inteligente - Guía Técnica

## Resumen Ejecutivo

El sistema de carga masiva implementa una **lógica de upsert inteligente** que:

1. ✅ **Previene duplicados** automáticamente
2. ✅ **Detecta cambios** en productos y variantes
3. ✅ **Actualiza solo lo necesario** (ahorra tiempo y recursos)
4. ✅ **Omite datos sin cambios** (evita operaciones innecesarias)

## Algoritmo de Procesamiento

### Flujo Principal

```
Para cada fila en el Excel:
│
├─ 1. Validar datos requeridos
│   ├─ serial_number, name, cost, retail_price
│   └─ Si falta alguno → Error
│
├─ 2. Verificar si producto existe (por serial_number)
│   │
│   ├─ SI EXISTE:
│   │   ├─ Comparar todos los campos actualizables
│   │   ├─ SI hay cambios:
│   │   │   └─ ✅ Actualizar producto
│   │   └─ SI NO hay cambios:
│   │       └─ ⏭️ Omitir (producto ya está actualizado)
│   │
│   └─ NO EXISTE:
│       └─ ✅ Crear nuevo producto
│
└─ 3. Procesar variante (si se especifica variant_branch_id)
    │
    ├─ Buscar variante existente por:
    │   product_id + color + size + size_unit + unit
    │
    ├─ SI EXISTE:
    │   ├─ Comparar: branch_id, stock, min_stock, images
    │   ├─ SI hay cambios:
    │   │   └─ ✅ Actualizar variante
    │   └─ SI NO hay cambios:
    │       └─ ⏭️ Omitir (variante ya está actualizada)
    │
    └─ NO EXISTE:
        └─ ✅ Crear nueva variante
```

## Comparación de Productos

### Campos Comparados

| Campo | Tipo | Actualizable | Nota |
|-------|------|--------------|------|
| `serial_number` | String | ❌ NO | Identificador único |
| `id` | Integer | ❌ NO | Primary key |
| `name` | String | ✅ SÍ | Nombre del producto |
| `description` | String/Null | ✅ SÍ | Descripción |
| `brand_id` | Integer/Null | ✅ SÍ | ID de marca |
| `category_id` | Integer/Null | ✅ SÍ | ID de categoría |
| `warranty_time` | Integer/Null | ✅ SÍ | Tiempo de garantía |
| `warranty_unit` | Enum/Null | ✅ SÍ | Unidad de garantía |
| `cost` | Float | ✅ SÍ | Costo del producto |
| `retail_price` | Float | ✅ SÍ | Precio de venta |
| `status` | Enum | ✅ SÍ | Estado del producto |

### Función de Comparación

```python
def product_has_changes(existing_product, new_data) -> (bool, List[str]):
    """
    Retorna:
    - bool: True si hay al menos un cambio
    - List[str]: Lista de cambios detectados
    """
    changes = []
    
    if existing_product.name != new_data.name:
        changes.append(f"name: '{existing_product.name}' -> '{new_data.name}'")
    
    if existing_product.cost != new_data.cost:
        changes.append(f"cost: {existing_product.cost} -> {new_data.cost}")
    
    # ... más comparaciones
    
    return len(changes) > 0, changes
```

## Comparación de Variantes

### Identificador Único de Variante

Una variante es única por la combinación de:

```python
unique_key = (
    product_id,    # ID del producto padre
    color,         # Color (puede ser NULL)
    size,          # Tamaño (puede ser NULL)
    size_unit,     # Unidad de tamaño (puede ser NULL)
    unit          # Unidad (puede ser NULL)
)
```

### Campos Comparados

| Campo | Tipo | Actualizable | Nota |
|-------|------|--------------|------|
| `product_id` | Integer | ❌ NO | Parte del identificador |
| `color` | Enum/Null | ❌ NO | Parte del identificador |
| `size` | String/Null | ❌ NO | Parte del identificador |
| `size_unit` | Enum/Null | ❌ NO | Parte del identificador |
| `unit` | Enum/Null | ❌ NO | Parte del identificador |
| `sku` | String | ❌ NO | Generado automáticamente |
| `branch_id` | Integer | ✅ SÍ | Sucursal donde está |
| `stock` | Integer | ✅ SÍ | Stock disponible |
| `min_stock` | Integer | ✅ SÍ | Stock mínimo |
| `images` | List[String] | ✅ SÍ | URLs de imágenes |

### Función de Comparación

```python
def variant_has_changes(existing_variant, new_data) -> (bool, List[str]):
    """
    Retorna:
    - bool: True si hay al menos un cambio
    - List[str]: Lista de cambios detectados
    """
    changes = []
    
    if existing_variant.branch_id != new_data.branch_id:
        changes.append(f"branch_id: {existing_variant.branch_id} -> {new_data.branch_id}")
    
    if existing_variant.stock != new_data.stock:
        changes.append(f"stock: {existing_variant.stock} -> {new_data.stock}")
    
    # ... más comparaciones
    
    return len(changes) > 0, changes
```

## Manejo de Imágenes

### Lógica Especial

1. **Imágenes desde Rutas Locales**:
   - Se convierten a Base64 data URLs
   - Se almacenan directamente en la BD

2. **Imágenes ya Cargadas** (al exportar):
   - Se marca como `[N imágenes ya cargadas en BD]`
   - Al reimportar, esta marca se detecta y se omite

3. **Actualización de Imágenes**:
   - Si se proporcionan nuevas rutas → Reemplaza todas las imágenes
   - Si NO se proporcionan rutas → Mantiene imágenes existentes

```python
# Detectar marca de imágenes ya cargadas
if image_paths and not any('[' in str(p) and 'imágenes ya cargadas' in str(p) 
                           for p in image_paths):
    # Procesar imágenes nuevas desde rutas
    for img_path in image_paths:
        base64_url = image_to_base64(img_path)
        image_urls.append(base64_url)
```

## Ejemplos Prácticos

### Ejemplo 1: Actualización Simple

**Excel (nueva versión)**:
```
serial_number | name              | cost   | retail_price
BAT-IP12-001 | Batería iPhone 12 | 25000  | 50000
```

**Base de Datos (versión actual)**:
```
serial_number | name              | cost   | retail_price
BAT-IP12-001 | Batería iPhone 12 | 25000  | 45000
```

**Resultado**:
```
✅ Producto actualizado: retail_price: 45000 -> 50000
```

### Ejemplo 2: Sin Cambios

**Excel y BD tienen datos idénticos**

**Resultado**:
```
⏭️ Producto omitido (sin cambios)
```

### Ejemplo 3: Nueva Variante

**Excel**:
```
serial_number | variant_color | variant_stock
BAT-IP12-001 | AZUL         | 30
```

**BD (variantes existentes)**:
```
serial_number | variant_color | variant_stock
BAT-IP12-001 | NEGRO        | 50
BAT-IP12-001 | BLANCO       | 20
```

**Resultado**:
```
✅ Variante AZUL creada
⏭️ Variantes NEGRO y BLANCO omitidas (no están en el Excel)
```

### Ejemplo 4: Actualizar Stock de Variante

**Excel**:
```
serial_number | variant_color | variant_stock
BAT-IP12-001 | NEGRO        | 75
```

**BD**:
```
serial_number | variant_color | variant_stock
BAT-IP12-001 | NEGRO        | 50
```

**Resultado**:
```
✅ Variante NEGRO actualizada: stock: 50 -> 75
```

## Ventajas del Sistema

### 1. Eficiencia
- Solo actualiza lo que cambió
- Evita writes innecesarias a la BD
- Reduce tiempo de procesamiento

### 2. Seguridad
- Previene duplicados automáticamente
- Validaciones en cada paso
- Reportes detallados de todas las operaciones

### 3. Flexibilidad
- Permite mezclar operaciones (crear + actualizar)
- Soporta actualizaciones parciales
- Maneja casos edge (NULL values, campos opcionales)

### 4. Trazabilidad
- Reporta exactamente qué cambió
- Distingue entre creado, actualizado y omitido
- Logs detallados de errores y warnings

## Reporte de Resultados

```json
{
  "total_rows": 100,
  "successful": 95,           // Filas procesadas exitosamente
  "failed": 2,                // Filas con error
  "skipped": 30,              // Productos sin cambios (omitidos)
  "updated_products": 10,     // Productos actualizados
  "updated_variants": 15,     // Variantes actualizadas
  "created_products": ["..."], // IDs de productos creados
  "created_variants": ["..."], // SKUs de variantes creadas
  "updated_products_list": ["..."],
  "updated_variants_list": ["..."],
  "skipped_products": ["..."],
  "errors": [...],
  "warnings": [...]
}
```

## Consideraciones Técnicas

### Performance

- **Comparaciones**: O(1) por producto/variante
- **Búsqueda en BD**: Usa índices en serial_number y campos de variante
- **Transacciones**: Cada fila se procesa en su propia transacción (rollback individual)

### Manejo de NULL

El sistema maneja correctamente NULL values usando comparaciones SQL apropiadas:

```python
# Comparación correcta de NULL
if color is None:
    conditions.append(ProductVariant.color.is_(None))
else:
    conditions.append(ProductVariant.color == color)
```

### Validaciones de Integridad

Antes de actualizar, se valida:
- IDs de relaciones existen (brand_id, category_id, branch_id)
- Valores de enums son válidos
- Campos numéricos son >= 0
- Campos requeridos no son NULL

---

**Última actualización**: Enero 2026
