from copy import deepcopy
from dataclasses import dataclass

from transmission_layers.intelligence.tier5 import (
    run_tier5b_federation_persistence,
    run_tier5c_federation_temporal_evolution,
    run_tier5d_federation_governance,
    run_tier5e_federation_observability,
)
from transmission_layers.intelligence.tier5.federation_resilience import (
    build_federation_resilience_sort_key,
    run_tier5g_federation_resilience,
)
from transmission_layers.intelligence.tier5.federation_structural_health import run_tier5f_federation_structural_health


def _sample():
    return dict(
        systems=[{"system_id":"A"},{"system_id":"B"}],
        bridges=[{"bridge_id":"ab","source":"A","target":"B"}],
        contagion_paths=[{"path_id":"p","source":"A","target":"B","contained":True}],
        dependencies=[{"source":"A","target":"B"}],
        replay_snapshots=[{"snapshot_id":"1","state":"ok"},{"snapshot_id":"2","state":"degraded"}],
    )


def test_tier5g_end_to_end_and_immutable_and_bounded():
    p=_sample();f=deepcopy(p)
    gov=run_tier5d_federation_governance(**p)
    obs=run_tier5e_federation_observability(**p)
    per=run_tier5b_federation_persistence(replay_snapshots=p["replay_snapshots"])
    evo=run_tier5c_federation_temporal_evolution(replay_snapshots=p["replay_snapshots"])
    health=run_tier5f_federation_structural_health(federation_id="fed", governance=gov, persistence=per, temporal=evo, observability=obs)
    a=run_tier5g_federation_resilience(federation_id="fed", governance=gov, persistence=per, temporal=evo, observability=obs, health=health, dependencies=p["dependencies"], contagion_paths=p["contagion_paths"], replay_snapshots=p["replay_snapshots"])
    b=run_tier5g_federation_resilience(federation_id="fed", governance=gov, persistence=per, temporal=evo, observability=obs, health=health, dependencies=p["dependencies"], contagion_paths=p["contagion_paths"], replay_snapshots=p["replay_snapshots"])
    assert p==f
    assert a==b
    for k,v in a.items():
        if k.endswith("_score"):
            assert 0<=v<=1


def test_sort_key_tiebreak_ordering():
    rows=[
        {"federation_resilience_id":"b","federation_resilience_score":0.9,"federation_recovery_readiness_score":0.7,"federation_recoverability_score":0.7,"federation_dependency_resilience_score":0.7,"federation_failure_containment_score":0.7,"federation_recovery_path_score":0.7,"federation_irreversibility_risk_score":0.2,"federation_recovery_gap_score":0.3},
        {"federation_resilience_id":"a","federation_resilience_score":0.9,"federation_recovery_readiness_score":0.8,"federation_recoverability_score":0.7,"federation_dependency_resilience_score":0.7,"federation_failure_containment_score":0.7,"federation_recovery_path_score":0.7,"federation_irreversibility_risk_score":0.2,"federation_recovery_gap_score":0.3},
    ]
    assert [r["federation_resilience_id"] for r in sorted(rows,key=build_federation_resilience_sort_key)]==["a","b"]


@dataclass
class _ResilienceRecord:
    federation_health_id: str
    federation_resilience_score: float
    federation_recovery_readiness_score: float
    federation_recoverability_score: float
    federation_dependency_resilience_score: float
    federation_failure_containment_score: float
    federation_recovery_path_score: float
    federation_irreversibility_risk_score: float
    federation_recovery_gap_score: float


