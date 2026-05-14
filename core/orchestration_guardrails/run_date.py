from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


SGT_TIMEZONE = "Asia/Singapore"


def today_sgt() -> str:
    """
    Return today's date in Singapore time as YYYY-MM-DD.
    """
    return datetime.now(ZoneInfo(SGT_TIMEZONE)).date().isoformat()


def resolve_run_date_sgt(requested_run_date_sgt: str | None = None) -> str:
    """
    Resolve run_date_sgt safely.

    Rules:
    - If requested_run_date_sgt is provided and non-empty, use it.
    - Otherwise use today's date in Asia/Singapore.
    """
    if requested_run_date_sgt and str(requested_run_date_sgt).strip():
        return str(requested_run_date_sgt).strip()

    return today_sgt()
