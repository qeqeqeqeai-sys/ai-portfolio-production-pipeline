"""CD4 Expectation Drift & Replay Saturation Intelligence (deterministic, read-only, recommendation-only)."""
from __future__ import annotations

from collections import Counter, OrderedDict
from copy import deepcopy
import hashlib, json
from typing import Any, Mapping

CERTIFIED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE = "CERTIFIED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE"
DEGRADED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE = "DEGRADED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE"
BLOCKED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE = "BLOCKED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE"

FRESH, ACTIVE, AGING, STALE, SATURATED = "FRESH", "ACTIVE", "AGING", "STALE", "SATURATED"
PERSISTENT, SLOW_DECAY, MODERATE_DECAY, RAPID_DECAY, COLLAPSED = "PERSISTENT", "SLOW_DECAY", "MODERATE_DECAY", "RAPID_DECAY", "COLLAPSED"
LOW_SATURATION, MODERATE_SATURATION, HIGH_SATURATION, EXTREME_SATURATION = "LOW_SATURATION", "MODERATE_SATURATION", "HIGH_SATURATION", "EXTREME_SATURATION"
STABLE, WATCHLIST, ELEVATED, FRAGILE, CRITICAL = "STABLE", "WATCHLIST", "ELEVATED", "FRAGILE", "CRITICAL"

REVIEW_FOR_REPLAY_REFRESH = "REVIEW_FOR_REPLAY_REFRESH"
DEFER_STALE_REPLAY = "DEFER_STALE_REPLAY"
MONITOR_EXPECTATION_DRIFT = "MONITOR_EXPECTATION_DRIFT"
REDUCE_REPLAY_CONCENTRATION = "REDUCE_REPLAY_CONCENTRATION"
INVESTIGATE_SEMANTIC_SATURATION = "INVESTIGATE_SEMANTIC_SATURATION"
DEFER_COLLAPSED_EXPECTATION_CLUSTER = "DEFER_COLLAPSED_EXPECTATION_CLUSTER"
NO_ACTION_REQUIRED = "NO_ACTION_REQUIRED"


def _as_rows(rows: Any) -> list[dict[str, Any]]:
    if isinstance(rows, Mapping): return [dict(rows)]
    return [dict(r) for r in list(rows or []) if isinstance(r, Mapping)]

def _bounded(x: Any, lo: float=0.0, hi: float=100.0) -> float:
    try: return max(lo, min(hi, round(float(x), 3)))
    except Exception: return lo

def _token(v: Any, d: str="unknown") -> str:
    s = str(v or "").strip().lower()
    return s if s else d

def _cid(r: Mapping[str, Any], i: int) -> str:
    return str(r.get("candidate_id") or r.get("replay_id") or r.get("record_id") or f"cd4_{i:04d}")

def _checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode()).hexdigest()

def _fresh_bucket(v: float) -> str:
    return FRESH if v>=85 else ACTIVE if v>=70 else AGING if v>=50 else STALE if v>=30 else SATURATED

def _decay_bucket(v: float) -> str:
    return PERSISTENT if v<=15 else SLOW_DECAY if v<=30 else MODERATE_DECAY if v<=50 else RAPID_DECAY if v<=75 else COLLAPSED

def _sat_bucket(v: float) -> str:
    return LOW_SATURATION if v<25 else MODERATE_SATURATION if v<50 else HIGH_SATURATION if v<75 else EXTREME_SATURATION

def _instability_bucket(v: float) -> str:
    return STABLE if v<20 else WATCHLIST if v<40 else ELEVATED if v<60 else FRAGILE if v<80 else CRITICAL

