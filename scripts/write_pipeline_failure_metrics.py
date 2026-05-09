"""
write_pipeline_failure_metrics.py

Schema-compatible failure metrics writer for production_pipeline_runs.

Works with current table columns only:

- run_timestamp_sgt
- run_date_sgt
- pipeline_name
- status
- runtime_seconds
- github_run_id
- github_workflow
- github_repository
- github_branch
- error_message
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


def now_sgt() -> datetime:
    return datetime.now(ZoneInfo("Asia/Singapore"))


def now_sgt_iso() -> str:
    return now_sgt().isoformat()


def today_sgt_iso() -> str:
    return now_sgt().date().isoformat()


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def read_text_file(path: Path, max_chars: int = 6000) -> Optional[str]:
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


def load_validation_failure_summary() -> str:
    data = read_json_file(VALIDATION_REPORT_PATH)

    if not data:
        return "Validation report not found."

    failed = [
        r for r in data.get("results", [])
        if not r.get("passed", True)
    ]

    lines = [
        "Failure type: VALIDATION_GATE_FAILED",
        f"Validation status: {data.get('status')}",
        f"Warnings: {data.get('warning_count')}",
        f"Errors: {data.get('error_count')}",
        f"Hard fails: {data.get('hard_fail_count')}",
        "",
        "Failed checks:",
    ]

    if not failed:
        lines.append("- No failed checks found.")
    else:
        for r in failed[:8]:
            lines.append(
                f"- [{r.get('severity')}] {r.get('check_name')}: {r.get('message')}"
            )

    return "\n".join(lines)


def detect_failure_type() -> str:
    validation_report = read_json_file(VALIDATION_REPORT_PATH)

    if validation_report and validation_report.get("status") == "FAILED":
        return "VALIDATION_GATE_FAILED"

    return "SCRIPT_RUNTIME_FAILED"


def collect_recent_logs(max_chars_per_file: int = 2500) -> str:
    log_files = [
        "01_signal_scoring.log",
        "02_portfolio_engine.log",
        "03_monitoring.log",
        "04_validation_gates.log",
        "05_pipeline_metrics.log",
        "06_pipeline_failure_metrics.log",
    ]

    sections = []

    for file_name in log_files:
        path = LOG_DIR / file_name
        text = read_text_file(path, max_chars=max_chars_per_file)

        if text:
            sections.append(
                f"\n--- {file_name} ---\n{text}"
            )

    if not sections:
        return "No log files found."

    return "\n".join(sections)


def truncate_error_message(message: str, max_chars: int = 12000) -> str:
    if len(message) <= max_chars:
        return message

    return message[-max_chars:]


def build_error_message() -> str:
    failure_type = detect_failure_type()

    if failure_type == "VALIDATION_GATE_FAILED":
        main_summary = load_validation_failure_summary()
    else:
        main_summary = "Failure type: SCRIPT_RUNTIME_FAILED"

    recent_logs = collect_recent_logs()

    message = f"""
AI Portfolio production pipeline failed.

{main_summary}

GitHub metadata:
- github_run_id: {os.getenv("GITHUB_RUN_ID")}
- github_workflow: {os.getenv("GITHUB_WORKFLOW")}
- github_repository: {os.getenv("GITHUB_REPOSITORY")}
- github_branch: {os.getenv("GITHUB_REF_NAME")}
- github_sha: {os.getenv("GITHUB_SHA")}

Recent logs:
{recent_logs}
""".strip()

    return truncate_error_message(message)


def build_failure_payload() -> Dict[str, Any]:
    runtime_seconds = safe_float(os.getenv("PIPELINE_RUNTIME_SECONDS"))

    payload = {
        "run_timestamp_sgt": now_sgt_iso(),
        "run_date_sgt": today_sgt_iso(),
        "pipeline_name": "AI_PORTFOLIO_PRODUCTION",
        "status": "FAILED",
        "runtime_seconds": runtime_seconds,

        # Existing GitHub metadata columns
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),

        # Existing error field
        "error_message": build_error_message(),
    }

    return payload


def write_local_failure_payload(payload: Dict[str, Any]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    path = OUTPUTS_DIR / "pipeline_failure_payload_latest.json"

    path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"[INFO] Local failure payload written to {path}")


def supabase_insert(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not SUPABASE_URL:
        raise RuntimeError("Missing SUPABASE_URL")

    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY")

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{PIPELINE_TABLE}"

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


def main() -> int:
    print("=" * 100)
    print("Writing pipeline failure metrics")
    print("=" * 100)

    try:
        payload = build_failure_payload()
        write_local_failure_payload(payload)

        result = supabase_insert(payload)

        print("[SUCCESS] Failure metrics written to Supabase.")
        print(json.dumps(result, indent=2, default=str))

        return 0

    except Exception as exc:
        print("[ERROR] Failed to write pipeline failure metrics.")
        print(str(exc))
        print(traceback.format_exc())

        fallback_payload = {
            "status": "FAILED",
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "created_at_sgt": now_sgt_iso(),
        }

        try:
            write_local_failure_payload(fallback_payload)
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
