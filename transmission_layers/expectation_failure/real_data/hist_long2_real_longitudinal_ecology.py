from __future__ import annotations

import json
from collections import Counter, OrderedDict
from datetime import date
from hashlib import sha256
from pathlib import Path
from statistics import pstdev
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
from transmission_layers.expectation_failure.real_data.hist_long1_longitudinal_ecology import _mean, _range, _trend, _volatility

HIST_LONG2_SCHEMA_VERSION = "hist_long2_v1"
DEFAULT_WINDOWS = (20, 60, 120)
DEFAULT_COMPLETED_SOURCES = (
    {
        "window_days": 20,
        "label": "hist_density4_completed_241_symbol_20d_baseline",
        "artifact_path": "artifacts/hist_density4_241_symbol_findings_review.json",
    },
)
DEFAULT_OUTPUT_ROOT = "reports/hist_long2_windows"
DEFAULT_REPORT_PATH = "reports/hist_long2_real_longitudinal_ecology_review.md"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_long2_real_longitudinal_ecology_review.json"

DensityRunner = Callable[..., Mapping[str, Any]]
ReviewBuilder = Callable[[str], Mapping[str, Any]]


def _governance() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("governance_mode", "observational_only"),
        ("phase", "HIST-LONG-2_real_multi_window_longitudinal_ecology_accumulation"),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("replay_activation_enabled", False),
        ("replay_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("topology_activation_enabled", False),
        ("supabase_write_enabled", False),
        ("raw_cache_write_enabled", False),
        ("local_artifacts_only", True),
        ("observational_report_only", True),
    ])


def _guard_plan(*, windows: Sequence[int], max_symbols: int, symbol_chunk_size: int, expected_chunk_count: int, raw_cache_write_enabled: bool, supabase_write_enabled: bool, replay_activation_enabled: bool, topology_persistence_enabled: bool) -> tuple[int, ...]:
    if not windows:
        raise ValueError("HIST-LONG-2 fails closed: at least one window is required")
    clean_windows = tuple(int(w) for w in windows)
    if any(w < 1 or w > 180 for w in clean_windows):
        raise ValueError("HIST-LONG-2 fails closed: window_days must be 1..180")
    if max_symbols > DEFAULT_MAX_SYMBOLS:
        raise ValueError("HIST-LONG-2 fails closed: max_symbols must be <= 241")
    if symbol_chunk_size != DEFAULT_SYMBOL_CHUNK_SIZE:
        raise ValueError("HIST-LONG-2 fails closed: symbol_chunk_size must remain 50")
    if expected_chunk_count != STAGE5_MAX_CHUNKS:
        raise ValueError("HIST-LONG-2 fails closed: expected_chunk_count must equal 5")
    if raw_cache_write_enabled:
        raise ValueError("HIST-LONG-2 fails closed: raw cache writes are forbidden")
    if supabase_write_enabled:
        raise ValueError("HIST-LONG-2 fails closed: Supabase writes are forbidden")
    if replay_activation_enabled:
        raise ValueError("HIST-LONG-2 fails closed: replay activation is forbidden")
    if topology_persistence_enabled:
        raise ValueError("HIST-LONG-2 fails closed: topology persistence is forbidden")
    return clean_windows


