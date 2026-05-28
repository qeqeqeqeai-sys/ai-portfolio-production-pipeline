from __future__ import annotations

import json
import time
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_FIXTURE, DENSITY_MODE_REAL, _deterministic_density_window_dates
from transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment import run_hist_density2
from transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation import DEFAULT_TELEMETRY_MAX_SAMPLES, TELEMETRY_MAX_SAMPLES_HARD_CAP
from transmission_layers.expectation_failure.real_data.sde2_curated_symbol_ecology_expansion import (
    SDE2_VERSION,
    get_sde2_curated_symbol_universe,
    get_sde2_diversity_metrics,
    get_sde2_symbol_categories,
    get_sde2_symbol_validation_metadata,
)

HIST_DENSITY3_SCHEMA_VERSION = "hist_density3_v1"
DEFAULT_TRADING_DAYS = 180
STAGE5_TRADING_DAYS = 20
DEFAULT_MAX_SYMBOLS = 241
DEFAULT_SYMBOL_CHUNK_SIZE = 50
STAGE5_MAX_CHUNKS = 5
REPLACEMENTS = {"RBT": "ROK", "FANUY": "ETN", "SENT": "CHKP", "ABB": "ETN", "CYBR": "PANW", "CFLT": "DDOG", "PARA": "FOXA"}
REPLACEMENT_CANDIDATES = {
    "RBT": ["ROK", "ZBRA", "TER", "ISRG", "SYM"],
    "FANUY": ["ETN", "NVT", "PH", "EMR", "HON"],
    "SENT": ["CHKP", "RBRK", "TENB", "VRNS", "GEN"],
    "ABB": ["ETN", "GEV", "PH", "EMR", "HON"],
    "CYBR": ["PANW", "SAIL", "RBRK", "TENB", "VRNS", "FTNT"],
    "CFLT": ["DDOG", "AKAM", "NET", "ESTC", "MDB"],
    "PARA": ["FOXA", "NWSA", "LYV", "SPOT", "NFLX"],
}
DUPLICATE_GUARD_FILLERS = ["NWSA", "LYV", "ZBRA", "NVT", "GEV", "RBRK", "SAIL", "PAYX", "VRSN", "IAC"]


def _gov() -> dict[str, Any]:
    return {
        "governance_mode": "observational_only",
        "replay_execution_enabled": False,
        "topology_activation_enabled": False,
        "persistence": "local_artifacts_only",
        "raw_input_cache_persistence_controlled_separately": True,
        "no_prediction_or_trading_execution": True,
        "no_cognition_replay_topology_persistence": True,
    }


def _select_unique_symbol(candidates: list[str], seen: set[str], reserved: set[str] | None = None) -> str:
    reserved = reserved or set()
    for candidate in candidates + DUPLICATE_GUARD_FILLERS:
        if candidate and candidate not in seen and candidate not in reserved:
            return candidate
    raise ValueError("HIST-DENSITY-3 fails closed: no unique replacement candidate available")


def _effective_symbols(*, max_symbols: int, include_high_risk_symbols: bool, apply_sde2_replacements: bool) -> tuple[list[str], dict[str, Any]]:
    picked = get_sde2_curated_symbol_universe()[:max_symbols]
    detected = [s for s in picked if s in REPLACEMENTS]
    replacements_applied: dict[str, str] = {}
    excluded: list[str] = []
    duplicate_guard_substitutions: dict[str, str] = {}
    out: list[str] = []
    seen: set[str] = set()
    reserved = set(picked) - set(REPLACEMENTS)
    for s in picked:
        selected = s
        if s in REPLACEMENTS and not include_high_risk_symbols:
            if apply_sde2_replacements:
                selected = _select_unique_symbol(REPLACEMENT_CANDIDATES.get(s, [REPLACEMENTS[s]]), seen, reserved)
                replacements_applied[s] = selected
            else:
                excluded.append(s)
                continue
        elif selected in seen:
            selected = _select_unique_symbol([], seen, reserved)
            duplicate_guard_substitutions[s] = selected
        out.append(selected)
        seen.add(selected)
    tel = {
        "original_symbol_count": len(picked),
        "effective_symbol_count": len(out),
        "high_risk_symbols_detected": detected,
        "replacements_applied": replacements_applied,
        "duplicate_guard_substitutions": duplicate_guard_substitutions,
        "excluded_symbols": excluded,
        "effective_universe_version": f"{SDE2_VERSION}_effective",
    }
    return out, tel


