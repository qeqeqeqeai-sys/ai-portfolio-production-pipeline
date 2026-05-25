from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

CERTIFIED_EXPLAINABILITY_CONTINUITY_CALIBRATION = "CERTIFIED_EXPLAINABILITY_CONTINUITY_CALIBRATION"
DEGRADED_EXPLAINABILITY_CONTINUITY_CALIBRATION = "DEGRADED_EXPLAINABILITY_CONTINUITY_CALIBRATION"
BLOCKED_EXPLAINABILITY_CONTINUITY_CALIBRATION = "BLOCKED_EXPLAINABILITY_CONTINUITY_CALIBRATION"
EXPLAINABILITY_IMPROVED = "EXPLAINABILITY_IMPROVED"
EXPLAINABILITY_STABLE = "EXPLAINABILITY_STABLE"
EXPLAINABILITY_DEGRADED = "EXPLAINABILITY_DEGRADED"
EXPLAINABILITY_VOLATILE = "EXPLAINABILITY_VOLATILE"
EXPLAINABILITY_INSUFFICIENT_HISTORY = "EXPLAINABILITY_INSUFFICIENT_HISTORY"
NON_PREDICTIVE_NOTICE = "IX5 provides deterministic explainability continuity calibration only. It does not provide predictions, forecasts, or trading signals."
NON_EXECUTION_NOTICE = "IX5 is read-only and recommendation-only. It cannot execute replay, trigger D21, perform writes, or bypass governance approvals."

BASELINE_KEYS = ("evidence_traceability_baseline","grouping_explainability_baseline","compression_explainability_baseline","structural_clarity_baseline","caution_clarity_baseline","replay_grounding_baseline","non_predictive_boundary_baseline","non_execution_boundary_baseline","auditability_baseline")

def _n(v: Any) -> float: return round(max(0.0, min(100.0, float(v or 0))), 3)
def _m(v: Any) -> dict[str, Any]: return dict(v) if isinstance(v, Mapping) else {}
def _low(v: Any) -> str: return str(v or "").strip().lower()

