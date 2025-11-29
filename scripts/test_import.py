"""
Script de prueba para importar una batería de ejemplo
Ejecutar: python scripts/test_import.py
"""
import sys
import requests

API_URL = "https://fastapi-teamcelular-dev.up.railway.app"
# API_URL = "http://localhost:8000"

def test_import():
    print("🧪 Test de importación de batería")
    print("=" * 60)
    
    # 1. Login
    print("\n1. Login...")
    username = input("Usuario: ").strip()
    password = input("Contraseña: ").strip()
    
    response = requests.post(
        f"{API_URL}/admin/login",
        json={"identifier": username, "password": password}
    )
    
    if response.status_code != 200:
        print(f"❌ Error login: {response.text}")
        return
    
    token = response.json()["access_token"]
    print("✅ Login exitoso")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Obtener categoría
    print("\n2. Obteniendo categoría 'Reparaciones'...")
    response = requests.get(f"{API_URL}/categories/get/all")
    categorias = response.json()
    categoria_id = None
    for cat in categorias:
        if cat["name"].lower() == "reparaciones":
            categoria_id = cat["id"]
            break
    
    if not categoria_id:
        print("❌ Categoría 'Reparaciones' no encontrada")
        return
    
    print(f"✅ Categoría ID: {categoria_id}")
    
    # 3. Obtener marca
    print("\n3. Obteniendo marca 'AMPSENTRIX'...")
    response = requests.get(f"{API_URL}/brands/get/all")
    marcas = response.json()
    marca_id = None
    for marca in marcas:
        if marca["name"] == "AMPSENTRIX":
            marca_id = marca["id"]
            break
    
    if not marca_id:
        print("❌ Marca 'AMPSENTRIX' no encontrada")
        return
    
    print(f"✅ Marca ID: {marca_id}")
    
    # 4. Obtener branch
    print("\n4. Obteniendo sucursal...")
    response = requests.get(f"{API_URL}/branches/get/all")
    branches = response.json()
    if not branches:
        print("❌ No hay sucursales")
        return
    
    branch_id = branches[0]["id"]
    print(f"✅ Branch ID: {branch_id}")
    
    # 5. Crear producto de prueba
    print("\n5. Creando producto de prueba...")
    producto = {
        "serial_number": "BAT-TEST-001",
        "name": "Cambio de Batería iPhone 15 - AMPSENTRIX (TEST)",
        "description": "Producto de prueba",
        "cost": 47850,
        "retail_price": 95700,
        "category_id": categoria_id,
        "brand_id": marca_id,
        "warranty_time": 3,
        "warranty_unit": "MONTHS",
        "status": "ACTIVE"
    }
    
    response = requests.post(
        f"{API_URL}/products/create",
        headers=headers,
        json=producto
    )
    
    if response.status_code not in [200, 201]:
        print(f"⚠️ Producto ya existe o error: {response.text}")
        # Buscar el producto existente
        response = requests.get(f"{API_URL}/products/all", headers=headers)
        productos = response.json()
        product_id = None
        for p in productos:
            if p.get("serial_number") == "BAT-TEST-001":
                product_id = p["id"]
                break
        if not product_id:
            print("❌ No se pudo obtener el producto")
            return
    else:
        product_id = response.json()["id"]
    
    print(f"✅ Producto ID: {product_id}")
    
    # 6. Crear variante con imágenes
    print("\n6. Creando variante con imágenes...")
    variante = {
        "variants": [{
            "product_id": product_id,
            "branch_id": branch_id,
            "stock": 10,
            "min_stock": 2,
            "images": [
                "https://i.ibb.co/test1.jpg",
                "https://i.ibb.co/test2.jpg"
            ]
        }]
    }
    
    response = requests.put(
        f"{API_URL}/products/upsert/variant",
        headers=headers,
        json=variante
    )
    
    if response.status_code in [200, 201]:
        print("✅ Variante creada exitosamente")
        print(f"Respuesta: {response.json()}")
    else:
        print(f"❌ Error creando variante: {response.text}")
        return
    
    # 7. Verificar variante
    print("\n7. Verificando variante...")
    response = requests.get(
        f"{API_URL}/products/get/{product_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        producto = response.json()
        variantes = producto.get("variants", [])
        if variantes:
            print(f"✅ Variante encontrada con {len(variantes[0].get('images', []))} imagen(es)")
            for img in variantes[0].get("images", []):
                print(f"   📷 {img.get('image_url')}")
        else:
            print("⚠️ No se encontraron variantes")
    else:
        print(f"❌ Error obteniendo producto: {response.text}")
    
    print("\n" + "=" * 60)
    print("✅ Test completado")

if __name__ == "__main__":
    test_import()
