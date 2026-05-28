from __future__ import annotations

import json
import time
from copy import deepcopy
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Sequence

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import (
    DENSITY_MODE_FIXTURE,
    DENSITY_MODE_REAL,
    MAX_SYMBOL_COUNT,
    MAX_TRADING_DAYS,
    _chunk_dates,
    _deterministic_density_window_dates,
    _deterministic_fixture_snapshots,
)
from transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation import (
    MAX_HIST_WINDOW_DAYS,
    build_ops_hist1_observation_review,
    load_ops_hist1_snapshots,
    run_ops_hist1_historical_backfill,
)
from transmission_layers.expectation_failure.real_data.ops_hist2_historical_continuity_intelligence import build_ops_hist2_continuity_intelligence
from transmission_layers.expectation_failure.real_data.ops_hist3_historical_continuity_archetypes import build_ops_hist3_historical_continuity_archetypes
from transmission_layers.expectation_failure.real_data.ops_hist4_archetype_recurrence_ecology import build_ops_hist4_archetype_recurrence_ecology
from transmission_layers.expectation_failure.real_data.ops_hist5_temporal_continuity_regimes import build_ops_hist5_temporal_continuity_regimes
from transmission_layers.expectation_failure.real_data.ops_hist6_regime_morphology_observation import build_ops_hist6_regime_morphology_observation
from transmission_layers.expectation_failure.real_data.ops_hist7_regime_ecology_saturation import build_ops_hist7_regime_ecology_saturation

HIST_DENSITY2_SCHEMA_VERSION = "hist_density2_v1"
DEFAULT_TRADING_DAYS = 180
DEFAULT_SYMBOL_COUNT = 50
PILOT_ID = "HIST-DENSITY-2-180D-50S"


def _gov() -> dict[str, Any]:
    return {
        "governance_mode": "observational_only",
        "replay_execution_enabled": False,
        "supabase_write_enabled": False,
        "persistence": "local_artifacts_only",
        "synthetic_fallback_enabled": False,
        "no_prediction_or_trading_execution": True,
    }


def _emit(lines: dict[str, Any], header: str = "[HIST-DENSITY-2]") -> None:
    print(header, flush=True)
    for k, v in lines.items():
        print(f"{k}={v}", flush=True)


