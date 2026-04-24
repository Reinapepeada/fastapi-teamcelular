from __future__ import annotations

import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

ARGENTINA_TIME_ZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def configure_process_timezone() -> None:
    os.environ.setdefault("TZ", "America/Argentina/Buenos_Aires")
    if hasattr(time, "tzset"):
        try:
            time.tzset()
        except Exception:
            pass


def now_argentina_naive() -> datetime:
    return datetime.now(ARGENTINA_TIME_ZONE).replace(tzinfo=None)


def to_argentina_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=ARGENTINA_TIME_ZONE)

    return value.astimezone(ARGENTINA_TIME_ZONE)