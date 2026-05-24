from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


D8_VERSION = "d8_evidence_prioritization_operational_insight_v1"


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _as_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _score_band(band: Any) -> int:
    b = _as_text(band).lower()
    if b == "strong":
        return 4
    if b == "moderate":
        return 3
    if b == "weak":
        return 2
    return 1


def build_d8_supporting_evidence_rankings(e2_payload: Mapping[str, Any], findings: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    quality = _as_list(e2_payload.get("evidence_quality_profiles"))
    linkages = _as_list(e2_payload.get("evidence_finding_linkages"))
    contradiction_refs = {r for r in _as_list((e2_payload.get("evidence_support_buckets") or {}).get("contradiction_evidence")) if _as_text(r)}

    quality_map = {q.get("evidence_ref"): q for q in quality if isinstance(q, Mapping)}
    evidence_index = {e.get("evidence_ref"): e for e in _as_list(evidence_maps) if isinstance(e, Mapping)}
    finding_index = {f.get("finding_id"): f for f in _as_list(findings) if isinstance(f, Mapping)}

    ranked = []
    for ref, qrow in quality_map.items():
        rel_links = [l for l in linkages if l.get("evidence_ref") == ref]
        max_link = max([int(l.get("linkage_strength_score") or 0) for l in rel_links] or [0])
        avg_link = sum(int(l.get("linkage_strength_score") or 0) for l in rel_links) / (len(rel_links) or 1)
        breadth = len({l.get("finding_id") for l in rel_links if _as_text(l.get("finding_id"))})
        score = int(qrow.get("evidence_quality_score") or 0) + max_link + breadth * 5
        ranked.append(OrderedDict([
            ("evidence_ref", ref),
            ("priority_score", score),
            ("quality_score", int(qrow.get("evidence_quality_score") or 0)),
            ("linkage_max_score", max_link),
            ("linkage_avg_score", round(avg_link, 2)),
            ("breadth", breadth),
            ("quality_band", qrow.get("evidence_quality_band")),
            ("is_contradicting", ref in contradiction_refs),
            ("finding_refs", sorted({str(l.get("finding_id")) for l in rel_links if _as_text(l.get("finding_id"))})),
            ("evidence_metadata", deepcopy((evidence_index.get(ref) or {}).get("evidence_metadata") or {})),
        ]))

    ranked = sorted(ranked, key=lambda x: (-int(x["priority_score"]), -int(x["quality_score"]), _as_text(x["evidence_ref"])))
    supporting = [r for r in ranked if not r.get("is_contradicting")]
    contradicting = [r for r in ranked if r.get("is_contradicting")]

    cluster_scores = []
    for fid, f in sorted(finding_index.items(), key=lambda kv: _as_text(kv[0])):
        refs = [r for r in ranked if fid in _as_list(r.get("finding_refs"))]
        if not refs:
            continue
        conf = _score_band(f.get("confidence"))
        score = sum(int(r.get("priority_score") or 0) for r in refs) + conf * 10
        cluster_scores.append(OrderedDict([("finding_id", fid), ("cluster_score", score), ("cluster_size", len(refs)), ("confidence_band", f.get("confidence"))]))
    cluster_scores = sorted(cluster_scores, key=lambda x: (-int(x["cluster_score"]), _as_text(x["finding_id"])))

    return OrderedDict([
        ("ranked_evidence", ranked),
        ("strongest_supporting_evidence", supporting[0] if supporting else None),
        ("strongest_contradicting_evidence", contradicting[0] if contradicting else None),
        ("highest_confidence_evidence_cluster", cluster_scores[0] if cluster_scores else None),
        ("weakest_link_evidence_cluster", cluster_scores[-1] if cluster_scores else None),
    ])


def build_d8_contradiction_priority_summary(e2_payload: Mapping[str, Any], e3_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    cmap = _as_list(e2_payload.get("contradiction_evidence_map"))
    contradiction_drift = _as_text((e3_payload.get("contradiction_drift") or {}).get("direction")).lower()
    prioritized = []
    for idx, row in enumerate(cmap, start=1):
        strength = int(row.get("contradiction_strength") or 0)
        breadth = len(set(_as_list(row.get("affected_findings"))))
        persistence = 2 if "persist" in _as_text(row.get("persistence_context")).lower() else 1
        direction = "escalating" if contradiction_drift in {"rising", "increasing", "accelerating"} else "de_escalating"
        severity_score = strength + breadth * 10 + persistence * 10 + (10 if direction == "escalating" else 0)
        prioritized.append(OrderedDict([
            ("contradiction_id", f"d8_contradiction_{idx:03d}"),
            ("contradiction_claim", row.get("contradiction_claim")),
            ("severity_score", severity_score),
            ("severity", "high" if severity_score >= 80 else "moderate" if severity_score >= 45 else "low"),
            ("breadth", breadth),
            ("persistence", "persistent" if persistence == 2 else "emerging"),
            ("direction", direction),
            ("operational_significance", "immediate_attention" if severity_score >= 80 else "monitor"),
            ("supporting_evidence_refs", sorted(_as_list(row.get("supporting_evidence_refs")))),
        ]))
    prioritized = sorted(prioritized, key=lambda x: (-int(x["severity_score"]), _as_text(x["contradiction_claim"])))
    return OrderedDict([
        ("contradictions", prioritized),
        ("top_contradiction", prioritized[0] if prioritized else None),
        ("overall_direction", "escalating" if any(c.get("direction") == "escalating" for c in prioritized) else "de_escalating"),
    ])


def build_d8_operational_insight_cards(e5_payload: Mapping[str, Any], rankings: Mapping[str, Any], contradiction_summary: Mapping[str, Any], e3_payload: Mapping[str, Any], e4_payload: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    dominant = _as_text(((e5_payload.get("composite_regime_synthesis") or {}).get("dominant_expectation_regime"))) or "unknown"
    top_con = contradiction_summary.get("top_contradiction") if isinstance(contradiction_summary.get("top_contradiction"), Mapping) else {}
    strong = rankings.get("strongest_supporting_evidence") if isinstance(rankings.get("strongest_supporting_evidence"), Mapping) else {}
    temporal_direction = _as_text((e3_payload.get("expectation_pressure_drift") or {}).get("direction")) or "unknown"
    semantic = _as_text((e4_payload.get("narrative_drift_profile") or {}).get("narrative_drift_direction")) or "stable"
    return [
        OrderedDict([("card_type", "regime_evidence_alignment"), ("insight", f"Dominant regime '{dominant}' is anchored by evidence {strong.get('evidence_ref') or 'unavailable'} with priority score {strong.get('priority_score') if strong else 'N/A'}."), ("evidence_refs", [strong.get("evidence_ref")] if strong.get("evidence_ref") else [])]),
        OrderedDict([("card_type", "contradiction_pressure"), ("insight", f"Top contradiction severity is {top_con.get('severity', 'unavailable')} ({top_con.get('severity_score', 'N/A')}); direction is {contradiction_summary.get('overall_direction', 'unknown')}."), ("evidence_refs", _as_list(top_con.get("supporting_evidence_refs")))]),
        OrderedDict([("card_type", "temporal_semantic_posture"), ("insight", f"Temporal pressure drift is {temporal_direction} while semantic narrative drift is {semantic}."), ("evidence_refs", [])]),
    ]


def build_d8_evidence_lineage_trace(e5_payload: Mapping[str, Any], rankings: Mapping[str, Any], contradiction_summary: Mapping[str, Any], e3_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("dominant_regime_lineage", OrderedDict([("dominant_regime", ((e5_payload.get("composite_regime_synthesis") or {}).get("dominant_expectation_regime"))), ("supporting_signal_refs", _as_list(((e5_payload.get("composite_regime_synthesis") or {}).get("supporting_signal_refs"))))])),
        ("evidence_cluster_contributors", OrderedDict([("highest_confidence_cluster", rankings.get("highest_confidence_evidence_cluster")), ("weakest_link_cluster", rankings.get("weakest_link_evidence_cluster"))])),
        ("contradiction_paths", contradiction_summary.get("contradictions") or []),
        ("temporal_confidence_factors", deepcopy(e3_payload.get("history_sufficiency") if isinstance(e3_payload, Mapping) else None)),
        ("degrading_caveats", _as_list((e5_payload.get("caveat_inventory") or {}).get("consolidated_caveats"))),
    ])


def build_d8_operational_interpretation(insight_cards: list[Mapping[str, Any]], lineage_trace: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("interpretation_sentences", [str(c.get("insight")) for c in _as_list(insight_cards) if _as_text(c.get("insight"))]),
        ("lineage_summary", f"Lineage references {len(_as_list(lineage_trace.get('contradiction_paths')))} contradiction path(s) and {len(_as_list((lineage_trace.get('dominant_regime_lineage') or {}).get('supporting_signal_refs')))} dominant regime signal ref(s)."),
    ])


def build_d8_evidence_priority_inventory(findings: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]], e2_payload: Mapping[str, Any], e3_payload: Mapping[str, Any], e4_payload: Mapping[str, Any], e5_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    rankings = build_d8_supporting_evidence_rankings(e2_payload, findings, evidence_maps)
    contradiction_summary = build_d8_contradiction_priority_summary(e2_payload, e3_payload)
    cards = build_d8_operational_insight_cards(e5_payload, rankings, contradiction_summary, e3_payload, e4_payload)
    lineage = build_d8_evidence_lineage_trace(e5_payload, rankings, contradiction_summary, e3_payload)
    interpretation = build_d8_operational_interpretation(cards, lineage)
    payload = OrderedDict([
        ("d8_version", D8_VERSION),
        ("supporting_evidence_rankings", rankings),
        ("contradiction_priority_summary", contradiction_summary),
        ("operational_insight_cards", cards),
        ("evidence_lineage_trace", lineage),
        ("operational_interpretation", interpretation),
        ("forbidden_capability_inventory", OrderedDict([("prediction_engine", False), ("trading_recommendation", False), ("execution_engine", False), ("black_box_ml", False), ("writes", False), ("network_calls", False)])),
    ])
    payload["d8_checksum"] = _stable_checksum(payload)
    return payload


