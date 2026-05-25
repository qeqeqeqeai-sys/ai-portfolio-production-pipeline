"""IX3 Structural Narrative Compression & Insight Clustering (deterministic, read-only)."""
from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

ELIGIBLE_FOR_COMPRESSION="ELIGIBLE_FOR_COMPRESSION"
RETAIN_AS_DISTINCT_FINDINGS="RETAIN_AS_DISTINCT_FINDINGS"
EVIDENCE_TOO_THIN_TO_COMPRESS="EVIDENCE_TOO_THIN_TO_COMPRESS"
MIXED_SIGNALS_REVIEW_REQUIRED="MIXED_SIGNALS_REVIEW_REQUIRED"

HIGH_SIGNIFICANCE_STRUCTURAL_NARRATIVE="HIGH_SIGNIFICANCE_STRUCTURAL_NARRATIVE"
HIGH_EVIDENCE_PERSISTENT_CLUSTER="HIGH_EVIDENCE_PERSISTENT_CLUSTER"
HIGH_EMERGENCE_CLUSTER="HIGH_EMERGENCE_CLUSTER"
HIGH_SEMANTIC_FRAGILITY_CLUSTER="HIGH_SEMANTIC_FRAGILITY_CLUSTER"
HIGH_CONCENTRATION_RISK_CLUSTER="HIGH_CONCENTRATION_RISK_CLUSTER"
MODERATE_OPERATOR_RELEVANCE="MODERATE_OPERATOR_RELEVANCE"
LOW_OPERATOR_RELEVANCE="LOW_OPERATOR_RELEVANCE"
THIN_EVIDENCE_REVIEW_ONLY="THIN_EVIDENCE_REVIEW_ONLY"

CERTIFIED_STRUCTURAL_NARRATIVE_COMPRESSION="CERTIFIED_STRUCTURAL_NARRATIVE_COMPRESSION"
DEGRADED_STRUCTURAL_NARRATIVE_COMPRESSION="DEGRADED_STRUCTURAL_NARRATIVE_COMPRESSION"
BLOCKED_STRUCTURAL_NARRATIVE_COMPRESSION="BLOCKED_STRUCTURAL_NARRATIVE_COMPRESSION"

NON_PREDICTIVE_NOTICE="IX3 provides deterministic evidence-linked structural narrative compression only. It does not provide predictions, market forecasts, or trading signals."
NON_EXECUTION_NOTICE="IX3 is read-only and recommendation-only. It cannot execute replay, trigger D21, perform writes, or bypass governance approvals."

_CLUSTER_DIMENSIONS=("contradiction persistence","semantic fragility","transition anomaly","continuity fracture","confidence instability","replay concentration","expectation decay","recurring structural pattern","evidence-thin","mixed structural")

def _rows(v: Any)->list[dict[str, Any]]:
    if isinstance(v, Mapping): return [dict(v)]
    return [dict(x) for x in list(v or []) if isinstance(x, Mapping)]
def _tok(v: Any)->str: return str(v or "").strip().lower()
def _uniq(v: Any)->list[str]: return sorted({str(x).strip() for x in list(v or []) if str(x).strip()})

def _cluster_type(r: Mapping[str, Any])->str:
    t=_tok(r.get("insight_category") or r.get("summary") or r.get("insight_id"));
    if "contradiction" in t: return "contradiction persistence clusters"
    if "fragility" in t or "semantic" in t: return "semantic fragility clusters"
    if "transition" in t or "anomaly" in t: return "transition anomaly clusters"
    if "continuity" in t or "fracture" in t: return "continuity fracture clusters"
    if "confidence" in t or "instability" in t: return "confidence instability clusters"
    if "concentration" in t or "saturation" in t: return "replay concentration clusters"
    if "decay" in t: return "expectation decay clusters"
    return "recurring structural pattern clusters"

