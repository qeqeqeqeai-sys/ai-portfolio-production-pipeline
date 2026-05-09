"""
write_pipeline_failure_metrics.py

Writes FAILED GitHub Actions pipeline runs into Supabase.

Supports:
- Normal script/runtime failures
- Intentional validation gate failures
- Validation report ingestion from outputs/validation_report.json
- Runtime duration tracking
- Log capture
- GitHub Actions metadata
"""

import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests


try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

PIPELINE_TABLE = "production_pipeline_runs"

LOG_DIR = Path("logs")
OUTPUTS_DIR = Path("outputs")
VALIDATION_REPORT_PATH = OUTPUTS_DIR / "validation_report.json"


def now_sgt_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def read_text_file(path: Path, max_chars: int = 12000) -> Optional[str]:
    if not path.exists():
        return None

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[-max_chars:]
    except Exception:
        return None


def read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_validation_failure_summary(path: Path = VALIDATION_REPORT_PATH) -> str:
    data = read_json_file(path)

    if not data:
        return "Validation report not found."

    failed = [
        r for r in data.get("results", [])
        if not r.get("passed", True)
    ]

    top_failed = failed[:8]

    lines = [
        f"Validation status: {data.get('status')}",
        f"Warnings: {data.get('warning_count')}",
        f"Errors: {data.get('error_count')}",
        f"Hard fails: {data.get('hard_fail_count')}",
        "",
        "Failed checks:",
    ]

    if not top_failed:
        lines.append("- No failed validation checks found.")
    else:
        for r in top_failed:
            lines.append(
                f"- [{r.get('severity')}] {r.get('check_name')}: {r.get('message')}"
            )

    return "\n".join(lines)


def detect_failure_type(validation_report: Optional[Dict[str, Any]]) -> str:
    if validation_report and validation_report.get("status") == "FAILED":
        return "VALIDATION_GATE_FAILED"

    return "SCRIPT_RUNTIME_FAILED"


def collect_log_bundle(max_chars_per_file: int = 8000) -> Dict[str, Optional[str]]:
    log_files = [
        "01_signal_scoring.log",
        "02_portfolio_engine.log",
        "03_monitoring.log",
        "04_validation_gates.log",
        "05_pipeline_metrics.log",
        "06_pipeline_failure_metrics.log",
    ]

    logs = {}

    for file_name in log_files:
        path = LOG_DIR / file_name
        logs[file_name] = read_text_file(path, max_chars=max_chars_per_file)

    return logs


def find_last_available_log(logs: Dict[str, Optional[str]]) -> Optional[str]:
    for key in reversed(list(logs.keys())):
        if logs.get(key):
            return logs[key]
    return None


def build_failure_payload() -> Dict[str, Any]:
    validation_report = read_json_file(VALIDATION_REPORT_PATH)
    validation_summary_text = load_validation_failure_summary(VALIDATION_REPORT_PATH)

    logs = collect_log_bundle()
    last_log = find_last_available_log(logs)

    failure_type = detect_failure_type(validation_report)

    runtime_seconds = safe_float(os.getenv("PIPELINE_RUNTIME_SECONDS"))

    payload = {
        "run_date_sgt": datetime.now(ZoneInfo("Asia/Singapore")).date().isoformat(),
        "run_timestamp_sgt": now_sgt_iso(),
        "status": "FAILED",
        "failure_type": failure_type,
        "runtime_seconds": runtime_seconds,

        # GitHub Actions metadata
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_run_number": os.getenv("GITHUB_RUN_NUMBER"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_job": os.getenv("GITHUB_JOB"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_ref": os.getenv("GITHUB_REF"),
        "github_ref_name": os.getenv("GITHUB_REF_NAME"),
        "github_sha": os.getenv("GITHUB_SHA"),
        "github_actor": os.getenv("GITHUB_ACTOR"),

        # Validation fields
        "validation_status": validation_report.get("status") if validation_report else None,
        "validation_warning_count": validation_report.get("warning_count") if validation_report else None,
        "validation_error_count": validation_report.get("error_count") if validation_report else None,
        "validation_hard_fail_count": validation_report.get("hard_fail_count") if validation_report else None,
        "validation_should_fail_pipeline": validation_report.get("should_fail_pipeline") if validation_report else None,
        "validation_summary": validation_summary_text,
        "validation_report_json": validation_report,

        # Logs
        "error_log": last_log,
        "logs_json": logs,

        # Source marker
        "source": "GITHUB_ACTIONS_FAILURE_WRITER",
        "created_at": now_sgt_iso(),
    }

    return payload


def supabase_insert(table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if not SUPABASE_URL:
        raise RuntimeError("Missing SUPABASE_URL")

    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY")

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase insert failed: HTTP {response.status_code} - {response.text}"
        )

    try:
        return response.json()
    except Exception:
        return {"raw_response": response.text}


def write_local_failure_payload(payload: Dict[str, Any]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    path = OUTPUTS_DIR / "pipeline_failure_payload_latest.json"

    path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"[INFO] Local failure payload written to {path}")


def main() -> int:
    print("=" * 100)
    print("Writing pipeline failure metrics")
    print("=" * 100)

    try:
        payload = build_failure_payload()

        write_local_failure_payload(payload)

        result = supabase_insert(PIPELINE_TABLE, payload)

        print("[SUCCESS] Failure metrics written to Supabase.")
        print(json.dumps(result, indent=2, default=str))

        return 0

    except Exception as exc:
        print("[ERROR] Failed to write pipeline failure metrics.")
        print(str(exc))
        print(traceback.format_exc())

        fallback = {
            "status": "FAILED",
            "failure_type": "FAILURE_METRICS_WRITE_FAILED",
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "created_at": now_sgt_iso(),
        }

        try:
            write_local_failure_payload(fallback)
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
