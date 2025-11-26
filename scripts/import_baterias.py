"""
Script para importar baterías de iPhone a la tienda
Ejecutar: python scripts/import_baterias.py
"""
import sys
try:
    import requests
except ImportError:
    print("El paquete 'requests' no está instalado. Instálalo con: python -m pip install requests")
    sys.exit(1)
import base64
import os
import json
from pathlib import Path

# ============================================
# CONFIGURACIÓN
# ============================================
API_URL = "https://fastapi-teamcelular-dev.up.railway.app"
# API_URL = "http://localhost:8080"  # Para pruebas locales

IMGBB_API_KEY = "e8772fdb755d70eabd4a9e99f300592d"

# Carpeta donde colocar las imágenes
IMAGES_FOLDER = Path(__file__).parent / "imagenes_baterias"

# ============================================
# DATOS DE BATERÍAS (costo en pesos)
# ============================================
BATERIAS = [
    # (modelo, marca, costo)
    ("12M", "CK", 23200),
    ("12M", "JC", 43500),
    ("12M", "AMPSENTRIX", 36250),
    ("12/12P", "CK", 24650),
    ("12/12P", "JC", 45675),
    ("12/12P", "AMPSENTRIX", 38425),
    ("12PM", "CK", 30450),
    ("12PM", "JC", 58725),
    ("12PM", "AMPSENTRIX", 51475),
    ("13M", "CK", 23925),
    ("13M", "JC", 44225),
    ("13M", "AMPSENTRIX", 36975),
    ("13", "CK", 26825),
    ("13", "JC", 50750),
    ("13", "AMPSENTRIX", 43500),
    ("13P", "CK", 29725),
    ("13P", "JC", 54375),
    ("13P", "AMPSENTRIX", 47125),
    ("13PM", "CK", 34075),
    ("13PM", "JC", 65975),
    ("13PM", "AMPSENTRIX", 58725),
    ("14", "CK", 26825),
    ("14", "JC", 54375),
    ("14", "AMPSENTRIX", 47125),
    ("14PLUS", "AMPSENTRIX", 52200),
    ("14P", "CK", 29725),
    ("14P", "JC", 58725),
    ("14P", "AMPSENTRIX", 51475),
    ("14PM", "CK", 34800),
    ("14PM", "JC", 68150),
    ("14PM", "AMPSENTRIX", 60900),
    ("15", "AMPSENTRIX", 47850),
    ("15PLUS", "AMPSENTRIX", 54375),
    ("15P", "AMPSENTRIX", 53650),
    ("15PM", "AMPSENTRIX", 65975),
    ("SE3", "AMPSENTRIX", 30450),
]

# ============================================
# FUNCIONES DE PRECIO
# ============================================
def calcular_precio_venta(costo, marca=None):
    """
    Calcula precio de venta. Si se proporciona `marca`, usa multiplicadores por marca:
      - CK: x2.5
      - JC: x2
      - AMPSENTRIX: x2
    Si no se proporciona marca, utiliza la lógica por rangos anterior:
      - Baratas (< 35000): x3.5
      - Medias (35000-55000): x2.5
      - Caras (> 55000): x2
    """
    if marca:
        m = marca.strip().upper()
        if m == "CK":
            precio = costo * 2.5
        elif m in ("JC", "AMPSENTRIX"):
            precio = costo * 2.0
        else:
            # fallback to default range-based pricing for unknown brands
            if costo < 35000:
                precio = costo * 3.5
            elif costo <= 55000:
                precio = costo * 2.5
            else:
                precio = costo * 2
    else:
        if costo < 35000:
            precio = costo * 3.5
        elif costo <= 55000:
            precio = costo * 2.5
        else:
            precio = costo * 2

    return redondear_precio(precio)


def redondear_precio(precio):
    """Redondea a precio psicológico (terminado en 900 o 990)"""
    # Redondear a miles y terminar en 900
    miles = int(precio / 1000)
    return (miles * 1000) + 900


