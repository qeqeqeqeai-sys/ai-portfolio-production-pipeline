from transmission_layers.expectation_failure.expectation_intelligence.d8_b2_backfill_readback_verification import compare_d8_b2_backfill_readback


def _row(run_id: str, evidence=None, themes=None, contradictions=None, lineage=None):
    return {
        "record_id": f"rec-{run_id}",
        "replay_id": run_id,
        "lineage_refs": lineage or [],
        "payload": {
            "run_id": run_id,
            "semantic": {"themes": themes or []},
            "contradictions": {"claims": contradictions or []},
            "evidence_highlights": evidence or [],
        },
    }


def test_deterministic_comparison_metrics_and_deltas():
    before = [_row("r1", evidence=[{"evidence_ref": "E1"}], themes=["t1"], contradictions=["c1"], lineage=["L1"])]
    after = before + [_row("r2", evidence=[{"evidence_ref": "E2", "supporting_evidence_refs": ["E1"]}], themes=["t2"], contradictions=["c2"], lineage=["L2", "L3"])]
    out1 = compare_d8_b2_backfill_readback(before_rows=before, after_rows=after, dry_run=True)
    out2 = compare_d8_b2_backfill_readback(before_rows=before, after_rows=after, dry_run=True)
    assert out1 == out2
    assert out1["deltas"]["replay_continuity_score_delta"] > 0
    assert out1["deltas"]["evidence_reinforcement_score_delta"] > 0


def test_no_write_governance_blocked_when_non_dry_run():
    out = compare_d8_b2_backfill_readback(before_rows=[], after_rows=[], dry_run=False)
    assert out["status"] == "BLOCKED_NON_DRY_RUN"
    assert out["no_write_governance"] is False


def test_sparse_history_degradation_and_duplicate_replay_handling():
    out = compare_d8_b2_backfill_readback(before_rows=[_row("r1")], after_rows=[_row("r1"), _row("r1")], dry_run=True)
    assert out["sparse_history"] is True
    assert out["duplicate_replay_ids_detected"] is True


def test_semantic_and_contradiction_and_reinforcement_delta_computations():
    before = [_row("r1", evidence=[{"evidence_ref": "E1"}], themes=["t1"], contradictions=["c1"]) ]
    after = before + [_row("r2", evidence=[{"evidence_ref": "E2"}], themes=["t2", "t3"], contradictions=["c2", "c3"]) ]
    out = compare_d8_b2_backfill_readback(before_rows=before, after_rows=after, dry_run=True)
    assert out["deltas"]["semantic_persistence_count_delta"] == 2.0
    assert out["deltas"]["contradiction_continuity_count_delta"] == 2.0
    assert out["deltas"]["evidence_reinforcement_score_delta"] > 0
