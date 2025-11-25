# 🤖 API DOCUMENTATION FOR AI AGENTS
## Team Celular - Product Catalog API

> **Purpose**: This document is optimized for AI/LLM consumption to understand and interact with the Team Celular API endpoints.

---

## 📊 BASE INFORMATION

```yaml
base_url: "https://fastapi-teamcelular-dev.up.railway.app"
local_url: "http://localhost:8080"
content_type: "application/json"
authentication: "JWT Bearer Token (for write operations)"
```

---

## 🔐 AUTHENTICATION SYSTEM

### Roles Hierarchy
```
SUPER_ADMIN > ADMIN > EDITOR
```

| Role | Can Create | Can Update | Can Delete | Can Manage Admins |
|------|-----------|------------|------------|-------------------|
| SUPER_ADMIN | ✅ All | ✅ All | ✅ All | ✅ Yes |
| ADMIN | ✅ All | ✅ All | ✅ All | ❌ No |
| EDITOR | ✅ All | ✅ All | ❌ No | ❌ No |

### Public vs Protected Endpoints
- **GET endpoints**: Public (no authentication required)
- **POST/PUT endpoints**: Require `Editor+` role
- **DELETE endpoints**: Require `Admin+` role
- **Admin management**: Require `SUPER_ADMIN` role

---

## 👤 ADMIN ENDPOINTS

### Setup First Admin (One-time)
```http
POST /admin/setup
Content-Type: application/json
```
**⚠️ Only works if no admins exist in the database.**

**Request Body:**
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "password": "your-secure-password"
}
```
**Response:** `AdminOut` (automatically becomes SUPER_ADMIN)
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "SUPER_ADMIN",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00"
}
```

**Example with curl:**
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/admin/setup" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "securePass123"}'
```

---

### Login ⭐ IMPORTANT
```http
POST /admin/login
Content-Type: application/json
```
**⚠️ IMPORTANT: This endpoint accepts JSON body, NOT form data.**

**Request Body (JSON):**
```json
{
  "identifier": "admin_or_email",
  "password": "your-password"
}
```
**The `identifier` field accepts either username OR email.**

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Example with curl (using username):**
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "admin", "password": "securePass123"}'
```

**Example with curl (using email):**
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "admin@example.com", "password": "securePass123"}'
```

**Using the Token:**
Include the token in the `Authorization` header for protected endpoints:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

### Get Current Admin Info
```http
GET /admin/me
Authorization: Bearer {token}
```
**Response:** `AdminOut`
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "SUPER_ADMIN",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00"
}
```

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/admin/me" \
  -H "Authorization: Bearer {your_token}"
```

---

### Register New Admin (SUPER_ADMIN only)
```http
POST /admin/register
Content-Type: application/json
Authorization: Bearer {super_admin_token}
```
**Request Body:**
```json
{
  "username": "new_admin",
  "email": "newadmin@example.com",
  "password": "secure-password",
  "role": "ADMIN"
}
```
**Available Roles:** `SUPER_ADMIN` | `ADMIN` | `EDITOR`

**Example with curl:**
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/admin/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {super_admin_token}" \
  -d '{"username": "editor1", "email": "editor@example.com", "password": "editorPass", "role": "EDITOR"}'
```

---

### List All Admins (SUPER_ADMIN only)
```http
GET /admin/list
Authorization: Bearer {super_admin_token}
```
**Response:** `List[AdminOut]`

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/admin/list" \
  -H "Authorization: Bearer {super_admin_token}"
```

---

### Change Password
```http
PUT /admin/me/password
Content-Type: application/json
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "current_password": "old-password",
  "new_password": "new-secure-password"
}
```
**Response:**
```json
{
  "msg": "Contraseña actualizada correctamente"
}
```

**Example with curl:**
```bash
curl -X PUT "https://fastapi-teamcelular-dev.up.railway.app/admin/me/password" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"current_password": "oldPass", "new_password": "newSecurePass123"}'
```

---

### Update Admin (SUPER_ADMIN only)
```http
PUT /admin/update/{admin_id}
Content-Type: application/json
Authorization: Bearer {super_admin_token}
```
**Path Parameters:**
- `admin_id` (int, required): ID of admin to update

**Request Body:** (all fields optional)
```json
{
  "email": "newemail@example.com",
  "role": "EDITOR",
  "is_active": true
}
```

**Example with curl:**
```bash
curl -X PUT "https://fastapi-teamcelular-dev.up.railway.app/admin/update/2" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {super_admin_token}" \
  -d '{"role": "ADMIN", "is_active": true}'
