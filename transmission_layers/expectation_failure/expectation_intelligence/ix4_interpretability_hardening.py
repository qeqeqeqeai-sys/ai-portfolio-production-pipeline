"""IX4 Interpretability Hardening & Narrative Explainability (deterministic, read-only)."""
from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

CERTIFIED_INTERPRETABILITY_HARDENING = "CERTIFIED_INTERPRETABILITY_HARDENING"
DEGRADED_INTERPRETABILITY_HARDENING = "DEGRADED_INTERPRETABILITY_HARDENING"
BLOCKED_INTERPRETABILITY_HARDENING = "BLOCKED_INTERPRETABILITY_HARDENING"

NON_PREDICTIVE_NOTICE = "IX4 provides deterministic explainability hardening only. It does not provide predictions, forecasts, or trading signals."
NON_EXECUTION_NOTICE = "IX4 is read-only and recommendation-only. It cannot execute replay, trigger D21, perform writes, or bypass governance approvals."

PROHIBITED_PATTERNS = OrderedDict([
    ("predictive_phrasing", ("will rise", "will fall", "predict", "forecast")),
    ("trading_language", ("buy", "sell", "position", "entry", "exit", "alpha")),
    ("unsupported_causal_claims", ("causes", "guarantees", "proves")),
    ("speculative_certainty", ("certainly", "undoubtedly", "no doubt")),
    ("autonomous_conclusion_language", ("we conclude", "final answer is", "must execute")),
    ("execution_implication_language", ("execute replay", "trigger d21", "write to", "persist now")),
    ("unsupported_dramatic_framing", ("catastrophic", "inevitable collapse")),
])

def _rows(v: Any) -> list[dict[str, Any]]:
    if isinstance(v, Mapping):
        return [dict(v)]
    return [dict(x) for x in list(v or []) if isinstance(x, Mapping)]

def _tok(v: Any) -> str:
    return str(v or "").strip().lower()

def _score(n: float) -> float:
    return round(max(0.0, min(100.0, n)), 3)

def build_ix4_cluster_explainability_cards(*, ix3_cluster_inventory: Any, ix3_cluster_priority_ranking: Any, ix3_compressed_structural_narratives: Any) -> list[OrderedDict[str, Any]]:
    inv = sorted(_rows(deepcopy(ix3_cluster_inventory)), key=lambda r: str(r.get("cluster_id")))
    pri = {str(r.get("cluster_id")): r for r in _rows(deepcopy(ix3_cluster_priority_ranking))}
    narr = {str(r.get("cluster_id")): r for r in _rows(deepcopy(ix3_compressed_structural_narratives))}
    out = []
    for r in inv:
        cid = str(r.get("cluster_id"))
        ev = list(r.get("evidence_refs") or [])
        m = list(r.get("member_insight_refs") or [])
        c = str(r.get("compression_eligibility_status") or "UNKNOWN")
        caution = list((narr.get(cid) or {}).get("caution_flags") or [])
        score = _score(40 + len(ev) * 7 + len(m) * 5 - (15 if "THIN" in c else 0) - (10 if "MIXED" in c else 0))
        out.append(OrderedDict([
            ("cluster_id", cid),
            ("explainability_category", "high" if score >= 75 else "moderate" if score >= 55 else "weak"),
            ("grouping_rationale", f"Grouped by aligned structural theme {r.get('cluster_type')} with deterministic cluster typing."),
            ("shared_evidence_summary", f"{len(ev)} shared evidence refs across {len(m)} findings."),
            ("retained_distinct_summary", "Distinct findings retained when compression status is not eligible or ambiguity detected."),
            ("compression_rationale", f"Compression status: {c}; priority bucket: {(pri.get(cid) or {}).get('priority_bucket', 'UNKNOWN')}."),
            ("caution_flags", caution),
            ("interpretability_score", score),
            ("evidence_trace_refs", sorted({str(x) for x in ev if str(x).strip()})),
        ]))
    return out

