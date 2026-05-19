from __future__ import annotations

from pathlib import Path
from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import write_stable_json

UPLOAD_COORDINATION_PATH = Path("logs/tier3h5_upload_coordination_summary.json")


def emit_upload_coordination(artifact_summary: dict[str, Any]) -> dict[str, Any]:
    inv = artifact_summary["artifact_inventory"]
    payload = {
        "eligible_artifacts": [i["artifact_path"] for i in inv if i["exists"]],
        "optional_artifacts_skipped": [i["artifact_path"] for i in inv if (not i["exists"] and not i["required"])],
        "required_artifacts_missing": [i["artifact_path"] for i in inv if (not i["exists"] and i["required"])],
        "upload_eligibility_status": "eligible" if all(i["exists"] or not i["required"] for i in inv) else "partial_orchestration_available",
    }
    write_stable_json(UPLOAD_COORDINATION_PATH, payload)
    return payload