def run_hist_density3(*, trading_days: int = DEFAULT_TRADING_DAYS, max_symbols: int = DEFAULT_MAX_SYMBOLS, symbol_chunk_size: int = DEFAULT_SYMBOL_CHUNK_SIZE, expected_chunk_count: int = STAGE5_MAX_CHUNKS, output_root: str = "reports/hist_density3_curated_241", density_mode: str = DENSITY_MODE_FIXTURE, raw_cache_enabled: bool = False, raw_cache_write_enabled: bool = False, cache_validation_mode: bool = False, cache_only_validation: bool = False, include_high_risk_symbols: bool = False, apply_sde2_replacements: bool = True, dry_run_config_only: bool = False, end_date: str | None = None) -> dict[str, Any]:
    if trading_days < 1 or trading_days > DEFAULT_TRADING_DAYS:
        raise ValueError("HIST-DENSITY-3 fails closed: trading day limit exceeded")
    if max_symbols < 1 or max_symbols > DEFAULT_MAX_SYMBOLS:
        raise ValueError("HIST-DENSITY-3 fails closed: max symbols cap exceeded")
    if symbol_chunk_size < 1 or symbol_chunk_size > 60:
        raise ValueError("HIST-DENSITY-3 fails closed: symbol chunk size must be 1..60")
    end_date = end_date or date.today().isoformat()

    effective_symbols, universe_tel = _effective_symbols(max_symbols=max_symbols, include_high_risk_symbols=include_high_risk_symbols, apply_sde2_replacements=apply_sde2_replacements)
    dates = sorted(_deterministic_density_window_dates(end_date, trading_days))
    symbol_chunks = [effective_symbols[i:i + symbol_chunk_size] for i in range(0, len(effective_symbols), symbol_chunk_size)]
    chunk_sizes = [len(c) for c in symbol_chunks]
    preflight = {
        "requested_max_symbols": max_symbols,
        "effective_symbol_count": len(effective_symbols),
        "chunk_count": len(symbol_chunks),
        "expected_chunk_count": expected_chunk_count,
        "chunk_sizes": chunk_sizes,
        "replacement_map_applied": universe_tel["replacements_applied"],
        "raw_cache_enabled": raw_cache_enabled,
        "raw_cache_write_enabled": raw_cache_write_enabled,
        "replay_execution_enabled": _gov()["replay_execution_enabled"],
        "topology_activation_enabled": _gov()["topology_activation_enabled"],
        "cognition_replay_topology_persistence_disabled": _gov()["no_cognition_replay_topology_persistence"],
    }
    print("[HIST-DENSITY-3][PREFLIGHT] " + json.dumps(preflight, sort_keys=True), flush=True)
    if len(effective_symbols) > DEFAULT_MAX_SYMBOLS:
        raise ValueError("HIST-DENSITY-3 fails closed: effective symbol count exceeds 241")
    if len(symbol_chunks) > STAGE5_MAX_CHUNKS or len(symbol_chunks) > expected_chunk_count:
        raise ValueError("HIST-DENSITY-3 fails closed: chunk count exceeds 5")
    if raw_cache_write_enabled:
        raise ValueError("HIST-DENSITY-3 fails closed: raw cache writes are forbidden")
    gov = _gov()
    if gov["replay_execution_enabled"] or gov["topology_activation_enabled"] or (not gov["no_cognition_replay_topology_persistence"]):
        raise ValueError("HIST-DENSITY-3 fails closed: replay/topology/cognition persistence guard violated")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    config_preview = {
        "schema_version": HIST_DENSITY3_SCHEMA_VERSION,
        "sde2_universe_version": SDE2_VERSION,
        "sde2_categories": get_sde2_symbol_categories(),
        "sde2_diversity_metrics": get_sde2_diversity_metrics(),
        "sde2_symbol_validation_metadata": get_sde2_symbol_validation_metadata(),
        "effective_symbols": effective_symbols,
        "universe_telemetry": universe_tel,
        "chunk_plan": {"symbol_chunk_size": symbol_chunk_size, "symbol_chunk_count": len(symbol_chunks), "trading_days": len(dates)},
        "preflight_validation": preflight,
        "chunk_symbols": symbol_chunks,
        "estimated_symbol_date_rows": len(effective_symbols) * len(dates),
        "cache_modes": {"raw_cache_enabled": raw_cache_enabled, "raw_cache_write_enabled": raw_cache_write_enabled, "cache_validation_mode": cache_validation_mode, "cache_only_validation": cache_only_validation},
        "governance_certification": _gov(),
    }
    (root / "hist_density3_config_preview.json").write_text(json.dumps(config_preview, indent=2, sort_keys=True), encoding="utf-8")
    (root / "hist_density3_config_preview.md").write_text("# HIST-DENSITY-3 Config Preview\n\n" + json.dumps(config_preview, indent=2, sort_keys=True), encoding="utf-8")
    if dry_run_config_only:
        return {"status": "ok", "dry_run_config_only": True, "config_preview": config_preview}

    run_start = time.monotonic()
    chunk_results = []
    aggregate_telemetry = {"chunks": len(symbol_chunks), "rows": 0, "missing_record_sample_count": 0, "endpoint_failure_sample_count": 0, "affected_symbol_count": 0, "affected_date_count": 0}
    aggregate_failure_reasons: dict[str, int] = {}
    aggregate_missing_samples: list[dict[str, Any]] = []
    aggregate_endpoint_samples: list[dict[str, Any]] = []
    for idx, chunk in enumerate(symbol_chunks, start=1):
        chunk_root = root / f"chunk_{idx:02d}"
        out = run_hist_density2(trading_days=trading_days, symbol_count=len(chunk), end_date=end_date, output_root=str(chunk_root), density_mode=density_mode, raw_cache_enabled=raw_cache_enabled, raw_cache_write_enabled=raw_cache_write_enabled, cache_validation_mode=cache_validation_mode, cache_only_validation=cache_only_validation, symbol_universe_override=chunk)
        t = out["density_summary"]["telemetry_summary"]
        chunk_digest = sha256("|".join(chunk).encode("utf-8")).hexdigest()[:16]
        for fr in t.get("top_failure_reasons", []):
            rk = str(fr.get("reason", "unknown"))
            aggregate_failure_reasons[rk] = aggregate_failure_reasons.get(rk, 0) + int(fr.get("count", 0))
        chunk_results.append({"chunk_index": idx, "chunk_symbol_count": len(chunk), "chunk_symbols": chunk, "chunk_symbol_digest": chunk_digest, "telemetry": t, "missing_record_samples": t.get("missing_record_samples", []), "endpoint_failure_samples": t.get("endpoint_failure_samples", [])})
        aggregate_telemetry["rows"] += len(dates) * len(chunk)
        aggregate_telemetry["missing_record_sample_count"] += int(t.get("missing_record_sample_count", 0))
        aggregate_telemetry["endpoint_failure_sample_count"] += int(t.get("endpoint_failure_sample_count", 0))
        aggregate_telemetry["affected_symbol_count"] += int(t.get("affected_symbol_count", 0))
        aggregate_telemetry["affected_date_count"] += int(t.get("affected_date_count", 0))
        aggregate_missing_samples.extend(t.get("missing_record_samples", []))
        aggregate_endpoint_samples.extend(t.get("endpoint_failure_samples", []))
        print(f"[HIST-DENSITY-3] chunk={idx}/{len(symbol_chunks)} symbols={len(chunk)} elapsed={int(time.monotonic()-run_start)}", flush=True)

    sample_limit = max(1, min(DEFAULT_TELEMETRY_MAX_SAMPLES, TELEMETRY_MAX_SAMPLES_HARD_CAP))
    bounded_missing_samples = sorted(aggregate_missing_samples, key=lambda s: (str(s.get("requested_snapshot_date", "")), str(s.get("symbol", ""))))[:sample_limit]
    bounded_endpoint_samples = sorted(aggregate_endpoint_samples, key=lambda s: (str(s.get("requested_snapshot_date", "")), str(s.get("symbol", "")), str(s.get("endpoint_name", "")), int(s.get("attempt_index", 0))))[:sample_limit]
    summary = {"status": "ok", "schema_version": HIST_DENSITY3_SCHEMA_VERSION, "sde2_universe_version": SDE2_VERSION, "universe_telemetry": universe_tel, "preflight_validation": preflight, "chunking_configuration": {"symbol_chunk_size": symbol_chunk_size, "chunk_count": len(symbol_chunks), "max_symbols": max_symbols, "trading_days": len(dates)}, "cache_telemetry": {**aggregate_telemetry, "missing_record_samples": bounded_missing_samples, "endpoint_failure_samples": bounded_endpoint_samples, "telemetry_sample_limit_default": DEFAULT_TELEMETRY_MAX_SAMPLES, "telemetry_sample_limit_hard_cap": TELEMETRY_MAX_SAMPLES_HARD_CAP}, "ops_hist_artifact_summary": {"chunk_results": chunk_results, "top_failure_reasons": [{"reason": k, "count": int(v)} for k, v in sorted(aggregate_failure_reasons.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]}, "governance_certification": gov, "runtime_summary": {"elapsed_seconds": int(time.monotonic()-run_start)}, "next_phase_recommendation": "Proceed staged runs after dry-run and cache validation."}
    (root / "hist_density3_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = [
        "# Stage 5 — Full Bounded 241-Symbol Historical Ecology Rollout Report",
        "",
        "## Workflow inputs used",
        f"- trading_days={trading_days}",
        f"- max_symbols={max_symbols}",
        f"- symbol_chunk_size={symbol_chunk_size}",
        f"- raw_cache_enabled={raw_cache_enabled}",
        f"- raw_cache_write_enabled={raw_cache_write_enabled}",
        f"- cache_validation_mode={cache_validation_mode}",
        f"- cache_only_validation={cache_only_validation}",
        f"- include_high_risk_symbols={include_high_risk_symbols}",
        f"- apply_sde2_replacements={apply_sde2_replacements}",
        f"- dry_run_config_only={dry_run_config_only}",
        "",
        "## Runtime",
        f"- elapsed_seconds={summary['runtime_summary']['elapsed_seconds']}",
        "## Effective symbol count",
        f"- effective_symbol_count={universe_tel['effective_symbol_count']}",
        "## Chunk execution summary",
        f"- chunk_count={len(symbol_chunks)}",
        f"- chunk_sizes={chunk_sizes}",
        "## Endpoint success/failure summary",
        f"- top_failure_reasons={summary['ops_hist_artifact_summary']['top_failure_reasons']}",
        "## Final usable row count",
        f"- estimated_symbol_date_rows={len(effective_symbols) * len(dates)}",
        "## Reconciliation summary",
        f"- exact/reconciled/missing available per chunk in artifact JSON chunk telemetry",
        "## Affected symbols/dates",
        f"- affected_symbol_count={aggregate_telemetry['affected_symbol_count']}",
        f"- affected_date_count={aggregate_telemetry['affected_date_count']}",
        "## Telemetry sample interpretation",
        f"- missing_record_sample_count={aggregate_telemetry['missing_record_sample_count']}",
        f"- endpoint_failure_sample_count={aggregate_telemetry['endpoint_failure_sample_count']}",
        "## Cache posture",
        f"- raw_cache_enabled={raw_cache_enabled}, raw_cache_write_enabled={raw_cache_write_enabled}",
        "## Governance confirmation",
        f"- governance={json.dumps(gov, sort_keys=True)}",
        "## Overall operational stability assessment",
        "- Deterministic bounded chunk execution completed under fail-closed guards.",
        "## Conclusion",
        "- SEFI historical ecology rollout is operationally stable when guard conditions remain satisfied.",
    ]
    (root / "hist_density3_summary.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return summary
