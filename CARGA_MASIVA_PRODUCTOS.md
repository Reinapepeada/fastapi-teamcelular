# Guía de Carga Masiva de Productos

## 📋 Descripción

Esta funcionalidad permite cargar productos de forma masiva utilizando un archivo Excel. Incluye la capacidad de crear productos, variantes, subir imágenes desde rutas locales, y **actualizar productos existentes de forma inteligente**.

## 🎯 Características Principales

- ✅ **Carga masiva** de productos y variantes desde Excel
- ✅ **Template descargable** con ejemplos y hoja de referencia
- ✅ **Exportación de productos existentes** para facilitar actualizaciones
- ✅ **Upsert inteligente**: detecta automáticamente cambios y actualiza
- ✅ **Prevención de duplicados**: no crea productos/variantes duplicadas
- ✅ **Carga de imágenes** desde rutas locales (convertidas a Base64)
- ✅ **Validaciones automáticas** de IDs y valores
- ✅ **Manejo inteligente de errores** (continúa procesando o detiene)
- ✅ **Reporte detallado** de creaciones, actualizaciones, omisiones y errores

## 🚀 Endpoints Disponibles

### 1. Descargar Template Excel Vacío
```
GET /product/bulk-upload/template
```
- **Autenticación**: No requerida (público)
- **Descripción**: Descarga un archivo Excel template vacío con ejemplos y referencias
- **Respuesta**: Archivo `template_carga_productos.xlsx`
- **Uso**: Para empezar desde cero con nuevos productos

### 2. Exportar Productos Existentes
```
GET /product/bulk-upload/export
```
- **Autenticación**: Requerida (Editor o superior)
- **Descripción**: Exporta todos los productos actuales de la base de datos a Excel
- **Respuesta**: Archivo `productos_exportados_[fecha].xlsx`
- **Uso**: Para actualizar productos existentes o agregar nuevos

### 3. Cargar Productos Masivamente
```
POST /product/bulk-upload
```
- **Autenticación**: Requerida (Editor o superior)
- **Content-Type**: multipart/form-data
- **Parámetros**:
  - `file`: Archivo Excel (.xlsx)
  - `skip_errors`: (opcional, default: true) Si es true, continúa procesando aunque haya errores

**Ejemplo de respuesta**:
```json
{
  "total_rows": 100,
  "successful": 95,
  "failed": 2,
  "skipped": 3,
  "updated_products": 10,
  "updated_variants": 15,
  "errors": [
    {
      "row": 10,
      "serial_number": "BAT-001",
      "error": "Categoría con id 999 no existe"
    }
  ],
  "warnings": [
    {
      "row": 15,
      "message": "Producto BAT-002 actualizado: cost: 25000 -> 27000"
    }
  ],
  "created_products": ["BAT-003", "CASE-001"],
  "created_variants": ["BAT-003-NEGRO-1", "CASE-001-AZUL-1"],
  "skipped_products": ["BAT-002"],
  "updated_products_list": ["BAT-004", "CASE-002"],
  "updated_variants_list": ["BAT-004-BLANCO-1"]
}
```

## 🔄 Lógica de Upsert Inteligente

### Cuando un Producto ya Existe (mismo serial_number)

El sistema compara los datos nuevos con los existentes:

**Campos Comparados**:
- name
- description
- brand_id
- category_id
- warranty_time
- warranty_unit
- cost
- retail_price
- status

**Comportamiento**:
- ✅ **Con cambios**: Actualiza el producto automáticamente
- ⏭️ **Sin cambios**: Omite el producto (no hace nada)
- ℹ️ **Reporte**: Indica qué campos cambiaron

### Cuando una Variante ya Existe

Una variante es única por la combinación de: `product_id` + `color` + `size` + `size_unit` + `unit`

**Campos Comparados**:
- branch_id
- stock
- min_stock
- images (si se proporcionan nuevas)

**Comportamiento**:
- ✅ **Con cambios**: Actualiza la variante automáticamente
- ⏭️ **Sin cambios**: Omite la variante
- 🖼️ **Imágenes nuevas**: Reemplaza las imágenes existentes

### Ejemplo Práctico

#### Escenario 1: Actualizar Precio
```
Serial: BAT-IP12-001
Precio antiguo: $45,000
Precio nuevo en Excel: $48,000
Resultado: ✅ Producto actualizado, precio cambia a $48,000
```

