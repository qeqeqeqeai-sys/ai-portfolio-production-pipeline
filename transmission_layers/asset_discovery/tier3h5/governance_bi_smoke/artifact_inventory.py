from __future__ import annotations

from pathlib import Path
from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import LOG_DIR
from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import write_stable_json

from .artifact_smoke_test import run_artifact_smoke_test

ARTIFACT_INVENTORY_PATH = LOG_DIR / "tier3h5_bi_artifact_inventory.json"


def build_artifact_inventory(artifact_specs: list[dict[str, Any]]) -> dict[str, Any]:
    inventory = []
    for spec in artifact_specs:
        path = Path(spec["path"])
        result = run_artifact_smoke_test(path, tuple(spec.get("required_fields", ())))
        inventory.append({"artifact_name": spec["artifact_name"], "artifact_category": spec["artifact_category"], **result})
    return {"artifact_inventory": inventory, "artifact_inventory_count": len(inventory)}


def write_artifact_inventory(artifact_specs: list[dict[str, Any]]) -> dict[str, Any]:
    payload = build_artifact_inventory(artifact_specs)
    write_stable_json(ARTIFACT_INVENTORY_PATH, payload)
    return payload
