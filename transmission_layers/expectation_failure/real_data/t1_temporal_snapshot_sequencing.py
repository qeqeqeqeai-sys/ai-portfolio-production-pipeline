"""T1 deterministic temporal snapshot sequencing for replay-safe structural evolution inputs."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json

APPROVED_WINDOW_TYPES = ("7D", "30D", "60D", "90D", "180D", "365D", "FULL_SEQUENCE")
WINDOW_DAYS = {"7D": 7, "30D": 30, "60D": 60, "90D": 90, "180D": 180, "365D": 365}

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
    "recursive_replay_expansion": False,
}

CERTIFICATION_GATES = [
    "inputs_are_sequence",
    "inputs_not_mutated",
    "required_identifiers_present",
    "required_dates_present",
    "required_checksums_present",
    "certification_status_visible",
    "deterministic_ordering_applied",
    "checksum_chain_built",
    "bounded_window_policy_used",
    "no_live_reads",
    "no_writes",
    "no_network_calls",
    "no_prediction_logic",
    "no_trading_logic",
    "replay_metadata_preserved",
]


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _extract_date(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return date.fromisoformat(raw[:10]).isoformat()
    except ValueError:
        return None


def _normalize_snapshot(index: int, snapshot: object) -> dict:
    if not isinstance(snapshot, dict):
        return {"index": index, "record_status": "INELIGIBLE", "issues": ["snapshot_not_dict"]}

    identifier = snapshot.get("snapshot_id") or snapshot.get("run_id")
    as_of_date = _extract_date(snapshot.get("as_of_date") or snapshot.get("run_date_sgt"))
    checksum = snapshot.get("checksum") or snapshot.get("snapshot_checksum") or snapshot.get("envelope_checksum")
    certification_status = snapshot.get("certification_status")

    issues: list[str] = []
    if not identifier:
        issues.append("missing_identifier")
    if not as_of_date:
        issues.append("missing_required_date")
    if not checksum:
        issues.append("missing_required_checksum")
    if certification_status is None:
        issues.append("missing_certification_status")

    status = "ELIGIBLE"
    if "missing_required_date" in issues or "missing_identifier" in issues:
        status = "INELIGIBLE"
    elif issues:
        status = "DEGRADED_ELIGIBLE"

    return {
        "index": index,
        "record_status": status,
        "issues": issues,
        "snapshot_identifier": str(identifier) if identifier else "",
        "as_of_date": as_of_date or "",
        "snapshot_checksum": str(checksum) if checksum else "",
        "certification_status": certification_status,
        "replay_metadata": deepcopy(snapshot.get("replay_metadata", {})),
        "persistence_eligibility": deepcopy(snapshot.get("persistence_eligibility", snapshot.get("persistence_ready"))),
        "payload_summary": deepcopy(snapshot.get("payload_summary", snapshot.get("entity_payload_summary", {}))),
        "source_snapshot": deepcopy(snapshot),
    }


def validate_temporal_snapshot_inputs(snapshots) -> dict:
    inputs_are_sequence = isinstance(snapshots, (list, tuple))
    if not inputs_are_sequence:
        return {"inputs_are_sequence": False, "records": [], "errors": ["inputs_not_list_or_tuple"]}

    records = [_normalize_snapshot(i, snap) for i, snap in enumerate(snapshots)]
    return {"inputs_are_sequence": True, "records": records, "errors": []}


def build_temporal_snapshot_sequence(snapshots, *, window_policy=None) -> dict:
    del window_policy
    validation = validate_temporal_snapshot_inputs(snapshots)
    records = validation["records"]
    eligible = [r for r in records if r["record_status"] in {"ELIGIBLE", "DEGRADED_ELIGIBLE"}]
    ordered = sorted(eligible, key=lambda r: (r.get("as_of_date", ""), r.get("snapshot_identifier", ""), r.get("snapshot_checksum", "")))
    return {
        "validation": validation,
        "ordered_sequence": ordered,
        "eligible_snapshot_count": sum(1 for r in records if r["record_status"] == "ELIGIBLE"),
        "degraded_snapshot_count": sum(1 for r in records if r["record_status"] == "DEGRADED_ELIGIBLE"),
        "blocked_snapshot_count": sum(1 for r in records if r["record_status"] == "INELIGIBLE"),
    }


def build_temporal_checksum_chain(sequence) -> dict:
    ordered = deepcopy(sequence)
    identifiers = [r.get("snapshot_identifier", "") for r in ordered]
    checksums = [r.get("snapshot_checksum", "") for r in ordered]
    return {
        "ordered_snapshot_identifiers": identifiers,
        "ordered_snapshot_checksums": checksums,
        "sequence_checksum": _stable_checksum({"ids": identifiers, "checksums": checksums}),
    }


def _gap_diagnostics(sequence: list[dict], *, window_days: int | None = None) -> dict:
    dates = [r.get("as_of_date") for r in sequence if r.get("as_of_date")]
    duplicate_dates = len(set(dates)) != len(dates)
    irregular_spacing = False
    if len(dates) > 2:
        parsed = [date.fromisoformat(d) for d in dates]
        deltas = {(parsed[i] - parsed[i - 1]).days for i in range(1, len(parsed))}
        irregular_spacing = len(deltas) > 1
    insufficient = bool(window_days and dates and (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days + 1 < window_days)
    return {
        "duplicate_dates_present": duplicate_dates,
        "missing_required_dates_unknown": any(not r.get("as_of_date") for r in sequence),
        "irregular_spacing_detected": irregular_spacing,
        "insufficient_history": insufficient,
        "degraded_snapshots_present": any(r.get("record_status") == "DEGRADED_ELIGIBLE" for r in sequence),
    }


def build_temporal_replay_window(sequence, *, window_type):
    if window_type not in APPROVED_WINDOW_TYPES:
        raise ValueError("window_type_not_approved")

    ordered = deepcopy(sequence)
    if window_type == "FULL_SEQUENCE":
        included = ordered
    else:
        days = WINDOW_DAYS[window_type]
        if not ordered:
            included = []
        else:
            end = date.fromisoformat(ordered[-1]["as_of_date"])
            start = end - timedelta(days=days - 1)
            included = [r for r in ordered if r.get("as_of_date") and date.fromisoformat(r["as_of_date"]) >= start]

    included_dates = [r.get("as_of_date", "") for r in included]
    chain = build_temporal_checksum_chain(included)
    window_checksum = _stable_checksum({"window_type": window_type, "sequence_checksum": chain["sequence_checksum"]})
    return {
        "window_type": window_type,
        "included_snapshot_count": len(included),
        "included_dates": included_dates,
        "excluded_snapshot_count": max(0, len(ordered) - len(included)),
        "gap_diagnostics": _gap_diagnostics(included, window_days=WINDOW_DAYS.get(window_type)),
        "sequence_start_date": included_dates[0] if included_dates else "",
        "sequence_end_date": included_dates[-1] if included_dates else "",
        "checksum_chain": {**chain, "window_checksum": window_checksum},
    }


def certify_temporal_snapshot_sequence(snapshots, *, window_policy=None) -> dict:
    frozen_input = deepcopy(snapshots)
    windows = list(window_policy or APPROVED_WINDOW_TYPES)
    bounded_ok = all(w in APPROVED_WINDOW_TYPES for w in windows)

    seq_result = build_temporal_snapshot_sequence(frozen_input)
    ordered = seq_result["ordered_sequence"]
    checksum_chain = build_temporal_checksum_chain(ordered)

    replay_windows = {w: build_temporal_replay_window(ordered, window_type=w) for w in windows if w in APPROVED_WINDOW_TYPES}

    gates = {
        "inputs_are_sequence": seq_result["validation"]["inputs_are_sequence"],
        "inputs_not_mutated": frozen_input == snapshots,
        "required_identifiers_present": all("missing_identifier" not in r.get("issues", []) for r in seq_result["validation"]["records"]),
        "required_dates_present": all("missing_required_date" not in r.get("issues", []) for r in seq_result["validation"]["records"]),
        "required_checksums_present": all("missing_required_checksum" not in r.get("issues", []) for r in seq_result["validation"]["records"]),
        "certification_status_visible": all("missing_certification_status" not in r.get("issues", []) for r in seq_result["validation"]["records"]),
        "deterministic_ordering_applied": True,
        "checksum_chain_built": bool(checksum_chain["sequence_checksum"]),
        "bounded_window_policy_used": bounded_ok,
        "no_live_reads": True,
        "no_writes": True,
        "no_network_calls": True,
        "no_prediction_logic": True,
        "no_trading_logic": True,
        "replay_metadata_preserved": True,
    }

    blocked = seq_result["blocked_snapshot_count"] > 0 or not gates["required_dates_present"]
    degraded = seq_result["degraded_snapshot_count"] > 0 or not gates["required_checksums_present"]
    status = "TEMPORAL_SEQUENCE_BLOCKED" if blocked else "TEMPORAL_SEQUENCE_DEGRADED" if degraded else "TEMPORAL_SEQUENCE_CERTIFIED"

    result = {
        "t1_status": status,
        "input_snapshot_count": len(frozen_input) if isinstance(frozen_input, (list, tuple)) else 0,
        "eligible_snapshot_count": seq_result["eligible_snapshot_count"],
        "degraded_snapshot_count": seq_result["degraded_snapshot_count"],
        "blocked_snapshot_count": seq_result["blocked_snapshot_count"],
        "ordered_sequence": ordered,
        "checksum_chain": checksum_chain,
        "replay_windows": replay_windows,
        "gap_diagnostics": _gap_diagnostics(ordered),
        "certification_gates": [{"gate": gate, "passed": bool(gates[gate])} for gate in CERTIFICATION_GATES],
        "forbidden_capabilities": deepcopy(FORBIDDEN_CAPABILITIES),
        "invariant_flags": {
            "deterministic_ordering": True,
            "immutable_inputs": True,
            "replay_safe": status != "TEMPORAL_SEQUENCE_BLOCKED",
            "bounded_windows_only": bounded_ok,
            "checksum_continuity_preserved": bool(checksum_chain["sequence_checksum"]),
            "no_runtime_reads": True,
            "no_runtime_writes": True,
            "no_network_access": True,
            "no_prediction_behavior": True,
            "no_trading_behavior": True,
            "additive_only": True,
        },
        "temporal_metadata": {
            "generated_at_utc": "DETERMINISTIC_T1_TEMPORAL_METADATA",
            "approved_windows": list(APPROVED_WINDOW_TYPES),
            "window_policy_used": windows,
        },
    }
    result["result_checksum"] = _stable_checksum(result)
    return result


def build_t1_temporal_sequencing_report(certification_result) -> str:
    frozen = deepcopy(certification_result)
    return "\n".join(
        [
            "# T1 Temporal Snapshot Sequencing Report",
            f"Status: {frozen.get('t1_status', 'UNKNOWN')}",
            f"Input snapshots: {frozen.get('input_snapshot_count', 0)}",
            f"Eligible snapshots: {frozen.get('eligible_snapshot_count', 0)}",
            f"Degraded snapshots: {frozen.get('degraded_snapshot_count', 0)}",
            f"Blocked snapshots: {frozen.get('blocked_snapshot_count', 0)}",
            f"Sequence checksum: {frozen.get('checksum_chain', {}).get('sequence_checksum', '')}",
        ]
    )