#### Escenario 2: Sin Cambios
```
Serial: CASE-IP13-001
Todos los campos iguales
Resultado: ⏭️ Producto omitido, no se hace nada
```

#### Escenario 3: Actualizar Stock de Variante
```
Serial: BAT-IP12-001, Color: NEGRO
Stock antiguo: 50
Stock nuevo: 75
Resultado: ✅ Variante actualizada, stock cambia a 75
```

## 📊 Estructura del Excel

### Columnas Requeridas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `serial_number` | String | Número de serie único del producto |
| `name` | String | Nombre del producto |
| `cost` | Decimal | Costo del producto |
| `retail_price` | Decimal | Precio de venta |

### Columnas Opcionales del Producto

| Columna | Tipo | Valores Permitidos | Default |
|---------|------|-------------------|---------|
| `description` | String | Texto libre | null |
| `brand_id` | Integer | ID válido de marca | null |
| `category_id` | Integer | ID válido de categoría | null |
| `warranty_time` | Integer | Número entero | null |
| `warranty_unit` | String | DAYS, MONTHS, YEARS | null |
| `status` | String | ACTIVE, INACTIVE, DISCONTINUED | ACTIVE |

### Columnas de Variante

| Columna | Tipo | Valores Permitidos | Default |
|---------|------|-------------------|---------|
| `variant_branch_id` | Integer | ID válido de sucursal | Requerido si se crea variante |
| `variant_color` | String | ROJO, AZUL, VERDE, AMARILLO, NARANJA, VIOLETA, ROSADO, MARRON, GRIS, BLANCO, NEGRO, BORDO | null |
| `variant_size` | String | Texto libre | null |
| `variant_size_unit` | String | CLOTHING, DIMENSIONS, WEIGHT, OTHER | null |
| `variant_unit` | String | KG, G, LB, CM, M, INCH, XS, S, L, XL, XXL | null |
| `variant_stock` | Integer | Número entero | 0 |
| `variant_min_stock` | Integer | Número entero | 5 |

### Columna de Imágenes

| Columna | Tipo | Formato | Ejemplo |
|---------|------|---------|---------|
| `image_paths` | String | Rutas separadas por `;` | `C:\imgs\img1.jpg;C:\imgs\img2.jpg` |

## 🖼️ Manejo de Imágenes

Las imágenes se procesan de la siguiente manera:

1. **Rutas**: Se especifican en la columna `image_paths` separadas por punto y coma (`;`)
2. **Formatos soportados**: JPG, JPEG, PNG, GIF, WEBP
3. **Conversión**: Las imágenes se convierten automáticamente a Base64 data URLs
4. **Almacenamiento**: Se guardan en la base de datos vinculadas a la variante

**Ejemplo**:
```
C:\Users\Usuario\Imagenes\bateria-12.jpg;C:\Users\Usuario\Imagenes\bateria-12-vista2.jpg
```

## 📝 Ejemplo de Uso

### Flujo Recomendado: Actualizar Productos Existentes

#### 1. Exportar Productos Actuales

```bash
curl -H "Authorization: Bearer <tu_token>" \
  http://localhost:8000/product/bulk-upload/export \
  -o productos_actuales.xlsx
```

O desde el navegador (con sesión activa):
```
http://localhost:8000/product/bulk-upload/export
```

#### 2. Editar el Excel

El archivo descargado contiene todos tus productos actuales. Ahora puedes:

**a) Actualizar productos existentes**:
- Cambiar precios, costos, descripciones, etc.
- Al volver a subir, solo se actualizarán los que tengan cambios

**b) Agregar nuevos productos**:
- Ir al final del archivo
- Agregar nuevas filas con nuevos serial_number
- Completar todos los campos requeridos

**c) Actualizar stock de variantes**:
- Modificar las columnas variant_stock
- El sistema detectará los cambios y actualizará

**d) Agregar nuevas variantes a productos existentes**:
- Duplicar la fila del producto
- Cambiar variant_color, variant_size, etc.
- Mantener el mismo serial_number

#### 3. Subir el Archivo Modificado

```bash
curl -X POST "http://localhost:8000/product/bulk-upload?skip_errors=true" \
  -H "Authorization: Bearer <tu_token>" \
  -F "file=@productos_actuales.xlsx"
```

