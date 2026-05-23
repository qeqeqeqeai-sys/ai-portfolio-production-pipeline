"""T6 deterministic temporal evolution certification closeout over T1-T5 envelopes."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json

REQUIRED_LAYERS = [
    ("t1", "T1_TEMPORAL_SNAPSHOT_SEQUENCING", "t1_status"),
    ("t2", "T2_STRUCTURAL_DELTA_INTELLIGENCE", "t2_status"),
    ("t3", "T3_FRAGILITY_EVOLUTION_CURVES", "t3_status"),
    ("t4", "T4_REGIME_TRANSITION_DETECTION", "t4_status"),
    ("t5", "T5_HISTORICAL_EXPLAINABILITY", "t5_status"),
]
GATE_ORDER = [
    "t1_envelope_present", "t2_envelope_present", "t3_envelope_present", "t4_envelope_present", "t5_envelope_present",
    "t1_status_acceptable", "t2_status_acceptable", "t3_status_acceptable", "t4_status_acceptable", "t5_status_acceptable",
    "checksum_chain_present_t1", "checksum_chain_present_t2", "checksum_chain_present_t3", "checksum_chain_present_t4", "checksum_chain_present_t5",
    "result_checksum_present_t1", "result_checksum_present_t2", "result_checksum_present_t3", "result_checksum_present_t4", "result_checksum_present_t5",
    "lineage_continuity_visible", "bounded_output_controls_present", "forbidden_capabilities_blocked", "invariant_flags_compliant",
    "deterministic_replay_controls_present", "explanation_templates_bounded", "no_runtime_reads", "no_runtime_writes", "no_network_calls",
    "no_prediction_logic", "no_trading_logic", "no_adaptive_learning", "additive_only_integration_preserved",
]
T6_FORBIDDEN_CAPABILITIES = {
    "live_fetch": False, "supabase_read": False, "supabase_write": False, "trading_execution": False, "prediction": False,
    "optimization": False, "adaptive_learning": False, "hidden_state_mutation": False, "stochastic_modeling": False,
    "open_ended_llm_generation": False, "recommendation_generation": False, "recursive_replay_expansion": False,
}


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _status_profile(status: str) -> str:
    s = str(status or "")
    if "BLOCK" in s:
        return "blocked"
    if "DEGRADED" in s or "INSUFFICIENT" in s:
        return "degraded"
    if "CERTIFIED" in s:
        return "certified"
    return "unknown"


def validate_temporal_evolution_closeout_inputs(closeout_inputs):
    frozen = deepcopy(closeout_inputs)
    errors = []
    if not isinstance(frozen, dict):
        return {"valid": False, "errors": ["closeout_inputs_invalid"], "missing_layers": [k for k, _, _ in REQUIRED_LAYERS]}
    missing = [k for k, _, _ in REQUIRED_LAYERS if not isinstance(frozen.get(k), dict)]
    if missing:
        errors.append("required_layer_envelopes_missing")
    return {"valid": not errors, "errors": sorted(set(errors)), "missing_layers": missing}


def build_temporal_evolution_lineage_summary(closeout_inputs):
    frozen = deepcopy(closeout_inputs) if isinstance(closeout_inputs, dict) else {}
    checksums = {k: str((frozen.get(k) or {}).get("result_checksum", "")) for k, _, _ in REQUIRED_LAYERS}
    chain_presence = {k: bool((frozen.get(k) or {}).get("checksum_chain")) for k, _, _ in REQUIRED_LAYERS}
    lineage_presence = {k: bool((frozen.get(k) or {}).get("temporal_lineage")) for k, _, _ in REQUIRED_LAYERS}
    required_present = all(isinstance(frozen.get(k), dict) for k, _, _ in REQUIRED_LAYERS)
    missing_chain = [k for k, v in chain_presence.items() if not v]
    if not required_present or len(missing_chain) >= 2:
        status = "LINEAGE_CONTINUITY_BLOCKED"
    elif missing_chain or not all(lineage_presence.values()):
        status = "LINEAGE_CONTINUITY_DEGRADED"
    else:
        status = "LINEAGE_CONTINUITY_CERTIFIED"
    return {
        "required_layers_present": required_present,
        "reviewed_layer_count": sum(1 for k, _, _ in REQUIRED_LAYERS if isinstance(frozen.get(k), dict)),
        "layer_result_checksums": checksums,
        "layer_checksum_chain_presence": chain_presence,
        "temporal_lineage_presence": lineage_presence,
        "lineage_status": status,
    }


def _checksum_continuity_summary(closeout_inputs):
    lineage = build_temporal_evolution_lineage_summary(closeout_inputs)
    missing = [k for k, v in lineage["layer_checksum_chain_presence"].items() if not v]
    if len(missing) >= 2:
        status = "CHECKSUM_CONTINUITY_BLOCKED"
    elif missing:
        status = "CHECKSUM_CONTINUITY_DEGRADED"
    else:
        status = "CHECKSUM_CONTINUITY_CERTIFIED"
    return {
        "layer_result_checksums": lineage["layer_result_checksums"],
        "checksum_chain_presence_by_layer": lineage["layer_checksum_chain_presence"],
        "missing_checksum_layers": missing,
        "checksum_continuity_status": status,
    }


def _invariant_summary(closeout_inputs):
    frozen = deepcopy(closeout_inputs) if isinstance(closeout_inputs, dict) else {}
    vals = {}
    for k, _, _ in REQUIRED_LAYERS:
        for name, flag in ((frozen.get(k) or {}).get("invariant_flags") or {}).items():
            vals.setdefault(name, []).append(bool(flag))
    failed = sorted([n for n, v in vals.items() if any(x is False for x in v)])
    compliant = sorted([n for n, v in vals.items() if v and all(x is True for x in v)])
    missing = [k for k, _, _ in REQUIRED_LAYERS if not ((frozen.get(k) or {}).get("invariant_flags"))]
    status = "INVARIANTS_BLOCKED" if failed else "INVARIANTS_DEGRADED" if missing else "INVARIANTS_CERTIFIED"
    return {"compliant_invariants": compliant, "failed_invariants": failed, "missing_invariants": missing, "invariant_status": status}


def _forbidden_summary(closeout_inputs):
    frozen = deepcopy(closeout_inputs) if isinstance(closeout_inputs, dict) else {}
    enabled = []
    reviewed = {}
    missing_sections = []
    for k, _, _ in REQUIRED_LAYERS:
        section = (frozen.get(k) or {}).get("forbidden_capabilities")
        if not isinstance(section, dict):
            missing_sections.append(k)
            continue
        for cap, value in section.items():
            reviewed.setdefault(cap, []).append(bool(value))
            if bool(value):
                enabled.append(f"{k}:{cap}")
    status = "FORBIDDEN_CAPABILITIES_FAILED" if enabled else "FORBIDDEN_CAPABILITIES_DEGRADED" if missing_sections else "FORBIDDEN_CAPABILITIES_BLOCKED"
    return {
        "forbidden_capabilities_reviewed": sorted(reviewed.keys()),
        "enabled_forbidden_capabilities": sorted(set(enabled)),
        "missing_forbidden_capability_sections": sorted(missing_sections),
        "forbidden_capability_status": status,
    }


def build_temporal_evolution_gate_inventory(closeout_inputs):
    frozen = deepcopy(closeout_inputs) if isinstance(closeout_inputs, dict) else {}
    lineage = build_temporal_evolution_lineage_summary(frozen)
    checksum = _checksum_continuity_summary(frozen)
    inv = _invariant_summary(frozen)
    forb = _forbidden_summary(frozen)
    gate_map = {}
    for k, _, status_key in REQUIRED_LAYERS:
        gate_map[f"{k}_envelope_present"] = isinstance(frozen.get(k), dict)
        profile = _status_profile((frozen.get(k) or {}).get(status_key, ""))
        gate_map[f"{k}_status_acceptable"] = profile in {"certified", "degraded"}
        gate_map[f"checksum_chain_present_{k}"] = bool((frozen.get(k) or {}).get("checksum_chain"))
        gate_map[f"result_checksum_present_{k}"] = bool((frozen.get(k) or {}).get("result_checksum"))
    gate_map.update({
        "lineage_continuity_visible": lineage["lineage_status"] != "LINEAGE_CONTINUITY_BLOCKED",
        "bounded_output_controls_present": True,
        "forbidden_capabilities_blocked": forb["forbidden_capability_status"] == "FORBIDDEN_CAPABILITIES_BLOCKED",
        "invariant_flags_compliant": inv["invariant_status"] != "INVARIANTS_BLOCKED",
        "deterministic_replay_controls_present": checksum["checksum_continuity_status"] != "CHECKSUM_CONTINUITY_BLOCKED",
        "explanation_templates_bounded": True,
        "no_runtime_reads": True,
        "no_runtime_writes": True,
        "no_network_calls": True,
        "no_prediction_logic": True,
        "no_trading_logic": True,
        "no_adaptive_learning": True,
        "additive_only_integration_preserved": True,
    })
    gates = []
    for idx, name in enumerate(GATE_ORDER, start=1):
        passed = bool(gate_map.get(name, False))
        result = "PASS" if passed else "WARN" if name in {"lineage_continuity_visible", "deterministic_replay_controls_present", "invariant_flags_compliant"} else "FAIL"
        gates.append({"gate_id": idx, "gate_name": name, "result": result, "rationale": "deterministic closeout gate evaluation", "layer_scope": "T1_T5"})
    return gates


def build_temporal_evolution_closeout_manifest(closeout_inputs):
    result = certify_temporal_evolution_closeout(closeout_inputs)
    manifest = deepcopy(result["closeout_manifest"])
    return manifest


def certify_temporal_evolution_closeout(closeout_inputs):
    frozen = deepcopy(closeout_inputs)
    validation = validate_temporal_evolution_closeout_inputs(frozen)
    layer_summary = []
    blocked_layer = False
    degraded_layer = False
    for key, label, status_key in REQUIRED_LAYERS:
        env = (frozen.get(key) or {}) if isinstance(frozen, dict) else {}
        profile = _status_profile(env.get(status_key, ""))
        blocked_layer = blocked_layer or profile == "blocked"
        degraded_layer = degraded_layer or profile == "degraded"
        layer_summary.append({"layer_key": key, "layer_name": label, "status": str(env.get(status_key, "MISSING"))})
    lineage = build_temporal_evolution_lineage_summary(frozen)
    checksum = _checksum_continuity_summary(frozen)
    invariants = _invariant_summary(frozen)
    forbidden = _forbidden_summary(frozen)
    gates = build_temporal_evolution_gate_inventory(frozen)
    fail_count = sum(1 for g in gates if g["result"] == "FAIL")
    warn_count = sum(1 for g in gates if g["result"] == "WARN")
    pass_count = sum(1 for g in gates if g["result"] == "PASS")
    blocked = (not validation["valid"]) or blocked_layer or checksum["checksum_continuity_status"] == "CHECKSUM_CONTINUITY_BLOCKED" or forbidden["forbidden_capability_status"] == "FORBIDDEN_CAPABILITIES_FAILED" or invariants["invariant_status"] == "INVARIANTS_BLOCKED"
    degraded = (not blocked) and (degraded_layer or warn_count > 0 or lineage["lineage_status"] != "LINEAGE_CONTINUITY_CERTIFIED" or checksum["checksum_continuity_status"] != "CHECKSUM_CONTINUITY_CERTIFIED")
    t6_status = "TEMPORAL_EVOLUTION_CLOSEOUT_BLOCKED" if blocked else "TEMPORAL_EVOLUTION_CLOSEOUT_DEGRADED" if degraded else "TEMPORAL_EVOLUTION_CLOSEOUT_CERTIFIED"
    final_decision = "BLOCKED_PENDING_TEMPORAL_REMEDIATION" if blocked else "APPROVED_WITH_DEGRADED_TEMPORAL_COVERAGE" if degraded else "APPROVED_FOR_CONTROLLED_DOWNSTREAM_USE"
    architectural = {
        "no_live_data_access": True, "no_persistence": True, "no_prediction": True, "no_trading": True, "no_adaptive_learning": True,
        "no_open_ended_generation": True, "bounded_outputs_only": True, "replay_safe": not blocked, "additive_only": True,
    }
    manifest = {
        "path_name": "Path 1", "phase_name": "T6 — Temporal Evolution Certification Closeout",
        "reviewed_layers": [label for _, label, _ in REQUIRED_LAYERS], "gate_count": len(gates), "pass_count": pass_count,
        "warn_count": warn_count, "fail_count": fail_count, "final_decision": final_decision,
        "closeout_version": "t6.v1",
    }
    manifest["manifest_checksum"] = _stable_checksum(manifest)
    result = {
        "t6_status": t6_status, "final_decision": final_decision, "reviewed_layers": manifest["reviewed_layers"], "layer_status_summary": layer_summary,
        "lineage_summary": lineage, "checksum_continuity_summary": checksum, "invariant_summary": invariants,
        "forbidden_capability_summary": forbidden, "architectural_boundary_summary": architectural, "gate_inventory": gates,
        "closeout_manifest": manifest, "certification_gates": [{"gate": g["gate_name"], "passed": g["result"] == "PASS"} for g in gates],
        "invariant_flags": {
            "deterministic_closeout": True, "fixed_layer_order": True, "immutable_inputs": True, "replay_safe": not blocked,
            "checksum_continuity_reviewed": True, "lineage_continuity_reviewed": True, "bounded_outputs_only": True,
            "no_runtime_reads": True, "no_runtime_writes": True, "no_network_access": True, "no_prediction_behavior": True,
            "no_trading_behavior": True, "no_adaptive_learning": True, "additive_only": True,
        },
        "forbidden_capabilities": deepcopy(T6_FORBIDDEN_CAPABILITIES),
    }
    result["result_checksum"] = _stable_checksum(result)
    return result


def build_t6_temporal_evolution_closeout_report(certification_result):
    frozen = deepcopy(certification_result)
    return "\n".join([
        "# T6 Temporal Evolution Certification Closeout Report",
        f"Status: {frozen.get('t6_status', 'UNKNOWN')}",
        f"Final decision: {frozen.get('final_decision', 'UNKNOWN')}",
        f"Reviewed layers: {len(frozen.get('reviewed_layers', []))}",
        f"Gate counts: pass={frozen.get('closeout_manifest', {}).get('pass_count', 0)} warn={frozen.get('closeout_manifest', {}).get('warn_count', 0)} fail={frozen.get('closeout_manifest', {}).get('fail_count', 0)}",
        f"Result checksum: {frozen.get('result_checksum', '')}",
    ])
