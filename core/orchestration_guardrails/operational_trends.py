from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


TREND_FILES = {
    "trend_summary": "platform_operational_trend_summary.json",
    "health_score": "platform_workflow_health_score.json",
    "recurring_warnings": "platform_recurring_warnings.json",
    "runtime_drift": "platform_runtime_drift_summary.json",
    "execution_consistency": "platform_execution_consistency.json",
}


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_json_file(path: Path, advisory_warnings: List[str], label: str) -> Dict[str, Any]:
    if not path.exists():
        advisory_warnings.append(f"missing input artifact: {label} ({path})")
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return _as_dict(json.load(f))
    except Exception as exc:
        advisory_warnings.append(f"malformed input artifact: {label} ({path}): {exc}")
        return {}


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _confidence(history_count: int, signal_count: int) -> str:
    if history_count < 2:
        return "insufficient_history"
    if signal_count <= 1:
        return "weak_signal"
    return "usable_trend"


def _analysis_window(days: int) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(1, days))
    return {
        "window_days": max(1, days),
        "start_utc": start.isoformat(),
        "end_utc": now.isoformat(),
    }


def _find_recurring_warnings(platform_validation: Dict[str, Any], platform_operational: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Tuple[str, int, str]] = []

    warnings_count = _to_int(platform_validation.get("warnings_count"))
    if warnings_count > 0:
        findings.append(("validation_warnings", warnings_count, "Validation warnings are repeatedly present; monitor rule calibration and noisy checks."))

    advisory_warnings = _as_dict(platform_operational.get("metadata")).get("advisory_warnings", [])
    if isinstance(advisory_warnings, list) and advisory_warnings:
        findings.append(("advisory_warnings", len(advisory_warnings), "Operational advisory warnings appear recurrently; review missing or malformed context artifacts."))

    errors_count = _to_int(platform_validation.get("errors_count")) + _to_int(platform_validation.get("hard_fail_count"))
    if errors_count > 0:
        findings.append(("validation_error_like_signals", errors_count, "Error-like validation signals were detected; investigate repeated integrity issues."))

    findings.sort(key=lambda x: x[0])
    return [
        {
            "pattern": p,
            "occurrences": c,
            "recommendation": r,
        }
        for p, c, r in findings
    ]


