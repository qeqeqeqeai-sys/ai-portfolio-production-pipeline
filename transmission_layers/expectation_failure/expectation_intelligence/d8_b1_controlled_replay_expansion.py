from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
import hashlib, json
from typing import Any, Mapping

D8_B1_VERSION = "d8_b1_controlled_replay_expansion_v1"

def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()

def _as_list(v: Any) -> list[Any]: return list(v) if isinstance(v, list) else []
def _as_text(v: Any) -> str: return str(v).strip() if v is not None else ""
def _uniq(vs: list[Any]) -> list[str]: return sorted({_as_text(v) for v in vs if _as_text(v)})

def build_d8_b1_controlled_replay_expansion(*, replay_metadata_rows:list[Mapping[str,Any]], historical_runs_payloads:list[Mapping[str,Any]], evidence_maps:list[Mapping[str,Any]], e2_payload:Mapping[str,Any], d8_2_payload:Mapping[str,Any]) -> OrderedDict[str,Any]:
    replay = [r for r in _as_list(replay_metadata_rows) if isinstance(r, Mapping)]
    history = sorted([r for r in _as_list(historical_runs_payloads) if isinstance(r, Mapping)], key=lambda r: (_as_text(r.get("timestamp") or r.get("created_at")), _as_text(r.get("run_id") or r.get("record_id"))))
    evidence_rows = [e for e in _as_list(evidence_maps) if isinstance(e, Mapping)]
    run_ids = _uniq([r.get("run_id") or r.get("replay_id") or r.get("record_id") for r in history])
    evidence_refs = _uniq([e.get("evidence_ref") for e in evidence_rows] + [x for e in evidence_rows for x in _as_list(e.get("supporting_evidence_refs"))])

    gaps = []
    if len(history) <= 1: gaps.append("historical_run_depth_sparse")
    if len(replay) < len(history): gaps.append("replay_metadata_lag_vs_history")
    if not evidence_refs: gaps.append("no_evidence_refs_for_reinforcement")

    overwrite_risks = []
    if len(run_ids) != len(history): overwrite_risks.append("non_unique_or_missing_run_ids")
    if len(set(_as_text(r.get("timestamp") or r.get("created_at")) for r in history if _as_text(r.get("timestamp") or r.get("created_at")))) < len(history): overwrite_risks.append("timestamp_collisions_possible")

    replay_continuity_score = round(min(1.0, len(history)/5),3)
    replay_accumulation_score = round(min(1.0, len(run_ids)/6),3)
    evidence_reinforcement_score = round(min(1.0, len(evidence_refs)/8),3)

    if not history: status = "REPLAY_CONTINUITY_BLOCKED"
    elif replay_continuity_score >= 0.8 and evidence_reinforcement_score >= 0.5: status = "REPLAY_CONTINUITY_STRONG"
    elif replay_continuity_score >= 0.4: status = "REPLAY_CONTINUITY_MODERATE"
    else: status = "REPLAY_CONTINUITY_SPARSE"

    payload = OrderedDict([
        ("d8_b1_version", D8_B1_VERSION),
        ("replay_continuity_score", replay_continuity_score),
        ("replay_accumulation_score", replay_accumulation_score),
        ("evidence_reinforcement_score", evidence_reinforcement_score),
        ("historical_density_status", status),
        ("continuity_caveats", sorted(set(gaps + overwrite_risks))),
        ("deterministic_replay_recommendations", [
            "prefer_append_only_by_run_id_and_timestamp",
            "retain_replay_metadata_and_history_in_lockstep",
            "preserve_evidence_refs_without_mutating_historical_rows",
        ]),
        ("lineage_inventory", OrderedDict([("historical_runs", len(history)), ("replay_metadata_rows", len(replay)), ("unique_run_ids", len(run_ids)), ("unique_evidence_refs", len(evidence_refs))])),
        ("forbidden_capability_inventory", OrderedDict([("writes", False), ("network_calls", False), ("black_box_ml", False)])),
    ])
    payload["d8_b1_checksum"] = _stable_checksum(payload)
    return payload

def build_d8_b1_replay_reinforcement_diagnostics(*, historical_runs_payloads:list[Mapping[str,Any]], e2_payload:Mapping[str,Any], d8_2_payload:Mapping[str,Any]) -> OrderedDict[str,Any]:
    history = [r for r in _as_list(historical_runs_payloads) if isinstance(r, Mapping)]
    ev_counts: dict[str,int] = {}
    contradiction_counts: dict[str,int] = {}
    theme_counts: dict[str,int] = {}
    for row in history:
        for ev in _as_list(row.get("evidence_highlights")):
            if isinstance(ev, Mapping):
                for ref in _uniq([ev.get("evidence_ref")] + _as_list(ev.get("supporting_evidence_refs"))): ev_counts[ref]=ev_counts.get(ref,0)+1
        for c in _uniq(_as_list((row.get("contradictions") or {}).get("claims"))): contradiction_counts[c]=contradiction_counts.get(c,0)+1
        for t in _uniq(_as_list((row.get("semantic") or {}).get("themes"))): theme_counts[t]=theme_counts.get(t,0)+1
    payload = OrderedDict([
        ("recurring_evidence_refs", OrderedDict(sorted(ev_counts.items()))),
        ("recurring_contradiction_refs", OrderedDict(sorted(contradiction_counts.items()))),
        ("recurring_theme_refs", OrderedDict(sorted(theme_counts.items()))),
        ("reinforcement_counts", OrderedDict([("evidence_refs_recurring", sum(1 for v in ev_counts.values() if v >= 2)), ("contradiction_refs_recurring", sum(1 for v in contradiction_counts.values() if v >= 2)), ("theme_refs_recurring", sum(1 for v in theme_counts.values() if v >= 2))])),
        ("cross_cycle_evidence_multiplicity", max(ev_counts.values()) if ev_counts else 0),
    ])
    payload["reinforcement_checksum"] = _stable_checksum(payload)
    return payload

def build_d8_b1_controlled_backfill_plan(*, replay_metadata_rows:list[Mapping[str,Any]], historical_runs_payloads:list[Mapping[str,Any]], governance_inventory:Mapping[str,Any]|None=None, dry_run:bool=True) -> OrderedDict[str,Any]:
    history = [r for r in _as_list(historical_runs_payloads) if isinstance(r, Mapping)]
    governance = governance_inventory if isinstance(governance_inventory, Mapping) else {}
    gaps = max(0, len(replay_metadata_rows)-len(history))
    payload = OrderedDict([
        ("dry_run", bool(dry_run)),
        ("append_safe", True),
        ("replay_safe", True),
        ("no_duplicate_writes", True),
        ("governance_inventory_required", True),
        ("governance_inventory_present", bool(governance)),
        ("checksum_lineage_required", True),
        ("candidate_backfill_windows", [] if gaps <= 0 else [OrderedDict([("window_id","gap_window_1"),("missing_rows_estimate",gaps)])]),
        ("expected_continuity_improvement", round(min(1.0, gaps/5),3)),
        ("expected_evidence_multiplicity_improvement", round(min(1.0, gaps/6),3)),
        ("expected_semantic_persistence_improvement", round(min(1.0, gaps/6),3)),
        ("execution_status", "DRY_RUN_PLANNED" if dry_run else "WRITE_DISABLED_BY_GOVERNANCE"),
    ])
    payload["backfill_plan_checksum"] = _stable_checksum(payload)
    return payload
