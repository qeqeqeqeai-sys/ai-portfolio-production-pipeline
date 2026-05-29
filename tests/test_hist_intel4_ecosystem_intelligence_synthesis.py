from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.history_long.hist_intel4_ecosystem_intelligence_synthesis import (
    GOVERNANCE_CERTIFICATION,
    build_ecosystem_intelligence_synthesis,
    run_hist_intel4,
)


def _fact1_rows() -> list[dict]:
    return [
        {
            "phase_id": "HIST-FACT-1",
            "fact_id": "f1_topology_20",
            "fact_type": "topology_stability_fact",
            "entity_type": "sector",
            "entity_id": "semiconductors",
            "metric_name": "topology_stability_score",
            "metric_value": 0.82,
            "window_days": 20,
            "evidence_count": 3,
            "confidence_label": "HIGH",
            "source_phase": "HIST-LONG-7",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_id": "f1_topology_60",
            "fact_type": "topology_stability_fact",
            "entity_type": "sector",
            "entity_id": "semiconductors",
            "metric_name": "topology_stability_score",
            "metric_value": 0.86,
            "window_days": 60,
            "evidence_count": 3,
            "confidence_label": "HIGH",
            "source_phase": "HIST-LONG-8",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_id": "f1_persistence_120",
            "fact_type": "persistence_fact",
            "entity_type": "sector",
            "entity_id": "semiconductors",
            "metric_name": "persistence_score",
            "metric_value": 0.88,
            "window_days": 120,
            "evidence_count": 4,
            "confidence_label": "HIGH",
            "source_phase": "HIST-LONG-9",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_id": "f1_replay_60",
            "fact_type": "replay_density_fact",
            "entity_type": "theme",
            "entity_id": "accelerated compute",
            "metric_name": "replay_density",
            "metric_value": 0.75,
            "window_days": 60,
            "evidence_count": 2,
            "confidence_label": "MEDIUM",
            "source_phase": "HIST-LONG-6",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_id": "f1_fragility_60",
            "fact_type": "breadth_fragility_fact",
            "entity_type": "subsector",
            "entity_id": "consumer devices",
            "metric_name": "fragility_score",
            "metric_value": 0.42,
            "window_days": 60,
            "evidence_count": 1,
            "confidence_label": "LOW",
            "source_phase": "HIST-LONG-7",
        },
    ]


def _fact2_rows() -> list[dict]:
    return [
        {
            "phase_id": "HIST-FACT-2",
            "fact_id": "r1_topology_delta",
            "fact_type": "topology_stabilization_fact",
            "entity_type": "sector",
            "entity_id": "semiconductors",
            "metric_name": "topology_window_delta",
            "metric_value": 0.04,
            "window_days": 60,
            "evidence_count": 6,
            "confidence_label": "HIGH",
            "source_phase": "HIST-FACT-1",
            "payload_jsonb": {"dimension": "topology", "window_count": 2, "evidence_role": "regime_transition_evidence"},
        },
        {
            "phase_id": "HIST-FACT-2",
            "fact_id": "r1_transition_pressure",
            "fact_type": "transition_pressure_fact",
            "entity_type": "theme",
            "entity_id": "accelerated compute",
            "metric_name": "replay_transition_pressure",
            "metric_value": 0.18,
            "window_days": 120,
            "evidence_count": 3,
            "confidence_label": "MEDIUM",
            "source_phase": "HIST-FACT-1",
            "payload_jsonb": {"dimension": "replay", "window_count": 3, "evidence_role": "transition_readiness_evidence"},
        },
    ]


def _intel2_payload() -> dict:
    return {
        "phase_id": "HIST-INTEL-2",
        "findings": {
            "strongest_structural_anchors": [
                {"name": "semiconductors", "anchor_score": 0.91, "supporting_fact_count": 4, "confidence": "HIGH", "windows": [20, 60, 120]}
            ],
            "topology_findings": [
                {"name": "semiconductors", "topology_score": 0.87, "supporting_fact_count": 3, "confidence": "HIGH", "windows": [20, 60]}
            ],
            "replay_concentration_leaders": [
                {"name": "accelerated_compute", "replay_score": 0.73, "supporting_fact_count": 2, "confidence": "MEDIUM", "windows": [60, 120]}
            ],
            "highest_ranked_ecosystem_hubs": [],
            "cross_window_persistence_leaders": [],
            "fragility_sources": [],
            "drift_morphology_change_leaders": [],
        },
    }


