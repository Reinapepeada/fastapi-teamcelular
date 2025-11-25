# 🤖 API DOCUMENTATION FOR AI AGENTS
## Team Celular - Product Catalog API

> **Purpose**: This document is optimized for AI/LLM consumption to understand and interact with the Team Celular API endpoints.

---

## 📊 BASE INFORMATION

```yaml
base_url: "http://localhost:8000"
content_type: "application/json"
authentication: none  # Public API
```

---

## 🗂️ DATA MODEL RELATIONSHIPS

```
Category (1) ──────< (N) Product (1) ──────< (N) ProductVariant
                          │                         │
Brand (1) ────────────────┘                         │
                                                    │
Branch (1) ────────────────────────────────────────┘
                                                    │
                                    ProductImage (N) ┘
```

### Entity Hierarchy:
1. **Category** & **Brand** → Must exist before creating Product
2. **Product** → Must exist before creating ProductVariant
3. **Branch** → Optional, used for stock location in ProductVariant
4. **ProductVariant** → Contains SKU, color, size, stock, images

---

## 🏷️ CATEGORIES ENDPOINTS

### Create Category
```http
POST /categories/create
```
**Request Body:**
```json
{
  "name": "string (required, unique)",
  "description": "string | null"
}
```
**Response:** `CategoryOut` object
**Use Case:** Create a category before adding products to it.

---

### Get All Categories
```http
GET /categories/get/all
```
**Response:** `List[CategoryOut]`
```json
[
  {
    "id": 1,
    "name": "Smartphones",
    "description": "Mobile phones and accessories",
    "created_at": "2025-01-01T00:00:00"
  }
]
```
**Use Case:** Retrieve all categories to populate filters or dropdowns.

---

### Update Category
```http
PUT /categories/update?category_id={id}
```
**Query Parameters:**
- `category_id` (int, required): ID of category to update

**Request Body:**
```json
{
  "name": "string | null",
  "description": "string | null"
}
```
**Use Case:** Modify category name or description.

---

### Delete Category
```http
DELETE /categories/delete?category_id={id}
```
**Query Parameters:**
- `category_id` (int, required): ID of category to delete

**Response:** `{"msg": "Category deleted successfully"}`
**⚠️ Warning:** Will fail if products are associated with this category.

---

## 🏢 BRANDS ENDPOINTS

### Create Brand
```http
POST /brands/create
```
**Request Body:**
```json
{
  "name": "string (required, unique)"
}
```
**Response:** `BrandOut` object

---

### Get All Brands
```http
GET /brands/get/all
```
**Response:** `List[BrandOut]`
```json
[
  {
    "id": 1,
    "name": "Samsung",
    "created_at": "2025-01-01T00:00:00"
  }
]
```

---

### Update Brand
```http
PUT /brands/update?brand_id={id}
```
**Query Parameters:**
- `brand_id` (int, required)

**Request Body:**
```json
{
  "name": "string | null"
}
```

---

### Delete Brand
```http
DELETE /brands/delete?brand_id={id}
```
**Query Parameters:**
- `brand_id` (int, required)

**Response:** `{"msg": "Brand deleted successfully"}`

---

## 🏪 BRANCHES (Store Locations) ENDPOINTS

### Create Branch
```http
POST /branches/create
```
**Request Body:**
```json
{
  "name": "string (required)",
  "location": "string | null"
}
```
**Response:** `BranchOut` object
**Use Case:** Create store locations to track inventory per location.

---

### Get All Branches
```http
GET /branches/get/all
```
**Response:** `List[BranchOut]`
```json
[
  {
    "id": 1,
    "name": "Main Store",
    "location": "123 Main Street",
    "created_at": "2025-01-01T00:00:00"
  }
]
```

---

### Update Branch
```http
PUT /branches/update?branch_id={id}
```
**Query Parameters:**
- `branch_id` (int, required)

**Request Body:**
```json
{
  "name": "string | null",
  "location": "string | null"
}
```

---

### Delete Branch
```http
DELETE /branches/delete?branch_id={id}
```
**Query Parameters:**
- `branch_id` (int, required)

**Response:** `{"msg": "Branch deleted successfully"}`

---

## 📦 PRODUCTS ENDPOINTS

