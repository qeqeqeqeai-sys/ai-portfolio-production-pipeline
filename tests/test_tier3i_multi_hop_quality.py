from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from transmission_layers.intelligence.tier3i.multi_hop_quality import (
    SCORING_VERSION,
    build_summary,
    score_multi_hop_paths,
)


def _edge(
    source: str,
    target: str,
    quality: float,
    confidence: str = "high",
    suppressed: bool = False,
    recurrence: float = 0.7,
    persistence: float = 0.7,
    evidence: float = 0.7,
    ambiguity: float = 0.02,
    conflict: float = 0.02,
):
    return {
        "source_node_id": source,
        "target_node_id": target,
        "edge_quality_score": quality,
        "decay_adjusted_weight": quality,
        "confidence_band": confidence,
        "suppressed_for_propagation": suppressed,
        "recurrence_score": recurrence,
        "persistence_score": persistence,
        "evidence_strength_score": evidence,
        "ambiguity_penalty": ambiguity,
        "conflict_penalty": conflict,
        "metadata": {},
    }


def test_deterministic_path_scoring_same_input():
    edges = [_edge("a", "b", 0.8), _edge("b", "c", 0.72), _edge("c", "d", 0.64)]
    first = score_multi_hop_paths(edges, max_hops=3)
    second = score_multi_hop_paths(edges, max_hops=3)
    assert first == second


def test_bounded_scores_and_confidence_bands():
    edges = [_edge("a", "b", 0.99, ambiguity=0.0, conflict=0.0), _edge("b", "c", 0.1, confidence="low")]
    paths = score_multi_hop_paths(edges, max_hops=3)
    assert paths
    assert all(0.0 <= p["path_quality_score"] <= 1.0 for p in paths)
    assert all(p["path_confidence_band"] in {"high", "medium", "low"} for p in paths)


def test_max_hops_respected():
    edges = [_edge("a", "b", 0.9), _edge("b", "c", 0.8), _edge("c", "d", 0.7), _edge("d", "e", 0.6)]
    paths = score_multi_hop_paths(edges, max_hops=2)
    assert paths
    assert all(p["hop_count"] <= 2 for p in paths)


def test_hop_decay_reduces_longer_path_scores():
    edges = [_edge("a", "b", 0.8), _edge("b", "c", 0.8)]
    paths = score_multi_hop_paths(edges, max_hops=2)
    one_hop = next(p for p in paths if p["path_nodes"] == ["a", "b"])
    two_hop = next(p for p in paths if p["path_nodes"] == ["a", "b", "c"])
    assert one_hop["path_quality_score"] > two_hop["path_quality_score"]


def test_reinforcement_modestly_increases_path_score():
    strong_edges = [
        _edge("a", "b", 0.6, recurrence=1.0, persistence=1.0, evidence=1.0),
        _edge("b", "c", 0.6, recurrence=1.0, persistence=1.0, evidence=1.0),
    ]
    weak_edges = [
        _edge("a", "b", 0.6, recurrence=0.0, persistence=0.0, evidence=0.0),
        _edge("b", "c", 0.6, recurrence=0.0, persistence=0.0, evidence=0.0),
    ]

    strong_path = next(p for p in score_multi_hop_paths(strong_edges, max_hops=2) if p["hop_count"] == 2)
    weak_path = next(p for p in score_multi_hop_paths(weak_edges, max_hops=2) if p["hop_count"] == 2)

    assert strong_path["reinforcement_score"] > weak_path["reinforcement_score"]
    assert strong_path["reinforcement_score"] <= 0.15


def test_suppressed_edges_suppress_paths():
    edges = [_edge("a", "b", 0.85), _edge("b", "c", 0.85, suppressed=True)]
    paths = score_multi_hop_paths(edges, max_hops=2)
    suppressed_path = next(p for p in paths if p["path_nodes"] == ["a", "b", "c"])
    assert suppressed_path["suppressed_for_propagation"] is True


def test_cycle_detection_prevents_repeated_nodes():
    edges = [_edge("a", "b", 0.9), _edge("b", "a", 0.9), _edge("b", "c", 0.7)]
    paths = score_multi_hop_paths(edges, max_hops=3)
    assert all(len(p["path_nodes"]) == len(set(p["path_nodes"])) for p in paths)
    assert ["a", "b", "a"] not in [p["path_nodes"] for p in paths]


def test_contamination_warning_for_risky_paths():
    edges = [
        _edge("a", "b", 0.5, confidence="low", ambiguity=0.4, conflict=0.4),
        _edge("b", "c", 0.5, confidence="low", ambiguity=0.4, conflict=0.4),
    ]
    paths = score_multi_hop_paths(edges, max_hops=2)
    risky = next(p for p in paths if p["hop_count"] == 2)
    assert risky["contamination_warning"] is True


def test_explainability_payload_has_required_components():
    paths = score_multi_hop_paths([_edge("a", "b", 0.7)], max_hops=1)
    payload = paths[0]["explainability_payload"]
    assert "component_scores" in payload
    assert "edge_sequence" in payload
    assert "rationale" in payload
    assert "warnings" in payload


def test_summary_and_scoring_version():
    paths = score_multi_hop_paths([_edge("a", "b", 0.8)], max_hops=1)
    summary = build_summary(paths)
    assert summary["scoring_version"] == SCORING_VERSION
    assert summary["status"] == "success"


def test_cli_writes_summary_json_and_no_tier3h5_dependency(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [sys.executable, "-m", "transmission_layers.intelligence.tier3i.multi_hop_quality"],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "[tier3i]" in result.stdout

    summary_path = tmp_path / "logs" / "tier3i_multi_hop_quality_summary.json"
    assert summary_path.exists()

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["tier"] == "3I"
    assert payload["phase"] == "2A"
    assert payload["status"] == "success"
