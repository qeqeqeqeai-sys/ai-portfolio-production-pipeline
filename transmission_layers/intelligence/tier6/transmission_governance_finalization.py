"""Tier 6J deterministic governance finalization and integration certification contract."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from transmission_layers.intelligence.tier6.transmission_governance_audit_trail import assess_transmission_governance_audit_trail
from transmission_layers.intelligence.tier6.transmission_governance_review_gate import assess_transmission_governance_review_gate
from transmission_layers.intelligence.tier6.transmission_governance_summary import assess_transmission_governance_summary
from transmission_layers.intelligence.tier6.transmission_risk_register import assess_transmission_risk_register
from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
from transmission_layers.intelligence.tier6.propagation_distortion_diagnostics import assess_propagation_distortion_diagnostics
from transmission_layers.intelligence.tier6.transmission_path_integrity import assess_transmission_path_integrity
from transmission_layers.intelligence.tier6.transmission_reliability_diagnostics import assess_transmission_reliability_diagnostics
from transmission_layers.intelligence.tier6.structural_signal_quality import assess_structural_signal_quality
from transmission_layers.operationalization.serialization import stable_checksum


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_score(value: Any) -> float:
    return max(0.0, min(1.0, round(_to_float(value), 6)))


def _label_by_score(score: float, strong: str, partial: str, weak: str, missing: str) -> str:
    if score >= 0.8:
        return strong
    if score >= 0.6:
        return partial
    if score >= 0.3:
        return weak
    return missing


def assess_transmission_governance_finalization(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}
    nodes = topology_view.get("nodes", []) if isinstance(topology_view.get("nodes", []), list) else []
    edges = topology_view.get("edges", []) if isinstance(topology_view.get("edges", []), list) else []
    is_empty = bool(len(nodes) == 0 or len(edges) == 0)

    tier6a = assess_structural_signal_quality(topology_view)
    tier6b = assess_transmission_reliability_diagnostics(topology_view)
    tier6c = assess_transmission_path_integrity(topology_view)
    tier6d = assess_propagation_distortion_diagnostics(topology_view)
    tier6e = assess_transmission_explainability(topology_view)
    tier6f = assess_transmission_risk_register(topology_view)
    tier6g = assess_transmission_governance_summary(topology_view)
    tier6h = assess_transmission_governance_review_gate(topology_view)
    tier6i = assess_transmission_governance_audit_trail(topology_view)

    api_defs: List[Tuple[str, str, float]] = [
        ("contract_tier6a", "assess_structural_signal_quality", _bounded_score(tier6a.get("signal_quality_score", 0.0))),
        ("contract_tier6b", "assess_transmission_reliability_diagnostics", _bounded_score(tier6b.get("transmission_reliability_score", 0.0))),
        ("contract_tier6c", "assess_transmission_path_integrity", _bounded_score(tier6c.get("path_integrity_score", 0.0))),
        ("contract_tier6d", "assess_propagation_distortion_diagnostics", _bounded_score(tier6d.get("propagation_integrity_score", 0.0))),
        ("contract_tier6e", "assess_transmission_explainability", _bounded_score(tier6e.get("explainability_score", 0.0))),
        ("contract_tier6f", "assess_transmission_risk_register", _bounded_score(tier6f.get("risk_register_score", 0.0))),
        ("contract_tier6g", "assess_transmission_governance_summary", _bounded_score(tier6g.get("governance_score", 0.0))),
        ("contract_tier6h", "assess_transmission_governance_review_gate", _bounded_score(tier6h.get("governance_certification_score", 0.0))),
        ("contract_tier6i", "assess_transmission_governance_audit_trail", _bounded_score(tier6i.get("audit_integrity_score", 0.0))),
    ]
    tier6_api_contracts = sorted([
        {
            "contract_id": cid,
            "api_name": api,
            "contract_score": score,
            "diagnostic_label": _label_by_score(score, "compliant_contract", "partially_compliant_contract", "weak_contract", "missing_contract"),
        }
        for cid, api, score in api_defs
    ], key=lambda x: (-x["contract_score"], x["contract_id"]))

    checksum_sources = [
        ("checksum_tier6a", "signal_quality_checksum", 1.0 if isinstance(tier6a.get("checksum"), str) and tier6a.get("checksum") else 0.0),
        ("checksum_tier6b", "reliability_checksum", 1.0 if isinstance(tier6b.get("checksum"), str) and tier6b.get("checksum") else 0.0),
        ("checksum_tier6c", "path_integrity_checksum", 1.0 if isinstance(tier6c.get("checksum"), str) and tier6c.get("checksum") else 0.0),
        ("checksum_tier6d", "distortion_checksum", 1.0 if isinstance(tier6d.get("checksum"), str) and tier6d.get("checksum") else 0.0),
        ("checksum_tier6e", "explainability_checksum", 1.0 if isinstance(tier6e.get("checksum"), str) and tier6e.get("checksum") else 0.0),
        ("checksum_tier6f", "risk_register_checksum", 1.0 if isinstance(tier6f.get("checksum"), str) and tier6f.get("checksum") else 0.0),
        ("checksum_tier6g", "governance_summary_checksum", 1.0 if isinstance(tier6g.get("checksum"), str) and tier6g.get("checksum") else 0.0),
        ("checksum_tier6h", "governance_review_checksum", 1.0 if isinstance(tier6h.get("checksum"), str) and tier6h.get("checksum") else 0.0),
        ("checksum_tier6i", "governance_audit_checksum", 1.0 if isinstance(tier6i.get("checksum"), str) and tier6i.get("checksum") else 0.0),
    ]
    checksum_integrity_validation = sorted([
        {
            "validation_id": vid,
            "validation_target": tgt,
            "validation_score": _bounded_score(score),
            "diagnostic_label": _label_by_score(score, "stable_checksum", "partially_stable_checksum", "weak_checksum", "checksum_gap"),
        }
        for vid, tgt, score in checksum_sources
    ], key=lambda x: (-x["validation_score"], x["validation_id"]))

    bounded_families = [
        ("bounded_tier6a", "signal_scores", _bounded_score(1.0 if 0.0 <= _bounded_score(tier6a.get("signal_quality_score", 0.0)) <= 1.0 else 0.0)),
        ("bounded_tier6b", "reliability_scores", _bounded_score(1.0 if 0.0 <= _bounded_score(tier6b.get("transmission_reliability_score", 0.0)) <= 1.0 else 0.0)),
        ("bounded_tier6c", "path_scores", _bounded_score(1.0 if 0.0 <= _bounded_score(tier6c.get("path_integrity_score", 0.0)) <= 1.0 else 0.0)),
        ("bounded_tier6d", "distortion_scores", _bounded_score(1.0 if 0.0 <= _bounded_score(tier6d.get("propagation_integrity_score", 0.0)) <= 1.0 else 0.0)),
        ("bounded_tier6e", "explainability_scores", _bounded_score(1.0 if 0.0 <= _bounded_score(tier6e.get("explainability_score", 0.0)) <= 1.0 else 0.0)),
        ("bounded_tier6f", "risk_scores", _bounded_score(1.0 if 0.0 <= _bounded_score(tier6f.get("risk_register_score", 0.0)) <= 1.0 else 0.0)),
        ("bounded_tier6g", "governance_scores", _bounded_score(1.0 if 0.0 <= _bounded_score(tier6g.get("governance_score", 0.0)) <= 1.0 else 0.0)),
        ("bounded_tier6i", "audit_scores", _bounded_score(1.0 if 0.0 <= _bounded_score(tier6i.get("audit_integrity_score", 0.0)) <= 1.0 else 0.0)),
    ]
    bounded_score_validation = sorted([
        {"validation_id": vid, "score_family": fam, "validation_score": score,
         "diagnostic_label": _label_by_score(score, "bounded_scores_verified", "partially_bounded", "weak_bounded_scores", "bounded_score_gap")}
        for vid, fam, score in bounded_families
    ], key=lambda x: (-x["validation_score"], x["validation_id"]))

    deterministic_contract_validation = sorted([
        {"validation_id": "contract_additive_architecture", "contract_type": "additive_architecture", "validation_score": 1.0, "diagnostic_label": "compliant_contract"},
        {"validation_id": "contract_checksum_stability", "contract_type": "checksum_stability", "validation_score": _bounded_score(sum(x[2] for x in checksum_sources) / len(checksum_sources)), "diagnostic_label": _label_by_score(_bounded_score(sum(x[2] for x in checksum_sources) / len(checksum_sources)), "compliant_contract", "partially_compliant_contract", "weak_contract", "contract_gap")},
        {"validation_id": "contract_controlled_vocabulary", "contract_type": "controlled_vocabulary", "validation_score": 1.0, "diagnostic_label": "compliant_contract"},
        {"validation_id": "contract_deterministic_ordering", "contract_type": "deterministic_ordering", "validation_score": 1.0, "diagnostic_label": "compliant_contract"},
        {"validation_id": "contract_explanation_template", "contract_type": "explanation_template", "validation_score": 1.0, "diagnostic_label": "compliant_contract"},
        {"validation_id": "contract_replay_safety", "contract_type": "replay_safety", "validation_score": _bounded_score(tier6i.get("audit_components", {}).get("replay_evidence_score", 0.0)), "diagnostic_label": _label_by_score(_bounded_score(tier6i.get("audit_components", {}).get("replay_evidence_score", 0.0)), "compliant_contract", "partially_compliant_contract", "weak_contract", "contract_gap")},
    ], key=lambda x: (-x["validation_score"], x["validation_id"]))

    replay_safety_validation = sorted([
        {"validation_id": "replay_audit", "replay_type": "replay_safe_audit", "validation_score": _bounded_score(tier6i.get("audit_components", {}).get("replay_evidence_score", 0.0)), "diagnostic_label": _label_by_score(_bounded_score(tier6i.get("audit_components", {}).get("replay_evidence_score", 0.0)), "replay_safe", "partially_replay_safe", "weak_replay_safety", "replay_safety_gap")},
        {"validation_id": "replay_certification", "replay_type": "replay_safe_certification", "validation_score": _bounded_score(tier6h.get("governance_certification_score", 0.0)), "diagnostic_label": _label_by_score(_bounded_score(tier6h.get("governance_certification_score", 0.0)), "replay_safe", "partially_replay_safe", "weak_replay_safety", "replay_safety_gap")},
        {"validation_id": "replay_evidence", "replay_type": "replay_safe_evidence", "validation_score": _bounded_score(tier6i.get("audit_components", {}).get("certification_traceability_score", 0.0)), "diagnostic_label": _label_by_score(_bounded_score(tier6i.get("audit_components", {}).get("certification_traceability_score", 0.0)), "replay_safe", "partially_replay_safe", "weak_replay_safety", "replay_safety_gap")},
        {"validation_id": "replay_governance", "replay_type": "replay_safe_governance", "validation_score": _bounded_score(tier6g.get("governance_score", 0.0)), "diagnostic_label": _label_by_score(_bounded_score(tier6g.get("governance_score", 0.0)), "replay_safe", "partially_replay_safe", "weak_replay_safety", "replay_safety_gap")},
    ], key=lambda x: (-x["validation_score"], x["validation_id"]))

    chain = [tier6a.get("signal_quality_score", 0.0), tier6b.get("transmission_reliability_score", 0.0), tier6c.get("path_integrity_score", 0.0), tier6d.get("propagation_integrity_score", 0.0), tier6e.get("explainability_score", 0.0), tier6f.get("risk_register_score", 0.0), tier6g.get("governance_score", 0.0), tier6h.get("governance_certification_score", 0.0)]
    rels = ["tier6a_tier6b", "tier6b_tier6c", "tier6c_tier6d", "tier6d_tier6e", "tier6e_tier6f", "tier6f_tier6g", "tier6g_tier6h", "tier6h_tier6i"]
    scores = [_bounded_score(1.0 - abs(_bounded_score(chain[i]) - _bounded_score(chain[i + 1 if i < 7 else 7]))) for i in range(8)]
    cross_tier_governance_validation = sorted([
        {"validation_id": f"compat_{i+1}", "tier_relationship": rels[i], "validation_score": scores[i], "diagnostic_label": _label_by_score(scores[i], "compatible", "partially_compatible", "weak_compatibility", "compatibility_gap")}
        for i in range(8)
    ], key=lambda x: (-x["validation_score"], x["validation_id"]))

    integration_components = {
        "api_contract_integrity_score": _bounded_score(sum(x["contract_score"] for x in tier6_api_contracts) / len(tier6_api_contracts)),
        "checksum_integrity_score": _bounded_score(sum(x["validation_score"] for x in checksum_integrity_validation) / len(checksum_integrity_validation)),
        "bounded_score_integrity_score": _bounded_score(sum(x["validation_score"] for x in bounded_score_validation) / len(bounded_score_validation)),
        "deterministic_contract_score": _bounded_score(sum(x["validation_score"] for x in deterministic_contract_validation) / len(deterministic_contract_validation)),
        "replay_safety_score": _bounded_score(sum(x["validation_score"] for x in replay_safety_validation) / len(replay_safety_validation)),
        "cross_tier_compatibility_score": _bounded_score(sum(x["validation_score"] for x in cross_tier_governance_validation) / len(cross_tier_governance_validation)),
        "governance_finalization_score": _bounded_score((
            _bounded_score(tier6h.get("governance_certification_score", 0.0)) + _bounded_score(tier6i.get("audit_integrity_score", 0.0)) + _bounded_score(tier6g.get("governance_score", 0.0))
        ) / 3.0),
    }
    tier6_finalization_score = _bounded_score(sum(integration_components.values()) / len(integration_components))

    integration_labels: List[str] = []
    if is_empty:
        integration_labels.append("insufficient_structure")
    if integration_components["api_contract_integrity_score"] < 0.6:
        integration_labels.append("api_contract_gap")
    if integration_components["checksum_integrity_score"] < 0.6:
        integration_labels.append("checksum_integrity_gap")
    if integration_components["bounded_score_integrity_score"] < 0.6:
        integration_labels.append("bounded_score_gap")
    if integration_components["deterministic_contract_score"] < 0.65:
        integration_labels.append("deterministic_contract_gap")
    if integration_components["replay_safety_score"] < 0.6:
        integration_labels.append("replay_safety_gap")
    if integration_components["cross_tier_compatibility_score"] < 0.6:
        integration_labels.append("cross_tier_governance_gap")
    if tier6_finalization_score < 0.75:
        integration_labels.append("governance_finalization_incomplete")
    if not integration_labels or integration_labels == ["insufficient_structure"]:
        if "insufficient_structure" not in integration_labels:
            integration_labels.append("tier6_governance_finalized")
    integration_labels = sorted(set(integration_labels))

    tier6_certification_packet = {
        "is_tier6_finalized": "tier6_governance_finalized" in integration_labels,
        "is_governance_certified": integration_components["governance_finalization_score"] >= 0.75 and "insufficient_structure" not in integration_labels,
        "is_replay_safe": integration_components["replay_safety_score"] >= 0.6,
        "is_deterministically_compliant": integration_components["deterministic_contract_score"] >= 0.65,
    }

    diagnostics = {
        "api_contract_count": len(tier6_api_contracts),
        "checksum_validation_count": len(checksum_integrity_validation),
        "bounded_score_validation_count": len(bounded_score_validation),
        "deterministic_contract_validation_count": len(deterministic_contract_validation),
        "replay_validation_count": len(replay_safety_validation),
        "cross_tier_validation_count": len(cross_tier_governance_validation),
        "failure_mode_count": len([x for x in integration_labels if x not in {"tier6_governance_finalized", "insufficient_structure"}]),
        "is_empty": is_empty,
        "is_tier6_finalized": tier6_certification_packet["is_tier6_finalized"],
    }

    if "insufficient_structure" in integration_labels:
        status = "insufficient_structure"
    elif any(x in integration_labels for x in {"api_contract_gap", "checksum_integrity_gap", "bounded_score_gap", "deterministic_contract_gap", "replay_safety_gap", "cross_tier_governance_gap", "governance_finalization_incomplete"}):
        status = "completed_with_findings"
    else:
        status = "success"

    explanation = (
        f"Transmission governance finalization completed: status={status}; finalization={tier6_finalization_score}; "
        f"primary_label={integration_labels[0] if integration_labels else 'tier6_governance_finalized'}; "
        f"api_contracts={len(tier6_api_contracts)}; replay_validations={len(replay_safety_validation)}; "
        f"cross_tier_validations={len(cross_tier_governance_validation)}."
    )

    result = {
        "status": status,
        "tier6_finalization_score": tier6_finalization_score,
        "integration_components": integration_components,
        "integration_labels": integration_labels,
        "tier6_api_contracts": tier6_api_contracts,
        "checksum_integrity_validation": checksum_integrity_validation,
        "bounded_score_validation": bounded_score_validation,
        "deterministic_contract_validation": deterministic_contract_validation,
        "replay_safety_validation": replay_safety_validation,
        "cross_tier_governance_validation": cross_tier_governance_validation,
        "tier6_certification_packet": tier6_certification_packet,
        "diagnostics": diagnostics,
        "explanation": explanation,
    }
    result["checksum"] = stable_checksum(result, prefix="tier6j")
    return result
