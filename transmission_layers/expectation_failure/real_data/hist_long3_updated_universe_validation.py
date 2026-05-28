from __future__ import annotations

import json
from collections import Counter, OrderedDict
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_REAL
from transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion import (
    DEFAULT_MAX_SYMBOLS,
    DEFAULT_SYMBOL_CHUNK_SIZE,
    STAGE5_MAX_CHUNKS,
    _effective_symbols,
    run_hist_density3,
)
from transmission_layers.expectation_failure.real_data.hist_density4_findings_review import build_hist_density4_findings_review

HIST_LONG3_SCHEMA_VERSION = "hist_long3_v1"
DEFAULT_TRADING_DAYS = 20
DEFAULT_OUTPUT_ROOT = "reports/hist_long3_updated_universe_validation"
DEFAULT_REPORT_PATH = "reports/hist_long3_updated_universe_validation.md"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_long3_updated_universe_validation.json"
ORIGINAL_BASELINE = OrderedDict([
    ("normalized_count_total", 4700),
    ("partial_count_total", 20),
    ("failed_count_total", 20),
    ("weak_symbols", ["PARA"]),
    ("provider_failures", {"HTTP_403": 20, "zero_records_returned": 20}),
])

DensityRunner = Callable[..., Mapping[str, Any]]
ReviewBuilder = Callable[[str], Mapping[str, Any]]


def _governance() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("governance_mode", "observational_only"),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("replay_activation_enabled", False),
        ("replay_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("topology_activation_enabled", False),
        ("supabase_write_enabled", False),
        ("raw_cache_write_enabled", False),
        ("local_artifacts_only", True),
    ])


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _chunk_symbols_from_preview(preview: Mapping[str, Any] | None) -> list[list[str]]:
    if preview and preview.get("chunk_symbols"):
        return [[str(s).upper() for s in chunk] for chunk in preview.get("chunk_symbols", [])]
    symbols, _ = _effective_symbols(max_symbols=DEFAULT_MAX_SYMBOLS, include_high_risk_symbols=False, apply_sde2_replacements=True)
    return [symbols[i:i + DEFAULT_SYMBOL_CHUNK_SIZE] for i in range(0, len(symbols), DEFAULT_SYMBOL_CHUNK_SIZE)]


