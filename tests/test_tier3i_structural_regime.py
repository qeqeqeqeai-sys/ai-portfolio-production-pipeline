import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import subprocess

from transmission_layers.intelligence.tier3i.structural_regime import compute_structural_regime


def _base_inputs():
    return {
        "quality_scored_edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.85, "confidence_band": "high"},
            {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.75, "confidence_band": "high"},
            {"source_node_id": "c", "target_node_id": "d", "edge_quality_score": 0.70, "confidence_band": "medium"},
        ],
        "structural_influence_nodes": [
            {"node_id": "a", "structural_influence_score": 0.50},
            {"node_id": "b", "structural_influence_score": 0.45},
            {"node_id": "c", "structural_influence_score": 0.40},
            {"node_id": "d", "structural_influence_score": 0.35},
        ],
        "multi_hop_paths": [
            {"path_id": "p1", "path_quality_score": 0.82, "reinforcement_score": 0.15, "contamination_warning": False},
            {"path_id": "p2", "path_quality_score": 0.74, "reinforcement_score": 0.10, "contamination_warning": False},
        ],
        "path_explanations": [{"path_id": "p1", "decision_usefulness_label": "actionable_watchlist"}],
        "transmission_intelligence_summary": {"average_reinforcement_score": 0.125},
    }


def test_deterministic_regime_classification():
    inputs = _base_inputs()
    assert compute_structural_regime(**inputs) == compute_structural_regime(**inputs)


def test_bounded_scores():
    out = compute_structural_regime(**_base_inputs())
    score_fields = [
        "graph_concentration_score",
        "top_node_dominance_ratio",
        "influence_entropy",
        "fragmentation_score",
        "weak_link_ratio",
        "overheating_score",
        "reinforcement_acceleration",
        "high_quality_path_density",
        "contagion_pressure",
        "propagation_density_score",
        "structural_fragility_score",
        "structural_stability_score",
    ]
    for field in score_fields:
        assert 0.0 <= out[field] <= 1.0


def test_concentration_increases_under_dominance():
    base = _base_inputs()
    dominated = _base_inputs()
    dominated["structural_influence_nodes"] = [
        {"node_id": "a", "structural_influence_score": 0.95},
        {"node_id": "b", "structural_influence_score": 0.10},
        {"node_id": "c", "structural_influence_score": 0.10},
        {"node_id": "d", "structural_influence_score": 0.10},
    ]
    assert compute_structural_regime(**dominated)["graph_concentration_score"] > compute_structural_regime(**base)[
        "graph_concentration_score"
    ]


def test_fragmentation_rises_with_weak_disconnected_structures():
    base = _base_inputs()
    fragmented = _base_inputs()
    fragmented["quality_scored_edges"] = [
        {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.2, "confidence_band": "low", "suppressed_for_propagation": True},
        {"source_node_id": "c", "target_node_id": "d", "edge_quality_score": 0.2, "confidence_band": "low", "suppressed_for_propagation": True},
    ]
    fragmented["multi_hop_paths"] = [{"path_id": "p", "path_quality_score": 0.2, "suppressed_for_propagation": True}]
    assert compute_structural_regime(**fragmented)["fragmentation_score"] > compute_structural_regime(**base)[
        "fragmentation_score"
    ]


def test_overheating_rises_with_reinforcement_concentration():
    base = _base_inputs()
    hot = _base_inputs()
    hot["transmission_intelligence_summary"] = {"average_reinforcement_score": 0.95}
    hot["multi_hop_paths"] = [
        {"path_id": "p1", "path_quality_score": 0.95, "reinforcement_score": 0.95, "contamination_warning": True},
        {"path_id": "p2", "path_quality_score": 0.90, "reinforcement_score": 0.90, "contamination_warning": True},
    ]
    hot["structural_influence_nodes"] = [
        {"node_id": "a", "structural_influence_score": 0.99},
        {"node_id": "b", "structural_influence_score": 0.05},
    ]
    assert compute_structural_regime(**hot)["overheating_score"] > compute_structural_regime(**base)["overheating_score"]


def test_fragility_rises_with_suppression_and_contamination():
    base = _base_inputs()
    fr = _base_inputs()
    fr["quality_scored_edges"] = [
        {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.2, "suppressed_for_propagation": True},
        {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.2, "suppressed_for_propagation": True},
    ]
    fr["multi_hop_paths"] = [
        {"path_id": "p1", "path_quality_score": 0.3, "contamination_warning": True, "suppressed_for_propagation": True}
    ]
    assert compute_structural_regime(**fr)["structural_fragility_score"] > compute_structural_regime(**base)[
        "structural_fragility_score"
    ]


def test_stable_regime_classification():
    out = compute_structural_regime(**_base_inputs())
    assert out["regime_state"] == "stable"


def test_fragmented_regime_classification():
    data = _base_inputs()
    data["quality_scored_edges"] = [
        {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.1, "confidence_band": "low", "suppressed_for_propagation": True},
        {"source_node_id": "c", "target_node_id": "d", "edge_quality_score": 0.1, "confidence_band": "low", "suppressed_for_propagation": True},
        {"source_node_id": "e", "target_node_id": "f", "edge_quality_score": 0.1, "confidence_band": "low", "suppressed_for_propagation": True},
    ]
    data["multi_hop_paths"] = [{"path_id": "p", "path_quality_score": 0.1, "suppressed_for_propagation": True}]
    assert compute_structural_regime(**data)["regime_state"] == "fragmented"


def test_overheated_regime_classification():
    data = _base_inputs()
    data["structural_influence_nodes"] = [
        {"node_id": "a", "structural_influence_score": 1.0},
        {"node_id": "b", "structural_influence_score": 0.01},
    ]
    data["transmission_intelligence_summary"] = {"average_reinforcement_score": 1.0}
    data["multi_hop_paths"] = [
        {"path_id": "p1", "path_quality_score": 0.95, "reinforcement_score": 0.95, "contamination_warning": True},
        {"path_id": "p2", "path_quality_score": 0.92, "reinforcement_score": 0.92, "contamination_warning": True},
    ]
    assert compute_structural_regime(**data)["regime_state"] == "overheated"


def test_transitioning_regime_classification():
    data = _base_inputs()
    data["quality_scored_edges"] = [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.45}]
    data["multi_hop_paths"] = [{"path_id": "p", "path_quality_score": 0.50, "reinforcement_score": 0.50}]
    data["transmission_intelligence_summary"] = {"average_reinforcement_score": 0.50}
    out = compute_structural_regime(**data)
    assert out["regime_state"] == "transitioning"


def test_explainability_payload_exists():
    out = compute_structural_regime(**_base_inputs())
    payload = out["explainability_payload"]
    for key in [
        "regime_rationale",
        "key_contributing_metrics",
        "warnings",
        "dominant_structural_drivers",
        "concentration_explanation",
        "fragility_explanation",
        "overheating_explanation",
        "connectivity_explanation",
    ]:
        assert key in payload


def test_cli_writes_summary_json():
    output = Path("logs/tier3i_structural_regime_summary.json")
    if output.exists():
        output.unlink()
    subprocess.run([sys.executable, "-m", "transmission_layers.intelligence.tier3i.structural_regime"], check=True)
    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["phase"] == "3A"
    assert data["status"] == "success"


def test_no_tier3h5_governance_dependency():
    source = Path("transmission_layers/intelligence/tier3i/structural_regime.py").read_text(encoding="utf-8").lower()
    assert "tier3h5" not in source
    assert "governance" not in source
