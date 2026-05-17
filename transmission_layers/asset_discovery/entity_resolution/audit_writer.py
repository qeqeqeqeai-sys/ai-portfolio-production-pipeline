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
    warnings: list[str] = []
    for table in tables:
        attempted.append(table)
        rows, err = fetch_table_rows(table, run_date_sgt, theme_name)
        if err and err.startswith("missing_supabase_env"):
            return [], {"tables_attempted": attempted, "table_selected": None, "warning": err, "warnings": [err], "rows_read": 0}
        if not err:
            selected = table
            return rows, {"tables_attempted": attempted, "table_selected": selected, "warning": warning, "warnings": warnings, "rows_read": len(rows)}
        warning = err
        warnings.append(err)
    return [], {"tables_attempted": attempted, "table_selected": None, "warning": warning, "warnings": warnings, "rows_read": 0}


def write_audit_rows(rows: list[dict]) -> dict:
    if not rows:
        return {"status": "skipped:no_rows"}
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return {"status": "skipped:missing_supabase_env"}
    try:
        resp = requests.post(f"{url}/rest/v1/tier3h_entity_resolution_audit", headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "return=minimal"}, json=rows, timeout=30)
        if resp.status_code < 400:
            return {"status": "written"}
        body = {}
        try:
            body = resp.json()
        except Exception:
            body = {"message": (resp.text or "")[:400]}
        return {
            "status": f"write_failed:{resp.status_code}",
            "write_error_code": body.get("code"),
            "write_error_message": body.get("message"),
            "write_error_details": body.get("details"),
            "write_error_hint": body.get("hint"),
        }
    except Exception as exc:
        return {"status": f"write_exception:{type(exc).__name__}"}


def write_evidence_rows(rows: list[dict]) -> dict:
    if not rows:
        return {"status": "skipped:no_rows", "rows_written": 0}
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return {"status": "skipped:missing_supabase_env", "rows_written": 0}
    payload = [{k: v for k, v in row.items() if k in EVIDENCE_COLUMNS} for row in rows]
    try:
        resp = requests.post(
            f"{url}/rest/v1/{EVIDENCE_TABLE_NAME}",
            headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "return=minimal"},
            json=payload,
            timeout=30,
        )
        if resp.status_code < 400:
            return {"status": "written", "rows_written": len(payload)}
        return {"status": f"write_failed:{resp.status_code}", "rows_written": 0}
    except Exception as exc:
        return {"status": f"write_exception:{type(exc).__name__}", "rows_written": 0}
EVIDENCE_TABLE_NAME = "tier3h_dynamic_entity_evidence"
EVIDENCE_COLUMNS = {
    "run_date_sgt", "workflow_run_id", "theme_name", "candidate_id", "candidate_asset_id", "candidate_name",
    "evidence_text", "source_url", "source_title", "source_domain", "evidence_type", "evidence_rank",
    "evidence_confidence", "extracted_ticker", "extracted_exchange", "extraction_method",
    "extraction_confidence", "extraction_notes", "raw_evidence",
}
