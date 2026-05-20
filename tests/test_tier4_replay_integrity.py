from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.intelligence.tier4.state_snapshot import build_structural_snapshot
from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier4.temporal_replay import replay_structural_timeline
from transmission_layers.intelligence.tier4.topology_hashing import (
    canonical_json_bytes,
    generate_topology_hash,
    normalize_for_hashing,
    normalize_for_replay,
)


def _in(edge=0.4, suppress=False):
    return {
        "quality_scored_edges": [
            {"source_node_id": "A", "target_node_id": "B", "edge_quality_score": edge, "suppressed_for_propagation": suppress},
            {"source_node_id": "C", "target_node_id": "D", "edge_quality_score": edge, "suppressed_for_propagation": suppress},
        ],
        "structural_influence_nodes": [
            {"node_id": "A", "influence_score": 1, "contagion_score": 1, "chokepoint_score": 1, "fragmentation_score": 1, "regime_fragility_score": 1, "resilience_score": 0, "traffic_score": 1, "centrality_score": 1},
            {"node_id": "B", "influence_score": 0, "contagion_score": 0, "chokepoint_score": 0, "fragmentation_score": 0, "regime_fragility_score": 0, "resilience_score": 1, "traffic_score": 0, "centrality_score": 0},
            {"node_id": "C", "influence_score": 0.2, "contagion_score": 0.2, "chokepoint_score": 0.2, "fragmentation_score": 0.2, "regime_fragility_score": 0.2, "resilience_score": 0.8, "traffic_score": 0.2, "centrality_score": 0.2},
            {"node_id": "D", "influence_score": 0.8, "contagion_score": 0.8, "chokepoint_score": 0.8, "fragmentation_score": 0.8, "regime_fragility_score": 0.8, "resilience_score": 0.2, "traffic_score": 0.8, "centrality_score": 0.8},
        ],
    }


def test_byte_stable_replay_and_checksums():
    s1 = build_structural_snapshot("2026-05-18", run_structural_simulation(_in(0.95))).to_dict()
    s2 = build_structural_snapshot("2026-05-19", run_structural_simulation(_in(0.15, True))).to_dict()
    r1 = replay_structural_timeline([s2, s1, s2])
    r2 = replay_structural_timeline([s2, s1, s2])
    assert r1 == r2
    assert canonical_json_bytes(r1) == canonical_json_bytes(r2)
    assert r1["operational_diagnostics"]["replay_checksum"] == r2["operational_diagnostics"]["replay_checksum"]


def test_topology_hash_reproducibility_and_change_detection():
    payload1 = {"simulation_health_state": "mixed", "node_metrics": {"B": {"x": 0.5}, "A": {"x": 0.5}}, "corridor_metrics": {"c2": {"state": "resilient"}, "c1": {"state": "failed"}}, "propagation_summary": {"p": 0.50000000001}}
    payload2 = {"corridor_metrics": {"c1": {"state": "failed"}, "c2": {"state": "resilient"}}, "node_metrics": {"A": {"x": 0.5}, "B": {"x": 0.5}}, "propagation_summary": {"p": 0.5}, "simulation_health_state": "mixed"}
    assert generate_topology_hash(payload1) == generate_topology_hash(payload2)
    payload2["corridor_metrics"]["c2"]["state"] = "failed"
    assert generate_topology_hash(payload1) != generate_topology_hash(payload2)


def test_replay_edge_cases_and_metric_bounds():
    s = build_structural_snapshot("2026-05-19", run_structural_simulation(_in(0.0, True))).to_dict()
    replay = replay_structural_timeline([s, s, dict(s, run_date_sgt="2026-05-18"), dict(s, run_date_sgt="2026-05-18")])
    assert replay["operational_diagnostics"]["replay_window_size"] == 4
    assert replay["operational_diagnostics"]["replay_ordering_stable"] is True
    assert replay["operational_diagnostics"]["topology_hash_sequence"] == [
        s["topology_hash"] for s in sorted([s, s, dict(s, run_date_sgt="2026-05-18"), dict(s, run_date_sgt="2026-05-18")], key=lambda x: (x["run_date_sgt"], x["simulation_run_id"], x["topology_hash"]))
    ]
    for score in replay["temporal_stability_metrics"].values():
        assert 0.0 <= float(score) <= 1.0


def test_normalization_distinguishes_hash_and_replay_semantics():
    shuffled = {
        "nodes": ["N2", "N1"],
        "corridors": [{"id": "c2"}, {"id": "c1"}],
    }
    reordered = {
        "nodes": ["N1", "N2"],
        "corridors": [{"id": "c1"}, {"id": "c2"}],
    }
    assert normalize_for_hashing(shuffled) == normalize_for_hashing(reordered)

    replay_payload = {
        "timeline": ["t2", "t1"],
        "topology_hash_sequence": ["h2", "h1"],
        "newly_failed_corridors": ["c2", "c1", "c2"],
    }
    normalized = normalize_for_replay(replay_payload)
    assert normalized["timeline"] == ["t2", "t1"]
    assert normalized["topology_hash_sequence"] == ["h2", "h1"]
    assert normalized["newly_failed_corridors"] == ["c1", "c2", "c2"]


def test_replay_preserves_topology_hash_and_transition_order():
    s1 = build_structural_snapshot("2026-05-18", run_structural_simulation(_in(0.95))).to_dict()
    s2 = build_structural_snapshot("2026-05-19", run_structural_simulation(_in(0.15, True))).to_dict()
    s3 = build_structural_snapshot("2026-05-20", run_structural_simulation(_in(0.95))).to_dict()
    replay = replay_structural_timeline([s3, s1, s2])
    ordered = sorted([s1, s2, s3], key=lambda s: (s["run_date_sgt"], s["simulation_run_id"], s["topology_hash"]))
    assert replay["operational_diagnostics"]["topology_hash_sequence"] == [s["topology_hash"] for s in ordered]
    assert [t["from"] for t in replay["transitions"]] == [ordered[0]["run_date_sgt"], ordered[1]["run_date_sgt"]]
