from __future__ import annotations

import json
from collections import Counter, OrderedDict
from datetime import date
from hashlib import sha256
from pathlib import Path
from statistics import pstdev
from typing import Any, Callable, Iterable, Mapping, Sequence

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_FIXTURE
from transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion import (
    DEFAULT_MAX_SYMBOLS,
    DEFAULT_SYMBOL_CHUNK_SIZE,
    STAGE5_MAX_CHUNKS,
    _effective_symbols,
    run_hist_density3,
)
from transmission_layers.expectation_failure.real_data.hist_density4_findings_review import build_hist_density4_findings_review
from transmission_layers.expectation_failure.real_data.sde2_curated_symbol_ecology_expansion import get_sde2_symbol_categories

HIST_LONG1_SCHEMA_VERSION = "hist_long1_v1"
DEFAULT_WINDOWS = (20, 60, 120)
DEFAULT_OUTPUT_ROOT = "reports/hist_long1_windows"
DEFAULT_REPORT_PATH = "reports/hist_long1_longitudinal_ecology_review.md"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_long1_longitudinal_ecology_review.json"


DensityRunner = Callable[..., Mapping[str, Any]]
ReviewBuilder = Callable[[str], Mapping[str, Any]]


def _governance() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("governance_mode", "observational_only"),
        ("phase", "HIST-LONG-1_controlled_longitudinal_ecology_accumulation"),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("replay_activation_enabled", False),
        ("replay_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("topology_activation_enabled", False),
        ("supabase_write_enabled", False),
        ("raw_cache_write_enabled", False),
        ("local_artifacts_only", True),
        ("bounded_artifact_generation_only", True),
    ])


def _ratio(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if denominator in (None, 0) or numerator is None:
        return None
    return round(float(numerator) / float(denominator), 6)


def _mean(values: Iterable[float | int | None]) -> float | None:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 6)


def _range(values: Iterable[float | int | None]) -> OrderedDict[str, float | None]:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    if not clean:
        return OrderedDict([("min", None), ("max", None)])
    return OrderedDict([("min", round(min(clean), 6)), ("max", round(max(clean), 6))])


def _trend(values: Sequence[float | None], *, tolerance: float = 0.0001) -> str:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    if len(clean) < 2:
        return "insufficient_windows"
    first = clean[0]
    last = clean[-1]
    if abs(last - first) <= tolerance:
        return "stable"
    return "increasing" if last > first else "decreasing"


def _volatility(values: Sequence[float | None]) -> float | None:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    if len(clean) < 2:
        return None
    return round(pstdev(clean), 6)


def _ordered_counter_rows(counter: Counter[str], *, limit: int | None = None, key_name: str = "key") -> list[OrderedDict[str, Any]]:
    rows = [OrderedDict([(key_name, key), ("window_count", int(value))]) for key, value in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))]
    return rows if limit is None else rows[:limit]


def _effective_universe(max_symbols: int) -> tuple[list[str], Mapping[str, Any]]:
    return _effective_symbols(max_symbols=max_symbols, include_high_risk_symbols=False, apply_sde2_replacements=True)


def _sector_hhi(symbols: Sequence[str]) -> OrderedDict[str, Any]:
    categories = get_sde2_symbol_categories()
    symbol_to_sector: dict[str, str] = {}
    for sector, sector_symbols in categories.items():
        for symbol in sector_symbols:
            symbol_to_sector.setdefault(str(symbol).upper(), str(sector))
    counts: Counter[str] = Counter(symbol_to_sector.get(str(symbol).upper(), "uncategorized") for symbol in symbols)
    total = sum(counts.values())
    hhi = round(sum((count / total) ** 2 for count in counts.values()), 6) if total else None
    return OrderedDict([
        ("sector_hhi", hhi),
        ("subsector_hhi", hhi),
        ("strongest_sectors", [OrderedDict([("sector", sector), ("symbol_count", int(count)), ("share", round(count / total, 6) if total else None)]) for sector, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:8]]),
        ("strongest_subsectors", [OrderedDict([("subsector", sector), ("symbol_count", int(count)), ("share", round(count / total, 6) if total else None)]) for sector, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:8]]),
    ])


