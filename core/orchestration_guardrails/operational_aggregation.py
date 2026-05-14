from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def maybe_load_json(path: str | Path | None, advisory_warnings: List[str], label: str) -> Optional[Dict[str, Any]]:
    if not path:
        advisory_warnings.append(f"{label} path not provided")
        return None

    candidate = Path(path)
    if not candidate.exists():
        advisory_warnings.append(f"{label} missing: {candidate}")
        return None

    try:
        return load_json(candidate)
    except Exception as exc:
        advisory_warnings.append(f"{label} unreadable: {candidate} ({exc})")
        return None


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


def aggregate_operational_summary(
    context_file: str,
    validation_summary_file: str,
    telemetry_snapshot_file: str,
    artifact_manifest_file: str,
    output_dir: str,
) -> Dict[str, Any]:
    advisory_warnings: List[str] = []

    context = load_json(context_file)
    validation = maybe_load_json(validation_summary_file, advisory_warnings, "validation_summary")
    telemetry = maybe_load_json(telemetry_snapshot_file, advisory_warnings, "telemetry_snapshot")
    manifest = maybe_load_json(artifact_manifest_file, advisory_warnings, "artifact_manifest")

    workflow_name = _to_str(context.get("workflow_name"))
    github_run_id = _to_str(context.get("github_run_id"))
    theme_name = _to_str(context.get("theme_name"))
    run_date_sgt = _to_str(context.get("resolved_run_date_sgt"))

    pipeline_status = _to_str((telemetry or {}).get("pipeline_status")) or _to_str(context.get("status"))
    validation_status = _to_str((validation or {}).get("validation_status"))
    runtime_seconds = _to_int((telemetry or {}).get("runtime_seconds"), default=0)

    warnings_count = _to_int((validation or {}).get("warnings_count"), default=0)
    errors_count = _to_int((validation or {}).get("errors_count"), default=0)
    hard_fail_count = _to_int((validation or {}).get("hard_fail_count"), default=0)
    consistency_status = _to_str((validation or {}).get("consistency_status"))

    if pipeline_status != "SUCCESS" or errors_count > 0 or hard_fail_count > 0:
        operational_status = "failed"
    elif warnings_count > 0 or advisory_warnings:
        operational_status = "warning"
    elif pipeline_status == "SUCCESS" and validation_status == "passed" and hard_fail_count == 0:
        operational_status = "healthy"
    else:
        operational_status = "warning"

    generated_at_utc = utc_now_iso()
    output_base = Path(output_dir)

    platform_pipeline_index = {
        "workflow_name": workflow_name,
        "github_run_id": github_run_id,
        "theme_name": theme_name,
        "run_date_sgt": run_date_sgt,
        "pipeline_status": pipeline_status,
        "validation_status": validation_status,
        "runtime_seconds": runtime_seconds,
        "artifact_manifest_file": artifact_manifest_file,
        "generated_at_utc": generated_at_utc,
        "metadata": {"advisory_warnings": advisory_warnings},
    }

    platform_runtime_summary = {
        "workflow_name": workflow_name,
        "github_run_id": github_run_id,
        "run_date_sgt": run_date_sgt,
        "runtime_seconds": runtime_seconds,
        "pipeline_status": pipeline_status,
        "created_at_utc": generated_at_utc,
    }

    platform_validation_summary = {
        "workflow_name": workflow_name,
        "github_run_id": github_run_id,
        "theme_name": theme_name,
        "run_date_sgt": run_date_sgt,
        "validation_status": validation_status,
        "warnings_count": warnings_count,
        "errors_count": errors_count,
        "hard_fail_count": hard_fail_count,
        "consistency_status": consistency_status,
        "created_at_utc": generated_at_utc,
    }

    platform_operational_summary = {
        "workflow_name": workflow_name,
        "github_run_id": github_run_id,
        "theme_name": theme_name,
        "run_date_sgt": run_date_sgt,
        "pipeline_status": pipeline_status,
        "validation_status": validation_status,
        "operational_status": operational_status,
        "runtime_seconds": runtime_seconds,
        "warnings_count": warnings_count,
        "errors_count": errors_count,
        "hard_fail_count": hard_fail_count,
        "generated_at_utc": generated_at_utc,
        "metadata": {"advisory_warnings": advisory_warnings},
    }

    files = {
        "platform_pipeline_index.json": platform_pipeline_index,
        "platform_runtime_summary.json": platform_runtime_summary,
        "platform_validation_summary.json": platform_validation_summary,
        "platform_operational_summary.json": platform_operational_summary,
    }

    for filename, payload in files.items():
        write_json(output_base / filename, payload)

    return {
        "files_written": [str(output_base / filename) for filename in files],
        "operational_status": operational_status,
        "warnings_count": warnings_count + len(advisory_warnings),
        "artifact_manifest_present": manifest is not None,
    }