```

---

### Delete Admin (SUPER_ADMIN only)
```http
DELETE /admin/delete/{admin_id}
Authorization: Bearer {super_admin_token}
```
**Path Parameters:**
- `admin_id` (int, required): ID of admin to delete

**⚠️ Note:** You cannot delete yourself.

**Response:**
```json
{
  "msg": "Admin eliminado correctamente"
}
```

**Example with curl:**
```bash
curl -X DELETE "https://fastapi-teamcelular-dev.up.railway.app/admin/delete/3" \
  -H "Authorization: Bearer {super_admin_token}"
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

### Get All Categories (PUBLIC)
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

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/categories/get/all"
```

---

### Create Category (Editor+)
```http
POST /categories/create
Content-Type: application/json
Authorization: Bearer {token}
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

**Example with curl:**
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/categories/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"name": "Smartphones", "description": "Celulares y accesorios"}'
```

---

### Update Category (Editor+)
```http
PUT /categories/update?category_id={id}
Content-Type: application/json
Authorization: Bearer {token}
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

**Example with curl:**
```bash
curl -X PUT "https://fastapi-teamcelular-dev.up.railway.app/categories/update?category_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"name": "Teléfonos Móviles", "description": "Updated description"}'
```

---

### Delete Category (Admin+)
```http
DELETE /categories/delete?category_id={id}
Authorization: Bearer {token}
```
**Query Parameters:**
- `category_id` (int, required): ID of category to delete

**Response:** `{"msg": "Category deleted successfully"}`
**⚠️ Warning:** Will fail if products are associated with this category.

**Example with curl:**
```bash
curl -X DELETE "https://fastapi-teamcelular-dev.up.railway.app/categories/delete?category_id=1" \
  -H "Authorization: Bearer {admin_token}"
```

---

## 🏢 BRANDS ENDPOINTS

### Get All Brands (PUBLIC)
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

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/brands/get/all"
```

---

### Create Brand (Editor+)
```http
POST /brands/create
Content-Type: application/json
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "name": "string (required, unique)"
}
```
**Response:** `BrandOut` object

**Example with curl:**
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/brands/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"name": "Apple"}'
```

---

### Update Brand (Editor+)
```http
PUT /brands/update?brand_id={id}
Content-Type: application/json
Authorization: Bearer {token}
```
**Query Parameters:**
- `brand_id` (int, required)

**Request Body:**
```json
{
  "name": "string | null"
}
```

**Example with curl:**
```bash
curl -X PUT "https://fastapi-teamcelular-dev.up.railway.app/brands/update?brand_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"name": "Samsung Electronics"}'
```

---

### Delete Brand (Admin+)
```http
DELETE /brands/delete?brand_id={id}
Authorization: Bearer {token}
```
**Query Parameters:**
- `brand_id` (int, required)

**Response:** `{"msg": "Brand deleted successfully"}`

**Example with curl:**
```bash
curl -X DELETE "https://fastapi-teamcelular-dev.up.railway.app/brands/delete?brand_id=1" \
  -H "Authorization: Bearer {admin_token}"
```

---

## 🏪 BRANCHES (Store Locations) ENDPOINTS

### Get All Branches (PUBLIC)
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

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/branches/get/all"
```

---

### Create Branch (Editor+)
```http
POST /branches/create
Content-Type: application/json
Authorization: Bearer {token}
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

**Example with curl:**
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/branches/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"name": "Sucursal Centro", "location": "Av. Principal 123"}'
```

---

### Update Branch (Editor+)
```http
PUT /branches/update?branch_id={id}
Content-Type: application/json
Authorization: Bearer {token}
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

**Example with curl:**
```bash
curl -X PUT "https://fastapi-teamcelular-dev.up.railway.app/branches/update?branch_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"name": "Sucursal Principal", "location": "Nueva dirección"}'
```

---

### Delete Branch (Admin+)
```http
DELETE /branches/delete?branch_id={id}
Authorization: Bearer {token}
```
**Query Parameters:**
- `branch_id` (int, required)

**Response:** `{"msg": "Branch deleted successfully"}`

**Example with curl:**
```bash
curl -X DELETE "https://fastapi-teamcelular-dev.up.railway.app/branches/delete?branch_id=1" \
  -H "Authorization: Bearer {admin_token}"
```