# ============================================
# NOMBRES Y DESCRIPCIONES SEO
# ============================================
def obtener_nombre_modelo_completo(modelo):
    """Convierte código de modelo a nombre completo"""
    modelos = {
        "12M": "iPhone 12 Mini",
        "12/12P": "iPhone 12 / 12 Pro",
        "12PM": "iPhone 12 Pro Max",
        "13M": "iPhone 13 Mini",
        "13": "iPhone 13",
        "13P": "iPhone 13 Pro",
        "13PM": "iPhone 13 Pro Max",
        "14": "iPhone 14",
        "14PLUS": "iPhone 14 Plus",
        "14P": "iPhone 14 Pro",
        "14PM": "iPhone 14 Pro Max",
        "15": "iPhone 15",
        "15PLUS": "iPhone 15 Plus",
        "15P": "iPhone 15 Pro",
        "15PM": "iPhone 15 Pro Max",
            "SE3": "iPhone SE (3rd generation)",
    }
    return modelos.get(modelo, f"iPhone {modelo}")


def generar_nombre_producto(modelo, marca):
    """Genera nombre de producto optimizado para búsquedas"""
    nombre_modelo = obtener_nombre_modelo_completo(modelo)
    return f"Cambio de Batería {nombre_modelo} - {marca}"


def generar_descripcion_seo(modelo, marca):
    """Genera descripción SEO optimizada para Google"""
    nombre_modelo = obtener_nombre_modelo_completo(modelo)
    
    # Descripciones según calidad de marca
    calidad_marca = {
        "CK": "estándar con excelente relación calidad-precio",
        "AMPSENTRIX": "premium de alta capacidad y larga duración",
        "JC": "original de máxima calidad certificada"
    }
    
    calidad = calidad_marca.get(marca, "de excelente calidad")
    
    descripcion = (
        f"🔋 Servicio profesional de cambio de batería para {nombre_modelo}. "
        f"Batería {marca} {calidad}. "
        f"✅ Instalación realizada por técnicos certificados con herramientas especializadas. "
        f"✅ Batería nueva de excelente calidad que restaura la autonomía original de tu iPhone. "
        f"✅ Garantía de 3 meses incluida. "
        f"⚡ Mejora el rendimiento y la duración de carga de tu {nombre_modelo}. "
        f"📱 Solución ideal si tu iPhone se apaga inesperadamente, carga lento o muestra 'Batería agotada'. "
        f"🏪 Servicio rápido disponible en tienda. ¡Recupera la vida útil de tu iPhone hoy!"
    )
    
    return descripcion