def build_cd4_replay_drift_profile(*, replay_candidates: Any, cd2_dashboard_payload: Mapping[str, Any] | None=None, cd3_dashboard_payload: Mapping[str, Any] | None=None) -> list[OrderedDict[str, Any]]:
    rows = sorted(_as_rows(deepcopy(replay_candidates)), key=lambda r: (_token(r.get("candidate_id") or r.get("record_id") or r.get("replay_id")), _token(r.get("replay_window_ref") or r.get("run_id"))))
    theme_counts = Counter(_token(r.get("semantic_theme_family") or r.get("semantic_themes") or r.get("themes")) for r in rows)
    out=[]
    for i,r in enumerate(rows):
        cid=_cid(r,i); recur=max(0,int(r.get("prior_recurrence_count") or r.get("recurrence_count") or 0))
        contradiction = 100.0 if "contradiction" in _token(r.get("contradiction_state")) else 40.0
        semantic_mutation = _bounded((1-1/max(theme_counts[_token(r.get('semantic_theme_family') or r.get('themes'))],1))*100)
        reinterpretation = _bounded((recur*12)+ (0 if _token(r.get("continuity_state")) in {"stable","persistent"} else 25))
        score = _bounded((contradiction*0.3)+(semantic_mutation*0.3)+(reinterpretation*0.4))
        out.append(OrderedDict([("candidate_id",cid),("replay_drift_score",score),("contradiction_accumulation",_bounded(contradiction)),("narrative_mutation",semantic_mutation),("expectation_reinterpretation",reinterpretation),("regime_instability_emergence",_bounded(100 if _token(r.get('regime_state')) in {'transition','unstable'} else 35))]))
    return out

def build_cd4_semantic_saturation_analysis(*, replay_drift_profile: Any) -> list[OrderedDict[str, Any]]:
    rows=_as_rows(deepcopy(replay_drift_profile)); drift_avg=sum(_bounded(r.get("replay_drift_score")) for r in rows)/max(len(rows),1)
    out=[]
    for i,r in enumerate(sorted(rows,key=lambda x:str(x.get("candidate_id")))):
        sat=_bounded((_bounded(r.get("narrative_mutation"))*0.45)+(_bounded(r.get("expectation_reinterpretation"))*0.35)+(drift_avg*0.2))
        out.append(OrderedDict([("candidate_id",_cid(r,i)),("semantic_saturation_score",sat),("saturation_bucket",_sat_bucket(sat)),("diminishing_information_gain",_bounded(sat*0.9)),("semantic_exhaustion_risk",_bounded(sat*1.05))]))
    return out

def build_cd4_expectation_decay_analysis(*, replay_drift_profile: Any, semantic_saturation_analysis: Any) -> list[OrderedDict[str, Any]]:
    sat={str(r.get('candidate_id')):r for r in _as_rows(deepcopy(semantic_saturation_analysis))}
    out=[]
    for i,r in enumerate(sorted(_as_rows(deepcopy(replay_drift_profile)), key=lambda x:str(x.get("candidate_id")))):
        cid=_cid(r,i); s=sat.get(cid,{})
        decay=_bounded(_bounded(r.get("replay_drift_score"))*0.55 + _bounded(s.get("semantic_saturation_score"))*0.45)
        out.append(OrderedDict([("candidate_id",cid),("expectation_decay_score",decay),("decay_bucket",_decay_bucket(decay)),("propagation_energy",_bounded(100-decay)),("informational_utility",_bounded(100-(decay*0.8)))]))
    return out

def build_cd4_replay_freshness_scoring(*, expectation_decay_analysis: Any, semantic_saturation_analysis: Any) -> list[OrderedDict[str, Any]]:
    sat={str(r.get('candidate_id')):r for r in _as_rows(deepcopy(semantic_saturation_analysis))}
    out=[]
    for i,r in enumerate(sorted(_as_rows(deepcopy(expectation_decay_analysis)), key=lambda x:str(x.get("candidate_id")))):
        cid=_cid(r,i); s=sat.get(cid,{})
        freshness=_bounded(100 - (_bounded(r.get("expectation_decay_score"))*0.65 + _bounded(s.get("semantic_saturation_score"))*0.35))
        out.append(OrderedDict([("candidate_id",cid),("freshness_score",freshness),("freshness_bucket",_fresh_bucket(freshness)),("replay_utility_rank_signal",_bounded(freshness))]))
    return sorted(out, key=lambda r:(-float(r.get("freshness_score",0.0)), str(r.get("candidate_id"))))

def build_cd4_replay_half_life_estimation(*, expectation_decay_analysis: Any, semantic_saturation_analysis: Any) -> list[OrderedDict[str, Any]]:
    sat={str(r.get('candidate_id')):r for r in _as_rows(deepcopy(semantic_saturation_analysis))}
    out=[]
    for i,r in enumerate(sorted(_as_rows(deepcopy(expectation_decay_analysis)), key=lambda x:str(x.get("candidate_id")))):
        cid=_cid(r,i); s=sat.get(cid,{})
        half=_bounded(100-(0.7*_bounded(r.get("expectation_decay_score"))+0.3*_bounded(s.get("semantic_saturation_score"))))
        bucket = "LONG" if half>=70 else "MEDIUM" if half>=40 else "SHORT" if half>=20 else "TERMINAL"
        out.append(OrderedDict([("candidate_id",cid),("half_life_score",half),("half_life_bucket",bucket)]))
    return out

