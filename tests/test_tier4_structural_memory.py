from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.intelligence.tier4.structural_memory import StructuralMemoryStore
from transmission_layers.intelligence.tier4.state_snapshot import build_structural_snapshot
from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier4.topology_hashing import generate_topology_hash


def _input(q=0.95):
    return {
        "quality_scored_edges": [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": q, "suppressed_for_propagation": False}],
        "structural_influence_nodes": [
            {"node_id": "A", "influence_score": 0.9, "contagion_score": 0.9, "chokepoint_score": 0.8, "fragmentation_score": 0.2, "regime_fragility_score": 0.5, "resilience_score": 0.4, "traffic_score": 0.8, "centrality_score": 0.8},
            {"node_id": "B", "influence_score": 0.6, "contagion_score": 0.6, "chokepoint_score": 0.5, "fragmentation_score": 0.2, "regime_fragility_score": 0.4, "resilience_score": 0.5, "traffic_score": 0.5, "centrality_score": 0.6},
        ],
    }


def test_snapshot_serialization_and_hash_stability():
    snap = build_structural_snapshot("2026-05-18", run_structural_simulation(_input()))
    d1 = snap.to_dict()
    d2 = json.loads(json.dumps(d1, sort_keys=True))
    assert d1 == d2
    assert generate_topology_hash(d1) == generate_topology_hash(d2)


def test_memory_indexing_retrieval_is_deterministic():
    store = StructuralMemoryStore()
    s1 = build_structural_snapshot("2026-05-18", run_structural_simulation(_input())).to_dict()
    s2 = build_structural_snapshot("2026-05-19", run_structural_simulation(_input(0.3))).to_dict()
    store.add_snapshot(s2)
    store.add_snapshot(s1)
    ordered = store.all_snapshots()
    assert [s["run_date_sgt"] for s in ordered] == ["2026-05-18", "2026-05-19"]
    assert store.query(run_date="2026-05-18")[0]["run_date_sgt"] == "2026-05-18"
    assert store.query(topology_hash=s1["topology_hash"])
