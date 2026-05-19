from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .artifact_drift import artifact_drift
from .monitoring_context import stable_json_dumps
from .orchestration_drift import orchestration_drift
from .readiness_drift import readiness_drift
from .validation_drift import validation_drift


def _load_previous() -> dict[str, Any] | None:
    p = Path("logs/tier3h5_monitoring_context.json")
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def run_drift_diagnostics(current: dict[str, Any]) -> dict[str, Any]:
    previous = _load_previous()
    if previous is None:
        return {"monitoring_history_status": "insufficient_monitoring_history", "drift_categories": {}, "drift_checks_executed": 0, "drift_checks_with_findings": 0}
    categories = {
        "orchestration": orchestration_drift(current, previous),
        "artifact": artifact_drift(current, previous),
        "validation": validation_drift(current, previous),
        "readiness": readiness_drift(current, previous),
    }
    checks = sum(len(v) for v in categories.values()) + 3
    findings = sum(1 for v in categories.values() for b in v.values() if b)
    return {"monitoring_history_status": "history_available", "drift_categories": categories, "drift_checks_executed": checks, "drift_checks_with_findings": findings}


def write_diagnostics_files(payload: dict[str, Any]) -> None:
    files = {
        "logs/tier3h5_governance_drift_diagnostics.json": payload,
        "logs/tier3h5_orchestration_drift_summary.json": payload.get("drift_categories", {}).get("orchestration", {}),
        "logs/tier3h5_artifact_drift_summary.json": payload.get("drift_categories", {}).get("artifact", {}),
        "logs/tier3h5_validation_drift_summary.json": payload.get("drift_categories", {}).get("validation", {}),
        "logs/tier3h5_readiness_drift_summary.json": payload.get("drift_categories", {}).get("readiness", {}),
    }
    for path, body in files.items():
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(stable_json_dumps(body), encoding="utf-8")
