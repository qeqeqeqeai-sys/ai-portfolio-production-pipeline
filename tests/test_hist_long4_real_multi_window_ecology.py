from __future__ import annotations

import json
from pathlib import Path

import pytest

from transmission_layers.expectation_failure.real_data.hist_long4_real_multi_window_ecology import (
    REQUIRED_WINDOWS,
    build_hist_long4_orchestration_plan,
    write_hist_long4_review,
)


def _write_completed_source(root: Path, trading_days: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    chunks = [[f"S{chunk}{idx:02d}" for idx in range(50)] for chunk in range(4)] + [["FOXA"] + [f"S5{idx:02d}" for idx in range(40)]]
    (root / "hist_density3_config_preview.json").write_text(
        json.dumps({"chunk_symbols": chunks, "chunk_plan": {"symbol_chunk_count": 5, "symbol_chunk_size": 50, "trading_days": trading_days}, "effective_symbols": sum(chunks, [])}),
        encoding="utf-8",
    )
    (root / "hist_density3_summary.json").write_text(json.dumps({"status": "ok"}), encoding="utf-8")
    for idx, symbols in enumerate(chunks, start=1):
        chunk = root / f"chunk_{idx:02d}"
        (chunk / "manifests").mkdir(parents=True, exist_ok=True)
        (chunk / "snapshots").mkdir(parents=True, exist_ok=True)
        expected = len(symbols) * trading_days
        telemetry = {
            "normalized_count": expected,
            "partial_count": 0,
            "failed_count": 0,
            "exact_date_matches": expected - idx,
            "reconciled_prior_dates": idx,
            "missing_dates": 0,
            "endpoint_status_counts": {},
            "top_failure_reasons": [],
        }
        (chunk / "manifests" / "density_summary.json").write_text(json.dumps({"density_summary": {"telemetry_summary": telemetry}}), encoding="utf-8")
        (chunk / "snapshots" / "ops_hist1_2026-05-28.json").write_text(
            json.dumps({"snapshot_date": "2026-05-28", "posture": "balanced", "operational_diagnostics": {"sector_hhi": 0.1, "normalization_completeness": 1.0, "symbols_successfully_normalized": len(symbols)}, "canonical_payloads": {"sector_transition_rows": [{"sector": "x"}]}}),
            encoding="utf-8",
        )


def _review_for(source_root: str) -> dict:
    root = Path(source_root)
    preview = json.loads((root / "hist_density3_config_preview.json").read_text(encoding="utf-8"))
    trading_days = int(preview["chunk_plan"]["trading_days"])
    rows = []
    for idx, symbols in enumerate(preview["chunk_symbols"], start=1):
        expected = len(symbols) * trading_days
        rows.append({
            "chunk_index": idx,
            "chunk_symbol_count": len(symbols),
            "chunk_symbols": symbols,
            "normalized_count": expected,
            "partial_count": 0,
            "failed_count": 0,
            "exact_date_matches": expected - idx,
            "reconciled_prior_dates": idx,
            "missing_dates": 0,
            "expected_symbol_date_rows": expected,
            "normalization_density": 1.0,
            "endpoint_status_counts": {},
            "top_failure_reasons": [],
        })
    return {
        "source_status": "ok",
        "source_mode": "completed_summary",
        "completed_telemetry_mode": True,
        "source_artifacts_inspected": {"ops_hist_snapshot_count": 5},
        "ingestion_quality": {
            "chunk_quality_rows": rows,
            "aggregate": {
                "chunk_count": 5,
                "effective_symbol_count": 241,
                "configured_symbol_count": 241,
                "trading_days": trading_days,
                "requested_symbol_date_capacity_total": 241 * trading_days,
                "normalized_count_total": 241 * trading_days,
                "partial_count_total": 0,
                "failed_count_total": 0,
                "missing_dates_total": 0,
                "exact_date_matches_total": 241 * trading_days - 15,
                "reconciled_prior_dates_total": 15,
                "endpoint_failures": {},
                "top_failure_reasons": [],
            },
        },
        "weak_symbol_review": [],
        "first_ecology_findings": {"monoculture_risk": "Low observed chunk monoculture risk; density spread is bounded.", "ops_hist_surface_counts": {"topology_reports": 3}},
        "ecology_findings": {
            "snapshot_count": 5,
            "posture_stability": "stable_single_posture",
            "posture_counts": {"balanced": 5},
            "temporal_stability_days": trading_days,
            "chunk_diagnostics": [{"chunk_index": idx, "sector_hhi_average": 0.1, "structural_richness": {"sector_transition_rows": 1, "posture_variety": 1}, "preflight_failure_symbols": []} for idx in range(1, 6)],
        },
        "chunk_comparison": {"dominant_chunk": None, "richest_chunks": []},
    }


def test_hist_long4_writes_completed_review_and_bundles(tmp_path):
    output_root = tmp_path / "reports" / "hist_long4_windows"

    def runner(**kwargs):
        _write_completed_source(Path(kwargs["output_root"]), int(kwargs["trading_days"]))
        assert kwargs["density_mode"] == "real_ops_hist1"
        assert kwargs["raw_cache_write_enabled"] is False
        assert kwargs["include_high_risk_symbols"] is False
        return {"status": "ok"}

    artifact = write_hist_long4_review(
        output_root=str(output_root),
        report_path=str(tmp_path / "reports" / "hist_long4_real_multi_window_ecology_review.md"),
        artifact_path=str(tmp_path / "artifacts" / "hist_long4_real_multi_window_ecology_review.json"),
        density_runner=runner,
        review_builder=_review_for,
        bundle_artifact_dir=str(tmp_path / "artifacts"),
    )

    assert artifact["status"] == "ok"
    assert artifact["all_three_real_windows_completed"] is True
    assert [row["normalized_rows"] for row in artifact["window_level_results"]] == [4820, 14460, 28920]
    assert artifact["longitudinal_comparison"]["weak_symbol_analysis"]["foxa_stability"]["assessment"] == "stable_not_weak"
    assert artifact["bounded_diagnostics"]["replay_persistence_trend"] == "stable"
    assert all(Path(row["completed_bundle_path"]).exists() for row in artifact["completed_artifact_bundles"])


def test_hist_long4_fail_closed_guards():
    with pytest.raises(ValueError, match="windows must be exactly"):
        build_hist_long4_orchestration_plan(windows=(20, 60))
    with pytest.raises(ValueError, match="max_symbols"):
        build_hist_long4_orchestration_plan(max_symbols=242)
    with pytest.raises(ValueError, match="Supabase writes"):
        build_hist_long4_orchestration_plan(supabase_write_enabled=True)
    with pytest.raises(ValueError, match="raw cache writes"):
        build_hist_long4_orchestration_plan(raw_cache_write_enabled=True)
    assert build_hist_long4_orchestration_plan()["windows"] == list(REQUIRED_WINDOWS)
