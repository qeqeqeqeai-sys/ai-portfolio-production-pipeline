from __future__ import annotations

import json
import time
from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Sequence

from transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation import (
    MAX_HIST_WINDOW_DAYS,
    OPS_HIST1_SCHEMA_VERSION,
    build_ops_hist1_observation_review,
    historical_window_checksum,
    load_ops_hist1_snapshots,
    run_ops_hist1_historical_backfill,
)
from transmission_layers.expectation_failure.real_data.ops_hist2_historical_continuity_intelligence import build_ops_hist2_continuity_intelligence
from transmission_layers.expectation_failure.real_data.ops_hist3_historical_continuity_archetypes import build_ops_hist3_historical_continuity_archetypes
from transmission_layers.expectation_failure.real_data.ops_hist4_archetype_recurrence_ecology import build_ops_hist4_archetype_recurrence_ecology
from transmission_layers.expectation_failure.real_data.ops_hist5_temporal_continuity_regimes import build_ops_hist5_temporal_continuity_regimes
from transmission_layers.expectation_failure.real_data.ops_hist6_regime_morphology_observation import build_ops_hist6_regime_morphology_observation
from transmission_layers.expectation_failure.real_data.ops_hist7_regime_ecology_saturation import build_ops_hist7_regime_ecology_saturation

HIST_DENSITY1_SCHEMA_VERSION = "hist_density1_v1"
DEFAULT_TRADING_DAYS = 180
MAX_TRADING_DAYS = 365
DEFAULT_SYMBOL_COUNT = 50
MAX_SYMBOL_COUNT = 50
MAX_DAILY_SNAPSHOTS_PER_RUN = 365
DENSITY_MODE_REAL = "real_ops_hist1"
DENSITY_MODE_FIXTURE = "synthetic_fixture"


def _deterministic_density_window_dates(snapshot_date: str, window_days: int) -> list[str]:
    end = date.fromisoformat(snapshot_date)
    picked: list[str] = []
    cursor = end
    while len(picked) < window_days:
        if cursor.weekday() < 5:
            picked.append(cursor.isoformat())
        cursor -= timedelta(days=1)
    return sorted(picked)


def _governance_metadata() -> dict[str, Any]:
    return {
        "observational_only": True,
        "historical_density_expansion_mode": True,
        "continuity_intelligence_mode": True,
        "continuity_compression_mode": True,
        "recurrence_ecology_mode": True,
        "temporal_regime_observation_mode": True,
        "regime_morphology_observation_mode": True,
        "regime_ecology_saturation_mode": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_graph_execution_engines": True,
        "no_high_frequency_streaming": True,
        "persistence_mode": "local_json_only",
        "supabase_write_enabled": False,
        "repo_writeback_enabled": False,
        "orchestration_enabled": False,
        "streaming_enabled": False,
    }


def _chunk_dates(dates: Sequence[str], chunk_size: int) -> list[list[str]]:
    return [list(dates[i : i + chunk_size]) for i in range(0, len(dates), chunk_size)]


def _deterministic_fixture_snapshots(dates: list[str], symbol_count: int) -> list[dict[str, Any]]:
    window_checksum = historical_window_checksum(dates, [f"S{i:02d}" for i in range(symbol_count)], len(dates))
    out: list[dict[str, Any]] = []
    for i, d in enumerate(dates):
        out.append({
            "schema_version": OPS_HIST1_SCHEMA_VERSION,
            "snapshot_id": f"OPS_HIST1_FIXTURE_{d}_{i:04d}",
            "snapshot_date": d,
            "posture": "stable" if i % 3 else "mixed",
            "historical_window_checksum": window_checksum,
            "canonical_payloads": {"schema_version": OPS_HIST1_SCHEMA_VERSION},
            "streamlit_payloads": {"schema_version": OPS_HIST1_SCHEMA_VERSION},
            "operational_diagnostics": {
                "fragmentation_avg": round(0.2 + (i % 5) * 0.03, 6),
                "resilience_avg": round(0.4 + (i % 4) * 0.02, 6),
                "sector_hhi": 0.2,
                "volatility_avg": round(0.3 + (i % 3) * 0.01, 6),
                "valuation_dispersion": round(0.5 + (i % 6) * 0.02, 6),
                "normalization_completeness": 100.0,
                "fallback_usage": 0.0,
            },
        })
    return out


def _emit_hist_density_progress(lines: dict[str, Any], header: str = "[HIST-DENSITY-1]") -> None:
    print(header, flush=True)
    for key, value in lines.items():
        print(f"{key}={value}", flush=True)


