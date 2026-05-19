from __future__ import annotations

from typing import Any


def build_monitoring_lineage_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    monitoring = manifest["lineage_categories"]["monitoring"]["artifacts"]
    drift = manifest["lineage_categories"]["drift"]["artifacts"]
    return {
        "monitoring_lineage_status": "generated",
        "monitoring_artifacts": monitoring,
        "drift_artifacts": drift,
        "monitoring_continuity_verified": bool(monitoring),
        "drift_continuity_verified": bool(drift),
    }
