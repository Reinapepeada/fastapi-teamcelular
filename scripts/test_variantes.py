"""
Script de prueba para verificar variantes e imágenes
Ejecutar: python scripts/test_variantes.py
"""
import sys
try:
    import requests
except ImportError:
    print("El paquete 'requests' no está instalado. Instálalo con: python -m pip install requests")
    sys.exit(1)

API_URL = "https://fastapi-teamcelular-dev.up.railway.app"
# API_URL = "http://localhost:8080"  # Para pruebas locales

def main():
    print("=" * 60)
    print("🔍 VERIFICADOR DE VARIANTES E IMÁGENES")
    print("=" * 60)
    
    # Credenciales
    print("\n📝 Ingresa tus credenciales de admin:")
    username = input("Usuario o email: ").strip()
    password = input("Contraseña: ").strip()
    
    try:
        # Login
        print("\n🔐 Iniciando sesión...")
        response = requests.post(
            f"{API_URL}/admin/login",
            json={"identifier": username, "password": password}
        )
        if response.status_code != 200:
            print(f"❌ Error de login: {response.text}")
            return 1
        
        token = response.json()["access_token"]
        print("✅ Sesión iniciada")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Obtener todos los productos
        print("\n📦 Obteniendo productos...")
        response = requests.get(f"{API_URL}/products/all", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo productos: {response.text}")
            return 1
        
        productos = response.json()
        if isinstance(productos, dict):
            productos = productos.get("items", productos.get("products", []))
        
        # Filtrar solo baterías
        baterias = [p for p in productos if "Batería" in p.get("name", "")]
        
        print(f"✅ Encontradas {len(baterias)} baterías")
        print("\n" + "=" * 60)
        
        # Verificar cada batería
        total_variantes = 0
        total_imagenes = 0
        sin_variantes = []
        sin_imagenes = []
        
        for producto in baterias:
            product_id = producto.get("id")
            nombre = producto.get("name", "Sin nombre")
            
            # Obtener detalles completos del producto
            response = requests.get(
                f"{API_URL}/products/get/{product_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"⚠️ Error obteniendo detalles de: {nombre}")
                continue
            
            detalles = response.json()
            variantes = detalles.get("variants", [])
            
            print(f"\n📱 {nombre}")
            print(f"   ID: {product_id}")
            
            if not variantes:
                print(f"   ⚠️ SIN VARIANTES")
                sin_variantes.append(nombre)
            else:
                total_variantes += len(variantes)
                print(f"   ✅ Variantes: {len(variantes)}")
                
                for i, variante in enumerate(variantes, 1):
                    sku = variante.get("sku", "N/A")
                    stock = variante.get("stock", 0)
                    imagenes = variante.get("images", [])
                    num_imagenes = len(imagenes)
                    
                    print(f"      Variante {i}: SKU={sku}, Stock={stock}, Imágenes={num_imagenes}")
                    
                    if num_imagenes == 0:
                        sin_imagenes.append(f"{nombre} (Variante {i})")
                    else:
                        total_imagenes += num_imagenes
                        for j, img in enumerate(imagenes, 1):
                            url = img.get("image_url", "N/A")
                            print(f"         Imagen {j}: {url[:60]}...")
        
        # Resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN")
        print("=" * 60)
        print(f"Total de baterías: {len(baterias)}")
        print(f"Total de variantes: {total_variantes}")
        print(f"Total de imágenes: {total_imagenes}")
        
        if sin_variantes:
            print(f"\n⚠️ Productos SIN variantes ({len(sin_variantes)}):")
            for nombre in sin_variantes:
                print(f"   - {nombre}")
        
        if sin_imagenes:
            print(f"\n⚠️ Variantes SIN imágenes ({len(sin_imagenes)}):")
            for nombre in sin_imagenes:
                print(f"   - {nombre}")
        
        if not sin_variantes and not sin_imagenes:
            print("\n✅ ¡Todos los productos tienen variantes e imágenes!")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
