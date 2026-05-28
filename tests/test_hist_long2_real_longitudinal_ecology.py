from __future__ import annotations

import json
from pathlib import Path

import pytest

from transmission_layers.expectation_failure.real_data.hist_long2_real_longitudinal_ecology import (
    build_hist_long2_artifact,
    build_hist_long2_comparison,
    build_hist_long2_orchestration_plan,
    render_hist_long2_markdown,
    write_hist_long2_review,
)


def _review(*, window: int = 20, normalized: int = 4700, capacity: int = 4820, weak: list[str] | None = None, completed: bool = True) -> dict:
    weak = weak or []
    chunk_capacity = [1000, 1000, 1000, 1000, capacity - 4000]
    chunk_norm = [980, 920, 1000, 1000, normalized - 3900]
    chunks = []
    for idx, (cap, norm) in enumerate(zip(chunk_capacity, chunk_norm, strict=True), start=1):
        chunks.append({
            "chunk_index": idx,
            "chunk_symbol_count": 50 if idx < 5 else 41,
            "expected_symbol_date_rows": cap,
            "normalized_count": norm,
            "partial_count": 0 if idx < 5 else (20 if weak else 0),
            "failed_count": 0 if idx < 5 else (20 if weak else 0),
            "exact_date_matches": int(norm * 0.95),
            "reconciled_prior_dates": norm - int(norm * 0.95),
            "missing_dates": 0 if idx < 5 else (20 if weak else 0),
            "endpoint_status_counts": {"HTTP_403": 20, "zero_records_returned": 20} if idx == 5 and weak else {"stable_historical_price_eod_full": norm},
            "top_failure_reasons": [{"reason": "HTTP_403", "count": 20}, {"reason": "zero_records_returned", "count": 20}] if idx == 5 and weak else [],
            "normalization_density": round(norm / cap, 6),
            "chunk_symbols": ["FOXA"] if idx == 5 and "FOXA" not in weak else weak,
        })
    return {
        "source_status": "ok",
        "source_mode": "completed_summary",
        "completed_telemetry_mode": completed,
        "source_artifacts_inspected": {"chunk_manifest_count": 5, "ops_hist_snapshot_count": window * 5},
        "ingestion_quality": {
            "chunk_quality_rows": chunks,
            "aggregate": {
                "chunk_count": 5,
                "configured_symbol_count": 241,
                "effective_symbol_count": 241,
                "trading_days": window,
                "estimated_symbol_date_rows": capacity,
                "requested_symbol_date_capacity_total": capacity,
                "normalized_count_total": normalized,
                "partial_count_total": 20 if weak else 0,
                "failed_count_total": 20 if weak else 0,
                "missing_dates_total": 20 if weak else 0,
                "exact_date_matches_total": int(normalized * 0.95),
                "reconciled_prior_dates_total": normalized - int(normalized * 0.95),
                "endpoint_failures": {"HTTP_403": 20, "zero_records_returned": 20} if weak else {},
                "top_failure_reasons": [{"reason": "HTTP_403", "count": 20}, {"reason": "zero_records_returned", "count": 20}] if weak else [],
            },
        },
        "weak_symbol_review": [{"symbol": symbol, "missing_sample_count": 20, "endpoint_failure_sample_count": 20, "observed_reasons": [{"reason": "HTTP_403", "count": 20}]} for symbol in weak],
        "ecology_findings": {
            "snapshot_count": window * 5,
            "temporal_stability_days": window,
            "posture_stability": "stable_single_posture",
            "posture_counts": {"pressure_building": window * 5},
            "chunk_diagnostics": [
                {"chunk_index": idx, "sector_hhi_average": 0.2 + idx / 100, "structural_richness": {"sector_transition_rows": 1, "posture_variety": 1}}
                for idx in range(1, 6)
            ],
        },
        "first_ecology_findings": {"monoculture_risk": "Low observed chunk monoculture risk; density spread is bounded."},
    }


