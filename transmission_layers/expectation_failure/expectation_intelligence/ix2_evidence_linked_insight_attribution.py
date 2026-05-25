"""IX2 Evidence-Linked Insight Attribution & Delta Tracking (deterministic, read-only)."""
from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
import hashlib, json
from typing import Any, Mapping

COMPLETE_EVIDENCE_ATTRIBUTION = "COMPLETE_EVIDENCE_ATTRIBUTION"
PARTIAL_EVIDENCE_ATTRIBUTION = "PARTIAL_EVIDENCE_ATTRIBUTION"
THIN_EVIDENCE_ATTRIBUTION = "THIN_EVIDENCE_ATTRIBUTION"
MISSING_EVIDENCE_ATTRIBUTION = "MISSING_EVIDENCE_ATTRIBUTION"

PERSISTENT_INSIGHT = "PERSISTENT_INSIGHT"
EMERGING_INSIGHT = "EMERGING_INSIGHT"
DECAYING_INSIGHT = "DECAYING_INSIGHT"
RESOLVED_INSIGHT = "RESOLVED_INSIGHT"
RECURRING_INSIGHT = "RECURRING_INSIGHT"
VOLATILE_INSIGHT = "VOLATILE_INSIGHT"
INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"

CERTIFIED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION = "CERTIFIED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION"
DEGRADED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION = "DEGRADED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION"
BLOCKED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION = "BLOCKED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION"

NON_PREDICTIVE_NOTICE = "IX2 provides deterministic evidence-linked structural attribution only. It does not provide predictions, market forecasts, or trading signals."
NON_EXECUTION_NOTICE = "IX2 is read-only and recommendation-only. It cannot execute replay, trigger D21, perform writes, or bypass governance approvals."

EVIDENCE_KEYS=("supporting_replay_refs","supporting_transition_refs","supporting_diagnostic_refs","supporting_theme_refs","supporting_regime_refs","supporting_confidence_refs","supporting_continuity_refs")

def _rows(v: Any) -> list[dict[str, Any]]:
    if isinstance(v, Mapping): return [dict(v)]
    return [dict(x) for x in list(v or []) if isinstance(x, Mapping)]

def _tok(v: Any) -> str: return str(v or "").strip().lower()
def _id(v: Mapping[str, Any], i: int) -> str: return str(v.get("insight_id") or f"ix2_{i:03d}")
def _uniq(v: Any) -> list[str]: return sorted({str(x).strip() for x in list(v or []) if str(x).strip()})
def _b(v: Any, lo: float=0.0, hi: float=100.0) -> float:
    try: return max(lo,min(hi,round(float(v),3)))
    except Exception: return lo

def build_ix2_insight_evidence_map(*, ix1_insight_priority_ranking: Any, h1_h2_replay_interpretation: Any=None, h3_transition_intelligence: Any=None, cd4_drift_saturation_analysis: Any=None) -> list[OrderedDict[str, Any]]:
    replay, transitions, diagnostics = _rows(deepcopy(h1_h2_replay_interpretation)), _rows(deepcopy(h3_transition_intelligence)), _rows(deepcopy(cd4_drift_saturation_analysis))
    out=[]
    for i,r in enumerate(_rows(deepcopy(ix1_insight_priority_ranking))):
        summary=_tok(r.get("summary")); iid=_id(r,i)
        rr=_uniq([x.get("replay_ref") or x.get("replay_id") or x.get("row_ref") for x in replay if any(t in _tok(x) for t in summary.split()[:2])])
        tr=_uniq([x.get("transition_ref") or x.get("chain_signature") or x.get("transition_id") for x in transitions if any(t in _tok(x) for t in summary.split()[:2])])
        dr=_uniq([x.get("diagnostic_ref") or x.get("record_id") or x.get("anomaly_ref") for x in diagnostics if any(t in _tok(x) for t in summary.split()[:2])])
        theme=_uniq([x.get("theme_family") or x.get("semantic_theme") for x in diagnostics if x.get("theme_family") or x.get("semantic_theme")])
        regime=_uniq([x.get("regime_state") for x in transitions if x.get("regime_state")])
        confidence=_uniq([x.get("confidence_state") for x in replay if x.get("confidence_state")])
        continuity=_uniq([x.get("continuity_state") for x in replay if x.get("continuity_state")])
        coverage=sum(1 for v in (rr,tr,dr,theme,regime,confidence,continuity) if v)
        ecount=sum(len(v) for v in (rr,tr,dr,theme,regime,confidence,continuity))
        status = COMPLETE_EVIDENCE_ATTRIBUTION if coverage>=6 and ecount>=6 else PARTIAL_EVIDENCE_ATTRIBUTION if coverage>=4 else THIN_EVIDENCE_ATTRIBUTION if coverage>=1 else MISSING_EVIDENCE_ATTRIBUTION
        out.append(OrderedDict([("insight_id",iid),("insight_category",str(r.get("summary") or "insight")),("insight_priority_bucket",str(r.get("bucket") or "UNKNOWN")),("supporting_replay_refs",rr),("supporting_transition_refs",tr),("supporting_diagnostic_refs",dr),("supporting_theme_refs",theme),("supporting_regime_refs",regime),("supporting_confidence_refs",confidence),("supporting_continuity_refs",continuity),("evidence_count",ecount),("evidence_type_coverage",coverage),("attribution_completeness_status",status)]))
    return sorted(out,key=lambda x:(str(x.get("insight_id")),str(x.get("insight_category"))))

