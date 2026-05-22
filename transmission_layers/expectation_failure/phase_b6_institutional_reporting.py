"""Phase B6 deterministic institutional reporting and analyst briefing layer."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Dict, List, Tuple

PHASE_ID = "B6"
PHASE_NAME = "Institutional Reporting & Analyst Briefing Layer"
REPORT_TEMPLATE_VERSION = "b6_report_template_v1"
SECTION_TEMPLATE_VERSION = "b6_section_templates_v1"
CLASSIFICATION_RULE_VERSION = "b6_classification_rules_v1"
SECTION_ORDER = [
    "report_header", "executive_summary", "key_fragility_findings", "heatmap_briefing", "asymmetry_briefing",
    "benchmark_relative_briefing", "historical_replay_briefing", "alert_briefing", "entity_briefing_cards",
    "subsector_briefing_cards", "evidence_appendix", "limitations_and_disclosures", "replay_metadata", "architecture_constraints",
]
INPUT_SECTIONS = ["B1_HEATMAP", "B2_ASYMMETRY", "B3_BENCHMARK_RELATIVE", "B4_HISTORICAL_REPLAY", "B5_ALERTS"]
ARCHITECTURE_CONSTRAINTS = [
    "deterministic_only", "replayable", "explainable", "bounded_labels", "bounded_sections", "immutable_input_safe",
    "additive_only", "fixed_report_sections", "fixed_section_ordering", "fixed_template_wording", "fixed_label_precedence",
    "no_unrestricted_llm_reasoning", "no_optimization_loops", "no_adaptive_control_systems", "no_trade_execution",
    "no_buy_sell_short_recommendations", "no_target_prices", "no_portfolio_allocation", "no_backtesting", "no_pnl_analysis",
    "no_predictive_timeseries_modeling", "no_autonomous_alert_dispatch", "no_external_notification_delivery", "no_freeform_ai_commentary",
]


def _stable_checksum(v: object) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _missing(section_id: str, template_id: str) -> dict:
    return {"section_id": section_id, "section_status": "MISSING_INPUT", "explanation": "Required deterministic source report is missing for this section.", "template_id": template_id}


def _collect_entities(report: dict | None, keys: Tuple[str, ...]) -> List[dict]:
    if not isinstance(report, dict):
        return []
    for k in keys:
        v = report.get(k)
        if isinstance(v, list):
            return [deepcopy(x) for x in v if isinstance(x, dict)]
    return []


def _entity_key(x: dict) -> tuple:
    return (str(x.get("entity_id") or "~"), str(x.get("ticker") or "~"), str(x.get("entity_name") or "~"))


def build_b6_report_context(b1_report=None, b2_report=None, b3_report=None, b4_report=None, b5_report=None, evidence_context=None):
    r = {"B1_HEATMAP": b1_report, "B2_ASYMMETRY": b2_report, "B3_BENCHMARK_RELATIVE": b3_report, "B4_HISTORICAL_REPLAY": b4_report, "B5_ALERTS": b5_report}
    available = [s for s in INPUT_SECTIONS if isinstance(r[s], dict)]
    missing = [s for s in INPUT_SECTIONS if s not in available]
    entity_ids, subsectors = set(), set()
    for src in [b1_report, b2_report, b3_report, b4_report, b5_report]:
        if isinstance(src, dict):
            for k, v in src.items():
                if isinstance(v, list):
                    for row in v:
                        if isinstance(row, dict):
                            if row.get("entity_id"): entity_ids.add(str(row.get("entity_id")))
                            if row.get("subsector"): subsectors.add(str(row.get("subsector")))
    checksums = {k: (_stable_checksum(deepcopy(v)) if isinstance(v, dict) else None) for k, v in r.items()}
    out = {
        "phase_id": PHASE_ID,
        "available_sections": available,
        "missing_sections": missing,
        "entity_count": len(entity_ids),
        "subsector_count": len(subsectors),
        "input_report_checksums": checksums,
        "evidence_context_used": deepcopy(evidence_context) if isinstance(evidence_context, dict) else {},
        "evidence_quality_flags": ([] if evidence_context else ["missing_evidence_context"]),
    }
    out["replay_metadata"] = {
        "phase_id": PHASE_ID, "phase_name": PHASE_NAME, "report_template_version": REPORT_TEMPLATE_VERSION,
        "section_template_version": SECTION_TEMPLATE_VERSION, "classification_rule_version": CLASSIFICATION_RULE_VERSION,
        "input_checksum": _stable_checksum({"reports": r, "evidence_context": evidence_context}), "output_checksum": _stable_checksum(out),
        "deterministic_section_order": SECTION_ORDER, "deterministic_sort_order": "fixed_severity_then_phase_then_identifier",
        "tie_breaker_policy": "entity_id_then_ticker_then_entity_name_then_subsector", "missing_section_policy": "emit_missing_input_section",
        "entity_matching_policy": "entity_id_then_ticker_then_entity_name_exact", "architecture_constraints": ARCHITECTURE_CONSTRAINTS,
    }
    return out


def build_executive_fragility_summary(report_context, b1_report=None, b2_report=None, b3_report=None, b4_report=None, b5_report=None):
    if not isinstance(report_context, dict):
        return _missing("EXECUTIVE_FRAGILITY_SUMMARY", "b6_executive_summary_v1")
    label = "LOW_EXPECTATION_FRAGILITY_ENVIRONMENT"
    universe_alert = str(((b5_report or {}).get("universe_alert_interpretation") or {}).get("universe_alert_label") or "")
    universe_replay = str(((b4_report or {}).get("universe_replay_interpretation") or {}).get("universe_replay_label") or "")
    b3_high = len([x for x in _collect_entities(b3_report, ("entity_relative_interpretations", "entity_benchmark_relative_interpretations")) if str(x.get("benchmark_relative_label")) in {"EXTREME_RELATIVE_FRAGILITY", "HIGH_RELATIVE_FRAGILITY"}])
    b2_high = len([x for x in _collect_entities(b2_report, ("entity_asymmetry_interpretations", )) if str(x.get("downside_asymmetry_label")) in {"EXTREME_DOWNSIDE_ASYMMETRY", "HIGH_DOWNSIDE_ASYMMETRY"}])
    b1_high = len([x for x in _collect_entities(b1_report, ("relative_fragility_ranking", "heatmap_entries")) if str(x.get("fragility_label")) in {"TOP_FRAGILITY_CANDIDATE", "HIGH_FRAGILITY_CANDIDATE"}])
    if universe_alert in {"UNIVERSE_CRITICAL_DETERIORATION_ALERT_REGIME"}: label = "CRITICAL_EXPECTATION_FRAGILITY_ENVIRONMENT"
    elif universe_alert in {"UNIVERSE_HIGH_DETERIORATION_ALERT_REGIME"}: label = "HIGH_EXPECTATION_FRAGILITY_ENVIRONMENT"
    elif universe_replay in {"UNIVERSE_ACCELERATING_FRAGILITY", "UNIVERSE_RISING_FRAGILITY"}: label = "HIGH_EXPECTATION_FRAGILITY_ENVIRONMENT"
    elif b3_high >= 3 or b2_high >= 3: label = "ELEVATED_EXPECTATION_FRAGILITY_ENVIRONMENT"
    elif b1_high >= 2: label = "MIXED_EXPECTATION_FRAGILITY_ENVIRONMENT"
    elif not report_context.get("available_sections"): label = "INSUFFICIENT_REPORTING_CONTEXT"
    return {"section_id": "EXECUTIVE_FRAGILITY_SUMMARY", "section_status": "OK", "summary_label": label, "executive_summary_points": [f"Executive classification is {label} under fixed B6 precedence.", "Summary is deterministic and bounded to supplied B1-B5 inputs.", "This output is institutional expectation-fragility intelligence only."], "dominant_system_condition": label, "evidence_quality_flags": report_context.get("evidence_quality_flags", []), "template_id": "b6_executive_summary_v1"}


def build_key_fragility_findings(b1_report=None, b2_report=None, b3_report=None, b4_report=None, b5_report=None):
    findings = []
    for e in _collect_entities(b5_report, ("entity_alert_interpretations", )):
        sev = "CRITICAL" if "CRITICAL" in str(e.get("alert_severity_label")) else ("HIGH" if "HIGH" in str(e.get("alert_severity_label")) else "ELEVATED")
        findings.append({"finding_id": f"B5_{e.get('entity_id')}", "finding_type": "ALERT_CONCENTRATION_FINDING", "finding_severity": sev, "finding_summary": f"Alert state {e.get('alert_state')} observed.", "source_phase": "B5", "source_reference": e.get("entity_id"), "evidence_quality_flags": e.get("evidence_quality_flags", [])})
    for e in _collect_entities(b4_report, ("entity_replay_interpretations", )):
        if "DETERIORATION" in str(e.get("change_label", "")):
            findings.append({"finding_id": f"B4_{e.get('entity_id')}", "finding_type": "HISTORICAL_DETERIORATION_FINDING", "finding_severity": "HIGH", "finding_summary": f"Historical fragility change label is {e.get('change_label')}.", "source_phase": "B4", "source_reference": e.get("entity_id"), "evidence_quality_flags": e.get("evidence_quality_flags", [])})
    if not findings:
        findings.append({"finding_id": "B6_INSUFFICIENT", "finding_type": "INSUFFICIENT_FINDING_CONTEXT", "finding_severity": "INSUFFICIENT", "finding_summary": "Insufficient source context for deterministic key findings.", "source_phase": "B6", "source_reference": "REPORT_CONTEXT", "evidence_quality_flags": ["missing_b1_b5_context"]})
    sev_order = {"CRITICAL": 0, "HIGH": 1, "ELEVATED": 2, "MONITORING": 3, "INFORMATIONAL": 4, "INSUFFICIENT": 5}
    phase_order = {"B5": 0, "B4": 1, "B3": 2, "B2": 3, "B1": 4, "B6": 5}
    findings = sorted(findings, key=lambda x: (sev_order.get(x.get("finding_severity"), 9), phase_order.get(x.get("source_phase"), 9), str(x.get("source_reference") or ""), str(x.get("finding_id") or "")))[:10]
    return {"section_id": "KEY_FRAGILITY_FINDINGS", "section_status": "OK", "findings": findings, "template_id": "b6_key_findings_v1"}


def build_heatmap_briefing_section(b1_report):
    if not isinstance(b1_report, dict): return _missing("HEATMAP_BRIEFING", "b6_heatmap_briefing_v1")
    rows = _collect_entities(b1_report, ("relative_fragility_ranking", "heatmap_entries"))
    return {"section_id": "HEATMAP_BRIEFING", "section_status": "OK", "top_fragility_entities": sorted([r.get("entity_id") for r in rows if str(r.get("fragility_label")) in {"TOP_FRAGILITY_CANDIDATE", "HIGH_FRAGILITY_CANDIDATE"}])[:10], "relative_fragility_ranking_summary": f"{len(rows)} entities available from B1 deterministic ranking context.", "cluster_summary_points": deepcopy((b1_report.get("cluster_summaries") or b1_report.get("fragility_cluster_summary") or []) )[:5], "subsector_summary_points": deepcopy((b1_report.get("subsector_summaries") or []) )[:5], "interpretation_summary": "B1 heatmap briefing extracted with deterministic ordering and bounded section fields.", "evidence_quality_flags": deepcopy(b1_report.get("evidence_quality_flags", [])), "template_id": "b6_heatmap_briefing_v1"}

def build_asymmetry_briefing_section(b2_report):
    if not isinstance(b2_report, dict): return _missing("ASYMMETRY_BRIEFING", "b6_asymmetry_briefing_v1")
    rows = _collect_entities(b2_report, ("entity_asymmetry_interpretations",))
    return {"section_id":"ASYMMETRY_BRIEFING","section_status":"OK","strongest_downside_asymmetry_candidates":sorted([r.get("entity_id") for r in rows if str(r.get("downside_asymmetry_label")) in {"EXTREME_DOWNSIDE_ASYMMETRY","HIGH_DOWNSIDE_ASYMMETRY"}])[:10],"long_risk_fragility_concentration":len([r for r in rows if "LONG" in str(r.get("long_risk_fragility_label",""))]),"expectation_support_mismatch_themes":sorted(set([str(r.get("expectation_support_mismatch_label")) for r in rows if r.get("expectation_support_mismatch_label")]))[:5],"relative_resilience_outliers":sorted([r.get("entity_id") for r in rows if "RESILIENCE" in str(r.get("relative_resilience_label",""))])[:10],"cluster_subsector_asymmetry_notes":deepcopy((b2_report.get("cluster_asymmetry_summaries") or []) )[:3] + deepcopy((b2_report.get("subsector_asymmetry_summaries") or []) )[:3],"evidence_quality_flags":deepcopy(b2_report.get("evidence_quality_flags", [])),"template_id":"b6_asymmetry_briefing_v1"}

def build_benchmark_relative_briefing_section(b3_report):
    if not isinstance(b3_report, dict): return _missing("BENCHMARK_RELATIVE_BRIEFING", "b6_benchmark_relative_briefing_v1")
    rows = _collect_entities(b3_report, ("entity_relative_interpretations", "entity_benchmark_relative_interpretations"))
    return {"section_id":"BENCHMARK_RELATIVE_BRIEFING","section_status":"OK","high_benchmark_relative_fragility_entities":sorted([r.get("entity_id") for r in rows if str(r.get("benchmark_relative_label")) in {"EXTREME_RELATIVE_FRAGILITY","HIGH_RELATIVE_FRAGILITY"}])[:10],"resilient_benchmark_relative_outliers":sorted([r.get("entity_id") for r in rows if "RESILIENCE" in str(r.get("benchmark_relative_resilience_label",""))])[:10],"dominant_benchmark_relative_drivers":sorted(set([str(r.get("relative_driver")) for r in rows if r.get("relative_driver")]))[:5],"peer_subsector_universe_relative_notes":[deepcopy(b3_report.get("peer_relative_interpretation")), deepcopy(b3_report.get("subsector_relative_interpretation")), deepcopy(b3_report.get("universe_relative_interpretation"))],"evidence_quality_flags":deepcopy(b3_report.get("evidence_quality_flags", [])),"template_id":"b6_benchmark_relative_briefing_v1"}

def build_historical_replay_briefing_section(b4_report):
    if not isinstance(b4_report, dict): return _missing("HISTORICAL_REPLAY_BRIEFING", "b6_historical_replay_briefing_v1")
    rows = _collect_entities(b4_report, ("entity_replay_interpretations",))
    return {"section_id":"HISTORICAL_REPLAY_BRIEFING","section_status":"OK","deterioration_candidates":sorted([r.get("entity_id") for r in rows if "DETERIORATION" in str(r.get("change_label",""))])[:10],"improvement_candidates":sorted([r.get("entity_id") for r in rows if "IMPROVEMENT" in str(r.get("change_label",""))])[:10],"persistent_high_fragility_names":sorted([r.get("entity_id") for r in rows if "PERSISTENT" in str(r.get("historical_state_label",""))])[:10],"subsector_replay_changes":deepcopy(b4_report.get("subsector_replay_interpretations", []))[:5],"universe_replay_label":deepcopy((b4_report.get("universe_replay_interpretation") or {}).get("universe_replay_label")),"evidence_quality_flags":deepcopy(b4_report.get("evidence_quality_flags", [])),"template_id":"b6_historical_replay_briefing_v1"}

def build_alert_briefing_section(b5_report):
    if not isinstance(b5_report, dict): return _missing("ALERT_BRIEFING", "b6_alert_briefing_v1")
    rows = _collect_entities(b5_report, ("entity_alert_interpretations",))
    return {"section_id":"ALERT_BRIEFING","section_status":"OK","active_critical_high_alerts":sorted([r.get("entity_id") for r in rows if r.get("alert_state") in {"ACTIVE_CRITICAL_DETERIORATION","ACTIVE_HIGH_DETERIORATION"}])[:15],"elevated_watchlist_alerts":sorted([r.get("entity_id") for r in rows if r.get("alert_state") == "ACTIVE_ELEVATED_WATCHLIST"])[:15],"alert_state_transitions":sorted(set([str(r.get("escalation_label")) for r in rows if r.get("escalation_label")]))[:6],"subsector_alert_concentrations":deepcopy(b5_report.get("subsector_alert_interpretations", []))[:5],"universe_alert_regime":deepcopy((b5_report.get("universe_alert_interpretation") or {}).get("universe_alert_label")),"evidence_quality_flags":deepcopy(b5_report.get("evidence_quality_flags", [])),"template_id":"b6_alert_briefing_v1"}

def build_entity_briefing_cards(b1_report=None, b2_report=None, b3_report=None, b4_report=None, b5_report=None):
    maps: Dict[tuple, dict] = {}
    def upsert(row: dict, key: str):
        k = (str(row.get("entity_id") or ""), str(row.get("ticker") or ""), str(row.get("entity_name") or ""))
        maps.setdefault(k, {})[key] = row
    for r in _collect_entities(b1_report, ("relative_fragility_ranking", "heatmap_entries")): upsert(r, "b1")
    for r in _collect_entities(b2_report, ("entity_asymmetry_interpretations",)): upsert(r, "b2")
    for r in _collect_entities(b3_report, ("entity_relative_interpretations", "entity_benchmark_relative_interpretations")): upsert(r, "b3")
    for r in _collect_entities(b4_report, ("entity_replay_interpretations",)): upsert(r, "b4")
    for r in _collect_entities(b5_report, ("entity_alert_interpretations",)): upsert(r, "b5")
    out=[]
    for k in sorted(maps):
        c = maps[k]; b1,b2,b3,b4,b5 = c.get("b1",{}),c.get("b2",{}),c.get("b3",{}),c.get("b4",{}),c.get("b5",{})
        label="PRIORITY_INFORMATIONAL"
        if b5.get("alert_state") in {"ACTIVE_CRITICAL_DETERIORATION"}: label="PRIORITY_CRITICAL_REVIEW"
        elif b5.get("alert_state") in {"ACTIVE_HIGH_DETERIORATION"}: label="PRIORITY_HIGH_REVIEW"
        elif "DETERIORATION" in str(b4.get("change_label","")): label="PRIORITY_ELEVATED_WATCHLIST"
        elif str(b3.get("benchmark_relative_label")) in {"EXTREME_RELATIVE_FRAGILITY","HIGH_RELATIVE_FRAGILITY"}: label="PRIORITY_ELEVATED_WATCHLIST"
        elif str(b2.get("downside_asymmetry_label")) in {"EXTREME_DOWNSIDE_ASYMMETRY","HIGH_DOWNSIDE_ASYMMETRY"}: label="PRIORITY_MONITORING"
        elif str(b1.get("fragility_label")) in {"TOP_FRAGILITY_CANDIDATE","HIGH_FRAGILITY_CANDIDATE"}: label="PRIORITY_MONITORING"
        elif "RESILIENCE" in str(b2.get("relative_resilience_label", "")) or "RESILIENCE" in str(b3.get("benchmark_relative_resilience_label", "")): label="PRIORITY_RESILIENCE_REVIEW"
        out.append({"entity_id":k[0] or None,"ticker":k[1] or None,"entity_name":k[2] or None,"subsector":b1.get("subsector") or b2.get("subsector") or b3.get("subsector") or b4.get("subsector") or b5.get("subsector"),"card_priority_label":label,"heatmap_context":deepcopy(b1),"asymmetry_context":deepcopy(b2),"benchmark_relative_context":deepcopy(b3),"historical_replay_context":deepcopy(b4),"alert_context":deepcopy(b5),"dominant_fragility_driver":b5.get("primary_alert_driver") or b4.get("change_label") or b3.get("benchmark_relative_label") or b2.get("downside_asymmetry_label") or b1.get("fragility_label") or "INSUFFICIENT_ENTITY_CONTEXT","analyst_attention_reason":f"Entity card assigned {label} under deterministic B6 precedence.","evidence_quality_flags":sorted(set(b1.get("evidence_quality_flags",[])+b2.get("evidence_quality_flags",[])+b3.get("evidence_quality_flags",[])+b4.get("evidence_quality_flags",[])+b5.get("evidence_quality_flags",[]))),"template_id":"b6_entity_card_v1"})
    return out[:25]

def build_subsector_briefing_cards(b1_report=None, b2_report=None, b3_report=None, b4_report=None, b5_report=None):
    cards={}
    for src,key in [(_collect_entities(b1_report,("subsector_summaries",)),"b1"),(_collect_entities(b2_report,("subsector_asymmetry_summaries",)),"b2"),(_collect_entities(b3_report,("subsector_relative_interpretations",)),"b3"),(_collect_entities(b4_report,("subsector_replay_interpretations",)),"b4"),(_collect_entities(b5_report,("subsector_alert_interpretations",)),"b5")]:
        for r in src: cards.setdefault(str(r.get("subsector") or "UNKNOWN"),{})[key]=r
    out=[]
    for s in sorted(cards):
        c=cards[s]; label="PRIORITY_INFORMATIONAL"
        if "CRITICAL" in str((c.get("b5",{}).get("subsector_alert_label",""))): label="PRIORITY_CRITICAL_REVIEW"
        elif "HIGH" in str((c.get("b5",{}).get("subsector_alert_label",""))): label="PRIORITY_HIGH_REVIEW"
        elif any(x in str((c.get("b4",{}).get("subsector_replay_label",""))) for x in ["ACCELERATING","RISING"]): label="PRIORITY_ELEVATED_WATCHLIST"
        out.append({"subsector":s,"card_priority_label":label,"heatmap_context":deepcopy(c.get("b1",{})),"asymmetry_context":deepcopy(c.get("b2",{})),"benchmark_relative_context":deepcopy(c.get("b3",{})),"historical_replay_context":deepcopy(c.get("b4",{})),"alert_context":deepcopy(c.get("b5",{})),"dominant_subsector_condition":(c.get("b5",{}).get("subsector_alert_label") or c.get("b4",{}).get("subsector_replay_label") or c.get("b3",{}).get("subsector_relative_label") or c.get("b2",{}).get("subsector_asymmetry_label") or c.get("b1",{}).get("subsector_fragility_label") or "INSUFFICIENT_SUBSECTOR_CONTEXT"),"analyst_attention_reason":f"Subsector card assigned {label} under deterministic B6 precedence.","evidence_quality_flags":[],"template_id":"b6_subsector_card_v1"})
    return out[:20]

def build_evidence_appendix(b1_report=None, b2_report=None, b3_report=None, b4_report=None, b5_report=None, evidence_context=None):
    src={"B1": isinstance(b1_report, dict), "B2": isinstance(b2_report, dict), "B3": isinstance(b3_report, dict), "B4": isinstance(b4_report, dict), "B5": isinstance(b5_report, dict)}
    return {"section_id":"EVIDENCE_APPENDIX","source_phase_inventory":src,"evidence_chain_references":deepcopy((evidence_context or {}).get("evidence_chain_references", [])) if isinstance(evidence_context, dict) else [],"input_report_checksums":{"B1":_stable_checksum(b1_report) if isinstance(b1_report,dict) else None,"B2":_stable_checksum(b2_report) if isinstance(b2_report,dict) else None,"B3":_stable_checksum(b3_report) if isinstance(b3_report,dict) else None,"B4":_stable_checksum(b4_report) if isinstance(b4_report,dict) else None,"B5":_stable_checksum(b5_report) if isinstance(b5_report,dict) else None},"data_quality_flags":([] if isinstance(evidence_context,dict) else ["missing_evidence_context"]),"replay_trace":["B1 to B5 deterministic source extraction","fixed section templates","stable checksum generation"],"section_status":"OK" if any(src.values()) else "MISSING_INPUT","template_id":"b6_evidence_appendix_v1"}

def build_limitations_and_disclosures():
    return {"section_id":"LIMITATIONS_AND_DISCLOSURES","section_status":"OK","disclosures":["This is deterministic expectation-fragility intelligence.","It is not investment advice.","It is not a trading system.","It does not generate buy/sell/short recommendations.","It does not produce target prices.","It does not perform portfolio allocation.","It does not execute trades.","It does not backtest returns or P&L.","It does not use unrestricted LLM reasoning.","It depends on supplied deterministic inputs and evidence quality."],"template_id":"b6_limitations_disclosures_v1"}

def build_phase_b6_institutional_report(b1_report=None,b2_report=None,b3_report=None,b4_report=None,b5_report=None,evidence_context=None):
    ctx = build_b6_report_context(b1_report,b2_report,b3_report,b4_report,b5_report,evidence_context)
    out = {"phase_id":PHASE_ID,"phase_name":PHASE_NAME,"report_header":{"report_title":"Phase B6 Institutional Reporting and Analyst Briefing","platform_identity":"deterministic institutional expectation-fragility intelligence","report_type":"institutional_deterministic_briefing","generated_from_phases":["B1","B2","B3","B4","B5"],"section_order":SECTION_ORDER,"report_status":"OK" if ctx.get("available_sections") else "MISSING_INPUT"},"executive_summary":build_executive_fragility_summary(ctx,b1_report,b2_report,b3_report,b4_report,b5_report),"key_fragility_findings":build_key_fragility_findings(b1_report,b2_report,b3_report,b4_report,b5_report),"heatmap_briefing":build_heatmap_briefing_section(b1_report),"asymmetry_briefing":build_asymmetry_briefing_section(b2_report),"benchmark_relative_briefing":build_benchmark_relative_briefing_section(b3_report),"historical_replay_briefing":build_historical_replay_briefing_section(b4_report),"alert_briefing":build_alert_briefing_section(b5_report),"entity_briefing_cards":build_entity_briefing_cards(b1_report,b2_report,b3_report,b4_report,b5_report),"subsector_briefing_cards":build_subsector_briefing_cards(b1_report,b2_report,b3_report,b4_report,b5_report),"evidence_appendix":build_evidence_appendix(b1_report,b2_report,b3_report,b4_report,b5_report,evidence_context),"limitations_and_disclosures":build_limitations_and_disclosures(),"architecture_constraints":ARCHITECTURE_CONSTRAINTS}
    out["replay_metadata"]={"phase_id":PHASE_ID,"phase_name":PHASE_NAME,"report_template_version":REPORT_TEMPLATE_VERSION,"section_template_version":SECTION_TEMPLATE_VERSION,"classification_rule_version":CLASSIFICATION_RULE_VERSION,"input_checksum":_stable_checksum({"b1":b1_report,"b2":b2_report,"b3":b3_report,"b4":b4_report,"b5":b5_report,"evidence_context":evidence_context}),"output_checksum":_stable_checksum(out),"deterministic_section_order":SECTION_ORDER,"deterministic_sort_order":"fixed_severity_then_phase_then_identifier","tie_breaker_policy":"entity_id_then_ticker_then_entity_name_then_subsector","missing_section_policy":"emit_missing_input_section","entity_matching_policy":"entity_id_then_ticker_then_entity_name_exact","architecture_constraints":ARCHITECTURE_CONSTRAINTS}
    return out
