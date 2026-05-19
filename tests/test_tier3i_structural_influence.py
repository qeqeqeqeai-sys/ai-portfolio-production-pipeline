import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import subprocess

from transmission_layers.intelligence.tier3i.structural_influence import score_structural_influence


def _base_edges():
    return [
        {
            "source_node_id": "a",
            "target_node_id": "b",
            "edge_quality_score": 0.9,
            "decay_adjusted_weight": 0.8,
            "confidence_band": "high",
            "suppressed_for_propagation": False,
            "recurrence_score": 0.8,
            "persistence_score": 0.8,
            "evidence_strength_score": 0.9,
        },
        {
            "source_node_id": "a",
            "target_node_id": "c",
            "edge_quality_score": 0.85,
            "decay_adjusted_weight": 0.8,
            "confidence_band": "high",
            "suppressed_for_propagation": False,
            "recurrence_score": 0.7,
            "persistence_score": 0.7,
            "evidence_strength_score": 0.9,
        },
        {
            "source_node_id": "c",
            "target_node_id": "d",
            "edge_quality_score": 0.4,
            "decay_adjusted_weight": 0.4,
            "confidence_band": "medium",
            "suppressed_for_propagation": False,
            "recurrence_score": 0.5,
            "persistence_score": 0.4,
            "evidence_strength_score": 0.5,
        },
    ]


def _row(rows, node_id):
    return next(row for row in rows if row["node_id"] == node_id)


def test_deterministic_scoring_for_same_input():
    edges = _base_edges()
    assert score_structural_influence(edges) == score_structural_influence(edges)


def test_scores_are_bounded():
    rows = score_structural_influence(_base_edges())
    for row in rows:
        assert 0.0 <= row["direct_influence_score"] <= 1.0
        assert 0.0 <= row["downstream_reach_score"] <= 1.0
        assert 0.0 <= row["weighted_centrality_score"] <= 1.0
        assert 0.0 <= row["persistence_adjusted_influence_score"] <= 1.0
        assert 0.0 <= row["structural_influence_score"] <= 1.0


def test_ranking_order_and_tie_break_deterministic():
    tie_edges = [
        {"source_node_id": "a", "target_node_id": "x", "edge_quality_score": 0.5},
        {"source_node_id": "b", "target_node_id": "y", "edge_quality_score": 0.5},
    ]
    rows = score_structural_influence(tie_edges)
    assert rows[0]["node_id"] == "a"
    assert rows[1]["node_id"] == "b"
    assert rows[0]["structural_importance_rank"] == 1


def test_suppressed_edges_heavily_downweighted():
    normal = score_structural_influence(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.9}]
    )
    suppressed = score_structural_influence(
        [
            {
                "source_node_id": "a",
                "target_node_id": "b",
                "edge_quality_score": 0.9,
                "suppressed_for_propagation": True,
            }
        ]
    )
    assert _row(suppressed, "a")["structural_influence_score"] < _row(normal, "a")["structural_influence_score"]


def test_missing_edge_quality_score_degrades_gracefully():
    rows = score_structural_influence(
        [{"source_node_id": "a", "target_node_id": "b", "base_weight": 0.6}]
    )
    assert _row(rows, "a")["structural_influence_score"] > 0.0


def test_high_confidence_edges_increase_influence():
    high = score_structural_influence(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.9, "confidence_band": "high"}]
    )
    low = score_structural_influence(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.4, "confidence_band": "low"}]
    )
    assert _row(high, "a")["structural_influence_score"] > _row(low, "a")["structural_influence_score"]


def test_downstream_reach_affects_score():
    one_target = score_structural_influence(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.8}]
    )
    two_targets = score_structural_influence(
        [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.8},
            {"source_node_id": "a", "target_node_id": "c", "edge_quality_score": 0.8},
        ]
    )
    assert _row(two_targets, "a")["downstream_reach_score"] >= _row(one_target, "a")["downstream_reach_score"]


def test_persistence_affects_score():
    high_p = score_structural_influence(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.6, "persistence_score": 0.9}]
    )
    low_p = score_structural_influence(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.6, "persistence_score": 0.1}]
    )
    assert _row(high_p, "a")["persistence_adjusted_influence_score"] > _row(low_p, "a")["persistence_adjusted_influence_score"]


def test_explainability_payload_present():
    rows = score_structural_influence(_base_edges())
    payload = _row(rows, "a")["explainability_payload"]
    assert "component_scores" in payload
    assert "contributing_edges" in payload
    assert "rationale" in payload


def test_cli_writes_summary_json():
    output_path = Path("logs/tier3i_structural_influence_summary.json")
    if output_path.exists():
        output_path.unlink()

    subprocess.run(
        [sys.executable, "-m", "transmission_layers.intelligence.tier3i.structural_influence"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["tier"] == "3I"
    assert payload["phase"] == "1B"
    assert payload["status"] == "success"


def test_module_has_no_tier3h5_governance_dependency():
    module_text = Path(
        "transmission_layers/intelligence/tier3i/structural_influence.py"
    ).read_text(encoding="utf-8")
    assert "tier3h5" not in module_text.lower()
    assert "governance" not in module_text.lower()
