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
RETRY_ATTEMPTS = int(os.getenv("DB_RETRY_ATTEMPTS", "30"))


def normalize_db_url(db_url: Optional[str]) -> Optional[str]:
    if not db_url:
        return None
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql://", 1)
    return db_url


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

    if not wait_for_db(database_url):
        print("ERROR: database unavailable; exiting")
        sys.exit(1)

    if not run_alembic():
        print("ERROR: Alembic migration failed; exiting")
        sys.exit(1)

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
