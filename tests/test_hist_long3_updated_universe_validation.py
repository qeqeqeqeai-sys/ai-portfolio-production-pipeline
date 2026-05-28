from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.hist_long3_updated_universe_validation import write_hist_long3_validation


def _write_preview(output_root: str) -> None:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    chunks = [[f"SYM{i:03d}" for i in range(50)], [f"S2{i:03d}" for i in range(50)], [f"S3{i:03d}" for i in range(50)], [f"S4{i:03d}" for i in range(50)], ["FOXA"] + [f"S5{i:03d}" for i in range(40)]]
    (root / "hist_density3_config_preview.json").write_text(json.dumps({"chunk_symbols": chunks, "chunk_plan": {"symbol_chunk_count": 5, "symbol_chunk_size": 50, "trading_days": 20}}), encoding="utf-8")


def test_hist_long3_writes_blocked_artifact_with_universe_guards(tmp_path):
    output_root = tmp_path / "reports" / "hist_long3_updated_universe_validation"

    def blocked_runner(**kwargs):
        _write_preview(str(output_root))
        raise RuntimeError("FMP_API_KEY missing; OPS-HIST-1 fails closed")

    artifact = write_hist_long3_validation(
        output_root=str(output_root),
        report_path=str(tmp_path / "reports" / "hist_long3_updated_universe_validation.md"),
        artifact_path=str(tmp_path / "artifacts" / "hist_long3_updated_universe_validation.json"),
        density_runner=blocked_runner,
    )

    assert artifact["status"] == "blocked_provider_credentials_missing_or_execution_failed"
    assert artifact["updated_universe_validation"]["foxa_present_exactly_once"] is True
    assert artifact["updated_universe_validation"]["para_absent"] is True
    assert artifact["updated_universe_validation"]["no_duplicate_symbols"] is True
    assert artifact["updated_universe_validation"]["expected_chunk_count_remains_5"] is True
    assert artifact["governance_certification"]["supabase_write_enabled"] is False
    assert artifact["governance_certification"]["raw_cache_write_enabled"] is False
    assert Path(tmp_path / "reports" / "hist_long3_updated_universe_validation.md").exists()
    assert Path(tmp_path / "artifacts" / "hist_long3_updated_universe_validation.json").exists()


def test_hist_long3_completed_comparison_and_foxa_assessment(tmp_path):
    output_root = tmp_path / "reports" / "hist_long3_updated_universe_validation"

    def completed_runner(**kwargs):
        _write_preview(str(output_root))
        (output_root / "hist_density3_summary.json").write_text(json.dumps({"status": "ok"}), encoding="utf-8")
        return {"status": "ok"}

    def review_builder(source_root: str):
        return {
            "source_artifacts_inspected": {"ops_hist_snapshot_count": 100},
            "ingestion_quality": {
                "chunk_quality_rows": [
                    {"chunk_index": 1, "chunk_symbols": ["FOXA"], "top_failure_reasons": []},
                ],
                "aggregate": {
                    "requested_symbol_date_capacity_total": 4820,
                    "normalized_count_total": 4820,
                    "partial_count_total": 0,
                    "failed_count_total": 0,
                    "exact_date_matches_total": 4800,
                    "reconciled_prior_dates_total": 20,
                    "endpoint_failures": {},
                    "top_failure_reasons": [],
                },
            },
            "weak_symbol_review": [],
            "ecology_findings": {"chunk_diagnostics": []},
        }

    artifact = write_hist_long3_validation(
        output_root=str(output_root),
        report_path=str(tmp_path / "reports" / "hist_long3_updated_universe_validation.md"),
        artifact_path=str(tmp_path / "artifacts" / "hist_long3_updated_universe_validation.json"),
        density_runner=completed_runner,
        review_builder=review_builder,
    )

    assert artifact["status"] == "ok"
    assert artifact["foxa_validation"]["status"] == "validated_suitable"
    assert artifact["comparison_vs_para_baseline"]["did_weak_symbol_disappear"] is True
    assert artifact["comparison_vs_para_baseline"]["did_provider_degradation_improve"] is True
    assert artifact["comparison_vs_para_baseline"]["did_completeness_improve"] is True
    assert artifact["hist_long4_justified"] is True