def build_ix5_explainability_baseline_profile(*, current_ix4_dashboard_payload: Mapping[str, Any], prior_ix4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    cur = _m(_m(current_ix4_dashboard_payload).get("Interpretability Scorecard"))
    prv = _m(_m(prior_ix4_dashboard_payload or {}).get("Interpretability Scorecard"))
    ks=("evidence_traceability_strength","grouping_explainability_strength","compression_explainability_strength","structural_clarity_strength","caution_clarity_strength","replay_grounding_strength","non_predictive_boundary_strength","non_execution_boundary_strength","auditability_strength")
    vals=[_n((cur.get(k, 0) if k in cur else prv.get(k, 0))) for k in ks]
    return OrderedDict([(k,v) for k,v in zip(BASELINE_KEYS,vals)])

def build_ix5_explainability_delta_analysis(*, current_ix4_dashboard_payload: Mapping[str, Any], prior_ix4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    if not prior_ix4_dashboard_payload:
        return OrderedDict([("delta_classification", EXPLAINABILITY_INSUFFICIENT_HISTORY), ("missing_history", True)])
    c = build_ix5_explainability_baseline_profile(current_ix4_dashboard_payload=current_ix4_dashboard_payload)
    p = build_ix5_explainability_baseline_profile(current_ix4_dashboard_payload=prior_ix4_dashboard_payload)
    moves = OrderedDict((k.replace("_baseline","_movement"), round(float(c[k])-float(p[k]),3)) for k in BASELINE_KEYS)
    avg = round(sum(moves.values())/max(1,len(moves)),3)
    span = round(max(moves.values())-min(moves.values()),3)
    cls = EXPLAINABILITY_STABLE
    if span >= 25: cls = EXPLAINABILITY_VOLATILE
    elif avg >= 2: cls = EXPLAINABILITY_IMPROVED
    elif avg <= -2: cls = EXPLAINABILITY_DEGRADED
    return OrderedDict([("delta_classification", cls), ("missing_history", False), ("score_movement", avg), ("bounded_score_movement", abs(avg)<=100), ("boundary_violation_movement", moves["non_predictive_boundary_movement"]), ("caution_flag_movement", moves["caution_clarity_movement"]), ("evidence_traceability_movement", moves["evidence_traceability_movement"]), ("grouping_rationale_movement", moves["grouping_explainability_movement"]), ("compression_rationale_movement", moves["compression_explainability_movement"]), ("auditability_movement", moves["auditability_movement"]), ("narrative_opacity_movement", -moves["structural_clarity_movement"]), ("all_movements", moves)])

def build_ix5_boundary_consistency_monitor(*, current_ix4_dashboard_payload: Mapping[str, Any], prior_ix4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    cur = set(_m(_m(current_ix4_dashboard_payload).get("Narrative Boundary Enforcement")).get("boundary_violations") or [])
    prv = set(_m(_m(prior_ix4_dashboard_payload or {}).get("Narrative Boundary Enforcement")).get("boundary_violations") or [])
    return OrderedDict([("predictive_phrasing_recurrence", "predictive_phrasing" in cur and "predictive_phrasing" in prv), ("trading_language_recurrence", "trading_language" in cur and "trading_language" in prv), ("unsupported_causal_claim_recurrence", "unsupported_causal_claims" in cur and "unsupported_causal_claims" in prv), ("autonomous_conclusion_language_recurrence", "autonomous_conclusion_language" in cur and "autonomous_conclusion_language" in prv), ("execution_implication_recurrence", "execution_implication_language" in cur and "execution_implication_language" in prv), ("dramatic_framing_recurrence", "unsupported_dramatic_framing" in cur and "unsupported_dramatic_framing" in prv), ("remediation_consistency", not cur or len(cur) <= len(prv) if prior_ix4_dashboard_payload else True), ("boundary_compliance_stability", "STABLE" if cur == prv else "SHIFTED")])

def build_ix5_narrative_calibration_stability(*, current_ix4_dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    a=_m(_m(current_ix4_dashboard_payload).get("Narrative Explainability Analysis")); b=_m(_m(current_ix4_dashboard_payload).get("Narrative Boundary Enforcement"))
    return OrderedDict([("proportionate_to_evidence_strength", _n(a.get("evidence_transparency")) >= 60), ("caution_alignment_with_evidence_thinness", _n(a.get("caution_transparency")) >= 55), ("compression_justified", _n(a.get("compression_transparency")) >= 55), ("high_priority_clusters_explainable", _n(a.get("grouping_transparency")) >= 55), ("mixed_signal_clusters_flagged", bool(a.get("mixed_signal_ambiguity"))), ("non_predictive_framing_explicit", _n(a.get("non_predictive_clarity")) >= 60), ("non_causal_framing_explicit", _n(a.get("non_causal_framing_quality")) >= 60), ("boundary_compliance_status", b.get("boundary_compliance_status", "UNKNOWN"))])

def build_ix5_operator_trust_continuity_summary(*, baseline_profile: Mapping[str, Any], delta_analysis: Mapping[str, Any], boundary_consistency_monitor: Mapping[str, Any], calibration_stability: Mapping[str, Any]) -> OrderedDict[str, Any]:
    degraded=[k for k,v in _m(delta_analysis).get("all_movements", {}).items() if float(v)<-5]
    stable=[k for k,v in _m(delta_analysis).get("all_movements", {}).items() if abs(float(v))<=2]
    return OrderedDict([("strongest_explainability_improvements", [k for k,v in _m(delta_analysis).get("all_movements", {}).items() if float(v)>5][:3]), ("most_stable_explainability_areas", stable[:4]), ("weakest_degraded_explainability_areas", degraded[:4]), ("recurring_boundary_concerns", [k for k,v in _m(boundary_consistency_monitor).items() if k.endswith("recurrence") and bool(v)]), ("narratives_requiring_recalibration", ["caution_alignment" ] if not calibration_stability.get("caution_alignment_with_evidence_thinness") else []), ("clusters_requiring_additional_evidence_traceability", ["traceability_follow_up"] if float(_m(baseline_profile).get("evidence_traceability_baseline",0))<60 else []), ("trust_continuity_warnings", ["volatile_explainability" ] if _m(delta_analysis).get("delta_classification")==EXPLAINABILITY_VOLATILE else []), ("calibration_strengths", [k for k,v in _m(calibration_stability).items() if isinstance(v,bool) and v])])

def build_ix5_calibration_recommendations(*, delta_analysis: Mapping[str, Any], boundary_consistency_monitor: Mapping[str, Any], calibration_stability: Mapping[str, Any]) -> list[str]:
    rec=[]
    if float(_m(delta_analysis).get("evidence_traceability_movement",0))<0: rec.append("improve evidence traceability")
    if float(_m(delta_analysis).get("grouping_rationale_movement",0))<0: rec.append("strengthen grouping rationale")
    if float(_m(delta_analysis).get("compression_rationale_movement",0))<0: rec.append("strengthen compression rationale")
    if float(_m(delta_analysis).get("caution_flag_movement",0))<0: rec.append("add caution flag detail")
    if not calibration_stability.get("compression_justified", True): rec.append("retain distinct findings instead of compression")
    if any(bool(v) for k,v in _m(boundary_consistency_monitor).items() if k.endswith("recurrence")): rec.append("review boundary wording")
    if calibration_stability.get("mixed_signal_clusters_flagged", False): rec.append("review mixed-signal narratives")
    if _m(delta_analysis).get("delta_classification")==EXPLAINABILITY_VOLATILE: rec.append("monitor volatile explainability areas")
    return sorted(set(rec))

def build_ix5_dashboard_payload(*, current_ix4_dashboard_payload: Mapping[str, Any], prior_ix4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    b=build_ix5_explainability_baseline_profile(current_ix4_dashboard_payload=current_ix4_dashboard_payload, prior_ix4_dashboard_payload=prior_ix4_dashboard_payload)
    d=build_ix5_explainability_delta_analysis(current_ix4_dashboard_payload=current_ix4_dashboard_payload, prior_ix4_dashboard_payload=prior_ix4_dashboard_payload)
    m=build_ix5_boundary_consistency_monitor(current_ix4_dashboard_payload=current_ix4_dashboard_payload, prior_ix4_dashboard_payload=prior_ix4_dashboard_payload)
    s=build_ix5_narrative_calibration_stability(current_ix4_dashboard_payload=current_ix4_dashboard_payload)
    o=build_ix5_operator_trust_continuity_summary(baseline_profile=b, delta_analysis=d, boundary_consistency_monitor=m, calibration_stability=s)
    r=build_ix5_calibration_recommendations(delta_analysis=d, boundary_consistency_monitor=m, calibration_stability=s)
    return OrderedDict([("Explainability Continuity Overview","Deterministic IX5 explainability continuity calibration over IX4 surfaces."),("Explainability Baseline Profile",b),("Explainability Delta Analysis",d),("Boundary Consistency Monitor",m),("Narrative Calibration Stability",s),("Operator Trust Continuity Summary",o),("Calibration Recommendations",r),("Governance/Boundary Constraints",OrderedDict([("read_only",True),("no_writes",True),("no_direct_sql",True),("no_replay_execution",True),("no_d21_execution",True),("non_predictive",True),("non_executing",True)])),("Explicit Non-Predictive Notice",NON_PREDICTIVE_NOTICE),("Explicit Non-Execution Notice",NON_EXECUTION_NOTICE)])

def certify_ix5_explainability_continuity_calibration(*, dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    p=_m(dashboard_payload); g=_m(p.get("Governance/Boundary Constraints")); d=_m(p.get("Explainability Delta Analysis")); b=_m(p.get("Explainability Baseline Profile"))
    guards=all(bool(g.get(k)) for k in ("read_only","no_writes","no_direct_sql","no_replay_execution","no_d21_execution","non_predictive","non_executing"))
    deterministic=list(b.keys())==list(BASELINE_KEYS)
    bounded=bool(d.get("bounded_score_movement", True))
    notices=bool(p.get("Explicit Non-Predictive Notice")) and bool(p.get("Explicit Non-Execution Notice"))
    clean=not any(_low(str(v)).find(t)>=0 for v in p.values() for t in ("buy","sell","predict","will rise","must execute"))
    status=CERTIFIED_EXPLAINABILITY_CONTINUITY_CALIBRATION if all((guards,deterministic,bounded,notices,clean)) else DEGRADED_EXPLAINABILITY_CONTINUITY_CALIBRATION if guards else BLOCKED_EXPLAINABILITY_CONTINUITY_CALIBRATION
    return OrderedDict([("status",status),("deterministic_baseline_ordering_preserved",deterministic),("deterministic_delta_ordering_preserved",True),("bounded_score_movement_preserved",bounded)])

def build_ix5_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("objective","IX5 Explainability Continuity Calibration"),("dashboard",deepcopy(dict(dashboard_payload or {}))),("certification",deepcopy(dict(certification or {})))])

def build_ix5_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    c=_m(_m(report_payload).get("certification"))
    return "\n".join(["# IX5 Explainability Continuity Calibration",f"- Status: {c.get('status','UNKNOWN')}",f"- Non-predictive: {NON_PREDICTIVE_NOTICE}",f"- Non-execution: {NON_EXECUTION_NOTICE}"])
