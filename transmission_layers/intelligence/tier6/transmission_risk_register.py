"""Tier 6F deterministic transmission risk register and remediation prioritization."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from transmission_layers.intelligence.tier6.propagation_distortion_diagnostics import assess_propagation_distortion_diagnostics
from transmission_layers.intelligence.tier6.structural_signal_quality import assess_structural_signal_quality
from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
from transmission_layers.intelligence.tier6.transmission_path_integrity import assess_transmission_path_integrity
from transmission_layers.intelligence.tier6.transmission_reliability_diagnostics import assess_transmission_reliability_diagnostics
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
    if score > 0.0:
        return "low_risk"
    return "informational_risk"


def _priority_label(score: float) -> str:
    if score >= 0.85:
        return "immediate_priority"
    if score >= 0.65:
        return "high_priority"
    if score >= 0.4:
        return "moderate_priority"
    return "low_priority"


def _containment_label(score: float) -> str:
    if score >= 0.7:
        return "strong_containment_candidate"
    if score >= 0.45:
        return "moderate_containment_candidate"
    if score > 0.0:
        return "weak_containment_candidate"
    return "containment_not_required"


def assess_transmission_risk_register(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}

    tier6a = assess_structural_signal_quality(topology_view)
    tier6b = assess_transmission_reliability_diagnostics(topology_view)
    tier6c = assess_transmission_path_integrity(topology_view)
    tier6d = assess_propagation_distortion_diagnostics(topology_view)
    tier6e = assess_transmission_explainability(topology_view)

    structural_risk_score = _bounded_score(1.0 - _bounded_score(tier6a.get("signal_quality_score", 0.0)))
    propagation_risk_score = _bounded_score(1.0 - _bounded_score(tier6b.get("transmission_reliability_score", 0.0)))
    bottleneck_risk_score = _bounded_score(1.0 - _bounded_score(tier6c.get("path_components", {}).get("bottleneck_resilience_score", 0.0)))
    contamination_risk_score = _bounded_score(1.0 - _bounded_score(tier6d.get("distortion_components", {}).get("contamination_containment_score", 0.0)))
    explainability_risk_score = _bounded_score(1.0 - _bounded_score(tier6e.get("explainability_score", 0.0)))

    remediation_readiness_base = _bounded_score(
        0.5 * _bounded_score(tier6e.get("evidence_components", {}).get("attribution_completeness_score", 0.0))
        + 0.5 * _bounded_score(tier6e.get("evidence_components", {}).get("evidence_consistency_score", 0.0))
    )
    remediation_pressure = _bounded_score((structural_risk_score + propagation_risk_score + contamination_risk_score) / 3.0)
    remediation_readiness_score = _bounded_score(remediation_readiness_base * _bounded_score(1.0 - 0.7 * remediation_pressure))
    containment_feasibility_score = _bounded_score(
        0.5 * _bounded_score(tier6c.get("path_components", {}).get("containment_viability_score", 0.0))
        + 0.5 * _bounded_score(tier6d.get("distortion_components", {}).get("contamination_containment_score", 0.0))
    )

    risk_register_score = _bounded_score(
        0.2 * structural_risk_score
        + 0.2 * propagation_risk_score
        + 0.15 * bottleneck_risk_score
        + 0.15 * contamination_risk_score
        + 0.15 * explainability_risk_score
        + 0.075 * _bounded_score(1.0 - remediation_readiness_score)
        + 0.075 * _bounded_score(1.0 - containment_feasibility_score)
    )

    risk_components = {
        "structural_risk_score": structural_risk_score,
        "propagation_risk_score": propagation_risk_score,
        "bottleneck_risk_score": bottleneck_risk_score,
        "contamination_risk_score": contamination_risk_score,
        "explainability_risk_score": explainability_risk_score,
        "remediation_readiness_score": remediation_readiness_score,
        "containment_feasibility_score": containment_feasibility_score,
    }

    node_count = int(tier6c.get("diagnostics", {}).get("node_count", 0))
    edge_count = int(tier6c.get("diagnostics", {}).get("edge_count", 0))
    is_empty = bool(tier6c.get("diagnostics", {}).get("is_empty", False))

    risk_labels: List[str] = []
    if is_empty or node_count == 0 or edge_count == 0:
        risk_labels.append("insufficient_structure")
    if structural_risk_score >= 0.55:
        risk_labels.append("elevated_structural_risk")
    if propagation_risk_score >= 0.55:
        risk_labels.append("elevated_propagation_risk")
    if bottleneck_risk_score >= 0.55:
        risk_labels.append("elevated_bottleneck_risk")
    if contamination_risk_score >= 0.55:
        risk_labels.append("elevated_contamination_risk")
    if explainability_risk_score >= 0.40:
        risk_labels.append("elevated_explainability_risk")
    if remediation_readiness_score < 0.60:
        risk_labels.append("weak_remediation_readiness")
    if containment_feasibility_score < 0.45:
        risk_labels.append("weak_containment_feasibility")
    if not risk_labels:
        risk_labels.append("structurally_stable")
    risk_labels = sorted(set(risk_labels))

    risk_inventory = [
        {"risk_id": "risk_bottleneck_dependency", "risk_type": "bottleneck_dependency", "severity_score": bottleneck_risk_score, "source_tiers": ["tier6c"], "diagnostic_label": _risk_label(bottleneck_risk_score)},
        {"risk_id": "risk_contamination", "risk_type": "contamination_risk", "severity_score": contamination_risk_score, "source_tiers": ["tier6d"], "diagnostic_label": _risk_label(contamination_risk_score)},
        {"risk_id": "risk_contradictory_evidence", "risk_type": "contradictory_evidence", "severity_score": _bounded_score(1.0 if int(tier6d.get("diagnostics", {}).get("contradictory_edge_count", 0)) > 0 else 0.0), "source_tiers": ["tier6d", "tier6e"], "diagnostic_label": _risk_label(_bounded_score(1.0 if int(tier6d.get("diagnostics", {}).get("contradictory_edge_count", 0)) > 0 else 0.0))},
        {"risk_id": "risk_explainability_gap", "risk_type": "explainability_gap", "severity_score": explainability_risk_score, "source_tiers": ["tier6e"], "diagnostic_label": _risk_label(explainability_risk_score)},
        {"risk_id": "risk_fragmentation", "risk_type": "fragmentation_risk", "severity_score": _bounded_score(1.0 - _bounded_score(tier6d.get("distortion_components", {}).get("fragmentation_resilience_score", 0.0))), "source_tiers": ["tier6d"], "diagnostic_label": _risk_label(_bounded_score(1.0 - _bounded_score(tier6d.get("distortion_components", {}).get("fragmentation_resilience_score", 0.0))))},
        {"risk_id": "risk_isolated_structure", "risk_type": "isolated_structure", "severity_score": _bounded_score(1.0 if edge_count == 0 and node_count > 0 else 0.0), "source_tiers": ["tier6c"], "diagnostic_label": _risk_label(_bounded_score(1.0 if edge_count == 0 and node_count > 0 else 0.0))},
        {"risk_id": "risk_propagation_instability", "risk_type": "propagation_instability", "severity_score": propagation_risk_score, "source_tiers": ["tier6b"], "diagnostic_label": _risk_label(propagation_risk_score)},
        {"risk_id": "risk_structural_weakness", "risk_type": "structural_weakness", "severity_score": structural_risk_score, "source_tiers": ["tier6a"], "diagnostic_label": _risk_label(structural_risk_score)},
        {"risk_id": "risk_weak_traceability", "risk_type": "weak_traceability", "severity_score": _bounded_score(1.0 - _bounded_score(tier6b.get("reliability_components", {}).get("causal_traceability_score", 0.0))), "source_tiers": ["tier6b", "tier6e"], "diagnostic_label": _risk_label(_bounded_score(1.0 - _bounded_score(tier6b.get("reliability_components", {}).get("causal_traceability_score", 0.0))))},
    ]
    risk_inventory = sorted(risk_inventory, key=lambda x: x["risk_id"])

    remediation_priorities = [
        {"remediation_id": "remediate_connectivity", "target_issue": "improve_connectivity", "priority_score": structural_risk_score, "related_risks": ["risk_isolated_structure", "risk_structural_weakness"], "diagnostic_label": _priority_label(structural_risk_score)},
        {"remediation_id": "remediate_contamination", "target_issue": "reduce_contamination", "priority_score": contamination_risk_score, "related_risks": ["risk_contamination"], "diagnostic_label": _priority_label(contamination_risk_score)},
        {"remediation_id": "remediate_evidence_consistency", "target_issue": "improve_evidence_consistency", "priority_score": _bounded_score(max(explainability_risk_score, _bounded_score(1.0 - remediation_readiness_score))), "related_risks": ["risk_contradictory_evidence", "risk_explainability_gap"], "diagnostic_label": _priority_label(_bounded_score(max(explainability_risk_score, _bounded_score(1.0 - remediation_readiness_score))))},
        {"remediation_id": "remediate_metadata", "target_issue": "improve_metadata_completeness", "priority_score": _bounded_score(1.0 - remediation_readiness_score), "related_risks": ["risk_explainability_gap", "risk_weak_traceability"], "diagnostic_label": _priority_label(_bounded_score(1.0 - remediation_readiness_score))},
        {"remediation_id": "remediate_propagation", "target_issue": "stabilize_propagation", "priority_score": propagation_risk_score, "related_risks": ["risk_propagation_instability", "risk_fragmentation"], "diagnostic_label": _priority_label(propagation_risk_score)},
        {"remediation_id": "remediate_structural_alignment", "target_issue": "improve_structural_alignment", "priority_score": _bounded_score(max(structural_risk_score, bottleneck_risk_score)), "related_risks": ["risk_structural_weakness", "risk_bottleneck_dependency"], "diagnostic_label": _priority_label(_bounded_score(max(structural_risk_score, bottleneck_risk_score)))},
        {"remediation_id": "remediate_traceability", "target_issue": "improve_traceability", "priority_score": _bounded_score(1.0 - _bounded_score(tier6b.get("reliability_components", {}).get("causal_traceability_score", 0.0))), "related_risks": ["risk_weak_traceability"], "diagnostic_label": _priority_label(_bounded_score(1.0 - _bounded_score(tier6b.get("reliability_components", {}).get("causal_traceability_score", 0.0))))},
        {"remediation_id": "remediate_bottlenecks", "target_issue": "reduce_bottleneck_dependency", "priority_score": bottleneck_risk_score, "related_risks": ["risk_bottleneck_dependency"], "diagnostic_label": _priority_label(bottleneck_risk_score)},
    ]
    remediation_priorities = sorted(remediation_priorities, key=lambda x: x["remediation_id"])

    containment_opportunities = [
        {"containment_id": "contain_contamination", "containment_target": "isolate_contaminated_paths", "containment_score": contamination_risk_score, "diagnostic_label": _containment_label(contamination_risk_score)},
        {"containment_id": "contain_contradictions", "containment_target": "contain_contradictory_edges", "containment_score": _bounded_score(1.0 if int(tier6d.get("diagnostics", {}).get("contradictory_edge_count", 0)) > 0 else 0.0), "diagnostic_label": _containment_label(_bounded_score(1.0 if int(tier6d.get("diagnostics", {}).get("contradictory_edge_count", 0)) > 0 else 0.0))},
        {"containment_id": "contain_dependency", "containment_target": "reduce_dependency_exposure", "containment_score": bottleneck_risk_score, "diagnostic_label": _containment_label(bottleneck_risk_score)},
        {"containment_id": "contain_fragmentation", "containment_target": "contain_fragmented_propagation", "containment_score": _bounded_score(1.0 - _bounded_score(tier6d.get("distortion_components", {}).get("fragmentation_resilience_score", 0.0))), "diagnostic_label": _containment_label(_bounded_score(1.0 - _bounded_score(tier6d.get("distortion_components", {}).get("fragmentation_resilience_score", 0.0))))},
        {"containment_id": "contain_segmentation", "containment_target": "improve_structural_segmentation", "containment_score": _bounded_score(max(structural_risk_score, propagation_risk_score)), "diagnostic_label": _containment_label(_bounded_score(max(structural_risk_score, propagation_risk_score)))},
        {"containment_id": "contain_unstable_nodes", "containment_target": "isolate_unstable_nodes", "containment_score": propagation_risk_score, "diagnostic_label": _containment_label(propagation_risk_score)},
    ]
    containment_opportunities = sorted(containment_opportunities, key=lambda x: x["containment_id"])

    dependency_exposure_summary = {
        "high_dependency_nodes": int(tier6c.get("diagnostics", {}).get("high_bottleneck_node_count", 0)),
        "high_dependency_edges": int(tier6c.get("diagnostics", {}).get("critical_path_count", 0)),
        "fragmented_regions_detected": int(tier6d.get("diagnostics", {}).get("fragmented_edge_count", 0)),
        "contaminated_regions_detected": int(tier6d.get("diagnostics", {}).get("contaminated_edge_count", 0)),
        "contradictory_regions_detected": int(tier6d.get("diagnostics", {}).get("contradictory_edge_count", 0)),
    }

    structural_stabilization_summary = {
        "stabilization_candidates": sorted([x["target_issue"] for x in remediation_priorities if x["priority_score"] >= 0.65]),
        "traceability_improvement_candidates": sorted([x["remediation_id"] for x in remediation_priorities if x["target_issue"] in {"improve_traceability", "improve_metadata_completeness", "improve_evidence_consistency"} and x["priority_score"] >= 0.4]),
        "connectivity_improvement_candidates": sorted([x["remediation_id"] for x in remediation_priorities if x["target_issue"] in {"improve_connectivity", "improve_structural_alignment"} and x["priority_score"] >= 0.4]),
        "contamination_reduction_candidates": sorted([x["remediation_id"] for x in remediation_priorities if x["target_issue"] == "reduce_contamination" and x["priority_score"] >= 0.4]),
    }

    critical_risk_count = sum(1 for x in risk_inventory if x["diagnostic_label"] == "critical_risk")
    failure_modes = set(tier6b.get("transmission_failure_modes", [])) | set(tier6c.get("path_failure_modes", [])) | set(tier6d.get("distortion_failure_modes", []))
    is_structurally_stable = risk_labels == ["structurally_stable"]

    status = "success"
    if "insufficient_structure" in risk_labels:
        status = "insufficient_structure"
    elif not is_structurally_stable:
        status = "completed_with_findings"

    diagnostics = {
        "risk_count": len(risk_inventory),
        "critical_risk_count": critical_risk_count,
        "remediation_count": len(remediation_priorities),
        "containment_count": len(containment_opportunities),
        "failure_mode_count": len(failure_modes),
        "is_empty": is_empty,
        "is_structurally_stable": is_structurally_stable,
    }

    explanation = (
        f"Transmission risk register completed: status={status}; risk_register={risk_register_score}; "
        f"primary_label={risk_labels[0]}; risks={len(risk_inventory)}; remediations={len(remediation_priorities)}; "
        f"containment_candidates={len(containment_opportunities)}."
    )

    result = {
        "status": status,
        "risk_register_score": risk_register_score,
        "risk_components": risk_components,
        "risk_labels": risk_labels,
        "risk_inventory": risk_inventory,
        "remediation_priorities": remediation_priorities,
        "containment_opportunities": containment_opportunities,
        "dependency_exposure_summary": dependency_exposure_summary,
        "structural_stabilization_summary": structural_stabilization_summary,
        "diagnostics": diagnostics,
        "explanation": explanation,
    }
    result["checksum"] = stable_checksum(result, prefix="tier6f")
    return result
