from __future__ import annotations

import json
import zipfile
from collections import Counter, OrderedDict
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_REAL
from transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion import (
    DEFAULT_MAX_SYMBOLS,
    DEFAULT_SYMBOL_CHUNK_SIZE,
    STAGE5_MAX_CHUNKS,
    _effective_symbols,
    run_hist_density3,
)
from transmission_layers.expectation_failure.real_data.hist_density4_findings_review import build_hist_density4_findings_review
from transmission_layers.expectation_failure.real_data.hist_long1_longitudinal_ecology import _mean, _range, _sector_hhi, _trend, _volatility

HIST_LONG4_SCHEMA_VERSION = "hist_long4_v1"
REQUIRED_WINDOWS = (20, 60, 120)
DEFAULT_OUTPUT_ROOT = "reports/hist_long4_windows"
DEFAULT_REPORT_PATH = "reports/hist_long4_real_multi_window_ecology_review.md"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_long4_real_multi_window_ecology_review.json"

DensityRunner = Callable[..., Mapping[str, Any]]
ReviewBuilder = Callable[[str], Mapping[str, Any]]


def _governance() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("governance_mode", "observational_only"),
        ("phase", "HIST-LONG-4_real_multi_window_ecology_accumulation"),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("replay_activation_enabled", False),
        ("replay_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("topology_activation_enabled", False),
        ("supabase_write_enabled", False),
        ("raw_cache_write_enabled", False),
        ("raw_cache_enabled", False),
        ("local_artifacts_only", True),
        ("observational_report_only", True),
        ("density_mode", DENSITY_MODE_REAL),
    ])


def _counter_rows(counter: Counter[str], key_name: str, *, limit: int | None = None) -> list[OrderedDict[str, Any]]:
    rows = [OrderedDict([(key_name, key), ("window_count", int(value))]) for key, value in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))]
    return rows if limit is None else rows[:limit]


