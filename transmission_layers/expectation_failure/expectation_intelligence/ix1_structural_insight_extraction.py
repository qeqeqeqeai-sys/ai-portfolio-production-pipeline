"""IX1 Structural Insight Extraction (deterministic, read-only, replay-grounded)."""
from __future__ import annotations
from collections import Counter, OrderedDict
from copy import deepcopy
import hashlib, json
from typing import Any, Mapping

CERTIFIED_STRUCTURAL_INSIGHT_EXTRACTION = "CERTIFIED_STRUCTURAL_INSIGHT_EXTRACTION"
DEGRADED_STRUCTURAL_INSIGHT_EXTRACTION = "DEGRADED_STRUCTURAL_INSIGHT_EXTRACTION"
BLOCKED_STRUCTURAL_INSIGHT_EXTRACTION = "BLOCKED_STRUCTURAL_INSIGHT_EXTRACTION"

IX1_PRIORITY_BUCKETS = (
    "HIGH_STRUCTURAL_SIGNIFICANCE","HIGH_TRANSITION_NOVELTY","HIGH_CONTRADICTION_PERSISTENCE","HIGH_SEMANTIC_FRAGILITY","HIGH_CONCENTRATION_RISK","MODERATE_INFORMATIONAL_VALUE","LOW_INFORMATIONAL_VALUE"
)

NON_PREDICTIVE_NOTICE = "IX1 produces deterministic replay-grounded structural findings only. It does not provide predictions, market forecasts, or trading signals."
NON_EXECUTION_NOTICE = "IX1 is read-only and recommendation-only. It cannot execute replay, trigger D21, perform writes, or bypass governance approvals."


def _rows(v: Any) -> list[dict[str, Any]]:
    if isinstance(v, Mapping): return [dict(v)]
    return [dict(x) for x in list(v or []) if isinstance(x, Mapping)]

def _b(v: Any, lo: float=0.0, hi: float=100.0) -> float:
    try: return max(lo,min(hi,round(float(v),3)))
    except Exception: return lo

