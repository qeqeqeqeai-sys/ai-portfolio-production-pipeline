from __future__ import annotations

import json

from transmission_layers.expectation_failure.review.hist_review1_longitudinal_ecology_review import (
    build_hist_review1_summary,
    render_hist_review1_markdown,
    run_hist_review1,
)


def _sample_hist7() -> dict:
    return {
        "saturation_scorecard": {
            "artifact_count": 4,
            "continuity_crowding_class": "moderate_continuity_crowding",
            "structural_density_class": "moderate_structural_density",
            "topology_concentration_class": "concentrated_topology",
            "morphology_diversity_class": "diversified_morphology",
            "ecology_saturation_class": "high_ecology_saturation",
        },
        "saturation_observation_summary": {
            "saturation_observation_notes": [
                "Saturation observed from morphology artifacts only.",
                "No replay activation or topology activation observed.",
            ]
        },
        "saturation_evidence_records": [
            {"artifact_id": "A", "regime_morphology_class": "alpha", "transition_shape_class": "ts1", "fragmentation_propagation_class": "low_fragmentation_propagation"},
            {"artifact_id": "A", "regime_morphology_class": "alpha", "transition_shape_class": "ts1", "fragmentation_propagation_class": "low_fragmentation_propagation"},
            {"artifact_id": "B", "regime_morphology_class": "beta", "transition_shape_class": "ts2", "fragmentation_propagation_class": "high_fragmentation_propagation"},
            {"artifact_id": "C", "regime_morphology_class": "gamma", "transition_shape_class": "ts1", "fragmentation_propagation_class": "moderate_fragmentation_propagation"},
        ],
    }


def test_hist_review1_summary_sections_and_metrics() -> None:
    summary = build_hist_review1_summary(_sample_hist7())
    for key in [
        "governance_certification", "review_metrics", "continuity_review",
        "recurrence_ecology_review", "morphology_review", "saturation_review",
        "temporal_evolution_review", "bounded_narratives",
    ]:
        assert key in summary
    assert set(summary["review_metrics"].keys()) == {
        "topology_concentration_ratio",
        "morphology_diversity_ratio",
        "recurrence_density_ratio",
        "continuity_density_ratio",
        "saturation_pressure_ratio",
    }


def test_hist_review1_determinism_excluding_timestamp() -> None:
    left = build_hist_review1_summary(_sample_hist7())
    right = build_hist_review1_summary(_sample_hist7())
    left["execution_metadata"].pop("generated_at_utc", None)
    right["execution_metadata"].pop("generated_at_utc", None)
    assert left == right


def test_hist_review1_bounded_outputs_and_safe_vocabulary(tmp_path) -> None:
    out = run_hist_review1(_sample_hist7(), output_root=str(tmp_path / "hist_review1"))
    blob = json.dumps(
        {
            "bounded_narratives": out["bounded_narratives"],
            "observational_findings": out["observational_findings"],
            "next_phase_recommendations": out["next_phase_recommendations"],
        }
    ).lower()
    for term in ["predict", "trade", "buy", "sell", "activate replay", "orchestrate autonomously"]:
        assert term not in blob
    assert len(out["bounded_narratives"]) <= 12
    assert len(json.dumps(out)) < 120_000
    assert (tmp_path / "hist_review1" / "hist_review1_summary.json").exists()
    assert (tmp_path / "hist_review1" / "hist_review1_summary.md").exists()


def test_hist_review1_markdown_sections() -> None:
    md = render_hist_review1_markdown(build_hist_review1_summary(_sample_hist7()))
    assert "## Continuity Review" in md
    assert "## Recurrence Ecology Review" in md
    assert "## Morphology Review" in md
    assert "## Saturation Review" in md
