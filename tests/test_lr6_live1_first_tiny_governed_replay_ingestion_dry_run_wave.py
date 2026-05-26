from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_live1_append_only_simulation,
    build_lr6_live1_dry_run_context,
    build_lr6_live1_entity_wave_selection,
    build_lr6_live1_governance_gate_review,
    build_lr6_live1_halt_condition_monitor,
    build_lr6_live1_markdown_report,
    build_lr6_live1_payload_preparation,
    build_lr6_live1_replay_window_scope,
    build_lr6_live1_shadow_persistence_simulation,
    build_lr6_live1_supervisor_review,
    build_lr6_live1_wave_summary,
    certify_lr6_live1_dry_run_boundary,
    run_lr6_live1_dry_run_wave,
)


def _entities():
    return [
        {"entity_id": "E1", "cluster": "A", "role": "r1", "metric_dimension": "replay_richness"},
        {"entity_id": "E2", "cluster": "B", "role": "r2", "metric_dimension": "replay_richness"},
        {"entity_id": "E3", "cluster": "A", "role": "r3", "metric_dimension": "replay_richness"},
        {"entity_id": "E4", "cluster": "C", "role": "r1", "metric_dimension": "replay_richness"},
        {"entity_id": "E5", "cluster": "D", "role": "r2", "metric_dimension": "replay_richness"},
        {"entity_id": "E6", "cluster": "E", "role": "r3", "metric_dimension": "weak_signal_attribution"},
    ]


def test_public_apis_exist_and_deterministic_output():
    assert build_lr6_live1_dry_run_context() == build_lr6_live1_dry_run_context()
    assert build_lr6_live1_supervisor_review() == build_lr6_live1_supervisor_review()


def test_wave_bounded_and_replay_richness_only():
    sel = build_lr6_live1_entity_wave_selection(_entities())
    assert sel["entity_count"] <= 5
    assert all(e["metric_dimension"] == "replay_richness" for e in sel["entity_records"])


def test_governance_failure_halts_before_simulation():
    run = run_lr6_live1_dry_run_wave(entities=_entities(), approval_token="BAD")
    assert run["governance_review"]["governance_passed"] is False
    assert run["halt_monitor"]["halt_triggered"] is True
    assert run["halt_monitor"]["halt_reason"] == "governance_failure"


def test_append_only_and_shadow_persistence_simulation_enabled_and_non_persistent():
    run = run_lr6_live1_dry_run_wave(entities=_entities())
    assert run["append_only_simulation"]["append_only_simulation"] is True
    assert run["shadow_persistence_simulation"]["simulated_only"] is True
    assert run["shadow_persistence_simulation"]["persisted"] is False


def test_halt_conditions_and_halt_on_first_behavior_exists():
    run = run_lr6_live1_dry_run_wave(entities=_entities())
    halt = run["halt_monitor"]
    assert "halt_conditions" in halt
    assert len(halt["halt_conditions"]) >= 12


def test_summary_exists_and_dry_run_flags_fixed():
    run = run_lr6_live1_dry_run_wave(entities=_entities())
    summary = run["wave_summary"]
    assert summary["dry_run_only"] is True
    assert summary["persisted"] is False


def test_boundary_flags_exact():
    assert certify_lr6_live1_dry_run_boundary() == {
        "dry_run_only": True,
        "governance_simulation_only": True,
        "append_only_simulation_only": True,
        "shadow_persistence_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "metric_target": "replay_richness",
        "max_entities": 5,
        "all_seven_metrics_implemented": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def test_report_sections_and_forbidden_paths():
    md = build_lr6_live1_markdown_report().lower()
    for section in [
        "## objective",
        "## inspected live0/evid paths",
        "## governance gate review",
        "## tiny-wave selection",
        "## replay window scope",
        "## payload preparation review",
        "## append-only simulation review",
        "## shadow persistence simulation review",
        "## halt-condition review",
        "## dry-run wave summary",
        "## realism warning",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert section in md

    for forbidden in ["insert into", "live ingestion authorized: true", "execution_authorized: true"]:
        assert forbidden not in md
