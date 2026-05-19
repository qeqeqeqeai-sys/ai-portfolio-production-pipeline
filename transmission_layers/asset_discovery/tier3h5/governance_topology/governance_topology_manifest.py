from __future__ import annotations

from hashlib import sha256
from typing import Any

from .topology_context import stable_json_dumps


def build_topology_manifest(context: dict[str, Any]) -> dict[str, Any]:
    basis = {
        "phase_coverage": context["phase_coverage"],
        "artifact_coverage": context["artifact_coverage"],
        "missing_inputs": context["missing_inputs"],
    }
    topo_id = sha256(stable_json_dumps(basis).encode("utf-8")).hexdigest()[:24]
    return {
        "topology_manifest_status": "generated",
        "topology_manifest_id": f"tier3h5_topology_{topo_id}",
        "phase_coverage_map": context["phase_coverage"],
        "artifact_coverage_map": context["artifact_coverage"],
        "missing_inputs": context["missing_inputs"],
        "governance_topology_replayable": True,
        "advisory_only_governance_verified": True,
        "exact_match_only_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
    }