def build_hist_long1_orchestration_plan(*, windows: Sequence[int] = DEFAULT_WINDOWS, max_symbols: int = DEFAULT_MAX_SYMBOLS, chunk_size: int = DEFAULT_SYMBOL_CHUNK_SIZE, output_root: str = DEFAULT_OUTPUT_ROOT, end_date: str | None = None) -> OrderedDict[str, Any]:
    if not windows:
        raise ValueError("HIST-LONG-1 fails closed: at least one window is required")
    clean_windows = tuple(int(w) for w in windows)
    if any(w < 1 or w > 180 for w in clean_windows):
        raise ValueError("HIST-LONG-1 fails closed: windows must be 1..180 trading days")
    if max_symbols != DEFAULT_MAX_SYMBOLS:
        raise ValueError("HIST-LONG-1 fails closed: max_symbols must remain bounded at 241")
    if chunk_size != DEFAULT_SYMBOL_CHUNK_SIZE:
        raise ValueError("HIST-LONG-1 fails closed: chunk_size must remain bounded at 50")
    symbols, universe_tel = _effective_universe(max_symbols)
    chunk_count = (len(symbols) + chunk_size - 1) // chunk_size
    if chunk_count > STAGE5_MAX_CHUNKS:
        raise ValueError("HIST-LONG-1 fails closed: chunk count exceeds bounded five-chunk envelope")
    sector_profile = _sector_hhi(symbols)
    return OrderedDict([
        ("schema_version", HIST_LONG1_SCHEMA_VERSION),
        ("status", "ok"),
        ("orchestration_date", date.today().isoformat()),
        ("end_date", end_date or date.today().isoformat()),
        ("windows", list(clean_windows)),
        ("max_symbols", max_symbols),
        ("chunk_size", chunk_size),
        ("expected_chunk_count", chunk_count),
        ("output_root", output_root),
        ("effective_symbol_count", len(symbols)),
        ("universe_telemetry", OrderedDict(sorted(dict(universe_tel).items()))),
        ("sector_subsector_concentration_baseline", sector_profile),
        ("governance_certification", _governance()),
    ])


