from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, weighted_bounded_score
from .federation_constraint_history import federation_constraint_history_diagnostics
from .federation_constraints import federation_constraint_diagnostics
from .federation_continuity_constraints import federation_continuity_constraint_diagnostics
from .federation_escalation import federation_escalation_diagnostics
from .federation_governance_explanations import fixed_federation_governance_explanations
from .federation_governance_signatures import governance_checksum
from .federation_guardrails import federation_guardrail_diagnostics
from .federation_policy_boundaries import federation_boundary_enforcement_diagnostics
from .federation_violation_detection import federation_violation_score


def run_tier5d_federation_governance(*, systems: list[dict[str, Any]], bridges: list[dict[str, Any]], contagion_paths: list[dict[str, Any]], dependencies: list[dict[str, Any]], replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    constraint = federation_constraint_diagnostics(list(systems), list(dependencies))
    guardrails = federation_guardrail_diagnostics(list(contagion_paths))
    boundaries = federation_boundary_enforcement_diagnostics(list(bridges))
    continuity = federation_continuity_constraint_diagnostics(list(replay_snapshots))
    recurrence = federation_constraint_history_diagnostics(list(replay_snapshots))
    violation = federation_violation_score(
        constraint_score=constraint["federation_constraint_score"],
        guardrail_score=guardrails["federation_guardrail_score"],
        boundary_enforcement_score=boundaries["federation_boundary_enforcement_score"],
        continuity_score=continuity["federation_continuity_constraint_score"],
    )
    escalation = federation_escalation_diagnostics(violation["federation_violation_score"], recurrence["federation_constraint_recurrence_score"])
    governance_score = weighted_bounded_score([
        (constraint["federation_constraint_score"], 0.2),
        (guardrails["federation_guardrail_score"], 0.2),
        (1.0 - boundaries["federation_boundary_enforcement_score"], 0.2),
        (violation["federation_violation_score"], 0.2),
        (escalation["federation_escalation_score"], 0.2),
    ])
    factors = sorted([
        ("federation_governance_score", governance_score),
        ("federation_violation_score", violation["federation_violation_score"]),
        ("federation_escalation_score", escalation["federation_escalation_score"]),
        ("federation_constraint_score", constraint["federation_constraint_score"]),
        ("federation_guardrail_score", guardrails["federation_guardrail_score"]),
        ("governance_containment_effectiveness_score", -guardrails["governance_containment_effectiveness_score"]),
        ("federation_governance_stability_score", -continuity["federation_governance_stability_score"]),
        ("federation_id", 0.0),
    ], key=lambda x: (-x[1], x[0]))
    result = {
        "federation_governance_id": governance_checksum({"systems": sorted(str(s.get('system_id', s.get('id', ''))) for s in systems)}, "fgid"),
        "federation_governance_score": governance_score,
        "bounded_federation_governance_score": clamp_score(governance_score),
        **constraint,
        **guardrails,
        **boundaries,
        **violation,
        **escalation,
        **continuity,
        **recurrence,
        "dominant_governance_factor": factors[0][0],
    }
    result["federation_governance_checksum"] = governance_checksum(result, "tier5d_governance")
    result["federation_constraint_checksum"] = governance_checksum({"federation_constraint_score": result["federation_constraint_score"], "federation_constraint_recurrence_score": result["federation_constraint_recurrence_score"]}, "tier5d_constraint")
    result["federation_guardrail_checksum"] = governance_checksum({"federation_guardrail_score": result["federation_guardrail_score"]}, "tier5d_guardrail")
    result["federation_boundary_enforcement_checksum"] = governance_checksum({"federation_boundary_enforcement_score": result["federation_boundary_enforcement_score"]}, "tier5d_boundary")
    result["federation_violation_checksum"] = governance_checksum({"federation_violation_score": result["federation_violation_score"]}, "tier5d_violation")
    result["federation_escalation_checksum"] = governance_checksum({"federation_escalation_score": result["federation_escalation_score"]}, "tier5d_escalation")
    result["federation_continuity_constraint_checksum"] = governance_checksum({"federation_continuity_constraint_score": result["federation_continuity_constraint_score"]}, "tier5d_continuity")
    result["governance_containment_checksum"] = governance_checksum({"governance_containment_effectiveness_score": result["governance_containment_effectiveness_score"]}, "tier5d_containment")
    result["federation_governance_signature_checksum"] = governance_checksum({"id": result["federation_governance_id"], "score": result["federation_governance_score"]}, "tier5d_signature")
    result.update(fixed_federation_governance_explanations(result))
    return result