---

## 📦 PRODUCTS ENDPOINTS

### Get Product by ID (PUBLIC)
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

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/products/get/1"
```

---

### Get All Products (PUBLIC)
```http
GET /products/all
```
**Response:** `List[ProductOut]`
**Use Case:** Retrieve complete product list without pagination. Use sparingly for large catalogs.

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/products/all"
```

---

### Get Products (Paginated + Filtered) ⭐ MAIN ENDPOINT (PUBLIC)
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

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/products/?page=1&size=10&categories=Smartphones&minPrice=100"
```

---

### Get Price Range (PUBLIC)
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

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/products/min-max-price"
```

---

### Create Product (Editor+)
```http
POST /products/create
Content-Type: application/json
Authorization: Bearer {token}
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

**Example with curl:**
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/products/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "serial_number": "IPHONE-15-001",
    "name": "iPhone 15",
    "description": "Latest iPhone model",
    "brand_id": 1,
    "category_id": 1,
    "warranty_time": 12,
    "warranty_unit": "MONTHS",
    "cost": 800.00,
    "retail_price": 999.99,
    "status": "ACTIVE"
  }'
```

---

### Update Product (Editor+)
```http
PUT /products/update?product_id={id}
Content-Type: application/json
Authorization: Bearer {token}
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

**Example with curl:**
```bash
curl -X PUT "https://fastapi-teamcelular-dev.up.railway.app/products/update?product_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"retail_price": 1099.99, "status": "ACTIVE"}'
```

---

### Delete Product (Admin+)
```http
DELETE /products/delete?product_id={id}
Authorization: Bearer {token}
```
**Query Parameters:**
- `product_id` (int, required)

**Response:** `{"msg": "Producto eliminado correctamente"}`
**⚠️ Warning:** This will cascade delete all associated variants and images.

**Example with curl:**
```bash
curl -X DELETE "https://fastapi-teamcelular-dev.up.railway.app/products/delete?product_id=1" \
  -H "Authorization: Bearer {admin_token}"
```

---

## 🎨 PRODUCT VARIANTS ENDPOINTS

### Get Variants by Product ID (PUBLIC)
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
    "min_stock": 5,
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

**Example with curl:**
```bash
curl -X GET "https://fastapi-teamcelular-dev.up.railway.app/products/get/variant?product_id=1"
```

---

### Create Product Variants (Batch) (Editor+)
```http
POST /products/create/variant
Content-Type: application/json
Authorization: Bearer {token}
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
```bash
curl -X POST "https://fastapi-teamcelular-dev.up.railway.app/products/create/variant" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
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
  }'
```

---

### Update Variant (Editor+)
```http
PUT /products/update/variant?variant_id={id}
Content-Type: application/json
Authorization: Bearer {token}
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

**Example with curl:**
```bash
curl -X PUT "https://fastapi-teamcelular-dev.up.railway.app/products/update/variant?variant_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"stock": 100, "branch_id": 2}'
```

---

### Delete Variant (Admin+)
```http
DELETE /products/delete/variant?variant_id={id}
Authorization: Bearer {token}
```
**Query Parameters:**
- `variant_id` (int, required)

**Response:** `{"msg": "Variante eliminada correctamente"}`

**Example with curl:**
```bash
curl -X DELETE "https://fastapi-teamcelular-dev.up.railway.app/products/delete/variant?variant_id=1" \
  -H "Authorization: Bearer {admin_token}"
```

---

## 🔄 COMMON WORKFLOWS

### Workflow 1: Initial Setup
```bash
# 1. Create the first admin (only works once)
curl -X POST "{base_url}/admin/setup" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@empresa.com", "password": "securePass123"}'

# 2. Login to get token
curl -X POST "{base_url}/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "admin", "password": "securePass123"}'
# Save the access_token from response
```

### Workflow 2: Setting up a new product catalog
```
1. POST /categories/create     → Create categories
2. POST /brands/create         → Create brands
3. POST /branches/create       → Create store locations (optional)
4. POST /products/create       → Create products
5. POST /products/create/variant → Add variants with stock
```

### Workflow 3: Displaying products on a storefront
```
1. GET /categories/get/all     → Get categories for filter sidebar
2. GET /brands/get/all         → Get brands for filter sidebar
3. GET /products/min-max-price → Get price range for slider
4. GET /products/?page=1&size=20&categories=X&brands=Y → Fetch filtered products
```

### Workflow 4: Viewing product details
```
1. GET /products/get/{id}      → Get full product with variants
   OR