El sistema procesará inteligentemente:
- ✅ Productos nuevos → se crean
- ✅ Productos con cambios → se actualizan
- ⏭️ Productos sin cambios → se omiten
- ✅ Variantes nuevas → se crean
- ✅ Variantes con cambios → se actualizan
- ⏭️ Variantes sin cambios → se omiten

### Flujo Alternativo: Empezar desde Cero

#### 1. Descargar el Template Vacío

```bash
curl -O http://localhost:8000/product/bulk-upload/template
```

O desde el navegador:
```
http://localhost:8000/product/bulk-upload/template
```

#### 2. Llenar el Excel

Edita el archivo descargado con tus productos. El template incluye:
- **Hoja "Productos"**: Con encabezados, descripciones y ejemplos
- **Hoja "Referencia"**: Con valores válidos para cada enum

#### 3. Preparar las Imágenes

Organiza tus imágenes en carpetas y anota las rutas completas:
```
C:\Productos\Imagenes\baterias\iphone12-negra.jpg
C:\Productos\Imagenes\fundas\iphone13-azul.jpg
```

#### 4. Subir el Archivo

**Con cURL**:
```bash
curl -X POST "http://localhost:8000/product/bulk-upload?skip_errors=true" \
  -H "Authorization: Bearer <tu_token>" \
  -F "file=@productos.xlsx"
```

**Con Python**:
```python
import requests

url = "http://localhost:8000/product/bulk-upload"
headers = {"Authorization": "Bearer <tu_token>"}
files = {"file": open("productos.xlsx", "rb")}
params = {"skip_errors": True}

response = requests.post(url, headers=headers, files=files, params=params)
print(response.json())
```

**Con Postman**:
1. Method: POST
2. URL: `http://localhost:8000/product/bulk-upload?skip_errors=true`
3. Headers: `Authorization: Bearer <tu_token>`
4. Body: form-data
   - Key: `file` (tipo: File)
   - Value: Seleccionar el archivo Excel

## ⚠️ Validaciones y Errores

### Prevención de Duplicados

El sistema previene duplicados automáticamente:

1. **Productos Duplicados**: 
   - Identificados por `serial_number`
   - Si existe: compara y actualiza solo si hay cambios
   - Si no existe: crea nuevo producto

2. **Variantes Duplicadas**:
   - Identificadas por: `product_id` + `color` + `size` + `size_unit` + `unit`
   - Si existe: compara y actualiza solo si hay cambios
   - Si no existe: crea nueva variante

3. **Ejemplo de Prevención**:
   ```
   Fila 10: BAT-IP12-001, Color: NEGRO (ya existe en BD)
   Resultado: ⏭️ Omitido (sin cambios) o ✅ Actualizado (con cambios)
   NO se crea duplicado
   ```

### Casos de Uso Comunes

#### Caso 1: Olvidé que ya había cargado productos

**Situación**: Descargo el template vacío, lleno productos, pero algunos ya existen en la BD.

**Solución Automática**:
- Productos que ya existen → Se comparan y actualizan solo si hay cambios
- Productos nuevos → Se crean normalmente
- No se generan duplicados

**Recomendación**: Usa el endpoint de exportación (`/bulk-upload/export`) en lugar del template vacío para evitar confusiones.

#### Caso 2: Actualizar precios masivamente

**Situación**: Necesito actualizar precios de 50 productos.

**Flujo**:
1. Exportar productos existentes: `GET /bulk-upload/export`
2. Modificar solo la columna `retail_price` en Excel
3. Subir el archivo: `POST /bulk-upload`
4. Resultado: Solo se actualizan productos con cambios de precio

#### Caso 3: Agregar nuevas variantes a productos existentes

**Situación**: Tengo el producto "Funda iPhone 14" en NEGRO, quiero agregar en AZUL.

**Flujo**:
1. Exportar productos existentes
2. Buscar la fila con "Funda iPhone 14" (NEGRO)
3. Duplicar la fila
4. En la fila duplicada: cambiar `variant_color` a AZUL
5. Mantener el mismo `serial_number`
6. Subir el archivo
7. Resultado: Se crea nueva variante AZUL, la NEGRA se omite (sin cambios)

