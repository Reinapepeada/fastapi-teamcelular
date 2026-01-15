"""
Script de prueba para la funcionalidad de carga masiva con upsert inteligente
"""
import requests
import os

BASE_URL = "http://localhost:8000"

def test_bulk_upload_workflow():
    """
    Prueba el flujo completo de carga masiva:
    1. Descarga template vacío
    2. Descarga productos existentes
    3. Prueba carga masiva (requiere autenticación)
    """
    
    print("=" * 60)
    print("PRUEBA DE CARGA MASIVA DE PRODUCTOS")
    print("=" * 60)
    
    # 1. Descargar template vacío (público)
    print("\n1. Descargando template vacío...")
    try:
        response = requests.get(f"{BASE_URL}/product/bulk-upload/template")
        if response.status_code == 200:
            with open("template_test.xlsx", "wb") as f:
                f.write(response.content)
            print("   ✅ Template descargado: template_test.xlsx")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        print("   ℹ️  Asegúrate de que el servidor esté corriendo")
        return
    
    # 2. Intentar descargar productos existentes (requiere auth)
    print("\n2. Intentando descargar productos existentes...")
    print("   ⚠️  Este endpoint requiere autenticación")
    print("   ℹ️  Pasos para probarlo:")
    print("      a) Obtén un token de autenticación")
    print("      b) Ejecuta:")
    print(f'         curl -H "Authorization: Bearer <token>" \\')
    print(f'              {BASE_URL}/product/bulk-upload/export \\')
    print(f'              -o productos_exportados.xlsx')
    
    # 3. Información sobre carga masiva
    print("\n3. Para probar la carga masiva:")
    print("   ⚠️  Requiere autenticación (Editor o superior)")
    print("   📝 Pasos:")
    print("      a) Llena el archivo template_test.xlsx o productos_exportados.xlsx")
    print("      b) Ejecuta:")
    print(f'         curl -X POST "{BASE_URL}/product/bulk-upload?skip_errors=true" \\')
    print(f'              -H "Authorization: Bearer <token>" \\')
    print(f'              -F "file=@template_test.xlsx"')
    
    print("\n" + "=" * 60)
    print("CARACTERÍSTICAS DE UPSERT INTELIGENTE")
    print("=" * 60)
    
    print("\n🔍 Detección de Duplicados:")
    print("   • Productos: identificados por serial_number")
    print("   • Variantes: product_id + color + size + size_unit + unit")
    
    print("\n✨ Comportamiento:")
    print("   • Producto/variante NUEVO → ✅ Se crea")
    print("   • Producto/variante EXISTENTE con cambios → ✅ Se actualiza")
    print("   • Producto/variante EXISTENTE sin cambios → ⏭️ Se omite")
    
    print("\n📊 Campos actualizables en productos:")
    print("   • name, description")
    print("   • brand_id, category_id")
    print("   • warranty_time, warranty_unit")
    print("   • cost, retail_price")
    print("   • status")
    
    print("\n📊 Campos actualizables en variantes:")
    print("   • branch_id")
    print("   • stock, min_stock")
    print("   • images (si se proporcionan nuevas)")
    
    print("\n🎯 Casos de uso:")
    print("   1. Actualizar precios: modifica retail_price y sube el Excel")
    print("   2. Actualizar stock: modifica variant_stock y sube el Excel")
    print("   3. Agregar variantes: duplica fila, cambia color/talla, sube")
    print("   4. Mezcla: crea nuevos + actualiza existentes en un solo archivo")
    
    print("\n" + "=" * 60)
    
    # Verificar que el template se creó
    if os.path.exists("template_test.xlsx"):
        size = os.path.getsize("template_test.xlsx")
        print(f"\n✅ Archivo creado exitosamente: template_test.xlsx ({size} bytes)")
        print("   Abre este archivo en Excel para ver el formato")
    
    print("\n" + "=" * 60)
    print("FIN DE LA PRUEBA")
    print("=" * 60)


def show_api_documentation():
    """Muestra documentación de los endpoints"""
    print("\n" + "=" * 60)
    print("DOCUMENTACIÓN DE ENDPOINTS")
    print("=" * 60)
    
    endpoints = [
        {
            "method": "GET",
            "path": "/product/bulk-upload/template",
            "auth": "No requerida",
            "description": "Descarga template Excel vacío con ejemplos"
        },
        {
            "method": "GET",
            "path": "/product/bulk-upload/export",
            "auth": "Editor+",
            "description": "Exporta productos existentes de la BD a Excel"
        },
        {
            "method": "POST",
            "path": "/product/bulk-upload",
            "auth": "Editor+",
            "description": "Carga masiva de productos desde Excel"
        }
    ]
    
    for ep in endpoints:
        print(f"\n{ep['method']} {ep['path']}")
        print(f"   Auth: {ep['auth']}")
        print(f"   {ep['description']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_bulk_upload_workflow()
    show_api_documentation()
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Asegúrate de que el servidor FastAPI esté corriendo")
    print("   2. Obtén un token de autenticación")
    print("   3. Prueba exportar productos existentes")
    print("   4. Modifica el Excel exportado")
    print("   5. Sube el Excel y observa el comportamiento de upsert")
    print()
