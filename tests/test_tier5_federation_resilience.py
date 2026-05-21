from copy import deepcopy

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
