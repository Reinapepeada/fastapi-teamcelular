#!/usr/bin/env python3
"""Entrypoint for Docker/Railway: wait for DB, run Alembic migrations, then start app.

This script attempts to connect to the database, retries until available,
runs `alembic upgrade head`, then replaces the process with the Uvicorn server.
"""
import os
import sys
import time
import subprocess
from typing import Optional

RETRY_INTERVAL = float(os.getenv("DB_RETRY_INTERVAL", "2"))
# Increase default attempts to 60 so slow DBs get more time to start in CI/PAAS
RETRY_ATTEMPTS = int(os.getenv("DB_RETRY_ATTEMPTS", "60"))


def normalize_db_url(db_url: Optional[str]) -> Optional[str]:
    if not db_url:
        return None
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql://", 1)
    return db_url


def mask_db_url(db_url: Optional[str]) -> str:
    """Return a masked version of the DB URL (no password shown)."""
    if not db_url:
        return "(none)"
    try:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(db_url)
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc += f":{parsed.port}"
        # include username, but mask password
        user = parsed.username
        if user:
            netloc = f"{user}@{netloc}"
        return urlunparse((parsed.scheme, netloc, parsed.path or "", "", "", ""))
    except Exception:
        return "(masked)"


def wait_for_db(database_url: Optional[str]) -> bool:
    from sqlalchemy import create_engine, text
    if not database_url:
        print("ERROR: DATABASE_URL not set; cannot wait for DB.")
        return False

    engine = create_engine(database_url, pool_pre_ping=True)

    attempt = 0
    while attempt < RETRY_ATTEMPTS:
        try:
            with engine.connect() as conn:
                # Use SQLAlchemy text() to make the SQL string executable
                conn.execute(text("SELECT 1"))
            print("Database is available")
            return True
        except Exception as e:
            attempt += 1
            print(f"Waiting for database (attempt {attempt}/{RETRY_ATTEMPTS})...: {e}")
            time.sleep(RETRY_INTERVAL)

    print("Timed out waiting for database")
    return False


def run_alembic():
    print("Running alembic upgrade head...")
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        print("Alembic migrations applied")
        # Set env var to signal migrations are done
        os.environ["ALEMBIC_RUN"] = "1"
        return True
    except subprocess.CalledProcessError as e:
        print(f"Alembic failed: {e}")
        return False


def main():
    # Load environment vars from .env if present
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass

    database_url = normalize_db_url(os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL"))

    print(f"DB wait settings: attempts={RETRY_ATTEMPTS}, interval={RETRY_INTERVAL}s")
    if not wait_for_db(database_url):
        print("ERROR: database unavailable; exiting")
        sys.exit(1)

    if not run_alembic():
        print("ERROR: Alembic migration failed; exiting")
        sys.exit(1)

    # After migrations, run diagnostics (alembic_version, enum and table checks)
    try:
        from sqlalchemy import create_engine, text
        print("--- Post-migration DB diagnostics ---")
        db_engine = create_engine(database_url, pool_pre_ping=True)
        with db_engine.connect() as conn:
            # Which DB did we connect to? (masked)
            print("Connected to:", mask_db_url(database_url))
            try:
                res = conn.execute(text("SELECT version_num FROM alembic_version;"))
                rows = [r[0] for r in res.fetchall()]
                print("Alembic version(s):", rows)
            except Exception as e:
                print("Alembic version table not found or error:", e)

            try:
                adminrole = conn.execute(text("SELECT typname FROM pg_type WHERE typname = 'adminrole';")).scalar()
                print("Enum 'adminrole' exists:", bool(adminrole))
            except Exception as e:
                print("Could not query pg_type for adminrole:", e)

            try:
                admin_table = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'admin';")).scalar()
                print("Table 'admin' exists:", bool(admin_table))
            except Exception as e:
                print("Could not query information_schema.tables:", e)

            # Optional: print counts for key tables if POST_MIGRATION_DIAG is set
            try:
                if os.getenv("POST_MIGRATION_DIAG", "0") == "1":
                    tables_to_check = ["admin", "product", "productvariant", "productimage"]
                    for t in tables_to_check:
                        try:
                            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t};")).scalar()
                            print(f"Table {t} count: {cnt}")
                        except Exception as e:
                            print(f"Could not count table {t}:", e)
            except Exception as e:
                print("Error running table counts diag:", e)

        print("--- End diagnostics ---")
    except Exception as e:
        print("Error running post-migration diagnostics:", e)

    # Exec uvicorn (replace process). If user passed command args, use them.
    cmd = [
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        os.getenv("PORT", "8000"),
    ]

    # Allow overriding via CMD/args
    if len(sys.argv) > 1:
        cmd = sys.argv[1:]

    print("Starting server with:", " ".join(cmd))
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    main()
