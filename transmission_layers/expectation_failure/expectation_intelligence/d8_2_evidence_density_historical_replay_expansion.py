from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


D8_2_VERSION = "d8_2_evidence_density_historical_replay_expansion_v1"


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _sorted_unique_texts(values: list[Any]) -> list[str]:
    return sorted({_as_text(v) for v in values if _as_text(v)})


def build_d8_2_replay_density_inventory(historical_runs_payloads: list[Mapping[str, Any]], findings: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]], e2_payload: Mapping[str, Any], e3_payload: Mapping[str, Any], e4_payload: Mapping[str, Any], e5_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    run_rows = [r for r in _as_list(historical_runs_payloads) if isinstance(r, Mapping)]
    run_rows = sorted(run_rows, key=lambda r: (_as_text(r.get("timestamp")), _as_text(r.get("run_id"))))

    continuity_pairs = []
    prior_regime = ""
    for row in run_rows:
        regime = _as_text(row.get("regime") or (row.get("composite_regime_synthesis") or {}).get("dominant_expectation_regime"))
        run_id = _as_text(row.get("run_id"))
        if prior_regime and regime:
            continuity_pairs.append(OrderedDict([
                ("from_regime", prior_regime),
                ("to_regime", regime),
                ("run_id", run_id),
                ("transition_type", "stable" if prior_regime == regime else "transition"),
            ]))
        prior_regime = regime or prior_regime

    evidence_refs = _sorted_unique_texts([e.get("evidence_ref") for e in _as_list(evidence_maps) if isinstance(e, Mapping)])
    linkage_rows = [l for l in _as_list(e2_payload.get("evidence_finding_linkages")) if isinstance(l, Mapping)]
    finding_ids = _sorted_unique_texts([f.get("finding_id") for f in _as_list(findings) if isinstance(f, Mapping)])

    evidence_lineage = []
    for ref in evidence_refs:
        linked_findings = _sorted_unique_texts([l.get("finding_id") for l in linkage_rows if _as_text(l.get("evidence_ref")) == ref])
        evidence_lineage.append(OrderedDict([
            ("evidence_ref", ref),
            ("linked_findings", linked_findings),
            ("linkage_density", len(linked_findings)),
        ]))

    payload = OrderedDict([
        ("runs_observed", len(run_rows)),
        ("finding_count", len(finding_ids)),
        ("evidence_count", len(evidence_refs)),
        ("replay_continuity_chain", continuity_pairs),
        ("evidence_lineage", evidence_lineage),
        ("history_sufficiency", deepcopy(e3_payload.get("history_sufficiency"))),
        ("semantic_memory_ref", deepcopy(e4_payload.get("semantic_memory_inventory") or {})),
        ("caveats", _sorted_unique_texts(_as_list((e5_payload.get("caveat_inventory") or {}).get("consolidated_caveats")))),
    ])
    payload["replay_density_checksum"] = _stable_checksum(payload)
    return payload