2. GET /products/get/variant?product_id={id} → Get only variants
```

### Workflow 5: Inventory management
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
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions (wrong role) |
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

### AdminRole
```
SUPER_ADMIN | ADMIN | EDITOR
```

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

## 📋 ENDPOINTS SUMMARY TABLE

### Admin Endpoints (`/admin`)
| Method | Endpoint | Auth Required | Role |
|--------|----------|---------------|------|
| POST | `/admin/setup` | ❌ No | - |
| POST | `/admin/login` | ❌ No | - |
| GET | `/admin/me` | ✅ Yes | Any |
| PUT | `/admin/me/password` | ✅ Yes | Any |
| POST | `/admin/register` | ✅ Yes | SUPER_ADMIN |
| GET | `/admin/list` | ✅ Yes | SUPER_ADMIN |
| PUT | `/admin/update/{id}` | ✅ Yes | SUPER_ADMIN |
| DELETE | `/admin/delete/{id}` | ✅ Yes | SUPER_ADMIN |

### Category Endpoints (`/categories`)
| Method | Endpoint | Auth Required | Role |
|--------|----------|---------------|------|
| GET | `/categories/get/all` | ❌ No | - |
| POST | `/categories/create` | ✅ Yes | Editor+ |
| PUT | `/categories/update` | ✅ Yes | Editor+ |
| DELETE | `/categories/delete` | ✅ Yes | Admin+ |

### Brand Endpoints (`/brands`)
| Method | Endpoint | Auth Required | Role |
|--------|----------|---------------|------|
| GET | `/brands/get/all` | ❌ No | - |
| POST | `/brands/create` | ✅ Yes | Editor+ |
| PUT | `/brands/update` | ✅ Yes | Editor+ |
| DELETE | `/brands/delete` | ✅ Yes | Admin+ |

### Branch Endpoints (`/branches`)
| Method | Endpoint | Auth Required | Role |
|--------|----------|---------------|------|
| GET | `/branches/get/all` | ❌ No | - |
| POST | `/branches/create` | ✅ Yes | Editor+ |
| PUT | `/branches/update` | ✅ Yes | Editor+ |
| DELETE | `/branches/delete` | ✅ Yes | Admin+ |

### Product Endpoints (`/products`)
| Method | Endpoint | Auth Required | Role |
|--------|----------|---------------|------|
| GET | `/products/` | ❌ No | - |
| GET | `/products/all` | ❌ No | - |
| GET | `/products/get/{id}` | ❌ No | - |
| GET | `/products/min-max-price` | ❌ No | - |
| GET | `/products/get/variant` | ❌ No | - |
| POST | `/products/create` | ✅ Yes | Editor+ |
| PUT | `/products/update` | ✅ Yes | Editor+ |
| DELETE | `/products/delete` | ✅ Yes | Admin+ |
| POST | `/products/create/variant` | ✅ Yes | Editor+ |
| PUT | `/products/update/variant` | ✅ Yes | Editor+ |
| DELETE | `/products/delete/variant` | ✅ Yes | Admin+ |

---

## 🔗 OPENAPI SPECIFICATION

For complete schema definitions, access:
- **Swagger UI:** `{base_url}/docs`
- **ReDoc:** `{base_url}/redoc`
- **OpenAPI JSON:** `{base_url}/openapi.json`

---

## 🚀 QUICK START EXAMPLE

```bash
# Set base URL
BASE_URL="https://fastapi-teamcelular-dev.up.railway.app"

# 1. Check if API is running
curl -X GET "$BASE_URL/docs"

# 2. Get all categories (public)
curl -X GET "$BASE_URL/categories/get/all"

# 3. Get products with filters (public)
curl -X GET "$BASE_URL/products/?page=1&size=10"

# 4. Login as admin
TOKEN=$(curl -s -X POST "$BASE_URL/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "admin", "password": "your-password"}' | jq -r '.access_token')

# 5. Create a new category (requires auth)
curl -X POST "$BASE_URL/categories/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Tablets", "description": "Tablets and iPad"}'

# 6. Get your admin info
curl -X GET "$BASE_URL/admin/me" \
  -H "Authorization: Bearer $TOKEN"
```
