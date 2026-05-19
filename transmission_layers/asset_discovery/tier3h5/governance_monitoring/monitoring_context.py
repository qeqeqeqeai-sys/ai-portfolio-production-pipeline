from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PHASE5A_INPUTS: tuple[str, ...] = (
    "logs/tier3h5_orchestration_summary.json",
    "logs/tier3h5_orchestration_runtime_context.json",
    "logs/tier3h5_orchestration_guardrails.json",
    "logs/tier3h5_artifact_coordination_summary.json",
    "logs/tier3h5_upload_coordination_summary.json",
    "logs/tier3h5_phase5a_orchestration_summary.json",
)


def stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": "))


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_value(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return sorted((_normalize_value(v) for v in value), key=lambda x: stable_json_dumps(x))
    if isinstance(value, bool) or value is None:
        return value
    return value


def load_monitoring_context() -> dict[str, Any]:
    context: dict[str, Any] = {"inputs": {}, "missing_inputs": []}
    for path in PHASE5A_INPUTS:
        p = Path(path)
        if not p.exists():
            context["missing_inputs"].append(path)
            continue
        context["inputs"][path] = _normalize_value(json.loads(p.read_text(encoding="utf-8")))
    context["loaded_input_count"] = len(context["inputs"])
    context["missing_input_count"] = len(context["missing_inputs"])
    return context


def write_monitoring_context(payload: dict[str, Any]) -> None:
    out = Path("logs/tier3h5_monitoring_context.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(stable_json_dumps(payload), encoding="utf-8")