def build_ix3_insight_cluster_inventory(*, ix1_insight_priority_ranking: Any, ix2_insight_evidence_map: Any, ix2_cross_run_delta_tracker: Any=None) -> list[OrderedDict[str, Any]]:
    em={str(r.get('insight_id')):r for r in _rows(deepcopy(ix2_insight_evidence_map))}; deltas={str(r.get('insight_id')):r for r in _rows(deepcopy(ix2_cross_run_delta_tracker))}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for i,r in enumerate(_rows(deepcopy(ix1_insight_priority_ranking))):
        iid=str(r.get("insight_id") or f"ix3_{i:03d}"); ct=_cluster_type(r); grouped.setdefault(ct,[]).append({**r,"insight_id":iid,"evidence":em.get(iid,{})})
    out=[]
    for i,ct in enumerate(sorted(grouped)):
        members=sorted(grouped[ct], key=lambda x:str(x.get("insight_id")))
        member_refs=[m["insight_id"] for m in members]
        evid=_uniq([e for m in members for k in ("supporting_replay_refs","supporting_transition_refs","supporting_diagnostic_refs","supporting_theme_refs","supporting_regime_refs","supporting_confidence_refs","supporting_continuity_refs") for e in list((m.get("evidence") or {}).get(k) or [])])
        priorities=[str(m.get("bucket") or m.get("insight_priority_bucket") or "UNKNOWN") for m in members]
        deltas_local=[str((deltas.get(m['insight_id']) or {}).get("delta_classification") or "INSUFFICIENT_HISTORY") for m in members]
        thin=all(int((m.get("evidence") or {}).get("evidence_count") or 0)<=1 for m in members)
        mixed=len(set(deltas_local))>2
        comp=EVIDENCE_TOO_THIN_TO_COMPRESS if thin else MIXED_SIGNALS_REVIEW_REQUIRED if mixed else ELIGIBLE_FOR_COMPRESSION if len(members)>=2 else RETAIN_AS_DISTINCT_FINDINGS
        sig=min(100.0, round(35+len(members)*10+len(evid)*2,3))
        out.append(OrderedDict([("cluster_id",f"ix3_cluster_{i:03d}"),("cluster_type",ct),("member_insight_refs",member_refs),("evidence_refs",evid),("dominant_theme",ct.replace(" clusters","")),("dominant_delta_classification",sorted(deltas_local)[0] if deltas_local else "INSUFFICIENT_HISTORY"),("dominant_priority_bucket",sorted(priorities)[0] if priorities else "UNKNOWN"),("cluster_size",len(member_refs)),("evidence_count",len(evid)),("redundancy_score",round(max(0.0,len(member_refs)-1)/max(1,len(member_refs)),3)),("structural_significance_score",sig),("compression_eligibility_status",comp)]))
    return out

def build_ix3_redundancy_and_overlap_analysis(*, insight_cluster_inventory: Any) -> OrderedDict[str, Any]:
    rows=_rows(deepcopy(insight_cluster_inventory)); total=max(1,sum(int(r.get("cluster_size") or 0) for r in rows)); redundant=sum(max(0,int(r.get("cluster_size") or 0)-1) for r in rows)
    dup=[OrderedDict([("cluster_id",r.get("cluster_id")),("theme",r.get("dominant_theme")),("member_count",r.get("cluster_size"))]) for r in rows if int(r.get("cluster_size") or 0)>=2]
    rep=[OrderedDict([("cluster_id",r.get("cluster_id")),("evidence_refs",list(r.get("evidence_refs") or []))]) for r in rows if len(list(r.get("evidence_refs") or []))>=2]
    return OrderedDict([("redundancy_density",round(redundant/total,3)),("overlap_families",[r.get("cluster_type") for r in rows]),("duplicate_theme_groups",dup),("repeated_evidence_groups",rep),("compression_candidates",[r.get("cluster_id") for r in rows if r.get("compression_eligibility_status")==ELIGIBLE_FOR_COMPRESSION]),("retain_distinct_candidates",[r.get("cluster_id") for r in rows if r.get("compression_eligibility_status")!=ELIGIBLE_FOR_COMPRESSION])])

