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
    (root / "hist_density3_summary.md").write_text("# completed summary\n", encoding="utf-8")
    (root / "hist_density3_config_preview.json").write_text(json.dumps({
        "schema_version": "hist_density3_v1",
        "effective_symbols": ["AAA", "BBB", "CCC"],
        "estimated_symbol_date_rows": 6,
        "chunk_plan": {"trading_days": 2},
        "chunk_symbols": [["AAA", "BBB"], ["CCC"]],
    }), encoding="utf-8")
    for chunk in payload["ops_hist_artifact_summary"]["chunk_results"]:
        manifest_dir = root / f"chunk_{chunk['chunk_index']:02d}" / "manifests"
        manifest_dir.mkdir(parents=True)
        (manifest_dir / "density_summary.json").write_text(json.dumps({
            "status": "ok",
            "density_summary": {
                "symbol_count": chunk["chunk_symbol_count"],
                "telemetry_summary": {
                    **chunk["telemetry"],
                    "missing_record_samples": chunk.get("missing_record_samples", []),
                    "endpoint_failure_samples": chunk.get("endpoint_failure_samples", []),
                    "top_failure_reasons": [{"reason": "HTTP_403", "count": 1}] if chunk["chunk_index"] == 2 else [],
                    "affected_symbol_count": 1 if chunk["chunk_index"] == 2 else 0,
                    "affected_date_count": 1 if chunk["chunk_index"] == 2 else 0,
                },
            },
        }), encoding="utf-8")
        snapshot_dir = root / f"chunk_{chunk['chunk_index']:02d}" / "snapshots"
        snapshot_dir.mkdir(parents=True)
        (snapshot_dir / "ops_hist1_2026-05-27.json").write_text(json.dumps({
            "snapshot_date": "2026-05-27",
            "posture": "pressure_building",
            "operational_diagnostics": {
                "sector_hhi": 0.25 + chunk["chunk_index"] / 100,
                "normalization_completeness": 100.0 if chunk["chunk_index"] == 1 else 50.0,
                "symbols_successfully_normalized": chunk["telemetry"]["normalized_count"],
            },
            "canonical_payloads": {"sector_transition_rows": [{"sector_hhi": 0.25}]},
            "adapter_diagnostics": {"historical_market_cap_endpoint_status": "degraded"},
        }), encoding="utf-8")


def test_completed_density3_review_extracts_chunk_quality_and_weak_symbols(tmp_path, monkeypatch):
    source = tmp_path / "hist_density3_curated_241"
    _write_completed_density3(source)
    monkeypatch.chdir(tmp_path)
    artifact = build_hist_density4_findings_review(source_root=str(source))
    assert artifact["status"] == "ok"
    assert artifact["source_mode"] == "completed_summary"
    assert artifact["completed_telemetry_mode"] is True
    assert artifact["source_artifacts_inspected"]["chunk_manifest_count"] == 2
    assert artifact["ingestion_quality"]["aggregate"]["configured_symbol_count"] == 3
    assert artifact["ingestion_quality"]["aggregate"]["endpoint_failures"] == {"HTTP_403": 1}
    assert artifact["ingestion_quality"]["aggregate"]["top_failure_reasons"] == [{"reason": "HTTP_403", "count": 1}]
    assert artifact["weak_symbol_review"][0]["symbol"] == "CCC"
    assert artifact["weak_symbol_review"][0]["replacement_review_later"] is True
    assert artifact["ecology_findings"]["snapshot_count"] == 2
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


def test_completed_density3_review_extracts_para_from_real_bundle(monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    artifact = build_hist_density4_findings_review(source_root="temp/hist-density3-curated-241-reports.zip")
    assert artifact["completed_telemetry_mode"] is True
    assert artifact["source_mode"] == "completed_artifact_bundle"
    assert artifact["ingestion_quality"]["aggregate"]["effective_symbol_count"] == 241
    assert artifact["ingestion_quality"]["aggregate"]["chunk_count"] == 5
    assert artifact["ingestion_quality"]["aggregate"]["trading_days"] == 20
    assert artifact["ingestion_quality"]["aggregate"]["estimated_symbol_date_rows"] == 4820
    assert [row["normalized_count"] for row in artifact["ingestion_quality"]["chunk_quality_rows"]] == [980, 920, 1000, 1000, 800]
    assert artifact["weak_symbol_review"][0]["symbol"] == "PARA"
    assert {reason["reason"] for reason in artifact["weak_symbol_review"][0]["observed_reasons"]} >= {"HTTP_403", "zero_records_returned"}
    assert artifact["ingestion_quality"]["aggregate"]["affected_symbol_count"] == 1
    assert artifact["ingestion_quality"]["aggregate"]["affected_date_count"] == 20
    assert artifact["chunk_comparison"]["richest_chunks"][0]["chunk_index"] == 3
    assert artifact["chunk_comparison"]["richest_chunks"][1]["chunk_index"] == 4
    assert artifact["governance_certification"]["supabase_write_enabled"] is False


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
