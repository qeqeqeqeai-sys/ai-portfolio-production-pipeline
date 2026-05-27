from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    GOVERNANCE_BOUNDARIES,
    build_live_fmp_fetcher,
    build_normalized_operational_surfaces,
    build_operator_payloads,
    get_ops_live1b_controlled_universe,
    ingest_controlled_daily_snapshot,
)

DEFAULT_HIST_WINDOW_DAYS = 30
MAX_HIST_WINDOW_DAYS = 90
MAX_SNAPSHOTS_PER_RUN = 90
OPS_HIST1_SCHEMA_VERSION = "ops_hist1_v1"
OPS_HIST1_OBSERVATION_MODE = "controlled_historical_observation"


def _governance_flags() -> dict[str, Any]:
    flags = deepcopy(GOVERNANCE_BOUNDARIES)
    flags.update(
        {
            "historical_observation_mode": True,
            "schema_version": OPS_HIST1_SCHEMA_VERSION,
            "persistence_mode": "local_json_only",
            "supabase_write_enabled": False,
            "repo_writeback_enabled": False,
            "orchestration_enabled": False,
            "streaming_enabled": False,
        }
    )
    return flags


def _parse_date(d: str) -> date:
    return date.fromisoformat(d)


def deterministic_historical_window_dates(snapshot_date: str, window_days: int) -> list[str]:
    if window_days > MAX_HIST_WINDOW_DAYS:
        raise ValueError(f"historical window {window_days} exceeds max {MAX_HIST_WINDOW_DAYS}")
    end = _parse_date(snapshot_date)
    picked: list[str] = []
    cursor = end
    while len(picked) < window_days:
        if cursor.weekday() < 5:
            picked.append(cursor.isoformat())
        cursor -= timedelta(days=1)
    return sorted(picked)


def historical_window_checksum(
    dates: Sequence[str],
    universe: Sequence[str],
    window_days: int,
    schema_version: str = OPS_HIST1_SCHEMA_VERSION,
    observation_mode: str = OPS_HIST1_OBSERVATION_MODE,
) -> str:
    payload = {
        "window_dates": list(dates),
        "universe": list(universe),
        "window_days": int(window_days),
        "schema_version": schema_version,
        "observation_mode": observation_mode,
    }
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def _deterministic_hist_snapshot_id(snapshot_date: str, universe_checksum: str) -> str:
    seed = f"{snapshot_date}|{universe_checksum}|{OPS_HIST1_SCHEMA_VERSION}|{OPS_HIST1_OBSERVATION_MODE}"
    return f"OPS_HIST1_{snapshot_date}_{sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _continuity_observation_rows(snapshots: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prev = None
    for s in snapshots:
        d = s["operational_diagnostics"]
        p = s["posture"]
        row = {
            "snapshot_id": s["snapshot_id"],
            "snapshot_date": s["snapshot_date"],
            "posture": p,
            "posture_transition": "initial" if prev is None else ("changed" if prev["posture"] != p else "unchanged"),
            "fragmentation_value": d["fragmentation_avg"],
            "resilience_value": d["resilience_avg"],
            "sector_concentration_hhi": d["sector_hhi"],
            "volatility_avg": d["volatility_avg"],
            "valuation_dispersion": d["valuation_dispersion"],
            "normalization_completeness": d["normalization_completeness"],
            "fallback_usage": d["fallback_usage"],
        }
        rows.append(row)
        prev = row
    return rows


def _range(values: list[float]) -> dict[str, float]:
    return {"min": round(min(values), 6), "max": round(max(values), 6)} if values else {"min": 0.0, "max": 0.0}


