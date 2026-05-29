from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.hist_long5b_temporal_delta_sensitivity_classification import (
    COMPLETED_SOURCE_ARTIFACT_ENV,
    build_hist_long5b,
    write_hist_long5b,
)


def _window(days: int, *, normalized: int | None = None, replay: float = 0.9, sector_hhi: float = 0.1, weak_symbols: list[str] | None = None, provider_failures: dict[str, int] | None = None, foxa_present: bool = True, foxa_weak: bool = False) -> dict:
    normalized = normalized if normalized is not None else days * 100
    return {
        "window_trading_days": days,
        "source_status": "ok",
        "completed_telemetry_mode": True,
        "normalized_rows": normalized,
        "completeness": 1.0,
        "partial_count": 0,
        "failed_count": 0,
        "exact_date_ratio": 1.0,
        "reconciled_date_ratio": 0.0,
        "endpoint_failures": provider_failures or {},
        "replay_density": replay,
        "replay_saturation": {"density": replay},
        "contradiction_burden": {"ratio": 0.0},
        "topology_richness": {"chunk_richness_average": 10.0},
        "morphology_persistence": {"score": 1.0},
        "temporal_persistence": {"score": 1.0},
        "sector_hhi": {"universe_hhi": sector_hhi},
        "subsector_hhi": {"universe_hhi": sector_hhi + 0.01},
        "monoculture_risk_score": 0.0,
        "diversity_retention_score": 1.0,
        "weak_symbols": weak_symbols or [],
        "foxa_present": foxa_present,
        "foxa_weak": foxa_weak,
    }


def _completed_hist_long4(windows: list[dict] | None = None, governance: dict | None = None) -> dict:
    base_governance = {
        "prediction_enabled": False,
        "trading_execution_enabled": False,
        "replay_activation_enabled": False,
        "replay_execution_enabled": False,
        "topology_persistence_enabled": False,
        "supabase_write_enabled": False,
        "raw_cache_write_enabled": False,
    }
    if governance:
        base_governance.update(governance)
    return {
        "status": "ok",
        "completed_window_count": 3,
        "governance_certification": base_governance,
        "window_level_results": windows or [_window(20), _window(60), _window(120)],
        "longitudinal_comparison": {"completed_window_count": 3},
    }


def test_successful_source_verification_from_completed_synthetic_hist_long4_like_artifact(tmp_path: Path):
    source = tmp_path / "hist_long4.json"
    report = tmp_path / "report.md"
    artifact_path = tmp_path / "artifact.json"
    source.write_text(json.dumps(_completed_hist_long4()), encoding="utf-8")

    artifact = write_hist_long5b(source_artifact_path=str(source), report_path=str(report), artifact_path=str(artifact_path))

    assert artifact["status"] == "completed"
    assert artifact["source_verification"]["verified"] is True
    assert artifact["completed_windows"] == [20, 60, 120]



def test_explicit_completed_source_artifact_path_overrides_default_blocked_source(tmp_path: Path):
    default_source = tmp_path / "blocked_default.json"
    completed_source = tmp_path / "completed_hist_long4.json"
    default_source.write_text(json.dumps({"status": "blocked"}), encoding="utf-8")
    completed_source.write_text(json.dumps(_completed_hist_long4()), encoding="utf-8")

    artifact = write_hist_long5b(
        source_artifact_path=str(default_source),
        completed_source_artifact_path=str(completed_source),
        report_path=str(tmp_path / "report.md"),
        artifact_path=str(tmp_path / "artifact.json"),
    )

    assert artifact["status"] == "completed"
    assert artifact["source_artifacts"] == [str(completed_source)]
    assert artifact["source_verification"]["verified"] is True


def test_env_completed_source_artifact_path_overrides_default_when_no_explicit_path(tmp_path: Path, monkeypatch):
    default_source = tmp_path / "blocked_default.json"
    completed_source = tmp_path / "completed_hist_long4.json"
    default_source.write_text(json.dumps({"status": "blocked"}), encoding="utf-8")
    completed_source.write_text(json.dumps(_completed_hist_long4()), encoding="utf-8")
    monkeypatch.setenv(COMPLETED_SOURCE_ARTIFACT_ENV, str(completed_source))

    artifact = write_hist_long5b(
        source_artifact_path=str(default_source),
        report_path=str(tmp_path / "report.md"),
        artifact_path=str(tmp_path / "artifact.json"),
    )

    assert artifact["status"] == "completed"
    assert artifact["source_artifacts"] == [str(completed_source)]

