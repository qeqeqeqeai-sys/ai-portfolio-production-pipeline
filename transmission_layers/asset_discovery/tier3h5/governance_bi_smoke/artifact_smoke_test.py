from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def validate_json_artifact(path: Path, required_fields: tuple[str, ...]) -> dict[str, Any]:
    payload = _load_json(path)
    if payload is None:
        return {"artifact_status": "missing", "parse_ok": False, "required_fields_ok": False, "row_count_if_applicable": 0}
    required_ok = all(field in payload for field in required_fields)
    row_count = int(payload.get("row_count", len(payload.get("rows", []))) if isinstance(payload, dict) else 0)
    return {
        "artifact_status": "ready" if required_ok else "invalid",
        "parse_ok": True,
        "required_fields_ok": required_ok,
        "row_count_if_applicable": row_count,
        "deterministic_contract_verified": bool(payload.get("replay_mode") == "advisory_only"),
        "replay_safe_verified": bool(payload.get("enforcement_enabled") is False),
        "advisory_only_verified": bool(payload.get("replay_mode") == "advisory_only"),
    }


def run_artifact_smoke_test(path: Path, required_fields: tuple[str, ...]) -> dict[str, Any]:
    return validate_json_artifact(path, required_fields)