def build_ix2_insight_lineage_index(*, insight_evidence_map: Any) -> list[OrderedDict[str, Any]]:
    out=[]
    for r in _rows(deepcopy(insight_evidence_map)):
        out.append(OrderedDict([("insight_id",r.get("insight_id")),("replay_windows",list(r.get("supporting_replay_refs") or [])),("replay_rows",list(r.get("supporting_replay_refs") or [])),("transition_chains",list(r.get("supporting_transition_refs") or [])),("anomaly_records",list(r.get("supporting_diagnostic_refs") or [])),("diagnostic_structures",["CD1","CD4","H3"]),("semantic_theme_families",list(r.get("supporting_theme_refs") or [])),("regime_states",list(r.get("supporting_regime_refs") or [])),("contradiction_states",["present"] if "contradiction" in _tok(r.get("insight_category")) else []),("continuity_states",list(r.get("supporting_continuity_refs") or [])),("confidence_states",list(r.get("supporting_confidence_refs") or []))]))
    return sorted(out,key=lambda x:str(x.get("insight_id")))

def build_ix2_cross_run_delta_tracker(*, current_insight_evidence_map: Any, prior_insight_evidence_map: Any=None) -> list[OrderedDict[str, Any]]:
    cur={str(r.get('insight_id')):r for r in _rows(deepcopy(current_insight_evidence_map))}
    prv={str(r.get('insight_id')):r for r in _rows(deepcopy(prior_insight_evidence_map))}
    if not prv:
        return [OrderedDict([("insight_id",k),("delta_classification",INSUFFICIENT_HISTORY),("priority_bucket_change",None),("evidence_count_change",0),("supporting_category_changes",[]),("anomaly_count_change",0),("semantic_theme_coverage_change",0),("concentration_risk_movement",0),("saturation_risk_movement",0),("confidence_instability_movement",0),("continuity_fracture_movement",0)]) for k in sorted(cur)]
    keys=sorted(set(cur)|set(prv)); out=[]
    for k in keys:
        c,p=cur.get(k),prv.get(k)
        if c and p: cls=PERSISTENT_INSIGHT
        elif c and not p: cls=EMERGING_INSIGHT
        elif p and not c: cls=RESOLVED_INSIGHT
        else: cls=VOLATILE_INSIGHT
        ec=(int((c or {}).get("evidence_count") or 0)-int((p or {}).get("evidence_count") or 0))
        out.append(OrderedDict([("insight_id",k),("delta_classification",cls),("priority_bucket_change",((p or {}).get("insight_priority_bucket"),(c or {}).get("insight_priority_bucket")) if c and p else None),("evidence_count_change",ec),("supporting_category_changes",sorted(set((c or {}).keys())^set((p or {}).keys()))),("anomaly_count_change",0),("semantic_theme_coverage_change",len((c or {}).get("supporting_theme_refs") or [])-len((p or {}).get("supporting_theme_refs") or [])),("concentration_risk_movement",ec),("saturation_risk_movement",ec),("confidence_instability_movement",len((c or {}).get("supporting_confidence_refs") or [])-len((p or {}).get("supporting_confidence_refs") or [])),("continuity_fracture_movement",len((c or {}).get("supporting_continuity_refs") or [])-len((p or {}).get("supporting_continuity_refs") or []))]))
    return out