def build_hist_long2_orchestration_plan(*, windows: Sequence[int] = DEFAULT_WINDOWS, max_symbols: int = DEFAULT_MAX_SYMBOLS, symbol_chunk_size: int = DEFAULT_SYMBOL_CHUNK_SIZE, expected_chunk_count: int = STAGE5_MAX_CHUNKS, output_root: str = DEFAULT_OUTPUT_ROOT, end_date: str | None = None, raw_cache_write_enabled: bool = False, supabase_write_enabled: bool = False, replay_activation_enabled: bool = False, topology_persistence_enabled: bool = False) -> OrderedDict[str, Any]:
    clean_windows = _guard_plan(windows=windows, max_symbols=max_symbols, symbol_chunk_size=symbol_chunk_size, expected_chunk_count=expected_chunk_count, raw_cache_write_enabled=raw_cache_write_enabled, supabase_write_enabled=supabase_write_enabled, replay_activation_enabled=replay_activation_enabled, topology_persistence_enabled=topology_persistence_enabled)
    symbols, universe_tel = _effective_symbols(max_symbols=max_symbols, include_high_risk_symbols=False, apply_sde2_replacements=True)
    if len(symbols) > DEFAULT_MAX_SYMBOLS:
        raise ValueError("HIST-LONG-2 fails closed: effective universe exceeds 241 symbols")
    chunk_count = (len(symbols) + symbol_chunk_size - 1) // symbol_chunk_size
    if chunk_count != expected_chunk_count:
        raise ValueError("HIST-LONG-2 fails closed: updated universe must resolve to five chunks")
    return OrderedDict([
        ("schema_version", HIST_LONG2_SCHEMA_VERSION),
        ("status", "ok"),
        ("orchestration_date", date.today().isoformat()),
        ("end_date", end_date or date.today().isoformat()),
        ("windows", list(clean_windows)),
        ("max_symbols", max_symbols),
        ("symbol_chunk_size", symbol_chunk_size),
        ("expected_chunk_count", expected_chunk_count),
        ("output_root", output_root),
        ("density_mode", DENSITY_MODE_REAL),
        ("raw_cache_write_enabled", False),
        ("effective_symbol_count", len(symbols)),
        ("updated_universe_contains_foxa", "FOXA" in symbols),
        ("updated_universe_contains_para", "PARA" in symbols),
        ("universe_telemetry", OrderedDict(sorted(dict(universe_tel).items()))),
        ("governance_certification", _governance()),
    ])


def _load_review_from_source(source: Mapping[str, Any], review_builder: ReviewBuilder = build_hist_density4_findings_review) -> OrderedDict[str, Any]:
    label = str(source.get("label") or source.get("artifact_path") or source.get("source_root") or "unnamed_source")
    if source.get("artifact_path"):
        path = Path(str(source["artifact_path"]))
        payload = json.loads(path.read_text(encoding="utf-8"))
        source_kind = "completed_review_artifact"
        source_path = str(path)
    elif source.get("source_root"):
        source_path = str(source["source_root"])
        payload = dict(review_builder(source_path))
        source_kind = "completed_source_root"
    else:
        raise ValueError("HIST-LONG-2 fails closed: completed source requires artifact_path or source_root")
    return OrderedDict([
        ("label", label),
        ("window_days", int(source.get("window_days") or (payload.get("ingestion_quality", {}).get("aggregate", {}) or {}).get("trading_days") or 0)),
        ("source_kind", source_kind),
        ("source_path", source_path),
        ("review", payload),
    ])


def _counter_rows(counter: Counter[str], key_name: str) -> list[OrderedDict[str, Any]]:
    return [OrderedDict([(key_name, key), ("window_count", int(value))]) for key, value in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))]


def _sum_endpoint_failures(rows: Iterable[Mapping[str, Any]]) -> OrderedDict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for key, value in (row.get("endpoint_status_counts", {}) or {}).items():
            text = str(key)
            if "403" in text or "http" in text.lower() or "zero_records" in text.lower() or "fail" in text.lower() or "error" in text.lower():
                counts[text] += int(value or 0)
        for failure in row.get("top_failure_reasons", []) or []:
            counts[str(failure.get("reason", "unknown"))] += int(failure.get("count", 0) or 0)
    return OrderedDict((key, int(value)) for key, value in sorted(counts.items()))


