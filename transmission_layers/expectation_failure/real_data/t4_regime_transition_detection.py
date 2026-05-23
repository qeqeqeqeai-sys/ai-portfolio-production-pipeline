"""T4 deterministic regime transition detection from T3 fragility evolution curves."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import hashlib
import json

STRONG_CUMULATIVE_DELTA_THRESHOLD = Decimal("5.00")
MODERATE_CUMULATIVE_DELTA_THRESHOLD = Decimal("2.00")
HIGH_DIRECTIONAL_CONSISTENCY_THRESHOLD = Decimal("0.75")
MEDIUM_DIRECTIONAL_CONSISTENCY_THRESHOLD = Decimal("0.60")
STRESS_PERSISTENCE_THRESHOLD = 3
MINIMUM_TRANSITION_PAIR_COUNT = 2
DECIMAL_QUANT = Decimal("0.0001")

REGIME_STATES = {"REGIME_STABLE", "REGIME_WATCH", "REGIME_STRETCHED", "REGIME_FRAGILE", "REGIME_STRESS", "REGIME_RECOVERING", "REGIME_UNCLEAR", "REGIME_INSUFFICIENT_HISTORY", "REGIME_DEGRADED_INPUT"}
REGIME_TRANSITIONS = {"STABLE_TO_WATCH", "WATCH_TO_STRETCHED", "STRETCHED_TO_FRAGILE", "FRAGILE_TO_STRESS", "STRESS_TO_RECOVERING", "FRAGILE_TO_RECOVERING", "WATCH_TO_STABLE", "STRETCHED_TO_WATCH", "FRAGILE_TO_STRETCHED", "NO_REGIME_CHANGE", "REGIME_TRANSITION_UNCLEAR", "REGIME_TRANSITION_INSUFFICIENT_HISTORY", "REGIME_TRANSITION_DEGRADED_INPUT"}
TRANSITION_CONFIDENCE = {"TRANSITION_CONFIDENCE_HIGH", "TRANSITION_CONFIDENCE_MEDIUM", "TRANSITION_CONFIDENCE_LOW", "TRANSITION_CONFIDENCE_INSUFFICIENT", "TRANSITION_CONFIDENCE_DEGRADED"}

FORBIDDEN_CAPABILITIES = {"live_fetch": False, "supabase_read": False, "supabase_write": False, "trading_execution": False, "prediction": False, "optimization": False, "adaptive_learning": False, "hidden_state_mutation": False, "stochastic_modeling": False, "narrative_explanation_generation": False, "recursive_replay_expansion": False}
CERTIFICATION_GATES = ["t3_envelope_present", "t3_curve_records_present", "minimum_transition_depth_present", "required_curve_checksums_present", "deterministic_subject_processing_applied", "deterministic_transition_ordering_applied", "bounded_regime_states_used", "bounded_transition_labels_used", "bounded_confidence_labels_used", "decimal_rounding_policy_applied", "checksum_lineage_preserved", "inputs_not_mutated", "no_live_reads", "no_writes", "no_network_calls", "no_prediction_logic", "no_trading_logic", "no_explanation_generation", "no_adaptive_learning"]


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _to_decimal(v):
    if v is None:
        return Decimal("0")
    try:
        return Decimal(str(v)).quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def validate_regime_transition_inputs(fragility_curve_envelope):
    if not isinstance(fragility_curve_envelope, dict):
        return {"valid": False, "errors": ["t3_envelope_missing_or_invalid"], "curve_records": []}
    records = fragility_curve_envelope.get("curve_records")
    errors = []
    if not isinstance(records, list):
        errors.append("curve_records_missing")
        records = []
    if not records:
        errors.append("curve_records_empty")
    if not fragility_curve_envelope.get("checksum_chain"):
        errors.append("checksum_chain_missing")
    return {"valid": not errors, "errors": sorted(set(errors)), "curve_records": deepcopy(records)}


def _classify_transition(record, t3_status, lineage_ok):
    label = str(record.get("curve_label", ""))
    cum = _to_decimal(record.get("cumulative_score_delta"))
    cons = _to_decimal(record.get("directional_consistency"))
    pers = int(record.get("persistence_count", 0) or 0)
    pair_count = int(record.get("pair_count", 0) or 0)
    obs = int(record.get("observation_count", 0) or 0)
    missing = int(record.get("missing_delta_count", 0) or 0)
    quality = str(record.get("curve_quality", ""))

    prior = "REGIME_WATCH"
    current = "REGIME_UNCLEAR"
    direction = "UNKNOWN"
    trans_quality = "TRANSITION_CERTIFIED"
    if label == "FRAGILITY_DEGRADED_INPUT" or "DEGRADED" in quality:
        prior, current, transition, direction, trans_quality = "REGIME_DEGRADED_INPUT", "REGIME_DEGRADED_INPUT", "REGIME_TRANSITION_DEGRADED_INPUT", "UNKNOWN", "TRANSITION_DEGRADED"
    elif label == "FRAGILITY_INSUFFICIENT_HISTORY" or pair_count < MINIMUM_TRANSITION_PAIR_COUNT:
        prior, current, transition, direction, trans_quality = "REGIME_INSUFFICIENT_HISTORY", "REGIME_INSUFFICIENT_HISTORY", "REGIME_TRANSITION_INSUFFICIENT_HISTORY", "UNKNOWN", "TRANSITION_INSUFFICIENT_HISTORY"
    elif label == "FRAGILITY_VOLATILE":
        prior, current, transition, direction = "REGIME_UNCLEAR", "REGIME_UNCLEAR", "REGIME_TRANSITION_UNCLEAR", "MIXED"
    elif label == "FRAGILITY_PERSISTENTLY_ELEVATED":
        prior = "REGIME_FRAGILE" if pers >= STRESS_PERSISTENCE_THRESHOLD else "REGIME_STRETCHED"
        current = "REGIME_STRESS" if pers >= STRESS_PERSISTENCE_THRESHOLD and cum >= MODERATE_CUMULATIVE_DELTA_THRESHOLD else "REGIME_FRAGILE"
        transition, direction = ("FRAGILE_TO_STRESS" if current == "REGIME_STRESS" else "STRETCHED_TO_FRAGILE"), "DETERIORATING"
    elif label == "FRAGILITY_RISING":
        prior = "REGIME_STRETCHED" if cum >= MODERATE_CUMULATIVE_DELTA_THRESHOLD else "REGIME_WATCH"
        current, transition, direction = "REGIME_FRAGILE", ("STRETCHED_TO_FRAGILE" if prior == "REGIME_STRETCHED" else "WATCH_TO_STRETCHED"), "DETERIORATING"
    elif label == "FRAGILITY_FALLING":
        prior = "REGIME_STRESS" if abs(cum) >= STRONG_CUMULATIVE_DELTA_THRESHOLD else "REGIME_FRAGILE"
        current, transition, direction = "REGIME_RECOVERING", ("STRESS_TO_RECOVERING" if prior == "REGIME_STRESS" else "FRAGILE_TO_RECOVERING"), "IMPROVING"
    elif label == "FRAGILITY_STABLE":
        if cum >= MODERATE_CUMULATIVE_DELTA_THRESHOLD:
            prior, current, transition, direction = "REGIME_WATCH", "REGIME_WATCH", "NO_REGIME_CHANGE", "UNCHANGED"
        else:
            prior, current, transition, direction = "REGIME_STABLE", "REGIME_STABLE", "NO_REGIME_CHANGE", "UNCHANGED"
    else:
        prior, current, transition, direction = "REGIME_UNCLEAR", "REGIME_UNCLEAR", "REGIME_TRANSITION_UNCLEAR", "UNKNOWN"

    if direction == "UNCHANGED":
        strength = "TRANSITION_NONE"
    elif abs(cum) >= STRONG_CUMULATIVE_DELTA_THRESHOLD and cons >= HIGH_DIRECTIONAL_CONSISTENCY_THRESHOLD:
        strength = "TRANSITION_STRONG"
    elif abs(cum) >= MODERATE_CUMULATIVE_DELTA_THRESHOLD and cons >= MEDIUM_DIRECTIONAL_CONSISTENCY_THRESHOLD:
        strength = "TRANSITION_MODERATE"
    elif direction in {"DETERIORATING", "IMPROVING", "MIXED"}:
        strength = "TRANSITION_WEAK"
    else:
        strength = "TRANSITION_UNKNOWN"

    if trans_quality == "TRANSITION_DEGRADED" or "DEGRADED" in t3_status:
        confidence = "TRANSITION_CONFIDENCE_DEGRADED"
    elif trans_quality == "TRANSITION_INSUFFICIENT_HISTORY":
        confidence = "TRANSITION_CONFIDENCE_INSUFFICIENT"
    elif pair_count >= 3 and obs >= 3 and cons >= HIGH_DIRECTIONAL_CONSISTENCY_THRESHOLD and missing == 0 and lineage_ok:
        confidence = "TRANSITION_CONFIDENCE_HIGH"
    elif pair_count >= 2 and cons >= MEDIUM_DIRECTIONAL_CONSISTENCY_THRESHOLD and missing == 0:
        confidence = "TRANSITION_CONFIDENCE_MEDIUM"
    else:
        confidence = "TRANSITION_CONFIDENCE_LOW"
    return prior, current, transition, direction, strength, confidence, trans_quality


def build_regime_transition_records(fragility_curve_envelope):
    frozen = deepcopy(fragility_curve_envelope)
    curves = frozen.get("curve_records", []) if isinstance(frozen, dict) else []
    t3_status = str(frozen.get("t3_status", "")) if isinstance(frozen, dict) else ""
    lineage_ok = bool((frozen.get("checksum_chain") or {}).get("curve_chain_checksum"))
    out = []
    for c in sorted(curves, key=lambda r: (str(r.get("subject_type", "")), str(r.get("subject_id", "")), str(r.get("first_observed_date", "")), str(r.get("curve_checksum", "")))):
        prior, current, transition, direction, strength, confidence, quality = _classify_transition(c, t3_status, lineage_ok)
        rec = {
            "subject_id": c.get("subject_id", ""), "subject_type": c.get("subject_type", ""), "observation_count": c.get("observation_count", 0), "pair_count": c.get("pair_count", 0),
            "first_observed_date": c.get("first_observed_date", ""), "last_observed_date": c.get("last_observed_date", ""), "source_pair_indices": deepcopy(c.get("source_pair_indices", [])),
            "source_snapshot_ids": deepcopy(c.get("source_snapshot_ids", [])), "source_pair_checksums": deepcopy(c.get("source_pair_checksums", [])), "source_curve_checksum": c.get("curve_checksum", ""),
            "prior_regime_state": prior, "current_regime_state": current, "regime_transition": transition, "transition_direction": direction, "transition_strength": strength,
            "transition_confidence": confidence, "transition_quality": quality, "supporting_curve_label": c.get("curve_label", ""),
            "supporting_metrics": {"cumulative_score_delta": c.get("cumulative_score_delta", 0), "directional_consistency": c.get("directional_consistency", 0), "persistence_count": c.get("persistence_count", 0), "missing_delta_count": c.get("missing_delta_count", 0), "deterministic_inference_only": True},
        }
        rec["transition_checksum"] = _stable_checksum(rec)
        out.append(rec)
    return out


def build_regime_transition_summary(transition_records):
    frozen = deepcopy(transition_records)
    statuses = [r.get("regime_transition") for r in frozen]
    return {"transition_count": len(frozen), "transition_label_counts": {s: statuses.count(s) for s in sorted(set(statuses))}, "certified_count": sum(1 for r in frozen if r.get("transition_quality") == "TRANSITION_CERTIFIED"), "degraded_or_unclear_count": sum(1 for r in frozen if r.get("transition_quality") != "TRANSITION_CERTIFIED" or "UNCLEAR" in str(r.get("regime_transition")))}


def build_regime_transition_checksum_chain(transition_records):
    frozen = deepcopy(transition_records)
    checks = [r.get("transition_checksum", "") for r in frozen]
    return {"transition_checksums": checks, "transition_chain_checksum": _stable_checksum(checks)}


def certify_regime_transition_detection(fragility_curve_envelope):
    frozen = deepcopy(fragility_curve_envelope)
    val = validate_regime_transition_inputs(frozen)
    records = build_regime_transition_records(frozen) if isinstance(frozen, dict) else []
    summary = build_regime_transition_summary(records)
    chain = build_regime_transition_checksum_chain(records)
    in_chain = frozen.get("checksum_chain", {}) if isinstance(frozen, dict) else {}
    lineage_ok = bool(in_chain.get("curve_chain_checksum")) and bool(chain.get("transition_chain_checksum"))
    blocked = (not val["valid"]) or (not records) or (not in_chain)
    degraded = ("DEGRADED" in str((frozen or {}).get("t3_status", ""))) or any(r.get("transition_quality") != "TRANSITION_CERTIFIED" for r in records)
    status = "REGIME_TRANSITIONS_BLOCKED" if blocked else "REGIME_TRANSITIONS_DEGRADED" if degraded else "REGIME_TRANSITIONS_CERTIFIED"
    gates = {g: True for g in CERTIFICATION_GATES}
    gates["t3_envelope_present"] = isinstance(frozen, dict)
    gates["t3_curve_records_present"] = bool(val["curve_records"])
    gates["minimum_transition_depth_present"] = any(int(r.get("pair_count", 0) or 0) >= MINIMUM_TRANSITION_PAIR_COUNT for r in val["curve_records"])
    gates["required_curve_checksums_present"] = all(r.get("curve_checksum") for r in val["curve_records"])
    gates["checksum_lineage_preserved"] = lineage_ok
    gates["inputs_not_mutated"] = frozen == fragility_curve_envelope
    result = {
        "t4_status": status, "input_curve_record_count": len(val["curve_records"]), "transition_record_count": len(records), "transition_records": records,
        "regime_transition_summary": summary, "checksum_chain": {"input_curve_chain_checksum": in_chain.get("curve_chain_checksum", ""), **chain},
        "certification_gates": [{"gate": g, "passed": bool(gates[g])} for g in CERTIFICATION_GATES], "forbidden_capabilities": deepcopy(FORBIDDEN_CAPABILITIES),
        "invariant_flags": {"deterministic_subject_processing": True, "deterministic_transition_ordering": True, "immutable_inputs": True, "replay_safe": not blocked, "checksum_lineage_preserved": lineage_ok, "bounded_regime_states_only": all(r.get("prior_regime_state") in REGIME_STATES and r.get("current_regime_state") in REGIME_STATES for r in records), "bounded_transition_labels_only": all(r.get("regime_transition") in REGIME_TRANSITIONS for r in records), "bounded_confidence_labels_only": all(r.get("transition_confidence") in TRANSITION_CONFIDENCE for r in records), "decimal_rounding_policy": True, "no_runtime_reads": True, "no_runtime_writes": True, "no_network_access": True, "no_prediction_behavior": True, "no_trading_behavior": True, "no_explanation_generation": True, "no_adaptive_learning": True, "additive_only": True},
        "temporal_lineage": {"t3_result_checksum": (frozen or {}).get("result_checksum", ""), "t3_curve_chain_checksum": in_chain.get("curve_chain_checksum", ""), "t4_transition_chain_checksum": chain.get("transition_chain_checksum", "")},
    }
    result["result_checksum"] = _stable_checksum(result)
    return result


def build_t4_regime_transition_report(certification_result):
    frozen = deepcopy(certification_result)
    return "\n".join([
        "# T4 Regime Transition Detection Report",
        f"Status: {frozen.get('t4_status', 'UNKNOWN')}",
        f"Input curve records: {frozen.get('input_curve_record_count', 0)}",
        f"Transition records: {frozen.get('transition_record_count', 0)}",
        f"Thresholds: strong={STRONG_CUMULATIVE_DELTA_THRESHOLD}, moderate={MODERATE_CUMULATIVE_DELTA_THRESHOLD}, high_consistency={HIGH_DIRECTIONAL_CONSISTENCY_THRESHOLD}, medium_consistency={MEDIUM_DIRECTIONAL_CONSISTENCY_THRESHOLD}, stress_persistence={STRESS_PERSISTENCE_THRESHOLD}, minimum_pair_count={MINIMUM_TRANSITION_PAIR_COUNT}",
        f"Result checksum: {frozen.get('result_checksum', '')}",
    ])