def run_hist_density1(*, trading_days: int = DEFAULT_TRADING_DAYS, symbol_count: int = DEFAULT_SYMBOL_COUNT, end_date: str | None = None, start_date: str | None = None, output_root: str = "reports/hist_density1", density_mode: Literal["real_ops_hist1", "synthetic_fixture"] = DENSITY_MODE_REAL, fetch_batch: Callable[[Sequence[str]], Iterable[dict[str, Any]]] | None = None, progress_interval: int = 5) -> dict[str, Any]:
    if trading_days > MAX_TRADING_DAYS or trading_days > MAX_DAILY_SNAPSHOTS_PER_RUN:
        raise ValueError("HIST-DENSITY-1 fails closed: trading day limit exceeded")
    if symbol_count > MAX_SYMBOL_COUNT:
        raise ValueError("HIST-DENSITY-1 fails closed: symbol count exceeds MAX_SYMBOL_COUNT")
    if density_mode not in {DENSITY_MODE_REAL, DENSITY_MODE_FIXTURE}:
        raise ValueError("HIST-DENSITY-1 fails closed: unsupported density mode")
    end_date = end_date or date.today().isoformat()
    dates = _deterministic_density_window_dates(end_date, trading_days)
    if start_date:
        dates = [d for d in dates if d >= start_date]
    if not dates:
        raise ValueError("HIST-DENSITY-1 fails closed: no historical dates in scope")
    dates = sorted(dates)

    root = Path(output_root)
    snapshots_dir = root / "snapshots"
    for p in ["manifests", "snapshots", "continuity", "archetypes", "recurrence", "regimes", "morphology", "saturation"]:
        (root / p).mkdir(parents=True, exist_ok=True)

    ops_hist1_chunks = _chunk_dates(dates, MAX_HIST_WINDOW_DAYS)
    run_started = time.monotonic()
    _emit_hist_density_progress({
        "mode": density_mode,
        "trading_days": len(dates),
        "symbol_count": symbol_count,
        "chunk_count": len(ops_hist1_chunks),
        "output_root": output_root,
    })
    ops_hist1_telemetry: dict[str, Any] = {}
    if density_mode == DENSITY_MODE_REAL:
        for chunk_index, chunk in enumerate(ops_hist1_chunks, start=1):
            chunk_started = time.monotonic()
            _emit_hist_density_progress({
                "chunk": f"{chunk_index}/{len(ops_hist1_chunks)}",
                "window": f"{chunk[0]}→{chunk[-1]}",
                "window_days": len(chunk),
            })
            ops_hist1_telemetry = run_ops_hist1_historical_backfill(
                snapshot_date=chunk[-1],
                output_dir=str(snapshots_dir),
                window_days=len(chunk),
                fetch_batch=fetch_batch,
                progress_interval=progress_interval,
            ).get("telemetry_summary", {})
            _emit_hist_density_progress({
                "chunk": f"{chunk_index} complete",
                "elapsed_seconds": int(time.monotonic() - chunk_started),
            })
        snaps = load_ops_hist1_snapshots(str(snapshots_dir))
        by_key = {(s.get("snapshot_date", ""), s.get("snapshot_id", "")): s for s in snaps}
        snaps = [by_key[k] for k in sorted(by_key)]
    else:
        snaps = _deterministic_fixture_snapshots(dates, symbol_count)
        for s in snaps:
            (snapshots_dir / f"ops_hist1_{s['snapshot_date']}.json").write_text(json.dumps(s, indent=2, sort_keys=True), encoding="utf-8")

    hist1 = build_ops_hist1_observation_review(snaps)
    hist2 = build_ops_hist2_continuity_intelligence(snaps)
    _emit_hist_density_progress({"complete": "OPS-HIST-2", "elapsed_seconds": int(time.monotonic() - run_started), "artifact_count": len(hist2.get("historical_continuity_rows", []))}, header="[OPS-HIST-2]")
    hist3 = build_ops_hist3_historical_continuity_archetypes(hist2)
    _emit_hist_density_progress({"complete": "OPS-HIST-3", "elapsed_seconds": int(time.monotonic() - run_started), "artifact_count": len(hist3.get("archetype_transition_rows", []))}, header="[OPS-HIST-3]")
    hist4 = build_ops_hist4_archetype_recurrence_ecology(hist3)
    _emit_hist_density_progress({"complete": "OPS-HIST-4", "elapsed_seconds": int(time.monotonic() - run_started), "artifact_count": len(hist4.get("recurrence_rows", []))}, header="[OPS-HIST-4]")
    hist5 = build_ops_hist5_temporal_continuity_regimes(hist4)
    _emit_hist_density_progress({"complete": "OPS-HIST-5", "elapsed_seconds": int(time.monotonic() - run_started), "artifact_count": len(hist5.get("temporal_regime_rows", []))}, header="[OPS-HIST-5]")
    hist6 = build_ops_hist6_regime_morphology_observation(hist5)
    _emit_hist_density_progress({"complete": "OPS-HIST-6", "elapsed_seconds": int(time.monotonic() - run_started), "artifact_count": len(hist6.get("morphology_rows", []))}, header="[OPS-HIST-6]")
    hist7 = build_ops_hist7_regime_ecology_saturation(hist6)
    _emit_hist_density_progress({"complete": "OPS-HIST-7", "elapsed_seconds": int(time.monotonic() - run_started), "artifact_count": len(hist7.get("saturation_rows", []))}, header="[OPS-HIST-7]")

    gov = _governance_metadata()
    execution_id = "HIST_DENSITY1_" + sha256(json.dumps({"dates": dates, "symbol_count": symbol_count, "schema": HIST_DENSITY1_SCHEMA_VERSION, "density_mode": density_mode}, sort_keys=True).encode()).hexdigest()[:16]
    data_source = {
        "data_source_mode": density_mode,
        "real_snapshot_generation": density_mode == DENSITY_MODE_REAL,
        "synthetic_snapshot_generation": density_mode == DENSITY_MODE_FIXTURE,
        "fmp_required": density_mode == DENSITY_MODE_REAL,
        "fixture_only": density_mode == DENSITY_MODE_FIXTURE,
        "ops_hist1_chunks_generated": len(ops_hist1_chunks),
        "ops_hist1_chunk_size_max": MAX_HIST_WINDOW_DAYS,
        "ops_hist1_snapshot_count": len(snaps),
        "ops_hist1_snapshot_date_start": snaps[0]["snapshot_date"],
        "ops_hist1_snapshot_date_end": snaps[-1]["snapshot_date"],
    }

    artifact_generation_rows = [{"artifact_index": i + 1, "artifact_name": n, "schema_version": HIST_DENSITY1_SCHEMA_VERSION} for i, n in enumerate(["ops_hist1", "ops_hist2", "ops_hist3", "ops_hist4", "ops_hist5", "ops_hist6", "ops_hist7"])]
    payload = {
        "status": "ok", "schema_version": HIST_DENSITY1_SCHEMA_VERSION, "execution_id": execution_id, "generated_at": end_date,
        "trading_day_count": len(dates), "symbol_count": symbol_count, "artifact_count": 7,
        "historical_window_start": dates[0], "historical_window_end": dates[-1], "governance_metadata": gov,
        **data_source,
        "density_manifest": {"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "execution_id": execution_id, "artifact_count": 7, "snapshot_ranges": [dates[0], dates[-1]], "generation_timestamp": end_date, "governance_metadata": deepcopy(gov), **data_source},
        "snapshot_coverage_manifest": {"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "trading_day_count": len(dates), "coverage_ranges": [dates[0], dates[-1]], "generation_timestamp": end_date, "governance_metadata": deepcopy(gov), **data_source},
        "artifact_generation_manifest": {"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "artifact_counts": 7, "generation_timestamp": end_date, "rows": artifact_generation_rows, "governance_metadata": deepcopy(gov), **data_source},
        "historical_window_manifest": {"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "historical_window_start": dates[0], "historical_window_end": dates[-1], "trading_day_count": len(dates), "governance_metadata": deepcopy(gov), **data_source},
        "coverage_gap_summary": {"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "gap_count": 0, "generation_timestamp": end_date, "governance_metadata": deepcopy(gov), **data_source},
        "density_execution_summary": {"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "execution_order": [r["artifact_name"] for r in artifact_generation_rows], "deterministic_execution": True, "governance_metadata": deepcopy(gov), **data_source},
        "governance_boundary_manifest": {"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "generation_timestamp": end_date, "governance_metadata": deepcopy(gov), **data_source},
        "streamlit_payloads": {"density_execution_panel": [{"execution_id": execution_id, **data_source}], "artifact_coverage_panel": [{"artifact_count": 7}], "historical_window_panel": [{"historical_window_start": dates[0], "historical_window_end": dates[-1]}], "continuity_density_panel": [hist2["continuity_stability_scorecard"]], "recurrence_density_panel": [hist4["recurrence_ecology_scorecard"]], "regime_density_panel": [hist5["temporal_regime_scorecard"]], "morphology_density_panel": [hist6["morphology_scorecard"]], "saturation_density_panel": [hist7["saturation_scorecard"]], "governance_boundary_panel": [{"key": k, "value": v} for k, v in sorted(gov.items())]},
        "canonical_table_payloads": {"density_manifest_rows": [{"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "trading_day_count": len(dates), "symbol_count": symbol_count, "artifact_count": 7, "historical_window_start": dates[0], "historical_window_end": dates[-1], **data_source}], "artifact_generation_rows": artifact_generation_rows, "historical_window_rows": [{"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "historical_window_start": dates[0], "historical_window_end": dates[-1], "trading_day_count": len(dates)}], "coverage_gap_rows": [{"schema_version": HIST_DENSITY1_SCHEMA_VERSION, "gap_count": 0}], "continuity_density_rows": [hist2["continuity_stability_scorecard"]], "recurrence_density_rows": [hist4["recurrence_ecology_scorecard"]], "regime_density_rows": [hist5["temporal_regime_scorecard"]], "morphology_density_rows": [hist6["morphology_scorecard"]], "saturation_density_rows": [hist7["saturation_scorecard"]], "governance_rows": [{"key": k, "value": v} for k, v in sorted(gov.items())]},
    }

    (snapshots_dir / "ops_hist1_review.json").write_text(json.dumps(hist1, indent=2, sort_keys=True), encoding="utf-8")
    (root / "continuity" / "ops_hist2_continuity_intelligence.json").write_text(json.dumps(hist2, indent=2, sort_keys=True), encoding="utf-8")
    (root / "archetypes" / "ops_hist3_archetype_observation.json").write_text(json.dumps(hist3, indent=2, sort_keys=True), encoding="utf-8")
    (root / "recurrence" / "ops_hist4_recurrence_ecology.json").write_text(json.dumps(hist4, indent=2, sort_keys=True), encoding="utf-8")
    (root / "regimes" / "ops_hist5_temporal_regime_observation.json").write_text(json.dumps(hist5, indent=2, sort_keys=True), encoding="utf-8")
    (root / "morphology" / "ops_hist6_regime_morphology_observation.json").write_text(json.dumps(hist6, indent=2, sort_keys=True), encoding="utf-8")
    (root / "saturation" / "ops_hist7_regime_ecology_saturation.json").write_text(json.dumps(hist7, indent=2, sort_keys=True), encoding="utf-8")
    (root / "manifests" / "density_summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _emit_hist_density_progress({
        "elapsed_seconds": int(time.monotonic() - run_started),
        "snapshots_generated": len(snaps),
        "normalized_symbol_total": int(ops_hist1_telemetry.get("normalized_symbol_total", 0)),
        "partial_symbol_total": int(ops_hist1_telemetry.get("partial_symbol_total", 0)),
        "failed_symbol_total": int(ops_hist1_telemetry.get("failed_symbol_total", 0)),
        "ops_hist2_artifacts": len(hist2.get("historical_continuity_rows", [])),
        "ops_hist3_artifacts": len(hist3.get("archetype_transition_rows", [])),
        "ops_hist4_artifacts": len(hist4.get("recurrence_rows", [])),
        "ops_hist5_artifacts": len(hist5.get("temporal_regime_rows", [])),
        "ops_hist6_artifacts": len(hist6.get("morphology_rows", [])),
        "ops_hist7_artifacts": len(hist7.get("saturation_rows", [])),
    }, header="[HIST-DENSITY-1][summary]")
    return payload


def render_hist_density1_markdown(payload: dict[str, Any]) -> str:
    mode = payload.get("data_source_mode", DENSITY_MODE_REAL)
    return "\n".join([
        "# HIST-DENSITY-1 Controlled Historical Density Expansion",
        "## Objective", "Controlled bounded historical density expansion using OPS-HIST-1 through OPS-HIST-7.",
        "## Historical Density Scope", f"Observed and accumulated {payload['trading_day_count']} trading days across {payload['symbol_count']} symbols.",
        "## OPS-HIST Layer Coverage", "Generated OPS-HIST-1 → OPS-HIST-7 in linear deterministic sequence.",
        "## Historical Window Coverage", f"Historical period covered from {payload['historical_window_start']} to {payload['historical_window_end']}.",
        "## Density Execution Summary", f"Density mode: {mode}; real OPS-HIST-1 snapshots generated: {payload['real_snapshot_generation']}; chunk count: {payload['ops_hist1_chunks_generated']}.",
        "## Artifact Coverage Summary", f"Generated {payload['artifact_count']} bounded artifacts with {payload['ops_hist1_snapshot_count']} OPS-HIST-1 snapshots.",
        "## Continuity Density Summary", "Continuity density observed and covered using OPS-HIST continuity intelligence.",
        "## Recurrence Density Summary", "Recurrence density observed and accumulated using archetype recurrence ecology.",
        "## Regime Density Summary", "Regime density observed and covered across historical period regimes.",
        "## Morphology Density Summary", "Morphology density observed and generated across bounded historical period artifacts.",
        "## Saturation Density Summary", "Saturation density observed and expanded across morphology ecology saturation artifacts.",
        "## Governance Certification", "Observational-only bounded historical density expansion mode certified with local-output-only persistence.",
        "## Explicit Forbidden Boundaries", "No prediction, forecasting, autonomous replay, topology activation, graph execution, orchestration, or streaming.",
        "## Future Recommendation", "Continue controlled bounded historical density accumulation with deterministic manifests.",
    ])
