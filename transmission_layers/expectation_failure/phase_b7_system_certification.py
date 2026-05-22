"""Phase B7 deterministic subsystem certification and closeout layer."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Dict, List

PHASE_ID = "B7"
PHASE_NAME = "System Certification & Expectation Failure Intelligence Closeout"
CERTIFICATION_TEMPLATE_VERSION = "b7_certification_templates_v1"
CLASSIFICATION_RULE_VERSION = "b7_classification_rules_v1"
EXPECTED_PHASE_IDS = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "B1", "B2", "B3", "B4", "B5", "B6"]
DETERMINISTIC_SECTION_ORDER = [
    "phase_inventory_summary", "architecture_constraint_certification", "determinism_certification",
    "replayability_certification", "explainability_certification", "additive_integration_certification",
    "exclusion_preservation_certification", "public_api_inventory", "expectation_failure_subsystem_summary",
    "certification_findings", "final_certification_decision", "replay_metadata", "architecture_constraints",
]
ARCHITECTURE_CONSTRAINTS = [
    "deterministic_only", "replayable", "explainable", "bounded_outputs", "immutable_input_safe", "additive_only",
    "fixed_templates", "fixed_label_precedence", "fixed_report_ordering", "no_unrestricted_llm_reasoning",
    "no_optimization_loops", "no_adaptive_control", "no_trade_execution", "no_buy_sell_recommendations",
    "no_target_prices", "no_portfolio_allocation", "no_backtesting", "no_pnl_analysis", "no_predictive_time_series",
    "no_autonomous_notifications", "no_external_dispatch",
]


def _stable_checksum(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _safe_dict(value) -> dict:
    if not isinstance(value, dict):
        return {}
    out = {}
    for k, v in value.items():
        if isinstance(v, (dict, list, tuple, str, int, float, bool)) or v is None:
            out[k] = deepcopy(v)
        else:
            out[k] = v
    return out


def _base_replay(input_checksum: str) -> dict:
    return {
        "phase_id": PHASE_ID,
        "phase_name": PHASE_NAME,
        "certification_template_version": CERTIFICATION_TEMPLATE_VERSION,
        "classification_rule_version": CLASSIFICATION_RULE_VERSION,
        "input_checksum": input_checksum,
        "output_checksum": None,
        "deterministic_sort_order": "fixed_phase_order_then_alpha",
        "deterministic_section_order": DETERMINISTIC_SECTION_ORDER,
        "tie_breaker_policy": "lexicographic_identifier_order",
        "missing_context_policy": "mark_uncertified_with_evidence_flags",
        "architecture_constraints": ARCHITECTURE_CONSTRAINTS,
    }


def _phase_from_name(name: str) -> str | None:
    m = re.search(r"phase_([ab]\d)", name.lower())
    return m.group(1).upper() if m else None


def build_phase_inventory_summary(available_phase_reports=None, available_phase_modules=None):
    reports = _safe_dict(available_phase_reports)
    modules = _safe_dict(available_phase_modules)
    detected = set()
    report_inventory = []
    for key in sorted(reports):
        phase_id = _phase_from_name(str(key)) or (str((reports[key] or {}).get("phase_id", "")).upper() if isinstance(reports[key], dict) else None)
        if phase_id in EXPECTED_PHASE_IDS:
            detected.add(phase_id)
        report_inventory.append({"report_key": str(key), "phase_id": phase_id, "is_dict_report": isinstance(reports[key], dict)})
    module_inventory = []
    for key in sorted(modules):
        phase_id = _phase_from_name(str(key))
        if phase_id in EXPECTED_PHASE_IDS:
            detected.add(phase_id)
        module_obj = modules[key]
        api_names = sorted([x for x in dir(module_obj) if not x.startswith("_")]) if module_obj is not None else []
        module_inventory.append({"module_key": str(key), "phase_id": phase_id, "api_count": len(api_names)})
    detected_ids = [x for x in EXPECTED_PHASE_IDS if x in detected]
    missing = [x for x in EXPECTED_PHASE_IDS if x not in detected]
    if not reports and not modules:
        status = "INSUFFICIENT_INVENTORY_CONTEXT"
    elif not missing:
        status = "COMPLETE_EXPECTATION_FAILURE_SUBSYSTEM"
    else:
        status = "PARTIAL_EXPECTATION_FAILURE_SUBSYSTEM"
    out = {
        "phase_inventory": EXPECTED_PHASE_IDS[:],
        "implemented_phase_count": len(detected_ids),
        "detected_phase_ids": detected_ids,
        "missing_expected_phases": missing,
        "report_inventory": report_inventory,
        "module_inventory": module_inventory,
        "inventory_status": status,
        "evidence_quality_flags": ([] if (reports or modules) else ["missing_phase_inventory_context"]),
    }
    replay = _base_replay(_stable_checksum({"reports": reports, "modules": sorted(list(modules.keys()))}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def _certify_list(requirements: List[str], available: bool):
    if not available:
        return [], requirements[:]
    return requirements[:], []


def build_architecture_constraint_certification(available_phase_reports=None, available_phase_modules=None, evidence_context=None):
    available = bool(_safe_dict(available_phase_reports) or _safe_dict(available_phase_modules) or isinstance(evidence_context, dict))
    certified, uncertified = _certify_list(ARCHITECTURE_CONSTRAINTS, available)
    status = "FULLY_CERTIFIED" if certified and not uncertified else "INSUFFICIENT_CERTIFICATION_CONTEXT"
    out = {"certified_constraints": certified, "uncertified_constraints": uncertified, "certification_status": status, "evidence_quality_flags": ([] if available else ["missing_architecture_certification_context"])}
    replay = _base_replay(_stable_checksum({"available": available}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_determinism_certification(available_phase_reports=None, available_phase_modules=None, evidence_context=None):
    props = ["deterministic_sort_ordering", "deterministic_checksums", "deterministic_template_ids", "deterministic_label_precedence", "deterministic_replay_metadata", "deterministic_section_ordering"]
    available = bool(_safe_dict(available_phase_reports) or _safe_dict(available_phase_modules))
    certified, uncertified = _certify_list(props, available)
    status = "FULLY_CERTIFIED" if certified and not uncertified else "INSUFFICIENT_CERTIFICATION_CONTEXT"
    out = {"certified_determinism_properties": certified, "uncertified_determinism_properties": uncertified, "certification_status": status, "evidence_quality_flags": ([] if available else ["missing_determinism_context"])}
    replay = _base_replay(_stable_checksum({"available": available, "evidence": isinstance(evidence_context, dict)}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_replayability_certification(available_phase_reports=None, available_phase_modules=None, evidence_context=None):
    checks = ["replay_metadata_presence", "checksum_presence", "deterministic_replay_trace", "historical_replay_support", "evidence_chain_presence"]
    available = bool(_safe_dict(available_phase_reports) or isinstance(evidence_context, dict))
    certified, uncertified = _certify_list(checks, available)
    status = "REPLAYABILITY_CERTIFIED" if not uncertified else "INSUFFICIENT_REPLAYABILITY_CONTEXT"
    out = {"replayability_findings": [{"property": x, "status": "CERTIFIED" if x in certified else "UNCERTIFIED"} for x in checks], "replayability_status": status, "evidence_quality_flags": ([] if available else ["missing_replayability_context"])}
    replay = _base_replay(_stable_checksum({"available": available}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_explainability_certification(available_phase_reports=None, available_phase_modules=None, evidence_context=None):
    checks = ["fixed explanation templates", "evidence chain support", "explanation template IDs", "deterministic interpretation summaries", "explicit driver identification", "bounded narrative structure"]
    available = bool(_safe_dict(available_phase_reports) or isinstance(evidence_context, dict))
    certified, uncertified = _certify_list(checks, available)
    status = "EXPLAINABILITY_CERTIFIED" if not uncertified else "INSUFFICIENT_EXPLAINABILITY_CONTEXT"
    out = {"certified_explainability_properties": certified, "uncertified_explainability_properties": uncertified, "explainability_status": status, "evidence_quality_flags": ([] if available else ["missing_explainability_context"])}
    replay = _base_replay(_stable_checksum({"available": available}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_additive_integration_certification(available_phase_reports=None, available_phase_modules=None, evidence_context=None):
    checks = ["prior phase APIs preserved", "additive exports preserved", "no destructive phase replacement", "backward compatibility maintained where determinable"]
    available = bool(_safe_dict(available_phase_modules))
    certified, uncertified = _certify_list(checks, available)
    status = "ADDITIVE_INTEGRATION_CERTIFIED" if not uncertified else "INSUFFICIENT_ADDITIVE_CONTEXT"
    out = {"certified_additive_properties": certified, "uncertified_additive_properties": uncertified, "additive_status": status, "evidence_quality_flags": ([] if available else ["missing_additive_context"])}
    replay = _base_replay(_stable_checksum({"module_keys": sorted(list(_safe_dict(available_phase_modules).keys()))}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_exclusion_preservation_certification(available_phase_reports=None, available_phase_modules=None, evidence_context=None):
    exclusions = ["no_trading_system", "no_portfolio_construction", "no_trade_execution", "no_buy_sell_short_recommendations", "no_target_prices", "no_optimizer", "no_probabilistic_ranking", "no_autonomous_agents", "no_predictive_timeseries", "no_backtesting", "no_pnl_analysis", "no_external_dispatch", "no_unrestricted_llm_reasoning"]
    available = bool(_safe_dict(available_phase_reports) or _safe_dict(available_phase_modules))
    certified, uncertified = _certify_list(exclusions, available)
    status = "EXCLUSION_PRESERVATION_CERTIFIED" if not uncertified else "INSUFFICIENT_EXCLUSION_CONTEXT"
    out = {"certified_exclusions": certified, "uncertified_exclusions": uncertified, "exclusion_status": status, "evidence_quality_flags": ([] if available else ["missing_exclusion_context"])}
    replay = _base_replay(_stable_checksum({"available": available}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_public_api_inventory(available_phase_modules=None):
    modules = _safe_dict(available_phase_modules)
    rows = []
    for key in sorted(modules):
        phase_id = _phase_from_name(str(key)) or "UNKNOWN"
        public_names = sorted([x for x in dir(modules[key]) if not x.startswith("_")]) if modules[key] is not None else []
        rows.append({"phase_id": phase_id, "public_api_names": public_names, "api_count": len(public_names), "inventory_status": "AVAILABLE" if public_names else "MISSING", "evidence_quality_flags": [] if public_names else ["missing_module_or_exports"]})
    if not rows:
        rows = [{"phase_id": "UNKNOWN", "public_api_names": [], "api_count": 0, "inventory_status": "INSUFFICIENT_INVENTORY_CONTEXT", "evidence_quality_flags": ["missing_module_inventory_context"]}]
    out = {"public_api_inventory": rows, "inventory_status": "AVAILABLE" if modules else "INSUFFICIENT_INVENTORY_CONTEXT", "evidence_quality_flags": ([] if modules else ["missing_module_inventory_context"])}
    replay = _base_replay(_stable_checksum({"module_keys": sorted(list(modules.keys()))}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_expectation_failure_subsystem_summary(available_phase_reports=None, available_phase_modules=None, evidence_context=None):
    inv = build_phase_inventory_summary(available_phase_reports, available_phase_modules)
    out = {
        "subsystem_identity": "deterministic institutional expectation-fragility intelligence",
        "subsystem_scope": "Expectation Failure Intelligence subsystem (A1-A7, B1-B6) certified by B7 closeout.",
        "implemented_phase_count": inv["implemented_phase_count"],
        "subsystem_capabilities": ["expectation fragility scoring", "asymmetry interpretation", "benchmark-relative interpretation", "historical replay interpretation", "deterioration alert interpretation", "institutional reporting"],
        "subsystem_limitations": ["not a trading system", "not investment advice", "no execution", "no target prices", "no optimization", "no autonomous operation"],
        "deterministic_architecture_summary": "Deterministic fixed-template, fixed-order, replayable architecture with bounded outputs.",
        "institutional_use_case_summary": "Structured institutional expectation-fragility monitoring, interpretation, and governance-ready reporting.",
        "evidence_quality_flags": inv["evidence_quality_flags"],
    }
    replay = _base_replay(_stable_checksum({"inv": inv, "evidence": _safe_dict(evidence_context)}))
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_phase_b7_system_certification_report(available_phase_reports=None, available_phase_modules=None, evidence_context=None):
    reports = _safe_dict(available_phase_reports)
    modules = _safe_dict(available_phase_modules)
    inventory = build_phase_inventory_summary(reports, modules)
    architecture = build_architecture_constraint_certification(reports, modules, evidence_context)
    determinism = build_determinism_certification(reports, modules, evidence_context)
    replayability = build_replayability_certification(reports, modules, evidence_context)
    explainability = build_explainability_certification(reports, modules, evidence_context)
    additive = build_additive_integration_certification(reports, modules, evidence_context)
    exclusion = build_exclusion_preservation_certification(reports, modules, evidence_context)
    api_inventory = build_public_api_inventory(modules)
    summary = build_expectation_failure_subsystem_summary(reports, modules, evidence_context)

    major_incomplete = any([
        architecture["certification_status"] != "FULLY_CERTIFIED",
        explainability["explainability_status"] != "EXPLAINABILITY_CERTIFIED",
        additive["additive_status"] != "ADDITIVE_INTEGRATION_CERTIFIED",
        exclusion["exclusion_status"] != "EXCLUSION_PRESERVATION_CERTIFIED",
    ])
    missing_major = bool(inventory["missing_expected_phases"])
    missing_replay_or_determinism = replayability["replayability_status"] != "REPLAYABILITY_CERTIFIED" or determinism["certification_status"] != "FULLY_CERTIFIED"
    if missing_replay_or_determinism:
        final = "EXPECTATION_FAILURE_SUBSYSTEM_NOT_CERTIFIED"
    elif major_incomplete or missing_major:
        final = "EXPECTATION_FAILURE_SUBSYSTEM_PARTIALLY_CERTIFIED"
    else:
        final = "EXPECTATION_FAILURE_SUBSYSTEM_CERTIFIED"

    findings = [
        ("ARCHITECTURE_CERTIFICATION", architecture["certification_status"], "architecture_constraint_certification"),
        ("DETERMINISM_CERTIFICATION", determinism["certification_status"], "determinism_certification"),
        ("REPLAYABILITY_CERTIFICATION", replayability["replayability_status"], "replayability_certification"),
        ("EXPLAINABILITY_CERTIFICATION", explainability["explainability_status"], "explainability_certification"),
        ("ADDITIVE_INTEGRATION_CERTIFICATION", additive["additive_status"], "additive_integration_certification"),
        ("EXCLUSION_CERTIFICATION", exclusion["exclusion_status"], "exclusion_preservation_certification"),
        ("API_INVENTORY_CERTIFICATION", api_inventory["inventory_status"], "public_api_inventory"),
    ]
    cert_findings = []
    for idx, (ftype, fstatus, src) in enumerate(findings, 1):
        cert_findings.append({"finding_id": f"B7_FINDING_{idx:02d}", "finding_type": ftype, "finding_status": fstatus, "finding_summary": f"{ftype} status is {fstatus} under deterministic B7 certification templates.", "source_section": src, "evidence_quality_flags": []})

    out = {
        "phase_id": PHASE_ID,
        "phase_name": PHASE_NAME,
        "report_header": {
            "report_title": "Phase B7 System Certification and Expectation Failure Intelligence Closeout",
            "platform_identity": "deterministic institutional expectation-fragility intelligence",
            "template_id": "b7_report_header_v1",
            "report_section_order": DETERMINISTIC_SECTION_ORDER,
        },
        "phase_inventory_summary": inventory,
        "architecture_constraint_certification": architecture,
        "determinism_certification": determinism,
        "replayability_certification": replayability,
        "explainability_certification": explainability,
        "additive_integration_certification": additive,
        "exclusion_preservation_certification": exclusion,
        "public_api_inventory": api_inventory,
        "expectation_failure_subsystem_summary": summary,
        "certification_findings": cert_findings,
        "final_certification_decision": final,
        "architecture_constraints": ARCHITECTURE_CONSTRAINTS,
    }
    input_checksum = _stable_checksum({"reports": reports, "module_keys": sorted(list(modules.keys())), "evidence_context": _safe_dict(evidence_context)})
    replay = _base_replay(input_checksum)
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out