def build_ix3_cluster_priority_ranking(*, insight_cluster_inventory: Any) -> list[OrderedDict[str, Any]]:
    out=[]
    for r in _rows(deepcopy(insight_cluster_inventory)):
        sig=float(r.get("structural_significance_score") or 0); e=int(r.get("evidence_count") or 0); d=_tok(r.get("dominant_delta_classification")); t=_tok(r.get("cluster_type")); c=r.get("compression_eligibility_status")
        if c==EVIDENCE_TOO_THIN_TO_COMPRESS: b=THIN_EVIDENCE_REVIEW_ONLY
        elif sig>=85: b=HIGH_SIGNIFICANCE_STRUCTURAL_NARRATIVE
        elif "persistent" in d: b=HIGH_EVIDENCE_PERSISTENT_CLUSTER
        elif "emerging" in d: b=HIGH_EMERGENCE_CLUSTER
        elif "semantic" in t or "fragility" in t: b=HIGH_SEMANTIC_FRAGILITY_CLUSTER
        elif "concentration" in t: b=HIGH_CONCENTRATION_RISK_CLUSTER
        elif sig>=60 or e>=3: b=MODERATE_OPERATOR_RELEVANCE
        else: b=LOW_OPERATOR_RELEVANCE
        out.append(OrderedDict([("cluster_id",r.get("cluster_id")),("priority_bucket",b),("structural_significance",sig),("evidence_strength",e)]))
    return sorted(out,key=lambda x:(str(x.get("priority_bucket")), -float(x.get("structural_significance") or 0), str(x.get("cluster_id"))))

def build_ix3_compressed_structural_narratives(*, insight_cluster_inventory: Any) -> list[OrderedDict[str, Any]]:
    out=[]
    for i,r in enumerate(_rows(deepcopy(insight_cluster_inventory))):
        evid=list(r.get("evidence_refs") or [])
        caution=[]
        if r.get("compression_eligibility_status")==EVIDENCE_TOO_THIN_TO_COMPRESS: caution.append("thin_evidence")
        if r.get("compression_eligibility_status")==MIXED_SIGNALS_REVIEW_REQUIRED: caution.append("mixed_signals")
        out.append(OrderedDict([("narrative_id",f"ix3_narrative_{i:03d}"),("cluster_id",r.get("cluster_id")),("narrative_title",f"{r.get('dominant_theme','Structural')} narrative"),("compressed_finding",f"Cluster compresses {r.get('cluster_size',0)} related findings under {r.get('dominant_theme','structural')} with evidence-linked support."),("supporting_evidence_refs",evid),("finding_delta_classification",r.get("dominant_delta_classification")),("structural_significance",r.get("structural_significance_score")),("evidence_strength_summary",f"{len(evid)} evidence refs linked."),("caution_flags",caution),("non_predictive_notice",NON_PREDICTIVE_NOTICE)]))
    return out

def build_ix3_dominant_theme_summary(*, insight_cluster_inventory: Any)->OrderedDict[str, Any]:
    rows=sorted(_rows(deepcopy(insight_cluster_inventory)), key=lambda x:(-float(x.get("structural_significance_score") or 0),str(x.get("cluster_id"))))
    def pick(key:str):
        for r in rows:
            if key in _tok(r.get("cluster_type")): return r.get("dominant_theme")
        return "none"
    return OrderedDict([("strongest contradiction persistence theme",pick("contradiction")),("strongest semantic fragility theme",pick("semantic")),("strongest transition anomaly theme",pick("transition")),("strongest continuity fracture theme",pick("continuity")),("strongest concentration-risk theme",pick("concentration")),("strongest expectation decay theme",pick("decay")),("strongest recurring structural pattern theme",pick("recurring")),("thinnest-evidence theme",next((r.get("dominant_theme") for r in rows if r.get("compression_eligibility_status")==EVIDENCE_TOO_THIN_TO_COMPRESS),"none")),("most volatile theme",next((r.get("dominant_theme") for r in rows if "volatile" in _tok(r.get("dominant_delta_classification"))),"none")),("most persistent theme",next((r.get("dominant_theme") for r in rows if "persistent" in _tok(r.get("dominant_delta_classification"))),"none"))])