def _token(v: Any) -> str: return str(v or "").strip().lower()
def _checksum(p: Any) -> str: return hashlib.sha256(json.dumps(p, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode()).hexdigest()

def build_ix1_structural_insight_inventory(*, h1_h2_replay_interpretation: Any, cd1_diversity_diagnostics: Any, h3_transition_intelligence: Any, cd4_drift_saturation_analysis: Any) -> OrderedDict[str, Any]:
    replay, diversity, transitions, drift = _rows(deepcopy(h1_h2_replay_interpretation)), _rows(deepcopy(cd1_diversity_diagnostics)), _rows(deepcopy(h3_transition_intelligence)), _rows(deepcopy(cd4_drift_saturation_analysis))
    contradiction = sum(1 for r in replay if "contradiction" in _token(r.get("contradiction_state") or r.get("status")))
    unstable = sum(1 for r in drift if _b(r.get("expectation_decay_score") or r.get("replay_drift_score")) >= 60)
    concentration = sum(1 for r in drift if _b(r.get("concentration_score")) >= 60)
    transition_risk = sum(1 for r in transitions if _b(r.get("transition_risk_score") or r.get("novelty_score")) >= 60)
    categories = OrderedDict([
        ("contradiction persistence findings", [f"Persistent contradiction signals: {contradiction} replay-linked records."]),
        ("continuity fracture findings", [f"Continuity fracture pressure observed in {unstable} drift-linked records."]),
        ("confidence instability findings", [f"Confidence instability pressure observed in {unstable} records from drift/decay surfaces."]),
        ("semantic saturation findings", [f"Semantic saturation pressure observed in {sum(1 for r in drift if _b(r.get('semantic_saturation_score'))>=60)} records."]),
        ("replay concentration findings", [f"Replay concentration risk observed in {concentration} records."]),
        ("transition anomaly findings", [f"Transition anomaly pressure observed in {transition_risk} transition records."]),
        ("regime migration findings", [f"Regime migration pathways catalogued from {len(transitions)} transition records."]),
        ("expectation decay findings", [f"Expectation decay pressure observed in {unstable} records."]),
        ("semantic fragility findings", [f"Semantic fragility pressure observed in {sum(1 for r in drift if _b(r.get('semantic_exhaustion_risk'))>=65)} records."]),
        ("recurring structural pattern findings", [f"Recurring pattern families extracted from replay={len(replay)}, diversity={len(diversity)}, transition={len(transitions)}, drift={len(drift)}."]),
    ])
    return OrderedDict([("inventory_categories", categories), ("inventory_size", sum(len(v) for v in categories.values()))])

def build_ix1_structural_anomaly_detection(*, structural_insight_inventory: Mapping[str, Any], h3_transition_intelligence: Any, cd4_drift_saturation_analysis: Any) -> list[OrderedDict[str, Any]]:
    transitions, drift = _rows(deepcopy(h3_transition_intelligence)), _rows(deepcopy(cd4_drift_saturation_analysis))
    anomalies=[]
    checks=[("unusually persistent contradictions", sum(1 for r in drift if _b(r.get("expectation_decay_score"))>=75)),("contradiction recurrence spikes", sum(1 for r in transitions if _b(r.get("transition_risk_score"))>=70)),("unstable confidence oscillations", sum(1 for r in drift if _b(r.get("replay_drift_score"))>=70)),("continuity collapse corridors", sum(1 for r in drift if _b(r.get("freshness_score"))<=30)),("semantic saturation spikes", sum(1 for r in drift if _b(r.get("semantic_saturation_score"))>=75)),("replay monoculture formation", sum(1 for r in drift if _b(r.get("concentration_score"))>=75)),("transition stagnation clusters", sum(1 for r in transitions if "loop" in _token(r.get("chain_signature") or r.get("transition_label")))),("abrupt expectation decay zones", sum(1 for r in drift if _b(r.get("expectation_decay_score"))>=80)),("replay novelty droughts", sum(1 for r in transitions if _b(r.get("novelty_score"))<=25)),("structural repetition acceleration", sum(1 for r in transitions if "repeat" in _token(r.get("transition_label"))))]
    for name,count in checks:
        if count>0: anomalies.append(OrderedDict([("anomaly",name),("count",count),("explanation",f"Detected via deterministic thresholding on replay-grounded transition/drift metrics; count={count}.")]))
    return sorted(anomalies, key=lambda r:(-int(r.get("count",0)), str(r.get("anomaly"))))[:25]

def build_ix1_transition_pattern_findings(*, h3_transition_intelligence: Any) -> list[OrderedDict[str, Any]]:
    rows = _rows(deepcopy(h3_transition_intelligence))
    patterns=["contradiction escalation pathways","contradiction resolution pathways","continuity fracture/recovery cycles","confidence divergence/convergence corridors","semantic persistence pathways","semantic decay pathways","regime instability corridors","recurring transition loops","fragile transition chains"]
    out=[]
    for i,p in enumerate(patterns):
        strength=sum(1 for r in rows if p.split()[0] in _token(r.get("transition_label") or r.get("chain_signature") or r.get("transition_type")))
        out.append(OrderedDict([("pattern",p),("support_count",strength),("finding",f"{p.title()} extracted deterministically from transition evidence; support_count={strength}.")]))
    return out

def build_ix1_expectation_structure_findings(*, structural_insight_inventory: Mapping[str, Any], structural_anomaly_detection: Any, transition_pattern_findings: Any) -> list[OrderedDict[str, Any]]:
    inv = dict(deepcopy(structural_insight_inventory or {})); anomalies=_rows(deepcopy(structural_anomaly_detection)); patterns=_rows(deepcopy(transition_pattern_findings))
    return [OrderedDict([("dimension",d),("finding",f"{d} assessed from inventory/anomaly/transition surfaces using deterministic aggregation."),("support",len(anomalies)+len(patterns)+len(inv.get('inventory_categories',{})))]) for d in (
        "expectation persistence","expectation fragility","expectation concentration","expectation saturation","expectation transition instability","expectation novelty decay","replay structural evolution quality","replay structural stagnation")]

def build_ix1_insight_priority_ranking(*, structural_anomaly_detection: Any, transition_pattern_findings: Any, expectation_structure_findings: Any) -> list[OrderedDict[str, Any]]:
    joined=_rows(structural_anomaly_detection)+_rows(transition_pattern_findings)+_rows(expectation_structure_findings)
    out=[]
    for i,r in enumerate(joined):
        score=_b((len(str(r))*0.1)+(float(r.get("count") or r.get("support_count") or r.get("support") or 0)*2),0,100)
        bucket = IX1_PRIORITY_BUCKETS[0] if score>=85 else IX1_PRIORITY_BUCKETS[1] if score>=75 else IX1_PRIORITY_BUCKETS[2] if "contradiction" in _token(r) else IX1_PRIORITY_BUCKETS[3] if "fragility" in _token(r) else IX1_PRIORITY_BUCKETS[4] if "concentration" in _token(r) else IX1_PRIORITY_BUCKETS[5] if score>=45 else IX1_PRIORITY_BUCKETS[6]
        out.append(OrderedDict([("insight_id",f"ix1_{i:03d}"),("bucket",bucket),("priority_score",score),("summary",str(r.get('anomaly') or r.get('pattern') or r.get('dimension') or 'insight'))]))
    return sorted(out,key=lambda x:(-float(x.get("priority_score",0)),str(x.get("summary"))))[:50]

def build_ix1_operator_insight_summary(*, insight_priority_ranking: Any) -> OrderedDict[str, Any]:
    rows=_rows(insight_priority_ranking)
    top=[r.get("summary") for r in rows[:8]]
    keys=["most persistent contradictions","most fragile semantic themes","strongest transition anomalies","strongest continuity fractures","strongest concentration risks","strongest replay stagnation signals","strongest novelty-collapse signals","strongest replay-evolution findings"]
    return OrderedDict((k, top[i] if i<len(top) else "No bounded replay-grounded finding available") for i,k in enumerate(keys))

def build_ix1_dashboard_payload(*, structural_insight_inventory: Mapping[str, Any], structural_anomaly_detection: Any, transition_pattern_findings: Any, expectation_structure_findings: Any, insight_priority_ranking: Any, operator_insight_summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Structural Insight Overview", "Deterministic replay-grounded structural insight extraction layer."),
        ("Structural Insight Inventory", deepcopy(dict(structural_insight_inventory or {}))),
        ("Structural Anomaly Detection", deepcopy(_rows(structural_anomaly_detection))),
        ("Transition Pattern Findings", deepcopy(_rows(transition_pattern_findings))),
        ("Expectation Structure Findings", deepcopy(_rows(expectation_structure_findings))),
        ("Insight Priority Ranking", deepcopy(_rows(insight_priority_ranking))),
        ("Operator Insight Summary", deepcopy(dict(operator_insight_summary or {}))),
        ("Governance/Boundary Constraints", OrderedDict([("read_only",True),("no_writes",True),("no_direct_sql",True),("no_replay_execution",True),("no_d21_execution",True),("non_predictive",True),("bounded_interpretive_synthesis",True)])),
        ("Explicit Non-Predictive Notice", NON_PREDICTIVE_NOTICE),
        ("Explicit Non-Execution Notice", NON_EXECUTION_NOTICE),
    ])

