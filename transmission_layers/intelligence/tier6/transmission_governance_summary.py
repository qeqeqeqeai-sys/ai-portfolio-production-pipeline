"""Tier 6G deterministic transmission governance summary and executive decision packet."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from transmission_layers.intelligence.tier6.propagation_distortion_diagnostics import assess_propagation_distortion_diagnostics
from transmission_layers.intelligence.tier6.structural_signal_quality import assess_structural_signal_quality
from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
from transmission_layers.intelligence.tier6.transmission_path_integrity import assess_transmission_path_integrity
from transmission_layers.intelligence.tier6.transmission_reliability_diagnostics import assess_transmission_reliability_diagnostics
from transmission_layers.intelligence.tier6.transmission_risk_register import assess_transmission_risk_register
from transmission_layers.operationalization.serialization import stable_checksum


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_score(value: float) -> float:
    return max(0.0, min(1.0, round(_to_float(value), 6)))


def _risk_label(score: float) -> str:
    if score >= 0.85:
        return "critical_risk"
    if score >= 0.65:
        return "elevated_risk"
    if score >= 0.4:
        return "moderate_risk"
    return "low_risk"


def _evidence_label(score: float) -> str:
    if score >= 0.85:
        return "decisive_evidence"
    if score >= 0.65:
        return "strong_evidence"
    if score >= 0.4:
        return "moderate_evidence"
    return "weak_evidence"


def _bottleneck_label(score: float) -> str:
    if score >= 0.85:
        return "severe_bottleneck"
    if score >= 0.65:
        return "elevated_bottleneck"
    if score >= 0.4:
        return "moderate_bottleneck"
    return "low_bottleneck"


def _contamination_label(score: float) -> str:
    if score >= 0.85:
        return "severe_contamination"
    if score >= 0.65:
        return "elevated_contamination"
    if score >= 0.4:
        return "moderate_contamination"
    return "low_contamination"


def _priority_label(score: float) -> str:
    if score >= 0.85:
        return "immediate_priority"
    if score >= 0.65:
        return "high_priority"
    if score >= 0.4:
        return "moderate_priority"
    return "low_priority"


def assess_transmission_governance_summary(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}

    tier6a = assess_structural_signal_quality(topology_view)
    tier6b = assess_transmission_reliability_diagnostics(topology_view)
    tier6c = assess_transmission_path_integrity(topology_view)
    tier6d = assess_propagation_distortion_diagnostics(topology_view)
    tier6e = assess_transmission_explainability(topology_view)
    tier6f = assess_transmission_risk_register(topology_view)

    structural_governance_score = _bounded_score(tier6a.get("signal_quality_score", 0.0))
    propagation_governance_score = _bounded_score(0.5 * _bounded_score(tier6b.get("transmission_reliability_score", 0.0)) + 0.5 * _bounded_score(tier6c.get("path_integrity_score", 0.0)))
    risk_governance_score = _bounded_score(1.0 - _bounded_score(tier6f.get("risk_register_score", 0.0)))
    explainability_governance_score = _bounded_score(tier6e.get("explainability_score", 0.0))
    remediation_governance_score = _bounded_score(tier6f.get("risk_components", {}).get("remediation_readiness_score", 0.0))

    node_count = int(tier6c.get("diagnostics", {}).get("node_count", 0))
    edge_count = int(tier6c.get("diagnostics", {}).get("edge_count", 0))
    is_empty = bool(tier6c.get("diagnostics", {}).get("is_empty", False))
    is_governance_ready = bool(not is_empty and node_count > 0 and edge_count > 0)

    governance_readiness_score = _bounded_score(
        0.4 * (1.0 if is_governance_ready else 0.0)
        + 0.3 * _bounded_score(tier6e.get("evidence_components", {}).get("attribution_completeness_score", 0.0))
        + 0.3 * _bounded_score(tier6b.get("reliability_components", {}).get("causal_traceability_score", 0.0))
    )
    operational_stability_score = _bounded_score(
        0.30 * structural_governance_score
        + 0.25 * propagation_governance_score
        + 0.20 * _bounded_score(tier6d.get("propagation_integrity_score", 0.0))
        + 0.15 * explainability_governance_score
        + 0.10 * risk_governance_score
    )

    governance_components = {
        "structural_governance_score": structural_governance_score,
        "propagation_governance_score": propagation_governance_score,
        "risk_governance_score": risk_governance_score,
        "explainability_governance_score": explainability_governance_score,
        "remediation_governance_score": remediation_governance_score,
        "governance_readiness_score": governance_readiness_score,
        "operational_stability_score": operational_stability_score,
    }
    governance_score = _bounded_score(sum(governance_components.values()) / float(len(governance_components)))

    top_risks = [
        {"risk_id": x["risk_id"], "risk_type": x["risk_type"], "severity_score": _bounded_score(x.get("severity_score", 0.0)), "diagnostic_label": _risk_label(_bounded_score(x.get("severity_score", 0.0)))}
        for x in tier6f.get("risk_inventory", [])
    ]
    top_risks = sorted(top_risks, key=lambda x: (-x["severity_score"], x["risk_id"]))[:5]

    primary_evidence = tier6e.get("primary_evidence", [])
    top_evidence = [
        {
            "evidence_id": x.get("evidence_id", ""),
            "source_tier": x.get("source_tier", ""),
            "evidence_type": x.get("evidence_type", ""),
            "evidence_score": _bounded_score(x.get("evidence_score", 0.0)),
            "diagnostic_label": _evidence_label(_bounded_score(x.get("evidence_score", 0.0))),
        }
        for x in primary_evidence
    ]
    top_evidence = sorted(top_evidence, key=lambda x: (-x["evidence_score"], x["evidence_id"]))[:5]

    bottleneck_score = _bounded_score(1.0 - _bounded_score(tier6c.get("path_components", {}).get("bottleneck_resilience_score", 0.0)))
    top_bottlenecks = sorted([
        {"bottleneck_id": "bottleneck_edge_dependency", "bottleneck_type": "edge_bottleneck", "dependency_score": _bounded_score(1.0 if int(tier6c.get("diagnostics", {}).get("critical_path_count", 0)) > 0 else 0.0), "diagnostic_label": _bottleneck_label(_bounded_score(1.0 if int(tier6c.get("diagnostics", {}).get("critical_path_count", 0)) > 0 else 0.0))},
        {"bottleneck_id": "bottleneck_node_dependency", "bottleneck_type": "node_bottleneck", "dependency_score": _bounded_score(1.0 if int(tier6c.get("diagnostics", {}).get("high_bottleneck_node_count", 0)) > 0 else bottleneck_score), "diagnostic_label": _bottleneck_label(_bounded_score(1.0 if int(tier6c.get("diagnostics", {}).get("high_bottleneck_node_count", 0)) > 0 else bottleneck_score))},
        {"bottleneck_id": "bottleneck_path_resilience", "bottleneck_type": "path_bottleneck", "dependency_score": bottleneck_score, "diagnostic_label": _bottleneck_label(bottleneck_score)},
    ], key=lambda x: (-x["dependency_score"], x["bottleneck_id"]))

    top_contamination_findings = sorted([
        {"finding_id": "finding_contaminated_node", "finding_type": "contaminated_node", "contamination_score": _bounded_score(1.0 if "contaminated_transmission" in tier6d.get("distortion_labels", []) else 0.0), "diagnostic_label": _contamination_label(_bounded_score(1.0 if "contaminated_transmission" in tier6d.get("distortion_labels", []) else 0.0))},
        {"finding_id": "finding_contradictory_transmission", "finding_type": "contradictory_transmission", "contamination_score": _bounded_score(1.0 if int(tier6d.get("diagnostics", {}).get("contradictory_edge_count", 0)) > 0 else 0.0), "diagnostic_label": _contamination_label(_bounded_score(1.0 if int(tier6d.get("diagnostics", {}).get("contradictory_edge_count", 0)) > 0 else 0.0))},
        {"finding_id": "finding_distorted_edge", "finding_type": "distorted_edge", "contamination_score": _bounded_score(1.0 - _bounded_score(tier6d.get("propagation_integrity_score", 0.0))), "diagnostic_label": _contamination_label(_bounded_score(1.0 - _bounded_score(tier6d.get("propagation_integrity_score", 0.0))))},
        {"finding_id": "finding_fragmented_path", "finding_type": "fragmented_path", "contamination_score": _bounded_score(1.0 if "fragmented_propagation" in tier6d.get("distortion_labels", []) else 0.0), "diagnostic_label": _contamination_label(_bounded_score(1.0 if "fragmented_propagation" in tier6d.get("distortion_labels", []) else 0.0))},
        {"finding_id": "finding_weak_semantic_alignment", "finding_type": "weak_semantic_alignment", "contamination_score": _bounded_score(1.0 - _bounded_score(tier6b.get("reliability_components", {}).get("semantic_alignment_score", 0.0))), "diagnostic_label": _contamination_label(_bounded_score(1.0 - _bounded_score(tier6b.get("reliability_components", {}).get("semantic_alignment_score", 0.0))))},
    ], key=lambda x: (-x["contamination_score"], x["finding_id"]))

    top_remediation_priorities = [
        {"remediation_id": x["remediation_id"], "target_issue": x["target_issue"], "priority_score": _bounded_score(x.get("priority_score", 0.0)), "diagnostic_label": _priority_label(_bounded_score(x.get("priority_score", 0.0)))}
        for x in tier6f.get("remediation_priorities", [])
    ]
    top_remediation_priorities = sorted(top_remediation_priorities, key=lambda x: (-x["priority_score"], x["remediation_id"]))[:5]

    governance_labels: List[str] = []
    if not is_governance_ready:
        governance_labels.append("insufficient_structure")
    if governance_score < 0.65:
        governance_labels.append("governance_attention_required")
    if structural_governance_score < 0.45:
        governance_labels.append("elevated_structural_governance_risk")
    if propagation_governance_score < 0.45:
        governance_labels.append("elevated_propagation_governance_risk")
    if top_contamination_findings and top_contamination_findings[0]["contamination_score"] >= 0.55:
        governance_labels.append("elevated_contamination_governance_risk")
    if top_bottlenecks and top_bottlenecks[0]["dependency_score"] >= 0.55:
        governance_labels.append("elevated_bottleneck_governance_risk")
    if explainability_governance_score < 0.55:
        governance_labels.append("weak_explainability_governance")
    if remediation_governance_score < 0.55:
        governance_labels.append("weak_remediation_governance")
    if is_governance_ready and governance_score >= 0.65:
        governance_labels.append("governance_ready")
    if operational_stability_score >= 0.7:
        governance_labels.append("operationally_stable")
    governance_labels = sorted(set(governance_labels))

    overall_operational_state = "stable" if operational_stability_score >= 0.7 else "stressed"
    if not is_governance_ready:
        overall_operational_state = "insufficient_structure"
    elif top_contamination_findings and top_contamination_findings[0]["contamination_score"] >= 0.65:
        overall_operational_state = "contaminated"
    elif top_bottlenecks and top_bottlenecks[0]["dependency_score"] >= 0.65:
        overall_operational_state = "bottlenecked"
    elif "fragmented_propagation" in tier6d.get("distortion_labels", []):
        overall_operational_state = "fragmented"

    executive_summary = {
        "primary_governance_label": governance_labels[0] if governance_labels else "governance_attention_required",
        "highest_risk_type": top_risks[0]["risk_type"] if top_risks else "none",
        "highest_remediation_priority": top_remediation_priorities[0]["target_issue"] if top_remediation_priorities else "none",
        "strongest_evidence_source": top_evidence[0]["source_tier"] if top_evidence else "none",
        "overall_operational_state": overall_operational_state,
    }

    governance_readiness = {
        "is_governance_ready": is_governance_ready,
        "is_operationally_stable": operational_stability_score >= 0.7,
        "requires_immediate_attention": (governance_score < 0.45) or (top_risks and top_risks[0]["severity_score"] >= 0.85),
        "requires_structural_remediation": structural_governance_score < 0.55 or propagation_governance_score < 0.55,
    }

    governance_packet = {
        "signal_quality_status": tier6a.get("status", "insufficient_structure"),
        "reliability_status": tier6b.get("status", "insufficient_structure"),
        "path_integrity_status": tier6c.get("status", "insufficient_structure"),
        "distortion_status": tier6d.get("status", "insufficient_structure"),
        "explainability_status": tier6e.get("status", "insufficient_structure"),
        "risk_register_status": tier6f.get("status", "insufficient_structure"),
    }

    failure_modes = set(tier6b.get("transmission_failure_modes", [])) | set(tier6c.get("path_failure_modes", [])) | set(tier6d.get("distortion_failure_modes", []))
    diagnostics = {
        "risk_count": len(top_risks),
        "evidence_count": len(top_evidence),
        "bottleneck_count": len(top_bottlenecks),
        "contamination_count": len(top_contamination_findings),
        "remediation_count": len(top_remediation_priorities),
        "failure_mode_count": len(failure_modes),
        "is_empty": is_empty,
        "is_governance_ready": is_governance_ready,
    }

    status = "success"
    if not is_governance_ready:
        status = "insufficient_structure"
    elif governance_labels and governance_labels != ["governance_ready", "operationally_stable"]:
        status = "completed_with_findings"

    explanation = (
        f"Transmission governance summary completed: status={status}; governance={governance_score}; "
        f"primary_label={executive_summary['primary_governance_label']}; risks={len(top_risks)}; "
        f"bottlenecks={len(top_bottlenecks)}; remediations={len(top_remediation_priorities)}."
    )

    result = {
        "status": status,
        "governance_score": governance_score,
        "governance_components": governance_components,
        "governance_labels": governance_labels,
        "executive_summary": executive_summary,
        "top_risks": top_risks,
        "top_evidence": top_evidence,
        "top_bottlenecks": top_bottlenecks,
        "top_contamination_findings": top_contamination_findings,
        "top_remediation_priorities": top_remediation_priorities,
        "governance_readiness": governance_readiness,
        "governance_packet": governance_packet,
        "diagnostics": diagnostics,
        "explanation": explanation,
    }
    result["checksum"] = stable_checksum(result, prefix="tier6g")
    return result
