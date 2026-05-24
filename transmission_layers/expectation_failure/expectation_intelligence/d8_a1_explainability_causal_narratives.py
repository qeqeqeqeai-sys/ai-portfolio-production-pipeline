from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
import hashlib, json
from typing import Any, Mapping

D8_A1_VERSION = "d8_a1_explainability_causal_narratives_v1"
def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
def _as_list(v: Any)->list[Any]: return list(v) if isinstance(v,list) else []
def _as_text(v: Any)->str: return str(v).strip() if v is not None else ""

def build_d8_a1_explainability_causal_narratives(*, d8_2_payload:Mapping[str,Any], d8_5_payload:Mapping[str,Any], d8_6_payload:Mapping[str,Any], d8_b1_payload:Mapping[str,Any], d8_b1_reinforcement:Mapping[str,Any]) -> OrderedDict[str,Any]:
    recurring_themes = _as_list((d8_2_payload.get("semantic_persistence_summary") or {}).get("recurring_themes"))
    weakening_themes = _as_list((d8_2_payload.get("theme_evolution_summary") or {}).get("weakening_themes"))
    recurring_evidence = d8_b1_reinforcement.get("recurring_evidence_refs") if isinstance(d8_b1_reinforcement.get("recurring_evidence_refs"), Mapping) else {}
    recurring_contradictions = d8_b1_reinforcement.get("recurring_contradiction_refs") if isinstance(d8_b1_reinforcement.get("recurring_contradiction_refs"), Mapping) else {}
    weak_linkage = _as_list(d8_6_payload.get("weakest_linkage_areas"))

    narratives = OrderedDict([
        ("evidence_reinforcement_narrative", f"Evidence reinforcement observed across {len(recurring_evidence)} tracked references with deterministic replay continuity constraints."),
        ("contradiction_progression_narrative", f"Contradiction continuity spans {len(recurring_contradictions)} recurring contradiction references across replay cycles."),
        ("persistent_theme_narrative", f"Persistent themes count is {len(recurring_themes)} based on replay-observed recurrence only."),
        ("weakening_theme_narrative", f"Weakening themes count is {len(weakening_themes)} where prior themes are not present in latest replay rows."),
        ("causal_pathway_summary", f"Dominant pathways prioritize evidence refs linked to multiple findings and recurrent themes; weak-linkage flags: {', '.join(sorted(set(str(x) for x in weak_linkage))) or 'none'}."),
        ("evidence_concentration_summary", f"Linkage density score is {d8_6_payload.get('linkage_density_score')} with {len(_as_list(d8_6_payload.get('strongest_evidence_candidates')))} strongest evidence candidates."),
        ("replay_continuity_interpretation", f"Replay continuity status is {d8_b1_payload.get('historical_density_status')} at score {d8_b1_payload.get('replay_continuity_score')}.") ,
        ("regime_pressure_explanation", f"Regime transition count {((d8_2_payload.get('regime_transition_history') or {}).get('transition_count'))} interpreted via deterministic transition tracking only."),
    ])

    replay_density = float(d8_b1_payload.get("replay_continuity_score") or 0.0)
    multiplicity = float(d8_b1_payload.get("evidence_reinforcement_score") or 0.0)
    linkage = float(d8_6_payload.get("linkage_density_score") or 0.0)
    contradiction_cont = 1.0 if len(recurring_contradictions) >= 1 else 0.0
    theme_cont = 1.0 if len(recurring_themes) >= 1 else 0.0
    conf = round((replay_density + multiplicity + min(1.0, linkage) + contradiction_cont + theme_cont) / 5, 3)
    if conf >= 0.75: status = "EXPLAINABILITY_STRONG"
    elif conf >= 0.45: status = "EXPLAINABILITY_MODERATE"
    elif conf > 0: status = "EXPLAINABILITY_LIMITED"
    else: status = "EXPLAINABILITY_BLOCKED"

    payload = OrderedDict([
        ("d8_a1_version", D8_A1_VERSION),
        ("narratives", narratives),
        ("causal_pathway_intelligence", OrderedDict([
            ("dominant_reinforcement_pathways", _as_list(d8_6_payload.get("strongest_evidence_candidates"))[:3]),
            ("recurring_weak_linkage_patterns", weak_linkage),
            ("reinforcing_regime_structure", ((d8_2_payload.get("regime_transition_history") or {}).get("continuity_status"))),
        ])),
        ("explainability_confidence_score", conf),
        ("explainability_status", status),
        ("interpretability_caveats", sorted(set(_as_list(d8_5_payload.get("caveat_reasons")) + weak_linkage))),
        ("forbidden_capability_inventory", OrderedDict([("writes", False), ("network_calls", False), ("black_box_ml", False)])),
    ])
    payload["d8_a1_checksum"] = _stable_checksum(payload)
    return payload

def build_d8_a1_dashboard_view_model(d8_a1_payload: Mapping[str,Any]) -> OrderedDict[str,Any]:
    return OrderedDict([
        ("explainability_status", d8_a1_payload.get("explainability_status")),
        ("explainability_confidence_score", d8_a1_payload.get("explainability_confidence_score")),
        ("narrative_summaries", deepcopy(d8_a1_payload.get("narratives") or {})),
        ("dominant_pathway_summaries", deepcopy((d8_a1_payload.get("causal_pathway_intelligence") or {}).get("dominant_reinforcement_pathways") or [])),
        ("interpretability_caveats", deepcopy(d8_a1_payload.get("interpretability_caveats") or [])),
    ])
