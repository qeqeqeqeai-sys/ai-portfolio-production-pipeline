from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def create_telemetry_snapshot(
    context_file: str,
    validation_summary_file: str,
    pipeline_status: str,
    runtime_seconds: int,
    output_file: str,
) -> None:

    context = load_json(context_file)
    validation = load_json(validation_summary_file)

    snapshot = {
        "workflow_name": context.get("workflow_name"),
        "github_run_id": context.get("github_run_id"),
        "run_mode": context.get("run_mode"),
        "theme_name": context.get("theme_name"),
        "requested_run_date_sgt": context.get("requested_run_date_sgt"),
        "resolved_run_date_sgt": context.get("resolved_run_date_sgt"),
        "pipeline_status": pipeline_status,
        "validation_status": validation.get("validation_status"),
        "warnings_count": validation.get("warnings_count", 0),
        "errors_count": validation.get("errors_count", 0),
        "hard_fail_count": validation.get("hard_fail_count", 0),
        "runtime_seconds": runtime_seconds,
        "created_at_utc": utc_now_iso(),
        "updated_at_utc": utc_now_iso(),
    }

    write_json(output_file, snapshot)