def _write_review(path: Path, review: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")


def test_completed_artifact_parsing_and_weak_symbol_recurrence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    first = tmp_path / "artifacts" / "review20.json"
    second = tmp_path / "artifacts" / "review60.json"
    _write_review(first, _review(window=20, weak=["PARA"]))
    _write_review(second, _review(window=60, normalized=14400, capacity=14460, weak=["PARA", "NWSA"]))
    artifact = write_hist_long2_review(
        windows=(20, 60),
        completed_sources=(
            {"window_days": 20, "label": "w20", "artifact_path": str(first)},
            {"window_days": 60, "label": "w60", "artifact_path": str(second)},
        ),
        report_path="reports/hist_long2_real_longitudinal_ecology_review.md",
        artifact_path="artifacts/hist_long2_real_longitudinal_ecology_review.json",
    )
    assert artifact["real_completed_telemetry_used"] is True
    assert artifact["new_real_execution_run"] is False
    assert artifact["longitudinal_comparison_summary"]["weak_symbol_recurrence"][0] == {"symbol": "PARA", "window_count": 2}
    assert Path("reports/hist_long2_real_longitudinal_ecology_review.md").exists()


def test_real_vs_fixture_mode_distinction(tmp_path):
    fixture = tmp_path / "fixture.json"
    _write_review(fixture, _review(normalized=0, capacity=4820, completed=True))
    plan = build_hist_long2_orchestration_plan(windows=(20,), end_date="2026-05-28")
    artifact = build_hist_long2_artifact(plan=plan, sources=({"window_days": 20, "label": "fixture_like", "artifact_path": str(fixture)},))
    assert artifact["real_completed_telemetry_used"] is False
    assert artifact["status"] == "blocked_no_real_completed_telemetry"


def test_fail_closed_guardrails():
    with pytest.raises(ValueError):
        build_hist_long2_orchestration_plan(windows=(181,))
    with pytest.raises(ValueError):
        build_hist_long2_orchestration_plan(windows=(20,), max_symbols=242)
    with pytest.raises(ValueError):
        build_hist_long2_orchestration_plan(windows=(20,), expected_chunk_count=4)
    with pytest.raises(ValueError):
        build_hist_long2_orchestration_plan(windows=(20,), supabase_write_enabled=True)
    with pytest.raises(ValueError):
        build_hist_long2_orchestration_plan(windows=(20,), replay_activation_enabled=True)
    with pytest.raises(ValueError):
        build_hist_long2_orchestration_plan(windows=(20,), topology_persistence_enabled=True)


def test_deterministic_comparison_output():
    rows = [
        {"window_trading_days": 20, "label": "a", "normalized_rows": 4700, "replay_density": 0.975104, "weak_symbols": ["PARA"], "provider_degradation": {"top_failure_reasons": [{"reason": "HTTP_403", "count": 20}]}, "morphology_persistence": {"posture_stability": "stable_single_posture"}, "historical_date_alignment": {"exact_date_ratio": 0.95, "reconciled_date_ratio": 0.05}, "sector_hhi": {"drift_proxy": 0.1}, "subsector_hhi": {"drift_proxy": 0.1}, "contradiction_persistence": {"burden_ratio": 0.01}, "topology_richness": {"chunk_richness_average": 2}},
        {"window_trading_days": 60, "label": "b", "normalized_rows": 14400, "replay_density": 0.995851, "weak_symbols": ["PARA"], "provider_degradation": {"top_failure_reasons": [{"reason": "HTTP_403", "count": 20}]}, "morphology_persistence": {"posture_stability": "stable_single_posture"}, "historical_date_alignment": {"exact_date_ratio": 0.96, "reconciled_date_ratio": 0.04}, "sector_hhi": {"drift_proxy": 0.1}, "subsector_hhi": {"drift_proxy": 0.1}, "contradiction_persistence": {"burden_ratio": 0.005}, "topology_richness": {"chunk_richness_average": 2}},
    ]
    assert build_hist_long2_comparison(rows) == build_hist_long2_comparison(list(reversed(rows)))


def test_governance_preservation_and_markdown_sections(tmp_path):
    review_path = tmp_path / "review.json"
    _write_review(review_path, _review(weak=[]))
    plan = build_hist_long2_orchestration_plan(windows=(20,), end_date="2026-05-28")
    artifact = build_hist_long2_artifact(plan=plan, sources=({"window_days": 20, "label": "w20", "artifact_path": str(review_path)},))
    gov = artifact["governance_certification"]
    assert gov["prediction_enabled"] is False
    assert gov["trading_execution_enabled"] is False
    assert gov["replay_activation_enabled"] is False
    assert gov["topology_persistence_enabled"] is False
    assert gov["supabase_write_enabled"] is False
    md = render_hist_long2_markdown(artifact)
    assert "## Governance Certification" in md
    assert "## Recommendation for next phase" in md
