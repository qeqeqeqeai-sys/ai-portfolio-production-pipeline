from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.intelligence.tier4.state_snapshot import build_structural_snapshot
from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier4.temporal_replay import compare_snapshots, replay_structural_timeline


def _input(edge_quality=0.95, suppress=False):
    return {
        "quality_scored_edges": [
            {"source_node_id": "A", "target_node_id": "B", "edge_quality_score": edge_quality, "suppressed_for_propagation": suppress},
            {"source_node_id": "B", "target_node_id": "C", "edge_quality_score": edge_quality, "suppressed_for_propagation": suppress},
        ],
        "structural_influence_nodes": [
            {"node_id": "A", "influence_score": 0.9, "contagion_score": 0.9, "chokepoint_score": 0.8, "fragmentation_score": 0.2, "regime_fragility_score": 0.5, "resilience_score": 0.4, "traffic_score": 0.8, "centrality_score": 0.8},
            {"node_id": "B", "influence_score": 0.7, "contagion_score": 0.8, "chokepoint_score": 0.8, "fragmentation_score": 0.2, "regime_fragility_score": 0.5, "resilience_score": 0.4, "traffic_score": 0.8, "centrality_score": 0.8},
            {"node_id": "C", "influence_score": 0.6, "contagion_score": 0.7, "chokepoint_score": 0.5, "fragmentation_score": 0.2, "regime_fragility_score": 0.4, "resilience_score": 0.5, "traffic_score": 0.5, "centrality_score": 0.6},
        ],
    }


def test_compare_snapshots_deterministic_and_bounded():
    s1 = build_structural_snapshot("2026-05-18", run_structural_simulation(_input())).to_dict()
    s2 = build_structural_snapshot("2026-05-19", run_structural_simulation(_input(0.35))).to_dict()
    diff1 = compare_snapshots(s1, s2)
    diff2 = compare_snapshots(s1, s2)
    assert diff1 == diff2
    assert -1.0 <= diff1["resilience_delta"] <= 1.0
    assert -1.0 <= diff1["overload_delta"] <= 1.0


def test_replay_timeline_ordering_recurrence_and_metrics():
    s1 = build_structural_snapshot("2026-05-17", run_structural_simulation(_input(0.95))).to_dict()
    s2 = build_structural_snapshot("2026-05-18", run_structural_simulation(_input(0.20, suppress=True))).to_dict()
    s3 = build_structural_snapshot("2026-05-19", run_structural_simulation(_input(0.20, suppress=True))).to_dict()
    replay = replay_structural_timeline([s3, s1, s2])

    assert replay["ordered_run_dates"] == ["2026-05-17", "2026-05-18", "2026-05-19"]
    assert len(replay["transitions"]) == 2
    for score in replay["temporal_stability_metrics"].values():
        assert 0.0 <= score <= 1.0
    assert replay["operational_diagnostics"]["replay_window_size"] == 3
    assert isinstance(replay["operational_diagnostics"]["replay_checksum"], str)


def test_empty_replay_window_is_stable():
    replay = replay_structural_timeline([])
    assert replay["ordered_run_dates"] == []
    assert replay["transitions"] == []
    assert replay["operational_diagnostics"]["replay_window_size"] == 0
