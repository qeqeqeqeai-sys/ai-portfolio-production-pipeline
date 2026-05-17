from __future__ import annotations
import os, requests


def fetch_table_rows(table: str, run_date_sgt: str, theme_name: str) -> tuple[list[dict], str | None]:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return [], "missing_supabase_env"
    try:
        resp = requests.get(f"{url}/rest/v1/{table}", headers={"apikey": key, "Authorization": f"Bearer {key}"}, params={"select": "*", "run_date_sgt": f"eq.{run_date_sgt}", "theme_name": f"eq.{theme_name}", "limit": "500"}, timeout=30)
        if resp.status_code >= 400:
            return [], f"read_failed:{table}:{resp.status_code}"
        payload = resp.json()
        return ([x for x in payload if isinstance(x, dict)] if isinstance(payload, list) else []), None
    except Exception as exc:
        return [], f"read_exception:{table}:{type(exc).__name__}"


def fetch_table_rows_with_fallback(tables: list[str], run_date_sgt: str, theme_name: str) -> tuple[list[dict], dict]:
    attempted, selected = [], None
    warning = None
    for table in tables:
        attempted.append(table)
        rows, err = fetch_table_rows(table, run_date_sgt, theme_name)
        if err and err.startswith("missing_supabase_env"):
            return [], {"tables_attempted": attempted, "table_selected": None, "warning": err, "rows_read": 0}
        if not err:
            selected = table
            return rows, {"tables_attempted": attempted, "table_selected": selected, "warning": warning, "rows_read": len(rows)}
        warning = err
    return [], {"tables_attempted": attempted, "table_selected": None, "warning": warning, "rows_read": 0}


def write_audit_rows(rows: list[dict]) -> str:
    if not rows:
        return "skipped:no_rows"
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return "skipped:missing_supabase_env"
    try:
        resp = requests.post(f"{url}/rest/v1/tier3h_entity_resolution_audit", headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "return=minimal"}, json=rows, timeout=30)
        return "written" if resp.status_code < 400 else f"write_failed:{resp.status_code}"
    except Exception as exc:
        return f"write_exception:{type(exc).__name__}"
