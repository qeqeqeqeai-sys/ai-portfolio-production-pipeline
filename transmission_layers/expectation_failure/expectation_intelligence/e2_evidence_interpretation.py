from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _as_text(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def _tokenize(*parts: Any) -> set[str]:
    text = " ".join(_as_text(p).lower() for p in parts)
    return {t for t in "".join(ch if ch.isalnum() else " " for ch in text).split() if len(t) >= 3}


def classify_e2_evidence_quality_band(score: int) -> str:
    if score >= 75:
        return "strong"
    if score >= 50:
        return "moderate"
    if score >= 25:
        return "weak"
    return "insufficient"


def classify_e2_linkage_strength(score: int) -> str:
    return classify_e2_evidence_quality_band(score)


def build_e2_evidence_quality_profile(evidence: list[Mapping[str, Any]] | None) -> list[OrderedDict[str, Any]]:
    rows = deepcopy(_as_list(evidence))
    out: list[OrderedDict[str, Any]] = []
    for idx, row in enumerate(rows):
        payload = row.get("payload") if isinstance(row.get("payload"), Mapping) else {}
        summary = _as_text(payload.get("evidence_summary") or row.get("evidence_ref"))
        links = _as_list(payload.get("linked_finding_ids") or row.get("linked_finding_ids"))
        refs = _as_list(payload.get("kpi_references") or payload.get("evidence_references"))
        has_recency = bool(payload.get("as_of") or payload.get("window") or payload.get("period") or row.get("created_at"))
        score = 0
        drivers: list[str] = []
        caveats: list[str] = []
        if len(summary) >= 40:
            score += 20; drivers.append("specific_evidence_summary")
        else:
            caveats.append("low_specificity")
        if has_recency:
            score += 15; drivers.append("recency_metadata_present")
        else:
            caveats.append("missing_recency")
        if links:
            score += 20; drivers.append("explicit_finding_linkage")
        else:
            caveats.append("weak_linkage")
        if refs:
            score += 15; drivers.append("reference_completeness")
        else:
            caveats.append("reference_incomplete")
        if _tokenize(summary, payload.get("semantic_drivers")):
            score += 15; drivers.append("semantic_relevance_detected")
        if any(k in summary.lower() for k in ("contradict", "diverg", "conflict")):
            score += 10; drivers.append("contradiction_relevance")
        if _as_text(payload.get("confidence")):
            score += 5; drivers.append("confidence_support_present")
        else:
            caveats.append("confidence_support_missing")
        score = max(0, min(100, score))
        out.append(OrderedDict([
            ("evidence_ref", _as_text(row.get("evidence_ref") or f"evidence_{idx+1}")),
            ("evidence_quality_score", score),
            ("evidence_quality_band", classify_e2_evidence_quality_band(score)),
            ("evidence_quality_drivers", sorted(set(drivers))),
            ("evidence_quality_caveats", sorted(set(caveats))),
        ]))
    return sorted(out, key=lambda x: (-int(x["evidence_quality_score"]), _as_text(x["evidence_ref"])))


def build_e2_evidence_finding_linkages(evidence: list[Mapping[str, Any]] | None, findings: list[Mapping[str, Any]] | None) -> list[OrderedDict[str, Any]]:
    ev_rows = deepcopy(_as_list(evidence))
    f_rows = deepcopy(_as_list(findings))
    out: list[OrderedDict[str, Any]] = []
    for ev in ev_rows:
        ep = ev.get("payload") if isinstance(ev.get("payload"), Mapping) else {}
        ev_ref = _as_text(ev.get("evidence_ref"))
        ev_find = _as_text(ev.get("finding_id"))
        ev_tokens = _tokenize(ep.get("evidence_summary"), ep.get("semantic_drivers"), ep.get("contradiction_or_divergence_notes"))
        for f in f_rows:
            fp = f.get("payload") if isinstance(f.get("payload"), Mapping) else {}
            fid = _as_text(f.get("finding_id"))
            score = 0
            drivers=[]; caveats=[]
            if ev_find and fid and ev_find == fid:
                score += 40; drivers.append("explicit_finding_id_match")
            if _as_text(f.get("finding_type")) and _as_text(f.get("finding_type")).lower() in _as_text(ep.get("evidence_summary")).lower():
                score += 15; drivers.append("shared_theme_alignment")
            if _as_text(f.get("finding_severity") or f.get("severity")) and _as_text(f.get("finding_severity") or f.get("severity")).lower() in _as_text(ep.get("evidence_summary")).lower():
                score += 10; drivers.append("severity_term_overlap")
            overlap = len(ev_tokens & _tokenize(f.get("finding_title"), fp.get("finding_summary"), f.get("finding_type")))
            if overlap:
                score += min(20, overlap * 5); drivers.append("semantic_keyword_overlap")
            if _as_list(ep.get("kpi_references") or ep.get("evidence_references")):
                score += 10; drivers.append("reference_completeness")
            contr_text = (_as_text(fp.get("contradiction_or_divergence_notes")) + " " + _as_text(ep.get("contradiction_or_divergence_notes"))).lower()
            if any(k in contr_text for k in ("contradict", "diverg", "conflict")):
                score += 5; drivers.append("contradiction_alignment")
            if score == 0:
                caveats.append("no_direct_support_detected")
            score = max(0, min(100, score))
            out.append(OrderedDict([
                ("evidence_ref", ev_ref), ("finding_id", fid),
                ("linkage_strength_score", score),
                ("linkage_strength_band", classify_e2_linkage_strength(score)),
                ("linkage_drivers", sorted(set(drivers))),
                ("linkage_caveats", sorted(set(caveats))),
            ]))
    return sorted(out, key=lambda x: (-int(x["linkage_strength_score"]), _as_text(x["evidence_ref"]), _as_text(x["finding_id"])))


def build_e2_interpretation_support_chains(evidence, findings, narratives, e1_payload) -> list[OrderedDict[str, Any]]:
    linkages = build_e2_evidence_finding_linkages(evidence, findings)
    narrs = _as_list(narratives)
    e1_refs = sorted([k for k in _as_list(list((e1_payload or {}).keys())) if k.endswith("summary") or k.endswith("profile")])
    chains=[]
    for i, link in enumerate(linkages[:10], start=1):
        if link["linkage_strength_score"] < 25:
            continue
        fid = _as_text(link["finding_id"])
        nrefs = sorted({_as_text(n.get("narrative_section") or (n.get("payload") or {}).get("narrative_section") or "market_context") for n in narrs if fid in [str(x) for x in _as_list(n.get("related_finding_ids") or (n.get("payload") or {}).get("related_findings"))]})
        chains.append(OrderedDict([
            ("support_chain_id", f"e2_chain_{i:03d}"),
            ("evidence_refs", [link["evidence_ref"]]),
            ("finding_refs", [fid] if fid else []),
            ("narrative_refs", nrefs),
            ("e1_signal_refs", e1_refs[:5]),
            ("interpretation_claim", f"Evidence {link['evidence_ref']} supports finding {fid or 'unlinked'} with {link['linkage_strength_band']} support."),
            ("support_strength", int(link["linkage_strength_score"])),
            ("caveats", list(link["linkage_caveats"])),
        ]))
    return chains


def build_e2_support_chain_summary(chains) -> OrderedDict[str, Any]:
    rows=_as_list(chains)
    return OrderedDict([("chain_count", len(rows)), ("strong_chain_count", sum(1 for c in rows if int(c.get("support_strength",0))>=75)), ("weak_chain_count", sum(1 for c in rows if int(c.get("support_strength",0))<50))])


def build_e2_evidence_support_buckets(quality_profiles):
    rows=_as_list(quality_profiles)
    buckets=OrderedDict([(k,[]) for k in ("strong_supporting_evidence","moderate_supporting_evidence","weak_supporting_evidence","contradiction_evidence","missing_or_insufficient_evidence")])
    for row in rows:
        ref=_as_text(row.get("evidence_ref"))
        band=_as_text(row.get("evidence_quality_band"))
        if band=="strong": buckets["strong_supporting_evidence"].append(ref)
        elif band=="moderate": buckets["moderate_supporting_evidence"].append(ref)
        elif band=="weak": buckets["weak_supporting_evidence"].append(ref)
        else: buckets["missing_or_insufficient_evidence"].append(ref)
        if "contradiction_relevance" in _as_list(row.get("evidence_quality_drivers")):
            buckets["contradiction_evidence"].append(ref)
    for k in buckets: buckets[k]=sorted(set(buckets[k]))
    return buckets


def build_e2_contradiction_evidence_map(evidence, findings):
    links=build_e2_evidence_finding_linkages(evidence, findings)
    contrad=[l for l in links if "contradiction_alignment" in _as_list(l.get("linkage_drivers")) or "contradict" in _as_text(l.get("evidence_ref")).lower()]
    out=[]
    for i, l in enumerate(contrad, start=1):
        out.append(OrderedDict([
            ("contradiction_claim", f"Contradiction pattern linked to finding {l.get('finding_id') or 'unlinked'}"),
            ("supporting_evidence_refs", [l.get("evidence_ref")]),
            ("affected_findings", [l.get("finding_id")]),
            ("contradiction_strength", int(l.get("linkage_strength_score") or 0)),
            ("persistence_context", "derived_from_persisted_evidence_and_findings"),
            ("caveats", list(l.get("linkage_caveats") or [])),
        ]))
    return out


def build_e2_confidence_caveats(quality_profiles, linkages):
    caveats=[]
    if any("missing_recency" in _as_list(q.get("evidence_quality_caveats")) for q in _as_list(quality_profiles)): caveats.append("missing_recency")
    if any("low_specificity" in _as_list(q.get("evidence_quality_caveats")) for q in _as_list(quality_profiles)): caveats.append("low_specificity")
    if any(int(l.get("linkage_strength_score",0))<50 for l in _as_list(linkages)): caveats.append("weak_linkage")
    if any("contradiction_alignment" in _as_list(l.get("linkage_drivers")) for l in _as_list(linkages)): caveats.append("conflicting_evidence")
    if not _as_list(quality_profiles): caveats.append("sparse_evidence")
    return sorted(set(caveats))


def build_e2_evidence_interpretation_summary(quality_profiles, linkages, chains, contradiction_map, caveats):
    return OrderedDict([
        ("supporting_evidence_count", len(_as_list(quality_profiles))),
        ("strong_linkage_count", sum(1 for l in _as_list(linkages) if int(l.get("linkage_strength_score",0))>=75)),
        ("contradiction_claim_count", len(_as_list(contradiction_map))),
        ("missing_evidence_count", sum(1 for q in _as_list(quality_profiles) if _as_text(q.get("evidence_quality_band"))=="insufficient")),
        ("confidence_caveats", sorted(set(_as_list(caveats)))),
        ("chain_summary", build_e2_support_chain_summary(chains)),
    ])


def build_e2_strategist_evidence_brief(summary):
    return OrderedDict([
        ("what_supports_this", f"{summary.get('supporting_evidence_count',0)} persisted evidence items were evaluated."),
        ("how_strong_is_support", f"{summary.get('strong_linkage_count',0)} strong linkage relationships were detected deterministically."),
        ("what_contradicts_it", f"{summary.get('contradiction_claim_count',0)} contradiction-attributed claims are present."),
        ("what_is_missing", f"{summary.get('missing_evidence_count',0)} evidence items are insufficient."),
        ("trust_or_discount_guidance", "Trust conclusions with strong linkage and quality bands; discount areas flagged by caveats."),
    ])


def build_e2_evidence_interpretation_payload(findings, narratives, evidence, e1_payload):
    quality=build_e2_evidence_quality_profile(evidence)
    linkages=build_e2_evidence_finding_linkages(evidence, findings)
    chains=build_e2_interpretation_support_chains(evidence, findings, narratives, e1_payload)
    contradiction_map=build_e2_contradiction_evidence_map(evidence, findings)
    caveats=build_e2_confidence_caveats(quality, linkages)
    summary=build_e2_evidence_interpretation_summary(quality, linkages, chains, contradiction_map, caveats)
    payload=OrderedDict([
        ("e2_version","e2_evidence_interpretation_v1"),
        ("evidence_quality_profiles", quality),
        ("evidence_finding_linkages", linkages),
        ("interpretation_support_chains", chains),
        ("evidence_support_buckets", build_e2_evidence_support_buckets(quality)),
        ("contradiction_evidence_map", contradiction_map),
        ("confidence_caveats", caveats),
        ("evidence_interpretation_summary", summary),
        ("strategist_evidence_brief", build_e2_strategist_evidence_brief(summary)),
        ("forbidden_capability_inventory", OrderedDict([("prediction_engine", False), ("trading_recommendation", False), ("autonomous_reasoning", False), ("live_fetching", False), ("writes", False)])),
    ])
    payload["e2_checksum"]=_stable_checksum(payload)
    return payload
