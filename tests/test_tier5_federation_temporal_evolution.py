from copy import deepcopy

from transmission_layers.intelligence.tier5.federation_temporal_evolution import run_tier5c_federation_temporal_evolution


def _snapshots():
    return [
        {"federation_id": "fed-a", "replay_index": 2, "systems": ["b", "a"], "bridges": [("a", "b")], "boundary_weaknesses": ["bw1"], "contagion_corridors": [("a", "b")], "bottlenecks": ["bn1"], "survivability_dependencies": [("a", "b")], "recovery_dependencies": [("b", "a")]},
        {"federation_id": "fed-a", "replay_index": 1, "systems": ["a"], "bridges": [], "boundary_weaknesses": [], "contagion_corridors": [], "bottlenecks": [], "survivability_dependencies": [], "recovery_dependencies": []},
    ]


def test_temporal_evolution_outputs_and_bounds_and_determinism():
    snaps = _snapshots()
    before = deepcopy(snaps)
    one = run_tier5c_federation_temporal_evolution(replay_snapshots=snaps)
    two = run_tier5c_federation_temporal_evolution(replay_snapshots=list(reversed(snaps)))
    assert one == two
    assert snaps == before
    for k, v in one.items():
        if k.endswith("_score"):
            assert 0.0 <= v <= 1.0
    assert one["replay_window_count"] == 2
    assert one["federation_evolution_checksum"].startswith("tier5c_chk_")


def test_temporal_evolution_empty_and_single():
    empty = run_tier5c_federation_temporal_evolution(replay_snapshots=[])
    single = run_tier5c_federation_temporal_evolution(replay_snapshots=[{"federation_id": "x"}])
    assert empty["replay_window_count"] == 0
    assert single["replay_window_count"] == 1
