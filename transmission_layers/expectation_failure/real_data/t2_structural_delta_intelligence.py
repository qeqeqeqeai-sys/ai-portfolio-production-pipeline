"""T2 deterministic structural delta intelligence for adjacent temporal snapshots."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import hashlib
import json

SCORE_FIELDS = ("ai_expectation_failure_score", "expectation_failure_score", "score")
BAND_FIELDS = ("score_band", "relative_fragility_band", "band")
RANK_FIELDS = ("relative_fragility_rank", "rank")
DRIVER_FIELDS = ("dominant_driver", "driver_map", "drivers")

BAND_ORDER = {"LOW": 0, "MODERATE": 1, "ELEVATED": 2, "HIGH": 3, "EXTREME": 4}

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
    "velocity_curve_generation": False,
    "recursive_replay_expansion": False,
}

CERTIFICATION_GATES = [
    "t1_sequence_present", "minimum_two_snapshots_present", "required_snapshot_ids_present", "required_dates_present", "required_checksums_present",
    "deterministic_pairing_applied", "deterministic_entity_ordering_applied", "score_delta_policy_applied", "band_delta_policy_applied",
    "rank_delta_policy_applied", "driver_delta_policy_applied", "checksum_lineage_preserved", "inputs_not_mutated", "no_live_reads", "no_writes",
    "no_network_calls", "no_prediction_logic", "no_trading_logic", "no_regime_detection", "no_velocity_curve_logic",
]


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _round_decimal(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _to_decimal(value):
    if value is None:
        return None
    try:
        return _round_decimal(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return None


def _extract_entities(snapshot: dict) -> dict:
    src = snapshot.get("source_snapshot", snapshot)
    entities = src.get("entities") or src.get("entity_rows") or src.get("payload", {}).get("entities") or []
    out = {}
    if isinstance(entities, list):
        for ent in entities:
            if isinstance(ent, dict):
                entity_id = ent.get("entity_id") or ent.get("ticker") or ent.get("entity_name")
                if entity_id:
                    out[str(entity_id)] = deepcopy(ent)
    return out


def validate_structural_delta_inputs(temporal_sequence) -> dict:
    if not isinstance(temporal_sequence, dict):
        return {"valid": False, "errors": ["t1_envelope_missing_or_invalid"], "ordered_sequence": []}
    ordered = temporal_sequence.get("ordered_sequence")
    if not isinstance(ordered, list):
        return {"valid": False, "errors": ["ordered_sequence_missing"], "ordered_sequence": []}
    records = deepcopy(ordered)
    errors = []
    if len(records) < 2:
        errors.append("minimum_two_snapshots_required")
    for rec in records:
        if not rec.get("snapshot_identifier"):
            errors.append("missing_snapshot_identifier")
        if not rec.get("as_of_date"):
            errors.append("missing_required_date")
        if not rec.get("snapshot_checksum"):
            errors.append("missing_required_checksum")
    return {"valid": not errors, "errors": sorted(set(errors)), "ordered_sequence": records}


def _score_delta(prev, curr):
    pv, cv = _to_decimal(prev), _to_decimal(curr)
    if pv is None:
        return {"label": "SCORE_MISSING_PREVIOUS", "previous_value": prev, "current_value": curr}
    if cv is None:
        return {"label": "SCORE_MISSING_CURRENT", "previous_value": prev, "current_value": curr}
    delta = _round_decimal(cv - pv)
    label = "SCORE_UNCHANGED" if delta == 0 else "SCORE_INCREASED" if delta > 0 else "SCORE_DECREASED"
    return {"label": label, "previous_value": float(pv), "current_value": float(cv), "delta": float(delta), "direction": label, "absolute_delta": float(abs(delta))}


def build_structural_delta_records(temporal_sequence) -> list[dict]:
    ordered = deepcopy(temporal_sequence.get("ordered_sequence", []))
    records = []
    for idx in range(len(ordered) - 1):
        p, c = ordered[idx], ordered[idx + 1]
        p_entities, c_entities = _extract_entities(p), _extract_entities(c)
        p_keys, c_keys = sorted(p_entities), sorted(c_entities)
        common = sorted(set(p_keys) & set(c_keys))
        missing_prev = sorted(set(p_keys) - set(c_keys))
        new_curr = sorted(set(c_keys) - set(p_keys))
        score_deltas = []
        band_transitions = []
        rank_transitions = []
        driver_deltas = []
        degraded = False
        for e in common:
            pe, ce = p_entities[e], c_entities[e]
            ps = next((pe.get(f) for f in SCORE_FIELDS if f in pe), None)
            cs = next((ce.get(f) for f in SCORE_FIELDS if f in ce), None)
            sd = _score_delta(ps, cs)
            score_deltas.append({"entity_id": e, **sd})
            if sd["label"] in {"SCORE_MISSING_PREVIOUS", "SCORE_MISSING_CURRENT"}:
                degraded = True

            pb = (next((pe.get(f) for f in BAND_FIELDS if f in pe), None) or "").upper()
            cb = (next((ce.get(f) for f in BAND_FIELDS if f in ce), None) or "").upper()
            if pb in BAND_ORDER and cb in BAND_ORDER:
                bl = "BAND_UNCHANGED" if pb == cb else "BAND_IMPROVED" if BAND_ORDER[cb] < BAND_ORDER[pb] else "BAND_DETERIORATED"
            else:
                bl = "BAND_UNKNOWN"; degraded = True
            band_transitions.append({"entity_id": e, "previous_band": pb or None, "current_band": cb or None, "label": bl})

            pr, cr = pe.get(RANK_FIELDS[0], pe.get(RANK_FIELDS[1])), ce.get(RANK_FIELDS[0], ce.get(RANK_FIELDS[1]))
            pdr, cdr = _to_decimal(pr), _to_decimal(cr)
            if pdr is None or cdr is None:
                rl = "RANK_UNKNOWN"; rd = None; degraded = True
            else:
                rd = int(cdr - pdr)
                rl = "RANK_UNCHANGED" if rd == 0 else "RANK_IMPROVED" if rd < 0 else "RANK_DETERIORATED"
            rank_transitions.append({"entity_id": e, "previous_rank": pr, "current_rank": cr, "rank_delta": rd, "rank_direction": rl})

            pmap = pe.get("driver_map") if isinstance(pe.get("driver_map"), dict) else {}
            cmap = ce.get("driver_map") if isinstance(ce.get("driver_map"), dict) else {}
            for k in sorted(set(pmap) | set(cmap)):
                pv, cv = _to_decimal(pmap.get(k)), _to_decimal(cmap.get(k))
                if pv is None or cv is None:
                    dl = "DRIVER_UNKNOWN"; degraded = True
                else:
                    dl = "DRIVER_UNCHANGED" if cv == pv else "DRIVER_STRENGTHENED" if cv > pv else "DRIVER_WEAKENED"
                driver_deltas.append({"entity_id": e, "driver_key": k, "previous_value": pmap.get(k), "current_value": cmap.get(k), "label": dl})

        rec = {
            "from_snapshot_id": p.get("snapshot_identifier", ""), "to_snapshot_id": c.get("snapshot_identifier", ""),
            "from_date": p.get("as_of_date", ""), "to_date": c.get("as_of_date", ""),
            "from_checksum": p.get("snapshot_checksum", ""), "to_checksum": c.get("snapshot_checksum", ""),
            "pair_index": idx, "comparable_entities": common, "missing_entities_from_previous": missing_prev, "new_entities_in_current": new_curr,
            "score_deltas": score_deltas, "band_transitions": band_transitions, "rank_transitions": rank_transitions, "driver_deltas": driver_deltas,
            "structural_change_flags": {
                "has_score_change": any(d.get("label") in {"SCORE_INCREASED", "SCORE_DECREASED"} for d in score_deltas),
                "has_band_transition": any(d.get("label") in {"BAND_IMPROVED", "BAND_DETERIORATED"} for d in band_transitions),
                "has_rank_transition": any(d.get("rank_direction") in {"RANK_IMPROVED", "RANK_DETERIORATED"} for d in rank_transitions),
                "has_driver_change": any(d.get("label") in {"DRIVER_STRENGTHENED", "DRIVER_WEAKENED"} for d in driver_deltas),
                "has_entity_membership_change": bool(missing_prev or new_curr), "has_degraded_inputs": degraded,
                "replay_lineage_preserved": bool(p.get("snapshot_checksum") and c.get("snapshot_checksum")),
            },
        }
        rec["pair_checksum"] = _stable_checksum(rec)
        records.append(rec)
    return records


def build_structural_delta_summary(delta_records):
    frozen = deepcopy(delta_records)
    return {"pair_count": len(frozen), "pairs_with_changes": sum(1 for r in frozen if any(r.get("structural_change_flags", {}).values())), "pairs_degraded": sum(1 for r in frozen if r.get("structural_change_flags", {}).get("has_degraded_inputs"))}


def build_structural_delta_checksum_chain(delta_records):
    frozen = deepcopy(delta_records)
    checks = [r.get("pair_checksum", "") for r in frozen]
    return {"pair_checksums": checks, "delta_chain_checksum": _stable_checksum(checks)}


def certify_structural_delta_intelligence(temporal_sequence):
    frozen = deepcopy(temporal_sequence)
    validation = validate_structural_delta_inputs(frozen)
    records = build_structural_delta_records(frozen) if isinstance(frozen, dict) else []
    summary = build_structural_delta_summary(records)
    chain = build_structural_delta_checksum_chain(records)
    lineage_ok = bool(frozen.get("checksum_chain", {}).get("sequence_checksum")) and bool(chain["delta_chain_checksum"]) if isinstance(frozen, dict) else False
    degraded = any(r.get("structural_change_flags", {}).get("has_degraded_inputs") for r in records)
    blocked = not validation["valid"]
    status = "STRUCTURAL_DELTA_BLOCKED" if blocked else "STRUCTURAL_DELTA_DEGRADED" if degraded else "STRUCTURAL_DELTA_CERTIFIED"
    gates = {g: True for g in CERTIFICATION_GATES}
    gates["t1_sequence_present"] = isinstance(frozen, dict) and isinstance(frozen.get("ordered_sequence"), list)
    gates["minimum_two_snapshots_present"] = len(validation["ordered_sequence"]) >= 2
    gates["required_snapshot_ids_present"] = "missing_snapshot_identifier" not in validation["errors"]
    gates["required_dates_present"] = "missing_required_date" not in validation["errors"]
    gates["required_checksums_present"] = "missing_required_checksum" not in validation["errors"]
    gates["checksum_lineage_preserved"] = lineage_ok
    gates["inputs_not_mutated"] = frozen == temporal_sequence
    result = {
        "t2_status": status, "input_snapshot_count": len(validation["ordered_sequence"]), "comparable_pair_count": len(records), "delta_record_count": len(records),
        "delta_records": records, "structural_delta_summary": summary, "checksum_chain": chain,
        "certification_gates": [{"gate": g, "passed": bool(gates[g])} for g in CERTIFICATION_GATES], "forbidden_capabilities": deepcopy(FORBIDDEN_CAPABILITIES),
        "invariant_flags": {
            "deterministic_pairing": True, "deterministic_entity_ordering": True, "immutable_inputs": True, "replay_safe": status != "STRUCTURAL_DELTA_BLOCKED",
            "checksum_lineage_preserved": lineage_ok, "bounded_delta_labels_only": True, "no_runtime_reads": True, "no_runtime_writes": True,
            "no_network_access": True, "no_prediction_behavior": True, "no_trading_behavior": True, "no_regime_detection": True,
            "no_velocity_scoring": True, "additive_only": True,
        },
        "temporal_lineage": {"t1_sequence_checksum": frozen.get("checksum_chain", {}).get("sequence_checksum", "") if isinstance(frozen, dict) else "", "delta_chain_checksum": chain["delta_chain_checksum"]},
    }
    result["result_checksum"] = _stable_checksum(result)
    return result


def build_t2_structural_delta_report(certification_result) -> str:
    frozen = deepcopy(certification_result)
    return "\n".join([
        "# T2 Structural Delta Intelligence Report",
        f"Status: {frozen.get('t2_status', 'UNKNOWN')}",
        f"Input snapshots: {frozen.get('input_snapshot_count', 0)}",
        f"Comparable pairs: {frozen.get('comparable_pair_count', 0)}",
        f"Delta records: {frozen.get('delta_record_count', 0)}",
        f"Result checksum: {frozen.get('result_checksum', '')}",
    ])