def analyze_operational_trends(logs_dir: str = "logs", analysis_window_days: int = 14) -> Dict[str, Any]:
    advisory_warnings: List[str] = []
    logs_path = Path(logs_dir)

    files = {
        "execution_context": logs_path / "execution_context.json",
        "validation_summary": logs_path / "validation_summary.json",
        "telemetry_snapshot": logs_path / "telemetry_context_snapshot.json",
        "artifact_manifest": logs_path / "context_artifact_manifest.json",
        "platform_pipeline_index": logs_path / "platform_pipeline_index.json",
        "platform_runtime_summary": logs_path / "platform_runtime_summary.json",
        "platform_validation_summary": logs_path / "platform_validation_summary.json",
        "platform_operational_summary": logs_path / "platform_operational_summary.json",
    }

    loaded = {name: _load_json_file(path, advisory_warnings, name) for name, path in files.items()}

    context = loaded["execution_context"]
    platform_runtime = loaded["platform_runtime_summary"]
    platform_validation = loaded["platform_validation_summary"]
    platform_operational = loaded["platform_operational_summary"]

    runtime_seconds = _to_int(platform_runtime.get("runtime_seconds"), _to_int(loaded["telemetry_snapshot"].get("runtime_seconds")))
    validation_warnings = _to_int(platform_validation.get("warnings_count"), _to_int(loaded["validation_summary"].get("warnings_count")))
    validation_errors = _to_int(platform_validation.get("errors_count"), _to_int(loaded["validation_summary"].get("errors_count")))
    hard_fails = _to_int(platform_validation.get("hard_fail_count"), _to_int(loaded["validation_summary"].get("hard_fail_count")))

    missing_artifacts = sum(1 for payload in loaded.values() if not payload)
    history_count = len(loaded) - missing_artifacts
    signal_count = sum(1 for val in [validation_warnings, validation_errors, hard_fails] if val > 0)

    health_score = max(0, 100 - (validation_warnings * 3) - (validation_errors * 8) - (hard_fails * 10) - (missing_artifacts * 4))
    if runtime_seconds > 7200:
        health_score = max(0, health_score - 8)

    trend_confidence = _confidence(history_count=history_count, signal_count=signal_count)
    drift_state = "stable"
    drift_reason = "No significant runtime drift signal observed from available artifacts."
    if runtime_seconds <= 0:
        drift_state = "insufficient_data"
        drift_reason = "Runtime seconds are unavailable or non-positive, so drift cannot be inferred confidently."
    elif runtime_seconds > 5400:
        drift_state = "high_runtime_drift"
        drift_reason = "Runtime appears materially elevated against lightweight advisory threshold."
    elif runtime_seconds > 1800:
        drift_state = "moderate_runtime_drift"
        drift_reason = "Runtime is above nominal advisory threshold; monitor for sustained elevation."

    recurring_warning_patterns = _find_recurring_warnings(platform_validation, platform_operational)

    generated_at_utc = _now_iso_utc()
    window = _analysis_window(analysis_window_days)

    common_meta = {
        "generated_at_utc": generated_at_utc,
        "analysis_window": window,
        "workflow_name": context.get("workflow_name", platform_runtime.get("workflow_name", "")),
        "github_run_id": context.get("github_run_id", platform_runtime.get("github_run_id", "")),
        "theme_name": context.get("theme_name", platform_validation.get("theme_name", "")),
        "advisory_warnings": sorted(advisory_warnings),
        "tier": "3F",
        "advisory_only": True,
    }

    trend_summary = {
        **common_meta,
        "trend_confidence": trend_confidence,
        "signals": {
            "runtime_seconds": runtime_seconds,
            "validation_warnings": validation_warnings,
            "validation_errors": validation_errors,
            "hard_fail_count": hard_fails,
            "missing_or_unreadable_inputs": missing_artifacts,
        },
        "recommendations": [
            "Review recurring warnings and malformed artifacts before broadening enforcement scope.",
            "Track runtime movement over multiple runs to strengthen trend confidence.",
        ],
    }

    workflow_health = {
        **common_meta,
        "workflow_health_score": health_score,
        "confidence": trend_confidence,
        "score_reasons": [
            f"validation_warnings={validation_warnings}",
            f"validation_errors={validation_errors}",
            f"hard_fail_count={hard_fails}",
            f"missing_or_unreadable_inputs={missing_artifacts}",
            f"runtime_seconds={runtime_seconds}",
        ],
        "recommendation": "Use this score for advisory trend tracking only; do not gate workflow execution.",
    }

    recurring_warnings = {
        **common_meta,
        "trend_confidence": trend_confidence,
        "patterns": recurring_warning_patterns,
        "recommendations": [
            "Reduce repeated warning classes by hardening artifact generation consistency.",
            "Prefer incremental correction of noisy checks instead of workflow controls.",
        ],
    }

    runtime_drift = {
        **common_meta,
        "trend_confidence": trend_confidence,
        "runtime_drift_state": drift_state,
        "runtime_seconds": runtime_seconds,
        "reason": drift_reason,
        "recommendation": "Investigate sustained runtime increases; keep Tier 3F advisory and non-blocking.",
    }

    execution_consistency = {
        **common_meta,
        "trend_confidence": trend_confidence,
        "consistency_signals": {
            "missing_or_unreadable_inputs": missing_artifacts,
            "partial_success_pattern_detected": missing_artifacts > 0,
            "validation_status": platform_validation.get("validation_status", loaded["validation_summary"].get("validation_status", "unknown")),
            "operational_status": platform_operational.get("operational_status", "unknown"),
        },
        "recommendations": [
            "Address repeated missing-artifact patterns to improve execution consistency confidence.",
            "Preserve always-on artifact uploads for trend continuity.",
        ],
    }

    outputs = {
        TREND_FILES["trend_summary"]: trend_summary,
        TREND_FILES["health_score"]: workflow_health,
        TREND_FILES["recurring_warnings"]: recurring_warnings,
        TREND_FILES["runtime_drift"]: runtime_drift,
        TREND_FILES["execution_consistency"]: execution_consistency,
    }

    logs_path.mkdir(parents=True, exist_ok=True)
    for filename, payload in outputs.items():
        with (logs_path / filename).open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    return {
        "files_written": [str(logs_path / name) for name in sorted(outputs.keys())],
        "trend_confidence": trend_confidence,
        "health_score": health_score,
    }
