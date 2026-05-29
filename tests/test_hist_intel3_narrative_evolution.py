from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.history_long.hist_intel3_narrative_evolution import (
    CONFIDENCE_LABELS,
    build_narrative_evolution_report,
    run_hist_intel3,
)


def _fact(fact_type: str, entity_id: str, metric_name: str, metric_value: float, window_days: int, *, entity_type: str = "sector", confidence_label: str = "HIGH", evidence_count: int = 2) -> dict:
    return {
        "phase_id": "HIST-FACT-1",
        "fact_type": fact_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "window_days": window_days,
        "evidence_count": evidence_count,
        "confidence_label": confidence_label,
        "source_phase": "HIST-LONG-8",
    }


def _facts() -> list[dict]:
    return [
        _fact("persistence_fact", "semiconductors", "persistence_score", 0.30, 20),
        _fact("persistence_fact", "semiconductors", "persistence_score", 0.78, 120),
        _fact("persistence_fact", "legacy_media", "persistence_score", 0.82, 20),
        _fact("persistence_decay_fact", "legacy_media", "persistence_score", 0.42, 120),
        _fact("sector_concentration_fact", "cloud_platforms", "sector_hhi", 0.34, 20),
        _fact("sector_concentration_fact", "cloud_platforms", "sector_hhi", 0.72, 120),
        _fact("replay_density_fact", "ai_infrastructure", "replay_density", 0.22, 20),
        _fact("replay_density_fact", "ai_infrastructure", "replay_density", 0.70, 120),
        _fact("topology_coherence_fact", "software_ecosystem", "coherence_score", 0.74, 20),
        _fact("topology_fragmentation_fact", "software_ecosystem", "coherence_score", 0.31, 120),
        _fact("fragility_fact", "consumer_devices", "fragility_score", 0.24, 20),
        _fact("fragility_fact", "consumer_devices", "fragility_score", 0.68, 120),
        _fact("topology_coherence_fact", "stable_network", "coherence_score", 0.72, 20),
        _fact("topology_coherence_fact", "stable_network", "coherence_score", 0.74, 120),
        _fact("sector_concentration_fact", "broad_participation_same_state", "sector_hhi", 0.08, 20),
        _fact("sector_concentration_fact", "broad_participation_same_state", "sector_hhi", 0.24, 120),
    ]


def test_deterministic_output_for_same_inputs():
    first = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    second = build_narrative_evolution_report(observation_facts=copy.deepcopy(_facts()), local_facts_path=None, intel2_path=None, top_n=20)
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)


def test_stable_narrative_identifiers_are_deterministic():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    ids = [row["narrative_id"] for row in report["findings"]["major_narrative_evolutions"]]
    stable_ids = [row["narrative_id"] for row in report["findings"]["stable_long_term_narratives"]]
    assert ids
    repeat = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    assert ids == [row["narrative_id"] for row in repeat["findings"]["major_narrative_evolutions"]]
    assert stable_ids == [row["narrative_id"] for row in repeat["findings"]["stable_long_term_narratives"]]
    assert all(item.startswith("histintel3_") for item in ids + stable_ids)


def test_transition_detection_works_for_required_regimes():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    transitions = {row["transition_label"] for row in report["findings"]["regime_transition_candidates"]}
    assert "Persistent → Decaying" in transitions
    assert "Low Replay → High Replay" in transitions
    assert "Broad Participation → Narrow Participation" in transitions
    assert "Coherent → Fragmented" in transitions


def test_unsupported_single_window_transition_not_emitted():
    facts = _facts() + [_fact("replay_density_fact", "unsupported_single_window", "replay_density", 0.90, 120)]
    report = build_narrative_evolution_report(observation_facts=facts, local_facts_path=None, intel2_path=None, top_n=20)
    payload = json.dumps(report["findings"], sort_keys=True)
    assert "unsupported_single_window" not in payload
    assert report["transition_diagnostics"]["rejected_insufficient_fact_count"] >= 1


def test_same_state_large_delta_goes_to_suppressed_not_major():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    major_payload = json.dumps(report["findings"]["major_narrative_evolutions"], sort_keys=True)
    suppressed = report["findings"]["suppressed_same_state_evolutions"]
    assert "broad_participation_same_state" not in major_payload
    assert any(row["supporting_entities"] == ["broad_participation_same_state"] for row in suppressed)
    assert all(row["starting_state"] == row["ending_state"] for row in suppressed)