### Create Product
```http
POST /products/create
```
**Request Body:**
```json
{
  "serial_number": "string (required, unique)",
  "name": "string (required)",
  "description": "string | null",
  "brand_id": "int | null",
  "category_id": "int | null",
  "warranty_time": "int | null",
  "warranty_unit": "DAYS | MONTHS | YEARS | null",
  "cost": "float (required, >= 0)",
  "retail_price": "float (required, >= 0)",
  "status": "ACTIVE | INACTIVE | DISCONTINUED (default: ACTIVE)"
}
```
**Response:** `ProductOut` object
**Status Code:** `201 Created`

**Important Notes:**
- `serial_number` must be unique across all products
- `cost` is internal purchase cost (not shown to customers)
- `retail_price` is the selling price
- Create Category and Brand first if you want to associate them

---

### Get Product by ID
```http
GET /products/get/{product_id}
```
**Path Parameters:**
- `product_id` (int, required)

**Response:** `ProductOut`
```json
{
  "id": 1,
  "serial_number": "PROD-001",
  "name": "iPhone 15",
  "description": "Latest iPhone model",
  "warranty_time": 12,
  "warranty_unit": "MONTHS",
  "cost": 800.00,
  "retail_price": 999.99,
  "status": "ACTIVE",
  "category": { "id": 1, "name": "Smartphones", ... },
  "brand": { "id": 1, "name": "Apple", ... },
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00",
  "variants": [...]
}
```

---

### Get All Products
```http
GET /products/all
```
**Response:** `List[ProductOut]`
**Use Case:** Retrieve complete product list without pagination. Use sparingly for large catalogs.

---

### Get Products (Paginated + Filtered) ⭐ MAIN ENDPOINT
```http
GET /products/
```
**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (starts at 1) |
| `size` | int | 10 | Items per page (max 100) |
| `categories` | string | null | Comma-separated category names: `"Smartphones,Tablets"` |
| `brands` | string | null | Comma-separated brand names: `"Apple,Samsung"` |
| `minPrice` | float | null | Minimum retail_price filter |
| `maxPrice` | float | null | Maximum retail_price filter |

**Example Request:**
```http
GET /products/?page=1&size=20&categories=Smartphones&brands=Apple,Samsung&minPrice=500&maxPrice=1500
```