# ============================================
# FUNCIONES DE IMGBB
# ============================================
def subir_imagen_imgbb(imagen_path):
    """Sube una imagen a ImgBB y retorna la URL"""
    try:
        with open(imagen_path, "rb") as file:
            image_data = base64.b64encode(file.read()).decode("utf-8")
        
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": IMGBB_API_KEY,
                "image": image_data,
                "name": imagen_path.stem
            }
        )
        
        if response.status_code == 200:
            url = response.json()["data"]["url"]
            print(f"  ✅ Imagen subida: {imagen_path.name}")
            return url
        else:
            print(f"  ❌ Error subiendo {imagen_path.name}: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def obtener_imagenes_modelo(modelo, marca):
    """
    Busca imágenes para un modelo específico.
    Intenta varias carpetas posibles según el código del modelo.
    
    Ejemplo para modelo "12/12P":
      - Busca en: 12/, 12P/, 12-12P/
    Ejemplo para modelo "12M":
      - Busca en: 12M/
    Ejemplo para modelo "13PM":
      - Busca en: 13PM/
    
    Si no encuentra, usa general/
    """
    imagenes = []
    origen = "general"
    
    # Generar lista de carpetas posibles a buscar
    carpetas_posibles = []
    
    # Si el modelo tiene "/" (ej: "12/12P"), buscar en ambas partes
    if "/" in modelo:
        partes = modelo.split("/")
        for parte in partes:
            carpetas_posibles.append(parte)
        # También probar con guión
        carpetas_posibles.append(modelo.replace("/", "-"))
    else:
        carpetas_posibles.append(modelo)
    
    # Buscar en las carpetas posibles
    for carpeta_nombre in carpetas_posibles:
        carpeta_modelo = IMAGES_FOLDER / carpeta_nombre
        if carpeta_modelo.exists() and carpeta_modelo.is_dir():
            for img in carpeta_modelo.glob("*"):
                if img.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    imagenes.append(img)
            if imagenes:
                origen = f"modelo ({carpeta_nombre})"
                break  # Encontró imágenes, no seguir buscando
    
    # Si no hay imágenes específicas, usar las generales
    if not imagenes:
        carpeta_general = IMAGES_FOLDER / "general"
        if carpeta_general.exists() and carpeta_general.is_dir():
            for img in carpeta_general.glob("*"):
                if img.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    imagenes.append(img)
    
    # Debug: mostrar de dónde vienen las imágenes
    if imagenes:
        print(f"   📂 Imágenes desde: {origen}")
    
    return imagenes


# ============================================
# FUNCIONES DE API
# ============================================
def login(username, password):
    """Obtiene token de autenticación"""
    response = requests.post(
        f"{API_URL}/admin/login",
        json={"identifier": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Error login: {response.text}")


def obtener_o_crear_categoria(token, nombre):
    """Obtiene o crea una categoría"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Buscar existente
    response = requests.get(f"{API_URL}/categories/get/all")
    categorias = response.json()
    for cat in categorias:
        if cat["name"].lower() == nombre.lower():
            return cat["id"]
    
    # Crear nueva
    response = requests.post(
        f"{API_URL}/categories/create",
        headers=headers,
        json={"name": nombre, "description": "Servicios de reparación de dispositivos"}
    )
    if response.status_code in [200, 201]:
        return response.json()["id"]
    raise Exception(f"Error creando categoría: {response.text}")


def obtener_o_crear_marca(token, nombre):
    """Obtiene o crea una marca"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Buscar existente
    response = requests.get(f"{API_URL}/brands/get/all")
    marcas = response.json()
    for marca in marcas:
        if marca["name"].lower() == nombre.lower():
            return marca["id"]
    
    # Crear nueva
    response = requests.post(
        f"{API_URL}/brands/create",
        headers=headers,
        json={"name": nombre}
    )
    if response.status_code in [200, 201]:
        return response.json()["id"]
    raise Exception(f"Error creando marca: {response.text}")


def obtener_o_crear_branch(token, nombre="Tienda Principal"):
    """Obtiene o crea una sucursal"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_URL}/branches/get/all")
    branches = response.json()
    if branches:
        return branches[0]["id"]
    
    response = requests.post(
        f"{API_URL}/branches/create",
        headers=headers,
        json={"name": nombre, "location": "Principal"}
    )
    if response.status_code in [200, 201]:
        return response.json()["id"]
    raise Exception(f"Error creando branch: {response.text}")


def buscar_producto_por_serial(token, serial):
    """Busca un producto por su serial_number y retorna su ID si existe"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Endpoint correcto: /products/all
        response = requests.get(f"{API_URL}/products/all", headers=headers)
        if response.status_code == 200:
            productos = response.json()
            # Puede ser una lista o un dict con 'items'
            if isinstance(productos, dict):
                productos = productos.get("items", productos.get("products", []))
            for prod in productos:
                prod_serial = prod.get("serial_number", "") or ""
                if prod_serial.lower() == serial.lower():
                    return prod.get("id")
    except Exception as e:
        print(f"   ⚠️ Error buscando producto: {e}")
    return None


def actualizar_producto(token, product_id, nombre, descripcion, costo, precio, categoria_id, marca_id):
    """Actualiza un producto existente"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Endpoint correcto: PUT /products/update?product_id=X
    response = requests.put(
        f"{API_URL}/products/update",
        headers=headers,
        params={"product_id": product_id},
        json={
            "name": nombre,
            "description": descripcion,
            "cost": costo,
            "retail_price": precio,
            "category_id": categoria_id,
            "brand_id": marca_id,
            "warranty_time": 3,
            "warranty_unit": "MONTHS",
            "status": "ACTIVE"
        }
    )
    
    if response.status_code in [200, 201]:
        return True
    else:
        print(f"  ⚠️ Error actualizando producto: {response.text}")
        return False


def crear_producto(token, serial, nombre, descripcion, costo, precio, categoria_id, marca_id):
    """Crea un producto"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_URL}/products/create",
        headers=headers,
        json={
            "serial_number": serial,
            "name": nombre,
            "description": descripcion,
            "cost": costo,
            "retail_price": precio,
            "category_id": categoria_id,
            "brand_id": marca_id,
            "warranty_time": 3,
            "warranty_unit": "MONTHS",
            "status": "ACTIVE"
        }
    )
    
    if response.status_code in [200, 201]:
        return response.json()["id"]
    elif "ya existe" in response.text.lower() or "duplicate" in response.text.lower():
        # Producto ya existe - retornamos -1 para indicar que hay que actualizarlo
        return -1
    else:
        raise Exception(f"Error creando producto: {response.text}")


def obtener_variantes_producto(token, product_id):
    """Obtiene las variantes de un producto"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{API_URL}/products/get/variant",
            headers=headers,
            params={"product_id": product_id}
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []


def crear_variante(token, product_id, branch_id, imagenes_urls):
    """Crea o actualiza una variante del producto (upsert)."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Usar endpoint upsert: crea si no existe, actualiza si existe
    response = requests.put(
        f"{API_URL}/products/upsert/variant",
        headers=headers,
        json={
            "variants": [{
                "product_id": product_id,
                "branch_id": branch_id,
                "stock": 10,
                "min_stock": 2,
                "images": imagenes_urls if imagenes_urls else []
            }]
        }
    )
    
    if response.status_code in [200, 201]:
        print(f"  ✅ Variante creada/actualizada con imágenes")
        return True
    else:
        print(f"  ⚠️ Error en variante: {response.text}")
        return False


def generar_payload_producto(serial, nombre, descripcion, costo, precio, categoria_id, marca_id, branch_id, imagenes_locales):
    """Genera el payload JSON que se enviaría al API para crear producto + variante.

    Esto se usa en modo 'preview' para mostrar cómo quedarían los objetos
    sin enviarlos a la API.
    """
    producto = {
        "serial_number": serial,
        "name": nombre,
        "description": descripcion,
        "cost": costo,
        "retail_price": precio,
        "category_id": categoria_id,
        "brand_id": marca_id,
        "warranty_time": 3,
        "warranty_unit": "MONTHS",
        "status": "ACTIVE"
    }

    variante = {
        "branch_id": branch_id,
        "stock": 10,
        "min_stock": 2,
        # En preview mostramos rutas/archivos locales en vez de URLs subidas
        "images_local": imagenes_locales or []
    }

    return {"product": producto, "variant": variante}


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    print("=" * 60)
    print("🔋 IMPORTADOR DE BATERÍAS iPHONE")
    print("=" * 60)
    
    # Credenciales
    print("\n📝 Ingresa tus credenciales de admin:")
    username = input("Usuario o email: ").strip()
    password = input("Contraseña: ").strip()
    
    try:
        print("\n🔐 Iniciando sesión...")
        token = login(username, password)
        print("✅ Sesión iniciada")
        
        print("\n📁 Configurando categoría y sucursal...")
        categoria_id = obtener_o_crear_categoria(token, "Reparaciones")
        branch_id = obtener_o_crear_branch(token)
        print(f"✅ Categoría ID: {categoria_id}, Branch ID: {branch_id}")
        
        # Cache de marcas
        marcas_cache = {}
        
        print("\n🔋 Importando baterías...")
        print("-" * 60)
        
        exitos = 0
        errores = 0

        # Preguntar si el usuario desea previsualizar los payloads
        preview_input = input("\n¿Deseas previsualizar los productos antes de crearlos? (s/n): ").strip().lower()
        preview_mode = preview_input in ("s", "y", "si", "yes")

        for modelo, marca, costo in BATERIAS:
            nombre = generar_nombre_producto(modelo, marca)
            serial = f"BAT-{modelo}-{marca}".replace("/", "-")
            precio = calcular_precio_venta(costo, marca)
            
            print(f"\n📱 {nombre}")
            print(f"   Costo: ${costo:,.0f} → Precio: ${precio:,.0f}")
            
            try:
                # Obtener/crear marca (si no está en cache)
                if marca not in marcas_cache:
                    marcas_cache[marca] = obtener_o_crear_marca(token, marca)
                marca_id = marcas_cache[marca]
                
                # Buscar imágenes locales
                imagenes_paths = obtener_imagenes_modelo(modelo, marca)
                imagenes_locales = [str(p) for p in imagenes_paths] if imagenes_paths else []
                
                if imagenes_paths:
                    print(f"   📷 Encontradas {len(imagenes_paths)} imagen(es) locales")
                
                # Crear producto con descripción SEO
                descripcion = generar_descripcion_seo(modelo, marca)

                if preview_mode:
                    # Generar y mostrar payload en vez de enviarlo
                    payload = generar_payload_producto(
                        serial, nombre, descripcion, costo, precio,
                        categoria_id, marca_id, branch_id, imagenes_locales
                    )
                    print("   🔎 PREVIEW payload:")
                    print(json.dumps(payload, ensure_ascii=False, indent=2))
                    continue

                # Verificar si el producto ya existe (búsqueda previa)
                product_id_existente = buscar_producto_por_serial(token, serial)
                product_id_final = None  # ID del producto (nuevo o existente)
                
                if product_id_existente and product_id_existente > 0:
                    # Actualizar producto existente
                    print(f"   🔄 Producto existente (ID: {product_id_existente}), actualizando...")
                    if actualizar_producto(
                        token, product_id_existente, nombre, descripcion,
                        costo, precio, categoria_id, marca_id
                    ):
                        print(f"   ✅ Producto actualizado")
                        product_id_final = product_id_existente
                    else:
                        errores += 1
                        continue
                else:
                    # Intentar crear producto nuevo
                    product_id = crear_producto(
                        token, serial, nombre, descripcion, 
                        costo, precio, categoria_id, marca_id
                    )
                    
                    if product_id == -1:
                        # El API detectó duplicado - buscar y actualizar
                        print(f"   🔄 Producto detectado como existente, buscando...")
                        product_id_existente = buscar_producto_por_serial(token, serial)
                        if product_id_existente:
                            if actualizar_producto(
                                token, product_id_existente, nombre, descripcion,
                                costo, precio, categoria_id, marca_id
                            ):
                                print(f"   ✅ Producto actualizado")
                                product_id_final = product_id_existente
                            else:
                                errores += 1
                                continue
                        else:
                            print(f"   ⚠️ No se pudo encontrar el producto")
                            errores += 1
                            continue
                    elif product_id:
                        print(f"   ✅ Producto nuevo creado (ID: {product_id})")
                        product_id_final = product_id
                    else:
                        errores += 1
                        continue
                
                # SIEMPRE intentar crear variante con imágenes (si hay product_id)
                if product_id_final:
                    # Subir imágenes a ImgBB
                    imagenes_urls = []
                    if imagenes_paths:
                        print(f"   📤 Subiendo {len(imagenes_paths)} imagen(es)...")
                        for img_path in imagenes_paths:
                            url = subir_imagen_imgbb(img_path)
                            if url:
                                imagenes_urls.append(url)
                    
                    # Crear variante (si ya existe, se ignora silenciosamente)
                    crear_variante(token, product_id_final, branch_id, imagenes_urls)
                    exitos += 1
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                errores += 1
        
        print("\n" + "=" * 60)
        print(f"📊 RESUMEN: {exitos} exitosos, {errores} errores")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
