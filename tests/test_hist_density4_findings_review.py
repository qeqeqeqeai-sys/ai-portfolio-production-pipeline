from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.hist_density4_findings_review import (
    build_hist_density4_findings_review,
    render_hist_density4_markdown,
    write_hist_density4_findings_review,
)


def _write_completed_density3(root: Path) -> None:
    root.mkdir(parents=True)
    payload = {
        "status": "ok",
        "ops_hist_artifact_summary": {
            "chunk_results": [
                {
                    "chunk_index": 1,
                    "chunk_symbol_count": 2,
                    "chunk_symbols": ["AAA", "BBB"],
                    "telemetry": {
                        "resolved_trading_days": 2,
                        "normalized_count": 4,
                        "partial_count": 0,
                        "failed_count": 0,
                        "exact_date_matches": 4,
                        "reconciled_prior_dates": 0,
                        "missing_dates": 0,
                        "endpoint_status_counts": {"ok": 4},
                    },
                    "missing_record_samples": [],
                    "endpoint_failure_samples": [],
                },
                {
                    "chunk_index": 2,
                    "chunk_symbol_count": 1,
                    "chunk_symbols": ["CCC"],
                    "telemetry": {
                        "resolved_trading_days": 2,
                        "normalized_count": 1,
                        "partial_count": 1,
                        "failed_count": 0,
                        "exact_date_matches": 1,
                        "reconciled_prior_dates": 0,
                        "missing_dates": 1,
                        "endpoint_status_counts": {"HTTP_403": 1},
                    },
                    "missing_record_samples": [{"symbol": "CCC", "requested_snapshot_date": "2026-05-27", "reason": "zero_records_returned"}],
                    "endpoint_failure_samples": [{"symbol": "CCC", "requested_snapshot_date": "2026-05-27", "status": "HTTP_403"}],
                },
            ]
        },
    }
    (root / "hist_density3_summary.json").write_text(json.dumps(payload), encoding="utf-8")


def test_completed_density3_review_extracts_chunk_quality_and_weak_symbols(tmp_path, monkeypatch):
    source = tmp_path / "hist_density3_curated_241"
    _write_completed_density3(source)
    monkeypatch.chdir(tmp_path)
    artifact = build_hist_density4_findings_review(source_root=str(source))
    assert artifact["status"] == "ok"
    assert artifact["source_mode"] == "completed_summary"
    assert artifact["ingestion_quality"]["aggregate"]["configured_symbol_count"] == 3
    assert artifact["ingestion_quality"]["aggregate"]["endpoint_failures"] == {"HTTP_403": 1}
    assert artifact["weak_symbol_review"][0]["symbol"] == "CCC"
    assert artifact["weak_symbol_review"][0]["replacement_review_later"] is True
    assert artifact["chunk_comparison"]["richest_chunks"][0]["chunk_index"] == 1


def test_config_preview_fallback_is_deterministic(tmp_path, monkeypatch):
    source = tmp_path / "preview"
    source.mkdir()
    (source / "hist_density3_config_preview.json").write_text(json.dumps({
        "schema_version": "hist_density3_v1",
        "chunk_plan": {"trading_days": 20},
        "chunk_symbols": [["AAA", "BBB"], ["CCC"]],
        "governance_certification": {"governance_mode": "observational_only"},
    }), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    out1 = build_hist_density4_findings_review(source_root=str(source))
    out2 = build_hist_density4_findings_review(source_root=str(source))
    assert out1 == out2
    assert out1["source_mode"] == "config_preview_only"
    assert out1["ingestion_quality"]["chunk_quality_rows"][0]["normalized_count"] is None
    assert out1["ingestion_quality"]["aggregate"]["configured_symbol_count"] == 3


def test_writer_outputs_markdown_json_and_governance(tmp_path, monkeypatch):
    source = tmp_path / "hist_density3_curated_241"
    _write_completed_density3(source)
    monkeypatch.chdir(tmp_path)
    report_path = tmp_path / "reports" / "hist_density4_241_symbol_findings_review.md"
    artifact_path = tmp_path / "artifacts" / "hist_density4_241_symbol_findings_review.json"
    artifact = write_hist_density4_findings_review(source_root=str(source), report_path=str(report_path), artifact_path=str(artifact_path))
    md = render_hist_density4_markdown(artifact)
    assert report_path.exists()
    assert artifact_path.exists()
    assert "## Governance Confirmation" in md
    g = artifact["governance_certification"]
    assert g["new_ingestion_enabled"] is False
    assert g["replay_activation_enabled"] is False
    assert g["supabase_write_enabled"] is False
    assert g["topology_persistence_enabled"] is False
    assert g["trading_execution_enabled"] is False