**Response:** `ProductOutPaginated`
```json
{
  "products": [
    {
      "id": 1,
      "name": "iPhone 15",
      "retail_price": 999.99,
      "status": "ACTIVE",
      "category": {...},
      "brand": {...},
      "variants": [...]
    }
  ],
  "total": 45,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

**Use Case:** Main endpoint for product catalog display with filtering.

---

### Get Price Range
```http
GET /products/min-max-price
```
**Response:**
```json
{
  "min": "99.99",
  "max": "1999.99"
}
```
**Use Case:** Get price range for slider filters in UI.

---

### Update Product
```http
PUT /products/update?product_id={id}
```
**Query Parameters:**
- `product_id` (int, required)

**Request Body:** (all fields optional)
```json
{
  "serial_number": "string | null",
  "name": "string | null",
  "description": "string | null",
  "brand_id": "int | null",
  "category_id": "int | null",
  "warranty_time": "int | null",
  "warranty_unit": "DAYS | MONTHS | YEARS | null",
  "cost": "float | null",
  "retail_price": "float | null",
  "status": "ACTIVE | INACTIVE | DISCONTINUED | null"
}
```
**Use Case:** Partial update - only send fields you want to change.

---

### Delete Product
```http
DELETE /products/delete?product_id={id}
```
**Query Parameters:**
- `product_id` (int, required)

**Response:** `{"msg": "Producto eliminado correctamente"}`
**⚠️ Warning:** This will cascade delete all associated variants and images.

---

## 🎨 PRODUCT VARIANTS ENDPOINTS

### Create Product Variants (Batch)
```http
POST /products/create/variant
```
**Request Body:**
```json
{
  "variants": [
    {
      "product_id": 1,
      "color": "NEGRO | BLANCO | ROJO | AZUL | VERDE | AMARILLO | NARANJA | VIOLETA | ROSADO | MARRON | GRIS | BORDO | null",
      "size": "string | null",
      "size_unit": "CLOTHING | DIMENSIONS | WEIGHT | OTHER | null",
      "unit": "KG | G | LB | CM | M | INCH | XS | S | L | XL | XXL | null",
      "branch_id": "int | null",
      "stock": "int (default: 0)",
      "min_stock": "int (default: 5)",
      "images": ["url1", "url2"] 
    }
  ]
}
```

**Response:** `List[ProductVariantOut]`

**Important Notes:**
- SKU is auto-generated
- Unique constraint: product_id + color + size + size_unit
- Images are stored as URLs (external hosting)

**Example - Creating variants for a phone:**
```json
{
  "variants": [
    {
      "product_id": 1,
      "color": "NEGRO",
      "size": "128GB",
      "size_unit": "OTHER",
      "stock": 50,
      "images": ["https://cdn.example.com/iphone-black.jpg"]
    },
    {
      "product_id": 1,
      "color": "BLANCO",
      "size": "128GB",
      "size_unit": "OTHER",
      "stock": 30,
      "images": ["https://cdn.example.com/iphone-white.jpg"]
    }
  ]
}
```

---

### Get Variants by Product ID
```http
GET /products/get/variant?product_id={id}
```
**Query Parameters:**
- `product_id` (int, required)

**Response:** `List[ProductVariantOut]`
```json
[
  {
    "id": 1,
    "product_id": 1,
    "sku": "IPHO-01-01-A1B2C3D4",
    "color": "NEGRO",
    "size": "128GB",
    "size_unit": "OTHER",
    "unit": null,
    "branch_id": 1,
    "stock": 50,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
    "images": [
      {
        "id": 1,
        "variant_id": 1,
        "image_url": "https://cdn.example.com/iphone-black.jpg",
        "created_at": "2025-01-01T00:00:00"
      }
    ]
  }
]
```

---

### Update Variant
```http
PUT /products/update/variant?variant_id={id}
```
**Query Parameters:**
- `variant_id` (int, required)

**Request Body:** (all fields optional)
```json
{
  "color": "NEGRO | ... | null",
  "size": "string | null",
  "size_unit": "CLOTHING | DIMENSIONS | WEIGHT | OTHER | null",
  "unit": "KG | G | ... | null",
  "branch_id": "int | null",
  "stock": "int | null"
}
```
**Use Case:** Update stock levels, change branch location, modify attributes.

---

### Delete Variant
```http
DELETE /products/delete/variant?variant_id={id}
```
**Query Parameters:**
- `variant_id` (int, required)

**Response:** `{"msg": "Variante eliminada correctamente"}`

---

## 🔄 COMMON WORKFLOWS

### Workflow 1: Setting up a new product catalog
```
1. POST /categories/create     → Create categories
2. POST /brands/create         → Create brands
3. POST /branches/create       → Create store locations (optional)
4. POST /products/create       → Create products
5. POST /products/create/variant → Add variants with stock
```

### Workflow 2: Displaying products on a storefront
```
1. GET /categories/get/all     → Get categories for filter sidebar
2. GET /brands/get/all         → Get brands for filter sidebar
3. GET /products/min-max-price → Get price range for slider
4. GET /products/?page=1&size=20&categories=X&brands=Y → Fetch filtered products
```

### Workflow 3: Viewing product details
```
1. GET /products/get/{id}      → Get full product with variants
   OR
2. GET /products/get/variant?product_id={id} → Get only variants
```

### Workflow 4: Inventory management
```
1. GET /products/get/variant?product_id={id} → Check current stock
2. PUT /products/update/variant?variant_id={id} → Update stock: {"stock": 100}
```

---

## ⚠️ ERROR RESPONSES

All endpoints return standard HTTP error codes:

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid input data, duplicate entry |
| 404 | Not Found | Product/Category/Brand/Variant not found |
| 422 | Validation Error | Missing required field, wrong type |
| 500 | Server Error | Database connection issues |

**Error Response Format:**
```json
{
  "detail": "Error message describing the problem"
}
```

---

## 📝 ENUM VALUES REFERENCE

### ProductStatus
```
ACTIVE | INACTIVE | DISCONTINUED
```

### Color
```
ROJO | AZUL | VERDE | AMARILLO | NARANJA | VIOLETA | ROSADO | MARRON | GRIS | BLANCO | NEGRO | BORDO
```

### SizeUnit
```
CLOTHING | DIMENSIONS | WEIGHT | OTHER
```

### Unit
```
KG | G | LB | CM | M | INCH | XS | S | L | XL | XXL
```

### WarrantyUnit
```
DAYS | MONTHS | YEARS
```

---

## 🔗 OPENAPI SPECIFICATION

For complete schema definitions, access:
- **Swagger UI:** `{base_url}/docs`
- **ReDoc:** `{base_url}/redoc`
- **OpenAPI JSON:** `{base_url}/openapi.json`
