from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PHASE5B_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("logs/tier3h5_monitoring_context.json", "monitoring_context.json"),
    ("logs/tier3h5_governance_drift_diagnostics.json", "governance_drift_diagnostics.json"),
    ("logs/tier3h5_orchestration_drift_summary.json", "orchestration_drift_summary.json"),
    ("logs/tier3h5_artifact_drift_summary.json", "artifact_drift_summary.json"),
    ("logs/tier3h5_validation_drift_summary.json", "validation_drift_summary.json"),
    ("logs/tier3h5_readiness_drift_summary.json", "readiness_drift_summary.json"),
    ("logs/tier3h5_phase5b_monitoring_summary.json", "monitoring_summary.json"),
)


def stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": "))


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): normalize(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return sorted((normalize(v) for v in value), key=stable_json_dumps)
    if value is None or isinstance(value, bool):
        return value
    return value


def load_phase5b_monitoring_context() -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    missing: list[str] = []
    for source, target_name in PHASE5B_ARTIFACTS:
        p = Path(source)
        if not p.exists():
            missing.append(source)
            continue
        loaded[target_name] = normalize(json.loads(p.read_text(encoding="utf-8")))
    return {
        "loaded_artifacts": loaded,
        "missing_artifacts": missing,
        "loaded_artifact_count": len(loaded),
        "missing_artifact_count": len(missing),
    }
