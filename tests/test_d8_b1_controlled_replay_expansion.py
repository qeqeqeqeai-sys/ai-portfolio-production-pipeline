from transmission_layers.expectation_failure.expectation_intelligence.d8_b1_controlled_replay_expansion import (
    build_d8_b1_controlled_replay_expansion,
    build_d8_b1_replay_reinforcement_diagnostics,
    build_d8_b1_controlled_backfill_plan,
)

def test_d8_b1_scoring_and_dry_run_backfill_default():
    history=[{"run_id":"r1","timestamp":"2026-05-20T00:00:00Z","semantic":{"themes":["t1"]},"contradictions":{"claims":["c1"]},"evidence_highlights":[{"evidence_ref":"EV1"}]},{"run_id":"r2","timestamp":"2026-05-21T00:00:00Z","semantic":{"themes":["t1","t2"]},"contradictions":{"claims":["c1"]},"evidence_highlights":[{"evidence_ref":"EV1"},{"evidence_ref":"EV2"}]}]
    replay=[{"replay_id":"r1"},{"replay_id":"r2"}]
    evidence=[{"evidence_ref":"EV1"},{"evidence_ref":"EV2"}]
    out=build_d8_b1_controlled_replay_expansion(replay_metadata_rows=replay,historical_runs_payloads=history,evidence_maps=evidence,e2_payload={},d8_2_payload={})
    assert out["historical_density_status"] in {"REPLAY_CONTINUITY_MODERATE","REPLAY_CONTINUITY_STRONG"}
    assert out["forbidden_capability_inventory"]["writes"] is False
    reinf=build_d8_b1_replay_reinforcement_diagnostics(historical_runs_payloads=history,e2_payload={},d8_2_payload={})
    assert reinf["reinforcement_counts"]["evidence_refs_recurring"] == 1
    plan=build_d8_b1_controlled_backfill_plan(replay_metadata_rows=replay,historical_runs_payloads=history,governance_inventory={"read_only":True})
    assert plan["dry_run"] is True
    assert plan["execution_status"] == "DRY_RUN_PLANNED"

def test_d8_b1_sparse_history_honest_degradation_and_no_fabrication():
    out=build_d8_b1_controlled_replay_expansion(replay_metadata_rows=[],historical_runs_payloads=[],evidence_maps=[],e2_payload={},d8_2_payload={})
    assert out["historical_density_status"] == "REPLAY_CONTINUITY_BLOCKED"
    assert "historical_run_depth_sparse" in out["continuity_caveats"]
    assert out["lineage_inventory"]["historical_runs"] == 0