def build_ix4_narrative_boundary_enforcement(*, narratives: Any) -> OrderedDict[str, Any]:
    rows = _rows(deepcopy(narratives))
    violations=[]; flagged=[]; phrases=[]
    for r in rows:
        text = " ".join(str(r.get(k) or "") for k in ("narrative_title","compressed_finding","narrative_text" )).lower()
        local=[]
        for kind, pats in PROHIBITED_PATTERNS.items():
            for p in pats:
                if p in text:
                    local.append(kind); phrases.append(p)
        if local:
            flagged.append(str(r.get("narrative_id") or r.get("cluster_id") or "unknown"))
            violations.extend(local)
    unique_v=sorted(set(violations)); unique_p=sorted(set(phrases))
    return OrderedDict([
        ("boundary_violations", unique_v),
        ("flagged_narratives", sorted(flagged)),
        ("flagged_phrases", unique_p),
        ("remediation_guidance", ["Remove predictive, trading, causal-certainty, and execution-implying language.", "Retain evidence-linked, non-causal, non-predictive framing."]),
        ("boundary_compliance_status", "COMPLIANT" if not unique_v else "VIOLATION_DETECTED"),
    ])

def build_ix4_narrative_explainability_analysis(*, ix3_compressed_structural_narratives: Any, ix4_cluster_explainability_cards: Any, ix2_cross_run_delta_tracker: Any=None) -> OrderedDict[str, Any]:
    nar = sorted(_rows(deepcopy(ix3_compressed_structural_narratives)), key=lambda r: str(r.get("narrative_id")))
    cards = {str(c.get("cluster_id")): c for c in _rows(deepcopy(ix4_cluster_explainability_cards))}
    boundary = build_ix4_narrative_boundary_enforcement(narratives=nar)
    weak=[n.get("narrative_id") for n in nar if float((cards.get(str(n.get('cluster_id'))) or {}).get("interpretability_score") or 0)<55]
    opaque=[n.get("narrative_id") for n in nar if len(list(n.get("supporting_evidence_refs") or []))==0]
    mixed=[n.get("narrative_id") for n in nar if "mixed_signals" in list(n.get("caution_flags") or [])]
    over=[n.get("narrative_id") for n in nar if "compresses" in _tok(n.get("compressed_finding")) and len(list(n.get("supporting_evidence_refs") or []))<=1]
    return OrderedDict([
        ("evidence_transparency", _score(100 - len(opaque)*20)),
        ("grouping_transparency", _score(100 - len(weak)*10)),
        ("compression_transparency", _score(100 - len(over)*20)),
        ("caution_transparency", _score(100 - len(mixed)*10)),
        ("structural_traceability", _score(100 - len(opaque)*15)),
        ("replay_grounding_clarity", _score(100 - len(opaque)*15)),
        ("delta_interpretation_clarity", _score(80 if ix2_cross_run_delta_tracker is None else 95)),
        ("non_predictive_clarity", _score(100 if boundary.get("boundary_compliance_status")=="COMPLIANT" else 60)),
        ("non_causal_framing_quality", _score(100 if "unsupported_causal_claims" not in set(boundary.get("boundary_violations") or []) else 50)),
        ("opaque_narratives", sorted(opaque)),("weakly_explained_clusters", sorted(set(str(n.get("cluster_id")) for n in nar if n.get("narrative_id") in weak))),
        ("insufficient_evidence_traceability", sorted(opaque)),("mixed_signal_ambiguity", sorted(mixed)),("over_compressed_narratives", sorted(over)),("weak_caution_framing", sorted([n.get("narrative_id") for n in nar if not list(n.get("caution_flags") or [])])),
    ])

