import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import subprocess
import sys
from transmission_layers.intelligence.tier3i.intelligence_summary import build_intelligence_summary


def _sample_edges():
    return [
        {"source_node_id": "b", "target_node_id": "x", "edge_quality_score": 0.8, "confidence_band": "high"},
        {"source_node_id": "a", "target_node_id": "y", "edge_quality_score": 0.8, "confidence_band": "high"},
        {
            "source_node_id": "z",
            "target_node_id": "m",
            "edge_quality_score": 0.3,
            "confidence_band": "low",
            "suppressed_for_propagation": True,
        },
    ]


def _sample_nodes():
    return [
        {
            "node_id": "beta",
            "structural_influence_score": 0.7,
            "influence_confidence_band": "high",
            "contributing_edge_count": 2,
        },
        {
            "node_id": "alpha",
            "structural_influence_score": 0.7,
            "influence_confidence_band": "high",
            "contributing_edge_count": 1,
        },
    ]


def _sample_paths():
    return [
        {
            "path_id": "path::b",
            "source_node_id": "src_b",
            "terminal_node_id": "term_a",
            "path_quality_score": 0.82,
            "path_confidence_band": "high",
            "suppressed_for_propagation": False,
            "contamination_warning": False,
        },
        {
            "path_id": "path::a",
            "source_node_id": "src_a",
            "terminal_node_id": "term_a",
            "path_quality_score": 0.82,
            "path_confidence_band": "medium",
            "suppressed_for_propagation": False,
            "contamination_warning": False,
        },
        {
            "path_id": "path::c",
            "source_node_id": "src_c",
            "terminal_node_id": "term_b",
            "path_quality_score": 0.40,
            "path_confidence_band": "low",
            "suppressed_for_propagation": True,
            "contamination_warning": True,
        },
    ]


def _sample_explanations():
    return [
        {"path_id": "path::c", "decision_usefulness_label": "weak_signal"},
        {"path_id": "path::a", "decision_usefulness_label": "actionable_watchlist"},
        {"path_id": "path::b", "decision_usefulness_label": "actionable_watchlist"},
    ]


def test_deterministic_summary_output_same_input():
    edges = _sample_edges()
    nodes = _sample_nodes()
    assert build_intelligence_summary(edges, nodes) == build_intelligence_summary(edges, nodes)


def test_phase_1c_style_usage_still_works_without_multi_hop_inputs():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes())
    assert summary["status"] == "success"
    assert summary["edges_scored"] == 3
    assert summary["nodes_scored"] == 2


def test_paths_defaults_zero_when_omitted():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes())
    assert summary["paths_scored"] == 0
    assert summary["paths_explained"] == 0
    assert summary["top_multi_hop_paths"] == []
    assert summary["actionable_causal_chains"] == []
    assert summary["suppressed_paths"] == []
    assert summary["contaminated_paths"] == []
    assert summary["weak_causal_chains"] == []
    assert summary["multi_hop_signal_health"]["average_path_quality_score"] == 0.0
    assert summary["multi_hop_signal_health"]["multi_hop_health_band"] == "fragile"


def test_top_edge_sorting_and_tiebreak():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes())
    top = summary["top_quality_edges"]
    assert top[0]["source_node_id"] == "a"
    assert top[1]["source_node_id"] == "b"


def test_top_node_sorting_and_tiebreak():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes())
    top = summary["top_structural_influence_nodes"]
    assert top[0]["node_id"] == "alpha"
    assert top[1]["node_id"] == "beta"


def test_top_multi_hop_paths_sorted_deterministically():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes(), _sample_paths(), _sample_explanations())
    top = summary["top_multi_hop_paths"]
    assert [p["path_id"] for p in top] == ["path::a", "path::b", "path::c"]


def test_actionable_causal_chains_extracted_correctly():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes(), _sample_paths(), _sample_explanations())
    assert [item["path_id"] for item in summary["actionable_causal_chains"]] == ["path::a", "path::b"]


def test_suppressed_paths_extracted_correctly():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes(), _sample_paths(), _sample_explanations())
    assert [item["path_id"] for item in summary["suppressed_paths"]] == ["path::c"]


def test_contaminated_paths_extracted_correctly():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes(), _sample_paths(), _sample_explanations())
    assert [item["path_id"] for item in summary["contaminated_paths"]] == ["path::c"]


