from __future__ import annotations

from dataclasses import dataclass
import os


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value is not None else default


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def env_csv(name: str, default: str = "*") -> list[str]:
    raw = env_str(name, default=default)
    if raw == "*":
        return ["*"]
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    log_level: str
    allowed_origins: list[str]
    cors_allow_credentials: bool
    run_migrations_on_startup: bool
    leads_whatsapp_number: str
    leads_dedupe_window_seconds: int
    leads_rate_limit_requests: int
    leads_rate_limit_window_seconds: int


def get_settings() -> Settings:
    environment = env_str("ENV", default="development")
    allowed_origins = env_csv("ALLOWED_ORIGINS", default="*")
    cors_allow_credentials = env_bool(
        "CORS_ALLOW_CREDENTIALS",
        default=False if allowed_origins == ["*"] else True,
    )
    return Settings(
        environment=environment,
        log_level=env_str("LOG_LEVEL", default="INFO").upper(),
        allowed_origins=allowed_origins,
        cors_allow_credentials=cors_allow_credentials,
        run_migrations_on_startup=env_bool("RUN_MIGRATIONS_ON_STARTUP", default=False),
        leads_whatsapp_number=env_str("LEADS_WHATSAPP_NUMBER", default=""),
        leads_dedupe_window_seconds=env_int("LEADS_DEDUPE_WINDOW_SECONDS", default=600),
        leads_rate_limit_requests=env_int("LEADS_RATE_LIMIT_REQUESTS", default=30),
        leads_rate_limit_window_seconds=env_int("LEADS_RATE_LIMIT_WINDOW_SECONDS", default=60),
    )
