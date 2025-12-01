"""
Script de inicialización para Team Celular API
Ejecutar: python run.py
"""
import os
import sys
import subprocess
from pathlib import Path

# Colores para la terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Muestra el banner de la aplicación"""
    print(f"""
{Colors.BLUE}{Colors.BOLD}
╔══════════════════════════════════════════════════════╗
║           🛒 TEAM CELULAR API                        ║
║           Catálogo de Productos                      ║
╚══════════════════════════════════════════════════════╝
{Colors.END}""")


def check_env_file():
    """Verifica que exista el archivo .env"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        print(f"{Colors.YELLOW}⚠️  Archivo .env no encontrado{Colors.END}")
        
        if env_example_path.exists():
            print(f"{Colors.BLUE}📋 Copiando .env.example a .env...{Colors.END}")
            with open(env_example_path, 'r') as src:
                content = src.read()
            with open(env_path, 'w') as dst:
                dst.write(content)
            print(f"{Colors.YELLOW}⚠️  Por favor, edita el archivo .env con tus credenciales de PostgreSQL{Colors.END}")
            return False
        else:
            print(f"{Colors.RED}❌ No se encontró .env.example{Colors.END}")
            print(f"{Colors.YELLOW}Crea un archivo .env con:{Colors.END}")
            print("DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/teamcelular")
            return False
    
    # Verificar que DATABASE_URL esté configurada
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "password" in db_url:
        print(f"{Colors.YELLOW}⚠️  Configura DATABASE_URL en el archivo .env{Colors.END}")
        return False
    
    print(f"{Colors.GREEN}✅ Archivo .env configurado{Colors.END}")
    return True


def check_database_connection():
    """Verifica la conexión a la base de datos"""
    print(f"{Colors.BLUE}🔌 Verificando conexión a PostgreSQL...{Colors.END}")
    
    try:
        from database.connection.SQLConection import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        print(f"{Colors.GREEN}✅ Conexión a PostgreSQL exitosa{Colors.END}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Error de conexión: {str(e)}{Colors.END}")
        print(f"{Colors.YELLOW}Verifica que:{Colors.END}")
        print("  • PostgreSQL esté ejecutándose")
        print("  • La base de datos exista")
        print("  • Las credenciales sean correctas")
        return False


def run_migrations():
    """Ejecuta las migraciones de Alembic"""
    print(f"{Colors.BLUE}🔄 Ejecutando migraciones...{Colors.END}")
    
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Migraciones aplicadas correctamente{Colors.END}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  Migraciones: {result.stderr}{Colors.END}")
            return True  # Continuar aunque haya warnings
            
    except FileNotFoundError:
        print(f"{Colors.YELLOW}⚠️  Alembic no encontrado, saltando migraciones{Colors.END}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Error en migraciones: {str(e)}{Colors.END}")
        return False


def create_tables():
    """Crea las tablas directamente si las migraciones fallan"""
    print(f"{Colors.BLUE}📦 Creando tablas en la base de datos...{Colors.END}")
    
    try:
        from database.connection.SQLConection import create_db_and_tables
        create_db_and_tables()
        print(f"{Colors.GREEN}✅ Tablas creadas/verificadas{Colors.END}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Error creando tablas: {str(e)}{Colors.END}")
        return False


def start_server(dev_mode=True):
    """Inicia el servidor FastAPI"""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    
    print(f"""
{Colors.GREEN}{Colors.BOLD}🚀 Iniciando servidor...{Colors.END}
{Colors.BLUE}   URL: http://{host}:{port}
   Docs: http://{host}:{port}/docs
   ReDoc: http://{host}:{port}/redoc{Colors.END}
""")
    
    if dev_mode:
        # Modo desarrollo con hot-reload
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=["."],
            log_level="info"
        )
    else:
        # Modo producción
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=4,
            log_level="warning"
        )


def main():
    """Función principal"""
    print_banner()
    
    dev_mode = "--prod" not in sys.argv
    skip_checks = "--skip-checks" in sys.argv
    
    if dev_mode:
        print(f"{Colors.BLUE}📝 Modo: Desarrollo{Colors.END}")
    else:
        print(f"{Colors.GREEN}🏭 Modo: Producción{Colors.END}")
    
    print()
    
    if not skip_checks:
        if not check_env_file():
            print(f"\n{Colors.YELLOW}Configura el archivo .env y vuelve a ejecutar{Colors.END}")
            sys.exit(1)
        
        if not check_database_connection():
            print(f"\n{Colors.YELLOW}Soluciona los problemas de conexión y vuelve a ejecutar{Colors.END}")
            sys.exit(1)
        
        if not run_migrations():
            create_tables()
    
    print()
    
    try:
        start_server(dev_mode=dev_mode)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Servidor detenido{Colors.END}")


if __name__ == "__main__":
    main()