def build_cd4_concentration_instability_analysis(*, replay_candidates: Any, semantic_saturation_analysis: Any) -> list[OrderedDict[str, Any]]:
    rows=sorted(_as_rows(deepcopy(replay_candidates)), key=lambda r:str(r.get("candidate_id") or r.get("record_id") or r.get("replay_id")))
    sat={str(r.get('candidate_id')):r for r in _as_rows(deepcopy(semantic_saturation_analysis))}
    theme_counts=Counter(_token(r.get("semantic_theme_family") or r.get("semantic_themes") or r.get("themes")) for r in rows)
    total=max(len(rows),1)
    out=[]
    for i,r in enumerate(rows):
        cid=_cid(r,i); conc=_bounded((theme_counts[_token(r.get("semantic_theme_family") or r.get("themes"))]/total)*100)
        instability=_bounded(conc*0.6 + _bounded(sat.get(cid,{}).get("semantic_saturation_score"))*0.4)
        out.append(OrderedDict([("candidate_id",cid),("concentration_score",conc),("instability_score",instability),("instability_bucket",_instability_bucket(instability))]))
    return out

def build_cd4_operator_attention_queue(*, replay_freshness_scoring: Any, expectation_decay_analysis: Any, concentration_instability_analysis: Any) -> list[OrderedDict[str, Any]]:
    dec={str(r.get('candidate_id')):r for r in _as_rows(expectation_decay_analysis)}; inst={str(r.get('candidate_id')):r for r in _as_rows(concentration_instability_analysis)}
    q=[]
    for i,r in enumerate(_as_rows(replay_freshness_scoring)):
        cid=_cid(r,i); fresh_bucket=str(r.get("freshness_bucket")); decay_bucket=str(dec.get(cid,{}).get("decay_bucket")); instability=str(inst.get(cid,{}).get("instability_bucket"))
        actions=[]
        if fresh_bucket in {STALE,SATURATED}: actions.append(DEFER_STALE_REPLAY)
        if fresh_bucket in {AGING,STALE}: actions.append(REVIEW_FOR_REPLAY_REFRESH)
        if decay_bucket in {RAPID_DECAY,COLLAPSED}: actions.append(DEFER_COLLAPSED_EXPECTATION_CLUSTER)
        if instability in {FRAGILE,CRITICAL}: actions.append(REDUCE_REPLAY_CONCENTRATION)
        if instability in {ELEVATED,FRAGILE,CRITICAL}: actions.append(INVESTIGATE_SEMANTIC_SATURATION)
        if not actions: actions=[MONITOR_EXPECTATION_DRIFT if fresh_bucket in {ACTIVE,AGING} else NO_ACTION_REQUIRED]
        priority=_bounded((100-float(r.get("freshness_score",0))) * 0.5 + (50 if instability in {CRITICAL,FRAGILE} else 15),0,200)
        q.append(OrderedDict([("candidate_id",cid),("priority_score",priority),("recommended_actions",actions)]))
    return sorted(q,key=lambda x:(-float(x.get("priority_score",0)),str(x.get("candidate_id"))))

def build_cd4_dashboard_payload(*, replay_drift_profile: Any, semantic_saturation_analysis: Any, expectation_decay_analysis: Any, replay_freshness_scoring: Any, replay_half_life_estimation: Any, concentration_instability_analysis: Any, operator_attention_queue: Any) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Expectation Drift Overview", deepcopy(_as_rows(replay_drift_profile))),
        ("Replay Freshness Scorecard", deepcopy(_as_rows(replay_freshness_scoring))),
        ("Semantic Saturation Analysis", deepcopy(_as_rows(semantic_saturation_analysis))),
        ("Expectation Decay Analysis", deepcopy(_as_rows(expectation_decay_analysis))),
        ("Replay Half-Life Estimation", deepcopy(_as_rows(replay_half_life_estimation))),
        ("Concentration Instability Summary", deepcopy(_as_rows(concentration_instability_analysis))),
        ("Operator Attention Queue", deepcopy(_as_rows(operator_attention_queue))),
        ("Governance & Boundary Constraints", OrderedDict([("read_only_intelligence",True),("no_execution_authority",True),("no_autonomous_replay_triggering",True),("no_direct_sql",True),("no_predictive_trading_behavior",True),("no_portfolio_optimization_behavior",True),("operator_reviewed_replay_only",True),("bounded_deterministic_logic_only",True)])),
        ("Explicit Non-Execution Notice", "CD4 is deterministic read-only intelligence. It cannot execute replay, persist writes, or bypass D8/D21 governance approvals."),
    ])

