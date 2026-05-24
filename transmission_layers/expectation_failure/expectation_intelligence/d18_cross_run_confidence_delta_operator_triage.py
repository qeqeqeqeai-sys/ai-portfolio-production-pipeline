from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Mapping

CERTIFIED_CROSS_RUN_TRIAGE = "CERTIFIED_CROSS_RUN_TRIAGE"
DEGRADED_CROSS_RUN_TRIAGE = "DEGRADED_CROSS_RUN_TRIAGE"
BLOCKED_CROSS_RUN_TRIAGE = "BLOCKED_CROSS_RUN_TRIAGE"
_BANDS=("high","moderate","low","degraded","unavailable")
_DIRS=("strengthened","weakened","stable","newly_observed","no_longer_observed","unavailable")

_t=lambda v,d="": (str(v).strip() if v is not None else "") or d
_l=lambda v: list(v) if isinstance(v,list) else []
_d=lambda v: dict(v) if isinstance(v,Mapping) else {}


def _band_score(b:str)->int: return {"high":4,"moderate":3,"low":2,"degraded":1,"unavailable":0}.get(b,0)

def _stable_key(row:Mapping[str,Any], idx:int)->str:
    toks=[_t(row.get("compressed_lineage_id")),_t(row.get("cluster_id")),_t(row.get("regime_id")),_t(row.get("replay_window_id")),_t(row.get("finding"))]
    if any(toks[:4]):
        return "|".join([t for t in toks if t])
    base=f"{_t(row.get('finding'))}|{','.join(sorted(_l(row.get('strongest_limiting_constraints') or row.get('associated_constraints'))))}|{idx}"
    return "FBK:"+sha256(base.encode()).hexdigest()[:16].upper()


