from copy import deepcopy

from transmission_layers.intelligence.tier5 import (
    run_tier5a_federation,
    run_tier5b_federation_persistence,
    run_tier5c_federation_temporal_evolution,
    run_tier5d_federation_governance,
    run_tier5e_federation_observability,
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


def test_end_to_end_deterministic_and_bounded_and_immutable():
    p=_sample(); frozen=deepcopy(p)
    gov=run_tier5d_federation_governance(**p)
    obs=run_tier5e_federation_observability(**p)
    per=run_tier5b_federation_persistence(replay_snapshots=p["replay_snapshots"])
    evo=run_tier5c_federation_temporal_evolution(replay_snapshots=p["replay_snapshots"])
    a=run_tier5f_federation_structural_health(federation_id="fed", governance=gov, persistence=per, temporal=evo, observability=obs)
    b=run_tier5f_federation_structural_health(federation_id="fed", governance=gov, persistence=per, temporal=evo, observability=obs)
    assert p==frozen
    assert a==b
    for k in ["federation_health_id","federation_structural_health_score","bounded_federation_structural_health_score","diagnostic_readiness_score","observability_alignment_score","governance_alignment_score","replay_health_score","continuity_health_score","propagation_health_score","health_degradation_score","dominant_health_factor","federation_health_classification","federation_health_checksum"]:
        assert k in a
    for k,v in a.items():
        if k.endswith("_score"):
            assert 0<=v<=1


def test_tier5abcde_compatibility():
    p=_sample()
    assert "tier5a_federation_checksum" in run_tier5a_federation(systems=p["systems"],bridges=p["bridges"],transmissions=[],contagion_paths=p["contagion_paths"],dependencies=p["dependencies"])