#### Caso 4: Actualizar stock de múltiples variantes

**Situación**: Recibí inventario nuevo y necesito actualizar stock de 100 variantes.

**Flujo**:
1. Exportar productos existentes
2. Modificar solo la columna `variant_stock`
3. Subir el archivo
4. Resultado: Solo se actualizan las variantes con cambios de stock

#### Caso 5: Mezcla de operaciones

**Situación**: Necesito crear productos nuevos + actualizar existentes + agregar variantes.

**Flujo**:
1. Exportar productos existentes
2. En el mismo Excel:
   - Modificar filas existentes (actualizar)
   - Agregar filas nuevas con nuevos `serial_number` (crear)
   - Duplicar filas y cambiar variantes (agregar variantes)
3. Subir el archivo
4. Resultado: El sistema procesa todo inteligentemente

### Validaciones Automáticas

1. **IDs de Relaciones**: Se valida que brand_id, category_id y branch_id existan
2. **Productos Duplicados**: Si un serial_number ya existe, solo se crea la variante
3. **Variantes Duplicadas**: Se detectan según product_id, color, size, size_unit y unit
4. **Imágenes**: Se valida que los archivos existan en las rutas especificadas

### Manejo de Errores

- **skip_errors=true** (default): Continúa procesando aunque haya errores, reportándolos al final
- **skip_errors=false**: Detiene el proceso en el primer error encontrado

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| "Columnas faltantes" | El Excel no tiene las columnas requeridas | Usar el template oficial |
| "Categoría con id X no existe" | ID de categoría inválido | Verificar IDs existentes o dejarlo vacío |
| "No se pudo cargar la imagen" | Ruta de imagen incorrecta | Verificar que el archivo existe en esa ruta |
| "serial_number es requerido" | Celda vacía | Completar el serial_number |

## 🔍 Consejos y Mejores Prácticas

### 1. Preparación del Excel
- ✅ Usar el template oficial descargado desde el endpoint
- ✅ No eliminar las filas de encabezados y descripciones
- ✅ Verificar que no haya espacios extra en los valores
- ✅ Usar los valores exactos para enums (MAYÚSCULAS)

### 2. Organización de Imágenes
- ✅ Organizar las imágenes en carpetas por tipo de producto
- ✅ Usar nombres descriptivos: `bateria-iphone12-negro-1.jpg`
- ✅ Verificar que todas las rutas sean accesibles antes de subir
- ✅ Usar rutas absolutas, no relativas

### 3. Proceso de Carga
- ✅ Empezar con un archivo pequeño de prueba (5-10 productos)
- ✅ Usar `skip_errors=true` para identificar todos los problemas
- ✅ Revisar el reporte de errores y warnings
- ✅ Corregir y volver a cargar

### 4. Performance
- 📊 Archivos recomendados: hasta 1000 productos por archivo
- 📊 Si tienes más productos, dividir en múltiples archivos
- 📊 Limitar imágenes grandes (< 2MB por imagen recomendado)

## 🛠️ Generar Template Manualmente

Si necesitas regenerar el template:

```bash
python scripts/create_template_excel.py
```

Esto creará el archivo `template_carga_productos.xlsx` en el directorio raíz del proyecto.

## 📚 Referencias

### IDs de Referencia

Antes de llenar el Excel, obtén los IDs válidos:

**Categorías**:
```bash
GET /categories/all
```

**Marcas**:
```bash
GET /brands/all
```

**Sucursales**:
```bash
GET /branches/all
```

### Valores Enum Válidos

El archivo Excel incluye una hoja "Referencia" con todos los valores válidos para cada enum.

---

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'openpyxl'"
```bash
pip install openpyxl pandas
```

### Error: "El archivo debe ser un Excel (.xlsx o .xls)"
Verifica que el archivo tenga la extensión correcta.

### Warning: "Producto X ya existe"
Esto no es un error. El sistema creará solo la variante para ese producto existente.

### Las imágenes no se cargan
1. Verifica que las rutas sean absolutas
2. Verifica que los archivos existan
3. Verifica que tengas permisos de lectura
4. Verifica el formato del archivo (JPG, PNG, etc.)

---

## 📞 Soporte

Para reportar problemas o solicitar nuevas funcionalidades, contacta al equipo de desarrollo.