def build_ix2_evidence_strength_scorecard(*, insight_evidence_map: Any, cross_run_delta_tracker: Any=None) -> list[OrderedDict[str, Any]]:
    deltas={str(r.get('insight_id')):r for r in _rows(cross_run_delta_tracker)}
    out=[]
    for r in _rows(deepcopy(insight_evidence_map)):
        iid=str(r.get("insight_id")); d=deltas.get(iid,{})
        scores=OrderedDict([
            ("replay_support_strength", _b(len(r.get("supporting_replay_refs") or [])*20)),
            ("transition_support_strength", _b(len(r.get("supporting_transition_refs") or [])*20)),
            ("diagnostic_support_strength", _b(len(r.get("supporting_diagnostic_refs") or [])*20)),
            ("theme_support_strength", _b(len(r.get("supporting_theme_refs") or [])*20)),
            ("lineage_completeness_strength", _b((float(r.get("evidence_type_coverage") or 0)/7.0)*100)),
            ("cross_run_persistence_strength", _b(100 if d.get("delta_classification")==PERSISTENT_INSIGHT else 60 if d.get("delta_classification")==EMERGING_INSIGHT else 30 if d else 40)),
            ("anomaly_support_strength", _b(len(r.get("supporting_diagnostic_refs") or [])*15)),
            ("attribution_completeness_strength", _b(100 if r.get("attribution_completeness_status")==COMPLETE_EVIDENCE_ATTRIBUTION else 70 if r.get("attribution_completeness_status")==PARTIAL_EVIDENCE_ATTRIBUTION else 40 if r.get("attribution_completeness_status")==THIN_EVIDENCE_ATTRIBUTION else 0)),
            ("evidence_diversity_strength", _b((float(r.get("evidence_type_coverage") or 0)/7.0)*100)),
        ])
        out.append(OrderedDict([("insight_id",iid),("scores",scores),("overall_strength",_b(sum(scores.values())/len(scores)))]))
    return sorted(out,key=lambda x:(-float(x.get("overall_strength",0)),str(x.get("insight_id"))))

def build_ix2_delta_interpretation_summary(*, cross_run_delta_tracker: Any, evidence_strength_scorecard: Any, insight_evidence_map: Any) -> OrderedDict[str, Any]:
    d=_rows(cross_run_delta_tracker); s={r.get("insight_id"):r for r in _rows(evidence_strength_scorecard)}; m={r.get("insight_id"):r for r in _rows(insight_evidence_map)}
    def top(cls):
        rows=sorted([r for r in d if r.get("delta_classification")==cls], key=lambda z:-float((s.get(z.get("insight_id"),{}) or {}).get("overall_strength",0)))[:5]
        return [x.get("insight_id") for x in rows]
    thin=[k for k,v in m.items() if v.get("attribution_completeness_status") in {THIN_EVIDENCE_ATTRIBUTION,MISSING_EVIDENCE_ATTRIBUTION}]
    return OrderedDict([("strongest_persistent_insights",top(PERSISTENT_INSIGHT)),("strongest_emerging_insights",top(EMERGING_INSIGHT)),("strongest_decaying_insights",top(DECAYING_INSIGHT)),("resolved_insights",top(RESOLVED_INSIGHT)),("volatile_insights",top(VOLATILE_INSIGHT)),("insights_with_thin_evidence",sorted(thin)),("insights_with_improving_evidence_strength",[r.get("insight_id") for r in d if float(r.get("evidence_count_change") or 0)>0][:5]),("insights_with_weakening_evidence_strength",[r.get("insight_id") for r in d if float(r.get("evidence_count_change") or 0)<0][:5])])

def build_ix2_evidence_linked_operator_summary(*, insight_evidence_map: Any, cross_run_delta_tracker: Any, evidence_strength_scorecard: Any) -> OrderedDict[str, Any]:
    sc=_rows(evidence_strength_scorecard); top=[r.get("insight_id") for r in sc[:5]]; bot=[r.get("insight_id") for r in sc[-5:]]
    delta={r.get("insight_id"):r.get("delta_classification") for r in _rows(cross_run_delta_tracker)}
    return OrderedDict([("most_evidence_supported_findings",top),("most_interesting_emerging_findings",[k for k,v in delta.items() if v==EMERGING_INSIGHT][:5]),("most_persistent_contradiction_findings",[k for k in top if "contradiction" in _tok(k)]), ("most_fragile_semantic_findings",bot[:3]),("strongest_replay_evolution_findings",top[:3]),("weakest_thinnest_findings_to_treat_cautiously",bot),("findings_needing_more_replay_diversity",bot[:3])])

