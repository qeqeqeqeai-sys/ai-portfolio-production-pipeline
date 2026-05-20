from copy import deepcopy

from transmission_layers.intelligence.tier5 import run_tier5a_federation, run_tier5b_federation_persistence, run_tier5c_federation_temporal_evolution, run_tier5d_federation_governance
from transmission_layers.intelligence.tier5.federation_observability import run_tier5e_federation_observability


def sample():
    return dict(
        systems=[{"system_id": "A"}, {"system_id": "B"}],
        bridges=[{"bridge_id":"ab","source":"A","target":"B"}],
        contagion_paths=[{"path_id":"p1","source":"A","target":"B","contained":True}],
        dependencies=[{"source":"A","target":"B"}],
        replay_snapshots=[{"snapshot_id":"1","state":"ok"},{"snapshot_id":"2","state":"ok"}],
    )


def test_required_outputs_and_bounds_and_determinism_and_immutable_inputs():
    payload = sample()
    frozen = deepcopy(payload)
    a = run_tier5e_federation_observability(**payload)
    b = run_tier5e_federation_observability(**payload)
    assert payload == frozen
    assert a == b
    for k in [
        "federation_observability_id","federation_observability_score","bounded_federation_observability_score",
        "federation_visibility_score","federation_lineage_score","federation_traceability_score","federation_telemetry_score",
        "federation_propagation_visibility_score","federation_continuity_observability_score","federation_replay_observability_score",
        "federation_observability_stability_score","federation_visibility_gap_score","dominant_observability_factor",
        "federation_observability_classification","federation_observability_checksum",
    ]:
        assert k in a
    for k,v in a.items():
        if k.endswith("_score"):
            assert 0.0 <= v <= 1.0


def test_tier5abcd_compatibility_smoke():
    p = sample()
    assert isinstance(run_tier5a_federation(systems=p["systems"], bridges=p["bridges"], transmissions=[], contagion_paths=p["contagion_paths"], dependencies=p["dependencies"]), dict)
    assert "federation_persistence_id" in run_tier5b_federation_persistence(replay_snapshots=p["replay_snapshots"])
    assert "federation_evolution_id" in run_tier5c_federation_temporal_evolution(replay_snapshots=p["replay_snapshots"])
    assert "federation_governance_id" in run_tier5d_federation_governance(**p)


def test_ranking_tiebreak_contract():
    rows=[
        {"id":"b","federation_observability_score":0.9,"federation_visibility_gap_score":0.2,"federation_traceability_score":0.8,"federation_lineage_score":0.7,"federation_propagation_visibility_score":0.6,"federation_continuity_observability_score":0.5,"federation_replay_observability_score":0.4},
        {"id":"a","federation_observability_score":0.9,"federation_visibility_gap_score":0.2,"federation_traceability_score":0.8,"federation_lineage_score":0.7,"federation_propagation_visibility_score":0.6,"federation_continuity_observability_score":0.5,"federation_replay_observability_score":0.4},
    ]
    ordered = sorted(rows, key=lambda x: (-x["federation_observability_score"], x["federation_visibility_gap_score"], -x["federation_traceability_score"], -x["federation_lineage_score"], -x["federation_propagation_visibility_score"], -x["federation_continuity_observability_score"], -x["federation_replay_observability_score"], x["id"]))
    assert [x["id"] for x in ordered] == ["a", "b"]


def test_dominant_factor_tie_break_precedence_is_stable():
    p = sample()
    p["contagion_paths"] = [{"path_id":"p1","source":"A","target":"B","contained":False}]
    p["dependencies"] = [{"source":"A","target":"B"}]
    p["replay_snapshots"] = [{"snapshot_id":"1","state":"ok"}]
    r = run_tier5e_federation_observability(**p)
    assert r["federation_lineage_score"] == r["federation_traceability_score"]
    assert r["dominant_observability_factor"] == "federation_traceability_score"
