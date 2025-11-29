"""
Script para probar el health check endpoint
Ejecutar: python scripts/test_health.py
"""
import requests
import sys

# Cambiar según tu entorno
URLS = [
    "https://fastapi-teamcelular-dev.up.railway.app",
    "http://localhost:8000"
]

def test_health(url):
    """Prueba el endpoint de health check"""
    print(f"\n🔍 Probando: {url}")
    print("-" * 60)
    
    try:
        # Test root endpoint
        response = requests.get(f"{url}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Root endpoint: {response.json()}")
        else:
            print(f"⚠️  Root endpoint: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint: {e}")
        return False
    
    try:
        # Test health endpoint
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data}")
            if data.get("status") == "healthy":
                print(f"✅ Database: {data.get('database', 'unknown')}")
                return True
            else:
                print(f"⚠️  Status: {data.get('status')}")
                return False
        else:
            print(f"❌ Health check: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check: {e}")
        return False

def main():
    print("=" * 60)
    print("🏥 TEST DE HEALTH CHECK")
    print("=" * 60)
    
    # Preguntar qué URL probar
    print("\nSelecciona el entorno:")
    print("1. Producción (Railway)")
    print("2. Local (localhost:8000)")
    print("3. Ambos")
    
    choice = input("\nOpción (1/2/3): ").strip()
    
    urls_to_test = []
    if choice == "1":
        urls_to_test = [URLS[0]]
    elif choice == "2":
        urls_to_test = [URLS[1]]
    else:
        urls_to_test = URLS
    
    results = []
    for url in urls_to_test:
        result = test_health(url)
        results.append((url, result))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    for url, result in results:
        status = "✅ OK" if result else "❌ FAIL"
        print(f"{status} - {url}")
    print("=" * 60)
    
    # Exit code
    if all(r for _, r in results):
        print("\n✅ Todos los tests pasaron")
        sys.exit(0)
    else:
        print("\n⚠️  Algunos tests fallaron")
        sys.exit(1)

if __name__ == "__main__":
    main()
