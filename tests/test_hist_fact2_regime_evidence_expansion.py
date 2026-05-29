from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.history_long.hist_fact2_regime_evidence_expansion import (
    GOVERNANCE_CERTIFICATION,
    build_hist_fact2_expansion,
    run_hist_fact2_expansion,
)
from transmission_layers.history_long.hist_intel2_taxonomy_weighted_intelligence import CONFIDENCE_LABELS


def _fact(fact_type: str, entity_id: str, metric_name: str, value: float, window: int, *, evidence_count: int = 2, confidence: str = "MEDIUM") -> dict[str, object]:
    return {
        "phase_id": "HIST-FACT-1",
        "fact_id": f"fixture_{fact_type}_{entity_id}_{metric_name}_{window}",
        "fact_type": fact_type,
        "entity_type": "window" if entity_id.startswith("window_") else "sector",
        "entity_id": entity_id,
        "metric_name": metric_name,
        "metric_value": value,
        "window_days": window,
        "evidence_count": evidence_count,
        "confidence_label": confidence,
        "source_phase": "HIST-LONG-fixture",
        "source_artifact": "local_fixture.json",
        "payload_jsonb": {"source_key": metric_name},
    }


def _facts() -> list[dict[str, object]]:
    return [
        _fact("replay_density_fact", "window_20", "replay_density", 0.20, 20, confidence="HIGH"),
        _fact("replay_density_fact", "window_60", "replay_density", 0.45, 60, confidence="HIGH"),
        _fact("replay_density_fact", "window_120", "replay_density", 0.75, 120, confidence="HIGH"),
        _fact("sector_concentration_fact", "alpha", "sector_hhi", 0.70, 20),
        _fact("sector_concentration_fact", "alpha", "sector_hhi", 0.55, 60),
        _fact("sector_concentration_fact", "alpha", "sector_hhi", 0.40, 120),
        _fact("topology_coherence_fact", "window_20", "topology_coherence", 0.80, 20),
        _fact("topology_coherence_fact", "window_60", "topology_coherence", 0.50, 60),
        _fact("topology_coherence_fact", "window_120", "topology_coherence", 0.30, 120),
        _fact("breadth_expansion_fact", "window_20", "effective_symbol_count", 100.0, 20),
        _fact("breadth_expansion_fact", "window_60", "effective_symbol_count", 150.0, 60),
        _fact("breadth_expansion_fact", "window_120", "effective_symbol_count", 125.0, 120),
    ]


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    fact1_path = tmp_path / "hist_fact1_expanded_observation_facts.json"
    intel2_path = tmp_path / "hist_intel2.json"
    intel3_path = tmp_path / "hist_intel3.json"
    fact1_path.write_text(json.dumps(_facts(), sort_keys=True), encoding="utf-8")
    intel2_path.write_text(json.dumps({"phase_id": "HIST-INTEL-2", "taxonomy_tier_counts": {"A": 12}}, sort_keys=True), encoding="utf-8")
    intel3_path.write_text(
        json.dumps(
            {
                "phase_id": "HIST-INTEL-3",
                "transition_diagnostics": {"candidate_transitions_found": 3, "candidate_transitions_emitted": 0},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return fact1_path, intel2_path, intel3_path


def test_deterministic_outputs_and_stable_identifiers(tmp_path: Path):
    fact1_path, intel2_path, intel3_path = _write_inputs(tmp_path)
    first = build_hist_fact2_expansion(fact1_path=fact1_path, intel2_path=intel2_path, intel3_path=intel3_path, max_facts=100)
    second = build_hist_fact2_expansion(fact1_path=copy.deepcopy(fact1_path), intel2_path=copy.deepcopy(intel2_path), intel3_path=copy.deepcopy(intel3_path), max_facts=100)
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)
    ids = [row["fact_id"] for row in first["expanded_regime_evidence"]]
    assert ids == [row["fact_id"] for row in second["expanded_regime_evidence"]]
    assert len(ids) == len(set(ids))


def test_net_new_facts_valid_confidence_and_high_requires_multi_window_support(tmp_path: Path):
    fact1_path, intel2_path, intel3_path = _write_inputs(tmp_path)
    report = build_hist_fact2_expansion(fact1_path=fact1_path, intel2_path=intel2_path, intel3_path=intel3_path, max_facts=100)
    assert report["source_fact_count"] == len(_facts())
    assert report["expanded_fact_count"] > 0
    assert report["net_new_fact_count"] > 0
    assert report["transition_relevant_fact_count"] == report["expanded_fact_count"]
    assert all(row["confidence_label"] in CONFIDENCE_LABELS for row in report["expanded_regime_evidence"])
    high_rows = [row for row in report["expanded_regime_evidence"] if row["confidence_label"] == "HIGH"]
    assert high_rows
    assert all(row["payload_jsonb"].get("source_fact_count", 0) >= 2 and row["payload_jsonb"].get("window_count", 0) >= 2 for row in high_rows)


def test_expected_regime_evidence_fact_classes_generated(tmp_path: Path):
    fact1_path, intel2_path, intel3_path = _write_inputs(tmp_path)
    report = build_hist_fact2_expansion(fact1_path=fact1_path, intel2_path=intel2_path, intel3_path=intel3_path, max_facts=100)
    fact_types = set(report["fact_type_distribution"])
    assert "replay_intensification_fact" in fact_types
    assert "concentration_relaxation_fact" in fact_types
    assert "topology_fragmentation_pressure_fact" in fact_types
    assert "participation_shift_fact" in fact_types
    assert "transition_pressure_fact" in fact_types
    assert "transition_rejection_fact" in fact_types


def test_governance_flags_present_true_and_no_api_paths():
    report = build_hist_fact2_expansion(observation_facts=_facts(), fact1_path=None, intel2_path=None, intel3_path=None, max_facts=100)
    assert report["governance_certification"] == GOVERNANCE_CERTIFICATION
    assert all(report["governance_certification"].values())
    source = Path("transmission_layers/history_long/hist_fact2_regime_evidence_expansion.py").read_text(encoding="utf-8")
    runner = Path("scripts/run_hist_fact2_regime_evidence_expansion.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "httpx.", "create_client(", "supabase.table(", ".insert(", ".upsert(", ".update(", ".delete("]
    assert not any(token in source + runner for token in forbidden)


def test_reports_and_expanded_evidence_artifact_created(tmp_path: Path):
    fact1_path, intel2_path, intel3_path = _write_inputs(tmp_path)
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    evidence_path = tmp_path / "expanded.json"
    report = run_hist_fact2_expansion(
        fact1_path=fact1_path,
        intel2_path=intel2_path,
        intel3_path=intel3_path,
        json_report_path=json_path,
        markdown_report_path=md_path,
        expanded_evidence_path=evidence_path,
        max_facts=100,
    )
    assert json_path.exists()
    assert md_path.exists()
    assert evidence_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["phase_id"] == "HIST-FACT-2"
    assert len(json.loads(evidence_path.read_text(encoding="utf-8"))) == report["expanded_fact_count"]
    markdown = md_path.read_text(encoding="utf-8")
    assert "# HIST-FACT-2" in markdown
    assert "analysis_only: true" in markdown
