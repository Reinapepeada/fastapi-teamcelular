"""
Script para verificar variantes de productos
Ejecutar: python scripts/check_variants.py
"""

import requests

API_URL = "https://fastapi-teamcelular-dev.up.railway.app"
# API_URL = "http://localhost:8000"


def check_variants():
    print("🔍 Verificando variantes de productos")
    print("=" * 60)

    # Obtener todos los productos
    response = requests.get(f"{API_URL}/products/all")

    if response.status_code != 200:
        print(f"❌ Error obteniendo productos: {response.text}")
        return

    productos = response.json()
    print(f"\n📦 Total de productos: {len(productos)}")

    # Estadísticas
    con_variantes = 0
    sin_variantes = 0
    con_imagenes = 0
    sin_imagenes = 0

    print("\n" + "=" * 60)

    for producto in productos:
        variantes = producto.get("variants", [])
        nombre = producto.get("name", "Sin nombre")

        if variantes:
            con_variantes += 1
            for variante in variantes:
                imagenes = variante.get("images", [])
                if imagenes:
                    con_imagenes += 1
                    print(f"✅ {nombre}")
                    print(f"   Variante ID: {variante.get('id')}")
                    print(f"   Stock: {variante.get('stock')}")
                    print(f"   Imágenes: {len(imagenes)}")
                    for img in imagenes:
                        print(f"      📷 {img.get('image_url')}")
                else:
                    sin_imagenes += 1
                    print(f"⚠️  {nombre}")
                    print(f"   Variante ID: {variante.get('id')}")
                    print(f"   Stock: {variante.get('stock')}")
                    print(f"   ⚠️  Sin imágenes")
        else:
            sin_variantes += 1
            print(f"❌ {nombre}")
            print(f"   Sin variantes")

        print()

    # Resumen
    print("=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"Productos con variantes: {con_variantes}")
    print(f"Productos sin variantes: {sin_variantes}")
    print(f"Variantes con imágenes: {con_imagenes}")
    print(f"Variantes sin imágenes: {sin_imagenes}")
    print("=" * 60)


if __name__ == "__main__":
    check_variants()