def build_ix4_interpretability_scorecard(*, cluster_explainability_cards: Any, narrative_explainability_analysis: Mapping[str, Any], boundary_enforcement: Mapping[str, Any]) -> OrderedDict[str, Any]:
    cards=_rows(deepcopy(cluster_explainability_cards)); a=dict(deepcopy(narrative_explainability_analysis or {})); b=dict(deepcopy(boundary_enforcement or {}))
    avg = _score(sum(float(c.get("interpretability_score") or 0) for c in cards)/max(1,len(cards)))
    compliant=b.get("boundary_compliance_status")=="COMPLIANT"
    return OrderedDict([
        ("evidence_traceability_strength", _score(a.get("evidence_transparency",0))),
        ("grouping_explainability_strength", _score(a.get("grouping_transparency",0))),
        ("compression_explainability_strength", _score(a.get("compression_transparency",0))),
        ("structural_clarity_strength", avg),
        ("caution_clarity_strength", _score(a.get("caution_transparency",0))),
        ("replay_grounding_strength", _score(a.get("replay_grounding_clarity",0))),
        ("non_predictive_boundary_strength", _score(100 if compliant else 60)),
        ("non_execution_boundary_strength", _score(100 if compliant else 60)),
        ("auditability_strength", _score((avg + float(a.get("structural_traceability",0)))/2)),
    ])

def build_ix4_operator_explainability_summary(*, cluster_explainability_cards: Any, narrative_explainability_analysis: Mapping[str, Any], boundary_enforcement: Mapping[str, Any]) -> OrderedDict[str, Any]:
    cards=sorted(_rows(cluster_explainability_cards), key=lambda c:(-float(c.get("interpretability_score") or 0), str(c.get("cluster_id"))) )
    weak=sorted(cards, key=lambda c:(float(c.get("interpretability_score") or 0), str(c.get("cluster_id"))))
    return OrderedDict([
        ("best_explained_narratives", [c.get("cluster_id") for c in cards[:3]]),
        ("weakest_explainability_narratives", [c.get("cluster_id") for c in weak[:3]]),
        ("strongest_evidence_traceability_clusters", [c.get("cluster_id") for c in cards if len(list(c.get("evidence_trace_refs") or []))>=2][:3]),
        ("highest_caution_risk_clusters", [c.get("cluster_id") for c in cards if list(c.get("caution_flags") or [])][:3]),
        ("clusters_needing_interpretability_review", list((narrative_explainability_analysis or {}).get("weakly_explained_clusters") or [])),
        ("clusters_retained_distinct_due_to_ambiguity", [c.get("cluster_id") for c in cards if "not eligible" in _tok(c.get("compression_rationale"))]),
        ("narratives_with_strongest_governance_safe_framing", [] if boundary_enforcement.get("boundary_compliance_status")!="COMPLIANT" else [c.get("cluster_id") for c in cards[:3]]),
    ])

def build_ix4_auditability_preview(*, cluster_explainability_cards: Any, boundary_enforcement: Mapping[str, Any]) -> OrderedDict[str, Any]:
    cards=_rows(cluster_explainability_cards)
    return OrderedDict([
        ("narrative_lineage_previews", [OrderedDict([("cluster_id",c.get("cluster_id")),("evidence_trace_refs",c.get("evidence_trace_refs"))]) for c in cards[:5]]),
        ("evidence_trace_previews", [c.get("evidence_trace_refs") for c in cards[:5]]),
        ("grouping_rationale_previews", [c.get("grouping_rationale") for c in cards[:5]]),
        ("compression_rationale_previews", [c.get("compression_rationale") for c in cards[:5]]),
        ("caution_lineage_previews", [c.get("caution_flags") for c in cards[:5]]),
        ("boundary_enforcement_previews", deepcopy(dict(boundary_enforcement or {}))),
        ("replay_grounding_previews", [f"{c.get('cluster_id')}: replay-grounded via evidence refs" for c in cards[:5]]),
    ])

