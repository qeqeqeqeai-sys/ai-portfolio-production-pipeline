from __future__ import annotations

import json
from pathlib import Path

import pytest

from transmission_layers.expectation_failure.real_data.hist_long1_longitudinal_ecology import (
    build_hist_long1_artifact,
    build_hist_long1_orchestration_plan,
    build_longitudinal_comparison,
    render_hist_long1_markdown,
    write_hist_long1_review,
)


def _review(window: int, *, weak: list[str] | None = None, failures: dict[str, int] | None = None, density: float = 1.0) -> dict:
    weak = weak or []
    failures = failures or {}
    capacity = 241 * window
    normalized = int(capacity * density)
    chunk_rows = []
    sizes = [50, 50, 50, 50, 41]
    for idx, size in enumerate(sizes, start=1):
        expected = size * window
        chunk_rows.append({
            "chunk_index": idx,
            "chunk_symbol_count": size,
            "expected_symbol_date_rows": expected,
            "normalized_count": int(expected * density),
            "partial_count": 0,
            "failed_count": 0,
            "exact_date_matches": int(expected * density),
            "reconciled_prior_dates": 0,
            "missing_dates": expected - int(expected * density),
            "affected_symbol_count": 1 if weak else 0,
            "affected_date_count": window if weak else 0,
            "endpoint_status_counts": failures,
            "normalization_density": density,
            "top_failure_reasons": [{"reason": k, "count": v} for k, v in failures.items()],
        })
    return {
        "source_status": "ok",
        "completed_telemetry_mode": True,
        "ingestion_quality": {
            "chunk_quality_rows": chunk_rows,
            "aggregate": {
                "chunk_count": 5,
                "configured_symbol_count": 241,
                "effective_symbol_count": 241,
                "estimated_symbol_date_rows": capacity,
                "requested_symbol_date_capacity_total": capacity,
                "normalized_count_total": normalized,
                "partial_count_total": 0,
                "failed_count_total": 0,
                "missing_dates_total": capacity - normalized,
                "endpoint_failures": failures,
                "top_failure_reasons": [{"reason": k, "count": v} for k, v in failures.items()],
            },
        },
        "weak_symbol_review": [{"symbol": symbol, "missing_sample_count": 1, "endpoint_failure_sample_count": 1} for symbol in weak],
        "ecology_findings": {
            "normalization_completeness_range": {"min": density * 100, "max": density * 100},
            "sector_hhi_range": {"min": 0.12, "max": 0.14},
            "temporal_stability_days": window,
            "posture_stability": "stable_single_posture",
            "posture_counts": {"pressure_building": window},
            "chunk_diagnostics": [
                {"structural_richness": {"sector_transition_rows": 3, "posture_variety": 1}}
                for _ in range(5)
            ],
        },
        "chunk_comparison": {
            "dominant_chunk": {"chunk_index": 1},
            "richest_chunks": [{"chunk_index": 1}],
        },
    }


def test_longitudinal_comparison_is_deterministic():
    plan = build_hist_long1_orchestration_plan(windows=(20, 60, 120), end_date="2026-05-28")
    reviews = [
        _review(20, weak=["FOXA"], failures={"HTTP_403": 1}, density=1.0),
        _review(60, weak=["FOXA", "NWSA"], failures={"HTTP_403": 2}, density=1.0),
        _review(120, weak=["FOXA"], failures={"HTTP_403": 3}, density=1.0),
    ]
    first = build_hist_long1_artifact(plan=plan, window_reviews=reviews, source_roots=["a", "b", "c"])
    second = build_hist_long1_artifact(plan=plan, window_reviews=reviews, source_roots=["a", "b", "c"])
    assert first == second
    assert first["longitudinal_comparison_summary"]["weak_symbol_recurrence"][0] == {"symbol": "FOXA", "window_count": 3}
    assert first["longitudinal_comparison_summary"]["replay_density"]["trend"] == "stable"


def test_bounded_window_orchestration_fails_closed():
    plan = build_hist_long1_orchestration_plan(windows=(20, 60, 120), max_symbols=241, chunk_size=50, end_date="2026-05-28")
    assert plan["expected_chunk_count"] == 5
    assert plan["governance_certification"]["supabase_write_enabled"] is False
    with pytest.raises(ValueError):
        build_hist_long1_orchestration_plan(windows=(20,), max_symbols=242)
    with pytest.raises(ValueError):
        build_hist_long1_orchestration_plan(windows=(20,), chunk_size=51)
    with pytest.raises(ValueError):
        build_hist_long1_orchestration_plan(windows=(181,))


def test_governance_preservation_and_markdown_sections():
    plan = build_hist_long1_orchestration_plan(windows=(20,), end_date="2026-05-28")
    artifact = build_hist_long1_artifact(plan=plan, window_reviews=[_review(20)], source_roots=["window_020d"])
    governance = artifact["governance_certification"]
    assert governance["prediction_enabled"] is False
    assert governance["trading_execution_enabled"] is False
    assert governance["replay_activation_enabled"] is False
    assert governance["topology_persistence_enabled"] is False
    assert governance["supabase_write_enabled"] is False
    md = render_hist_long1_markdown(artifact)
    assert "## Operational Stability" in md
    assert "## Readiness Assessment" in md


def test_stable_artifact_generation_with_injected_runners(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_density_runner(**kwargs):
        calls.append(kwargs)
        root = Path(kwargs["output_root"])
        root.mkdir(parents=True, exist_ok=True)
        return {"status": "ok"}

    def fake_review_builder(source_root: str):
        window = int(Path(source_root).name.split("_")[1].removesuffix("d"))
        return _review(window, weak=["FOXA"] if window >= 60 else [], failures={"HTTP_403": 1} if window >= 60 else {}, density=1.0)

    artifact = write_hist_long1_review(
        windows=(20, 60),
        output_root="reports/windows",
        end_date="2026-05-28",
        report_path="reports/hist_long1_longitudinal_ecology_review.md",
        artifact_path="artifacts/hist_long1_longitudinal_ecology_review.json",
        density_runner=fake_density_runner,
        review_builder=fake_review_builder,
    )
    assert len(calls) == 2
    assert all(call["max_symbols"] == 241 and call["symbol_chunk_size"] == 50 for call in calls)
    assert Path("reports/hist_long1_longitudinal_ecology_review.md").exists()
    saved = json.loads(Path("artifacts/hist_long1_longitudinal_ecology_review.json").read_text(encoding="utf-8"))
    assert saved["artifact_checksum"] == artifact["artifact_checksum"]
    assert saved["bounded_telemetry"]["chunk_consistency_metrics"]["consistent"] is True
