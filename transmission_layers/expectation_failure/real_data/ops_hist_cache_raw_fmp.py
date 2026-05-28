from __future__ import annotations

import json
import os
from datetime import date
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence


def build_cache_key(symbol: str, price_date: str, source: str = "fmp") -> str:
    return f"{str(source).strip().lower()}|{str(symbol).strip().upper()}|{str(price_date).strip()}"


def compute_payload_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(canonical.encode("utf-8")).hexdigest()


def normalize_fmp_historical_price_row(row: Mapping[str, Any], *, endpoint_family: str | None = None, source: str = "fmp") -> dict[str, Any] | None:
    symbol = str(row.get("symbol") or "").strip().upper()
    price_date = str(row.get("price_date") or row.get("date") or "").strip()
    if not symbol or not price_date:
        return None
    try:
        date.fromisoformat(price_date)
    except Exception:
        return None
    normalized = {
        "symbol": symbol,
        "price_date": price_date,
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": row.get("close"),
        "adj_close": row.get("adj_close", row.get("adjClose")),
        "volume": row.get("volume"),
        "source": source,
        "endpoint_family": endpoint_family or row.get("endpoint_family"),
        "payload_hash": compute_payload_hash(dict(row)),
    }
    return normalized


def _cache_enabled() -> bool:
    return str(os.getenv("OPS_HIST_RAW_CACHE_ENABLED", "false")).lower() == "true"


def _cache_write_enabled() -> bool:
    return str(os.getenv("OPS_HIST_RAW_CACHE_WRITE_ENABLED", "false")).lower() == "true"


def _build_client():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_KEY", "")
    if not (_cache_enabled() and url and key):
        return None
    try:
        from supabase import create_client
    except Exception:
        return None
    return create_client(url, key)


def read_cached_historical_prices(symbols: Sequence[str], requested_dates: Sequence[str], source: str = "fmp", client: Any | None = None) -> tuple[list[dict[str, Any]], int]:
    c = client or _build_client()
    if c is None:
        return [], 0
    safe_symbols = sorted({str(s).upper() for s in symbols if s})
    safe_dates = sorted({str(d) for d in requested_dates if d})
    if not safe_symbols or not safe_dates:
        return [], 0
    try:
        resp = c.table("raw_fmp_historical_prices").select("symbol,price_date,open,high,low,close,adj_close,volume,source,endpoint_family,payload_hash").in_("symbol", safe_symbols).in_("price_date", safe_dates).eq("source", source).execute()
        rows = resp.data if hasattr(resp, "data") else []
    except Exception:
        return [], 1
    out = []
    for row in rows or []:
        norm = normalize_fmp_historical_price_row(row, source=source)
        if norm is not None:
            out.append(norm)
    return out, 0


def identify_missing_symbol_dates(symbols: Sequence[str], requested_dates: Sequence[str], cached_rows: Iterable[Mapping[str, Any]], source: str = "fmp") -> dict[str, list[str]]:
    cached_keys = {build_cache_key(str(r.get("symbol", "")), str(r.get("price_date", "")), source=source) for r in cached_rows}
    missing: dict[str, list[str]] = {}
    for sym in sorted({str(s).upper() for s in symbols if s}):
        missing_dates = []
        for d in sorted({str(x) for x in requested_dates if x}):
            if build_cache_key(sym, d, source=source) not in cached_keys:
                missing_dates.append(d)
        if missing_dates:
            missing[sym] = missing_dates
    return missing


def write_raw_historical_prices(rows: Sequence[Mapping[str, Any]], *, client: Any | None = None, dry_run: bool = False) -> tuple[int, int]:
    result = summarize_write_result(rows, client=client, dry_run=dry_run)
    success_rows = result.get("write_success_rows")
    if success_rows is None:
        return int(result.get("write_attempted_rows", 0)), int(result.get("write_failed_rows", 0))
    return int(success_rows), int(result.get("write_failed_rows", 0))


def summarize_write_result(rows: Sequence[Mapping[str, Any]], *, client: Any | None = None, dry_run: bool = False) -> dict[str, Any]:
    if dry_run or not _cache_write_enabled():
        return {"write_attempted_rows": 0, "write_success_rows": 0, "write_failed_rows": 0, "write_status": "disabled", "write_confirmation_limited": False, "error_reason_counts": {}}
    c = client or _build_client()
    if c is None:
        return {"write_attempted_rows": 0, "write_success_rows": 0, "write_failed_rows": 0, "write_status": "client_unavailable", "write_confirmation_limited": False, "error_reason_counts": {"client_unavailable": 1}}
    payload = [r for r in (normalize_fmp_historical_price_row(row) for row in rows) if r is not None]
    attempted = len(payload)
    if attempted == 0:
        return {"write_attempted_rows": 0, "write_success_rows": 0, "write_failed_rows": 0, "write_status": "no_valid_rows", "write_confirmation_limited": False, "error_reason_counts": {}}
    try:
        resp = c.table("raw_fmp_historical_prices").upsert(payload, on_conflict="symbol,price_date,source").execute()
    except Exception as exc:
        reason = type(exc).__name__[:64]
        return {"write_attempted_rows": attempted, "write_success_rows": 0, "write_failed_rows": attempted, "write_status": "failed", "write_confirmation_limited": False, "error_reason_counts": {reason: 1}}
    data = getattr(resp, "data", None)
    if isinstance(data, list):
        success = len(data)
        failed = max(0, attempted - success)
        return {"write_attempted_rows": attempted, "write_success_rows": success, "write_failed_rows": failed, "write_status": "confirmed", "write_confirmation_limited": False, "error_reason_counts": {}}
    return {"write_attempted_rows": attempted, "write_success_rows": None, "write_failed_rows": 0, "write_status": "submitted_unconfirmed", "write_confirmation_limited": True, "error_reason_counts": {}}