def _window_summary(source_row: Mapping[str, Any]) -> OrderedDict[str, Any]:
    review = source_row["review"]
    ingestion = review.get("ingestion_quality", {}) or {}
    agg = ingestion.get("aggregate", {}) or {}
    chunk_rows = list(ingestion.get("chunk_quality_rows", []) or [])
    weak_rows = list(review.get("weak_symbol_review", []) or [])
    ecology = review.get("ecology_findings", {}) or {}
    ops_sources = review.get("source_artifacts_inspected", {}) or {}
    normalized = int(agg.get("normalized_count_total") or 0)
    capacity = int(agg.get("requested_symbol_date_capacity_total") or agg.get("estimated_symbol_date_rows") or 0)
    exact = int(agg.get("exact_date_matches_total") or 0)
    reconciled = int(agg.get("reconciled_prior_dates_total") or 0)
    missing = int(agg.get("missing_dates_total") or 0)
    partial = int(agg.get("partial_count_total") or 0)
    failed = int(agg.get("failed_count_total") or 0)
    densities = [row.get("normalization_density") for row in chunk_rows if isinstance(row.get("normalization_density"), (int, float))]
    hhi_values = []
    for row in ecology.get("chunk_diagnostics", []) or []:
        hhi = row.get("sector_hhi_average")
        if isinstance(hhi, (int, float)):
            hhi_values.append(float(hhi))
    topology_values = []
    for row in ecology.get("chunk_diagnostics", []) or []:
        richness = row.get("structural_richness", {}) or {}
        topology_values.append(int(richness.get("sector_transition_rows") or 0) + int(richness.get("posture_variety") or 0))
    symbols: list[str] = []
    for row in chunk_rows:
        symbols.extend(str(s).upper() for s in (row.get("chunk_symbols", []) or []))
    weak_symbols = [str(row.get("symbol", "")).upper() for row in weak_rows if row.get("symbol")]
    mode_markers = sorted({str(row.get("mode")) for row in chunk_rows if row.get("mode")})
    return OrderedDict([
        ("label", source_row["label"]),
        ("window_trading_days", int(source_row["window_days"])),
        ("source_kind", source_row["source_kind"]),
        ("source_path", source_row["source_path"]),
        ("source_status", review.get("source_status")),
        ("source_mode", review.get("source_mode")),
        ("completed_telemetry_mode", bool(review.get("completed_telemetry_mode"))),
        ("real_completed_telemetry_used", bool(review.get("completed_telemetry_mode")) and normalized > 0 and review.get("source_mode") != "config_preview_only"),
        ("chunk_count", int(agg.get("chunk_count") or len(chunk_rows))),
        ("ops_hist_snapshot_count", int(ops_sources.get("ops_hist_snapshot_count") or ecology.get("snapshot_count") or 0)),
        ("configured_symbol_count", int(agg.get("configured_symbol_count") or 0)),
        ("effective_symbol_count", int(agg.get("effective_symbol_count") or 0)),
        ("normalized_rows", normalized),
        ("requested_symbol_date_capacity_total", capacity),
        ("normalization_completeness", OrderedDict([("density", round(normalized / capacity, 6) if capacity else None), ("chunk_density_range", _range(densities)), ("chunk_density_mean", _mean(densities))])),
        ("partial_failed_counts", OrderedDict([("partial_count_total", partial), ("failed_count_total", failed), ("missing_dates_total", missing)])),
        ("historical_date_alignment", OrderedDict([("exact_date_matches_total", exact), ("reconciled_prior_dates_total", reconciled), ("exact_date_ratio", round(exact / max(normalized, 1), 6) if normalized else None), ("reconciled_date_ratio", round(reconciled / max(normalized, 1), 6) if normalized else None)])),
        ("weak_symbols", weak_symbols),
        ("weak_symbol_details", weak_rows),
        ("provider_degradation", OrderedDict([("endpoint_failures", OrderedDict(sorted((agg.get("endpoint_failures") or _sum_endpoint_failures(chunk_rows)).items()))), ("top_failure_reasons", agg.get("top_failure_reasons", []))])),
        ("sector_hhi", OrderedDict([("range", _range(hhi_values)), ("drift_proxy", round(max(hhi_values) - min(hhi_values), 6) if hhi_values else None)])),
        ("subsector_hhi", OrderedDict([("range", _range(hhi_values)), ("drift_proxy", round(max(hhi_values) - min(hhi_values), 6) if hhi_values else None)])),
        ("replay_density", round(normalized / capacity, 6) if capacity else None),
        ("contradiction_persistence", OrderedDict([("burden_count", missing + partial + failed), ("burden_ratio", round((missing + partial + failed) / capacity, 6) if capacity else None)])),
        ("morphology_persistence", OrderedDict([("posture_stability", ecology.get("posture_stability")), ("posture_counts", ecology.get("posture_counts", {}))])),
        ("topology_richness", OrderedDict([("chunk_richness_range", _range(topology_values)), ("chunk_richness_average", _mean(topology_values)), ("topology_persistence_enabled", False)])),
        ("monoculture_risk", (review.get("first_ecology_findings", {}) or {}).get("monoculture_risk") or (review.get("ecology_findings", {}) or {}).get("monoculture_risk")),
        ("temporal_stability", OrderedDict([("days", ecology.get("temporal_stability_days") or source_row["window_days"]), ("assessment", "stable_single_posture" if ecology.get("posture_stability") == "stable_single_posture" else "mixed_or_unavailable")])),
        ("foxa_present", "FOXA" in symbols),
        ("foxa_weak", "FOXA" in weak_symbols),
        ("para_present", "PARA" in symbols),
        ("fixture_mode_markers", mode_markers),
    ])


