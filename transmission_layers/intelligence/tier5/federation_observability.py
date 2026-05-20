from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, weighted_bounded_score
from .federation_continuity_observability import federation_continuity_observability_diagnostics
from .federation_lineage import federation_lineage_diagnostics
from .federation_observability_explanations import fixed_federation_observability_explanations
from .federation_observability_signatures import observability_checksum
from .federation_propagation_visibility import federation_propagation_visibility_diagnostics
from .federation_replay_observability import federation_replay_observability_diagnostics
from .federation_telemetry import federation_telemetry_diagnostics
from .federation_traceability import federation_traceability_diagnostics
from .federation_visibility import federation_visibility_diagnostics


def run_tier5e_federation_observability(*, systems: list[dict[str, Any]], bridges: list[dict[str, Any]], contagion_paths: list[dict[str, Any]], dependencies: list[dict[str, Any]], replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    visibility = federation_visibility_diagnostics(list(systems), list(bridges))
    lineage = federation_lineage_diagnostics(list(dependencies), list(replay_snapshots))
    traceability = federation_traceability_diagnostics(list(contagion_paths))
    telemetry = federation_telemetry_diagnostics(list(replay_snapshots))
    propagation = federation_propagation_visibility_diagnostics(list(contagion_paths))
    continuity = federation_continuity_observability_diagnostics(list(replay_snapshots))
    replay = federation_replay_observability_diagnostics(list(replay_snapshots))
    score = weighted_bounded_score([
        (visibility["federation_visibility_score"], 1.0),
        (lineage["federation_lineage_score"], 1.0),
        (traceability["federation_traceability_score"], 1.0),
        (telemetry["federation_telemetry_score"], 1.0),
        (propagation["federation_propagation_visibility_score"], 1.0),
        (continuity["federation_continuity_observability_score"], 1.0),
        (replay["federation_replay_observability_score"], 1.0),
    ])
    stability = clamp_score((continuity["federation_continuity_observability_score"] + replay["federation_replay_observability_score"]) / 2.0)
    factor_priority = {
        "federation_traceability_score": 0,
        "federation_lineage_score": 1,
        "federation_propagation_visibility_score": 2,
        "federation_continuity_observability_score": 3,
        "federation_replay_observability_score": 4,
        "federation_visibility_score": 5,
        "federation_telemetry_score": 6,
    }
    factors = sorted([
        ("federation_visibility_score", visibility["federation_visibility_score"]),
        ("federation_lineage_score", lineage["federation_lineage_score"]),
        ("federation_traceability_score", traceability["federation_traceability_score"]),
        ("federation_telemetry_score", telemetry["federation_telemetry_score"]),
        ("federation_propagation_visibility_score", propagation["federation_propagation_visibility_score"]),
        ("federation_continuity_observability_score", continuity["federation_continuity_observability_score"]),
        ("federation_replay_observability_score", replay["federation_replay_observability_score"]),
    ], key=lambda x: (-x[1], factor_priority[x[0]], x[0]))
    classification = "strong" if score >= 0.75 else "moderate" if score >= 0.4 else "weak"
    result = {
        "federation_observability_id": observability_checksum({"systems": sorted(str(s.get("system_id", s.get("id", ""))) for s in systems)}, "foid"),
        "federation_observability_score": score,
        "bounded_federation_observability_score": clamp_score(score),
        **visibility, **lineage, **traceability, **telemetry, **propagation, **continuity, **replay,
        "federation_observability_stability_score": stability,
        "dominant_observability_factor": factors[0][0] if factors else "none",
        "federation_observability_classification": classification,
    }
    result["federation_observability_checksum"] = observability_checksum(result, "tier5e_observability")
    result["federation_observability_signature_checksum"] = observability_checksum({"id": result["federation_observability_id"], "score": result["federation_observability_score"]}, "tier5e_signature")
    result.update(fixed_federation_observability_explanations(result))
    return result
