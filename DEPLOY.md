# 🚀 Guía de Deploy en Railway

## Configuración Actual

Tu proyecto está configurado para deployar automáticamente en Railway usando:
- **Dockerfile** para el build
- **docker-entrypoint.py** para inicialización
- **railway.json** para configuración de Railway

## Variables de Entorno Requeridas

Asegúrate de tener estas variables configuradas en Railway:

```
DATABASE_URL=postgresql://user:password@host:port/database
PORT=8000
ALLOWED_ORIGINS=*
```

Railway automáticamente provee `DATABASE_URL` si tienes PostgreSQL conectado.

## Health Check

Railway usa el endpoint `/health` para verificar que el servicio esta funcionando (sin depender de DB):
- **Path:** `/health`
- **Timeout:** 100 segundos
- **Política de reinicio:** ON_FAILURE (máximo 3 reintentos)

Para verificar la base de datos, usa el endpoint `/health/db`.

## Railway Healthcheck Details

### Configure the Healthcheck Path
- Ensure your web server has an endpoint (for example `/health`) that returns HTTP 200 when the app is live and ready.
- In Railway service settings, set the healthcheck path to that endpoint.
- The healthcheck is only used during deployment; it is not a continuous monitor.

### Configure the Healthcheck Port
- Railway injects a `PORT` environment variable and uses it for healthchecks.
- Your app must listen on `PORT`. If you use target ports, set `PORT` explicitly so Railway checks the right port.

### Healthcheck Timeout
- Default timeout is 300 seconds.
- You can change it in service settings or set `RAILWAY_HEALTHCHECK_TIMEOUT_SEC`.

### Services with Attached Volumes
- Deployments with attached volumes are not run concurrently; brief downtime is expected.

### Healthcheck Hostname
- Healthcheck requests come from `healthcheck.railway.app`.
- If you restrict allowed hosts, allow this hostname.

### Continuous Healthchecks
- Healthchecks are not used for continuous monitoring after deploy.
- Use an external monitor (for example, Uptime Kuma) if needed.

## Proceso de Deploy

1. **Push a GitHub:** Railway detecta cambios automáticamente
2. **Build:** Usa Dockerfile para construir la imagen
3. **Migraciones:** docker-entrypoint.py ejecuta Alembic automáticamente
4. **Start:** Inicia Uvicorn en el puerto especificado

## Verificar Deploy

Después del deploy, verifica:

```bash
# Health check
curl https://tu-app.railway.app/health
curl https://tu-app.railway.app/health/db

# API docs
curl https://tu-app.railway.app/docs
```

## Solución de Problemas

### Build falla

1. Revisa los logs en Railway dashboard
2. Verifica que requirements.txt esté actualizado
3. Asegúrate que Dockerfile esté en la raíz

### Migraciones fallan

1. Verifica que DATABASE_URL esté configurada
2. Revisa que PostgreSQL esté conectado
3. Chequea los logs de docker-entrypoint.py

### Servicio no inicia

1. Verifica el health check endpoint
2. Revisa que el puerto sea correcto (Railway usa PORT env var)
3. Chequea los logs de Uvicorn

## Logs Útiles

Los logs ahora son más limpios. Verás:
- `✅ Migraciones aplicadas` - Alembic ejecutó correctamente
- `🚀 Backend listo` - Servidor iniciado
- `Starting server...` - Uvicorn arrancando

## Rollback

Si algo sale mal:
1. Ve a Railway dashboard
2. Selecciona un deploy anterior
3. Click en "Redeploy"