def _intel3_payload() -> dict:
    return {
        "phase_id": "HIST-INTEL-3",
        "transition_diagnostics": {"candidate_transitions_found": 2, "candidate_transitions_emitted": 1, "rejected_same_state_count": 3},
        "findings": {
            "stable_long_term_narratives": [
                {
                    "narrative_id": "n_topology_stable",
                    "narrative_type": "topology",
                    "starting_state": "high",
                    "ending_state": "high",
                    "supporting_fact_count": 5,
                    "supporting_windows": [20, 60, 120],
                    "supporting_entities": ["semiconductors"],
                    "confidence_label": "HIGH",
                }
            ],
            "major_narrative_evolutions": [
                {
                    "narrative_id": "n_replay_evolving",
                    "narrative_type": "replay",
                    "starting_state": "medium",
                    "ending_state": "high",
                    "supporting_fact_count": 3,
                    "supporting_windows": [60, 120],
                    "supporting_entities": ["accelerated compute"],
                    "confidence_label": "MEDIUM",
                }
            ],
            "regime_transition_candidates": [
                {
                    "narrative_id": "n_candidate",
                    "narrative_type": "replay",
                    "transition_label": "replay_intensification",
                    "supporting_fact_count": 3,
                    "supporting_windows": [60, 120],
                    "supporting_entities": ["accelerated compute"],
                    "confidence_label": "MEDIUM",
                }
            ],
            "persistence_evolution": [],
            "replay_evolution": [],
            "concentration_evolution": [],
            "topology_evolution": [],
            "fragility_evolution": [],
        },
    }


def _build_report() -> dict:
    return build_ecosystem_intelligence_synthesis(
        fact1_path=None,
        fact2_path=None,
        intel2_path=None,
        intel3_path=None,
        observation_facts=_fact1_rows(),
        regime_evidence=_fact2_rows(),
        intel2_payload=_intel2_payload(),
        intel3_payload=_intel3_payload(),
    )


def test_deterministic_output_and_stable_synthesis_identifier():
    first = _build_report()
    second = build_ecosystem_intelligence_synthesis(
        fact1_path=None,
        fact2_path=None,
        intel2_path=None,
        intel3_path=None,
        observation_facts=copy.deepcopy(_fact1_rows()),
        regime_evidence=copy.deepcopy(_fact2_rows()),
        intel2_payload=copy.deepcopy(_intel2_payload()),
        intel3_payload=copy.deepcopy(_intel3_payload()),
    )
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)
    assert first["synthesis_id"].startswith("hist_intel4_")
    assert first["findings"]["ecosystem_characterization"]["characterization_id"].startswith("hist_intel4_")


def test_required_sections_are_evidence_backed():
    report = _build_report()
    findings = report["findings"]
    assert findings["structural_identity"]["confidence"] in {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT"}
    assert findings["dominant_historical_forces"]
    assert all(force["supporting_fact_count"] > 0 for force in findings["dominant_historical_forces"])
    assert findings["stability_assessment"]["classification"] in {"highly stable", "stable", "mixed", "unstable"}
    assert findings["transition_readiness_assessment"]["classification"] in {"low transition readiness", "moderate transition readiness", "elevated transition readiness"}
    assert findings["narrative_continuity_assessment"]["classification"] in {"fragmented narratives", "stable narratives", "evolving narratives"}
    assert findings["evidence_summary"]["eligible_evidence_count"] > 0


def test_governance_flags_present_and_no_provider_api_paths():
    report = _build_report()
    assert report["governance_certification"] == GOVERNANCE_CERTIFICATION
    assert all(report["governance_certification"].values())
    input_text = json.dumps(report["input_status"], sort_keys=True).lower()
    assert "fmp" not in input_text
    assert "api" not in input_text


def test_no_action_or_market_language_in_synthesis_statements():
    report = _build_report()
    findings = report["findings"]
    synthesis_text = " ".join(
        [
            findings["executive_synthesis"]["statement"],
            findings["structural_identity"]["statement"],
            findings["ecosystem_characterization"]["statement"],
        ]
    ).lower()
    blocked_terms = {"forecast", "price target", "buy", "sell", "trade", "portfolio allocation"}
    assert not any(term in synthesis_text for term in blocked_terms)


def test_json_and_markdown_reports_created(tmp_path: Path):
    json_path = tmp_path / "hist_intel4.json"
    md_path = tmp_path / "hist_intel4.md"
    fact1_path = tmp_path / "fact1.json"
    fact2_path = tmp_path / "fact2.json"
    intel2_path = tmp_path / "intel2.json"
    intel3_path = tmp_path / "intel3.json"
    fact1_path.write_text(json.dumps(_fact1_rows()), encoding="utf-8")
    fact2_path.write_text(json.dumps(_fact2_rows()), encoding="utf-8")
    intel2_path.write_text(json.dumps(_intel2_payload()), encoding="utf-8")
    intel3_path.write_text(json.dumps(_intel3_payload()), encoding="utf-8")

    report = run_hist_intel4(
        fact1_path=fact1_path,
        fact2_path=fact2_path,
        intel2_path=intel2_path,
        intel3_path=intel3_path,
        json_report_path=json_path,
        markdown_report_path=md_path,
    )
    assert json_path.exists()
    assert md_path.exists()
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved["synthesis_id"] == report["synthesis_id"]
    markdown = md_path.read_text(encoding="utf-8")
    for section in (
        "Executive Synthesis",
        "Structural Identity",
        "Dominant Historical Forces",
        "Stability Assessment",
        "Transition Readiness Assessment",
        "Narrative Continuity Assessment",
        "Ecosystem Characterization",
        "Evidence Summary",
        "Limitations",
    ):
        assert section in markdown