def test_same_state_small_delta_goes_to_stable_long_term_narratives():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    stable = report["findings"]["stable_long_term_narratives"]
    assert any(row["supporting_entities"] == ["stable_network"] for row in stable)
    durable = next(row for row in stable if row["supporting_entities"] == ["stable_network"])
    assert durable["starting_state"] == durable["ending_state"] == "Coherent"
    assert abs(durable["delta"]) < 0.05


def test_duplicate_narratives_are_deduplicated():
    report = build_narrative_evolution_report(observation_facts=_facts() + copy.deepcopy(_facts()), local_facts_path=None, intel2_path=None, top_n=20)
    keys = [
        (row["dimension"], row["supporting_entities"][0], row["starting_state"], row["ending_state"], row["narrative_type"])
        for row in report["findings"]["major_narrative_evolutions"]
    ]
    assert len(keys) == len(set(keys))


def test_regime_transition_candidates_only_contain_true_supported_transitions():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    candidates = report["findings"]["regime_transition_candidates"]
    assert candidates
    assert all(row["starting_state"] != row["ending_state"] for row in candidates)
    assert all(row["transition_label"] is not None for row in candidates)
    assert all(row["supporting_fact_count"] >= 2 for row in candidates)
    assert all(len(row["supporting_windows"]) >= 2 for row in candidates)


def test_executive_summary_excludes_same_state_as_major_transition():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    summary = " ".join(report["findings"]["executive_narrative_summary"])
    assert "true state transition" in summary
    assert "supported narrative evolution" not in summary
    assert "broad_participation_same_state" not in summary


def test_confidence_labels_valid_and_high_requires_multi_window_support():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    labels = [row["confidence_label"] for row in report["findings"]["major_narrative_evolutions"]]
    labels += [row["confidence_label"] for row in report["findings"]["stable_long_term_narratives"]]
    labels += [row["confidence_label"] for row in report["findings"]["suppressed_same_state_evolutions"]]
    assert labels
    assert set(labels) <= set(CONFIDENCE_LABELS)
    high_rows = [row for row in report["findings"]["major_narrative_evolutions"] if row["confidence_label"] == "HIGH"]
    assert high_rows
    assert all(row["supporting_fact_count"] >= 2 and len(row["supporting_windows"]) >= 2 for row in high_rows)


def test_governance_flags_present_and_true():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    expected = {
        "analysis_only",
        "local_only",
        "no_provider_calls",
        "no_supabase_writes",
        "no_prediction",
        "no_trading",
        "no_portfolio_recommendation",
        "no_governed_activation",
    }
    assert set(report["governance_certification"]) == expected
    assert all(report["governance_certification"].values())


def test_no_provider_api_or_supabase_write_path_is_introduced():
    source = Path("transmission_layers/history_long/hist_intel3_narrative_evolution.py").read_text(encoding="utf-8")
    runner = Path("scripts/run_hist_intel3_narrative_evolution.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "httpx.", ".upsert(", ".update(", ".delete(", "create_client(", "supabase.table(", ".insert("]
    combined = source + runner
    assert not any(token in combined for token in forbidden)


def test_no_prediction_trading_or_portfolio_wording_appears_in_findings():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    findings_text = json.dumps(report["findings"], sort_keys=True).lower()
    banned = ["buy", "sell", "hold", "price target", "outperform", "underperform", "forecast"]
    assert not any(term in findings_text for term in banned)


def test_json_and_markdown_reports_are_created(tmp_path: Path):
    json_path = tmp_path / "hist_intel3.json"
    md_path = tmp_path / "hist_intel3.md"
    report = run_hist_intel3(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=10, json_report_path=json_path, markdown_report_path=md_path)
    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["phase_id"] == "HIST-INTEL-3"
    markdown = md_path.read_text(encoding="utf-8")
    assert "# HIST-INTEL-3" in markdown
    assert "## Executive Narrative Summary" in markdown
    assert report["output_paths"]["json_report_path"] == json_path.as_posix()


def test_required_sections_present_and_narrative_types_generated():
    report = build_narrative_evolution_report(observation_facts=_facts(), local_facts_path=None, intel2_path=None, top_n=20)
    findings = report["findings"]
    expected_sections = {
        "executive_narrative_summary",
        "major_narrative_evolutions",
        "regime_transition_candidates",
        "persistence_evolution",
        "replay_evolution",
        "concentration_evolution",
        "topology_evolution",
        "fragility_evolution",
        "stable_long_term_narratives",
        "suppressed_same_state_evolutions",
    }
    assert set(findings) == expected_sections
    assert "Persistence Expansion" in report["narrative_types_generated"]
    assert "Stable Long-Term Narrative" in report["narrative_types_generated"]