def build_d8_2_semantic_persistence_summary(replay_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    runs = _as_list(replay_inventory.get("historical_runs_payloads"))
    if not runs:
        runs = []
    themes_by_run = []
    for row in runs:
        themes = _sorted_unique_texts(_as_list((row.get("semantic") or {}).get("themes"))) if isinstance(row, Mapping) else []
        themes_by_run.append(themes)

    all_themes = _sorted_unique_texts([t for ts in themes_by_run for t in ts])
    counts = OrderedDict()
    for theme in all_themes:
        counts[theme] = sum(1 for ts in themes_by_run if theme in ts)

    recurring = [k for k, v in counts.items() if v >= 2]
    emerging = themes_by_run[-1] if themes_by_run else []
    prior_flat = {t for ts in themes_by_run[:-1] for t in ts} if len(themes_by_run) > 1 else set()
    emerging = sorted([t for t in emerging if t not in prior_flat])
    decaying = sorted([t for t in prior_flat if t not in set(themes_by_run[-1] if themes_by_run else [])])

    return OrderedDict([
        ("themes_observed", all_themes),
        ("theme_occurrence_counts", counts),
        ("recurring_themes", recurring),
        ("emerging_themes", emerging),
        ("decaying_themes", decaying),
    ])


def build_d8_2_evidence_density_summary(replay_inventory: Mapping[str, Any], e2_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    lineage = _as_list(replay_inventory.get("evidence_lineage"))
    cluster_count = len(lineage)
    avg_linkage = round(sum(int(row.get("linkage_density") or 0) for row in lineage) / (cluster_count or 1), 2)
    contradiction_map = _as_list(e2_payload.get("contradiction_evidence_map"))
    contradiction_refs = _sorted_unique_texts([r for row in contradiction_map if isinstance(row, Mapping) for r in _as_list(row.get("supporting_evidence_refs"))])
    broad_theme_count = len(_as_list((replay_inventory.get("semantic_memory_ref") or {}).get("themes")))
    return OrderedDict([
        ("evidence_cluster_count", cluster_count),
        ("avg_linkage_density", avg_linkage),
        ("contradiction_evidence_count", len(contradiction_refs)),
        ("thematic_breadth", broad_theme_count),
        ("evidence_breadth_indicator", "broad" if cluster_count >= 5 else "moderate" if cluster_count >= 3 else "narrow"),
    ])


def build_d8_2_theme_evolution_summary(semantic_summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    recurring = _as_list(semantic_summary.get("recurring_themes"))
    emerging = _as_list(semantic_summary.get("emerging_themes"))
    decaying = _as_list(semantic_summary.get("decaying_themes"))
    return OrderedDict([
        ("strengthening_themes", recurring),
        ("emerging_themes", emerging),
        ("decaying_themes", decaying),
        ("weakening_themes", decaying),
    ])


def build_d8_2_regime_transition_history(replay_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    transitions = _as_list(replay_inventory.get("replay_continuity_chain"))
    transition_count = sum(1 for t in transitions if _as_text(t.get("transition_type")) == "transition")
    return OrderedDict([
        ("regime_transitions", transitions),
        ("transition_count", transition_count),
        ("continuity_status", "continuous" if transitions else "insufficient_history"),
    ])


def build_d8_2_contradiction_persistence_summary(historical_runs_payloads: list[Mapping[str, Any]], e2_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    known = _sorted_unique_texts([_as_text(row.get("contradiction_claim")) for row in _as_list(e2_payload.get("contradiction_evidence_map")) if isinstance(row, Mapping)])
    run_claims = []
    for row in _as_list(historical_runs_payloads):
        claims = _sorted_unique_texts(_as_list((row.get("contradictions") or {}).get("claims"))) if isinstance(row, Mapping) else []
        run_claims.append(set(claims))
    persistent = sorted([c for c in known if sum(1 for rc in run_claims if c in rc) >= 2])
    return OrderedDict([
        ("persistent_contradiction_themes", persistent),
        ("tracked_contradiction_themes", known),
        ("persistence_count", len(persistent)),
    ])


def build_d8_2_evidence_relationship_graph(findings: list[Mapping[str, Any]], narratives: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]], replay_inventory: Mapping[str, Any], contradiction_summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    nodes = []
    edges = []
    for f in sorted([x for x in findings if isinstance(x, Mapping)], key=lambda x: _as_text(x.get("finding_id"))):
        fid = _as_text(f.get("finding_id"))
        if fid:
            nodes.append(OrderedDict([("node_id", fid), ("node_type", "finding")]))
    for e in sorted([x for x in evidence_maps if isinstance(x, Mapping)], key=lambda x: _as_text(x.get("evidence_ref"))):
        ref = _as_text(e.get("evidence_ref"))
        if ref:
            nodes.append(OrderedDict([("node_id", ref), ("node_type", "evidence")]))
            for fid in _as_list(e.get("finding_refs")):
                if _as_text(fid):
                    edges.append(OrderedDict([("from", ref), ("to", _as_text(fid)), ("edge_type", "supports")]))
    for n in sorted([x for x in narratives if isinstance(x, Mapping)], key=lambda x: _as_text(x.get("record_id"))):
        rid = _as_text(n.get("record_id") or n.get("narrative_id"))
        if rid:
            nodes.append(OrderedDict([("node_id", rid), ("node_type", "narrative")]))
    for c in _as_list(contradiction_summary.get("persistent_contradiction_themes")):
        cid = f"contradiction::{c}"
        nodes.append(OrderedDict([("node_id", cid), ("node_type", "contradiction")]))
    return OrderedDict([("nodes", nodes), ("edges", sorted(edges, key=lambda x: (_as_text(x.get('from')), _as_text(x.get('to')), _as_text(x.get('edge_type'))))), ("replay_continuity", deepcopy(replay_inventory.get("replay_continuity_chain") or []))])


def build_d8_2_dashboard_view_model(d8_2_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("semantic_persistence_summary", deepcopy(d8_2_payload.get("semantic_persistence_summary") or {})),
        ("regime_transition_history", deepcopy(d8_2_payload.get("regime_transition_history") or {})),
        ("evidence_density_indicators", deepcopy(d8_2_payload.get("evidence_density_summary") or {})),
        ("replay_continuity_summary", deepcopy(d8_2_payload.get("replay_density_inventory") or {})),
        ("persistent_contradiction_tracking", deepcopy(d8_2_payload.get("contradiction_persistence_summary") or {})),
        ("thematic_evolution_summary", deepcopy(d8_2_payload.get("theme_evolution_summary") or {})),
    ])


def certify_d8_2_replay_density_expansion(d8_2_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("deterministic", True),
        ("replayable", True),
        ("read_only", True),
        ("checksum_present", bool(d8_2_payload.get("d8_2_checksum"))),
        ("forbidden_capability_inventory", deepcopy(d8_2_payload.get("forbidden_capability_inventory") or {})),
    ])


def build_d8_2_replay_density_report(d8_2_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("d8_2_version", d8_2_payload.get("d8_2_version")),
        ("runs_observed", ((d8_2_payload.get("replay_density_inventory") or {}).get("runs_observed"))),
        ("theme_count", len(_as_list((d8_2_payload.get("semantic_persistence_summary") or {}).get("themes_observed")))),
        ("transition_count", ((d8_2_payload.get("regime_transition_history") or {}).get("transition_count"))),
        ("d8_2_checksum", d8_2_payload.get("d8_2_checksum")),
    ])


def build_d8_2_payload(historical_runs_payloads: list[Mapping[str, Any]], findings: list[Mapping[str, Any]], narratives: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]], e2_payload: Mapping[str, Any], e3_payload: Mapping[str, Any], e4_payload: Mapping[str, Any], e5_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    replay = build_d8_2_replay_density_inventory(historical_runs_payloads, findings, evidence_maps, e2_payload, e3_payload, e4_payload, e5_payload)
    replay_with_runs = OrderedDict(replay)
    replay_with_runs["historical_runs_payloads"] = deepcopy(_as_list(historical_runs_payloads))
    semantic = build_d8_2_semantic_persistence_summary(replay_with_runs)
    density = build_d8_2_evidence_density_summary(replay, e2_payload)
    evolution = build_d8_2_theme_evolution_summary(semantic)
    regime = build_d8_2_regime_transition_history(replay)
    contradiction = build_d8_2_contradiction_persistence_summary(historical_runs_payloads, e2_payload)
    graph = build_d8_2_evidence_relationship_graph(findings, narratives, evidence_maps, replay, contradiction)
    payload = OrderedDict([
        ("d8_2_version", D8_2_VERSION),
        ("replay_density_inventory", replay),
        ("semantic_persistence_summary", semantic),
        ("evidence_density_summary", density),
        ("theme_evolution_summary", evolution),
        ("regime_transition_history", regime),
        ("contradiction_persistence_summary", contradiction),
        ("evidence_relationship_graph", graph),
        ("dashboard_view_model", OrderedDict()),
        ("forbidden_capability_inventory", OrderedDict([("prediction_engine", False), ("trading_recommendation", False), ("execution_engine", False), ("black_box_ml", False), ("writes", False), ("network_calls", False)])),
    ])
    payload["dashboard_view_model"] = build_d8_2_dashboard_view_model(payload)
    payload["d8_2_checksum"] = _stable_checksum(payload)
    return payload