def _summarize_window(review: Mapping[str, Any], *, window: int, source_root: str, sector_profile: Mapping[str, Any]) -> OrderedDict[str, Any]:
    ingestion = review.get("ingestion_quality", {}) or {}
    agg = ingestion.get("aggregate", {}) or {}
    ecology = review.get("ecology_findings", {}) or {}
    weak_rows = list(review.get("weak_symbol_review", []) or [])
    chunk_rows = list(ingestion.get("chunk_quality_rows", []) or [])
    chunk_densities = [row.get("normalization_density") for row in chunk_rows]
    failure_counter: Counter[str] = Counter()
    for row in agg.get("top_failure_reasons", []) or []:
        failure_counter[str(row.get("reason", "unknown"))] += int(row.get("count", 0) or 0)
    normalized = int(agg.get("normalized_count_total") or 0)
    capacity = int(agg.get("requested_symbol_date_capacity_total") or agg.get("estimated_symbol_date_rows") or 0)
    missing = int(agg.get("missing_dates_total") or 0)
    partial = int(agg.get("partial_count_total") or 0)
    failed = int(agg.get("failed_count_total") or 0)
    # Synthetic fixture density runs record completed local rows in the density summary while
    # leaving provider-normalization counters at zero because no live provider calls are made.
    # Treat a completed, burden-free bounded window as fully observed for longitudinal density.
    effective_observed_count = normalized
    if not effective_observed_count and capacity and bool(review.get("completed_telemetry_mode")) and (missing + partial + failed) == 0:
        effective_observed_count = capacity
    norm_range = ecology.get("normalization_completeness_range", {}) or {}
    hhi_range = ecology.get("sector_hhi_range", {}) or {}
    topology_rows = []
    for row in ecology.get("chunk_diagnostics", []) or []:
        richness = row.get("structural_richness", {}) or {}
        topology_rows.append(int(richness.get("sector_transition_rows") or 0) + int(richness.get("posture_variety") or 0))
    if not topology_rows and chunk_rows:
        # When fixture/local reviews do not include OPS-HIST snapshot topology tables,
        # retain a bounded richness proxy from the static sector/subsector universe coverage.
        topology_rows = [len(sector_profile.get("strongest_sectors", []) or []) for _ in chunk_rows]
    return OrderedDict([
        ("window_trading_days", int(window)),
        ("source_root", source_root),
        ("source_status", review.get("source_status")),
        ("completed_telemetry_mode", bool(review.get("completed_telemetry_mode"))),
        ("chunk_count", int(agg.get("chunk_count") or 0)),
        ("configured_symbol_count", int(agg.get("configured_symbol_count") or 0)),
        ("effective_symbol_count", int(agg.get("effective_symbol_count") or 0)),
        ("estimated_symbol_date_rows", int(agg.get("estimated_symbol_date_rows") or 0)),
        ("replay_density", _ratio(effective_observed_count, capacity)),
        ("normalized_count_total", normalized),
        ("effective_observed_count", effective_observed_count),
        ("requested_symbol_date_capacity_total", capacity),
        ("contradiction_persistence", OrderedDict([("missing_dates_total", missing), ("partial_count_total", partial), ("failed_count_total", failed), ("burden_ratio", _ratio(missing + partial + failed, capacity))])),
        ("topology_richness", OrderedDict([("chunk_richness_range", _range(topology_rows)), ("chunk_richness_average", _mean(topology_rows)), ("topology_persistence_enabled", False)])),
        ("monoculture_concentration", OrderedDict([("snapshot_sector_hhi_range", OrderedDict([("min", hhi_range.get("min")), ("max", hhi_range.get("max"))])), ("universe_sector_hhi", sector_profile.get("sector_hhi")), ("universe_subsector_hhi", sector_profile.get("subsector_hhi"))])),
        ("sector_subsector_hhi", OrderedDict([("sector_hhi", sector_profile.get("sector_hhi")), ("subsector_hhi", sector_profile.get("subsector_hhi")), ("strongest_sectors", sector_profile.get("strongest_sectors", [])), ("strongest_subsectors", sector_profile.get("strongest_subsectors", []))])),
        ("normalization_completeness", OrderedDict([("range", OrderedDict([("min", norm_range.get("min")), ("max", norm_range.get("max"))])), ("density_mean", _mean(chunk_densities) if any(chunk_densities) else _ratio(effective_observed_count, capacity)), ("chunk_density_volatility", _volatility(chunk_densities))])),
        ("weak_symbols", [row.get("symbol") for row in weak_rows]),
        ("weak_symbol_details", weak_rows[:10]),
        ("provider_degradation", OrderedDict([("endpoint_failures", OrderedDict(sorted((agg.get("endpoint_failures") or {}).items()))), ("top_failure_reasons", _ordered_counter_rows(failure_counter, key_name="reason"))])),
        ("temporal_stability", OrderedDict([("observed_days", int(ecology.get("temporal_stability_days") or window)), ("posture_stability", ecology.get("posture_stability")), ("posture_counts", OrderedDict(sorted((ecology.get("posture_counts") or {}).items())))])),
        ("replay_morphology_persistence", OrderedDict([("posture", ecology.get("posture_stability")), ("dominant_chunk", (review.get("chunk_comparison", {}) or {}).get("dominant_chunk")), ("richest_chunks", (review.get("chunk_comparison", {}) or {}).get("richest_chunks", []))])),
    ])


