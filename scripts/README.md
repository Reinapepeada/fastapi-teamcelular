# 🔋 GUÍA RÁPIDA - Importar Baterías iPhone

## 📁 PASO 1: Preparar Imágenes (Opcional)

Crea esta estructura de carpetas:

```
scripts/
└── imagenes_baterias/
    ├── 12M/
    │   └── (fotos de batería 12 Mini)
    ├── 12PM/
    │   └── (fotos de batería 12 Pro Max)
    ├── 13/
    │   └── (fotos de batería 13)
    ├── 13P/
    │   └── (fotos de batería 13 Pro)
    └── general/
        └── bateria_generica.jpg  ← Usada si no hay específica
```

**Formatos aceptados:** .jpg, .jpeg, .png, .webp

**Si no colocas imágenes**, los productos se crean sin fotos.

---

## 🚀 PASO 2: Ejecutar el Script

Abre terminal en la carpeta del proyecto y ejecuta:

```bash
# Windows
python scripts/import_baterias.py

# Si no funciona, intenta:
py scripts/import_baterias.py
```

---

## 📝 PASO 3: Ingresar Credenciales

El script te pedirá:
- **Usuario o email** del admin
- **Contraseña**

---

## 💰 PRECIOS CALCULADOS

| Rango Costo | Multiplicador | Ejemplo |
|-------------|---------------|---------|
| < $35,000 | x3.5 | $23,200 → $81,900 |
| $35,000 - $55,000 | x2.5 | $43,500 → $108,900 |
| > $55,000 | x2.0 | $65,975 → $131,900 |

*Todos los precios se redondean a terminación en 900*

---

## ✅ Resultado

El script creará:
- **Categoría:** "Reparaciones"
- **Marcas:** CK, JC, AMPSENTRIX
- **35 productos** de baterías con sus precios

---

## 🧪 Script de Prueba

Antes de importar todo, prueba con un producto:

```bash
python scripts/test_import.py
```

Este script crea un producto de prueba con variante e imágenes para verificar que todo funciona.

---

## ⚠️ Solución de Errores

**"requests no está instalado":**
```bash
pip install requests
```

**"Error de login":**
- Verifica usuario y contraseña
- Asegúrate de tener rol EDITOR o superior

**"Producto ya existe":**
- El script actualiza productos existentes automáticamente

**"Error creando variante":**
- Verifica que exista al menos una sucursal (branch)
- Revisa los logs del servidor para más detalles