def test_build_federation_resilience_sort_key_full_tiebreak_and_deterministic_and_immutable():
    baseline = {
        "federation_resilience_score": 0.5,
        "federation_recovery_readiness_score": 0.5,
        "federation_recoverability_score": 0.5,
        "federation_dependency_resilience_score": 0.5,
        "federation_failure_containment_score": 0.5,
        "federation_recovery_path_score": 0.5,
        "federation_irreversibility_risk_score": 0.5,
        "federation_recovery_gap_score": 0.5,
    }
    rows = [
        {**baseline, "federation_resilience_id": "a_step1_win", "federation_resilience_score": 0.52},
        {**baseline, "federation_resilience_id": "z_step1_lose", "federation_resilience_score": 0.51},
        {**baseline, "federation_resilience_id": "a_step2_win", "federation_recovery_readiness_score": 0.52},
        {**baseline, "federation_resilience_id": "z_step2_lose", "federation_recovery_readiness_score": 0.51},
        {**baseline, "federation_resilience_id": "a_step3_win", "federation_recoverability_score": 0.52},
        {**baseline, "federation_resilience_id": "z_step3_lose", "federation_recoverability_score": 0.51},
        {**baseline, "federation_resilience_id": "a_step4_win", "federation_dependency_resilience_score": 0.52},
        {**baseline, "federation_resilience_id": "z_step4_lose", "federation_dependency_resilience_score": 0.51},
        {**baseline, "federation_resilience_id": "a_step5_win", "federation_failure_containment_score": 0.52},
        {**baseline, "federation_resilience_id": "z_step5_lose", "federation_failure_containment_score": 0.51},
        {**baseline, "federation_resilience_id": "a_step6_win", "federation_recovery_path_score": 0.52},
        {**baseline, "federation_resilience_id": "z_step6_lose", "federation_recovery_path_score": 0.51},
        {**baseline, "federation_resilience_id": "a_step7_win", "federation_irreversibility_risk_score": 0.49},
        {**baseline, "federation_resilience_id": "z_step7_lose", "federation_irreversibility_risk_score": 0.51},
        {**baseline, "federation_resilience_id": "a_step8_win", "federation_recovery_gap_score": 0.49},
        {**baseline, "federation_resilience_id": "z_step8_lose", "federation_recovery_gap_score": 0.51},
        {**baseline, "federation_resilience_id": "a_step9a"},
        {**baseline, "federation_resilience_id": "a_step9b"},
        _ResilienceRecord("a_health_object", 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
        {**baseline, "id": "z_id_fallback"},
    ]
    before = deepcopy(rows)

    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[:2], key=build_federation_resilience_sort_key)] == ["a_step1_win", "z_step1_lose"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[2:4], key=build_federation_resilience_sort_key)] == ["a_step2_win", "z_step2_lose"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[4:6], key=build_federation_resilience_sort_key)] == ["a_step3_win", "z_step3_lose"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[6:8], key=build_federation_resilience_sort_key)] == ["a_step4_win", "z_step4_lose"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[8:10], key=build_federation_resilience_sort_key)] == ["a_step5_win", "z_step5_lose"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[10:12], key=build_federation_resilience_sort_key)] == ["a_step6_win", "z_step6_lose"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[12:14], key=build_federation_resilience_sort_key)] == ["a_step7_win", "z_step7_lose"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[14:16], key=build_federation_resilience_sort_key)] == ["a_step8_win", "z_step8_lose"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[16:18], key=build_federation_resilience_sort_key)] == ["a_step9a", "a_step9b"]
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted(rows[18:], key=build_federation_resilience_sort_key)] == ["a_health_object", "z_id_fallback"]

    ordered = sorted(rows, key=build_federation_resilience_sort_key)
    ordered_ids = [build_federation_resilience_sort_key(r)[-1] for r in ordered]

    low_risk = {**baseline, "federation_resilience_id": "low_risk", "federation_irreversibility_risk_score": 0.1}
    high_risk = {**baseline, "federation_resilience_id": "high_risk", "federation_irreversibility_risk_score": 0.9}
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted([high_risk, low_risk], key=build_federation_resilience_sort_key)] == ["low_risk", "high_risk"]

    low_gap = {**baseline, "federation_resilience_id": "low_gap", "federation_recovery_gap_score": 0.1}
    high_gap = {**baseline, "federation_resilience_id": "high_gap", "federation_recovery_gap_score": 0.9}
    assert [build_federation_resilience_sort_key(r)[-1] for r in sorted([high_gap, low_gap], key=build_federation_resilience_sort_key)] == ["low_gap", "high_gap"]

    expected = ordered_ids
    for _ in range(7):
        repeated = sorted(deepcopy(rows), key=build_federation_resilience_sort_key)
        assert [build_federation_resilience_sort_key(r)[-1] for r in repeated] == expected

    assert rows == before
