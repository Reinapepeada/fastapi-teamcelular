# Cambios Realizados - Script de Importación de Baterías

## Problema Identificado

El script `import_baterias.py` no estaba creando correctamente las variantes de productos con sus imágenes. Los problemas eran:

1. **Imágenes duplicadas**: Cada vez que se ejecutaba el script, se agregaban imágenes nuevas sin eliminar las antiguas
2. **Variantes no se creaban**: El endpoint upsert fallaba silenciosamente
3. **Falta de manejo de errores**: No había información clara sobre qué estaba fallando

## Soluciones Implementadas

### 1. Servicio de Productos (`services/product_s.py`)

**Cambio en `upsert_product_variant_db()`:**

Se modificó la función para que **elimine las imágenes antiguas** antes de agregar las nuevas cuando se actualiza una variante existente:

```python
if existing_variant:
    # ACTUALIZAR variante existente
    existing_variant.branch_id = variant.branch_id
    existing_variant.stock = variant.stock
    existing_variant.min_stock = variant.min_stock
    session.commit()
    session.refresh(existing_variant)
    
    # Reemplazar imágenes si se proporcionan
    if variant.images is not None:
        # Eliminar imágenes antiguas
        old_images = session.exec(
            select(ProductImage).where(ProductImage.variant_id == existing_variant.id)
        ).all()
        for img in old_images:
            session.delete(img)
        session.commit()
        
        # Agregar nuevas imágenes
        if variant.images:  # Solo si la lista no está vacía
            persist_product_images(variant.images, existing_variant.id, session)
```

**Beneficios:**
- ✅ No más imágenes duplicadas
- ✅ Las imágenes se reemplazan correctamente en cada ejecución
- ✅ Mantiene la base de datos limpia

### 2. Script de Importación (`scripts/import_baterias.py`)

**Simplificación de `crear_variante()`:**

Se simplificó la función para confiar en el endpoint `upsert` que ahora funciona correctamente:

```python
def crear_variante(token, product_id, branch_id, imagenes_urls):
    """Crea o actualiza una variante del producto con sus imágenes."""
    headers = {"Authorization": f"Bearer {token}"}

    # Payload con campos explícitos en None para productos sin variaciones
    payload = {
        "variants": [{
            "product_id": product_id,
            "branch_id": branch_id,
            "color": None,
            "size": None,
            "size_unit": None,
            "unit": None,
            "stock": 10,
            "min_stock": 2,
            "images": imagenes_urls if imagenes_urls else []
        }]
    }

    print(f"   ▶️ Creando/actualizando variante con {len(imagenes_urls)} imagen(es)...")
    
    # Usar upsert que ahora reemplaza las imágenes correctamente
    response = requests.put(
        f"{API_URL}/products/upsert/variant",
        headers=headers,
        json=payload
    )

    if response.status_code in [200, 201]:
        print(f"  ✅ Variante creada/actualizada con {len(imagenes_urls)} imagen(es)")
        return True
    else:
        print(f"  ⚠️ Error en upsert (status {response.status_code}): {response.text[:300]}")
        
        # Intentar crear si no existe
        print("   ▶️ Intentando crear variante...")
        create_resp = requests.post(
            f"{API_URL}/products/create/variant",
            headers=headers,
            json=payload
        )
        
        if create_resp.status_code in [200, 201]:
            print(f"  ✅ Variante creada con {len(imagenes_urls)} imagen(es)")
            return True
        else:
            print(f"  ⚠️ Error creando variante: {create_resp.text[:300]}")
            return False
```

**Beneficios:**
- ✅ Código más simple y mantenible
- ✅ Mejor manejo de errores con mensajes claros
- ✅ Fallback automático si upsert falla

### 3. Documentación (`scripts/README.md`)

Se actualizó el README para incluir:
- Información sobre cómo funcionan las variantes
- Explicación de que las imágenes se reemplazan en cada ejecución
- Nuevos errores comunes y sus soluciones

## Cómo Usar

1. **Preparar imágenes** en las carpetas correspondientes (ej: `scripts/imagenes_baterias/12M/`)
2. **Ejecutar el script**: `python scripts/import_baterias.py`
3. **Ingresar credenciales** de admin
4. El script:
   - Crea productos si no existen
   - Actualiza productos existentes
   - Crea variantes con imágenes
   - **Reemplaza imágenes antiguas** si ejecutas el script nuevamente

## Resultado Esperado

Cada batería tendrá:
- ✅ Un producto con información completa
- ✅ Una variante (sin color/talla, producto simple)
- ✅ Imágenes asociadas a la variante
- ✅ Stock configurado (10 unidades por defecto)

## Notas Técnicas

- Las variantes se identifican por: `product_id + color + size + size_unit + unit`
- Para productos simples (sin variaciones), todos estos campos son `None`
- El endpoint `upsert` ahora elimina imágenes antiguas antes de agregar nuevas
- Si una variante ya existe, se actualiza; si no, se crea
