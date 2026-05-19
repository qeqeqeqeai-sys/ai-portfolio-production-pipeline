from __future__ import annotations

from typing import Any


def build_evidence_inventory(context: dict[str, Any], manifest: dict[str, Any], generated: list[str]) -> dict[str, Any]:
    consumed = sorted(context["inputs"].keys())
    return {
        "evidence_inventory_status": "generated",
        "governance_artifacts_consumed": consumed,
        "governance_artifacts_generated": sorted(generated),
        "lineage_manifests": ["logs/tier3h5_governance_lineage_manifest.json"],
        "release_audit_snapshots": ["logs/tier3h5_release_audit_snapshot.json"],
        "evidence_inventory_lineage": manifest["lineage_categories"],
    }