def test_weak_causal_chains_extracted_correctly():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes(), _sample_paths(), _sample_explanations())
    assert [item["path_id"] for item in summary["weak_causal_chains"]] == ["path::c"]


def test_suppressed_edge_extraction():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes())
    assert len(summary["suppressed_edges"]) == 1
    assert summary["suppressed_edges"][0]["source_node_id"] == "z"


def test_weak_link_extraction():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes())
    weak = summary["weak_transmission_links"]
    assert len(weak) == 1
    assert weak[0]["source_node_id"] == "z"


def test_emerging_driver_detection():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes())
    drivers = summary["emerging_structural_drivers"]
    assert [d["node_id"] for d in drivers] == ["alpha", "beta"]


def test_graph_signal_health_band_classification():
    healthy = build_intelligence_summary(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.9, "confidence_band": "high"}],
        [{"node_id": "a", "structural_influence_score": 0.8, "influence_confidence_band": "high"}],
    )
    assert healthy["graph_signal_health"]["graph_signal_health_band"] == "healthy"

    watch = build_intelligence_summary(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.5, "confidence_band": "medium"}],
        [{"node_id": "a", "structural_influence_score": 0.5, "influence_confidence_band": "medium"}],
    )
    assert watch["graph_signal_health"]["graph_signal_health_band"] == "watch"

    fragile = build_intelligence_summary(
        [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.2, "confidence_band": "low"}],
        [{"node_id": "a", "structural_influence_score": 0.2, "influence_confidence_band": "low"}],
    )
    assert fragile["graph_signal_health"]["graph_signal_health_band"] == "fragile"


def test_multi_hop_signal_health_band_classification():
    healthy = build_intelligence_summary(
        _sample_edges(),
        _sample_nodes(),
        [{"path_id": "p1", "path_quality_score": 0.75, "path_confidence_band": "high"}],
        [{"path_id": "p1", "decision_usefulness_label": "actionable_watchlist"}],
    )
    assert healthy["multi_hop_signal_health"]["multi_hop_health_band"] == "healthy"

    watch = build_intelligence_summary(
        _sample_edges(),
        _sample_nodes(),
        [{"path_id": "p1", "path_quality_score": 0.50, "path_confidence_band": "medium"}],
        [{"path_id": "p1", "decision_usefulness_label": "actionable_watchlist"}],
    )
    assert watch["multi_hop_signal_health"]["multi_hop_health_band"] == "watch"

    fragile = build_intelligence_summary(
        _sample_edges(),
        _sample_nodes(),
        [{"path_id": "p1", "path_quality_score": 0.30, "path_confidence_band": "low"}],
        [{"path_id": "p1", "decision_usefulness_label": "weak_signal"}],
    )
    assert fragile["multi_hop_signal_health"]["multi_hop_health_band"] == "fragile"


def test_explainability_rationales_include_multi_hop_inputs():
    summary = build_intelligence_summary(_sample_edges(), _sample_nodes(), _sample_paths(), _sample_explanations())
    joined = " ".join(summary["explainability_rationales"]).lower()
    assert "top multi-hop path" in joined
    assert "multi-hop health" in joined
    assert "suppressed" in joined
    assert "contamination" in joined
    assert "actionable causal chains" in joined


def test_missing_optional_fields_degrade_gracefully():
    summary = build_intelligence_summary(
        [{"source_node_id": "a", "target_node_id": "b"}],
        [{"node_id": "a"}],
    )
    assert summary["status"] == "success"
    assert summary["graph_signal_health"]["average_edge_quality_score"] == 0.0


def test_cli_writes_summary_log():
    root = Path(__file__).resolve().parents[1]
    out = root / "logs" / "tier3i_transmission_intelligence_summary.json"
    if out.exists():
        out.unlink()

    result = subprocess.run(
        [sys.executable, "-m", "transmission_layers.intelligence.tier3i.intelligence_summary"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "[tier3i]" in result.stdout
    assert "paths_scored=" in result.stdout
    assert "multi_hop_health=" in result.stdout
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["phase"] == "2C"
    assert "multi_hop_signal_health" in payload


def test_no_dependency_on_tier3h5_governance_modules():
    module_path = Path(__file__).resolve().parents[1] / "transmission_layers" / "intelligence" / "tier3i" / "intelligence_summary.py"
    text = module_path.read_text(encoding="utf-8")
    assert "tier3h5" not in text.lower()
    assert "governance" not in text.lower()