def build_hist_long2_comparison(window_summaries: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    ordered = sorted(window_summaries, key=lambda row: (int(row["window_trading_days"]), str(row["label"])))
    weak_counter: Counter[str] = Counter()
    provider_counter: Counter[str] = Counter()
    posture_counter: Counter[str] = Counter()
    for row in ordered:
        weak_counter.update(row.get("weak_symbols", []) or [])
        for reason in (row.get("provider_degradation", {}) or {}).get("top_failure_reasons", []) or []:
            provider_counter[str(reason.get("reason", "unknown"))] += 1
        posture = (row.get("morphology_persistence", {}) or {}).get("posture_stability")
        if posture:
            posture_counter[str(posture)] += 1
    normalized_values = [row.get("normalized_rows") for row in ordered]
    density_values = [row.get("replay_density") for row in ordered]
    burden_values = [(row.get("contradiction_persistence", {}) or {}).get("burden_ratio") for row in ordered]
    topology_values = [(row.get("topology_richness", {}) or {}).get("chunk_richness_average") for row in ordered]
    sector_drift = [(row.get("sector_hhi", {}) or {}).get("drift_proxy") for row in ordered]
    subsector_drift = [(row.get("subsector_hhi", {}) or {}).get("drift_proxy") for row in ordered]
    exact_values = [(row.get("historical_date_alignment", {}) or {}).get("exact_date_ratio") for row in ordered]
    reconciled_values = [(row.get("historical_date_alignment", {}) or {}).get("reconciled_date_ratio") for row in ordered]
    return OrderedDict([
        ("window_count", len(ordered)),
        ("windows", [int(row["window_trading_days"]) for row in ordered]),
        ("real_completed_window_count", sum(1 for row in ordered if row.get("real_completed_telemetry_used"))),
        ("normalized_rows", OrderedDict([("values", normalized_values), ("trend", _trend(normalized_values))])),
        ("normalization_completeness", OrderedDict([("density_values", density_values), ("trend", _trend(density_values)), ("volatility", _volatility(density_values))])),
        ("partial_failed_counts", [row.get("partial_failed_counts") for row in ordered]),
        ("weak_symbol_recurrence", _counter_rows(weak_counter, "symbol")),
        ("provider_degradation_recurrence", _counter_rows(provider_counter, "reason")),
        ("historical_date_alignment", OrderedDict([("exact_date_ratio_values", exact_values), ("reconciled_date_ratio_values", reconciled_values), ("exact_trend", _trend(exact_values)), ("reconciled_trend", _trend(reconciled_values))])),
        ("sector_hhi_drift", OrderedDict([("values", sector_drift), ("trend", _trend(sector_drift))])),
        ("subsector_hhi_drift", OrderedDict([("values", subsector_drift), ("trend", _trend(subsector_drift))])),
        ("replay_density", OrderedDict([("values", density_values), ("trend", _trend(density_values)), ("activation_status", "not_activated")])),
        ("contradiction_persistence", OrderedDict([("burden_values", burden_values), ("trend", _trend(burden_values)), ("volatility", _volatility(burden_values))])),
        ("morphology_persistence", OrderedDict([("posture_recurrence", _counter_rows(posture_counter, "posture")), ("assessment", "stable_across_real_windows" if len(posture_counter) == 1 and len(ordered) > 1 else "single_window_or_mixed")])),
        ("topology_richness", OrderedDict([("values", topology_values), ("trend", _trend(topology_values)), ("persistence_status", "report_local_not_persisted")])),
        ("monoculture_risk", [row.get("monoculture_risk") for row in ordered]),
        ("temporal_stability", OrderedDict([("assessment", "insufficient_real_multi_window_evidence" if len(ordered) < 2 else "multi_window_comparison_available"), ("density_decay", _trend(density_values))])),
        ("foxa_validation", OrderedDict([("foxa_present_windows", [row["label"] for row in ordered if row.get("foxa_present")]), ("foxa_weak_windows", [row["label"] for row in ordered if row.get("foxa_weak")]), ("status", "healthy_in_real_completed_windows" if any(row.get("foxa_present") for row in ordered) and not any(row.get("foxa_weak") for row in ordered) else "not_validated_by_completed_real_window")])),
    ])


def build_hist_long2_artifact(*, plan: Mapping[str, Any], sources: Sequence[Mapping[str, Any]], review_builder: ReviewBuilder = build_hist_density4_findings_review, new_execution_run: bool = False) -> OrderedDict[str, Any]:
    source_rows = [_load_review_from_source(source, review_builder=review_builder) for source in sources]
    summaries = [_window_summary(source_row) for source_row in source_rows]
    for row in summaries:
        if int(row["chunk_count"]) != int(plan["expected_chunk_count"]):
            raise ValueError("HIST-LONG-2 fails closed: ingested completed artifact does not contain five chunks")
        if row.get("completed_telemetry_mode") is not True:
            raise ValueError("HIST-LONG-2 fails closed: config-only fallback is not accepted for HIST-LONG-2")
    comparison = build_hist_long2_comparison(summaries)
    checksum_input = json.dumps({"plan": plan, "summaries": summaries, "comparison": comparison, "new_execution_run": new_execution_run}, sort_keys=True, default=str)
    real_used = any(row.get("real_completed_telemetry_used") for row in summaries)
    return OrderedDict([
        ("schema_version", HIST_LONG2_SCHEMA_VERSION),
        ("status", "ok" if real_used else "blocked_no_real_completed_telemetry"),
        ("review_date", date.today().isoformat()),
        ("real_completed_telemetry_used", real_used),
        ("new_real_execution_run", bool(new_execution_run)),
        ("execution_mode", "completed_artifact_ingestion_only" if not new_execution_run else "real_bounded_execution_plus_artifact_ingestion"),
        ("governance_certification", _governance()),
        ("orchestration_plan", OrderedDict(plan)),
        ("real_artifact_sources", [OrderedDict((k, source_row[k]) for k in ("label", "window_days", "source_kind", "source_path")) for source_row in source_rows]),
        ("window_level_ingestion_quality", summaries),
        ("longitudinal_comparison_summary", comparison),
        ("operational_stability_assessment", OrderedDict([
            ("real_multi_window_status", "multi_window_real_comparison_available" if comparison["real_completed_window_count"] >= 2 else "only_one_completed_real_window_available"),
            ("foxa_validation_status", comparison["foxa_validation"]["status"]),
            ("provider_degradation_trend", comparison["provider_degradation_recurrence"]),
            ("recommendation", "Run the next bounded real updated-universe 20d/60d windows before longer accumulation." if comparison["real_completed_window_count"] < 2 else "Proceed only with bounded observational accumulation."),
        ])),
        ("governance_certification_summary", "Observed only; no replay activation, prediction, trading, topology persistence, Supabase writes, or raw cache writes."),
        ("recommendation_for_next_phase", "Proceed to a bounded real updated-universe validation window before 60d/120d accumulation; do not activate replay/topology/trading." if comparison["foxa_validation"]["status"] != "healthy_in_real_completed_windows" else "Safe to proceed to additional bounded real windows under HIST-LONG-2 guards."),
        ("artifact_checksum", sha256(checksum_input.encode("utf-8")).hexdigest()),
    ])


def render_hist_long2_markdown(artifact: Mapping[str, Any]) -> str:
    comparison = artifact["longitudinal_comparison_summary"]
    g = artifact["governance_certification"]
    lines = [
        "# HIST-LONG-2 — Real Multi-Window Longitudinal Ecology Review",
        "",
        "## Real Artifact Sources",
        f"- Real completed telemetry used: {artifact['real_completed_telemetry_used']}",
        f"- New real execution run: {artifact['new_real_execution_run']}",
        f"- Execution mode: {artifact['execution_mode']}",
    ]
    for src in artifact["real_artifact_sources"]:
        lines.append(f"- {src['label']}: window_days={src['window_days']}, kind={src['source_kind']}, path=`{src['source_path']}`")
    lines.extend(["", "## Window-Level Ingestion Quality"])
    for row in artifact["window_level_ingestion_quality"]:
        lines.append(f"- {row['label']}: days={row['window_trading_days']}, chunks={row['chunk_count']}, snapshots={row['ops_hist_snapshot_count']}, normalized={row['normalized_rows']}/{row['requested_symbol_date_capacity_total']}, completeness={row['normalization_completeness']['density']}, exact_ratio={row['historical_date_alignment']['exact_date_ratio']}, reconciled_ratio={row['historical_date_alignment']['reconciled_date_ratio']}, partial_failed={json.dumps(row['partial_failed_counts'], sort_keys=True)}, weak={row['weak_symbols']}")
    lines.extend([
        "",
        "## Weak Symbol Recurrence",
        f"- {json.dumps(comparison['weak_symbol_recurrence'], sort_keys=True)}",
        "",
        "## Provider Degradation Recurrence",
        f"- {json.dumps(comparison['provider_degradation_recurrence'], sort_keys=True)}",
        "",
        "## Replay/Topology Ecology Findings",
        f"- Replay density: {json.dumps(comparison['replay_density'], sort_keys=True)}",
        f"- Topology richness: {json.dumps(comparison['topology_richness'], sort_keys=True)}",
        f"- Morphology persistence: {json.dumps(comparison['morphology_persistence'], sort_keys=True)}",
        "",
        "## Sector/Subsector Concentration Drift",
        f"- Sector HHI drift: {json.dumps(comparison['sector_hhi_drift'], sort_keys=True)}",
        f"- Subsector HHI drift: {json.dumps(comparison['subsector_hhi_drift'], sort_keys=True)}",
        f"- Monoculture risk: {json.dumps(comparison['monoculture_risk'], sort_keys=True)}",
        "",
        "## Temporal Stability and Decay",
        f"- {json.dumps(comparison['temporal_stability'], sort_keys=True)}",
        f"- Historical date alignment: {json.dumps(comparison['historical_date_alignment'], sort_keys=True)}",
        f"- Contradiction persistence: {json.dumps(comparison['contradiction_persistence'], sort_keys=True)}",
        "",
        "## Operational Stability Assessment",
    ])
    for key, value in artifact["operational_stability_assessment"].items():
        lines.append(f"- {key}: {json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value}")
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
        "## Recommendation for next phase",
        f"- {artifact['recommendation_for_next_phase']}",
    ])
    return "\n".join(lines) + "\n"


