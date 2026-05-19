import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import subprocess
from transmission_layers.intelligence.tier3i.edge_quality import score_edge_quality


def test_deterministic_scoring_same_input():
    edge = {"evidence_count": 5, "evidence_confidence": 0.8, "base_weight": 0.7}
    assert score_edge_quality(edge) == score_edge_quality(edge)


def test_score_boundedness():
    edge = {
        "evidence_count": 100,
        "evidence_confidence": 10,
        "recurrence_count": 999,
        "persistence_days": 999,
        "directional_consistency": 5,
        "ambiguity_count": 0,
        "conflict_count": 0,
        "last_seen_days_ago": 0,
        "base_weight": 2.0,
    }
    scored = score_edge_quality(edge)
    assert 0.0 <= scored["edge_quality_score"] <= 1.0
    assert 0.0 <= scored["decay_adjusted_weight"] <= 1.0


def test_missing_optional_fields_graceful_degradation():
    scored = score_edge_quality({})
    assert 0.0 <= scored["edge_quality_score"] <= 1.0
    assert scored["confidence_band"] in {"high", "medium", "low"}


def test_high_confidence_edge_classification():
    scored = score_edge_quality(
        {
            "evidence_count": 10,
            "evidence_confidence": 1.0,
            "recurrence_count": 10,
            "persistence_days": 365,
            "directional_consistency": 1.0,
            "last_seen_days_ago": 0,
        }
    )
    assert scored["confidence_band"] == "high"


def test_low_quality_edge_suppression():
    scored = score_edge_quality(
        {
            "evidence_count": 0,
            "evidence_confidence": 0.0,
            "recurrence_count": 0,
            "persistence_days": 0,
            "directional_consistency": 0.0,
            "ambiguity_count": 5,
            "conflict_count": 5,
            "last_seen_days_ago": 30,
        }
    )
    assert scored["edge_quality_score"] < 0.30
    assert scored["suppressed_for_propagation"] is True


def test_ambiguity_and_conflict_penalties_reduce_score():
    base = {
        "evidence_count": 6,
        "evidence_confidence": 0.8,
        "recurrence_count": 6,
        "persistence_days": 120,
        "directional_consistency": 0.9,
        "last_seen_days_ago": 2,
    }
    no_penalty = score_edge_quality(base)
    with_penalty = score_edge_quality({**base, "ambiguity_count": 5, "conflict_count": 5})
    assert with_penalty["edge_quality_score"] < no_penalty["edge_quality_score"]


def test_freshness_decay_reduces_score():
    fresh = score_edge_quality({"evidence_count": 5, "evidence_confidence": 0.8, "last_seen_days_ago": 0})
    stale = score_edge_quality({"evidence_count": 5, "evidence_confidence": 0.8, "last_seen_days_ago": 30})
    assert stale["edge_quality_score"] < fresh["edge_quality_score"]


def test_explanation_payload_contains_component_scores():
    scored = score_edge_quality({"evidence_count": 4, "evidence_confidence": 0.6})
    payload = scored["explainability_payload"]
    assert "positive_components" in payload
    assert "penalties" in payload
    assert "rationale" in payload


def test_cli_writes_summary_json():
    output_path = Path("logs/tier3i_edge_quality_summary.json")
    if output_path.exists():
        output_path.unlink()

    subprocess.run(
        [sys.executable, "-m", "transmission_layers.intelligence.tier3i.edge_quality"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["tier"] == "3I"
    assert payload["phase"] == "1A"
    assert payload["status"] == "success"


def test_scoring_module_has_no_tier3h5_governance_imports():
    module_text = Path("transmission_layers/intelligence/tier3i/edge_quality.py").read_text(
        encoding="utf-8"
    )
    assert "tier3h5" not in module_text.lower()
    assert "governance" not in module_text.lower()
