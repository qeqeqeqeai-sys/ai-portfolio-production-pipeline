import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.intelligence.tier4.structural_simulation import (
    classify_simulation_health_state,
    compute_amplification_effects,
    run_structural_simulation,
)


def _base_input():
    return {
        "quality_scored_edges": [
            {"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.95, "suppressed_for_propagation": False},
            {"source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.90, "suppressed_for_propagation": False},
        ],
        "structural_influence_nodes": [
            {"node_id": "A", "influence_score": 0.9, "contagion_score": 0.9, "chokepoint_score": 0.8, "fragmentation_score": 0.2, "regime_fragility_score": 0.5, "resilience_score": 0.4, "traffic_score": 0.8, "centrality_score": 0.8},
            {"node_id": "B", "influence_score": 0.7, "contagion_score": 0.8, "chokepoint_score": 0.8, "fragmentation_score": 0.2, "regime_fragility_score": 0.5, "resilience_score": 0.4, "traffic_score": 0.8, "centrality_score": 0.8},
            {"node_id": "C", "influence_score": 0.6, "contagion_score": 0.7, "chokepoint_score": 0.5, "fragmentation_score": 0.2, "regime_fragility_score": 0.4, "resilience_score": 0.5, "traffic_score": 0.5, "centrality_score": 0.6},
        ],
    }


def test_deterministic_output_and_bounded_scores():
    r1 = run_structural_simulation(_base_input())
    r2 = run_structural_simulation(_base_input())
    assert r1 == r2
    for k, v in r1.items():
        if k.endswith("_score"):
            assert 0.0 <= v <= 1.0


def test_propagation_increases_along_high_quality_paths():
    hi = _base_input()
    lo = _base_input()
    lo["quality_scored_edges"][0]["edge_quality_score"] = 0.2
    assert run_structural_simulation(hi)["propagated_stress_score"] > run_structural_simulation(lo)["propagated_stress_score"]


def test_amplification_rises_with_contagion_hubs():
    low_nodes = _base_input()["structural_influence_nodes"]
    high_nodes = [dict(n, contagion_score=0.95) for n in low_nodes]
    assert compute_amplification_effects(high_nodes) > compute_amplification_effects(low_nodes)


def test_chokepoint_overload_and_suppression_and_resilience_and_corridor_failure_detection():
    inp = _base_input()
    inp["quality_scored_edges"].append({"source_node_id": "C", "target_node_id": "D", "edge_quality_score": 0.3, "suppressed_for_propagation": True})
    inp["structural_influence_nodes"].append({"node_id": "D", "influence_score": 0.4, "contagion_score": 0.6, "chokepoint_score": 0.9, "fragmentation_score": 0.8, "regime_fragility_score": 0.8, "resilience_score": 0.2, "traffic_score": 0.9, "centrality_score": 0.9})
    r = run_structural_simulation(inp)
    assert r["chokepoint_overload_score"] > 0.0
    assert r["suppression_cascade_score"] > 0.0
    assert r["resilience_degradation_score"] > 0.0
    assert r["suppressed_corridors"]


def test_health_classifications():
    assert classify_simulation_health_state(0.80, 0.80, 0.80, 0.80, 4) == "cascading_failure"
    assert classify_simulation_health_state(0.60, 0.40, 0.40, 0.60, 3) == "fragile"
    assert classify_simulation_health_state(0.63, 0.40, 0.40, 0.40, 3) == "overloaded"
    assert classify_simulation_health_state(0.40, 0.51, 0.30, 0.30, 3) == "stressed"
    assert classify_simulation_health_state(0.20, 0.20, 0.20, 0.20, 1) == "contained"
    assert classify_simulation_health_state(0.40, 0.40, 0.40, 0.41, 3) == "mixed"


def test_explainability_payload_exists_and_complete_keys():
    r = run_structural_simulation(_base_input())
    payload = r["explainability_payload"]
    for k in ["simulation_rationale_strings", "propagation_explanations", "amplification_explanations", "chokepoint_explanations", "suppression_explanations", "resilience_explanations", "corridor_failure_explanations", "warnings", "dominant_simulation_drivers"]:
        assert k in payload


def test_cli_writes_summary_json():
    subprocess.run([sys.executable, "-m", "transmission_layers.intelligence.tier4.structural_simulation"], check=True)
    summary_path = Path("logs/tier4_structural_simulation_summary.json")
    assert summary_path.exists()
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["tier"] == "4"
    assert data["phase"] == "4A"


def test_no_tier3h5_governance_dependency():
    source = Path("transmission_layers/intelligence/tier4/structural_simulation.py").read_text(encoding="utf-8").lower()
    assert "tier3h5" not in source
    assert "governance" not in source