def certify_cd4_expectation_drift_and_replay_saturation_intelligence(*, dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    p=dict(deepcopy(dashboard_payload or {})); g=dict(p.get("Governance & Boundary Constraints") or {})
    rows=_as_rows(p.get("Replay Freshness Scorecard")); bounded=all(0<=float(r.get("freshness_score",0))<=100 for r in rows)
    deterministic = [str(r.get("candidate_id")) for r in rows] == sorted([str(r.get("candidate_id")) for r in rows], key=lambda cid: (-next((float(x.get("freshness_score",0)) for x in rows if str(x.get("candidate_id"))==cid),0), cid))
    guards=all(bool(g.get(k)) for k in ("read_only_intelligence","no_execution_authority","no_autonomous_replay_triggering","no_direct_sql","no_predictive_trading_behavior","no_portfolio_optimization_behavior","operator_reviewed_replay_only","bounded_deterministic_logic_only"))
    status = BLOCKED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE if not guards else DEGRADED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE if not bounded else CERTIFIED_EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE
    return OrderedDict([("status",status),("bounded_scoring",bounded),("deterministic_tie_breaking",deterministic),("recommendation_only",True),("checksum",_checksum(p))])

def build_cd4_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("objective","Expectation Drift & Replay Saturation Intelligence"),("methodology","Deterministic bounded rule-based scoring over replay drift, saturation, decay, freshness, half-life, and concentration instability."),("bounded_scoring_rules","All applicable scores bounded to 0-100 using fixed thresholds."),("replay_freshness_interpretation","FRESH→SATURATED indicates decreasing utility and increasing staleness risk."),("saturation_interpretation","LOW→EXTREME saturation indicates overcrowding and diminishing marginal information gain."),("decay_interpretation","PERSISTENT→COLLAPSED captures persistence weakening and narrative utility decay."),("concentration_instability_interpretation","STABLE→CRITICAL captures monoculture fragility and concentration risk."),("governance_boundaries",deepcopy(dict(dashboard_payload.get("Governance & Boundary Constraints") or {}))),("operator_action_semantics","Recommendation-only queue; all actions require operator review and D8/D21 governance."),("explicit_non_execution_declaration",dashboard_payload.get("Explicit Non-Execution Notice")),("dashboard",deepcopy(dict(dashboard_payload))), ("certification",deepcopy(dict(certification)))])

def build_cd4_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    rp=dict(report_payload or {}); cert=dict(rp.get("certification") or {})
    return "\n".join(["# CD4 Expectation Drift & Replay Saturation Intelligence",f"- Status: {cert.get('status','UNKNOWN')}",f"- Objective: {rp.get('objective','')}",f"- Methodology: {rp.get('methodology','')}",f"- Governance boundaries: {rp.get('governance_boundaries',{})}",f"- Non-execution: {rp.get('explicit_non_execution_declaration','')}"])

__all__=[x for x in globals() if x.startswith("build_cd4_") or x.startswith("certify_cd4_") or x.endswith("EXPECTATION_DRIFT_AND_REPLAY_SATURATION_INTELLIGENCE") or x in {"FRESH","ACTIVE","AGING","STALE","SATURATED","PERSISTENT","SLOW_DECAY","MODERATE_DECAY","RAPID_DECAY","COLLAPSED","LOW_SATURATION","MODERATE_SATURATION","HIGH_SATURATION","EXTREME_SATURATION","STABLE","WATCHLIST","ELEVATED","FRAGILE","CRITICAL","REVIEW_FOR_REPLAY_REFRESH","DEFER_STALE_REPLAY","MONITOR_EXPECTATION_DRIFT","REDUCE_REPLAY_CONCENTRATION","INVESTIGATE_SEMANTIC_SATURATION","DEFER_COLLAPSED_EXPECTATION_CLUSTER","NO_ACTION_REQUIRED"}]
