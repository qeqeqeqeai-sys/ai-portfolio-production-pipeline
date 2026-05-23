"""T3 deterministic fragility evolution curves from T2 structural delta intelligence."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import hashlib
import json

DIRECTIONAL_CONSISTENCY_THRESHOLD = Decimal("0.60")
STABLE_ABS_DELTA_THRESHOLD = Decimal("1.00")
PERSISTENCE_THRESHOLD = 2
DECIMAL_QUANT = Decimal("0.0001")

CURVE_LABELS = {
    "FRAGILITY_RISING",
    "FRAGILITY_FALLING",
    "FRAGILITY_STABLE",
    "FRAGILITY_VOLATILE",
    "FRAGILITY_PERSISTENTLY_ELEVATED",
    "FRAGILITY_INSUFFICIENT_HISTORY",
    "FRAGILITY_DEGRADED_INPUT",
}

FORBIDDEN_CAPABILITIES = {
    "live_fetch": False,
    "supabase_read": False,
    "supabase_write": False,
    "trading_execution": False,
    "prediction": False,
    "optimization": False,
    "adaptive_learning": False,
    "hidden_state_mutation": False,
    "stochastic_modeling": False,
    "regime_detection": False,
    "explanation_generation": False,
    "recursive_replay_expansion": False,
}

CERTIFICATION_GATES = [
    "t2_envelope_present", "t2_delta_records_present", "minimum_temporal_depth_present", "required_pair_checksums_present",
    "deterministic_subject_grouping_applied", "deterministic_curve_ordering_applied", "bounded_curve_labels_used", "decimal_rounding_policy_applied",
    "checksum_lineage_preserved", "inputs_not_mutated", "no_live_reads", "no_writes", "no_network_calls", "no_prediction_logic",
    "no_trading_logic", "no_regime_detection", "no_explanation_generation", "no_adaptive_learning",
]


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _round_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)


def _to_decimal(value):
    if value is None:
        return None
    try:
        return _round_decimal(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return None


def _subject(sd: dict) -> tuple[str, str]:
    return str(sd.get("subject_type") or "entity"), str(sd.get("entity_id") or sd.get("subject_id") or "")


def validate_fragility_curve_inputs(structural_delta_envelope) -> dict:
    if not isinstance(structural_delta_envelope, dict):
        return {"valid": False, "errors": ["t2_envelope_missing_or_invalid"], "delta_records": []}
    records = structural_delta_envelope.get("delta_records")
    if not isinstance(records, list):
        return {"valid": False, "errors": ["delta_records_missing"], "delta_records": []}
    errors = []
    if not records:
        errors.append("delta_records_empty")
    if not structural_delta_envelope.get("checksum_chain"):
        errors.append("checksum_chain_missing")
    return {"valid": not errors, "errors": sorted(set(errors)), "delta_records": deepcopy(records)}


def build_fragility_evolution_curves(structural_delta_envelope) -> list[dict]:
    frozen = deepcopy(structural_delta_envelope)
    records = frozen.get("delta_records", []) if isinstance(frozen, dict) else []
    status = str(frozen.get("t2_status", "")) if isinstance(frozen, dict) else ""
    grouped: dict[tuple[str, str], list[dict]] = {}
    for pair in records:
        pair_checksum = pair.get("pair_checksum", "")
        from_date, to_date = pair.get("from_date", ""), pair.get("to_date", "")
        pair_index = pair.get("pair_index")
        snap_pair = [pair.get("from_snapshot_id", ""), pair.get("to_snapshot_id", "")]
        for sd in pair.get("score_deltas", []):
            st, sid = _subject(sd)
            if not sid:
                continue
            grouped.setdefault((st, sid), []).append({
                "delta": _to_decimal(sd.get("delta")), "pair_index": pair_index, "from_date": from_date, "to_date": to_date,
                "pair_checksum": pair_checksum, "snapshot_ids": snap_pair,
            })

    out = []
    for (st, sid), items in grouped.items():
        ordered = sorted(items, key=lambda x: (x.get("pair_index", -1), x.get("from_date", ""), x.get("to_date", ""), x.get("pair_checksum", "")))
        vals = [i["delta"] for i in ordered if i["delta"] is not None]
        available = len(vals)
        pos = sum(1 for v in vals if v > 0)
        neg = sum(1 for v in vals if v < 0)
        unchg = sum(1 for v in vals if v == 0)
        miss = len(ordered) - available
        cumulative = _round_decimal(sum(vals, Decimal("0"))) if vals else Decimal("0")
        avg = _round_decimal(cumulative / Decimal(str(available))) if available else Decimal("0")
        dominant = max(pos, neg, unchg) if available else 0
        directional = _round_decimal(Decimal(str(dominant)) / Decimal(str(available))) if available else Decimal("0")
        max_inc = max(vals) if vals else Decimal("0")
        max_dec = min(vals) if vals else Decimal("0")
        pers = 0
        for i in range(1, len(vals)):
            if vals[i] != 0 and vals[i - 1] != 0 and ((vals[i] > 0 and vals[i - 1] > 0) or (vals[i] < 0 and vals[i - 1] < 0)):
                pers += 1

        if "DEGRADED" in status or miss > 0:
            label, quality = "FRAGILITY_DEGRADED_INPUT", "CURVE_DEGRADED"
        elif available < 2:
            label, quality = "FRAGILITY_INSUFFICIENT_HISTORY", "CURVE_INSUFFICIENT_HISTORY"
        elif cumulative > 0 and pers >= PERSISTENCE_THRESHOLD and directional >= DIRECTIONAL_CONSISTENCY_THRESHOLD:
            label, quality = "FRAGILITY_PERSISTENTLY_ELEVATED", "CURVE_CERTIFIED"
        elif cumulative > 0 and directional >= DIRECTIONAL_CONSISTENCY_THRESHOLD:
            label, quality = "FRAGILITY_RISING", "CURVE_CERTIFIED"
        elif cumulative < 0 and directional >= DIRECTIONAL_CONSISTENCY_THRESHOLD:
            label, quality = "FRAGILITY_FALLING", "CURVE_CERTIFIED"
        elif abs(cumulative) <= STABLE_ABS_DELTA_THRESHOLD and (unchg >= max(pos, neg)):
            label, quality = "FRAGILITY_STABLE", "CURVE_CERTIFIED"
        elif pos > 0 and neg > 0 and directional < DIRECTIONAL_CONSISTENCY_THRESHOLD:
            label, quality = "FRAGILITY_VOLATILE", "CURVE_CERTIFIED"
        else:
            label, quality = "FRAGILITY_STABLE", "CURVE_CERTIFIED"

        record = {
            "subject_id": sid, "subject_type": st, "observation_count": len(ordered), "pair_count": len(ordered),
            "first_observed_date": ordered[0]["from_date"] if ordered else "", "last_observed_date": ordered[-1]["to_date"] if ordered else "",
            "source_pair_indices": [o["pair_index"] for o in ordered], "source_snapshot_ids": [o["snapshot_ids"] for o in ordered],
            "source_pair_checksums": [o["pair_checksum"] for o in ordered], "cumulative_score_delta": float(cumulative),
            "average_pair_delta": float(avg), "positive_delta_count": pos, "negative_delta_count": neg, "unchanged_delta_count": unchg,
            "missing_delta_count": miss, "directional_consistency": float(directional), "persistence_count": pers,
            "max_single_pair_increase": float(max_inc), "max_single_pair_decrease": float(max_dec), "curve_label": label, "curve_quality": quality,
        }
        record["curve_checksum"] = _stable_checksum(record)
        out.append(record)

    return sorted(out, key=lambda r: (r.get("subject_type", ""), r.get("subject_id", ""), r.get("first_observed_date", ""), r.get("curve_checksum", "")))


def build_fragility_curve_summary(curve_records):
    frozen = deepcopy(curve_records)
    labels = [c.get("curve_label") for c in frozen]
    return {"curve_count": len(frozen), "label_counts": {l: labels.count(l) for l in sorted(set(labels))}, "degraded_count": sum(1 for c in frozen if c.get("curve_quality") == "CURVE_DEGRADED")}


def build_fragility_curve_checksum_chain(curve_records):
    frozen = deepcopy(curve_records)
    checks = [c.get("curve_checksum", "") for c in frozen]
    return {"curve_checksums": checks, "curve_chain_checksum": _stable_checksum(checks)}


def certify_fragility_evolution_curves(structural_delta_envelope):
    frozen = deepcopy(structural_delta_envelope)
    validation = validate_fragility_curve_inputs(frozen)
    curves = build_fragility_evolution_curves(frozen) if isinstance(frozen, dict) else []
    summary = build_fragility_curve_summary(curves)
    chain = build_fragility_curve_checksum_chain(curves)
    input_chain = frozen.get("checksum_chain", {}) if isinstance(frozen, dict) else {}
    lineage_ok = bool(input_chain.get("delta_chain_checksum")) and bool(chain.get("curve_chain_checksum"))
    blocked = (not validation["valid"]) or (not curves)
    degraded = ("DEGRADED" in str((frozen or {}).get("t2_status", ""))) or any(c.get("curve_quality") != "CURVE_CERTIFIED" for c in curves)
    status = "FRAGILITY_CURVES_BLOCKED" if blocked else "FRAGILITY_CURVES_DEGRADED" if degraded else "FRAGILITY_CURVES_CERTIFIED"
    gates = {g: True for g in CERTIFICATION_GATES}
    gates["t2_envelope_present"] = isinstance(frozen, dict)
    gates["t2_delta_records_present"] = bool(validation["delta_records"])
    gates["minimum_temporal_depth_present"] = len(validation["delta_records"]) >= 1
    gates["required_pair_checksums_present"] = all(r.get("pair_checksum") for r in validation["delta_records"])
    gates["checksum_lineage_preserved"] = lineage_ok
    gates["inputs_not_mutated"] = frozen == structural_delta_envelope
    result = {
        "t3_status": status, "input_delta_record_count": len(validation["delta_records"]), "curve_record_count": len(curves), "curve_records": curves,
        "fragility_curve_summary": summary, "checksum_chain": {"input_delta_chain_checksum": input_chain.get("delta_chain_checksum", ""), **chain},
        "certification_gates": [{"gate": g, "passed": bool(gates[g])} for g in CERTIFICATION_GATES], "forbidden_capabilities": deepcopy(FORBIDDEN_CAPABILITIES),
        "invariant_flags": {
            "deterministic_subject_grouping": True, "deterministic_curve_ordering": True, "immutable_inputs": True, "replay_safe": not blocked,
            "checksum_lineage_preserved": lineage_ok, "bounded_curve_labels_only": all(c.get("curve_label") in CURVE_LABELS for c in curves),
            "decimal_rounding_policy": True, "no_runtime_reads": True, "no_runtime_writes": True, "no_network_access": True,
            "no_prediction_behavior": True, "no_trading_behavior": True, "no_regime_detection": True, "no_explanation_generation": True,
            "no_adaptive_learning": True, "additive_only": True,
        },
        "temporal_lineage": {"t2_result_checksum": frozen.get("result_checksum", "") if isinstance(frozen, dict) else "", "t2_delta_chain_checksum": input_chain.get("delta_chain_checksum", ""), "t3_curve_chain_checksum": chain.get("curve_chain_checksum", "")},
    }
    result["result_checksum"] = _stable_checksum(result)
    return result


def build_t3_fragility_evolution_report(certification_result):
    frozen = deepcopy(certification_result)
    return "\n".join([
        "# T3 Fragility Evolution Curves Report",
        f"Status: {frozen.get('t3_status', 'UNKNOWN')}",
        f"Input delta records: {frozen.get('input_delta_record_count', 0)}",
        f"Curve records: {frozen.get('curve_record_count', 0)}",
        f"Result checksum: {frozen.get('result_checksum', '')}",
    ])
