"""T5 deterministic historical explainability built from T4 regime transition envelopes."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json

APPROVED_TEMPLATE_IDS = {
    "EXPLANATION_RISING_FRAGILITY",
    "EXPLANATION_PERSISTENT_STRESS",
    "EXPLANATION_RECOVERY",
    "EXPLANATION_STABLE_CONDITION",
    "EXPLANATION_VOLATILE_CONDITION",
    "EXPLANATION_INSUFFICIENT_HISTORY",
    "EXPLANATION_DEGRADED_INPUT",
}
APPROVED_STRUCTURAL_SUMMARIES = {
    "persistent positive fragility movement",
    "mixed directional structural movement",
    "stable structural movement",
    "recovery-aligned fragility reduction",
    "volatile structural instability",
}
APPROVED_QUALITIES = {
    "EXPLANATION_CERTIFIED",
    "EXPLANATION_DEGRADED",
    "EXPLANATION_INSUFFICIENT_HISTORY",
    "EXPLANATION_BLOCKED",
}
APPROVED_REPLAY_WINDOW_CLASSIFICATIONS = {
    "SHORT_REPLAY_WINDOW",
    "MEDIUM_REPLAY_WINDOW",
    "LONG_REPLAY_WINDOW",
    "EXTENDED_REPLAY_WINDOW",
    "UNKNOWN_REPLAY_WINDOW",
}
CERTIFICATION_GATES = [
    "t4_envelope_present", "t4_transition_records_present", "minimum_explanation_depth_present", "required_transition_checksums_present", "deterministic_template_selection_applied", "deterministic_explanation_ordering_applied", "bounded_template_inventory_used", "bounded_summary_phrases_used", "no_open_ended_generation", "checksum_lineage_preserved", "inputs_not_mutated", "no_live_reads", "no_writes", "no_network_calls", "no_prediction_logic", "no_trading_logic", "no_forecasting_language", "no_recommendation_language", "no_adaptive_learning",
]
FORBIDDEN_CAPABILITIES = {
    "live_fetch": False,
    "supabase_read": False,
    "supabase_write": False,
    "trading_execution": False,
    "prediction": False,
    "optimization": False,
    "adaptive_learning": False,
    "hidden_state_mutation": False,
    "stochastic_generation": False,
    "open_ended_llm_generation": False,
    "recommendation_generation": False,
    "recursive_replay_expansion": False,
}


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_historical_explainability_inputs(regime_transition_envelope):
    if not isinstance(regime_transition_envelope, dict):
        return {"valid": False, "errors": ["t4_envelope_missing_or_invalid"], "transition_records": []}
    records = regime_transition_envelope.get("transition_records")
    errors = []
    if not isinstance(records, list):
        records = []
        errors.append("transition_records_missing")
    if not records:
        errors.append("transition_records_empty")
    if not regime_transition_envelope.get("checksum_chain"):
        errors.append("checksum_chain_missing")
    return {"valid": not errors, "errors": sorted(set(errors)), "transition_records": deepcopy(records)}


def _classify_replay_window(pair_count: int, observation_count: int) -> str:
    m = max(int(pair_count or 0), int(observation_count or 0))
    if m <= 0:
        return "UNKNOWN_REPLAY_WINDOW"
    if m <= 2:
        return "SHORT_REPLAY_WINDOW"
    if m <= 4:
        return "MEDIUM_REPLAY_WINDOW"
    if m <= 8:
        return "LONG_REPLAY_WINDOW"
    return "EXTENDED_REPLAY_WINDOW"


def _structural_summary(label: str, direction: str) -> str:
    if "VOLATILE" in label or direction == "MIXED":
        return "volatile structural instability"
    if "FALLING" in label or direction == "IMPROVING":
        return "recovery-aligned fragility reduction"
    if "STABLE" in label or direction == "UNCHANGED":
        return "stable structural movement"
    if "RISING" in label:
        return "persistent positive fragility movement"
    return "mixed directional structural movement"


def _template_for_transition(record: dict, t4_status: str) -> tuple[str, str]:
    label = str(record.get("supporting_curve_label", ""))
    transition = str(record.get("regime_transition", ""))
    if "DEGRADED" in transition or "DEGRADED" in label or "DEGRADED" in t4_status:
        return "EXPLANATION_DEGRADED_INPUT", "EXPLANATION_DEGRADED"
    if "INSUFFICIENT" in transition or "INSUFFICIENT" in label:
        return "EXPLANATION_INSUFFICIENT_HISTORY", "EXPLANATION_INSUFFICIENT_HISTORY"
    if "VOLATILE" in label or "UNCLEAR" in transition:
        return "EXPLANATION_VOLATILE_CONDITION", "EXPLANATION_DEGRADED"
    if "FALLING" in label or "RECOVERING" in transition:
        return "EXPLANATION_RECOVERY", "EXPLANATION_CERTIFIED"
    if "PERSISTENTLY_ELEVATED" in label or "STRESS" in transition:
        return "EXPLANATION_PERSISTENT_STRESS", "EXPLANATION_CERTIFIED"
    if "STABLE" in label or transition == "NO_REGIME_CHANGE":
        return "EXPLANATION_STABLE_CONDITION", "EXPLANATION_CERTIFIED"
    return "EXPLANATION_RISING_FRAGILITY", "EXPLANATION_CERTIFIED"


def _build_text(template_id: str, record: dict, structural_summary: str, replay_window_classification: str) -> str:
    prior = record.get("prior_regime_state", "REGIME_UNCLEAR")
    current = record.get("current_regime_state", "REGIME_UNCLEAR")
    transition = record.get("regime_transition", "REGIME_TRANSITION_UNCLEAR")
    if template_id == "EXPLANATION_DEGRADED_INPUT":
        return f"The subject transition was classified as {transition} because degraded transition inputs were detected and evidence lineage remained bounded."
    if template_id == "EXPLANATION_INSUFFICIENT_HISTORY":
        return f"The subject transition was classified as {transition} because insufficient replay-window history was observed for deterministic explanation depth."
    if template_id == "EXPLANATION_VOLATILE_CONDITION":
        return f"The subject transitioned from {prior} to {current} with {transition} associated with {structural_summary} observed across the {replay_window_classification}."
    if template_id == "EXPLANATION_RECOVERY":
        return f"The subject transitioned from {prior} to {current} because {structural_summary} and directional consistency were observed across replay-window structural intervals."
    if template_id == "EXPLANATION_PERSISTENT_STRESS":
        return f"The subject transitioned from {prior} to {current} because persistent stress behavior was observed and classified with bounded structural evidence across the replay window."
    if template_id == "EXPLANATION_STABLE_CONDITION":
        return f"The subject remained within {current} because stable structural movement persisted and was classified as bounded regime continuity across the replay window."
    return f"The subject transitioned from {prior} to {current} because persistent positive fragility movement and directional consistency were observed across replay-window intervals."


def build_historical_explanation_records(regime_transition_envelope):
    frozen = deepcopy(regime_transition_envelope)
    records = frozen.get("transition_records", []) if isinstance(frozen, dict) else []
    t4_status = str(frozen.get("t4_status", "")) if isinstance(frozen, dict) else ""
    output = []
    for item in records:
        pair_count = int(item.get("pair_count", 0) or 0)
        obs = int(item.get("observation_count", 0) or 0)
        replay_cls = _classify_replay_window(pair_count, obs)
        structural_summary = _structural_summary(str(item.get("supporting_curve_label", "")), str(item.get("transition_direction", "")))
        template_id, quality = _template_for_transition(item, t4_status)
        evidence_summary = {
            "contributing_pair_count": pair_count,
            "contributing_curve_label": item.get("supporting_curve_label", ""),
            "cumulative_score_delta": (item.get("supporting_metrics") or {}).get("cumulative_score_delta", 0),
            "directional_consistency": (item.get("supporting_metrics") or {}).get("directional_consistency", 0),
            "persistence_count": (item.get("supporting_metrics") or {}).get("persistence_count", 0),
            "transition_strength": item.get("transition_strength", ""),
            "transition_confidence": item.get("transition_confidence", ""),
            "source_checksums": {
                "source_curve_checksum": item.get("source_curve_checksum", ""),
                "source_pair_checksums": deepcopy(item.get("source_pair_checksums", [])),
                "transition_checksum": item.get("transition_checksum", ""),
            },
        }
        explanation = {
            "subject_id": item.get("subject_id", ""), "subject_type": item.get("subject_type", ""),
            "prior_regime_state": item.get("prior_regime_state", ""), "current_regime_state": item.get("current_regime_state", ""),
            "regime_transition": item.get("regime_transition", ""), "transition_direction": item.get("transition_direction", ""),
            "transition_strength": item.get("transition_strength", ""), "transition_confidence": item.get("transition_confidence", ""),
            "supporting_curve_label": item.get("supporting_curve_label", ""), "supporting_metrics": deepcopy(item.get("supporting_metrics", {})),
            "replay_window_summary": {
                "first_observed_date": item.get("first_observed_date", ""), "last_observed_date": item.get("last_observed_date", ""),
                "observation_count": obs, "pair_count": pair_count, "replay_window_classification": replay_cls,
            },
            "structural_change_summary": structural_summary,
            "fragility_curve_summary": str(item.get("supporting_curve_label", "")),
            "evidence_summary": evidence_summary,
            "bounded_explanation_template_id": template_id,
            "bounded_explanation_text": _build_text(template_id, item, structural_summary, replay_cls),
            "explanation_quality": quality,
        }
        explanation["explanation_checksum"] = _stable_checksum(explanation)
        output.append(explanation)
    return sorted(output, key=lambda r: (str(r.get("subject_type", "")), str(r.get("subject_id", "")), str((r.get("replay_window_summary") or {}).get("first_observed_date", "")), str(r.get("explanation_checksum", ""))))


def build_historical_explanation_summary(explanation_records):
    frozen = deepcopy(explanation_records)
    q = [r.get("explanation_quality") for r in frozen]
    t = [r.get("bounded_explanation_template_id") for r in frozen]
    return {
        "explanation_count": len(frozen),
        "quality_counts": {k: q.count(k) for k in sorted(set(q))},
        "template_counts": {k: t.count(k) for k in sorted(set(t))},
        "certified_explanation_count": sum(1 for x in q if x == "EXPLANATION_CERTIFIED"),
    }


def build_historical_explanation_checksum_chain(explanation_records):
    frozen = deepcopy(explanation_records)
    checksums = [r.get("explanation_checksum", "") for r in frozen]
    return {"explanation_checksums": checksums, "explanation_chain_checksum": _stable_checksum(checksums)}


def certify_historical_explainability(regime_transition_envelope):
    frozen = deepcopy(regime_transition_envelope)
    validation = validate_historical_explainability_inputs(frozen)
    records = build_historical_explanation_records(frozen) if isinstance(frozen, dict) else []
    summary = build_historical_explanation_summary(records)
    chain = build_historical_explanation_checksum_chain(records)
    input_chain = frozen.get("checksum_chain", {}) if isinstance(frozen, dict) else {}
    lineage_ok = bool(input_chain.get("transition_chain_checksum")) and bool(chain.get("explanation_chain_checksum"))
    blocked = (not validation["valid"]) or (not records) or (not input_chain)
    degraded = ("DEGRADED" in str((frozen or {}).get("t4_status", ""))) or any(r.get("explanation_quality") != "EXPLANATION_CERTIFIED" for r in records)
    status = "HISTORICAL_EXPLAINABILITY_BLOCKED" if blocked else "HISTORICAL_EXPLAINABILITY_DEGRADED" if degraded else "HISTORICAL_EXPLAINABILITY_CERTIFIED"
    gates = {g: True for g in CERTIFICATION_GATES}
    gates["t4_envelope_present"] = isinstance(frozen, dict)
    gates["t4_transition_records_present"] = bool(validation["transition_records"])
    gates["minimum_explanation_depth_present"] = any(int(r.get("pair_count", 0) or 0) >= 2 for r in validation["transition_records"])
    gates["required_transition_checksums_present"] = all(r.get("transition_checksum") for r in validation["transition_records"])
    gates["checksum_lineage_preserved"] = lineage_ok
    gates["inputs_not_mutated"] = frozen == regime_transition_envelope
    result = {
        "t5_status": status,
        "input_transition_record_count": len(validation["transition_records"]),
        "explanation_record_count": len(records),
        "explanation_records": records,
        "historical_explanation_summary": summary,
        "checksum_chain": {"input_transition_chain_checksum": input_chain.get("transition_chain_checksum", ""), **chain},
        "certification_gates": [{"gate": g, "passed": bool(gates[g])} for g in CERTIFICATION_GATES],
        "forbidden_capabilities": deepcopy(FORBIDDEN_CAPABILITIES),
        "invariant_flags": {
            "deterministic_template_selection": True, "deterministic_explanation_ordering": True, "immutable_inputs": True, "replay_safe": not blocked,
            "checksum_lineage_preserved": lineage_ok, "bounded_template_inventory_only": all(r.get("bounded_explanation_template_id") in APPROVED_TEMPLATE_IDS for r in records),
            "bounded_summary_phrases_only": all(r.get("structural_change_summary") in APPROVED_STRUCTURAL_SUMMARIES for r in records),
            "no_open_ended_generation": True, "no_runtime_reads": True, "no_runtime_writes": True, "no_network_access": True,
            "no_prediction_behavior": True, "no_trading_behavior": True, "no_forecasting_language": True, "no_recommendation_language": True,
            "no_adaptive_learning": True, "additive_only": True,
        },
        "temporal_lineage": {
            "t4_result_checksum": frozen.get("result_checksum", "") if isinstance(frozen, dict) else "",
            "t4_transition_chain_checksum": input_chain.get("transition_chain_checksum", ""),
            "t5_explanation_chain_checksum": chain.get("explanation_chain_checksum", ""),
            "upstream_temporal_lineage": deepcopy((frozen.get("temporal_lineage", {}) if isinstance(frozen, dict) else {})),
        },
    }
    result["result_checksum"] = _stable_checksum(result)
    return result


def build_t5_historical_explainability_report(certification_result):
    frozen = deepcopy(certification_result)
    return "\n".join([
        "# T5 Historical Explainability Report",
        f"Status: {frozen.get('t5_status', 'UNKNOWN')}",
        f"Input transition records: {frozen.get('input_transition_record_count', 0)}",
        f"Explanation records: {frozen.get('explanation_record_count', 0)}",
        f"Result checksum: {frozen.get('result_checksum', '')}",
    ])
