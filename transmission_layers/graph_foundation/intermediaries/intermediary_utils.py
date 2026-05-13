"""Supabase REST helpers for graph intermediary formation."""
from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote

import requests


class SupabaseClient:
    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        self.url = (url or os.getenv("SUPABASE_URL") or "").rstrip("/")
        self.key = key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""
        if not self.url or not self.key:
            raise RuntimeError("Missing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY")
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = requests.request(method, f"{self.url}/rest/v1/{path}", headers=self.headers, timeout=40, **kwargs)
                if response.status_code in {429, 500, 502, 503, 504}:
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                if not response.text:
                    return None
                return response.json()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(2 ** attempt)
        raise RuntimeError(f"Supabase request failed: {method} {path}: {last_error}")

    def select(self, table: str, query: str = "", limit: int = 1000) -> list[dict[str, Any]]:
        sep = "&" if query else ""
        path = f"{table}?{query}{sep}limit={limit}"
        return self._request("GET", path) or []

    def upsert(self, table: str, rows: list[dict[str, Any]], on_conflict: str, chunk_size: int = 500) -> int:
        if not rows:
            return 0
        total = 0
        conflict = quote(on_conflict, safe=",")
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            path = f"{table}?on_conflict={conflict}"
            headers = {**self.headers, "Prefer": "resolution=merge-duplicates,return=representation"}
            out = self._request("POST", path, json=chunk, headers=headers)
            total += len(out or chunk)
        return total


def today_sgt_iso() -> str:
    import datetime as dt
    from zoneinfo import ZoneInfo
    return dt.datetime.now(ZoneInfo("Asia/Singapore")).date().isoformat()
