from __future__ import annotations

from typing import Any


def build_reachability_summary(context: dict[str, Any]) -> dict[str, Any]:
    by_phase = {
        phase: [p for p in paths if context["artifact_coverage"].get(p, False)]
        for phase, paths in sorted(context["phase_inputs"].items())
    }
    by_invariant = {
        "tier3h4_freeze_boundary_preserved": sorted(
            [p for p in context["loaded_inputs"] if "summary" in p or "registry" in p]
        )
    }
    return {
        "artifacts_supporting_phase": by_phase,
        "summaries_supporting_invariant": by_invariant,
        "lineage_supporting_release_auditability": sorted(
            [p for p in context["loaded_inputs"] if "lineage" in p or "audit" in p]
        ),
        "topology_supporting_control_plane_observability": sorted(
            [p for p in context["loaded_inputs"] if "topology" in p or "control_plane" in p]
        ),
        "reachability_records_generated": len(by_phase) + len(by_invariant),
    }
