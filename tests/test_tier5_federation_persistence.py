from transmission_layers.intelligence.tier5.federation_persistence import run_tier5b_federation_persistence
from transmission_layers.intelligence.tier5.federation_engine import run_tier5a_federation


def _history():
    return [
        {"federation_id": "fed-a", "replay_index": 1, "systems": ["a", "b"], "bridges": [["a", "b"]], "boundary_weaknesses": ["bw1"], "contagion_corridors": [["a", "b"]], "bottlenecks": ["b1"], "survivability_dependencies": [["a", "b"]], "recovery_dependencies": [["a", "b"]]},
        {"federation_id": "fed-a", "replay_index": 2, "systems": ["a", "b"], "bridges": [["a", "b"]], "boundary_weaknesses": ["bw1"], "contagion_corridors": [["a", "b"]], "bottlenecks": ["b1"], "survivability_dependencies": [["a", "b"]], "recovery_dependencies": [["a", "b"]]},
    ]


def test_tier5b_outputs_and_stability():
    out1 = run_tier5b_federation_persistence(replay_snapshots=_history())
    out2 = run_tier5b_federation_persistence(replay_snapshots=_history())
    assert out1 == out2
    keys = ["federation_persistence_id","replay_window_size","federation_persistence_score","bounded_federation_persistence_score","bridge_persistence_score","boundary_recurrence_score","contagion_corridor_persistence_score","bottleneck_persistence_score","survivability_dependency_recurrence_score","recovery_dependency_recurrence_score","federation_signature_stability_score","federation_continuity_drift_score","dominant_persistence_factor","federation_persistence_classification","federation_persistence_checksum"]
    for k in keys:
        assert k in out1
    for k, v in out1.items():
        if k.endswith("_score"):
            assert 0.0 <= v <= 1.0


def test_empty_and_disconnected_history():
    out = run_tier5b_federation_persistence(replay_snapshots=[])
    assert out["replay_window_size"] == 0
    dis = run_tier5b_federation_persistence(replay_snapshots=[{"federation_id": "x", "replay_index": 1}, {"federation_id": "x", "replay_index": 2}])
    assert 0.0 <= dis["federation_persistence_score"] <= 1.0


def test_tier5a_compatibility_path():
    res = run_tier5a_federation(systems=[], bridges=[], transmissions=[], contagion_paths=[], dependencies=[])
    assert res["phase"] == "5A"