def build_d8_dashboard_view_model(d8_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    rankings = d8_payload.get("supporting_evidence_rankings") if isinstance(d8_payload.get("supporting_evidence_rankings"), Mapping) else {}
    contradictions = d8_payload.get("contradiction_priority_summary") if isinstance(d8_payload.get("contradiction_priority_summary"), Mapping) else {}
    return OrderedDict([
        ("strongest_supporting_evidence_panel", rankings.get("strongest_supporting_evidence") or {}),
        ("strongest_contradiction_panel", contradictions.get("top_contradiction") or {}),
        ("evidence_priority_cards", _as_list(d8_payload.get("operational_insight_cards"))),
        ("operational_insight_cards", _as_list(d8_payload.get("operational_insight_cards"))),
        ("contradiction_severity_summaries", _as_list(contradictions.get("contradictions"))),
        ("evidence_lineage_summaries", d8_payload.get("evidence_lineage_trace") or {}),
    ])


def certify_d8_evidence_prioritization(d8_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("deterministic", True),
        ("read_only", True),
        ("replayable", True),
        ("checksum_present", bool(d8_payload.get("d8_checksum"))),
        ("forbidden_capability_inventory", deepcopy(d8_payload.get("forbidden_capability_inventory") or {})),
    ])


def build_d8_evidence_prioritization_report(d8_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("d8_version", d8_payload.get("d8_version")),
        ("top_supporting_evidence", ((d8_payload.get("supporting_evidence_rankings") or {}).get("strongest_supporting_evidence") or {}).get("evidence_ref")),
        ("top_contradiction_severity", ((d8_payload.get("contradiction_priority_summary") or {}).get("top_contradiction") or {}).get("severity")),
        ("operational_interpretation", deepcopy((d8_payload.get("operational_interpretation") or {}).get("interpretation_sentences") or [])),
        ("d8_checksum", d8_payload.get("d8_checksum")),
    ])
