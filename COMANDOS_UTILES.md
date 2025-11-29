# 🛠️ Comandos Útiles

## Desarrollo Local

### Iniciar servidor
```bash
# Modo desarrollo (con hot-reload)
python run.py

# Modo producción
python run.py --prod

# Saltar checks (más rápido)
python run.py --skip-checks
```

### Base de datos
```bash
# Crear migración
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver historial
alembic history
```

## Scripts

### Health Check
```bash
python scripts/test_health.py
```

### Importación

#### Prueba rápida
```bash
python scripts/test_import.py
```

#### Verificar estado
```bash
python scripts/check_variants.py
```

#### Importación completa
```bash
python scripts/import_baterias.py
```

## Testing API

### Health check
```bash
# Local
curl http://localhost:8000/health

# Producción
curl https://fastapi-teamcelular-dev.up.railway.app/health
```

### Obtener productos
```bash
# Todos los productos
curl https://fastapi-teamcelular-dev.up.railway.app/products/all

# Producto específico
curl https://fastapi-teamcelular-dev.up.railway.app/products/get/1

# Con filtros
curl "https://fastapi-teamcelular-dev.up.railway.app/products/?page=1&size=10&brands=AMPSENTRIX"
```

### Login
```bash
curl -X POST https://fastapi-teamcelular-dev.up.railway.app/admin/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"admin","password":"password"}'
```

## Docker

### Build local
```bash
docker build -t teamcelular-api .
```

### Run local
```bash
docker run -p 8000:8000 --env-file .env teamcelular-api
```

### Ver logs
```bash
docker logs -f <container_id>
```

## Git

### Commit y push
```bash
git add .
git commit -m "Limpieza de código y mejoras"
git push origin main
```

### Ver cambios
```bash
git status
git diff
```

## Railway CLI

### Login
```bash
railway login
```

### Ver logs
```bash
railway logs
```

### Variables de entorno
```bash
railway variables
```

### Redeploy
```bash
railway up
```

## Python

### Instalar dependencias
```bash
pip install -r requirements.txt
```

### Actualizar dependencias
```bash
pip freeze > requirements.txt
```

### Crear entorno virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

## Limpieza

### Limpiar cache Python
```bash
# Windows
del /s /q __pycache__
del /s /q *.pyc

# Linux/Mac
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Limpiar Docker
```bash
docker system prune -a
```
