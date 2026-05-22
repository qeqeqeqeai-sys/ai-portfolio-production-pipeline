from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_d1_seed_payload,
    build_d3_acceptance_gates,
    build_d3_acceptance_payload,
    build_d3_demo_step_sequence,
    build_d3_degraded_state_walkthrough,
    build_d3_empty_state_walkthrough,
    build_d3_playback_inventory,
    build_d3_playback_manifest,
    build_d3_playback_report_payload,
    build_d3_read_only_boundary_checks,
    build_d3_supervisor_runbook,
    build_d3_visibility_walkthrough,
    run_d1_controlled_seed,
    run_d2_dashboard_visibility_certification,
    run_d3_supervisor_playback,
    run_dashboard_o10_closeout_certification,
    build_d1_guardrail_certification,
)


def test_d3_public_api_exports_present():
    inventory = build_d3_playback_inventory()
    assert inventory["schema_version"].startswith("dashboard_d3_")


def test_d3_deterministic_repeated_output_and_checksum_stability():
    payload = build_d1_seed_payload()
    r1 = run_d3_supervisor_playback(payload)
    r2 = run_d3_supervisor_playback(payload)
    assert r1 == r2
    assert r1["manifest_checksum"] == r2["manifest_checksum"]


def test_d3_fixed_ordering():
    stages = build_d3_demo_step_sequence()
    gates = build_d3_acceptance_gates()
    assert len(stages) == 15
    assert stages[0] == "STAGE_01_VERIFY_D1_SEED_MANIFEST"
    assert stages[-1] == "STAGE_15_FINALIZE_SUPERVISOR_ACCEPTANCE_PAYLOAD"
    assert gates[0] == "D1_SEED_MANIFEST_VERIFIED"
    assert gates[-1] == "STABLE_MANIFEST_CHECKSUM_VERIFIED"


def test_d3_pass_degraded_blocked_outcomes():
    good = run_d3_supervisor_playback(build_d1_seed_payload())
    assert good["overall_status"] == "PASS"

    degraded_payload = build_d1_seed_payload()
    degraded_payload["dashboard_entity_facts"][0].pop("sample_data_flag")
    degraded = run_d3_supervisor_playback(degraded_payload)
    assert degraded["overall_status"] == "DEGRADED"

    blocked = run_d3_supervisor_playback(None)
    assert blocked["overall_status"] == "BLOCKED"


def test_d3_inventory_runbook_manifest_and_walkthrough_integrity():
    inv = build_d3_playback_inventory()
    runbook = build_d3_supervisor_runbook()
    manifest = build_d3_playback_manifest()
    vis = build_d3_visibility_walkthrough()
    ro = build_d3_read_only_boundary_checks()
    assert inv["outcome_states"] == ["PASS", "DEGRADED", "BLOCKED"]
    assert len(runbook["observation_checkpoints"]) == 15
    assert manifest["manifest_checksum"]
    assert "replay_metadata_visibility" in vis
    assert ro["mode"] == "read_only"


def test_d3_degraded_empty_and_sample_data_label_verification():
    assert build_d3_degraded_state_walkthrough()["certified"] is True
    assert build_d3_empty_state_walkthrough()["certified"] is True
    payload = build_d1_seed_payload()
    result = run_d3_supervisor_playback(payload)
    assert result["sample_data_label_confirmation"].startswith("all_visible_records")


def test_d3_immutable_input_safety_and_additive_export_behavior():
    payload = build_d1_seed_payload()
    original = deepcopy(payload)
    _ = run_d3_supervisor_playback(payload)
    assert payload == original
    acceptance = build_d3_acceptance_payload(payload)
    report = build_d3_playback_report_payload(payload)
    assert acceptance["decision"] == "APPROVED_FOR_D3_SUPERVISOR_PLAYBACK_CERTIFICATION"
    assert report["final_supervisor_decision"] == "APPROVED_FOR_D3_SUPERVISOR_PLAYBACK_CERTIFICATION"


def test_d1_d1g_d2_o10_smoke():
    d1 = run_d1_controlled_seed(confirm_execute=False, dry_run=True)
    d1g = build_d1_guardrail_certification()
    d2 = run_d2_dashboard_visibility_certification(build_d1_seed_payload())
    o10 = run_dashboard_o10_closeout_certification()
    assert d1["seed_manifest"]["checksum"]
    assert d1g["status"] == "certified"
    assert d2["overall_status"] == "PASS"
    assert "final_decision" in o10