def run_hist_long2(*, windows: Sequence[int] = DEFAULT_WINDOWS, completed_sources: Sequence[Mapping[str, Any]] = DEFAULT_COMPLETED_SOURCES, execute_real_windows: bool = False, max_symbols: int = DEFAULT_MAX_SYMBOLS, symbol_chunk_size: int = DEFAULT_SYMBOL_CHUNK_SIZE, expected_chunk_count: int = STAGE5_MAX_CHUNKS, output_root: str = DEFAULT_OUTPUT_ROOT, end_date: str | None = None, density_runner: DensityRunner = run_hist_density3, review_builder: ReviewBuilder = build_hist_density4_findings_review) -> OrderedDict[str, Any]:
    plan = build_hist_long2_orchestration_plan(windows=windows, max_symbols=max_symbols, symbol_chunk_size=symbol_chunk_size, expected_chunk_count=expected_chunk_count, output_root=output_root, end_date=end_date)
    sources = [dict(source) for source in completed_sources]
    new_execution_run = False
    if execute_real_windows:
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
            sources.append({"window_days": int(window), "label": f"real_bounded_execution_{int(window):03d}d", "source_root": source_root})
            new_execution_run = True
    return build_hist_long2_artifact(plan=plan, sources=sources, review_builder=review_builder, new_execution_run=new_execution_run)


def write_hist_long2_review(*, report_path: str = DEFAULT_REPORT_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH, **kwargs: Any) -> OrderedDict[str, Any]:
    artifact = run_hist_long2(**kwargs)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_hist_long2_markdown(artifact), encoding="utf-8")
    return artifact
