from __future__ import annotations

from typing import Any


def validate_measure_readiness(measure_catalog: dict[str, Any]) -> dict[str, Any]:
    measures = measure_catalog.get("measures", []) if isinstance(measure_catalog, dict) else []
    return {
        "measure_catalog_ready": bool(measures),
        "measure_inventory_complete": bool(measures),
        "measure_count": len(measures),
    }
