"""Tier 6E deterministic transmission explainability and structural evidence attribution."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from transmission_layers.intelligence.tier6.propagation_distortion_diagnostics import assess_propagation_distortion_diagnostics
from transmission_layers.intelligence.tier6.structural_signal_quality import assess_structural_signal_quality
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


def _evidence_label(score: float) -> str:
    if score >= 0.75:
        return "strong_evidence"
    if score >= 0.50:
        return "moderate_evidence"
    if score > 0.0:
        return "weak_evidence"
    return "missing_evidence"


def assess_transmission_explainability(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}

    tier6a = assess_structural_signal_quality(topology_view)
    tier6b = assess_transmission_reliability_diagnostics(topology_view)
    tier6c = assess_transmission_path_integrity(topology_view)
    tier6d = assess_propagation_distortion_diagnostics(topology_view)

    signal_evidence_score = _bounded_score(tier6a.get("signal_quality_score", 0.0))
    reliability_evidence_score = _bounded_score(tier6b.get("transmission_reliability_score", 0.0))
    path_evidence_score = _bounded_score(tier6c.get("path_integrity_score", 0.0))
    distortion_evidence_score = _bounded_score(tier6d.get("propagation_integrity_score", 0.0))

    contradictory_count = int(tier6d.get("diagnostics", {}).get("contradictory_edge_count", 0))
    consistency_penalty = 0.35 if contradictory_count > 0 else 0.0
    evidence_consistency_score = _bounded_score(1.0 - consistency_penalty)

    completeness_inputs = [signal_evidence_score, reliability_evidence_score, path_evidence_score, distortion_evidence_score]
    attribution_completeness_score = _bounded_score(sum(1.0 for x in completeness_inputs if x > 0.0) / 4.0)

    explainability_score = _bounded_score(
        0.20 * signal_evidence_score
        + 0.20 * reliability_evidence_score
        + 0.20 * path_evidence_score
        + 0.20 * distortion_evidence_score
        + 0.10 * attribution_completeness_score
        + 0.10 * evidence_consistency_score
    )

    primary_evidence = [
        {
            "evidence_id": "tier6a_signal_quality",
            "source_tier": "tier6a",
            "evidence_type": "signal_quality",
            "evidence_score": signal_evidence_score,
            "diagnostic_label": _evidence_label(signal_evidence_score),
        },
        {
            "evidence_id": "tier6b_reliability_component",
            "source_tier": "tier6b",
            "evidence_type": "reliability_component",
            "evidence_score": reliability_evidence_score,
            "diagnostic_label": _evidence_label(reliability_evidence_score),
        },
        {
            "evidence_id": "tier6c_path_integrity",
            "source_tier": "tier6c",
            "evidence_type": "path_integrity",
            "evidence_score": path_evidence_score,
            "diagnostic_label": _evidence_label(path_evidence_score),
        },
        {
            "evidence_id": "tier6d_distortion_detection",
            "source_tier": "tier6d",
            "evidence_type": "distortion_detection",
            "evidence_score": distortion_evidence_score,
            "diagnostic_label": _evidence_label(distortion_evidence_score),
        },
    ]

    supporting_evidence = [
        {
            "evidence_id": "tier6c_bottleneck_attribution",
            "source_tier": "tier6c",
            "supports": "tier6c_path_integrity",
            "support_score": _bounded_score(tier6c.get("path_components", {}).get("bottleneck_resilience_score", 0.0)),
            "diagnostic_label": "supports_primary",
        },
        {
            "evidence_id": "tier6d_contamination_support",
            "source_tier": "tier6d",
            "supports": "tier6d_distortion_detection",
            "support_score": _bounded_score(tier6d.get("distortion_components", {}).get("contamination_containment_score", 0.0)),
            "diagnostic_label": "supports_primary",
        },
    ]
    for item in supporting_evidence:
        score = item["support_score"]
        if score == 0.0:
            item["diagnostic_label"] = "missing_support"
        elif score < 0.45:
            item["diagnostic_label"] = "weak_support"

    contradictory_evidence = [
        {
            "evidence_id": "tier6d_contradictory_transmission",
            "source_tier": "tier6d",
            "contradicts": "tier6b_reliability_component",
            "contradiction_score": _bounded_score(1.0 if contradictory_count > 0 else 0.0),
            "diagnostic_label": "contradiction_detected" if contradictory_count > 0 else "no_contradiction",
        }
    ]

    explainability_labels: List[str] = []
    if attribution_completeness_score == 0.0:
        explainability_labels.append("insufficient_evidence")
    if signal_evidence_score < 0.45:
        explainability_labels.append("weak_signal_evidence")
    if reliability_evidence_score < 0.45:
        explainability_labels.append("weak_reliability_evidence")
    if path_evidence_score < 0.45:
        explainability_labels.append("weak_path_evidence")
    if distortion_evidence_score < 0.55:
        explainability_labels.append("weak_distortion_evidence")
    if contradictory_count > 0:
        explainability_labels.append("contradictory_structural_evidence")
    if attribution_completeness_score < 1.0:
        explainability_labels.append("incomplete_attribution")
    if not explainability_labels:
        explainability_labels.append("structurally_explainable")
    explainability_labels = sorted(set(explainability_labels))

    structural_attribution = []
    if attribution_completeness_score == 0.0:
        structural_attribution.append({"attribution_id": "cause_insufficient_structure", "structural_cause": "insufficient_structure", "source_tiers": ["tier6a", "tier6b", "tier6c", "tier6d"], "attribution_score": 1.0, "diagnostic_label": "primary_cause"})
    if signal_evidence_score < 0.45:
        structural_attribution.append({"attribution_id": "cause_weak_signal", "structural_cause": "weak_signal_quality", "source_tiers": ["tier6a"], "attribution_score": _bounded_score(1.0 - signal_evidence_score), "diagnostic_label": "contributing_cause"})
    if reliability_evidence_score < 0.45:
        structural_attribution.append({"attribution_id": "cause_weak_reliability", "structural_cause": "weak_reliability", "source_tiers": ["tier6b"], "attribution_score": _bounded_score(1.0 - reliability_evidence_score), "diagnostic_label": "contributing_cause"})
    if any("bottleneck" in x for x in tier6c.get("path_failure_modes", [])):
        structural_attribution.append({"attribution_id": "cause_path_bottleneck", "structural_cause": "path_bottleneck", "source_tiers": ["tier6c"], "attribution_score": _bounded_score(1.0 - tier6c.get("path_components", {}).get("bottleneck_resilience_score", 0.0)), "diagnostic_label": "contributing_cause"})
    if any(x in tier6d.get("distortion_labels", []) for x in ["distorted_signal_flow", "fragmented_propagation"]):
        structural_attribution.append({"attribution_id": "cause_distorted_propagation", "structural_cause": "distorted_propagation", "source_tiers": ["tier6d"], "attribution_score": _bounded_score(1.0 - distortion_evidence_score), "diagnostic_label": "contributing_cause"})
    if "contaminated_transmission" in tier6d.get("distortion_labels", []):
        structural_attribution.append({"attribution_id": "cause_contaminated_transmission", "structural_cause": "contaminated_transmission", "source_tiers": ["tier6d"], "attribution_score": _bounded_score(1.0 - tier6d.get("distortion_components", {}).get("contamination_containment_score", 0.0)), "diagnostic_label": "contributing_cause"})
    if "weak_causal_traceability" in tier6b.get("transmission_failure_modes", []):
        structural_attribution.append({"attribution_id": "cause_weak_traceability", "structural_cause": "weak_traceability", "source_tiers": ["tier6b"], "attribution_score": _bounded_score(1.0 - tier6b.get("reliability_components", {}).get("causal_traceability_score", 0.0)), "diagnostic_label": "weak_cause"})
    if contradictory_count > 0:
        structural_attribution.append({"attribution_id": "cause_contradictory_evidence", "structural_cause": "contradictory_evidence", "source_tiers": ["tier6d", "tier6b"], "attribution_score": 1.0, "diagnostic_label": "primary_cause"})
    if not structural_attribution:
        structural_attribution.append({"attribution_id": "cause_no_material_issue", "structural_cause": "no_material_issue_detected", "source_tiers": ["tier6a", "tier6b", "tier6c", "tier6d"], "attribution_score": _bounded_score(explainability_score), "diagnostic_label": "no_issue"})

    primary_evidence = sorted(primary_evidence, key=lambda x: x["evidence_id"])
    supporting_evidence = sorted(supporting_evidence, key=lambda x: x["evidence_id"])
    contradictory_evidence = sorted(contradictory_evidence, key=lambda x: x["evidence_id"])
    structural_attribution = sorted(structural_attribution, key=lambda x: x["attribution_id"])

    failure_modes = set(tier6b.get("transmission_failure_modes", [])) | set(tier6c.get("path_failure_modes", [])) | set(tier6d.get("distortion_failure_modes", []))

    is_empty = bool(tier6c.get("diagnostics", {}).get("is_empty", False))
    is_explainable = explainability_labels == ["structurally_explainable"]

    status = "success"
    missing_nodes = bool(tier6c.get("diagnostics", {}).get("node_count", 0) == 0)
    missing_edges = bool(tier6c.get("diagnostics", {}).get("edge_count", 0) == 0)
    if is_empty or missing_nodes or missing_edges:
        status = "insufficient_structure"
    elif not is_explainable:
        status = "completed_with_findings"

    diagnostics = {
        "primary_evidence_count": len(primary_evidence),
        "supporting_evidence_count": len(supporting_evidence),
        "contradictory_evidence_count": len(contradictory_evidence),
        "structural_attribution_count": len(structural_attribution),
        "failure_mode_count": len(failure_modes),
        "is_empty": is_empty,
        "is_explainable": is_explainable,
    }

    result = {
        "status": status,
        "explainability_score": explainability_score,
        "evidence_components": {
            "signal_evidence_score": signal_evidence_score,
            "reliability_evidence_score": reliability_evidence_score,
            "path_evidence_score": path_evidence_score,
            "distortion_evidence_score": distortion_evidence_score,
            "attribution_completeness_score": attribution_completeness_score,
            "evidence_consistency_score": evidence_consistency_score,
        },
        "explainability_labels": explainability_labels,
        "primary_evidence": primary_evidence,
        "supporting_evidence": supporting_evidence,
        "contradictory_evidence": contradictory_evidence,
        "structural_attribution": structural_attribution,
        "diagnostics": diagnostics,
        "explanation": f"Transmission explainability completed: status={status}; explainability={explainability_score}; primary_label={explainability_labels[0]}; primary_evidence={len(primary_evidence)}; attributions={len(structural_attribution)}; contradictions={len(contradictory_evidence)}.",
    }
    result["checksum"] = stable_checksum(result, prefix="tier6e")
    return result