def test_blocked_artifact_when_hist_long4_source_missing(tmp_path: Path):
    artifact = write_hist_long5b(source_artifact_path=str(tmp_path / "missing.json"), report_path=str(tmp_path / "report.md"), artifact_path=str(tmp_path / "artifact.json"))

    assert artifact["status"] == "blocked"
    assert artifact["source_verification"]["reason"] == "HIST-LONG-4 JSON missing"


def test_blocked_artifact_when_completed_windows_not_exactly_required(tmp_path: Path):
    source = tmp_path / "hist_long4.json"
    source.write_text(json.dumps(_completed_hist_long4([_window(20), _window(60), _window(90)])), encoding="utf-8")

    artifact = write_hist_long5b(source_artifact_path=str(source), report_path=str(tmp_path / "report.md"), artifact_path=str(tmp_path / "artifact.json"))

    assert artifact["status"] == "blocked"
    assert "20, 60, 120" in artifact["source_verification"]["reason"]


def test_forbidden_governance_flags_are_rejected():
    artifact = build_hist_long5b(_completed_hist_long4(governance={"supabase_write_enabled": True}))

    assert artifact["status"] == "blocked"
    assert "supabase_write_enabled" in artifact["source_verification"]["reason"]


def test_delta_table_includes_required_pairs():
    artifact = build_hist_long5b(_completed_hist_long4())
    pairs = {(row["from_window"], row["to_window"]) for row in artifact["temporal_delta_tables"]["ingestion_continuity"] if row["metric"] == "normalized_rows"}

    assert pairs == {(20, 60), (60, 120), (20, 120)}


def test_stable_metric_classification_works():
    artifact = build_hist_long5b(_completed_hist_long4())

    assert artifact["structural_persistence_classification"]["completeness_ratio"] == "stable"


def test_emerging_decaying_volatile_classification_works():
    windows = [
        _window(20, replay=0.2, sector_hhi=0.3, weak_symbols=[]),
        _window(60, replay=0.4, sector_hhi=0.2, weak_symbols=["ABC"]),
        _window(120, replay=0.6, sector_hhi=0.1, weak_symbols=[]),
    ]
    artifact = build_hist_long5b(_completed_hist_long4(windows))

    assert artifact["structural_persistence_classification"]["replay_density"] == "emerging"
    assert artifact["structural_persistence_classification"]["sector_hhi"] == "decaying"
    assert artifact["structural_persistence_classification"]["weak_symbol_count"] == "volatile"


def test_sensitivity_ranking_deterministic():
    artifact_a = build_hist_long5b(_completed_hist_long4())
    artifact_b = build_hist_long5b(_completed_hist_long4())

    assert artifact_a["sensitivity_ranking"] == artifact_b["sensitivity_ranking"]
    assert [row["sensitivity_rank"] for row in artifact_a["sensitivity_ranking"]] == list(range(1, len(artifact_a["sensitivity_ranking"]) + 1))


def test_foxa_insufficient_granular_data_handled_correctly():
    artifact = build_hist_long5b(_completed_hist_long4())

    foxa = artifact["foxa_longitudinal_assessment"]
    assert foxa["present_all_windows"] is True
    assert foxa["contribution_consistency"] == "insufficient granular signal"
    assert foxa["insufficient_granular_signal"] is True


def test_fragility_no_fragility_condition_handled():
    artifact = build_hist_long5b(_completed_hist_long4())

    assert artifact["fragility_emergence_detection"]["classification"] == ["no_fragility_detected"]


def test_report_and_json_outputs_are_written(tmp_path: Path):
    source = tmp_path / "hist_long4.json"
    report = tmp_path / "report.md"
    artifact_path = tmp_path / "artifact.json"
    source.write_text(json.dumps(_completed_hist_long4()), encoding="utf-8")

    write_hist_long5b(source_artifact_path=str(source), report_path=str(report), artifact_path=str(artifact_path))

    assert report.exists()
    assert artifact_path.exists()
    assert json.loads(artifact_path.read_text(encoding="utf-8"))["status"] == "completed"
    assert "## Temporal Delta Tables" in report.read_text(encoding="utf-8")
