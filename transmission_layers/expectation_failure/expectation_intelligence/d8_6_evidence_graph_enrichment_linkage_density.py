from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

D8_6_VERSION = "d8_6_evidence_graph_enrichment_linkage_density_v1"


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _uniq(values: list[Any]) -> list[str]:
    return sorted({_as_text(v) for v in values if _as_text(v)})


def build_d8_6_evidence_graph_enrichment_linkage_density(*, findings: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]], historical_runs_payloads: list[Mapping[str, Any]], e2_payload: Mapping[str, Any], d8_2_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    finding_rows = [f for f in _as_list(findings) if isinstance(f, Mapping)]
    evidence_rows = [e for e in _as_list(evidence_maps) if isinstance(e, Mapping)]
    history_rows = [h for h in _as_list(historical_runs_payloads) if isinstance(h, Mapping)]

    finding_ids = _uniq([f.get("finding_id") for f in finding_rows])
    evidence_to_findings: dict[str, set[str]] = {}
    finding_to_evidence: dict[str, set[str]] = {fid: set() for fid in finding_ids}
    all_evidence_refs = set()

    for row in evidence_rows:
        payload = row.get("payload") if isinstance(row.get("payload"), Mapping) else {}
        refs = _uniq([row.get("evidence_ref")] + _as_list(row.get("supporting_evidence_refs")) + _as_list(payload.get("supporting_evidence_refs")) + _as_list(row.get("evidence_refs")) + _as_list(payload.get("evidence_refs")))
        fids = _uniq([row.get("finding_id")] + _as_list(row.get("finding_refs")) + _as_list(payload.get("finding_refs")) + _as_list(payload.get("linked_finding_ids")))
        all_evidence_refs.update(refs)
        for ref in refs:
            evidence_to_findings.setdefault(ref, set()).update(fids)
        for fid in fids:
            if fid in finding_to_evidence:
                finding_to_evidence[fid].update(refs)

    linkages = [l for l in _as_list(e2_payload.get("evidence_finding_linkages")) if isinstance(l, Mapping)]
    for row in linkages:
        ref = _as_text(row.get("evidence_ref"))
        fid = _as_text(row.get("finding_id"))
        if not ref:
            continue
        all_evidence_refs.add(ref)
        if fid:
            evidence_to_findings.setdefault(ref, set()).add(fid)
            if fid in finding_to_evidence:
                finding_to_evidence[fid].add(ref)

    contradiction_map = [r for r in _as_list(e2_payload.get("contradiction_evidence_map")) if isinstance(r, Mapping)]
    contradiction_refs = set(_uniq([ref for r in contradiction_map for ref in _as_list(r.get("supporting_evidence_refs"))]))

    recurring_themes = _uniq(((d8_2_payload.get("semantic_persistence_summary") or {}).get("recurring_themes")))
    theme_support_profile = _as_list(((d8_2_payload.get("replay_density_inventory") or {}).get("semantic_memory_ref") or {}).get("theme_evidence_support_profile"))
    theme_linked_refs = set(_uniq([ref for row in theme_support_profile if isinstance(row, Mapping) for ref in _as_list(row.get("supporting_evidence_refs"))]))

    replay_refs = set()
    for row in history_rows:
        for e in _as_list(row.get("evidence_highlights")):
            if isinstance(e, Mapping):
                replay_refs.update(_uniq([e.get("evidence_ref")] + _as_list(e.get("supporting_evidence_refs"))))

    evidence_by_finding = OrderedDict((fid, len(finding_to_evidence.get(fid, set()))) for fid in sorted(finding_ids))
    findings_by_evidence = OrderedDict((ref, len(evidence_to_findings.get(ref, set()))) for ref in sorted(all_evidence_refs))

    ranked = []
    for ref in sorted(all_evidence_refs):
        linked_findings = sorted(evidence_to_findings.get(ref, set()))
        if not linked_findings:
            continue
        score = len(linked_findings) * 100
        score += 25 if ref in contradiction_refs else 0
        score += 15 if ref in theme_linked_refs else 0
        score += 10 if ref in replay_refs else 0
        ranked.append(OrderedDict([
            ("evidence_ref", ref),
            ("deterministic_rank_score", score),
            ("linked_findings", linked_findings),
            ("finding_multiplicity", len(linked_findings)),
            ("links_to_contradiction", ref in contradiction_refs),
            ("links_to_persistent_theme", ref in theme_linked_refs),
            ("appears_in_replay_history", ref in replay_refs),
        ]))
    ranked = sorted(ranked, key=lambda r: (-int(r["deterministic_rank_score"]), -int(r["finding_multiplicity"]), _as_text(r["evidence_ref"])))

    edges = sum(len(v) for v in evidence_to_findings.values())
    total_nodes = len(finding_ids) + len(all_evidence_refs)
    evidence_linked_findings = sum(1 for fid in finding_ids if finding_to_evidence.get(fid))
    unlinked_findings = len(finding_ids) - evidence_linked_findings
    multi_hop_count = sum(1 for ref, fids in evidence_to_findings.items() if len(fids) >= 2)

    weak_areas = []
    if unlinked_findings:
        weak_areas.append("findings_without_evidence_refs")
    if any(len(fids) == 0 for fids in evidence_to_findings.values()):
        weak_areas.append("evidence_refs_without_finding_refs")
    if contradiction_map and not contradiction_refs:
        weak_areas.append("contradiction_clusters_without_evidence_refs")
    if recurring_themes and not theme_linked_refs:
        weak_areas.append("persistent_themes_without_evidence_refs")
    if evidence_rows and edges == 0:
        weak_areas.append("evidence_maps_present_but_disconnected")
    if all(len(fids) <= 1 for fids in evidence_to_findings.values()) and evidence_to_findings:
        weak_areas.append("low_multiplicity_graph")
    if evidence_rows and not all_evidence_refs:
        weak_areas.append("schema_shape_gaps")

    linkage_density_score = round(edges / (total_nodes or 1), 3)
    if evidence_rows and not all_evidence_refs:
        status = "EVIDENCE_GRAPH_BLOCKED_SHAPE_GAP"
    elif not all_evidence_refs:
        status = "EVIDENCE_GRAPH_BLOCKED_NO_EVIDENCE"
    elif evidence_rows and edges == 0:
        status = "EVIDENCE_GRAPH_BLOCKED_SHAPE_GAP"
    elif linkage_density_score >= 0.7 and multi_hop_count > 0:
        status = "EVIDENCE_GRAPH_ENRICHED"
    else:
        status = "EVIDENCE_GRAPH_SPARSE_BUT_VALID"

    caveats = sorted(set(weak_areas))
    strongest = ranked[0] if ranked else None
    if strongest is None:
        strongest = OrderedDict([("evidence_ref", None), ("status", "Unavailable"), ("caveat", "no_rankable_linked_evidence")])

    payload = OrderedDict([
        ("d8_6_version", D8_6_VERSION),
        ("total_findings", len(finding_ids)),
        ("total_evidence_refs", len(all_evidence_refs)),
        ("total_graph_nodes", total_nodes),
        ("total_graph_edges", edges),
        ("evidence_linked_finding_count", evidence_linked_findings),
        ("unlinked_finding_count", unlinked_findings),
        ("contradiction_linked_evidence_count", len([r for r in all_evidence_refs if r in contradiction_refs])),
        ("theme_linked_evidence_count", len([r for r in all_evidence_refs if r in theme_linked_refs])),
        ("multi_hop_linkage_count", multi_hop_count),
        ("evidence_multiplicity_by_finding", evidence_by_finding),
        ("finding_multiplicity_by_evidence_ref", findings_by_evidence),
        ("strongest_evidence_candidates", ranked[:5]),
        ("strongest_supporting_evidence", strongest),
        ("weakest_linkage_areas", caveats),
        ("linkage_density_score", linkage_density_score),
        ("linkage_caveats", caveats),
        ("enrichment_status", status),
        ("forbidden_capability_inventory", OrderedDict([("prediction_engine", False), ("trading_recommendation", False), ("execution_engine", False), ("black_box_ml", False), ("writes", False), ("network_calls", False)])),
    ])
    payload["d8_6_checksum"] = _stable_checksum(payload)
    return payload


def build_d8_6_dashboard_view_model(d8_6_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("enrichment_status", d8_6_payload.get("enrichment_status")),
        ("linkage_density_score", d8_6_payload.get("linkage_density_score")),
        ("strongest_supporting_evidence", deepcopy(d8_6_payload.get("strongest_supporting_evidence") or {})),
        ("strongest_evidence_candidates", deepcopy(d8_6_payload.get("strongest_evidence_candidates") or [])),
        ("weakest_linkage_areas", deepcopy(d8_6_payload.get("weakest_linkage_areas") or [])),
    ])
