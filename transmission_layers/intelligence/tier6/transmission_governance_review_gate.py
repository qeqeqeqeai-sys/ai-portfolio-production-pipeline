"""Tier 6H deterministic transmission governance review gate and release certification."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from transmission_layers.intelligence.tier6.propagation_distortion_diagnostics import assess_propagation_distortion_diagnostics
from transmission_layers.intelligence.tier6.structural_signal_quality import assess_structural_signal_quality
from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
from transmission_layers.intelligence.tier6.transmission_governance_summary import assess_transmission_governance_summary
from transmission_layers.intelligence.tier6.transmission_path_integrity import assess_transmission_path_integrity
from transmission_layers.intelligence.tier6.transmission_reliability_diagnostics import assess_transmission_reliability_diagnostics
from transmission_layers.intelligence.tier6.transmission_risk_register import assess_transmission_risk_register
from transmission_layers.operationalization.serialization import stable_checksum


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_score(value: Any) -> float:
    return max(0.0, min(1.0, round(_to_float(value), 6)))


def _finding_diag(score: float) -> str:
    if score >= 0.75:
        return "blocking_finding"
    if score >= 0.55:
        return "elevated_finding"
    if score >= 0.30:
        return "moderate_finding"
    return "informational_finding"


def _failure_diag(score: float) -> str:
    if score >= 0.75:
        return "critical_failure"
    if score >= 0.55:
        return "elevated_failure"
    if score >= 0.30:
        return "moderate_failure"
    return "no_failure"


def _requirement_diag(score: float) -> str:
    if score >= 0.75:
        return "mandatory_requirement"
    if score >= 0.55:
        return "high_requirement"
    if score >= 0.30:
        return "moderate_requirement"
    return "optional_requirement"


def assess_transmission_governance_review_gate(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}

    tier6a = assess_structural_signal_quality(topology_view)
    tier6b = assess_transmission_reliability_diagnostics(topology_view)
    tier6c = assess_transmission_path_integrity(topology_view)
    tier6d = assess_propagation_distortion_diagnostics(topology_view)
    tier6e = assess_transmission_explainability(topology_view)
    tier6f = assess_transmission_risk_register(topology_view)
    tier6g = assess_transmission_governance_summary(topology_view)

    node_count = int(tier6c.get("diagnostics", {}).get("node_count", 0))
    edge_count = int(tier6c.get("diagnostics", {}).get("edge_count", 0))
    is_empty = bool(tier6c.get("diagnostics", {}).get("is_empty", False))

    structural_certification_score = _bounded_score(tier6a.get("signal_quality_score", 0.0))
    explainability_certification_score = _bounded_score(tier6e.get("explainability_score", 0.0))
    remediation_certification_score = _bounded_score(tier6f.get("risk_components", {}).get("remediation_readiness_score", 0.0))
    contamination_certification_score = _bounded_score(tier6d.get("propagation_integrity_score", 0.0))
    operational_readiness_score = _bounded_score(0.5 * _bounded_score(tier6g.get("governance_components", {}).get("governance_readiness_score", 0.0)) + 0.5 * _bounded_score(tier6g.get("governance_components", {}).get("operational_stability_score", 0.0)))
    governance_release_score = _bounded_score(0.5 * _bounded_score(tier6g.get("governance_score", 0.0)) + 0.5 * _bounded_score(1.0 - _bounded_score(tier6f.get("risk_register_score", 0.0))))

    failure_modes = set(tier6b.get("transmission_failure_modes", [])) | set(tier6c.get("path_failure_modes", [])) | set(tier6d.get("distortion_failure_modes", []))
    integrity_raw = 1.0 - min(1.0, 0.18 * float(len(failure_modes)))
    if not bool(tier6g.get("governance_readiness", {}).get("is_governance_ready", False)):
        integrity_raw -= 0.2
    deterministic_integrity_score = _bounded_score(integrity_raw)

    review_components = {
        "structural_certification_score": structural_certification_score,
        "explainability_certification_score": explainability_certification_score,
        "remediation_certification_score": remediation_certification_score,
        "contamination_certification_score": contamination_certification_score,
        "operational_readiness_score": operational_readiness_score,
        "governance_release_score": governance_release_score,
        "deterministic_integrity_score": deterministic_integrity_score,
    }
    governance_certification_score = _bounded_score(sum(review_components.values()) / float(len(review_components)))

    review_labels: List[str] = []
    if is_empty or node_count <= 0 or edge_count <= 0:
        review_labels.append("insufficient_structure")
    if structural_certification_score < 0.45:
        review_labels.append("structural_certification_failure")
    if explainability_certification_score < 0.60:
        review_labels.append("explainability_certification_failure")
    if remediation_certification_score < 0.60:
        review_labels.append("remediation_certification_failure")
    if contamination_certification_score < 0.60:
        review_labels.append("contamination_certification_failure")
    if governance_release_score < 0.55:
        review_labels.append("governance_release_blocked")
    if operational_readiness_score < 0.65:
        review_labels.append("operational_instability_detected")
    if governance_certification_score < 0.65:
        review_labels.append("certification_attention_required")
    if governance_certification_score >= 0.65 and "insufficient_structure" not in review_labels:
        review_labels.append("governance_certified")
    if governance_release_score >= 0.65 and operational_readiness_score >= 0.65 and "insufficient_structure" not in review_labels:
        review_labels.append("governance_release_ready")
    review_labels = sorted(set(review_labels))

    finding_defs = [
        ("finding_contamination_gap", "contamination_gap", 1.0 - contamination_certification_score, ["tier6d", "tier6f"]),
        ("finding_deterministic_integrity_gap", "deterministic_integrity_gap", 1.0 - deterministic_integrity_score, ["tier6b", "tier6c", "tier6d", "tier6g"]),
        ("finding_explainability_gap", "explainability_gap", 1.0 - explainability_certification_score, ["tier6e"]),
        ("finding_governance_release_gap", "governance_release_gap", 1.0 - governance_release_score, ["tier6f", "tier6g"]),
        ("finding_propagation_gap", "propagation_gap", 1.0 - _bounded_score(tier6b.get("transmission_reliability_score", 0.0)), ["tier6b", "tier6d"]),
        ("finding_remediation_gap", "remediation_gap", 1.0 - remediation_certification_score, ["tier6f"]),
        ("finding_structural_gap", "structural_gap", 1.0 - structural_certification_score, ["tier6a", "tier6c"]),
        ("finding_bottleneck_gap", "bottleneck_gap", 1.0 - _bounded_score(tier6c.get("path_components", {}).get("bottleneck_resilience_score", 0.0)), ["tier6c"]),
    ]
    review_findings = sorted([
        {
            "finding_id": finding_id,
            "finding_type": finding_type,
            "severity_score": _bounded_score(severity_score),
            "source_tiers": sorted(source_tiers),
            "diagnostic_label": _finding_diag(_bounded_score(severity_score)),
        }
        for finding_id, finding_type, severity_score, source_tiers in finding_defs
    ], key=lambda x: (-x["severity_score"], x["finding_id"]))

    failure_defs = [
        ("failure_structural", "structural_failure", 1.0 - structural_certification_score),
        ("failure_explainability", "explainability_failure", 1.0 - explainability_certification_score),
        ("failure_remediation", "remediation_failure", 1.0 - remediation_certification_score),
        ("failure_contamination", "contamination_failure", 1.0 - contamination_certification_score),
        ("failure_deterministic_integrity", "deterministic_integrity_failure", 1.0 - deterministic_integrity_score),
        ("failure_operational_readiness", "operational_readiness_failure", 1.0 - operational_readiness_score),
        ("failure_governance_release", "governance_release_failure", 1.0 - governance_release_score),
    ]
    certification_failures = sorted([
        {"failure_id": fid, "failure_type": ftype, "failure_score": _bounded_score(fscore), "diagnostic_label": _failure_diag(_bounded_score(fscore))}
        for fid, ftype, fscore in failure_defs
    ], key=lambda x: (-x["failure_score"], x["failure_id"]))

    requirement_defs = [
        ("requirement_improve_connectivity", "improve_connectivity", 1.0 - operational_readiness_score),
        ("requirement_improve_traceability", "improve_traceability", 1.0 - _bounded_score(tier6b.get("reliability_components", {}).get("causal_traceability_score", 0.0))),
        ("requirement_reduce_contamination", "reduce_contamination", 1.0 - contamination_certification_score),
        ("requirement_reduce_bottleneck_dependency", "reduce_bottleneck_dependency", 1.0 - _bounded_score(tier6c.get("path_components", {}).get("bottleneck_resilience_score", 0.0))),
        ("requirement_improve_explainability", "improve_explainability", 1.0 - explainability_certification_score),
        ("requirement_improve_remediation_coverage", "improve_remediation_coverage", 1.0 - remediation_certification_score),
        ("requirement_improve_structural_consistency", "improve_structural_consistency", 1.0 - structural_certification_score),
        ("requirement_improve_deterministic_integrity", "improve_deterministic_integrity", 1.0 - deterministic_integrity_score),
    ]
    remediation_requirements = sorted([
        {"requirement_id": rid, "requirement_type": rtype, "requirement_score": _bounded_score(rscore), "diagnostic_label": _requirement_diag(_bounded_score(rscore))}
        for rid, rtype, rscore in requirement_defs
    ], key=lambda x: (-x["requirement_score"], x["requirement_id"]))

    if is_empty or node_count <= 0 or edge_count <= 0:
        deterministic_integrity_state = "insufficient_structure"
    elif deterministic_integrity_score >= 0.8:
        deterministic_integrity_state = "deterministic"
    elif deterministic_integrity_score >= 0.55:
        deterministic_integrity_state = "partially_deterministic"
    else:
        deterministic_integrity_state = "structurally_inconsistent"

    release_blocked = "governance_release_blocked" in review_labels or any(x["diagnostic_label"] == "critical_failure" for x in certification_failures)
    requires_review = governance_certification_score < 0.65 or "certification_attention_required" in review_labels
    if "insufficient_structure" in review_labels:
        overall_release_state = "insufficient_structure"
    elif release_blocked:
        overall_release_state = "blocked"
    elif requires_review:
        overall_release_state = "review_required"
    else:
        overall_release_state = "certified"

    certification_summary = {
        "primary_review_label": review_labels[0] if review_labels else "governance_certified",
        "highest_certification_risk": certification_failures[0]["failure_type"] if certification_failures else "none",
        "highest_remediation_requirement": remediation_requirements[0]["requirement_type"] if remediation_requirements else "none",
        "deterministic_integrity_state": deterministic_integrity_state,
        "overall_release_state": overall_release_state,
    }

    release_readiness = {
        "is_governance_certified": "governance_certified" in review_labels,
        "is_release_ready": "governance_release_ready" in review_labels and not release_blocked,
        "requires_blocking_remediation": any(x["diagnostic_label"] == "mandatory_requirement" for x in remediation_requirements),
        "requires_governance_review": requires_review or release_blocked,
    }

    governance_release_packet = {
        "signal_quality_review_status": tier6a.get("status", "insufficient_structure"),
        "reliability_review_status": tier6b.get("status", "insufficient_structure"),
        "path_integrity_review_status": tier6c.get("status", "insufficient_structure"),
        "distortion_review_status": tier6d.get("status", "insufficient_structure"),
        "explainability_review_status": tier6e.get("status", "insufficient_structure"),
        "risk_register_review_status": tier6f.get("status", "insufficient_structure"),
        "governance_summary_review_status": tier6g.get("status", "insufficient_structure"),
    }

    diagnostics = {
        "finding_count": len(review_findings),
        "blocking_finding_count": sum(1 for x in review_findings if x["diagnostic_label"] == "blocking_finding"),
        "failure_count": len(certification_failures),
        "mandatory_requirement_count": sum(1 for x in remediation_requirements if x["diagnostic_label"] == "mandatory_requirement"),
        "failure_mode_count": len(failure_modes),
        "is_empty": is_empty,
        "is_release_ready": release_readiness["is_release_ready"],
    }

    if "insufficient_structure" in review_labels:
        status = "insufficient_structure"
    elif any(label in review_labels for label in {"certification_attention_required", "governance_release_blocked", "operational_instability_detected"}):
        status = "completed_with_findings"
    else:
        status = "success"

    explanation = (
        f"Transmission governance review gate completed: status={status}; certification={governance_certification_score}; "
        f"primary_label={certification_summary['primary_review_label']}; findings={len(review_findings)}; "
        f"failures={len(certification_failures)}; requirements={len(remediation_requirements)}."
    )

    result = {
        "status": status,
        "governance_certification_score": governance_certification_score,
        "review_components": review_components,
        "review_labels": review_labels,
        "certification_summary": certification_summary,
        "review_findings": review_findings,
        "certification_failures": certification_failures,
        "remediation_requirements": remediation_requirements,
        "release_readiness": release_readiness,
        "governance_release_packet": governance_release_packet,
        "diagnostics": diagnostics,
        "explanation": explanation,
    }
    result["checksum"] = stable_checksum(result, prefix="tier6h")
    return result