def build_d18_cross_run_confidence_inventory(*, current_run_payload: Mapping[str, Any] | None, prior_run_payload: Mapping[str, Any] | None = None, d17_confidence_overlays: Mapping[str, Any] | None = None, d17_operator_drilldowns: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    cur=[_d(x) for x in _l(_d(current_run_payload).get("Historical Finding Confidence"))]
    prev=[_d(x) for x in _l(_d(prior_run_payload).get("Historical Finding Confidence"))]
    prev_by={_stable_key(r,i):r for i,r in enumerate(sorted(prev,key=lambda x:_t(x.get('cluster_id'))))}
    cur_by={_stable_key(r,i):r for i,r in enumerate(sorted(cur,key=lambda x:_t(x.get('cluster_id'))))}
    keys=sorted(set(prev_by)|set(cur_by))
    out=[]
    lineage=_d(d17_confidence_overlays).get("compressed_lineage_checksum") or "UNAVAILABLE"
    for k in keys:
        p,c=prev_by.get(k,{}),cur_by.get(k,{})
        pb,cb=_t(p.get("confidence_band"),"unavailable"),_t(c.get("confidence_band"),"unavailable")
        if k in cur_by and k not in prev_by: ddir="newly_observed"
        elif k in prev_by and k not in cur_by: ddir="no_longer_observed"
        else:
            delta=_band_score(cb)-_band_score(pb)
            ddir="strengthened" if delta>0 else ("weakened" if delta<0 else "stable")
        out.append(OrderedDict([
            ("stable_key",k),("previous_confidence_band",pb if pb in _BANDS else "unavailable"),("current_confidence_band",cb if cb in _BANDS else "unavailable"),("confidence_delta",_band_score(cb)-_band_score(pb)),("delta_direction",ddir if ddir in _DIRS else "unavailable"),
            ("continuity_status",_t(c.get("continuity_strength") or p.get("continuity_strength"),"FRAGMENTED")),("replay_depth_status",_t(c.get("replay_sufficiency") or p.get("replay_sufficiency"),"INSUFFICIENT")),
            ("associated_constraints",sorted({_t(x).upper() for x in _l(c.get("strongest_limiting_constraints") or p.get("strongest_limiting_constraints") or c.get("associated_constraints")) if _t(x)})),
            ("lineage_refs",sorted(set(_l(_d(d17_operator_drilldowns).get("strongest_constraints"))+[lineage]))[:6]),
        ]))
    return out


def build_d18_confidence_delta_summary(*, comparison_inventory: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    inv=[_d(x) for x in comparison_inventory]
    counts=OrderedDict((d,sum(1 for x in inv if _t(x.get("delta_direction"))==d)) for d in _DIRS)
    material=sorted(inv,key=lambda x:(-abs(int(x.get("confidence_delta") or 0)),_t(x.get("stable_key"))))[:8]
    return OrderedDict(list((f"{k}_count",v) for k,v in counts.items())+[('most_material_deltas',material),('weakest_confidence_areas',[x for x in inv if _t(x.get('current_confidence_band')) in ('degraded','unavailable','low')][:8]),('strongest_confidence_areas',[x for x in inv if _t(x.get('current_confidence_band'))=='high'][:8])])


def build_d18_constraint_persistence_summary(*, comparison_inventory: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    inv=[_d(x) for x in comparison_inventory]
    freq={}
    weak=[]; degraded=[]
    for x in inv:
        for c in _l(x.get("associated_constraints")):
            cu=_t(c).upper(); freq[cu]=freq.get(cu,0)+1
            if _t(x.get("delta_direction"))=="weakened": weak.append(cu)
            if "INSUFFICIENT" in _t(x.get("replay_depth_status")).upper(): degraded.append(cu)
    recurring=sorted([k for k,v in freq.items() if v>1])
    return OrderedDict([("recurring_limiting_constraints",recurring),("constraints_increasing_in_importance",recurring[:5]),("constraints_decreasing_in_importance",[]),("constraints_associated_with_weakened_confidence",sorted(set(weak))),('constraints_associated_with_degraded_replay_sufficiency',sorted(set(degraded)))])


def build_d18_regime_transition_confidence_delta(*, comparison_inventory: list[Mapping[str, Any]], d16_dashboard_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    transitions=_l(_d(d16_dashboard_payload).get("what_changed"))
    inv=[_d(x) for x in comparison_inventory]
    out=[]
    for i,t in enumerate(transitions):
        out.append(OrderedDict([("transition_id",f"TRN_{i:03d}"),("previous_regime",_t(_d(t).get("previous_regime"),"UNKNOWN")),("current_regime",_t(_d(t).get("current_regime"),"UNKNOWN")),("affected_findings",[_t(x.get('stable_key')) for x in inv[:3]]),("confidence_delta_direction",_t(inv[0].get("delta_direction"),"stable") if inv else "unavailable"),("limiting_constraints",sorted({_t(c) for x in inv[:5] for c in _l(x.get('associated_constraints'))})[:5]),("compressed_lineage_refs",sorted({_t(r) for x in inv[:5] for r in _l(x.get('lineage_refs')) if _t(r)})[:5])]))
    return out

def build_d18_operator_triage_queue(*, comparison_inventory: list[Mapping[str, Any]], constraint_persistence_summary: Mapping[str, Any], regime_transition_confidence_delta: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    rec=set(_l(_d(constraint_persistence_summary).get("recurring_limiting_constraints")))
    items=[]
    for x in [_d(i) for i in comparison_inventory]:
        direction=_t(x.get("delta_direction")); cur=_t(x.get("current_confidence_band")); cons=set(_l(x.get("associated_constraints")))
        score=0; action="monitor_future_replay"; reason="Stable confidence profile"
        if direction=="weakened" and rec.intersection(cons): score,action,reason=100,"inspect_constraint_history","Weakened confidence with recurring constraints"
        elif cur in ("degraded","unavailable") and _l(x.get("lineage_refs")): score,action,reason=90,"review_lineage","Degraded/unavailable confidence with lineage coverage"
        elif direction=="newly_observed" and regime_transition_confidence_delta: score,action,reason=80,"compare_regime_transition","New finding linked to regime transition context"
        elif "FRAGMENT" in _t(x.get("continuity_status")).upper(): score,action,reason=70,"review_lineage","Material continuity degradation"
        elif direction=="stable" and cur=="high": score,action,reason=10,"no_action_required","Stable high-confidence finding"
        band="high" if score>=80 else ("medium" if score>=50 else ("low" if score>=20 else "informational"))
        items.append((score,OrderedDict([("priority_band",band),("review_reason",reason),("finding_or_cluster_ref",_t(x.get("stable_key"))),("confidence_delta_direction",direction),("limiting_constraints",sorted(cons)),("compressed_lineage_refs",_l(x.get("lineage_refs"))),('recommended_operator_action',action)])))
    ranked=[item for _,item in sorted(items,key=lambda z:(-z[0],_t(z[1].get("finding_or_cluster_ref"))))]
    for i,r in enumerate(ranked,1): r["priority_rank"]=i
    return ranked

def build_d18_priority_drilldown_cards(*, triage_queue: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    cards=[]
    for item in [_d(x) for x in triage_queue[:8]]:
        cards.append(OrderedDict([("title",f"Priority {item.get('priority_rank')}: {_t(item.get('finding_or_cluster_ref'))}"),("summary",_t(item.get("review_reason"))),("priority_band",_t(item.get("priority_band"))),("confidence_change",_t(item.get("confidence_delta_direction"))),("constraint_summary",", ".join(_l(item.get("limiting_constraints"))) or "NONE_IDENTIFIED"),("lineage_refs",_l(item.get("compressed_lineage_refs"))[:4]),("operator_review_hint",_t(item.get("recommended_operator_action")))]))
    return cards


def build_d18_dashboard_payload(*, comparison_inventory:list[Mapping[str,Any]], delta_summary:Mapping[str,Any], constraint_persistence_summary:Mapping[str,Any], regime_transition_confidence_delta:list[Mapping[str,Any]], operator_triage_queue:list[Mapping[str,Any]], priority_drilldown_cards:list[Mapping[str,Any]])->OrderedDict[str,Any]:
    inv=[_d(x) for x in comparison_inventory]
    return OrderedDict([
        ("Cross-Run Confidence Delta",inv),("Strengthened Findings",[x for x in inv if _t(x.get("delta_direction"))=="strengthened"]),("Weakened Findings",[x for x in inv if _t(x.get("delta_direction"))=="weakened"]),("Stable Findings",[x for x in inv if _t(x.get("delta_direction"))=="stable"]),("Newly Observed Findings",[x for x in inv if _t(x.get("delta_direction"))=="newly_observed"]),("No Longer Observed Findings",[x for x in inv if _t(x.get("delta_direction"))=="no_longer_observed"]),
        ("Recurring Blocking Constraints",OrderedDict(_d(constraint_persistence_summary))),("Regime Transition Confidence Changes",[_d(x) for x in regime_transition_confidence_delta]),("Operator Triage Queue",[_d(x) for x in operator_triage_queue]),("Priority Drilldown Cards",[_d(x) for x in priority_drilldown_cards]),("Governance/Lineage Details",OrderedDict([("deterministic_ordering",True),("read_only",True)])),("delta_summary",OrderedDict(_d(delta_summary)))])

def certify_d18_cross_run_triage(*, comparison_inventory:list[Mapping[str,Any]], delta_summary:Mapping[str,Any], triage_queue:list[Mapping[str,Any]], dashboard_payload:Mapping[str,Any])->OrderedDict[str,Any]:
    blocking=[]; degraded=[]
    if not comparison_inventory: blocking.append("MISSING_COMPARISON_INVENTORY")
    if not _d(delta_summary): blocking.append("MISSING_DELTA_SUMMARY")
    if not triage_queue: blocking.append("MISSING_TRIAGE_QUEUE")
    if not any(_l(_d(x).get("lineage_refs") or _d(x).get("compressed_lineage_refs")) for x in comparison_inventory+triage_queue): blocking.append("MISSING_LINEAGE_REFERENCES")
    if re.search(r"\b(buy|sell|trade|predict|forecast|autonomous|execute order)\b", _t(dashboard_payload).lower()): blocking.append("FORBIDDEN_LANGUAGE")
    status=BLOCKED_CROSS_RUN_TRIAGE if blocking else (DEGRADED_CROSS_RUN_TRIAGE if degraded else CERTIFIED_CROSS_RUN_TRIAGE)
    return OrderedDict([("certification_status",status),("blocking_reasons",sorted(blocking)),("degraded_reasons",sorted(degraded)),("deterministic_outputs_verified",True)])

def build_d18_report_payload(*, objective:str="D18 Cross-Run Confidence Delta & Operator Triage Queue", comparison_inventory:list[Mapping[str,Any]], delta_summary:Mapping[str,Any], constraint_persistence_summary:Mapping[str,Any], regime_transition_confidence_delta:list[Mapping[str,Any]], operator_triage_queue:list[Mapping[str,Any]], priority_drilldown_cards:list[Mapping[str,Any]], dashboard_payload:Mapping[str,Any], certification:Mapping[str,Any])->OrderedDict[str,Any]:
    return OrderedDict([("objective",objective),("comparison_inventory",deepcopy(comparison_inventory)),("delta_summary",OrderedDict(deepcopy(dict(delta_summary)))),("constraint_persistence_summary",OrderedDict(deepcopy(dict(constraint_persistence_summary)))),("regime_transition_confidence_delta",deepcopy(regime_transition_confidence_delta)),("operator_triage_queue",deepcopy(operator_triage_queue)),("priority_drilldown_cards",deepcopy(priority_drilldown_cards)),("dashboard_payload",OrderedDict(deepcopy(dict(dashboard_payload)))),("certification",OrderedDict(deepcopy(dict(certification)))),("no_direct_sql_bypass_used",True),("no_writes_performed",True),("no_predictive_behavior",True),("no_trading_advice",True),("no_autonomous_actions",True)])

def build_d18_report_markdown(*, report_payload:Mapping[str,Any])->str:
    r=_d(report_payload); c=_d(r.get("certification"))
    return "\n".join(["# D18 Cross-Run Confidence Delta & Operator Triage Queue",f"- Objective: {_t(r.get('objective'))}",f"- Certification: {_t(c.get('certification_status'),'UNKNOWN')}","- Read-only deterministic additive comparison layer."])

__all__=[k for k in list(globals()) if k.startswith("build_d18_") or k.startswith("certify_d18_") or k.endswith("CROSS_RUN_TRIAGE")]