def _validate_updated_universe(preview: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    chunks = _chunk_symbols_from_preview(preview)
    symbols = [symbol for chunk in chunks for symbol in chunk]
    counts = Counter(symbols)
    duplicate_symbols = sorted(symbol for symbol, count in counts.items() if count > 1)
    return OrderedDict([
        ("foxa_count", int(counts.get("FOXA", 0))),
        ("foxa_present_exactly_once", counts.get("FOXA", 0) == 1),
        ("para_count", int(counts.get("PARA", 0))),
        ("para_absent", counts.get("PARA", 0) == 0),
        ("duplicate_symbol_count", len(duplicate_symbols)),
        ("duplicate_symbols", duplicate_symbols),
        ("no_duplicate_symbols", not duplicate_symbols),
        ("chunk_count", len(chunks)),
        ("expected_chunk_count", STAGE5_MAX_CHUNKS),
        ("expected_chunk_count_remains_5", len(chunks) == STAGE5_MAX_CHUNKS),
        ("chunk_sizes", [len(chunk) for chunk in chunks]),
        ("effective_symbol_count", len(symbols)),
    ])


def _aggregate_from_review(review: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    if not review:
        return OrderedDict([
            ("normalized_count_total", 0),
            ("normalization_completeness", None),
            ("partial_count_total", 0),
            ("failed_count_total", 0),
            ("exact_date_matches_total", 0),
            ("reconciled_prior_dates_total", 0),
            ("endpoint_failures", {}),
            ("top_failure_reasons", []),
            ("weak_symbols", []),
        ])
    agg = (review.get("ingestion_quality", {}) or {}).get("aggregate", {}) or {}
    capacity = int(agg.get("requested_symbol_date_capacity_total") or agg.get("estimated_symbol_date_rows") or 0)
    normalized = int(agg.get("normalized_count_total") or 0)
    weak = [str(row.get("symbol", "")).upper() for row in review.get("weak_symbol_review", []) or [] if row.get("symbol")]
    return OrderedDict([
        ("normalized_count_total", normalized),
        ("requested_symbol_date_capacity_total", capacity),
        ("normalization_completeness", round(normalized / capacity, 6) if capacity else None),
        ("partial_count_total", int(agg.get("partial_count_total") or 0)),
        ("failed_count_total", int(agg.get("failed_count_total") or 0)),
        ("exact_date_matches_total", int(agg.get("exact_date_matches_total") or 0)),
        ("reconciled_prior_dates_total", int(agg.get("reconciled_prior_dates_total") or 0)),
        ("endpoint_failures", dict(agg.get("endpoint_failures", {}) or {})),
        ("top_failure_reasons", list(agg.get("top_failure_reasons", []) or [])),
        ("weak_symbols", weak),
    ])


def _foxa_validation(review: Mapping[str, Any] | None, preview: Mapping[str, Any] | None, execution_status: str) -> OrderedDict[str, Any]:
    universe = _validate_updated_universe(preview)
    foxa_missing_samples: list[Mapping[str, Any]] = []
    foxa_endpoint_samples: list[Mapping[str, Any]] = []
    profile_failures: dict[str, int] = {}
    snapshot_count = 0
    if review:
        for row in (review.get("ingestion_quality", {}) or {}).get("chunk_quality_rows", []) or []:
            if "FOXA" not in [str(s).upper() for s in row.get("chunk_symbols", []) or []]:
                continue
            for reason in row.get("top_failure_reasons", []) or []:
                if isinstance(reason, dict) and "FOXA" in json.dumps(reason).upper():
                    foxa_endpoint_samples.append(reason)
        for weak in review.get("weak_symbol_review", []) or []:
            if str(weak.get("symbol", "")).upper() == "FOXA":
                foxa_missing_samples.extend(weak.get("observed_dates", []) or [])
                foxa_endpoint_samples.extend(weak.get("observed_reasons", []) or [])
        snapshot_count = int((review.get("source_artifacts_inspected", {}) or {}).get("ops_hist_snapshot_count") or 0)
        for snap in (review.get("ecology_findings", {}) or {}).get("chunk_diagnostics", []) or []:
            for symbol in snap.get("preflight_failure_symbols", []) or []:
                if str(symbol).upper() == "FOXA":
                    profile_failures["preflight_failure_symbol"] = profile_failures.get("preflight_failure_symbol", 0) + 1
    validated = bool(review) and execution_status == "completed" and universe["foxa_present_exactly_once"] and not foxa_missing_samples and not foxa_endpoint_samples
    return OrderedDict([
        ("status", "validated_suitable" if validated else ("not_validated_execution_blocked" if not review else "review_required")),
        ("historical_price_coverage", "no_foxa_price_failures_observed" if validated else "not_measured_in_completed_window" if not review else "foxa_failures_present_or_indeterminate"),
        ("profile_coverage", "no_foxa_profile_failures_observed" if validated and not profile_failures else ("not_measured_in_completed_window" if not review else "foxa_profile_failure_or_indeterminate")),
        ("missing_date_behavior", "no_foxa_missing_dates_observed" if validated else ("not_measured_in_completed_window" if not review else "foxa_missing_dates_or_indeterminate")),
        ("endpoint_failures", foxa_endpoint_samples),
        ("profile_failure_reasons", profile_failures),
        ("ops_hist_snapshot_count", snapshot_count),
        ("replacement_suitability_assessment", "FOXA is suitable for continued bounded real accumulation" if validated else "FOXA suitability remains unproven until a completed real 20-day window runs with provider credentials"),
    ])


def _comparison(metrics: Mapping[str, Any], execution_status: str) -> OrderedDict[str, Any]:
    baseline_failures = sum(int(v) for v in ORIGINAL_BASELINE["provider_failures"].values())
    current_failures = sum(int(v) for v in (metrics.get("endpoint_failures") or {}).values())
    weak_symbols = list(metrics.get("weak_symbols") or [])
    complete = metrics.get("normalization_completeness")
    return OrderedDict([
        ("did_weak_symbol_disappear", "PARA" not in weak_symbols if execution_status == "completed" else None),
        ("did_provider_degradation_improve", current_failures < baseline_failures if execution_status == "completed" else None),
        ("did_completeness_improve", complete is not None and complete > round(ORIGINAL_BASELINE["normalized_count_total"] / 4820, 6) if execution_status == "completed" else None),
        ("did_any_new_weak_symbols_emerge", bool([s for s in weak_symbols if s != "PARA"]) if execution_status == "completed" else None),
        ("current_provider_failure_total", current_failures),
        ("baseline_provider_failure_total", baseline_failures),
        ("assessment", "comparison_pending_completed_real_window" if execution_status != "completed" else "comparison_available"),
    ])


def build_hist_long3_artifact(*, output_root: str = DEFAULT_OUTPUT_ROOT, execution_error: str | None = None, review_builder: ReviewBuilder = build_hist_density4_findings_review) -> OrderedDict[str, Any]:
    root = Path(output_root)
    preview = _read_json(root / "hist_density3_config_preview.json")
    summary = _read_json(root / "hist_density3_summary.json")
    review: Mapping[str, Any] | None = None
    if summary and summary.get("status") == "ok":
        review = review_builder(str(root))
    execution_status = "completed" if review else "blocked_real_execution_failed"
    metrics = _aggregate_from_review(review)
    universe_validation = _validate_updated_universe(preview)
    run_config = OrderedDict([
        ("trading_days", DEFAULT_TRADING_DAYS),
        ("max_symbols", DEFAULT_MAX_SYMBOLS),
        ("symbol_chunk_size", DEFAULT_SYMBOL_CHUNK_SIZE),
        ("expected_chunk_count", STAGE5_MAX_CHUNKS),
        ("density_mode", DENSITY_MODE_REAL),
        ("raw_cache_write_enabled", False),
        ("replay_enabled", False),
        ("topology_persistence_enabled", False),
        ("supabase_write_enabled", False),
        ("duplicate_guard_enabled", True),
        ("apply_sde2_replacements", True),
        ("include_high_risk_symbols", False),
    ])
    checksum_input = json.dumps({"run_config": run_config, "metrics": metrics, "universe": universe_validation, "execution_error": execution_error}, sort_keys=True, default=str)
    return OrderedDict([
        ("schema_version", HIST_LONG3_SCHEMA_VERSION),
        ("status", "ok" if execution_status == "completed" else "blocked_provider_credentials_missing_or_execution_failed"),
        ("validation_status", execution_status),
        ("review_date", date.today().isoformat()),
        ("output_root", str(root)),
        ("run_configuration", run_config),
        ("execution_error", execution_error),
        ("governance_certification", _governance()),
        ("updated_universe_validation", universe_validation),
        ("ingestion_metrics", metrics),
        ("foxa_validation", _foxa_validation(review, preview, execution_status)),
        ("original_baseline", ORIGINAL_BASELINE),
        ("comparison_vs_para_baseline", _comparison(metrics, execution_status)),
        ("artifact_paths", OrderedDict([
            ("report", DEFAULT_REPORT_PATH),
            ("artifact", DEFAULT_ARTIFACT_PATH),
            ("output_root", str(root)),
            ("config_preview", str(root / "hist_density3_config_preview.json")),
            ("summary", str(root / "hist_density3_summary.json") if summary else None),
        ])),
        ("hist_long4_justified", execution_status == "completed" and _foxa_validation(review, preview, execution_status)["status"] == "validated_suitable"),
        ("artifact_checksum", sha256(checksum_input.encode("utf-8")).hexdigest()),
    ])


def render_hist_long3_markdown(artifact: Mapping[str, Any]) -> str:
    g = artifact["governance_certification"]
    metrics = artifact["ingestion_metrics"]
    comp = artifact["comparison_vs_para_baseline"]
    foxa = artifact["foxa_validation"]
    lines = [
        "# HIST-LONG-3 — Updated Universe Real Validation Window",
        "",
        "## Validation Status",
        f"- Status: `{artifact['status']}`",
        f"- Validation status: `{artifact['validation_status']}`",
        f"- Execution error: `{artifact['execution_error']}`",
        "",
        "## Updated Universe Checks",
    ]
    for key, value in artifact["updated_universe_validation"].items():
        lines.append(f"- {key}: `{json.dumps(value, sort_keys=True)}`")
    lines.extend([
        "",
        "## Ingestion Metrics",
        f"- Normalized rows: {metrics['normalized_count_total']}",
        f"- Normalization completeness: {metrics['normalization_completeness']}",
        f"- Partial count: {metrics['partial_count_total']}",
        f"- Failed count: {metrics['failed_count_total']}",
        f"- Exact date matches: {metrics['exact_date_matches_total']}",
        f"- Reconciled prior dates: {metrics['reconciled_prior_dates_total']}",
        f"- Endpoint failures: `{json.dumps(metrics['endpoint_failures'], sort_keys=True)}`",
        f"- Top failure reasons: `{json.dumps(metrics['top_failure_reasons'], sort_keys=True)}`",
        f"- Weak symbols: `{json.dumps(metrics['weak_symbols'], sort_keys=True)}`",
        "",
        "## FOXA Validation",
    ])
    for key, value in foxa.items():
        lines.append(f"- {key}: `{json.dumps(value, sort_keys=True)}`")
    lines.extend([
        "",
        "## Comparison vs Original PARA Baseline",
        f"- Original baseline: `{json.dumps(artifact['original_baseline'], sort_keys=True)}`",
    ])
    for key, value in comp.items():
        lines.append(f"- {key}: `{json.dumps(value, sort_keys=True)}`")
    lines.extend([
        "",
        "## Governance Certification",
        f"- Observational only: {g['governance_mode'] == 'observational_only'}",
        f"- Prediction enabled: {g['prediction_enabled']}",
        f"- Trading execution enabled: {g['trading_execution_enabled']}",
        f"- Replay activation enabled: {g['replay_activation_enabled']}",
        f"- Replay execution enabled: {g['replay_execution_enabled']}",
        f"- Topology persistence enabled: {g['topology_persistence_enabled']}",
        f"- Supabase writes enabled: {g['supabase_write_enabled']}",
        f"- Raw cache writes enabled: {g['raw_cache_write_enabled']}",
        "",
        "## HIST-LONG-4 Gate",
        f"- HIST-LONG-4 justified: {artifact['hist_long4_justified']}",
    ])
    return "\n".join(lines) + "\n"


def write_hist_long3_validation(*, output_root: str = DEFAULT_OUTPUT_ROOT, report_path: str = DEFAULT_REPORT_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH, execute_real: bool = True, density_runner: DensityRunner = run_hist_density3, review_builder: ReviewBuilder = build_hist_density4_findings_review) -> OrderedDict[str, Any]:
    execution_error = None
    if execute_real:
        try:
            density_runner(
                trading_days=DEFAULT_TRADING_DAYS,
                max_symbols=DEFAULT_MAX_SYMBOLS,
                symbol_chunk_size=DEFAULT_SYMBOL_CHUNK_SIZE,
                expected_chunk_count=STAGE5_MAX_CHUNKS,
                output_root=output_root,
                density_mode=DENSITY_MODE_REAL,
                raw_cache_enabled=False,
                raw_cache_write_enabled=False,
                cache_validation_mode=False,
                cache_only_validation=False,
                include_high_risk_symbols=False,
                apply_sde2_replacements=True,
                dry_run_config_only=False,
            )
        except Exception as exc:  # artifact-writing supervisor must capture fail-closed cause
            execution_error = f"{type(exc).__name__}: {exc}"
    artifact = build_hist_long3_artifact(output_root=output_root, execution_error=execution_error, review_builder=review_builder)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_hist_long3_markdown(artifact), encoding="utf-8")
    return artifact