def build_ix4_dashboard_payload(*, ix3_cluster_inventory: Any, ix3_cluster_priority_ranking: Any, ix3_compressed_structural_narratives: Any, ix2_cross_run_delta_tracker: Any=None) -> OrderedDict[str, Any]:
    cards=build_ix4_cluster_explainability_cards(ix3_cluster_inventory=ix3_cluster_inventory, ix3_cluster_priority_ranking=ix3_cluster_priority_ranking, ix3_compressed_structural_narratives=ix3_compressed_structural_narratives)
    boundary=build_ix4_narrative_boundary_enforcement(narratives=ix3_compressed_structural_narratives)
    analysis=build_ix4_narrative_explainability_analysis(ix3_compressed_structural_narratives=ix3_compressed_structural_narratives, ix4_cluster_explainability_cards=cards, ix2_cross_run_delta_tracker=ix2_cross_run_delta_tracker)
    scorecard=build_ix4_interpretability_scorecard(cluster_explainability_cards=cards, narrative_explainability_analysis=analysis, boundary_enforcement=boundary)
    summary=build_ix4_operator_explainability_summary(cluster_explainability_cards=cards, narrative_explainability_analysis=analysis, boundary_enforcement=boundary)
    audit=build_ix4_auditability_preview(cluster_explainability_cards=cards, boundary_enforcement=boundary)
    return OrderedDict([("Interpretability Hardening Overview","Deterministic IX4 explainability hardening over IX3 narratives and clusters."),("Cluster Explainability Cards",cards),("Narrative Explainability Analysis",analysis),("Interpretability Scorecard",scorecard),("Narrative Boundary Enforcement",boundary),("Operator Explainability Summary",summary),("Auditability Preview",audit),("Governance/Boundary Constraints",OrderedDict([("read_only",True),("no_writes",True),("no_direct_sql",True),("no_replay_execution",True),("no_d21_execution",True),("non_predictive",True),("non_executing",True)])),("Explicit Non-Predictive Notice",NON_PREDICTIVE_NOTICE),("Explicit Non-Execution Notice",NON_EXECUTION_NOTICE)])

def certify_ix4_interpretability_hardening(*, dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    p=dict(deepcopy(dashboard_payload or {})); g=dict(p.get("Governance/Boundary Constraints") or {}); b=dict(p.get("Narrative Boundary Enforcement") or {})
    guards=all(bool(g.get(k)) for k in ("read_only","no_writes","no_direct_sql","no_replay_execution","no_d21_execution","non_predictive","non_executing"))
    cards=_rows(p.get("Cluster Explainability Cards")); det=cards==sorted(cards,key=lambda x:str(x.get("cluster_id")))
    linked=all(bool(c.get("evidence_trace_refs")) for c in cards) if cards else True
    bounded=all(0<=float(v)<=100 for v in dict(p.get("Interpretability Scorecard") or {}).values() if isinstance(v,(int,float)))
    clean=b.get("boundary_compliance_status")=="COMPLIANT"
    notices=bool(p.get("Explicit Non-Predictive Notice")) and bool(p.get("Explicit Non-Execution Notice")); audit=bool(p.get("Auditability Preview"))
    status=CERTIFIED_INTERPRETABILITY_HARDENING if all((guards,det,linked,bounded,clean,notices,audit)) else DEGRADED_INTERPRETABILITY_HARDENING if guards else BLOCKED_INTERPRETABILITY_HARDENING
    return OrderedDict([("status",status),("deterministic_explainability_ordering_preserved",det),("narratives_evidence_linked",linked),("interpretability_scores_bounded",bounded),("boundary_clean",clean)])

def build_ix4_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("objective","IX4 Interpretability Hardening & Narrative Explainability"),("dashboard",deepcopy(dict(dashboard_payload or {}))),("certification",deepcopy(dict(certification or {})))])

def build_ix4_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    cert=dict((report_payload or {}).get("certification") or {})
    return "\n".join(["# IX4 Interpretability Hardening & Narrative Explainability",f"- Status: {cert.get('status','UNKNOWN')}",f"- Non-predictive: {NON_PREDICTIVE_NOTICE}",f"- Non-execution: {NON_EXECUTION_NOTICE}"])
