"""
Script para probar el health check endpoint
Ejecutar: python scripts/test_health.py
"""

import requests
import sys

# Cambiar según tu entorno
URLS = ["https://fastapi-teamcelular-dev.up.railway.app", "http://localhost:8000"]


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

    ok = True
    try:
        # Test health endpoint (no DB dependency)
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"OK Health check: {data}")
            if data.get("status") != "healthy":
                print(f"FAIL Status: {data.get('status')}")
                ok = False
        else:
            print(f"FAIL Health check: Status {response.status_code}")
            print(f"   Response: {response.text}")
            ok = False
    except Exception as e:
        print(f"ERR Health check: {e}")
        ok = False

    try:
        # Test database health endpoint
        response = requests.get(f"{url}/health/db", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"OK DB health: {data}")
            if data.get("status") != "healthy":
                print(f"FAIL DB status: {data.get('status')}")
                ok = False
        else:
            print(f"FAIL DB health: Status {response.status_code}")
            print(f"   Response: {response.text}")
            ok = False
    except Exception as e:
        print(f"ERR DB health: {e}")
        ok = False

    return ok


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
