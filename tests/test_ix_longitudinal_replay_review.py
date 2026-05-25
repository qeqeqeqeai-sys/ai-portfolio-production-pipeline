from scripts.run_ix_longitudinal_replay_review import _extract_runs, _build_review


def test_longitudinal_review_detects_ix_gap_and_governance_boundaries():
    rows = [
        {
            "record_id": "R1",
            "created_at": "2026-05-20T00:00:00Z",
            "payload": {
                "run_id": "run-1",
                "semantic": {"themes": ["fragility", "liquidity"]},
                "contradictions": {"claims": ["macro tension"]},
                "ix1": {"certification": {"status": "CERTIFIED"}},
                "ix2": {"certification": {"status": "CERTIFIED"}},
                "ix3": {"dashboard": {"compression_stability_score": 72}},
                "ix4": {"dashboard": {"interpretability_scorecard": {"average_interpretability_score": 68}}},
            },
            "lineage_refs": ["L1"],
        },
        {
            "record_id": "R2",
            "created_at": "2026-05-21T00:00:00Z",
            "payload": {
                "run_id": "run-2",
                "semantic": {"themes": ["fragility", "transition"]},
                "contradictions": {"claims": ["macro tension", "valuation conflict"]},
                "ix1": {"certification": {"status": "CERTIFIED"}},
                "ix2": {"certification": {"status": "DEGRADED"}},
                "ix3": {"dashboard": {"compression_stability_score": 65}},
                "ix4": {"dashboard": {"interpretability_scorecard": {"average_interpretability_score": 61}}},
                "ix5": {"dashboard": {"continuity_scorecard": {"overall_continuity_score": 59}}},
            },
            "lineage_refs": ["L2"],
        },
    ]
    review = _build_review(_extract_runs(rows))
    assert review["run_count"] == 2
    assert review["governance_boundary_confirmation"]["read_only_review"] is True
    assert review["stress_test_readiness"]["status"] == "NOT_READY_MIN_HISTORY"
    assert review["operational_gap_report"]["ix_persistability_gap"] == "not_detected"