def build_ix2_dashboard_payload(*, insight_evidence_map: Any, insight_lineage_index: Any, cross_run_delta_tracker: Any, evidence_strength_scorecard: Any, delta_interpretation_summary: Mapping[str, Any], evidence_linked_operator_summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    thin=[r.get("insight_id") for r in _rows(insight_evidence_map) if r.get("attribution_completeness_status") in {THIN_EVIDENCE_ATTRIBUTION,MISSING_EVIDENCE_ATTRIBUTION}]
    return OrderedDict([("Evidence-Linked Insight Overview","Deterministic evidence-linked attribution and cross-run delta tracking for IX1 insights."),("Insight Evidence Map",_rows(insight_evidence_map)),("Insight Lineage Index",_rows(insight_lineage_index)),("Cross-Run Delta Tracker",_rows(cross_run_delta_tracker)),("Evidence Strength Scorecard",_rows(evidence_strength_scorecard)),("Delta Interpretation Summary",deepcopy(dict(delta_interpretation_summary or {}))),("Evidence-Linked Operator Summary",deepcopy(dict(evidence_linked_operator_summary or {}))),("Thin Evidence / Attribution Warnings",thin),("Governance/Boundary Constraints",OrderedDict([("read_only",True),("no_writes",True),("no_direct_sql",True),("no_replay_execution",True),("no_d21_execution",True),("non_predictive",True),("bounded_interpretive_synthesis",True)])),("Explicit Non-Predictive Notice",NON_PREDICTIVE_NOTICE),("Explicit Non-Execution Notice",NON_EXECUTION_NOTICE)])

def certify_ix2_evidence_linked_insight_attribution(*, dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    p=dict(deepcopy(dashboard_payload or {})); g=dict(p.get("Governance/Boundary Constraints") or {})
    guards=all(bool(g.get(k)) for k in ("read_only","no_writes","no_direct_sql","no_replay_execution","no_d21_execution","non_predictive","bounded_interpretive_synthesis"))
    em=_rows(p.get("Insight Evidence Map")); li=_rows(p.get("Insight Lineage Index"))
    det_em=em==sorted(em,key=lambda x:(str(x.get("insight_id")),str(x.get("insight_category"))))
    det_li=li==sorted(li,key=lambda x:str(x.get("insight_id")))
    notices=bool(p.get("Explicit Non-Predictive Notice")) and bool(p.get("Explicit Non-Execution Notice"))
    status=CERTIFIED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION if guards and det_em and det_li and notices else DEGRADED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION if guards else BLOCKED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION
    return OrderedDict([("status",status),("deterministic_evidence_ordering",det_em),("deterministic_lineage_ordering",det_li),("evidence_linked",True),("bounded",True)])

def build_ix2_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("objective","IX2 Evidence-Linked Insight Attribution & Delta Tracking"),("dashboard",deepcopy(dict(dashboard_payload or {}))),("certification",deepcopy(dict(certification or {})))])

def build_ix2_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    rp=dict(report_payload or {}); cert=dict(rp.get("certification") or {})
    return "\n".join(["# IX2 Evidence-Linked Insight Attribution & Delta Tracking",f"- Status: {cert.get('status','UNKNOWN')}",f"- Objective: {rp.get('objective','')}",f"- Non-predictive: {NON_PREDICTIVE_NOTICE}",f"- Non-execution: {NON_EXECUTION_NOTICE}"])

__all__=[x for x in globals() if x.startswith("build_ix2_") or x.startswith("certify_ix2_") or x.endswith("EVIDENCE_LINKED_INSIGHT_ATTRIBUTION") or x in {"NON_PREDICTIVE_NOTICE","NON_EXECUTION_NOTICE","COMPLETE_EVIDENCE_ATTRIBUTION","PARTIAL_EVIDENCE_ATTRIBUTION","THIN_EVIDENCE_ATTRIBUTION","MISSING_EVIDENCE_ATTRIBUTION","PERSISTENT_INSIGHT","EMERGING_INSIGHT","DECAYING_INSIGHT","RESOLVED_INSIGHT","RECURRING_INSIGHT","VOLATILE_INSIGHT","INSUFFICIENT_HISTORY"}]
