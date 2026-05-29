from __future__ import annotations

import json
from collections import OrderedDict
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from transmission_layers.expectation_failure.real_data.hist_long4_real_multi_window_ecology import REQUIRED_WINDOWS
from transmission_layers.expectation_failure.real_data.hist_long1_longitudinal_ecology import _trend

HIST_LONG5_SCHEMA_VERSION = "hist_long5_v1"
DEFAULT_SOURCE_ARTIFACT_PATH = "artifacts/hist_long4_real_multi_window_ecology_review.json"
DEFAULT_REPORT_PATH = "reports/hist_long5_analysis_only_review.md"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_long5_analysis_only_review.json"


def _governance() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("governance_mode", "analysis_only"),
        ("phase", "HIST-LONG-5_completed_hist_long4_consumption"),
        ("fmp_calls_enabled", False),
        ("hist_long4_reexecution_enabled", False),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("replay_activation_enabled", False),
        ("replay_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("supabase_write_enabled", False),
        ("raw_cache_write_enabled", False),
        ("local_artifacts_only", True),
    ])


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _assert_completed_hist_long4(source: Mapping[str, Any]) -> None:
    if source.get("status") != "ok" or source.get("all_three_real_windows_completed") is not True:
        raise ValueError("HIST-LONG-5 fails closed: source HIST-LONG-4 artifact must be completed and ok")
    windows = tuple(int(row.get("window_trading_days") or 0) for row in source.get("window_level_results", []) or [])
    if windows != REQUIRED_WINDOWS:
        raise ValueError("HIST-LONG-5 fails closed: source HIST-LONG-4 windows must be exactly 20, 60, and 120")
    governance = source.get("governance_certification", {}) or {}
    forbidden = (
        "prediction_enabled",
        "trading_execution_enabled",
        "replay_activation_enabled",
        "replay_execution_enabled",
        "topology_persistence_enabled",
        "supabase_write_enabled",
        "raw_cache_write_enabled",
    )
    enabled = [key for key in forbidden if governance.get(key) is True]
    if enabled:
        raise ValueError(f"HIST-LONG-5 fails closed: forbidden source governance enabled: {', '.join(enabled)}")


def _recurrence(values: Sequence[str]) -> OrderedDict[str, Any]:
    unique = sorted({value for value in values if value})
    return OrderedDict([("count", len(unique)), ("values", unique)])


def build_hist_long5_analysis(source: Mapping[str, Any]) -> OrderedDict[str, Any]:
    _assert_completed_hist_long4(source)
    windows = list(source.get("window_level_results", []) or [])
    comparison = source.get("longitudinal_comparison", {}) or {}
    diagnostics = source.get("bounded_diagnostics", {}) or {}
    normalized = [int(row.get("normalized_rows") or 0) for row in windows]
    completeness = [row.get("completeness") for row in windows]
    weak_symbols = sorted({symbol for row in windows for symbol in (row.get("weak_symbols", []) or [])})
    endpoint_failure_windows = [int(row.get("window_trading_days") or 0) for row in windows if row.get("endpoint_failures")]
    replay_density = [row.get("replay_density") for row in windows]
    sector_hhi = [(row.get("sector_hhi", {}) or {}).get("universe_hhi") for row in windows]
    source_digest = sha256(json.dumps(source, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return OrderedDict([
        ("schema_version", HIST_LONG5_SCHEMA_VERSION),
        ("status", "ok"),
        ("review_date", date.today().isoformat()),
        ("source_hist_long4_digest", source_digest),
        ("governance_certification", _governance()),
        ("source_window_count", len(windows)),
        ("source_windows", [int(row["window_trading_days"]) for row in windows]),
        ("ingestion_continuity", OrderedDict([
            ("normalized_rows", normalized),
            ("normalized_row_trend", _trend(normalized)),
            ("completeness", completeness),
            ("completeness_trend", _trend(completeness)),
            ("partial_counts", [row.get("partial_count") for row in windows]),
            ("failed_counts", [row.get("failed_count") for row in windows]),
            ("endpoint_failure_windows", endpoint_failure_windows),
        ])),
        ("ecology_persistence", OrderedDict([
            ("replay_density", replay_density),
            ("replay_persistence_trend", diagnostics.get("replay_persistence_trend") or comparison.get("replay_persistence_trend")),
            ("morphology_persistence", (comparison.get("ecology_stability", {}) or {}).get("morphology_persistence")),
            ("replay_activation_status", "not_activated"),
        ])),
        ("concentration_drift", OrderedDict([
            ("sector_hhi", sector_hhi),
            ("trend", diagnostics.get("concentration_trend") or comparison.get("concentration_trend")),
            ("strongest_recurring_sectors", diagnostics.get("strongest_recurring_sectors", [])),
            ("strongest_recurring_subsectors", diagnostics.get("strongest_recurring_subsectors", [])),
        ])),
        ("fragility_watchlist", OrderedDict([
            ("recurring_weak_symbols", diagnostics.get("recurring_weak_symbols", [])),
            ("all_weak_symbols_observed", weak_symbols),
            ("weak_symbol_recurrence", _recurrence(weak_symbols)),
            ("foxa_assessment", (comparison.get("weak_symbol_analysis", {}) or {}).get("foxa_stability")),
            ("provider_degradation_recurrence", (comparison.get("weak_symbol_analysis", {}) or {}).get("provider_degradation_recurrence", [])),
        ])),
        ("hist_long5_recommendation", "Proceed with analysis-only monitoring if HIST-LONG-4 remains completed, replay inactive, and topology non-persistent; do not execute FMP ingestion from HIST-LONG-5."),
    ])


def render_hist_long5_markdown(artifact: Mapping[str, Any]) -> str:
    lines = [
        "# HIST-LONG-5 — Analysis-Only Completed HIST-LONG-4 Review",
        "",
        "## Source Certification",
        f"- Source windows: {artifact['source_windows']}",
        f"- Source window count: {artifact['source_window_count']}",
        f"- Source digest: `{artifact['source_hist_long4_digest']}`",
        "",
        "## Ingestion Continuity",
        f"- `{json.dumps(artifact['ingestion_continuity'], sort_keys=True)}`",
        "",
        "## Ecology Persistence",
        f"- `{json.dumps(artifact['ecology_persistence'], sort_keys=True)}`",
        "",
        "## Concentration Drift",
        f"- `{json.dumps(artifact['concentration_drift'], sort_keys=True)}`",
        "",
        "## Fragility Watchlist",
        f"- `{json.dumps(artifact['fragility_watchlist'], sort_keys=True)}`",
        "",
        "## Governance Certification",
    ]
    for key, value in artifact["governance_certification"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Recommendation", f"- {artifact['hist_long5_recommendation']}"])
    return "\n".join(lines) + "\n"


def write_hist_long5_analysis(*, source_artifact_path: str = DEFAULT_SOURCE_ARTIFACT_PATH, report_path: str = DEFAULT_REPORT_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH) -> OrderedDict[str, Any]:
    source = _load_json(source_artifact_path)
    artifact = build_hist_long5_analysis(source)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_hist_long5_markdown(artifact), encoding="utf-8")
    return artifact
