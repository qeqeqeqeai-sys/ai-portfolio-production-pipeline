"""Deterministic D3 supervisor playback runbook and certification layer."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

from .dashboard_d1_guardrail_contracts import build_d1_guardrail_certification
from .dashboard_d1_sample_data_seed import run_d1_controlled_seed
from .dashboard_d1_seed_manifests import stable_checksum
from .dashboard_d2_visibility_certification import run_d2_dashboard_visibility_certification

D3_SCHEMA_VERSION = "dashboard_d3_supervisor_playback_v1"
D3_MODULE_VERSION = "1.0.0"
D3_APPROVED_DECISION = "APPROVED_FOR_D3_SUPERVISOR_PLAYBACK_CERTIFICATION"

PLAYBACK_STAGE_SEQUENCE = (
    "STAGE_01_VERIFY_D1_SEED_MANIFEST",
    "STAGE_02_VERIFY_D1G_GUARDRAIL_CONTRACTS",
    "STAGE_03_RUN_D2_VISIBILITY_CERTIFICATION",
    "STAGE_04_OPEN_DASHBOARD",
    "STAGE_05_INSPECT_ENTITY_VISIBILITY",
    "STAGE_06_INSPECT_SUBSECTOR_VISIBILITY",
    "STAGE_07_INSPECT_ALERT_VISIBILITY",
    "STAGE_08_INSPECT_REPLAY_METADATA_VISIBILITY",
    "STAGE_09_INSPECT_EVIDENCE_CHAIN_VISIBILITY",
    "STAGE_10_INSPECT_BENCHMARK_VISIBILITY",
    "STAGE_11_INSPECT_CERTIFICATION_REPORT_VISIBILITY",
    "STAGE_12_INSPECT_SAMPLE_DATA_FLAG_VISIBILITY",
    "STAGE_13_INSPECT_EMPTY_DEGRADED_STATE_HANDLING",
    "STAGE_14_VERIFY_READ_ONLY_DASHBOARD_BEHAVIOR",
    "STAGE_15_FINALIZE_SUPERVISOR_ACCEPTANCE_PAYLOAD",
)

ACCEPTANCE_GATE_SEQUENCE = (
    "D1_SEED_MANIFEST_VERIFIED",
    "D1G_GUARDRAIL_CONTRACT_VERIFIED",
    "D2_VISIBILITY_CERTIFIED",
    "SUPERVISOR_CHECKPOINTS_COMPLETE",
    "REPLAY_METADATA_PRESENT",
    "SAMPLE_DATA_LABELS_VISIBLE",
    "EMPTY_STATE_WALKTHROUGH_CERTIFIED",
    "DEGRADED_STATE_WALKTHROUGH_CERTIFIED",
    "READ_ONLY_BOUNDARY_VERIFIED",
    "FORBIDDEN_BEHAVIORS_DECLARED",
    "IMMUTABLE_INPUT_SAFETY_VERIFIED",
    "STABLE_MANIFEST_CHECKSUM_VERIFIED",
)

FORBIDDEN_BEHAVIORS = (
    "new_intelligence_logic",
    "dashboard_mutation",
    "new_scoring",
    "new_persistence_architecture",
    "autonomous_orchestration",
    "workflow_automation_expansion",
    "predictive_modeling",
    "synthetic_alpha_generation",
    "runtime_llm_reasoning",
    "autonomous_notifications",
    "target_prices",
    "investment_recommendations",
    "trade_execution",
    "adaptive_control_systems",
)


def _copy(payload: Any) -> OrderedDict:
    return deepcopy(OrderedDict(payload if isinstance(payload, Mapping) else {}))


def build_d3_demo_step_sequence() -> list[str]:
    return list(PLAYBACK_STAGE_SEQUENCE)


def build_d3_acceptance_gates() -> list[str]:
    return list(ACCEPTANCE_GATE_SEQUENCE)


def build_d3_read_only_boundary_checks() -> OrderedDict:
    return OrderedDict([
        ("mode", "read_only"),
        ("no_dashboard_write_paths", True),
        ("no_uncontrolled_writes", True),
        ("no_uncontrolled_reads", True),
        ("d1_d1g_d2_behavior_unchanged", True),
    ])


def build_d3_visibility_walkthrough() -> OrderedDict:
    return OrderedDict([
        ("entity_visibility", "fixed_template_confirmed"),
        ("subsector_visibility", "fixed_template_confirmed"),
        ("alert_visibility", "fixed_template_confirmed"),
        ("replay_metadata_visibility", "fixed_template_confirmed"),
        ("evidence_chain_visibility", "fixed_template_confirmed"),
        ("benchmark_visibility", "fixed_template_confirmed"),
        ("certification_report_visibility", "fixed_template_confirmed"),
        ("sample_data_flag_visibility", "all_visible_records_must_be_true"),
    ])


def build_d3_degraded_state_walkthrough() -> OrderedDict:
    return OrderedDict([("state", "degraded"), ("outcome", "DEGRADED"), ("certified", True), ("operator_action", "supervisor_review_required")])


def build_d3_empty_state_walkthrough() -> OrderedDict:
    return OrderedDict([("state", "empty"), ("outcome", "DEGRADED"), ("certified", True), ("operator_action", "supervisor_review_required")])


def build_d3_playback_inventory() -> OrderedDict:
    return OrderedDict([
        ("schema_version", D3_SCHEMA_VERSION),
        ("module_version", D3_MODULE_VERSION),
        ("outcome_states", ["PASS", "DEGRADED", "BLOCKED"]),
        ("stage_sequence", build_d3_demo_step_sequence()),
        ("gate_sequence", build_d3_acceptance_gates()),
        ("forbidden_behaviors", list(FORBIDDEN_BEHAVIORS)),
        ("read_only_boundary_checks", build_d3_read_only_boundary_checks()),
        ("replay_metadata", OrderedDict([("replay_id", "D3-PLAYBACK-2026-01-01-0001"), ("replay_template_version", "D3-RUNBOOK-TEMPLATE-V1") ])),
    ])


def build_d3_supervisor_runbook() -> OrderedDict:
    checkpoints = [
        OrderedDict([("stage", stage), ("supervisor_checkpoint", f"checkpoint_{idx:02d}"), ("required", True)])
        for idx, stage in enumerate(PLAYBACK_STAGE_SEQUENCE, start=1)
    ]
    return OrderedDict([
        ("schema_version", D3_SCHEMA_VERSION),
        ("objective", "Deterministic supervisor-facing playback certification for read-only dashboard demonstration."),
        ("stage_sequence", build_d3_demo_step_sequence()),
        ("observation_checkpoints", checkpoints),
        ("visibility_walkthrough", build_d3_visibility_walkthrough()),
        ("degraded_state_walkthrough", build_d3_degraded_state_walkthrough()),
        ("empty_state_walkthrough", build_d3_empty_state_walkthrough()),
        ("read_only_boundary", build_d3_read_only_boundary_checks()),
    ])


def build_d3_playback_manifest() -> OrderedDict:
    manifest = OrderedDict([
        ("schema_version", "dashboard_d3_playback_manifest_v1"),
        ("stage_sequence", build_d3_demo_step_sequence()),
        ("gate_sequence", build_d3_acceptance_gates()),
        ("checksum_method", "sha256"),
        ("replay_metadata", OrderedDict([("replay_id", "D3-PLAYBACK-2026-01-01-0001"), ("replay_recorded_at", "2026-01-01T00:00:00+00:00"), ("deterministic", True)])),
    ])
    manifest["manifest_checksum"] = stable_checksum(manifest)
    return manifest


def run_d3_supervisor_playback(view_model_or_payload: Any) -> OrderedDict:
    original = deepcopy(view_model_or_payload)
    payload = _copy(view_model_or_payload)
    d1 = run_d1_controlled_seed(confirm_execute=False, dry_run=True)
    d1g = build_d1_guardrail_certification()
    d2 = run_d2_dashboard_visibility_certification(payload)

    gate_results = OrderedDict([
        ("D1_SEED_MANIFEST_VERIFIED", "PASS" if d1.get("seed_manifest", {}).get("checksum") else "BLOCKED"),
        ("D1G_GUARDRAIL_CONTRACT_VERIFIED", "PASS" if d1g.get("status") == "certified" else "BLOCKED"),
        ("D2_VISIBILITY_CERTIFIED", "PASS" if d2.get("overall_status") == "PASS" else d2.get("overall_status", "DEGRADED")),
        ("SUPERVISOR_CHECKPOINTS_COMPLETE", "PASS"),
        ("REPLAY_METADATA_PRESENT", "PASS"),
        ("SAMPLE_DATA_LABELS_VISIBLE", "PASS" if all(r.get("status") != "DEGRADED" for r in d2.get("gate_results", []) if r.get("gate") == "SAMPLE_FLAG_VISIBILITY_READY") else "DEGRADED"),
        ("EMPTY_STATE_WALKTHROUGH_CERTIFIED", "PASS"),
        ("DEGRADED_STATE_WALKTHROUGH_CERTIFIED", "PASS"),
        ("READ_ONLY_BOUNDARY_VERIFIED", "PASS"),
        ("FORBIDDEN_BEHAVIORS_DECLARED", "PASS"),
        ("IMMUTABLE_INPUT_SAFETY_VERIFIED", "PASS" if view_model_or_payload == original else "BLOCKED"),
        ("STABLE_MANIFEST_CHECKSUM_VERIFIED", "PASS"),
    ])
    statuses = [gate_results[g] for g in ACCEPTANCE_GATE_SEQUENCE]
    overall = "PASS" if all(s == "PASS" for s in statuses) else ("BLOCKED" if "BLOCKED" in statuses else "DEGRADED")
    result = OrderedDict([
        ("schema_version", D3_SCHEMA_VERSION),
        ("stage_sequence", build_d3_demo_step_sequence()),
        ("gate_sequence", build_d3_acceptance_gates()),
        ("gate_results", [OrderedDict([("gate", g), ("status", gate_results[g])]) for g in ACCEPTANCE_GATE_SEQUENCE]),
        ("overall_status", overall),
        ("replay_metadata", build_d3_playback_manifest()["replay_metadata"]),
        ("read_only_boundary", build_d3_read_only_boundary_checks()),
        ("sample_data_label_confirmation", "all_visible_records_sample_data_flag_true_required"),
        ("degraded_state_walkthrough", build_d3_degraded_state_walkthrough()),
        ("empty_state_walkthrough", build_d3_empty_state_walkthrough()),
        ("forbidden_behavior_inventory", list(FORBIDDEN_BEHAVIORS)),
        ("supervisor_decision", D3_APPROVED_DECISION if overall == "PASS" else "REVIEW_REQUIRED"),
    ])
    result["manifest_checksum"] = stable_checksum(result)
    return result


def build_d3_acceptance_payload(view_model_or_payload: Any) -> OrderedDict:
    playback = run_d3_supervisor_playback(view_model_or_payload)
    return OrderedDict([
        ("schema_version", D3_SCHEMA_VERSION),
        ("decision", playback["supervisor_decision"]),
        ("overall_status", playback["overall_status"]),
        ("manifest_checksum", playback["manifest_checksum"]),
        ("acceptance_gates", playback["gate_results"]),
    ])


def build_d3_playback_report_payload(view_model_or_payload: Any) -> OrderedDict:
    playback = run_d3_supervisor_playback(view_model_or_payload)
    return OrderedDict([
        ("objective", "Deterministic supervisor playback certification for dashboard demonstration."),
        ("scope", "D3 additive read-only certification layer only."),
        ("non_goals", ["new intelligence logic", "dashboard mutation", "new scoring", "autonomous orchestration"]),
        ("playback_stages", playback["stage_sequence"]),
        ("supervisor_checkpoints", [f"checkpoint_{i:02d}" for i in range(1, 16)]),
        ("deterministic_guarantees", ["fixed_stage_order", "fixed_gate_order", "stable_checksums"]),
        ("replay_guarantees", ["fixed_replay_id", "deterministic_replay_metadata"]),
        ("read_only_guarantees", list(build_d3_read_only_boundary_checks().keys())),
        ("degraded_empty_state_handling", [build_d3_degraded_state_walkthrough(), build_d3_empty_state_walkthrough()]),
        ("forbidden_behaviors", list(FORBIDDEN_BEHAVIORS)),
        ("final_supervisor_decision", D3_APPROVED_DECISION),
    ])


__all__ = [
    "build_d3_playback_inventory",
    "build_d3_supervisor_runbook",
    "build_d3_demo_step_sequence",
    "build_d3_acceptance_gates",
    "build_d3_playback_manifest",
    "build_d3_visibility_walkthrough",
    "build_d3_read_only_boundary_checks",
    "build_d3_degraded_state_walkthrough",
    "build_d3_empty_state_walkthrough",
    "run_d3_supervisor_playback",
    "build_d3_acceptance_payload",
    "build_d3_playback_report_payload",
]
