from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier5.federation_common import clamp_score, weighted_bounded_score
from transmission_layers.intelligence.tier5.federation_engine import run_tier5a_federation


def _fixture():
    return dict(
        systems=[{"id": "A"}, {"id": "B"}, {"id": "C"}],
        bridges=[
            {"from": "A", "to": "B", "redundancy": 0.8, "stability": 0.7, "boundary_hardening": 0.9, "breach_exposure": 0.2},
            {"from": "B", "to": "C", "redundancy": 0.6, "stability": 0.8, "boundary_hardening": 0.85, "breach_exposure": 0.1},
        ],
        transmissions=[
            {"throughput": 0.7, "integrity": 0.9, "latency_penalty": 0.2},
            {"throughput": 0.8, "integrity": 0.85, "latency_penalty": 0.1},
        ],
        contagion_paths=[
            {"contagion_risk": 0.5, "bottleneck_risk": 0.6, "containment": 0.7},
            {"contagion_risk": 0.4, "bottleneck_risk": 0.5, "containment": 0.8},
        ],
        dependencies=[
            {"survivability": 0.75, "recovery_readiness": 0.7, "dependency_fragility": 0.3},
            {"survivability": 0.8, "recovery_readiness": 0.65, "dependency_fragility": 0.25},
        ],
    )


def test_bounded_helpers():
    assert clamp_score(-1) == 0.0
    assert clamp_score(2) == 1.0
    assert 0.0 <= weighted_bounded_score([(2, 1), (-1, 1)]) <= 1.0


def test_tier5a_deterministic_and_bounded():
    payload = _fixture()
    r1 = run_tier5a_federation(**payload)
    r2 = run_tier5a_federation(**payload)
    assert r1 == r2
    for k, v in r1.items():
        if k.endswith("_score"):
            assert 0.0 <= v <= 1.0


def test_tier4_smoke_output_preserved():
    result = run_structural_simulation()
    line = f"[tier4] simulation_health_state={result['simulation_health_state']} propagated_stress={result['propagated_stress_score']:.4f} overload={result['chokepoint_overload_score']:.4f} resilience={result['resilience_degradation_score']:.4f} status=success"
    assert line == "[tier4] simulation_health_state=stressed propagated_stress=0.5854 overload=0.5953 resilience=0.5371 status=success"