def certify_ix1_structural_insight_extraction(*, dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    p=dict(deepcopy(dashboard_payload or {})); g=dict(p.get("Governance/Boundary Constraints") or {})
    guards=all(bool(g.get(k)) for k in ("read_only","no_writes","no_direct_sql","no_replay_execution","no_d21_execution","non_predictive","bounded_interpretive_synthesis"))
    notices=bool(p.get("Explicit Non-Predictive Notice")) and bool(p.get("Explicit Non-Execution Notice"))
    rank=_rows(p.get("Insight Priority Ranking")); deterministic=rank==sorted(rank,key=lambda x:(-float(x.get("priority_score",0)),str(x.get("summary"))))
    status = CERTIFIED_STRUCTURAL_INSIGHT_EXTRACTION if guards and notices and deterministic else DEGRADED_STRUCTURAL_INSIGHT_EXTRACTION if guards else BLOCKED_STRUCTURAL_INSIGHT_EXTRACTION
    return OrderedDict([("status",status),("deterministic_ordering",deterministic),("replay_grounded",True),("bounded",True),("checksum",_checksum(p))])

def build_ix1_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("objective","IX1 Structural Insight Extraction"),("dashboard",deepcopy(dict(dashboard_payload or {}))),("certification",deepcopy(dict(certification or {})))])

def build_ix1_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    rp=dict(report_payload or {}); cert=dict(rp.get("certification") or {})
    return "\n".join(["# IX1 Structural Insight Extraction",f"- Status: {cert.get('status','UNKNOWN')}",f"- Objective: {rp.get('objective','')}",f"- Non-predictive: {NON_PREDICTIVE_NOTICE}",f"- Non-execution: {NON_EXECUTION_NOTICE}"])

__all__=[x for x in globals() if x.startswith("build_ix1_") or x.startswith("certify_ix1_") or x.endswith("STRUCTURAL_INSIGHT_EXTRACTION") or x in {"IX1_PRIORITY_BUCKETS","NON_PREDICTIVE_NOTICE","NON_EXECUTION_NOTICE"}]
