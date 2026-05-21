"""Tier 6I deterministic governance audit trail and certification replay evidence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from transmission_layers.intelligence.tier6.transmission_governance_review_gate import assess_transmission_governance_review_gate
from transmission_layers.intelligence.tier6.transmission_governance_summary import assess_transmission_governance_summary
from transmission_layers.intelligence.tier6.transmission_risk_register import assess_transmission_risk_register
from transmission_layers.operationalization.serialization import stable_checksum


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_score(value: Any) -> float:
    return max(0.0, min(1.0, round(_to_float(value), 6)))


def _lineage_diag(score: float) -> str:
    if score >= 0.8:
        return "strong_lineage"
    if score >= 0.6:
        return "moderate_lineage"
    if score >= 0.3:
        return "weak_lineage"
    return "missing_lineage"


def _trace_diag(score: float) -> str:
    if score >= 0.8:
        return "traceable"
    if score >= 0.6:
        return "partially_traceable"
    if score >= 0.3:
        return "weakly_traceable"
    return "non_traceable"


def _dependency_diag(score: float) -> str:
    if score >= 0.8:
        return "strongly_reconstructed"
    if score >= 0.6:
        return "moderately_reconstructed"
    if score >= 0.3:
        return "weakly_reconstructed"
    return "reconstruction_gap"


def _replay_diag(score: float) -> str:
    if score >= 0.8:
        return "replay_ready"
    if score >= 0.6:
        return "partially_replay_ready"
    if score >= 0.3:
        return "weak_replay_evidence"
    return "replay_gap"


def assess_transmission_governance_audit_trail(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}

    tier6h = assess_transmission_governance_review_gate(topology_view)
    tier6g = assess_transmission_governance_summary(topology_view)
    tier6f = assess_transmission_risk_register(topology_view)

    diagnostics_gate = tier6h.get("diagnostics", {})
    nodes = topology_view.get("nodes", []) if isinstance(topology_view.get("nodes", []), list) else []
    edges = topology_view.get("edges", []) if isinstance(topology_view.get("edges", []), list) else []
    is_empty = bool(len(nodes) == 0 or len(edges) == 0 or diagnostics_gate.get("is_empty", True))

    lineage_defs = [
        ("lineage_certification_decision", "tier6h", "certification_decision", _bounded_score(tier6h.get("governance_certification_score", 0.0))),
        ("lineage_contamination_review", "tier6f", "contamination_review", _bounded_score(1.0 - _bounded_score(tier6f.get("risk_components", {}).get("contamination_risk_score", 0.0)))),
        ("lineage_explainability_review", "tier6g", "explainability_review", _bounded_score(tier6g.get("governance_components", {}).get("explainability_governance_score", 0.0))),
        ("lineage_governance_review", "tier6g", "governance_review", _bounded_score(tier6g.get("governance_score", 0.0))),
        ("lineage_release_review", "tier6h", "release_review", _bounded_score(tier6h.get("review_components", {}).get("governance_release_score", 0.0))),
        ("lineage_remediation_review", "tier6f", "remediation_review", _bounded_score(tier6f.get("risk_components", {}).get("remediation_readiness_score", 0.0))),
        ("lineage_structural_review", "tier6h", "structural_review", _bounded_score(tier6h.get("review_components", {}).get("structural_certification_score", 0.0))),
    ]
    certification_lineage = sorted([
        {
            "lineage_id": lineage_id,
            "source_tier": source_tier,
            "lineage_type": lineage_type,
            "lineage_score": lineage_score,
            "diagnostic_label": _lineage_diag(lineage_score),
        }
        for lineage_id, source_tier, lineage_type, lineage_score in lineage_defs
    ], key=lambda x: (-x["lineage_score"], x["lineage_id"]))

    traceability_defs = [
        ("trace_contamination_to_release", "contamination_review", "release_review", _bounded_score(0.5 * lineage_defs[1][3] + 0.5 * lineage_defs[4][3])),
        ("trace_explainability_to_certification", "explainability_review", "certification_decision", _bounded_score(0.5 * lineage_defs[2][3] + 0.5 * lineage_defs[0][3])),
        ("trace_governance_to_release", "governance_review", "release_review", _bounded_score(0.5 * lineage_defs[3][3] + 0.5 * lineage_defs[4][3])),
        ("trace_remediation_to_governance", "remediation_review", "governance_review", _bounded_score(0.5 * lineage_defs[5][3] + 0.5 * lineage_defs[3][3])),
        ("trace_structural_to_certification", "structural_review", "certification_decision", _bounded_score(0.5 * lineage_defs[6][3] + 0.5 * lineage_defs[0][3])),
    ]
    review_traceability_chain = sorted([
        {
            "trace_id": trace_id,
            "trace_source": trace_source,
            "trace_target": trace_target,
            "traceability_score": traceability_score,
            "diagnostic_label": _trace_diag(traceability_score),
        }
        for trace_id, trace_source, trace_target, traceability_score in traceability_defs
    ], key=lambda x: (-x["traceability_score"], x["trace_id"]))

    dep_defs = [
        ("dependency_bottleneck", "bottleneck_dependency", _bounded_score(1.0 - _bounded_score(tier6h.get("review_components", {}).get("operational_readiness_score", 0.0)))),
        ("dependency_contamination", "contamination_dependency", _bounded_score(1.0 - lineage_defs[1][3])),
        ("dependency_explainability", "explainability_dependency", _bounded_score(1.0 - lineage_defs[2][3])),
        ("dependency_governance", "governance_dependency", _bounded_score(1.0 - lineage_defs[3][3])),
        ("dependency_propagation", "propagation_dependency", _bounded_score(1.0 - _bounded_score(tier6h.get("review_components", {}).get("contamination_certification_score", 0.0)))),
        ("dependency_remediation", "remediation_dependency", _bounded_score(1.0 - lineage_defs[5][3])),
        ("dependency_structural", "structural_dependency", _bounded_score(1.0 - lineage_defs[6][3])),
    ]
    dependency_reconstruction = sorted([
        {
            "dependency_id": dependency_id,
            "dependency_type": dependency_type,
            "dependency_score": _bounded_score(1.0 - dependency_gap),
            "diagnostic_label": _dependency_diag(_bounded_score(1.0 - dependency_gap)),
        }
        for dependency_id, dependency_type, dependency_gap in dep_defs
    ], key=lambda x: (-x["dependency_score"], x["dependency_id"]))

    evidence_defs = [
        ("evidence_certification", "certification_evidence", lineage_defs[0][3]),
        ("evidence_contamination", "contamination_evidence", lineage_defs[1][3]),
        ("evidence_deterministic_review", "deterministic_review_evidence", _bounded_score(tier6h.get("review_components", {}).get("deterministic_integrity_score", 0.0))),
        ("evidence_explainability", "explainability_evidence", lineage_defs[2][3]),
        ("evidence_governance_summary", "governance_summary_evidence", _bounded_score(tier6g.get("governance_score", 0.0))),
        ("evidence_release", "release_evidence", lineage_defs[4][3]),
        ("evidence_remediation", "remediation_evidence", lineage_defs[5][3]),
    ]
    replay_evidence_inventory = sorted([
        {
            "evidence_id": evidence_id,
            "evidence_type": evidence_type,
            "evidence_score": evidence_score,
            "diagnostic_label": _replay_diag(evidence_score),
        }
        for evidence_id, evidence_type, evidence_score in evidence_defs
    ], key=lambda x: (-x["evidence_score"], x["evidence_id"]))

    audit_components = {
        "certification_traceability_score": _bounded_score(sum(x["lineage_score"] for x in certification_lineage) / float(len(certification_lineage))),
        "replay_evidence_score": _bounded_score(sum(x["evidence_score"] for x in replay_evidence_inventory) / float(len(replay_evidence_inventory))),
        "governance_lineage_score": _bounded_score(0.5 * lineage_defs[3][3] + 0.5 * lineage_defs[4][3]),
        "dependency_reconstruction_score": _bounded_score(sum(x["dependency_score"] for x in dependency_reconstruction) / float(len(dependency_reconstruction))),
        "reproducibility_score": _bounded_score(0.5 * _bounded_score(tier6h.get("review_components", {}).get("deterministic_integrity_score", 0.0)) + 0.5 * _bounded_score(tier6h.get("governance_certification_score", 0.0))),
        "deterministic_audit_score": _bounded_score(0.5 * _bounded_score(tier6h.get("review_components", {}).get("deterministic_integrity_score", 0.0)) + 0.5 * _bounded_score(tier6g.get("governance_score", 0.0))),
        "review_consistency_score": _bounded_score(0.5 * _bounded_score(tier6h.get("review_components", {}).get("operational_readiness_score", 0.0)) + 0.5 * _bounded_score(tier6h.get("review_components", {}).get("governance_release_score", 0.0))),
    }
    audit_integrity_score = _bounded_score(sum(audit_components.values()) / float(len(audit_components)))

    audit_labels: List[str] = []
    if is_empty:
        audit_labels.append("insufficient_structure")
    if audit_components["certification_traceability_score"] < 0.6:
        audit_labels.append("incomplete_audit_lineage")
    if audit_components["replay_evidence_score"] < 0.6:
        audit_labels.append("weak_replay_evidence")
    if audit_components["dependency_reconstruction_score"] < 0.6:
        audit_labels.append("weak_dependency_reconstruction")
    if audit_components["review_consistency_score"] < 0.6:
        audit_labels.append("weak_review_consistency")
    if audit_components["reproducibility_score"] < 0.65:
        audit_labels.append("governance_reproducibility_risk")
    if audit_components["deterministic_audit_score"] < 0.65:
        audit_labels.append("deterministic_audit_gap")
    if not audit_labels or audit_labels == ["insufficient_structure"]:
        if "insufficient_structure" not in audit_labels:
            audit_labels.append("governance_audit_complete")
    audit_labels = sorted(set(audit_labels))

    governance_decision_reproducibility = {
        "is_deterministically_reproducible": audit_components["reproducibility_score"] >= 0.65 and "insufficient_structure" not in audit_labels,
        "is_review_consistent": audit_components["review_consistency_score"] >= 0.6,
        "is_traceability_sufficient": audit_components["certification_traceability_score"] >= 0.6,
        "is_replay_evidence_sufficient": audit_components["replay_evidence_score"] >= 0.6,
    }

    if "insufficient_structure" in audit_labels:
        overall_audit_state = "insufficient_structure"
    elif audit_components["review_consistency_score"] < 0.45:
        overall_audit_state = "inconsistent"
    elif audit_integrity_score < 0.65:
        overall_audit_state = "fragmented"
    elif audit_integrity_score < 0.8:
        overall_audit_state = "reviewable"
    else:
        overall_audit_state = "complete"

    gap_pairs = sorted([
        ("incomplete_audit_lineage", 1.0 - audit_components["certification_traceability_score"]),
        ("weak_replay_evidence", 1.0 - audit_components["replay_evidence_score"]),
        ("weak_dependency_reconstruction", 1.0 - audit_components["dependency_reconstruction_score"]),
        ("weak_review_consistency", 1.0 - audit_components["review_consistency_score"]),
        ("governance_reproducibility_risk", 1.0 - audit_components["reproducibility_score"]),
        ("deterministic_audit_gap", 1.0 - audit_components["deterministic_audit_score"]),
    ], key=lambda x: (-x[1], x[0]))

    audit_summary = {
        "primary_audit_label": audit_labels[0] if audit_labels else "governance_audit_complete",
        "highest_audit_gap": gap_pairs[0][0] if gap_pairs else "none",
        "strongest_lineage_source": certification_lineage[0]["source_tier"] if certification_lineage else "none",
        "strongest_replay_evidence": replay_evidence_inventory[0]["evidence_type"] if replay_evidence_inventory else "none",
        "overall_audit_state": overall_audit_state,
    }

    diagnostics = {
        "lineage_count": len(certification_lineage),
        "traceability_count": len(review_traceability_chain),
        "dependency_count": len(dependency_reconstruction),
        "replay_evidence_count": len(replay_evidence_inventory),
        "failure_mode_count": len(set(tier6h.get("review_labels", [])) - {"governance_certified", "governance_release_ready"}),
        "is_empty": is_empty,
        "is_audit_complete": "governance_audit_complete" in audit_labels,
    }

    if "insufficient_structure" in audit_labels:
        status = "insufficient_structure"
    elif any(x in audit_labels for x in {"incomplete_audit_lineage", "weak_replay_evidence", "weak_dependency_reconstruction", "weak_review_consistency", "governance_reproducibility_risk", "deterministic_audit_gap"}):
        status = "completed_with_findings"
    else:
        status = "success"

    explanation = (
        f"Transmission governance audit trail completed: status={status}; audit_integrity={audit_integrity_score}; "
        f"primary_label={audit_summary['primary_audit_label']}; lineage={len(certification_lineage)}; "
        f"replay_evidence={len(replay_evidence_inventory)}; dependencies={len(dependency_reconstruction)}."
    )

    result = {
        "status": status,
        "audit_integrity_score": audit_integrity_score,
        "audit_components": audit_components,
        "audit_labels": audit_labels,
        "certification_lineage": certification_lineage,
        "review_traceability_chain": review_traceability_chain,
        "dependency_reconstruction": dependency_reconstruction,
        "replay_evidence_inventory": replay_evidence_inventory,
        "governance_decision_reproducibility": governance_decision_reproducibility,
        "audit_summary": audit_summary,
        "diagnostics": diagnostics,
        "explanation": explanation,
    }
    result["checksum"] = stable_checksum(result, prefix="tier6i")
    return result
