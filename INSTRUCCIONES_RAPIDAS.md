# ⚡ Instrucciones Rápidas

## 🎯 Para Empezar

### 1. Verificar que el servidor funciona
```bash
python scripts/test_health.py
```

Selecciona la opción que necesites:
- `1` - Probar producción (Railway)
- `2` - Probar local
- `3` - Probar ambos

OK. **Resultado esperado:** `Status: healthy` y `DB: connected` en `/health/db`

---

### 2. Probar importación con un producto
```bash
python scripts/test_import.py
```

Ingresa tus credenciales de admin cuando te las pida.

OK. **Resultado esperado:** Producto creado con variante e imagenes

---

### 3. Ver estado actual de productos
```bash
python scripts/check_variants.py
```

OK. **Resultado esperado:** Lista de productos con sus variantes e imagenes

---

### 4. Importar todas las baterías
```bash
python scripts/import_baterias.py
```

Ingresa tus credenciales de admin cuando te las pida.

OK. **Resultado esperado:** 35 productos importados con variantes e imagenes

---

## 🚀 Deploy a Railway

### Opción 1: Push automático
```bash
git add .
git commit -m "Limpieza y correcciones"
git push origin main
```

Railway detectará el push y hará deploy automáticamente.

### Opción 2: Railway CLI
```bash
railway up
```

---

## 🔍 Verificar Deploy

### 1. Health Check
```bash
curl https://fastapi-teamcelular-dev.up.railway.app/health
curl https://fastapi-teamcelular-dev.up.railway.app/health/db
```

### 2. Ver productos
```bash
curl https://fastapi-teamcelular-dev.up.railway.app/products/all
```

### 3. Ver documentación
Abre en el navegador:
```
https://fastapi-teamcelular-dev.up.railway.app/docs
```

---

## ⚠️ Solución Rápida de Problemas

### Health check falla
1. Verifica que PostgreSQL esté conectado en Railway
2. Revisa la variable `DATABASE_URL` en Railway
3. Mira los logs: `railway logs`

### Importación falla
1. Verifica tus credenciales de admin
2. Asegúrate de tener rol EDITOR o superior
3. Verifica que exista al menos una sucursal (branch)

### Variantes sin imágenes
1. Verifica tu API key de ImgBB en el script
2. Asegúrate de que las imágenes existan en las carpetas
3. Ejecuta `test_import.py` para probar con URLs de prueba

---

## 📚 Más Información

- `CHANGELOG.md` - Lista completa de cambios
- `DEPLOY.md` - Guía detallada de deploy
- `COMANDOS_UTILES.md` - Todos los comandos disponibles
- `scripts/README.md` - Documentación de scripts
