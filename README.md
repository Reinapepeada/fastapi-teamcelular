# 🛒 Team Celular API

API REST para catálogo de productos de Team Celular, construida con FastAPI y PostgreSQL.

## 📋 Características

- ✅ Gestión de productos con variantes (colores, tallas)
- ✅ Categorías y marcas
- ✅ Gestión de stock por sucursal
- ✅ Imágenes de productos
- ✅ Sistema de descuentos
- ✅ Filtros y paginación
- ✅ Conexión con PostgreSQL

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/Reinapepeada/fastapi-teamcelular.git
cd fastapi-teamcelular
```

### 2. Crear entorno virtual
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crea un archivo `.env` basándote en `.env.example`:
```bash
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/teamcelular
```

### 5. Ejecutar migraciones
```bash
alembic upgrade head
```

### 6. Ejecutar el servidor
```bash
# Desarrollo (con hot-reload)
fastapi dev main.py

# Producción
fastapi run main.py
```

## 📁 Estructura del Proyecto

```
fastapi-teamcelular/
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias
├── alembic.ini            # Configuración de Alembic
├── .env.example           # Ejemplo de variables de entorno
│
├── database/
│   ├── connection/
│   │   └── SQLConection.py # Conexión a PostgreSQL
│   └── models/
│       └── product.py      # Modelos SQLModel y schemas Pydantic
│
├── routers/
│   ├── product_r.py       # Endpoints de productos
│   ├── categories_r.py    # Endpoints de categorías
│   ├── brands_r.py        # Endpoints de marcas
│   └── branches_r.py      # Endpoints de sucursales
│
├── controllers/
│   └── product_c.py       # Lógica de controladores
│
├── services/
│   ├── product_s.py       # Lógica de negocio (productos)
│   ├── category_s.py      # Lógica de negocio (categorías)
│   ├── brand_s.py         # Lógica de negocio (marcas)
│   └── branch_s.py        # Lógica de negocio (sucursales)
│
└── alembic/
    └── versions/          # Migraciones de base de datos
```

## 🔗 Endpoints Principales

### Productos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/products/` | Listar productos (paginado y filtros) |
| GET | `/products/all` | Obtener todos los productos |
| GET | `/products/get/{id}` | Obtener producto por ID |
| POST | `/products/create` | Crear producto |
| PUT | `/products/update` | Actualizar producto |
| DELETE | `/products/delete` | Eliminar producto |
| GET | `/products/min-max-price` | Obtener rango de precios |

### Variantes de Producto
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/products/create/variant` | Crear variantes |
| GET | `/products/get/variant` | Obtener variantes por producto |
| PUT | `/products/update/variant` | Actualizar variante |
| DELETE | `/products/delete/variant` | Eliminar variante |

### Categorías, Marcas, Sucursales
Cada entidad tiene endpoints CRUD bajo sus respectivos prefijos:
- `/categories/`
- `/brands/`
- `/branches/`

## 📖 Documentación API

Una vez ejecutando el servidor, accede a:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗃️ Migraciones con Alembic

```bash
# Crear nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

## 🛠️ Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **SQLModel** - ORM que combina SQLAlchemy + Pydantic
- **PostgreSQL** - Base de datos relacional
- **Alembic** - Migraciones de base de datos
- **Uvicorn** - Servidor ASGI

## 🚂 Deploy en Railway

### 1. Crear proyecto en Railway
1. Ve a [railway.app](https://railway.app) y crea una cuenta
2. Crea un nuevo proyecto desde tu repositorio de GitHub

### 2. Agregar PostgreSQL
1. En tu proyecto de Railway, click en **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway configurará automáticamente las variables de entorno

### 3. Variables de Entorno
Railway configura `DATABASE_URL` automáticamente. Variables adicionales opcionales:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de PostgreSQL (auto) | `postgresql://...` |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos | `https://tudominio.com,https://otro.com` |

### 4. Deploy
Railway detecta automáticamente el proyecto y lo despliega. Archivos de configuración incluidos:
- `railway.json` - Configuración de Railway
- `nixpacks.toml` - Configuración de Nixpacks
- `Procfile` - Comando de inicio
- `runtime.txt` - Versión de Python

### 5. Health Check
El endpoint `/health` está configurado para que Railway verifique el estado de la app.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.