def build_ix3_operator_narrative_brief(*, compressed_structural_narratives: Any, insight_cluster_inventory: Any, cluster_priority_ranking: Any, redundancy_and_overlap_analysis: Mapping[str, Any]) -> OrderedDict[str, Any]:
    nar=_rows(compressed_structural_narratives); cl=_rows(insight_cluster_inventory); pr=_rows(cluster_priority_ranking)
    return OrderedDict([("top compressed narratives",nar[:5]),("highest-significance clusters",sorted([r.get("cluster_id") for r in cl], key=lambda x:x)[:5]),("redundant findings compressed",list((redundancy_and_overlap_analysis or {}).get("compression_candidates") or [])),("findings retained as distinct",list((redundancy_and_overlap_analysis or {}).get("retain_distinct_candidates") or [])),("thin-evidence narrative warnings",[n.get("narrative_id") for n in nar if "thin_evidence" in list(n.get("caution_flags") or [])]),("volatile/emerging narrative warnings",[n.get("narrative_id") for n in nar if any(x in _tok(n.get("finding_delta_classification")) for x in ("volatile","emerging"))]),("suggested operator focus areas",[r.get("cluster_id") for r in pr[:3]])])

def build_ix3_dashboard_payload(*, insight_cluster_inventory: Any, redundancy_and_overlap_analysis: Mapping[str, Any], compressed_structural_narratives: Any, dominant_theme_summary: Mapping[str, Any], cluster_priority_ranking: Any, operator_narrative_brief: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("Structural Narrative Compression Overview","Deterministic IX3 compression and clustering over IX1/IX2 evidence-linked findings."),("Insight Cluster Inventory",_rows(insight_cluster_inventory)),("Redundancy and Overlap Analysis",deepcopy(dict(redundancy_and_overlap_analysis or {}))),("Compressed Structural Narratives",_rows(compressed_structural_narratives)),("Dominant Theme Summary",deepcopy(dict(dominant_theme_summary or {}))),("Cluster Priority Ranking",_rows(cluster_priority_ranking)),("Operator Narrative Brief",deepcopy(dict(operator_narrative_brief or {}))),("Thin Evidence / Narrative Caution Flags",[r.get("narrative_id") for r in _rows(compressed_structural_narratives) if list(r.get("caution_flags") or [])]),("Governance/Boundary Constraints",OrderedDict([("read_only",True),("no_writes",True),("no_direct_sql",True),("no_replay_execution",True),("no_d21_execution",True),("non_predictive",True),("bounded_interpretive_synthesis",True)])),("Explicit Non-Predictive Notice",NON_PREDICTIVE_NOTICE),("Explicit Non-Execution Notice",NON_EXECUTION_NOTICE)])

def certify_ix3_structural_narrative_compression(*, dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    p=dict(deepcopy(dashboard_payload or {})); g=dict(p.get("Governance/Boundary Constraints") or {})
    guards=all(bool(g.get(k)) for k in ("read_only","no_writes","no_direct_sql","no_replay_execution","no_d21_execution","non_predictive","bounded_interpretive_synthesis"))
    cl=_rows(p.get("Insight Cluster Inventory")); na=_rows(p.get("Compressed Structural Narratives"))
    det_cl=cl==sorted(cl,key=lambda x:str(x.get("cluster_id"))); det_na=na==sorted(na,key=lambda x:str(x.get("narrative_id")))
    linked=all(set(list(n.get("supporting_evidence_refs") or [])).issubset(set(e for c in cl for e in list(c.get("evidence_refs") or []))) for n in na)
    notices=bool(p.get("Explicit Non-Predictive Notice")) and bool(p.get("Explicit Non-Execution Notice"))
    status=CERTIFIED_STRUCTURAL_NARRATIVE_COMPRESSION if guards and det_cl and det_na and linked and notices else DEGRADED_STRUCTURAL_NARRATIVE_COMPRESSION if guards else BLOCKED_STRUCTURAL_NARRATIVE_COMPRESSION
    return OrderedDict([("status",status),("deterministic_cluster_ordering",det_cl),("deterministic_narrative_ordering",det_na),("evidence_linked",linked)])

def build_ix3_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any])->OrderedDict[str, Any]:
    return OrderedDict([("objective","IX3 Structural Narrative Compression & Insight Clustering"),("dashboard",deepcopy(dict(dashboard_payload or {}))),("certification",deepcopy(dict(certification or {})))])

def build_ix3_report_markdown(*, report_payload: Mapping[str, Any])->str:
    cert=dict((report_payload or {}).get("certification") or {})
    return "\n".join(["# IX3 Structural Narrative Compression & Insight Clustering",f"- Status: {cert.get('status','UNKNOWN')}",f"- Non-predictive: {NON_PREDICTIVE_NOTICE}",f"- Non-execution: {NON_EXECUTION_NOTICE}"])