def _snapshot_payload(snapshot_date: str, ingest_result: dict[str, Any], universe: Sequence[str], window_dates: Sequence[str]) -> dict[str, Any]:
    rows = ingest_result.get("rows", [])
    universe_checksum = sha256("|".join(universe).encode("utf-8")).hexdigest()[:16]
    sid = _deterministic_hist_snapshot_id(snapshot_date, universe_checksum)
    op = ingest_result.get("operator_payload", {})
    post = (op.get("daily_ecosystem_posture") or [{}])[0].get("posture", "unknown")
    sector_counts: dict[str, int] = {}
    for r in rows:
        sector_counts[r["sector"]] = sector_counts.get(r["sector"], 0) + 1
    total = max(len(rows), 1)
    hhi = round(sum((c / total) ** 2 for c in sector_counts.values()), 6)
    vol = round(sum(r["volatility_structure"] for r in rows) / total, 6)
    res = round(sum(r["profitability_structure"] - r["leverage_liquidity_structure"] for r in rows) / total, 6)
    frag = round(sum(r["breadth_dispersion_structure"] for r in rows) / total, 6)
    vals = sorted(r["valuation_structure"] for r in rows)
    val_disp = round(vals[-1] - vals[0], 6) if vals else 0.0
    window_checksum = historical_window_checksum(window_dates, universe, len(window_dates))
    diagnostics = {
        "symbols_requested": len(universe),
        "symbols_successfully_normalized": len(rows),
        "normalization_completeness": round((len(rows) / max(len(universe), 1)) * 100.0, 6),
        "fallback_usage": 0.0,
        "fragmentation_avg": frag,
        "resilience_avg": res,
        "sector_hhi": hhi,
        "volatility_avg": vol,
        "valuation_dispersion": val_disp,
        "persistence_mode": "local_json_only",
        "supabase_write_enabled": False,
        "repo_writeback_enabled": False,
        "orchestration_enabled": False,
        "streaming_enabled": False,
    }
    streamlit_payloads = {
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "historical_posture_timeline": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "posture": post}],
        "fragmentation_timeline": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "fragmentation": frag}],
        "resilience_migration_table": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "resilience": res}],
        "sector_transition_table": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "sector_hhi": hhi}],
        "continuity_stability_panel": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "window_checksum": window_checksum}],
        "diagnostics_evolution_table": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "normalization_completeness": diagnostics["normalization_completeness"], "fallback_usage": 0.0}],
        "valuation_dispersion_timeline": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "valuation_dispersion": val_disp}],
        "volatility_transition_table": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "volatility": vol}],
    }
    canonical_tables = {
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "historical_snapshot_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "symbol_count": len(rows)}],
        "historical_posture_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "posture": post}],
        "fragmentation_evolution_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "fragmentation": frag}],
        "resilience_evolution_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "resilience": res}],
        "sector_transition_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "sector_hhi": hhi}],
        "diagnostics_evolution_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "normalization_completeness": diagnostics["normalization_completeness"], "fallback_usage": 0.0}],
        "continuity_stability_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "historical_window_checksum": window_checksum}],
        "governance_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, **_governance_flags()}],
    }
    return {
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "snapshot_id": sid,
        "snapshot_date": snapshot_date,
        "historical_window_metadata": {
            "window_days": len(window_dates),
            "max_window_days": MAX_HIST_WINDOW_DAYS,
            "window_dates": list(window_dates),
        },
        "universe_checksum": universe_checksum,
        "historical_window_checksum": window_checksum,
        "continuity_metadata": {"observation_mode": OPS_HIST1_OBSERVATION_MODE},
        "governance_metadata": _governance_flags(),
        "canonical_payloads": canonical_tables,
        "streamlit_payloads": streamlit_payloads,
        "operational_diagnostics": diagnostics,
        "posture": post,
    }


def run_ops_hist1_historical_backfill(*, snapshot_date: str, output_dir: str, window_days: int = DEFAULT_HIST_WINDOW_DAYS, fetch_batch: Callable[[Sequence[str]], Iterable[dict]] | None = None) -> dict[str, Any]:
    if fetch_batch is None:
        api_key = os.getenv("FMP_API_KEY", "")
        if not api_key:
            raise RuntimeError("FMP_API_KEY missing; OPS-HIST-1 fails closed")
        fetch_batch = build_live_fmp_fetcher(api_key)

    window_dates = deterministic_historical_window_dates(snapshot_date, window_days)
    if len(window_dates) > MAX_SNAPSHOTS_PER_RUN:
        raise ValueError("OPS-HIST-1 fails closed: snapshot count exceeds MAX_SNAPSHOTS_PER_RUN")
    universe = get_ops_live1b_controlled_universe()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshots = []
    for d in window_dates:
        result = ingest_controlled_daily_snapshot(universe, d, fetch_batch)
        result["surfaces"] = build_normalized_operational_surfaces(result.get("rows", []), result.get("snapshot_ts", ""), result.get("snapshot_identity", {}))
        result["operator_payload"] = build_operator_payloads(result["surfaces"])
        snap = _snapshot_payload(d, result, universe, window_dates)
        Path(out_dir / f"ops_hist1_{d}.json").write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
        snapshots.append(snap)
    continuity_rows = _continuity_observation_rows(snapshots)
    return {"status": "ok", "schema_version": OPS_HIST1_SCHEMA_VERSION, "snapshot_count": len(snapshots), "output_dir": str(out_dir), "continuity_rows": continuity_rows, "governance_metadata": _governance_flags()}


