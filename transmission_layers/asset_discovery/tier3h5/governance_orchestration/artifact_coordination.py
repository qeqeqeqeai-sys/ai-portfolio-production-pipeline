from __future__ import annotations

from pathlib import Path
from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import write_stable_json

ARTIFACT_COORDINATION_PATH = Path("logs/tier3h5_artifact_coordination_summary.json")


def emit_artifact_coordination(stage_registry: list[dict[str, Any]]) -> dict[str, Any]:
    inventory = []
    for stage in stage_registry:
        for path in stage["expected_artifacts"]:
            inventory.append({"stage_name": stage["stage_name"], "artifact_path": path, "exists": Path(path).exists(), "required": stage["required"]})
    payload = {
        "artifact_inventory": inventory,
        "artifact_inventory_count": len(inventory),
        "required_artifact_count": sum(1 for i in inventory if i["required"]),
        "ready_artifact_count": sum(1 for i in inventory if i["exists"]),
    }
    write_stable_json(ARTIFACT_COORDINATION_PATH, payload)
    return payload
