from copy import deepcopy

from transmission_layers.intelligence.tier5 import (
    run_tier5a_federation,
    run_tier5b_federation_persistence,
    run_tier5c_federation_temporal_evolution,
    run_tier5d_federation_governance,
    run_tier5e_federation_observability,
)
from transmission_layers.intelligence.tier5.federation_structural_health import (
    build_federation_health_sort_key,
    run_tier5f_federation_structural_health,
)


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


def test_build_federation_health_sort_key_full_tiebreak_and_deterministic_and_immutable():
    baseline = {
        "federation_structural_health_score": 0.9,
        "diagnostic_readiness_score": 0.8,
        "health_degradation_score": 0.3,
        "observability_alignment_score": 0.7,
        "governance_alignment_score": 0.7,
        "replay_health_score": 0.7,
        "continuity_health_score": 0.7,
        "propagation_health_score": 0.7,
    }
    rows = [
        dict(baseline, federation_health_id="z-base"),
        dict(baseline, federation_health_id="a-lower-degradation", health_degradation_score=0.2),
        dict(baseline, federation_health_id="b-observability", observability_alignment_score=0.8),
        dict(baseline, federation_health_id="c-governance", observability_alignment_score=0.8, governance_alignment_score=0.8),
        dict(baseline, federation_health_id="d-replay", observability_alignment_score=0.8, governance_alignment_score=0.8, replay_health_score=0.8),
        dict(baseline, federation_health_id="e-continuity", observability_alignment_score=0.8, governance_alignment_score=0.8, replay_health_score=0.8, continuity_health_score=0.8),
        dict(baseline, federation_health_id="f-propagation", observability_alignment_score=0.8, governance_alignment_score=0.8, replay_health_score=0.8, continuity_health_score=0.8, propagation_health_score=0.8),
        dict(baseline, federation_health_id="aa-id"),
        dict(baseline, federation_health_id="ab-id"),
    ]
    frozen = deepcopy(rows)
    ordered_once = sorted(rows, key=build_federation_health_sort_key)
    ordered_twice = sorted(rows, key=build_federation_health_sort_key)
    assert rows == frozen
    assert ordered_once == ordered_twice
    assert [r["federation_health_id"] for r in ordered_once] == [
        "a-lower-degradation",
        "f-propagation",
        "e-continuity",
        "d-replay",
        "c-governance",
        "b-observability",
        "aa-id",
        "ab-id",
        "z-base",
    ]