def load_ops_hist1_snapshots(input_dir: str) -> list[dict[str, Any]]:
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(input_dir).glob("ops_hist1_*.json"), key=lambda p: p.name)]
    return sorted(rows, key=lambda r: (r.get("snapshot_date", ""), r.get("snapshot_id", "")))


def build_ops_hist1_observation_review(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    if not snapshots:
        raise ValueError("No OPS-HIST-1 snapshots found")
    canonical_keys = [tuple(sorted(s.get("canonical_payloads", {}).keys())) for s in snapshots]
    streamlit_keys = [tuple(sorted(s.get("streamlit_payloads", {}).keys())) for s in snapshots]
    checks = {
        "continuity_stability": len(set(s["historical_window_checksum"] for s in snapshots)) == 1,
        "payload_stability": len(set(canonical_keys)) == 1,
        "streamlit_payload_stability": len(set(streamlit_keys)) == 1,
        "diagnostics_stability": all("normalization_completeness" in s["operational_diagnostics"] for s in snapshots),
    }
    rows = _continuity_observation_rows(snapshots)
    transition_counts = {
        "initial": sum(1 for r in rows if r["posture_transition"] == "initial"),
        "changed": sum(1 for r in rows if r["posture_transition"] == "changed"),
        "unchanged": sum(1 for r in rows if r["posture_transition"] == "unchanged"),
    }
    continuity_metrics = {
        "posture_transition_counts": transition_counts,
        "fragmentation_value_range": _range([float(r["fragmentation_value"]) for r in rows]),
        "resilience_value_range": _range([float(r["resilience_value"]) for r in rows]),
        "sector_concentration_hhi_range": _range([float(r["sector_concentration_hhi"]) for r in rows]),
        "volatility_avg_range": _range([float(r["volatility_avg"]) for r in rows]),
        "valuation_dispersion_range": _range([float(r["valuation_dispersion"]) for r in rows]),
        "normalization_completeness_range": _range([float(r["normalization_completeness"]) for r in rows]),
        "fallback_usage_range": _range([float(r["fallback_usage"]) for r in rows]),
    }
    review = {
        "status": "ok",
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "reviewed_snapshot_count": len(snapshots),
        "governance_metadata": _governance_flags(),
        "continuity_stability": checks,
        "continuity_metrics": continuity_metrics,
        "posture_drift": rows,
        "fragmentation_persistence": [{"snapshot_id": r["snapshot_id"], "snapshot_date": r["snapshot_date"], "fragmentation_value": r["fragmentation_value"]} for r in rows],
        "resilience_persistence": [{"snapshot_id": r["snapshot_id"], "snapshot_date": r["snapshot_date"], "resilience_value": r["resilience_value"]} for r in rows],
        "sector_evolution": [{"snapshot_id": r["snapshot_id"], "snapshot_date": r["snapshot_date"], "sector_concentration_hhi": r["sector_concentration_hhi"]} for r in rows],
        "streamlit_review_payload": {"schema_version": OPS_HIST1_SCHEMA_VERSION, "continuity_stability_panel": [{"check": k, "value": v} for k, v in checks.items()], "historical_posture_timeline": rows, "continuity_metrics": continuity_metrics},
        "canonical_review_payload": {"schema_version": OPS_HIST1_SCHEMA_VERSION, "continuity_stability_rows": [{"check": k, "value": v} for k, v in checks.items()], "historical_snapshot_rows": [{"snapshot_id": s["snapshot_id"], "snapshot_date": s["snapshot_date"]} for s in snapshots], "continuity_metrics_rows": [{"metric": k, "value": v} for k, v in continuity_metrics.items()]},
    }
    return review


def render_ops_hist1_observation_review_markdown(review: dict[str, Any]) -> str:
    return "\n".join([
        "# OPS-HIST-1 Historical Observation Review",
        "## Objective",
        "Bounded historical observational review across deterministic 50-symbol snapshots.",
        f"## Schema version\n{review['schema_version']}",
        f"## Reviewed snapshots\n{review['reviewed_snapshot_count']}",
        "## Continuity stability",
        json.dumps(review["continuity_stability"], sort_keys=True),
        "## Continuity metrics",
        json.dumps(review["continuity_metrics"], sort_keys=True),
        "## Governance certification",
        "Observational-only historical mode; no replay/topology/prediction/trading/orchestration/streaming.",
    ])
