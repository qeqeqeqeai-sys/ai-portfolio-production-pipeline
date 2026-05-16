#!/usr/bin/env python3
"""Tier 3G advisory persistence writer for workflow observability history.

Purpose:
- Persist operational telemetry snapshots into Supabase.
- Establish historical operational intelligence foundation.
- Remain advisory/non-blocking during initial rollout.

Behavior:
- Missing observability files are tolerated.
- Persistence failures are surfaced as warnings.
- Intended for gradual integration into workflow governance.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


SGT = ZoneInfo("Asia/Singapore")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

TABLE_NAME = "platform_workflow_observability_history"
LOGS_DIR = Path(os.getenv("LOGS_DIR", "logs"))


def log(message: str) -> None:
    now = datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now} SGT] {message}", flush=True)


def read_json(filename: str) -> dict | None:
    path = LOGS_DIR / filename

    if not path.exists():
        log(f"[WARNING] Missing observability artifact: {path}")
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"[WARNING] Failed reading {path}: {exc}")
        return None

    if not isinstance(payload, dict):
        log(f"[WARNING] Non-object JSON payload in {path}")
        return None

    return payload


def _clean_str(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def resolve_run_date_sgt(execution_context: dict | None) -> str:
    env_value = _clean_str(os.getenv("RUN_DATE_SGT"))
    if env_value:
        log("Resolved run_date_sgt from environment variable RUN_DATE_SGT.")
        return env_value

    context = execution_context if isinstance(execution_context, dict) else {}
    file_value = _clean_str(
        context.get("resolved_run_date_sgt") or context.get("run_date_sgt")
    )
    if file_value:
        log("Resolved run_date_sgt from logs/execution_context.json.")
        return file_value

    try:
        fallback = datetime.now(ZoneInfo("Asia/Singapore")).date().isoformat()
        log("Resolved run_date_sgt from Asia/Singapore current date fallback.")
        return fallback
    except Exception:
        fallback = datetime.now(timezone.utc).date().isoformat()
        log("Resolved run_date_sgt from UTC current date fallback.")
        return fallback


def require_env() -> bool:
    missing = []

    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")

    if not SUPABASE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    if missing:
        log(f"[WARNING] Missing environment variables: {missing}")
        return False

    return True


def build_payload() -> dict:
    execution_context = read_json("execution_context.json")
    validation_summary = read_json("validation_summary.json")
    telemetry_snapshot = read_json("telemetry_context_snapshot.json")
    operational_summary = read_json("platform_operational_summary.json")
    trend_summary = read_json("platform_operational_trend_summary.json")
    workflow_health = read_json("platform_workflow_health_score.json")

    validation_context = validation_summary or {}
    telemetry_context = telemetry_snapshot or {}
    trend_context = trend_summary or {}
    run_date_sgt = resolve_run_date_sgt(execution_context)

    return {
        "run_date_sgt": run_date_sgt,
        "workflow_name": os.getenv("GITHUB_WORKFLOW"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "branch_name": os.getenv("GITHUB_REF_NAME"),
        "run_mode": os.getenv("GITHUB_EVENT_NAME"),
        "theme_name": os.getenv("THEME_NAME"),
        "pipeline_status": telemetry_context.get("pipeline_status"),
        "validation_status": validation_context.get("validation_status"),
        "runtime_seconds": telemetry_context.get("runtime_seconds"),
        "warnings_count": validation_context.get("warnings_count"),
        "errors_count": validation_context.get("errors_count"),
        "hard_fail_count": validation_context.get("hard_fail_count"),
        "health_score": trend_context.get("health_score"),
        "trend_regime": trend_context.get("trend_regime"),
        "runtime_drift_regime": trend_context.get("runtime_drift_regime"),
        "execution_consistency": trend_context.get("execution_consistency"),
        "execution_context": execution_context,
        "validation_summary": validation_summary,
        "telemetry_context_snapshot": telemetry_snapshot,
        "platform_operational_summary": operational_summary,
        "platform_operational_trend_summary": trend_summary,
        "platform_workflow_health_score": workflow_health,
    }


def persist(payload: dict) -> None:
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        timeout=60,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed writing observability history: "
            f"{response.status_code} - {response.text}"
        )


def main() -> int:
    log("Starting Tier 3G observability persistence writer...")

    if not require_env():
        log("[WARNING] Advisory persistence skipped.")
        return 0

    payload = build_payload()

    try:
        persist(payload)
    except Exception as exc:
        log(f"[WARNING] Advisory persistence failed: {exc}")
        return 0

    log("[DONE] Tier 3G observability history persisted successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