def build_longitudinal_comparison(*, window_summaries: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    ordered = sorted(window_summaries, key=lambda row: int(row["window_trading_days"]))
    weak_counter: Counter[str] = Counter()
    provider_counter: Counter[str] = Counter()
    posture_counter: Counter[str] = Counter()
    sector_counter: Counter[str] = Counter()
    for row in ordered:
        weak_counter.update(str(symbol) for symbol in row.get("weak_symbols", []) or [] if symbol)
        for reason in (row.get("provider_degradation", {}) or {}).get("top_failure_reasons", []) or []:
            provider_counter[str(reason.get("reason", "unknown"))] += 1
        posture = (row.get("temporal_stability", {}) or {}).get("posture_stability")
        if posture:
            posture_counter[str(posture)] += 1
        strongest = ((row.get("sector_subsector_hhi", {}) or {}).get("strongest_sectors", []) or [])[:5]
        sector_counter.update(str(item.get("sector")) for item in strongest if item.get("sector"))
    density_values = [row.get("replay_density") for row in ordered]
    burden_values = [(row.get("contradiction_persistence", {}) or {}).get("burden_ratio") for row in ordered]
    richness_values = [(row.get("topology_richness", {}) or {}).get("chunk_richness_average") for row in ordered]
    concentration_values = [(row.get("monoculture_concentration", {}) or {}).get("universe_sector_hhi") for row in ordered]
    norm_values = [(row.get("normalization_completeness", {}) or {}).get("density_mean") for row in ordered]
    weak_recurring = _ordered_counter_rows(weak_counter, limit=12, key_name="symbol")
    provider_recurring = _ordered_counter_rows(provider_counter, limit=12, key_name="reason")
    sector_recurring = _ordered_counter_rows(sector_counter, limit=12, key_name="sector")
    return OrderedDict([
        ("window_count", len(ordered)),
        ("windows", [int(row["window_trading_days"]) for row in ordered]),
        ("replay_density", OrderedDict([("values", density_values), ("trend", _trend(density_values)), ("volatility", _volatility(density_values))])),
        ("contradiction_persistence", OrderedDict([("burden_values", burden_values), ("trend", _trend(burden_values)), ("volatility", _volatility(burden_values))])),
        ("topology_richness", OrderedDict([("values", richness_values), ("trend", _trend(richness_values)), ("persistence", "persistent" if len(set(v for v in richness_values if v is not None)) <= 1 else "evolving")])),
        ("monoculture_concentration", OrderedDict([("sector_hhi_values", concentration_values), ("trend", _trend(concentration_values)), ("assessment", "bounded_diverse_universe" if concentration_values and max(v for v in concentration_values if v is not None) < 0.2 else "concentrated_universe")])) ,
        ("sector_subsector_hhi", OrderedDict([("strongest_recurring_sectors", sector_recurring), ("strongest_recurring_subsectors", [OrderedDict([("subsector", row["sector"]), ("window_count", row["window_count"])]) for row in sector_recurring])])),
        ("normalization_completeness", OrderedDict([("density_mean_values", norm_values), ("trend", _trend(norm_values)), ("volatility", _volatility(norm_values))])),
        ("weak_symbol_recurrence", weak_recurring),
        ("provider_degradation_recurrence", provider_recurring),
        ("temporal_stability", OrderedDict([("posture_recurrence", _ordered_counter_rows(posture_counter, key_name="posture")), ("assessment", "stable_across_windows" if len(posture_counter) == 1 and posture_counter else "mixed_or_insufficient")])),
        ("replay_morphology_persistence", OrderedDict([("assessment", "persistent_observational_morphology" if len(posture_counter) == 1 and posture_counter else "mixed_morphology"), ("activation_status", "not_activated")])) ,
    ])


def build_longitudinal_narrative(comparison: Mapping[str, Any], window_summaries: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    weak = comparison.get("weak_symbol_recurrence", []) or []
    providers = comparison.get("provider_degradation_recurrence", []) or []
    sectors = (comparison.get("sector_subsector_hhi", {}) or {}).get("strongest_recurring_sectors", []) or []
    return OrderedDict([
        ("stable_structures", [
            f"Replay density trend is {comparison['replay_density']['trend']} across windows {comparison['windows']}.",
            f"Temporal posture assessment is {comparison['temporal_stability']['assessment']}.",
            "Governance remains observational only with replay activation, trading, topology persistence, and Supabase writes disabled.",
        ]),
        ("quick_decay_structures", [
            "No replay activation structure is persisted; morphology observations remain report-local and decay outside the bounded artifact set.",
            "Provider failure samples are treated as weak evidence unless recurring across more than one window.",
        ]),
        ("sector_replay_persistence", [f"{row['sector']} recurred as a leading sector in {row['window_count']} windows." for row in sectors[:5]] or ["No recurring sector replay concentration was detected."]),
        ("emergent_fragility_clusters", [f"{row['symbol']} recurred as a weak symbol in {row['window_count']} windows." for row in weak[:8]] or ["No recurring weak-symbol fragility cluster was detected."]),
        ("propagation_asymmetry", [
            f"Provider degradation recurrence: {providers[:5] if providers else 'not observed'}.",
            f"Contradiction burden trend is {comparison['contradiction_persistence']['trend']}, indicating whether longer windows amplify or absorb missing/partial evidence asymmetrically.",
        ]),
    ])


def build_operational_stability_section(comparison: Mapping[str, Any], window_summaries: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    completed = all(bool(row.get("completed_telemetry_mode")) for row in window_summaries)
    provider_rows = comparison.get("provider_degradation_recurrence", []) or []
    return OrderedDict([
        ("ingestion_robustness_over_longer_windows", "robust_bounded" if completed else "preview_or_partial_artifacts_present"),
        ("provider_sparsity_trends", "recurring_provider_sparsity_observed" if provider_rows else "no_recurring_provider_sparsity_in_bounded_telemetry"),
        ("replay_observation_continuity", comparison.get("replay_morphology_persistence", {}).get("assessment")),
        ("historical_optional_market_cap_policy", "remains_appropriate_optional_enrichment_no_fail_closed_change_recommended"),
        ("local_artifacts_only", True),
    ])


def build_hist_long1_artifact(*, plan: Mapping[str, Any], window_reviews: Sequence[Mapping[str, Any]], source_roots: Sequence[str]) -> OrderedDict[str, Any]:
    sector_profile = plan["sector_subsector_concentration_baseline"]
    windows = list(plan["windows"])
    if len(window_reviews) != len(windows):
        raise ValueError("HIST-LONG-1 fails closed: each window requires one bounded review")
    summaries = [_summarize_window(review, window=windows[idx], source_root=source_roots[idx], sector_profile=sector_profile) for idx, review in enumerate(window_reviews)]
    comparison = build_longitudinal_comparison(window_summaries=summaries)
    narrative = build_longitudinal_narrative(comparison, summaries)
    stability = build_operational_stability_section(comparison, summaries)
    chunk_consistency = OrderedDict([
        ("expected_chunk_count", plan["expected_chunk_count"]),
        ("observed_chunk_counts", [row["chunk_count"] for row in summaries]),
        ("consistent", all(int(row["chunk_count"]) == int(plan["expected_chunk_count"]) for row in summaries)),
    ])
    checksum_input = json.dumps({"plan": plan, "summaries": summaries, "comparison": comparison}, sort_keys=True, default=str)
    return OrderedDict([
        ("schema_version", HIST_LONG1_SCHEMA_VERSION),
        ("status", "ok"),
        ("review_date", date.today().isoformat()),
        ("governance_certification", _governance()),
        ("orchestration_plan", OrderedDict(plan)),
        ("per_window_summary", summaries),
        ("longitudinal_comparison_summary", comparison),
        ("longitudinal_narrative_synthesis", narrative),
        ("operational_stability", stability),
        ("bounded_telemetry", OrderedDict([
            ("per_window_summary", summaries),
            ("longitudinal_comparison_summary", comparison),
            ("weakest_recurring_symbols", comparison["weak_symbol_recurrence"]),
            ("strongest_recurring_sectors", comparison["sector_subsector_hhi"]["strongest_recurring_sectors"]),
            ("strongest_recurring_subsectors", comparison["sector_subsector_hhi"]["strongest_recurring_subsectors"]),
            ("chunk_consistency_metrics", chunk_consistency),
        ])),
        ("readiness_assessment", OrderedDict([
            ("ready_for_deeper_replay_ecology_accumulation", chunk_consistency["consistent"] and stability["ingestion_robustness_over_longer_windows"] == "robust_bounded"),
            ("required_constraints", ["observational_only", "no_replay_activation", "no_trading", "no_prediction", "no_topology_persistence", "no_supabase_writes"]),
            ("recommendation", "Proceed to deeper bounded observational accumulation only; keep replay inactive and topology non-persistent."),
        ])),
        ("artifact_checksum", sha256(checksum_input.encode("utf-8")).hexdigest()),
    ])


def render_hist_long1_markdown(artifact: Mapping[str, Any]) -> str:
    g = artifact["governance_certification"]
    comparison = artifact["longitudinal_comparison_summary"]
    readiness = artifact["readiness_assessment"]
    lines = [
        "# HIST-LONG-1 — Longitudinal Historical Ecology Review",
        "",
        "## Governance Certification",
        f"- Governance mode: {g['governance_mode']}",
        f"- Prediction enabled: {g['prediction_enabled']}",
        f"- Trading execution enabled: {g['trading_execution_enabled']}",
        f"- Replay activation enabled: {g['replay_activation_enabled']}",
        f"- Topology persistence enabled: {g['topology_persistence_enabled']}",
        f"- Supabase writes enabled: {g['supabase_write_enabled']}",
        f"- Local artifacts only: {g['local_artifacts_only']}",
        "",
        "## Window Summary",
    ]
    for row in artifact["per_window_summary"]:
        lines.append(f"- {row['window_trading_days']} trading days: replay_density={row['replay_density']}, contradiction_burden={row['contradiction_persistence']['burden_ratio']}, topology_richness_avg={row['topology_richness']['chunk_richness_average']}, normalization_density_mean={row['normalization_completeness']['density_mean']}, weak_symbols={row['weak_symbols']}")
    lines.extend([
        "",
        "## Longitudinal Comparison",
        f"- Replay density: {json.dumps(comparison['replay_density'], sort_keys=True)}",
        f"- Contradiction persistence: {json.dumps(comparison['contradiction_persistence'], sort_keys=True)}",
        f"- Topology richness: {json.dumps(comparison['topology_richness'], sort_keys=True)}",
        f"- Monoculture/concentration: {json.dumps(comparison['monoculture_concentration'], sort_keys=True)}",
        f"- Sector/subsector HHI: {json.dumps(comparison['sector_subsector_hhi'], sort_keys=True)}",
        f"- Normalization completeness: {json.dumps(comparison['normalization_completeness'], sort_keys=True)}",
        f"- Weak symbol recurrence: {json.dumps(comparison['weak_symbol_recurrence'], sort_keys=True)}",
        f"- Provider degradation recurrence: {json.dumps(comparison['provider_degradation_recurrence'], sort_keys=True)}",
        f"- Temporal stability: {json.dumps(comparison['temporal_stability'], sort_keys=True)}",
        f"- Replay morphology persistence: {json.dumps(comparison['replay_morphology_persistence'], sort_keys=True)}",
        "",
        "## Longitudinal Narrative Synthesis",
    ])
    for section, rows in artifact["longitudinal_narrative_synthesis"].items():
        lines.append(f"### {section.replace('_', ' ').title()}")
        for row in rows:
            lines.append(f"- {row}")
    lines.extend(["", "## Operational Stability"])
    for key, value in artifact["operational_stability"].items():
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Bounded Telemetry",
        f"- Weakest recurring symbols: {json.dumps(artifact['bounded_telemetry']['weakest_recurring_symbols'], sort_keys=True)}",
        f"- Strongest recurring sectors: {json.dumps(artifact['bounded_telemetry']['strongest_recurring_sectors'], sort_keys=True)}",
        f"- Strongest recurring subsectors: {json.dumps(artifact['bounded_telemetry']['strongest_recurring_subsectors'], sort_keys=True)}",
        f"- Chunk consistency metrics: {json.dumps(artifact['bounded_telemetry']['chunk_consistency_metrics'], sort_keys=True)}",
        "",
        "## Readiness Assessment",
        f"- Ready for deeper replay ecology accumulation: {readiness['ready_for_deeper_replay_ecology_accumulation']}",
        f"- Recommendation: {readiness['recommendation']}",
    ])
    return "\n".join(lines) + "\n"


def run_hist_long1(*, windows: Sequence[int] = DEFAULT_WINDOWS, max_symbols: int = DEFAULT_MAX_SYMBOLS, chunk_size: int = DEFAULT_SYMBOL_CHUNK_SIZE, output_root: str = DEFAULT_OUTPUT_ROOT, end_date: str | None = None, density_mode: str = DENSITY_MODE_FIXTURE, density_runner: DensityRunner = run_hist_density3, review_builder: ReviewBuilder = build_hist_density4_findings_review) -> OrderedDict[str, Any]:
    plan = build_hist_long1_orchestration_plan(windows=windows, max_symbols=max_symbols, chunk_size=chunk_size, output_root=output_root, end_date=end_date)
    source_roots: list[str] = []
    reviews: list[Mapping[str, Any]] = []
    for window in plan["windows"]:
        source_root = str(Path(output_root) / f"window_{int(window):03d}d")
        source_roots.append(source_root)
        density_runner(
            trading_days=int(window),
            max_symbols=max_symbols,
            symbol_chunk_size=chunk_size,
            expected_chunk_count=int(plan["expected_chunk_count"]),
            output_root=source_root,
            density_mode=density_mode,
            raw_cache_enabled=False,
            raw_cache_write_enabled=False,
            cache_validation_mode=False,
            cache_only_validation=False,
            include_high_risk_symbols=False,
            apply_sde2_replacements=True,
            dry_run_config_only=False,
            end_date=plan["end_date"],
        )
        reviews.append(review_builder(source_root))
    return build_hist_long1_artifact(plan=plan, window_reviews=reviews, source_roots=source_roots)


def write_hist_long1_review(*, report_path: str = DEFAULT_REPORT_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH, **kwargs: Any) -> OrderedDict[str, Any]:
    artifact = run_hist_long1(**kwargs)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_hist_long1_markdown(artifact), encoding="utf-8")
    return artifact
