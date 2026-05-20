from transmission_layers.intelligence.tier5.federation_governance import run_tier5d_federation_governance


def sample():
    return dict(
        systems=[{"system_id": "A"}, {"system_id": "B"}],
        bridges=[{"bridge_id": "ab", "source": "A", "target": "B", "boundary_strength": 0.4, "minimum_boundary_strength": 0.5}],
        contagion_paths=[{"path_id": "p1", "source": "A", "target": "B", "stress": 0.9, "guardrail_limit": 0.8, "contained": False}],
        dependencies=[{"source": "A", "target": "B"}, {"source": "A", "target": "B"}],
        replay_snapshots=[{"snapshot_id": "1", "boundary_weaknesses": ["w1"]}, {"snapshot_id": "2", "boundary_weaknesses": ["w1", "w2"]}],
    )


def test_governance_required_outputs_and_bounds():
    r = run_tier5d_federation_governance(**sample())
    for k in [
        "federation_governance_id","federation_governance_score","bounded_federation_governance_score","federation_constraint_score",
        "federation_guardrail_score","federation_boundary_enforcement_score","federation_violation_score","federation_escalation_score",
        "federation_continuity_constraint_score","governance_containment_effectiveness_score","federation_constraint_recurrence_score",
        "federation_governance_stability_score","dominant_governance_factor","federation_governance_classification","federation_governance_checksum",
    ]:
        assert k in r
    for k, v in r.items():
        if k.endswith("_score"):
            assert 0.0 <= v <= 1.0


def test_governance_determinism():
    a = run_tier5d_federation_governance(**sample())
    b = run_tier5d_federation_governance(**sample())
    assert a == b