def _sum_failure_counts(rows: Iterable[Mapping[str, Any]]) -> OrderedDict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for key, value in (row.get("endpoint_status_counts", {}) or {}).items():
            text = str(key)
            if any(marker in text.lower() for marker in ("fail", "error", "http", "zero_records")) or "403" in text:
                counts[text] += int(value or 0)
        for reason in row.get("top_failure_reasons", []) or []:
            if isinstance(reason, Mapping):
                counts[str(reason.get("reason", "unknown"))] += int(reason.get("count", 0) or 0)
    return OrderedDict((key, int(value)) for key, value in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _guard_plan(*, windows: Sequence[int], max_symbols: int, symbol_chunk_size: int, expected_chunk_count: int, density_mode: str, apply_sde2_replacements: bool, include_high_risk_symbols: bool, supabase_write_enabled: bool, replay_activation_enabled: bool, topology_persistence_enabled: bool, raw_cache_write_enabled: bool) -> tuple[int, ...]:
    clean_windows = tuple(int(w) for w in windows)
    if clean_windows != REQUIRED_WINDOWS:
        raise ValueError("HIST-LONG-4 fails closed: windows must be exactly 20, 60, and 120 trading days")
    if any(w < 1 or w > 180 for w in clean_windows):
        raise ValueError("HIST-LONG-4 fails closed: window_days must be <= 180")
    if max_symbols > DEFAULT_MAX_SYMBOLS:
        raise ValueError("HIST-LONG-4 fails closed: max_symbols must be <= 241")
    if symbol_chunk_size != DEFAULT_SYMBOL_CHUNK_SIZE:
        raise ValueError("HIST-LONG-4 fails closed: symbol_chunk_size must remain 50")
    if expected_chunk_count != STAGE5_MAX_CHUNKS:
        raise ValueError("HIST-LONG-4 fails closed: expected_chunk_count must equal 5")
    if density_mode != DENSITY_MODE_REAL:
        raise ValueError("HIST-LONG-4 fails closed: density_mode must be real_ops_hist1")
    if apply_sde2_replacements is not True:
        raise ValueError("HIST-LONG-4 fails closed: apply_sde2_replacements must be True")
    if include_high_risk_symbols is not False:
        raise ValueError("HIST-LONG-4 fails closed: include_high_risk_symbols must be False")
    if supabase_write_enabled:
        raise ValueError("HIST-LONG-4 fails closed: Supabase writes are forbidden")
    if replay_activation_enabled:
        raise ValueError("HIST-LONG-4 fails closed: replay activation is forbidden")
    if topology_persistence_enabled:
        raise ValueError("HIST-LONG-4 fails closed: topology persistence is forbidden")
    if raw_cache_write_enabled:
        raise ValueError("HIST-LONG-4 fails closed: raw cache writes are forbidden")
    return clean_windows


def build_hist_long4_orchestration_plan(*, windows: Sequence[int] = REQUIRED_WINDOWS, max_symbols: int = DEFAULT_MAX_SYMBOLS, symbol_chunk_size: int = DEFAULT_SYMBOL_CHUNK_SIZE, expected_chunk_count: int = STAGE5_MAX_CHUNKS, density_mode: str = DENSITY_MODE_REAL, apply_sde2_replacements: bool = True, include_high_risk_symbols: bool = False, output_root: str = DEFAULT_OUTPUT_ROOT, end_date: str | None = None, supabase_write_enabled: bool = False, replay_activation_enabled: bool = False, topology_persistence_enabled: bool = False, raw_cache_write_enabled: bool = False) -> OrderedDict[str, Any]:
    clean_windows = _guard_plan(windows=windows, max_symbols=max_symbols, symbol_chunk_size=symbol_chunk_size, expected_chunk_count=expected_chunk_count, density_mode=density_mode, apply_sde2_replacements=apply_sde2_replacements, include_high_risk_symbols=include_high_risk_symbols, supabase_write_enabled=supabase_write_enabled, replay_activation_enabled=replay_activation_enabled, topology_persistence_enabled=topology_persistence_enabled, raw_cache_write_enabled=raw_cache_write_enabled)
    symbols, universe_tel = _effective_symbols(max_symbols=max_symbols, include_high_risk_symbols=include_high_risk_symbols, apply_sde2_replacements=apply_sde2_replacements)
    chunk_count = (len(symbols) + symbol_chunk_size - 1) // symbol_chunk_size
    if len(symbols) > DEFAULT_MAX_SYMBOLS:
        raise ValueError("HIST-LONG-4 fails closed: effective universe exceeds 241 symbols")
    if chunk_count != expected_chunk_count:
        raise ValueError("HIST-LONG-4 fails closed: effective universe must resolve to exactly five chunks")
    return OrderedDict([
        ("schema_version", HIST_LONG4_SCHEMA_VERSION),
        ("status", "ok"),
        ("orchestration_date", date.today().isoformat()),
        ("end_date", end_date or date.today().isoformat()),
        ("windows", list(clean_windows)),
        ("max_symbols", max_symbols),
        ("symbol_chunk_size", symbol_chunk_size),
        ("expected_chunk_count", expected_chunk_count),
        ("density_mode", density_mode),
        ("apply_sde2_replacements", apply_sde2_replacements),
        ("include_high_risk_symbols", include_high_risk_symbols),
        ("output_root", output_root),
        ("effective_symbol_count", len(symbols)),
        ("foxa_present", "FOXA" in symbols),
        ("para_present", "PARA" in symbols),
        ("universe_telemetry", OrderedDict(sorted(dict(universe_tel).items()))),
        ("sector_subsector_concentration_baseline", _sector_hhi(symbols)),
        ("governance_certification", _governance()),
    ])


def _bundle_source_root(source_root: str, *, window: int, artifact_dir: str = "artifacts") -> str:
    root = Path(source_root)
    if not root.exists():
        raise ValueError(f"HIST-LONG-4 fails closed: source root missing for {window}d window")
    Path(artifact_dir).mkdir(parents=True, exist_ok=True)
    bundle_path = Path(artifact_dir) / f"hist_long4_window_{int(window):03d}d_completed_bundle.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            zf.write(path, arcname=str(path.relative_to(root)))
    return str(bundle_path)


def _parse_source_artifacts(source_root: str) -> OrderedDict[str, Any]:
    root = Path(source_root)
    summary_path = root / "hist_density3_summary.json"
    preview_path = root / "hist_density3_config_preview.json"
    chunk_manifest_paths = sorted(root.glob("chunk_*/manifests/density_summary.json"))
    snapshot_paths = sorted(root.glob("chunk_*/snapshots/ops_hist1_*.json"))
    summary = _read_json(summary_path) if summary_path.exists() else {}
    preview = _read_json(preview_path) if preview_path.exists() else {}
    manifest_payloads = [_read_json(path) for path in chunk_manifest_paths]
    snapshot_payloads = [_read_json(path) for path in snapshot_paths]
    telemetry_rows = [((payload.get("density_summary", {}) or {}).get("telemetry_summary", {}) or {}) for payload in manifest_payloads]
    snapshot_postures = Counter(str(payload.get("posture", "unknown")) for payload in snapshot_payloads)
    snapshot_sector_hhi = [((payload.get("operational_diagnostics", {}) or {}).get("sector_hhi")) for payload in snapshot_payloads]
    snapshot_sector_hhi = [float(value) for value in snapshot_sector_hhi if isinstance(value, (int, float))]
    snapshot_transition_counts = [len((((payload.get("canonical_payloads", {}) or {}).get("sector_transition_rows")) or [])) for payload in snapshot_payloads]
    return OrderedDict([
        ("hist_density3_summary_present", bool(summary)),
        ("hist_density3_config_preview_present", bool(preview)),
        ("chunk_manifest_count", len(chunk_manifest_paths)),
        ("ops_hist_snapshot_count", len(snapshot_paths)),
        ("telemetry_summary_count", len(telemetry_rows)),
        ("chunk_manifest_paths", [str(path) for path in chunk_manifest_paths]),
        ("ops_hist_snapshot_sample_paths", [str(path) for path in snapshot_paths[:10]]),
        ("density_summary", summary),
        ("config_preview", preview),
        ("telemetry_summaries", telemetry_rows),
        ("ops_hist_snapshot_summary", OrderedDict([
            ("posture_counts", OrderedDict(sorted(snapshot_postures.items()))),
            ("sector_hhi_range", _range(snapshot_sector_hhi)),
            ("sector_transition_row_range", _range(snapshot_transition_counts)),
        ])),
    ])


def _window_summary(*, window: int, source_root: str, review: Mapping[str, Any], parsed: Mapping[str, Any], bundle_path: str, sector_profile: Mapping[str, Any]) -> OrderedDict[str, Any]:
    ingestion = review.get("ingestion_quality", {}) or {}
    agg = ingestion.get("aggregate", {}) or {}
    chunk_rows = list(ingestion.get("chunk_quality_rows", []) or [])
    weak_rows = list(review.get("weak_symbol_review", []) or [])
    ecology = review.get("ecology_findings", {}) or {}
    first_ecology = review.get("first_ecology_findings", {}) or {}
    normalized = int(agg.get("normalized_count_total") or 0)
    capacity = int(agg.get("requested_symbol_date_capacity_total") or agg.get("estimated_symbol_date_rows") or 0)
    partial = int(agg.get("partial_count_total") or 0)
    failed = int(agg.get("failed_count_total") or 0)
    missing = int(agg.get("missing_dates_total") or 0)
    exact = int(agg.get("exact_date_matches_total") or 0)
    reconciled = int(agg.get("reconciled_prior_dates_total") or 0)
    endpoint_failures = OrderedDict(sorted((agg.get("endpoint_failures") or _sum_failure_counts(chunk_rows)).items()))
    density_values = [row.get("normalization_density") for row in chunk_rows if isinstance(row.get("normalization_density"), (int, float))]
    topology_values: list[int] = []
    sector_hhi_values: list[float] = []
    preflight_symbols: set[str] = set()
    for row in ecology.get("chunk_diagnostics", []) or []:
        richness = row.get("structural_richness", {}) or {}
        topology_values.append(int(richness.get("sector_transition_rows") or 0) + int(richness.get("posture_variety") or 0))
        if isinstance(row.get("sector_hhi_average"), (int, float)):
            sector_hhi_values.append(float(row["sector_hhi_average"]))
        preflight_symbols.update(str(s).upper() for s in row.get("preflight_failure_symbols", []) or [])
    symbols: list[str] = []
    for row in chunk_rows:
        symbols.extend(str(symbol).upper() for symbol in (row.get("chunk_symbols", []) or []))
    weak_symbols = [str(row.get("symbol", "")).upper() for row in weak_rows if row.get("symbol")]
    return OrderedDict([
        ("window_trading_days", int(window)),
        ("source_root", source_root),
        ("completed_bundle_path", bundle_path),
        ("source_status", review.get("source_status")),
        ("source_mode", review.get("source_mode")),
        ("completed_telemetry_mode", bool(review.get("completed_telemetry_mode"))),
        ("chunk_count", int(agg.get("chunk_count") or len(chunk_rows))),
        ("configured_symbol_count", int(agg.get("configured_symbol_count") or 0)),
        ("effective_symbol_count", int(agg.get("effective_symbol_count") or len(symbols) or 0)),
        ("parsed_artifact_counts", OrderedDict((k, parsed[k]) for k in ("hist_density3_summary_present", "hist_density3_config_preview_present", "chunk_manifest_count", "ops_hist_snapshot_count", "telemetry_summary_count"))),
        ("ops_hist_snapshot_summary", parsed.get("ops_hist_snapshot_summary", {})),
        ("normalized_rows", normalized),
        ("requested_symbol_date_capacity_total", capacity),
        ("completeness", round(normalized / capacity, 6) if capacity else None),
        ("partial_count", partial),
        ("failed_count", failed),
        ("missing_dates", missing),
        ("exact_date_matches", exact),
        ("reconciled_dates", reconciled),
        ("exact_date_ratio", round(exact / max(normalized, 1), 6) if normalized else None),
        ("reconciled_date_ratio", round(reconciled / max(normalized, 1), 6) if normalized else None),
        ("endpoint_failures", endpoint_failures),
        ("top_failure_reasons", agg.get("top_failure_reasons", [])),
        ("replay_density", round(normalized / capacity, 6) if capacity else None),
        ("contradiction_burden", OrderedDict([("count", missing + partial + failed), ("ratio", round((missing + partial + failed) / capacity, 6) if capacity else None)])),
        ("topology_richness", OrderedDict([("chunk_richness_range", _range(topology_values)), ("chunk_richness_average", _mean(topology_values)), ("topology_persistence_enabled", False)])),
        ("morphology_persistence", OrderedDict([("posture_stability", ecology.get("posture_stability")), ("posture_counts", OrderedDict(sorted((ecology.get("posture_counts") or {}).items()))), ("dominant_chunk", (review.get("chunk_comparison", {}) or {}).get("dominant_chunk"))])),
        ("temporal_persistence", OrderedDict([("observed_days", int(ecology.get("temporal_stability_days") or window)), ("assessment", "stable_single_posture" if ecology.get("posture_stability") == "stable_single_posture" else "mixed_or_unavailable")])),
        ("replay_saturation", OrderedDict([("status", "not_activated"), ("density", round(normalized / capacity, 6) if capacity else None), ("saturation_surface", first_ecology.get("ops_hist_surface_counts", {}))])),
        ("sector_hhi", OrderedDict([("snapshot_range", _range(sector_hhi_values)), ("universe_hhi", sector_profile.get("sector_hhi")), ("strongest_sectors", sector_profile.get("strongest_sectors", []))])),
        ("subsector_hhi", OrderedDict([("snapshot_range", _range(sector_hhi_values)), ("universe_hhi", sector_profile.get("subsector_hhi")), ("strongest_subsectors", sector_profile.get("strongest_subsectors", []))])),
        ("monoculture_risk", first_ecology.get("monoculture_risk") or ecology.get("monoculture_risk")),
        ("diversity_persistence", "stable_curated_universe"),
        ("weak_symbols", weak_symbols),
        ("weak_symbol_details", weak_rows),
        ("foxa_present", "FOXA" in symbols),
        ("foxa_weak", "FOXA" in weak_symbols or "FOXA" in preflight_symbols),
        ("provider_degradation", OrderedDict([("endpoint_failures", endpoint_failures), ("top_failure_reasons", agg.get("top_failure_reasons", []))])),
        ("chunk_density_range", _range(density_values)),
    ])


def _build_comparison(window_summaries: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    ordered = sorted(window_summaries, key=lambda row: int(row["window_trading_days"]))
    weak_counter: Counter[str] = Counter()
    provider_counter: Counter[str] = Counter()
    sector_counter: Counter[str] = Counter()
    subsector_counter: Counter[str] = Counter()
    posture_counter: Counter[str] = Counter()
    endpoint_failure_windows = 0
    for row in ordered:
        weak_counter.update(row.get("weak_symbols", []) or [])
        if row.get("endpoint_failures"):
            endpoint_failure_windows += 1
        for reason in row.get("top_failure_reasons", []) or []:
            if isinstance(reason, Mapping):
                provider_counter[str(reason.get("reason", "unknown"))] += 1
        for item in ((row.get("sector_hhi", {}) or {}).get("strongest_sectors", []) or [])[:8]:
            sector_counter[str(item.get("sector"))] += 1
        for item in ((row.get("subsector_hhi", {}) or {}).get("strongest_subsectors", []) or [])[:8]:
            subsector_counter[str(item.get("subsector"))] += 1
        posture = ((row.get("morphology_persistence", {}) or {}).get("posture_stability"))
        if posture:
            posture_counter[str(posture)] += 1
    normalized = [row.get("normalized_rows") for row in ordered]
    completeness = [row.get("completeness") for row in ordered]
    exact_ratios = [row.get("exact_date_ratio") for row in ordered]
    reconciled_ratios = [row.get("reconciled_date_ratio") for row in ordered]
    burdens = [(row.get("contradiction_burden", {}) or {}).get("ratio") for row in ordered]
    richness = [(row.get("topology_richness", {}) or {}).get("chunk_richness_average") for row in ordered]
    replay = [row.get("replay_density") for row in ordered]
    sector_hhi = [(row.get("sector_hhi", {}) or {}).get("universe_hhi") for row in ordered]
    subsector_hhi = [(row.get("subsector_hhi", {}) or {}).get("universe_hhi") for row in ordered]
    weak_by_window = [set(row.get("weak_symbols", []) or []) for row in ordered]
    recurring_weak = sorted(set.intersection(*weak_by_window)) if weak_by_window else []
    new_weak = sorted((weak_by_window[-1] - set.union(*weak_by_window[:-1])) if len(weak_by_window) > 1 else weak_by_window[-1] if weak_by_window else set())
    stable_structures = ["five_chunk_envelope", "curated_241_symbol_universe", "observational_governance"]
    if len(posture_counter) == 1 and posture_counter:
        stable_structures.append(next(iter(posture_counter)))
    return OrderedDict([
        ("windows", [int(row["window_trading_days"]) for row in ordered]),
        ("completed_window_count", sum(1 for row in ordered if row.get("completed_telemetry_mode") and row.get("source_status") == "ok")),
        ("ingestion_quality", OrderedDict([("normalized_rows", OrderedDict([("values", normalized), ("trend", _trend(normalized))])), ("completeness", OrderedDict([("values", completeness), ("trend", _trend(completeness)), ("volatility", _volatility(completeness))])), ("partial_counts", [row.get("partial_count") for row in ordered]), ("failed_counts", [row.get("failed_count") for row in ordered]), ("exact_date_match_ratios", OrderedDict([("values", exact_ratios), ("trend", _trend(exact_ratios))])), ("reconciled_date_ratios", OrderedDict([("values", reconciled_ratios), ("trend", _trend(reconciled_ratios))])), ("endpoint_failure_window_count", endpoint_failure_windows)])),
        ("ecology_stability", OrderedDict([("replay_density", OrderedDict([("values", replay), ("trend", _trend(replay)), ("activation_status", "not_activated")])), ("contradiction_burden", OrderedDict([("values", burdens), ("trend", _trend(burdens)), ("volatility", _volatility(burdens))])), ("topology_richness", OrderedDict([("values", richness), ("trend", _trend(richness)), ("persistence_status", "report_local_not_persisted")])), ("morphology_persistence", OrderedDict([("posture_recurrence", _counter_rows(posture_counter, "posture")), ("assessment", "stable_across_completed_real_windows" if len(posture_counter) == 1 and len(ordered) == 3 else "mixed_or_insufficient")])), ("temporal_persistence", "multi_window_comparison_available"), ("replay_saturation", "not_activated_density_only")])) ,
        ("concentration_diversity", OrderedDict([("sector_hhi", OrderedDict([("values", sector_hhi), ("trend", _trend(sector_hhi))])), ("subsector_hhi", OrderedDict([("values", subsector_hhi), ("trend", _trend(subsector_hhi))])), ("strongest_recurring_sectors", _counter_rows(sector_counter, "sector", limit=10)), ("strongest_recurring_subsectors", _counter_rows(subsector_counter, "subsector", limit=10)), ("monoculture_risk", [row.get("monoculture_risk") for row in ordered]), ("diversity_persistence", "persistent_static_curated_universe"), ("concentration_drift", _trend(sector_hhi))])) ,
        ("weak_symbol_analysis", OrderedDict([("recurring_weak_symbols", recurring_weak), ("new_weak_symbols", new_weak), ("weak_symbol_recurrence", _counter_rows(weak_counter, "symbol")), ("provider_degradation_recurrence", _counter_rows(provider_counter, "reason")), ("foxa_stability", OrderedDict([("present_all_windows", all(row.get("foxa_present") for row in ordered)), ("weak_windows", [int(row["window_trading_days"]) for row in ordered if row.get("foxa_weak")]), ("assessment", "stable_not_weak" if all(row.get("foxa_present") for row in ordered) and not any(row.get("foxa_weak") for row in ordered) else "requires_review")]))])),
        ("structural_persistence", OrderedDict([("stable_structures", stable_structures), ("decaying_structures", [] if _trend(burdens) in {"stable", "decreasing"} else ["contradiction_burden"]), ("emerging_structures", [f"new_weak_symbol:{s}" for s in new_weak]), ("propagation_asymmetry", "provider_degradation_not_recurring" if not provider_counter else "provider_degradation_recurrence_present"), ("fragility_clusters", [f"weak_symbol:{s}" for s in recurring_weak] or ["none_detected"])])),
        ("replay_persistence_trend", _trend(replay)),
        ("concentration_trend", _trend(sector_hhi)),
    ])


def _validate_completed_window(row: Mapping[str, Any], plan: Mapping[str, Any]) -> None:
    if int(row.get("window_trading_days") or 0) > 180:
        raise ValueError("HIST-LONG-4 fails closed: completed window exceeds 180 days")
    if int(row.get("chunk_count") or 0) != int(plan["expected_chunk_count"]):
        raise ValueError("HIST-LONG-4 fails closed: completed artifact does not contain five chunks")
    if row.get("completed_telemetry_mode") is not True or row.get("source_status") != "ok":
        raise ValueError("HIST-LONG-4 fails closed: all windows must complete with real telemetry")
    parsed = row.get("parsed_artifact_counts", {}) or {}
    if parsed.get("hist_density3_summary_present") is not True or parsed.get("hist_density3_config_preview_present") is not True:
        raise ValueError("HIST-LONG-4 fails closed: completed density summary/config artifacts are required")
    if int(parsed.get("chunk_manifest_count") or 0) != int(plan["expected_chunk_count"]):
        raise ValueError("HIST-LONG-4 fails closed: completed artifact must include five chunk manifests")
    if int(parsed.get("telemetry_summary_count") or 0) != int(plan["expected_chunk_count"]):
        raise ValueError("HIST-LONG-4 fails closed: completed artifact must include five telemetry summaries")
    if int(parsed.get("ops_hist_snapshot_count") or 0) < int(plan["expected_chunk_count"]):
        raise ValueError("HIST-LONG-4 fails closed: completed artifact must include OPS-HIST snapshots for every chunk")
    if int(row.get("effective_symbol_count") or 0) > int(plan["max_symbols"]):
        raise ValueError("HIST-LONG-4 fails closed: effective symbol count exceeds cap")


def run_hist_long4(*, windows: Sequence[int] = REQUIRED_WINDOWS, max_symbols: int = DEFAULT_MAX_SYMBOLS, symbol_chunk_size: int = DEFAULT_SYMBOL_CHUNK_SIZE, expected_chunk_count: int = STAGE5_MAX_CHUNKS, output_root: str = DEFAULT_OUTPUT_ROOT, end_date: str | None = None, density_runner: DensityRunner = run_hist_density3, review_builder: ReviewBuilder = build_hist_density4_findings_review, execute_real_windows: bool = True, bundle_artifact_dir: str = "artifacts", supabase_write_enabled: bool = False, replay_activation_enabled: bool = False, topology_persistence_enabled: bool = False, raw_cache_write_enabled: bool = False) -> OrderedDict[str, Any]:
    plan = build_hist_long4_orchestration_plan(windows=windows, max_symbols=max_symbols, symbol_chunk_size=symbol_chunk_size, expected_chunk_count=expected_chunk_count, output_root=output_root, end_date=end_date, supabase_write_enabled=supabase_write_enabled, replay_activation_enabled=replay_activation_enabled, topology_persistence_enabled=topology_persistence_enabled, raw_cache_write_enabled=raw_cache_write_enabled)
    window_summaries: list[OrderedDict[str, Any]] = []
    parsed_sources: list[OrderedDict[str, Any]] = []
    if not execute_real_windows:
        raise ValueError("HIST-LONG-4 fails closed: execute_real_windows must remain True for real accumulation")
    for window in plan["windows"]:
        source_root = str(Path(output_root) / f"window_{int(window):03d}d")
        density_runner(
            trading_days=int(window),
            max_symbols=max_symbols,
            symbol_chunk_size=symbol_chunk_size,
            expected_chunk_count=expected_chunk_count,
            output_root=source_root,
            density_mode=DENSITY_MODE_REAL,
            raw_cache_enabled=False,
            raw_cache_write_enabled=False,
            cache_validation_mode=False,
            cache_only_validation=False,
            include_high_risk_symbols=False,
            apply_sde2_replacements=True,
            dry_run_config_only=False,
            end_date=plan["end_date"],
        )
        parsed = _parse_source_artifacts(source_root)
        review = review_builder(source_root)
        bundle_path = _bundle_source_root(source_root, window=int(window), artifact_dir=bundle_artifact_dir)
        summary = _window_summary(window=int(window), source_root=source_root, review=review, parsed=parsed, bundle_path=bundle_path, sector_profile=plan["sector_subsector_concentration_baseline"])
        _validate_completed_window(summary, plan)
        parsed_sources.append(OrderedDict([
            ("window_trading_days", int(window)),
            ("source_root", source_root),
            ("completed_bundle_path", bundle_path),
            ("parsed_artifact_counts", summary["parsed_artifact_counts"]),
        ]))
        window_summaries.append(summary)
    comparison = _build_comparison(window_summaries)
    all_completed = comparison["completed_window_count"] == len(REQUIRED_WINDOWS)
    checksum_input = json.dumps({"plan": plan, "windows": window_summaries, "comparison": comparison}, sort_keys=True, default=str)
    return OrderedDict([
        ("schema_version", HIST_LONG4_SCHEMA_VERSION),
        ("status", "ok" if all_completed else "blocked_incomplete_real_windows"),
        ("review_date", date.today().isoformat()),
        ("all_three_real_windows_completed", all_completed),
        ("governance_certification", _governance()),
        ("orchestration_plan", plan),
        ("completed_artifact_bundles", parsed_sources),
        ("window_level_results", window_summaries),
        ("longitudinal_comparison", comparison),
        ("bounded_diagnostics", OrderedDict([
            ("window_comparison_table", [{"window_trading_days": row["window_trading_days"], "normalized_rows": row["normalized_rows"], "completeness": row["completeness"], "partial_count": row["partial_count"], "failed_count": row["failed_count"], "weak_symbols": row["weak_symbols"]} for row in window_summaries]),
            ("strongest_recurring_sectors", comparison["concentration_diversity"]["strongest_recurring_sectors"]),
            ("strongest_recurring_subsectors", comparison["concentration_diversity"]["strongest_recurring_subsectors"]),
            ("recurring_weak_symbols", comparison["weak_symbol_analysis"]["recurring_weak_symbols"]),
            ("concentration_trend", comparison["concentration_trend"]),
            ("replay_persistence_trend", comparison["replay_persistence_trend"]),
        ])),
        ("operational_stability_assessment", OrderedDict([
            ("real_multi_window_status", "all_required_windows_completed" if all_completed else "incomplete"),
            ("five_chunk_envelope", "stable"),
            ("provider_degradation_trend", comparison["weak_symbol_analysis"]["provider_degradation_recurrence"]),
            ("foxa_assessment", comparison["weak_symbol_analysis"]["foxa_stability"]),
            ("governance_boundary", "observational_only_no_replay_no_supabase_no_raw_cache_write_no_topology_persistence"),
        ])),
        ("recommendation_for_hist_long5", "Proceed to HIST-LONG-5 with the same observational-only guards if operator accepts stable replay persistence and concentration drift findings; keep replay inactive and topology non-persistent." if all_completed else "Do not proceed to HIST-LONG-5 until all three real windows complete."),
        ("artifact_checksum", sha256(checksum_input.encode("utf-8")).hexdigest()),
    ])


def _md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return out


def render_hist_long4_markdown(artifact: Mapping[str, Any]) -> str:
    g = artifact["governance_certification"]
    comparison = artifact["longitudinal_comparison"]
    diagnostics = artifact["bounded_diagnostics"]
    lines = [
        "# HIST-LONG-4 — Real Multi-Window Ecology Accumulation Review",
        "",
    ]
    if artifact.get("status") != "ok":
        lines.extend([
            "## Execution Status",
            f"- Status: {artifact.get('status')}",
            f"- Execution error: {artifact.get('execution_error', 'none')}",
            f"- All three real windows completed: {artifact.get('all_three_real_windows_completed')}",
            "",
        ])
    lines.append("## Window-Level Results")
    lines.extend(_md_table(["Window", "Normalized rows", "Completeness", "Partial", "Failed", "Exact ratio", "Reconciled ratio", "Weak symbols"], [[row["window_trading_days"], row["normalized_rows"], row["completeness"], row["partial_count"], row["failed_count"], row["exact_date_ratio"], row["reconciled_date_ratio"], ", ".join(row["weak_symbols"]) or "none"] for row in artifact["window_level_results"]]))
    lines.extend(["", "### Parsed Artifact Bundles"])
    for bundle in artifact["completed_artifact_bundles"]:
        lines.append(f"- {bundle['window_trading_days']}d: bundle=`{bundle['completed_bundle_path']}`, parsed={json.dumps(bundle['parsed_artifact_counts'], sort_keys=True)}")
    lines.extend(["", "## Longitudinal Comparison"])
    lines.extend(_md_table(["Window", "Normalized", "Completeness", "Weak symbols"], [[row["window_trading_days"], row["normalized_rows"], row["completeness"], ", ".join(row["weak_symbols"]) or "none"] for row in diagnostics["window_comparison_table"]]))
    lines.extend([
        f"- Ingestion quality: `{json.dumps(comparison['ingestion_quality'], sort_keys=True)}`",
        f"- Ecology stability: `{json.dumps(comparison['ecology_stability'], sort_keys=True)}`",
        "",
        "## Weak Symbol Recurrence",
        f"- Recurring weak symbols: `{json.dumps(comparison['weak_symbol_analysis']['recurring_weak_symbols'], sort_keys=True)}`",
        f"- New weak symbols: `{json.dumps(comparison['weak_symbol_analysis']['new_weak_symbols'], sort_keys=True)}`",
        f"- FOXA stability: `{json.dumps(comparison['weak_symbol_analysis']['foxa_stability'], sort_keys=True)}`",
        "",
        "## Provider Degradation Trends",
        f"- Provider degradation recurrence: `{json.dumps(comparison['weak_symbol_analysis']['provider_degradation_recurrence'], sort_keys=True)}`",
        "",
        "## Replay Ecology Persistence",
        f"- Replay persistence trend: {diagnostics['replay_persistence_trend']}",
        f"- Replay density: `{json.dumps(comparison['ecology_stability']['replay_density'], sort_keys=True)}`",
        f"- Morphology persistence: `{json.dumps(comparison['ecology_stability']['morphology_persistence'], sort_keys=True)}`",
        "",
        "## Concentration Drift",
        f"- Concentration trend: {diagnostics['concentration_trend']}",
        f"- Sector HHI: `{json.dumps(comparison['concentration_diversity']['sector_hhi'], sort_keys=True)}`",
        f"- Subsector HHI: `{json.dumps(comparison['concentration_diversity']['subsector_hhi'], sort_keys=True)}`",
        f"- Strongest recurring sectors: `{json.dumps(diagnostics['strongest_recurring_sectors'], sort_keys=True)}`",
        f"- Strongest recurring subsectors: `{json.dumps(diagnostics['strongest_recurring_subsectors'], sort_keys=True)}`",
        "",
        "## Structural Stability",
        f"- Stable structures: `{json.dumps(comparison['structural_persistence']['stable_structures'], sort_keys=True)}`",
        f"- Decaying structures: `{json.dumps(comparison['structural_persistence']['decaying_structures'], sort_keys=True)}`",
        f"- Emerging structures: `{json.dumps(comparison['structural_persistence']['emerging_structures'], sort_keys=True)}`",
        f"- Propagation asymmetry: {comparison['structural_persistence']['propagation_asymmetry']}",
        "",
        "## Fragility Emergence",
        f"- Fragility clusters: `{json.dumps(comparison['structural_persistence']['fragility_clusters'], sort_keys=True)}`",
        "",
        "## Operational Stability Assessment",
    ])
    for key, value in artifact["operational_stability_assessment"].items():
        lines.append(f"- {key}: `{json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value}`")
    lines.extend([
        "",
        "## Governance Certification",
        f"- Governance mode: {g['governance_mode']}",
        f"- Prediction enabled: {g['prediction_enabled']}",
        f"- Trading execution enabled: {g['trading_execution_enabled']}",
        f"- Replay activation enabled: {g['replay_activation_enabled']}",
        f"- Replay execution enabled: {g['replay_execution_enabled']}",
        f"- Topology persistence enabled: {g['topology_persistence_enabled']}",
        f"- Supabase writes enabled: {g['supabase_write_enabled']}",
        f"- Raw cache writes enabled: {g['raw_cache_write_enabled']}",
        f"- Local artifacts only: {g['local_artifacts_only']}",
        "",
        "## Recommendation For HIST-LONG-5",
        f"- {artifact['recommendation_for_hist_long5']}",
    ])
    return "\n".join(lines) + "\n"


def _blocked_hist_long4_artifact(*, execution_error: str, report_path: str, artifact_path: str, **kwargs: Any) -> OrderedDict[str, Any]:
    plan = build_hist_long4_orchestration_plan(
        windows=kwargs.get("windows", REQUIRED_WINDOWS),
        max_symbols=kwargs.get("max_symbols", DEFAULT_MAX_SYMBOLS),
        symbol_chunk_size=kwargs.get("symbol_chunk_size", DEFAULT_SYMBOL_CHUNK_SIZE),
        expected_chunk_count=kwargs.get("expected_chunk_count", STAGE5_MAX_CHUNKS),
        output_root=kwargs.get("output_root", DEFAULT_OUTPUT_ROOT),
        end_date=kwargs.get("end_date"),
    )
    empty_comparison = OrderedDict([
        ("windows", list(plan["windows"])),
        ("completed_window_count", 0),
        ("ingestion_quality", OrderedDict([
            ("normalized_rows", OrderedDict([("values", []), ("trend", "insufficient_windows")])),
            ("completeness", OrderedDict([("values", []), ("trend", "insufficient_windows"), ("volatility", None)])),
            ("partial_counts", []),
            ("failed_counts", []),
            ("exact_date_match_ratios", OrderedDict([("values", []), ("trend", "insufficient_windows")])),
            ("reconciled_date_ratios", OrderedDict([("values", []), ("trend", "insufficient_windows")])),
            ("endpoint_failure_window_count", 0),
        ])),
        ("ecology_stability", OrderedDict([
            ("replay_density", OrderedDict([("values", []), ("trend", "insufficient_windows"), ("activation_status", "not_activated")])),
            ("contradiction_burden", OrderedDict([("values", []), ("trend", "insufficient_windows"), ("volatility", None)])),
            ("topology_richness", OrderedDict([("values", []), ("trend", "insufficient_windows"), ("persistence_status", "report_local_not_persisted")])),
            ("morphology_persistence", OrderedDict([("posture_recurrence", []), ("assessment", "blocked_no_completed_real_windows")])),
            ("temporal_persistence", "blocked_no_completed_real_windows"),
            ("replay_saturation", "not_activated_density_only"),
        ])),
        ("concentration_diversity", OrderedDict([
            ("sector_hhi", OrderedDict([("values", []), ("trend", "insufficient_windows")])),
            ("subsector_hhi", OrderedDict([("values", []), ("trend", "insufficient_windows")])),
            ("strongest_recurring_sectors", []),
            ("strongest_recurring_subsectors", []),
            ("monoculture_risk", []),
            ("diversity_persistence", "blocked_no_completed_real_windows"),
            ("concentration_drift", "insufficient_windows"),
        ])),
        ("weak_symbol_analysis", OrderedDict([
            ("recurring_weak_symbols", []),
            ("new_weak_symbols", []),
            ("weak_symbol_recurrence", []),
            ("provider_degradation_recurrence", []),
            ("foxa_stability", OrderedDict([("present_all_windows", False), ("weak_windows", []), ("assessment", "blocked_no_completed_real_windows")])),
        ])),
        ("structural_persistence", OrderedDict([
            ("stable_structures", ["observational_governance"]),
            ("decaying_structures", []),
            ("emerging_structures", []),
            ("propagation_asymmetry", "blocked_no_completed_real_windows"),
            ("fragility_clusters", ["not_assessed"]),
        ])),
        ("replay_persistence_trend", "insufficient_windows"),
        ("concentration_trend", "insufficient_windows"),
    ])
    return OrderedDict([
        ("schema_version", HIST_LONG4_SCHEMA_VERSION),
        ("status", "blocked_provider_credentials_missing_or_execution_failed"),
        ("review_date", date.today().isoformat()),
        ("execution_error", execution_error),
        ("all_three_real_windows_completed", False),
        ("governance_certification", _governance()),
        ("orchestration_plan", plan),
        ("completed_artifact_bundles", []),
        ("window_level_results", []),
        ("longitudinal_comparison", empty_comparison),
        ("bounded_diagnostics", OrderedDict([
            ("window_comparison_table", []),
            ("strongest_recurring_sectors", []),
            ("strongest_recurring_subsectors", []),
            ("recurring_weak_symbols", []),
            ("concentration_trend", "insufficient_windows"),
            ("replay_persistence_trend", "insufficient_windows"),
        ])),
        ("operational_stability_assessment", OrderedDict([
            ("real_multi_window_status", "blocked_before_all_required_windows_completed"),
            ("five_chunk_envelope", "preflight_only"),
            ("provider_degradation_trend", []),
            ("foxa_assessment", empty_comparison["weak_symbol_analysis"]["foxa_stability"]),
            ("governance_boundary", "observational_only_no_replay_no_supabase_no_raw_cache_write_no_topology_persistence"),
        ])),
        ("recommendation_for_hist_long5", "Do not proceed to HIST-LONG-5 until all three real windows complete under HIST-LONG-4 guards."),
        ("artifact_paths", OrderedDict([("report_path", report_path), ("artifact_path", artifact_path)])),
    ])


def write_hist_long4_review(*, report_path: str = DEFAULT_REPORT_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH, **kwargs: Any) -> OrderedDict[str, Any]:
    try:
        artifact = run_hist_long4(**kwargs)
    except Exception as exc:
        artifact = _blocked_hist_long4_artifact(execution_error=str(exc), report_path=report_path, artifact_path=artifact_path, **kwargs)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_hist_long4_markdown(artifact), encoding="utf-8")
    return artifact