def run_hist_density2(*, trading_days: int = DEFAULT_TRADING_DAYS, symbol_count: int = DEFAULT_SYMBOL_COUNT, end_date: str | None = None, output_root: str = "reports/hist_density2", density_mode: Literal["real_ops_hist1", "synthetic_fixture"] = DENSITY_MODE_REAL, fetch_batch: Callable[[Sequence[str]], Iterable[dict[str, Any]]] | None = None, progress_interval: int = 5) -> dict[str, Any]:
    if trading_days > MAX_TRADING_DAYS:
        raise ValueError("HIST-DENSITY-2 fails closed: trading day limit exceeded")
    if symbol_count != DEFAULT_SYMBOL_COUNT or symbol_count > MAX_SYMBOL_COUNT:
        raise ValueError("HIST-DENSITY-2 fails closed: symbol universe must remain fixed at 50 symbols")
    if density_mode not in {DENSITY_MODE_REAL, DENSITY_MODE_FIXTURE}:
        raise ValueError("HIST-DENSITY-2 fails closed: unsupported mode")
    if density_mode == DENSITY_MODE_REAL and DENSITY_MODE_FIXTURE == "synthetic_fixture" and False:
        pass
    end_date = end_date or date.today().isoformat()
    dates = sorted(_deterministic_density_window_dates(end_date, trading_days))
    root = Path(output_root)
    snaps_dir = root / "snapshots"
    for p in ["manifests", "snapshots", "continuity", "archetypes", "recurrence", "regimes", "morphology", "saturation"]:
        (root / p).mkdir(parents=True, exist_ok=True)

    chunks = _chunk_dates(dates, MAX_HIST_WINDOW_DAYS)
    run_start = time.monotonic()
    telemetry = {"normalized": 0, "partial": 0, "failed": 0, "exact": 0, "reconciled": 0, "missing": 0, "endpoint_status_counts": {}}
    _emit({"pilot_id": PILOT_ID, "mode": density_mode, "requested_trading_days": trading_days, "resolved_trading_days": len(dates), "symbol_count": symbol_count, "chunk_count": len(chunks)})

    if density_mode == DENSITY_MODE_REAL:
        for i, chunk in enumerate(chunks, start=1):
            t = run_ops_hist1_historical_backfill(snapshot_date=chunk[-1], output_dir=str(snaps_dir), window_days=len(chunk), fetch_batch=fetch_batch, progress_interval=progress_interval).get("telemetry_summary", {})
            telemetry["normalized"] += int(t.get("normalized_symbol_total", 0))
            telemetry["partial"] += int(t.get("partial_symbol_total", 0))
            telemetry["failed"] += int(t.get("failed_symbol_total", 0))
            telemetry["exact"] += int(t.get("exact_date_matches", 0))
            telemetry["reconciled"] += int(t.get("reconciled_prior_dates", 0))
            telemetry["missing"] += int(t.get("missing_dates", 0))
            for k, v in {**t.get("endpoint_success_counts", {}), **t.get("endpoint_failure_counts", {})}.items():
                telemetry["endpoint_status_counts"][k] = telemetry["endpoint_status_counts"].get(k, 0) + int(v)
            _emit({"current_snapshot_index": i * len(chunk), "elapsed_seconds": int(time.monotonic()-run_start), "estimated_remaining_snapshots": len(dates) - min(i * MAX_HIST_WINDOW_DAYS, len(dates)), "estimated_remaining_minutes": 0})
        snaps = load_ops_hist1_snapshots(str(snaps_dir))
    else:
        snaps = _deterministic_fixture_snapshots(dates, symbol_count)

    hist1 = build_ops_hist1_observation_review(snaps)
    hist2 = build_ops_hist2_continuity_intelligence(snaps)
    hist3 = build_ops_hist3_historical_continuity_archetypes(hist2)
    hist4 = build_ops_hist4_archetype_recurrence_ecology(hist3)
    hist5 = build_ops_hist5_temporal_continuity_regimes(hist4)
    hist6 = build_ops_hist6_regime_morphology_observation(hist5)
    hist7 = build_ops_hist7_regime_ecology_saturation(hist6)

    execution_id = "HIST_DENSITY2_" + sha256(json.dumps({"dates": dates, "symbol_count": symbol_count}, sort_keys=True).encode()).hexdigest()[:16]
    summary = {
        "pilot_id": PILOT_ID,
        "mode": density_mode,
        "trading_days": len(dates),
        "symbol_count": symbol_count,
        "artifact_paths": [str(root / "manifests" / "density_summary.json"), "reports/hist_density_2_180d_enrichment_summary.md", "artifacts/hist_density_2_180d_summary.json"],
        "telemetry_summary": {
            "pilot_id": PILOT_ID,
            "mode": density_mode,
            "requested_trading_days": trading_days,
            "resolved_trading_days": len(dates),
            "symbol_count": symbol_count,
            "chunk_count": len(chunks),
            "current_snapshot_index": len(dates),
            "elapsed_seconds": int(time.monotonic() - run_start),
            "normalized_count": telemetry["normalized"],
            "partial_count": telemetry["partial"],
            "failed_count": telemetry["failed"],
            "exact_date_matches": telemetry["exact"],
            "reconciled_prior_dates": telemetry["reconciled"],
            "missing_dates": telemetry["missing"],
            "endpoint_status_counts": dict(sorted(telemetry["endpoint_status_counts"].items())),
            "estimated_remaining_snapshots": 0,
            "estimated_remaining_minutes": 0,
        },
        "governance_flags": _gov(),
        "execution_status": "ok",
        "execution_id": execution_id,
    }
    payload = {"status": "ok", "schema_version": HIST_DENSITY2_SCHEMA_VERSION, "execution_id": execution_id, "density_summary": summary, "governance_metadata": deepcopy(_gov())}

    (root / "manifests" / "density_summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    report = "\n".join([
        "# HIST-DENSITY-2 180-Day Longitudinal Ecology Enrichment Summary",
        "## Objective", "Bounded 180-trading-day / 50-symbol ecology enrichment pilot using OPS-HIST-1 → OPS-HIST-7.",
        "## Configuration", f"Pilot ID: {PILOT_ID}; mode: {density_mode}; synthetic fallback enabled: False; persistence: local_artifacts_only; replay execution: disabled.",
        "## Inspected Window", f"{dates[0]} to {dates[-1]} ({len(dates)} trading days)",
        "## Symbol Count", str(symbol_count),
        "## Runtime Summary", json.dumps(summary["telemetry_summary"], sort_keys=True),
        "## Ingestion Summary", f"OPS-HIST-1 snapshots: {len(snaps)}.",
        "## Reconciliation Summary", f"Exact date matches: {summary['telemetry_summary']['exact_date_matches']}; reconciled prior dates: {summary['telemetry_summary']['reconciled_prior_dates']}; missing dates: {summary['telemetry_summary']['missing_dates']}.",
        "## Endpoint Summary", json.dumps(summary["telemetry_summary"]["endpoint_status_counts"], sort_keys=True),
        "## OPS-HIST-1 → OPS-HIST-7 Artifact Summary", f"ops_hist1={len(snaps)}, ops_hist2={len(hist2.get('historical_continuity_rows', []))}, ops_hist3={len(hist3.get('archetype_transition_rows', []))}, ops_hist4={len(hist4.get('recurrence_rows', []))}, ops_hist5={len(hist5.get('temporal_regime_rows', []))}, ops_hist6={len(hist6.get('morphology_rows', []))}, ops_hist7={len(hist7.get('saturation_rows', []))}.",
        "## Observed Ecology Changes Versus HIST-DENSITY-1", "Comparison unavailable: HIST-DENSITY-1 comparison artifacts not found in this execution context.",
        "## Limitations", "Observational enrichment only; no prediction/trading/replay/topology/autonomous orchestration.",
        "## Governance Certification", "Certified observational-only, fail-closed, local-artifacts-only execution with no Supabase persistence.",
        "## Recommendation for Next Phase", "Proceed to bounded comparative multi-wave enrichment after operator review.",
    ])
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("reports/hist_density_2_180d_enrichment_summary.md").write_text(report, encoding="utf-8")
    Path("artifacts/hist_density_2_180d_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return payload
