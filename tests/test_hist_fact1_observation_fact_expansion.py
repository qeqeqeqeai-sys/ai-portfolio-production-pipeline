from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.history_long.hist_fact1_observation_fact_expansion import (
    GOVERNANCE_CERTIFICATION,
    VALID_CONFIDENCE_LABELS,
    build_hist_fact1_expansion,
    run_hist_fact1_expansion,
)


def _write_sources(tmp_path: Path) -> dict[str, Path]:
    hist4 = {
        "status": "ok",
        "window_level_results": [
            {
                "window_trading_days": 20,
                "replay_density": 1.0,
                "replay_saturation": {"density": 0.9},
                "effective_symbol_count": 10,
                "failed_count": 0,
                "completeness": 1.0,
                "sector_hhi": {"universe_hhi": 0.2, "strongest_sectors": [{"sector": "alpha", "share": 0.4, "symbol_count": 4}]},
                "subsector_hhi": {"universe_hhi": 0.3, "strongest_subsectors": [{"subsector": "alpha_sub", "share": 0.3, "symbol_count": 3}]},
            },
            {
                "window_trading_days": 60,
                "replay_density": 0.8,
                "replay_saturation": {"density": 0.85},
                "effective_symbol_count": 11,
                "failed_count": 0,
                "completeness": 1.0,
                "sector_hhi": {"universe_hhi": 0.21, "strongest_sectors": [{"sector": "alpha", "share": 0.38, "symbol_count": 4}]},
                "subsector_hhi": {"universe_hhi": 0.31, "strongest_subsectors": [{"subsector": "alpha_sub", "share": 0.31, "symbol_count": 3}]},
            },
        ],
    }
    hist5b = {
        "status": "ok",
        "metric_values_by_window": {"20": {"replay_density": 1.0, "sector_hhi": 0.2}, "60": {"replay_density": 0.8, "sector_hhi": 0.21}, "120": {"replay_density": 0.75, "sector_hhi": 0.22}},
        "structural_persistence_classification": {"replay_density": "stable", "sector_hhi": "volatile", "morphology_persistence": "stable"},
        "temporal_delta_tables": {"replay": [{"metric": "replay_density", "from_window": 20, "to_window": 60, "absolute_delta": -0.2, "direction": "down", "interpretation": "decaying"}]},
    }
    hist6 = {"status": "ok", "primary_baseline_window": 120, "findings": {"strongest_differentiated_sectors": [{"sector": "alpha", "group_type": "sector", "differentiation_score": 0.4, "confidence": "high", "representation_label": "overrepresented", "stability_label": "stable_distinct", "symbol_count": 4}]}}
    hist7 = {
        "status": "ok",
        "group_morphology_decomposition": [
            {
                "group": "alpha",
                "metrics": {"morphology_persistence_score": 1.0, "structural_coherence_score": 0.9, "breadth_of_differentiation": 0.8, "hidden_concentration_intensity": 0.3, "anchor_dependency_score": 0.2, "leader_tail_gap": 0.1},
                "structural_read": {"persistent_vs_episodic": "persistent", "coherent_vs_stratified": "coherent"},
                "morphology_classifications": ["broad_coherent"],
                "persistence_indicators": {"stable_leaders_across_20_60_120": True, "low_rank_churn": True},
                "fragility_indicators": {"weak_breadth": False, "high_leader_tail_gap": False},
                "window_observations": [{"window": 20}, {"window": 60}, {"window": 120}],
            }
        ],
    }
    sources = {
        "HIST-LONG-4": tmp_path / "hist4.json",
        "HIST-LONG-5B": tmp_path / "hist5b.json",
        "HIST-LONG-6": tmp_path / "hist6.json",
        "HIST-LONG-7": tmp_path / "hist7.json",
        "HIST-LONG-8": tmp_path / "missing8.json",
        "HIST-LONG-9": tmp_path / "missing9.json",
    }
    for phase, payload in (("HIST-LONG-4", hist4), ("HIST-LONG-5B", hist5b), ("HIST-LONG-6", hist6), ("HIST-LONG-7", hist7)):
        sources[phase].write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return sources


def test_deterministic_outputs_and_stable_identifiers(tmp_path: Path):
    sources = _write_sources(tmp_path)
    first = build_hist_fact1_expansion(source_paths=sources, max_facts=100)
    second = build_hist_fact1_expansion(source_paths=copy.deepcopy(sources), max_facts=100)
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)
    ids = [row["fact_id"] for row in first["expanded_facts"]]
    assert ids == [row["fact_id"] for row in second["expanded_facts"]]
    assert len(ids) == len(set(ids))


def test_bounded_fact_generation_and_valid_confidence(tmp_path: Path):
    report = build_hist_fact1_expansion(source_paths=_write_sources(tmp_path), max_facts=7)
    assert report["bounded_output"] is True
    assert report["expanded_fact_count"] == 7
    assert all(row["confidence_label"] in VALID_CONFIDENCE_LABELS for row in report["expanded_facts"])


def test_governance_flags_present_true_and_no_api_paths(tmp_path: Path):
    report = build_hist_fact1_expansion(source_paths=_write_sources(tmp_path), max_facts=100)
    assert report["governance_certification"] == GOVERNANCE_CERTIFICATION
    assert all(report["governance_certification"].values())
    source_text = json.dumps(report["source_artifacts_loaded"] + report["source_artifacts_missing"] + [row["source_artifact"] for row in report["expanded_facts"]], sort_keys=True).lower()
    assert "fmp" not in source_text
    assert "api" not in source_text
    assert "supabase" not in source_text


def test_reports_and_expanded_fact_artifact_created(tmp_path: Path):
    sources = _write_sources(tmp_path)
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    facts_path = tmp_path / "facts.json"
    report = run_hist_fact1_expansion(source_paths=sources, json_report_path=json_path, markdown_report_path=md_path, expanded_facts_path=facts_path, max_facts=100)
    assert json_path.exists()
    assert md_path.exists()
    assert facts_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["expanded_fact_count"] == report["expanded_fact_count"]
    assert len(json.loads(facts_path.read_text(encoding="utf-8"))) == report["expanded_fact_count"]
    assert report["net_new_fact_count"] > 0


def test_expected_fact_classes_are_generated_when_source_data_exists(tmp_path: Path):
    report = build_hist_fact1_expansion(source_paths=_write_sources(tmp_path), max_facts=100)
    fact_types = set(report["fact_type_distribution"])
    assert {"sector_concentration_fact", "replay_stability_fact", "entity_persistence_fact", "topology_stability_fact"} <= fact_types
    assert report["expanded_fact_count"] > report["original_fact_count"]
