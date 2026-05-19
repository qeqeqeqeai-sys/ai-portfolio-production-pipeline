import json
import subprocess
import sys
from pathlib import Path

from transmission_layers.intelligence.tier3i.contagion_mapping import map_structural_contagion


def _inputs(**overrides):
    base = {
        "quality_scored_edges": [
            {"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.8},
            {"source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.7},
            {"source_node_id": "C", "target_node_id": "D", "edge_quality_score": 0.4},
        ],
        "structural_influence_nodes": [
            {"node_id": "A", "structural_influence_score": 0.9},
            {"node_id": "B", "structural_influence_score": 0.8},
            {"node_id": "C", "structural_influence_score": 0.5},
            {"node_id": "D", "structural_influence_score": 0.3},
        ],
        "multi_hop_paths": [
            {"path_id": "p1", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.82, "reinforcement_score": 0.12, "suppressed_for_propagation": False, "contamination_warning": False},
            {"path_id": "p2", "path_nodes": ["A", "B", "D"], "path_quality_score": 0.75, "reinforcement_score": 0.10, "suppressed_for_propagation": False, "contamination_warning": False},
            {"path_id": "p3", "path_nodes": ["C", "D"], "path_quality_score": 0.35, "reinforcement_score": 0.02, "suppressed_for_propagation": True, "contamination_warning": True},
        ],
        "path_explanations": [],
        "structural_regime_summary": {"regime_state": "transitioning"},
        "regime_drift_summary": {"drift_direction": "mixed"},
    }
    base.update(overrides)
    return base


def _run(**kwargs):
    i = _inputs(**kwargs)
    return map_structural_contagion(**i)


def test_deterministic_contagion_output():
    out1 = _run()
    out2 = _run()
    assert out1 == out2


def test_bounded_scores():
    out = _run()
    keys = [
        "contagion_pressure_score",
        "amplification_score",
        "chokepoint_score",
        "corridor_density_score",
        "suppression_bottleneck_score",
        "contamination_spread_score",
        "hub_concentration_score",
        "contagion_fragility_score",
        "contagion_resilience_score",
    ]
    assert all(0.0 <= out[k] <= 1.0 for k in keys)


def test_pressure_rises_with_high_quality_dense_paths():
    low = _run(multi_hop_paths=[{"path_id": "x", "path_nodes": ["A", "D"], "path_quality_score": 0.30, "reinforcement_score": 0.01}])
    high = _run(multi_hop_paths=[
        {"path_id": "x1", "path_nodes": ["A", "B"], "path_quality_score": 0.90, "reinforcement_score": 0.12},
        {"path_id": "x2", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.85, "reinforcement_score": 0.12},
        {"path_id": "x3", "path_nodes": ["B", "C", "D"], "path_quality_score": 0.80, "reinforcement_score": 0.11},
    ])
    assert high["contagion_pressure_score"] > low["contagion_pressure_score"]


def test_amplification_rises_when_high_influence_nodes_dominate_strong_paths():
    low = _run(multi_hop_paths=[{"path_id": "l1", "path_nodes": ["C", "D"], "path_quality_score": 0.40, "reinforcement_score": 0.01}])
    high = _run(multi_hop_paths=[
        {"path_id": "h1", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.86, "reinforcement_score": 0.13},
        {"path_id": "h2", "path_nodes": ["A", "B", "D"], "path_quality_score": 0.84, "reinforcement_score": 0.13},
        {"path_id": "h3", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.82, "reinforcement_score": 0.12},
    ])
    assert high["amplification_score"] > low["amplification_score"]


def test_chokepoint_score_rises_when_node_appears_across_many_paths():
    low = _run(multi_hop_paths=[
        {"path_id": "l1", "path_nodes": ["A", "B"], "path_quality_score": 0.8},
        {"path_id": "l2", "path_nodes": ["C", "D"], "path_quality_score": 0.7},
    ])
    high = _run(multi_hop_paths=[
        {"path_id": "h1", "path_nodes": ["B", "A"], "path_quality_score": 0.8},
        {"path_id": "h2", "path_nodes": ["B", "C"], "path_quality_score": 0.8},
        {"path_id": "h3", "path_nodes": ["B", "D"], "path_quality_score": 0.4, "suppressed_for_propagation": True},
    ])
    assert high["chokepoint_score"] > low["chokepoint_score"]


def test_suppression_bottleneck_rises_with_clustered_suppressed_paths():
    low = _run(multi_hop_paths=[{"path_id": "l1", "path_nodes": ["A", "C"], "path_quality_score": 0.7, "suppressed_for_propagation": False}])
    high = _run(multi_hop_paths=[
        {"path_id": "h1", "path_nodes": ["B", "A"], "path_quality_score": 0.3, "suppressed_for_propagation": True},
        {"path_id": "h2", "path_nodes": ["B", "C"], "path_quality_score": 0.2, "suppressed_for_propagation": True},
    ])
    assert high["suppression_bottleneck_score"] > low["suppression_bottleneck_score"]


def test_contamination_spread_rises_with_overlapping_contaminated_paths():
    low = _run(multi_hop_paths=[{"path_id": "l1", "path_nodes": ["A", "D"], "path_quality_score": 0.4, "contamination_warning": False}])
    high = _run(multi_hop_paths=[
        {"path_id": "h1", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.8, "contamination_warning": True},
        {"path_id": "h2", "path_nodes": ["A", "B", "D"], "path_quality_score": 0.75, "contamination_warning": True},
    ])
    assert high["contamination_spread_score"] > low["contamination_spread_score"]


def test_hub_concentration_rises_when_few_nodes_dominate_pressure():
    dispersed = _run(multi_hop_paths=[
        {"path_id": "d1", "path_nodes": ["A", "B"], "path_quality_score": 0.8},
        {"path_id": "d2", "path_nodes": ["C", "D"], "path_quality_score": 0.8},
    ])
    concentrated = _run(multi_hop_paths=[
        {"path_id": "c1", "path_nodes": ["A", "B"], "path_quality_score": 0.85},
        {"path_id": "c2", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.84},
        {"path_id": "c3", "path_nodes": ["A", "B", "D"], "path_quality_score": 0.83},
    ])
    assert concentrated["hub_concentration_score"] > dispersed["hub_concentration_score"]


def test_contained_classification():
    out = _run(multi_hop_paths=[{"path_id": "l1", "path_nodes": ["C", "D"], "path_quality_score": 0.25, "reinforcement_score": 0.0}])
    assert out["contagion_risk_state"] == "contained"


def test_spreading_or_amplified_classification():
    out = _run(multi_hop_paths=[
        {"path_id": "h1", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.95, "reinforcement_score": 0.15},
        {"path_id": "h2", "path_nodes": ["A", "B", "D"], "path_quality_score": 0.93, "reinforcement_score": 0.14},
    ])
    assert out["contagion_risk_state"] in {"spreading", "amplified"}


def test_bottlenecked_classification():
    out = _run(multi_hop_paths=[
        {"path_id": "b1", "path_nodes": ["B", "A"], "path_quality_score": 0.30, "suppressed_for_propagation": True},
        {"path_id": "b2", "path_nodes": ["B", "C"], "path_quality_score": 0.35, "suppressed_for_propagation": True},
        {"path_id": "b3", "path_nodes": ["B", "D"], "path_quality_score": 0.32, "suppressed_for_propagation": True},
        {"path_id": "b4", "path_nodes": ["B", "A", "C"], "path_quality_score": 0.40, "suppressed_for_propagation": True},
    ])
    assert out["contagion_risk_state"] == "bottlenecked"


def test_contaminated_classification():
    out = _run(multi_hop_paths=[
        {"path_id": "c1", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.8, "contamination_warning": True},
        {"path_id": "c2", "path_nodes": ["A", "B", "D"], "path_quality_score": 0.8, "contamination_warning": True},
        {"path_id": "c3", "path_nodes": ["A", "C", "D"], "path_quality_score": 0.7, "contamination_warning": True},
    ])
    assert out["contagion_risk_state"] == "contaminated"


def test_fragile_or_mixed_classification():
    out = _run(multi_hop_paths=[
        {"path_id": "f1", "path_nodes": ["B", "A"], "path_quality_score": 0.65, "suppressed_for_propagation": True, "contamination_warning": True},
        {"path_id": "f2", "path_nodes": ["B", "C"], "path_quality_score": 0.62, "suppressed_for_propagation": True, "contamination_warning": True},
    ])
    assert out["contagion_risk_state"] in {"fragile", "mixed", "contaminated", "bottlenecked"}


def test_corridor_state_classification():
    out = _run(multi_hop_paths=[
        {"path_id": "a", "path_nodes": ["A", "B"], "path_quality_score": 0.9, "reinforcement_score": 0.12},
        {"path_id": "s", "path_nodes": ["A", "D"], "path_quality_score": 0.4, "suppressed_for_propagation": True},
        {"path_id": "c", "path_nodes": ["B", "D"], "path_quality_score": 0.8, "contamination_warning": True},
        {"path_id": "w", "path_nodes": ["C", "D"], "path_quality_score": 0.2},
    ])
    mapping = {p["path_id"]: p["corridor_state"] for p in out["path_corridor_states"]}
    assert mapping["a"] in {"amplified_corridor", "healthy_corridor"}
    assert mapping["s"] == "suppressed_corridor"
    assert mapping["c"] == "contaminated_corridor"
    assert mapping["w"] == "weak_corridor"


def test_explainability_payload_exists():
    payload = _run()["explainability_payload"]
    for key in [
        "contagion_rationale",
        "key_contributing_metrics",
        "dominant_contagion_drivers",
        "hub_explanations",
        "corridor_explanations",
        "chokepoint_explanations",
        "suppression_explanations",
        "contamination_explanations",
        "resilience_explanation",
        "warnings",
    ]:
        assert key in payload


def test_cli_writes_output_log(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    payload = _inputs()
    (logs_dir / "tier3i_contagion_mapping_inputs.json").write_text(json.dumps(payload), encoding="utf-8")

    subprocess.run(
        [sys.executable, "-m", "transmission_layers.intelligence.tier3i.contagion_mapping"],
        cwd=tmp_path,
        check=True,
        env={"PYTHONPATH": str(repo_root)},
    )

    output_path = logs_dir / "tier3i_contagion_mapping_summary.json"
    assert output_path.exists()
    summary = json.loads(output_path.read_text(encoding="utf-8"))
    assert summary["status"] == "success"


def test_no_tier3h5_governance_dependency():
    source = Path("transmission_layers/intelligence/tier3i/contagion_mapping.py").read_text(encoding="utf-8").lower()
    assert "tier3h5" not in source
    assert "governance" not in source
