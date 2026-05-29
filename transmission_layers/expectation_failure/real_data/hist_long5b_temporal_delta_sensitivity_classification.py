from __future__ import annotations

import json
import os
from collections import Counter, OrderedDict
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from transmission_layers.expectation_failure.real_data.hist_long4_real_multi_window_ecology import REQUIRED_WINDOWS

HIST_LONG5B_SCHEMA_VERSION = "hist_long5b_v1"
DEFAULT_SOURCE_ARTIFACT_PATH = "artifacts/hist_long4_real_multi_window_ecology_review.json"
DEFAULT_REPORT_PATH = "reports/hist_long5b_temporal_delta_sensitivity_classification.md"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_long5b_temporal_delta_sensitivity_classification.json"
COMPLETED_SOURCE_ARTIFACT_ENV = "HIST_LONG5B_COMPLETED_SOURCE_ARTIFACT_PATH"

ADJACENT_WINDOW_PAIRS = ((20, 60), (60, 120))
DELTA_WINDOW_PAIRS = ((20, 60), (60, 120), (20, 120))
STABLE_TOLERANCE = 0.000001
MATERIAL_RELATIVE_DELTA = 0.05
MATERIAL_ABSOLUTE_DELTA = 0.000001

METRIC_GROUPS: OrderedDict[str, tuple[str, ...]] = OrderedDict([
    ("ingestion_continuity", (
        "normalized_rows",
        "completeness_ratio",
        "partial_count",
        "failed_count",
        "exact_date_match_ratio",
        "reconciled_date_ratio",
        "endpoint_failure_count",
    )),
    ("replay_ecology", (
        "replay_density",
        "replay_saturation",
        "contradiction_burden",
        "topology_richness",
        "morphology_persistence",
        "temporal_persistence",
    )),
    ("concentration_diversity", (
        "sector_hhi",
        "subsector_hhi",
        "monoculture_risk_score",
        "diversity_retention_score",
    )),
    ("weak_symbol_provider_quality", (
        "weak_symbol_count",
        "recurring_weak_symbol_count",
        "provider_degradation_count",
        "foxa_weak_window_count",
    )),
])

FORBIDDEN_SOURCE_GOVERNANCE_FLAGS = (
    "prediction_enabled",
    "trading_execution_enabled",
    "replay_activation_enabled",
    "replay_execution_enabled",
    "topology_persistence_enabled",
    "supabase_write_enabled",
    "raw_cache_write_enabled",
)


def _governance() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("governance_mode", "observational_only"),
        ("phase", "HIST-LONG-5B_temporal_delta_sensitivity_classification"),
        ("source_artifact_only", True),
        ("fmp_calls_enabled", False),
        ("provider_api_calls_enabled", False),
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


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _nested_number(value: Any, keys: Sequence[str]) -> float | None:
    if isinstance(value, Mapping):
        for key in keys:
            number = _as_number(value.get(key))
            if number is not None:
                return number
    return _as_number(value)


def _endpoint_failure_count(value: Any) -> int:
    if isinstance(value, Mapping):
        total = 0
        for item in value.values():
            if isinstance(item, bool):
                continue
            if isinstance(item, (int, float)):
                total += int(item)
            else:
                total += 1
        return total
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return len(value)
    return 0


def _status_completed(status: Any) -> bool:
    return str(status).lower() in {"ok", "success", "completed"}


def _window_id(row: Mapping[str, Any]) -> int | None:
    value = row.get("window_trading_days", row.get("window_days", row.get("window")))
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _verification_failure(reason: str, source_path: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("verified", False),
        ("source_path", source_path),
        ("reason", reason),
    ])


def verify_source(source: Mapping[str, Any] | None, *, source_path: str) -> OrderedDict[str, Any]:
    if source is None:
        return _verification_failure("HIST-LONG-4 JSON missing", source_path)
    if not _status_completed(source.get("status")):
        return _verification_failure("source status is not completed/success", source_path)
    windows = list(source.get("window_level_results", []) or [])
    detected = [_window_id(row) for row in windows]
    if tuple(detected) != REQUIRED_WINDOWS:
        return _verification_failure("completed windows are not exactly 20, 60, 120", source_path)
    comparison = source.get("longitudinal_comparison", {}) or {}
    completed_count = source.get("completed_window_count", comparison.get("completed_window_count"))
    if completed_count is not None and int(completed_count) != 3:
        return _verification_failure("completed_window_count != 3", source_path)
    if len(windows) != 3 or any(not isinstance(row, Mapping) or not row for row in windows):
        return _verification_failure("one or more window summaries are missing", source_path)
    governance = source.get("governance_certification", {}) or {}
    enabled = [key for key in FORBIDDEN_SOURCE_GOVERNANCE_FLAGS if governance.get(key) is True]
    if enabled:
        return _verification_failure(f"forbidden source governance enabled: {', '.join(enabled)}", source_path)
    return OrderedDict([
        ("verified", True),
        ("source_path", source_path),
        ("source_status", source.get("status")),
        ("completed_window_count", completed_count if completed_count is not None else 3),
        ("completed_windows", list(REQUIRED_WINDOWS)),
        ("source_digest", sha256(json.dumps(source, sort_keys=True, default=str).encode("utf-8")).hexdigest()),
    ])


def _recurring_symbols(windows: Sequence[Mapping[str, Any]]) -> set[str]:
    counter: Counter[str] = Counter()
    for row in windows:
        counter.update({str(symbol).upper() for symbol in row.get("weak_symbols", []) or []})
    return {symbol for symbol, count in counter.items() if count >= 2}


def _extract_metrics(row: Mapping[str, Any], recurring_symbols: set[str]) -> OrderedDict[str, float | None]:
    weak_symbols = {str(symbol).upper() for symbol in row.get("weak_symbols", []) or []}
    provider = row.get("provider_degradation", {}) or {}
    top_failure_reasons = row.get("top_failure_reasons", []) or provider.get("top_failure_reasons", []) or []
    endpoint_failure_count = _endpoint_failure_count(row.get("endpoint_failures", provider.get("endpoint_failures", {})))
    return OrderedDict([
        ("normalized_rows", _as_number(row.get("normalized_rows"))),
        ("completeness_ratio", _as_number(row.get("completeness_ratio", row.get("completeness")))),
        ("partial_count", _as_number(row.get("partial_count"))),
        ("failed_count", _as_number(row.get("failed_count"))),
        ("exact_date_match_ratio", _as_number(row.get("exact_date_match_ratio", row.get("exact_date_ratio")))),
        ("reconciled_date_ratio", _as_number(row.get("reconciled_date_ratio"))),
        ("endpoint_failure_count", float(endpoint_failure_count)),
        ("replay_density", _as_number(row.get("replay_density"))),
        ("replay_saturation", _nested_number(row.get("replay_saturation"), ("density", "score", "ratio"))),
        ("contradiction_burden", _nested_number(row.get("contradiction_burden"), ("ratio", "score", "count"))),
        ("topology_richness", _nested_number(row.get("topology_richness"), ("chunk_richness_average", "average", "score"))),
        ("morphology_persistence", _nested_number(row.get("morphology_persistence"), ("score", "ratio"))),
        ("temporal_persistence", _nested_number(row.get("temporal_persistence"), ("score", "ratio", "observed_days"))),
        ("sector_hhi", _nested_number(row.get("sector_hhi"), ("universe_hhi", "score", "hhi"))),
        ("subsector_hhi", _nested_number(row.get("subsector_hhi"), ("universe_hhi", "score", "hhi"))),
        ("monoculture_risk_score", _nested_number(row.get("monoculture_risk_score", row.get("monoculture_risk")), ("score", "risk_score", "ratio"))),
        ("diversity_retention_score", _nested_number(row.get("diversity_retention_score", row.get("diversity_persistence")), ("score", "retention_score", "ratio"))),
        ("weak_symbol_count", float(len(weak_symbols))),
        ("recurring_weak_symbol_count", float(len(weak_symbols & recurring_symbols))),
        ("provider_degradation_count", float(endpoint_failure_count + len(top_failure_reasons))),
        ("foxa_weak_window_count", 1.0 if row.get("foxa_weak") is True or "FOXA" in weak_symbols else 0.0),
    ])


def _direction(from_value: float | None, to_value: float | None) -> str:
    if from_value is None or to_value is None:
        return "insufficient_signal"
    delta = to_value - from_value
    if abs(delta) <= STABLE_TOLERANCE:
        return "flat"
    return "increase" if delta > 0 else "decrease"


def _relative_delta(from_value: float | None, to_value: float | None) -> float | None:
    if from_value is None or to_value is None or abs(from_value) <= STABLE_TOLERANCE:
        return None
    return round((to_value - from_value) / abs(from_value), 6)


def _delta_row(from_window: int, to_window: int, metric: str, values_by_window: Mapping[int, Mapping[str, float | None]]) -> OrderedDict[str, Any]:
    from_value = values_by_window[from_window][metric]
    to_value = values_by_window[to_window][metric]
    direction = _direction(from_value, to_value)
    absolute_delta = None if from_value is None or to_value is None else round(to_value - from_value, 6)
    relative_delta = _relative_delta(from_value, to_value)
    interpretation = "insufficient_signal"
    if direction != "insufficient_signal":
        if abs(absolute_delta or 0.0) <= STABLE_TOLERANCE or abs(relative_delta or 0.0) < MATERIAL_RELATIVE_DELTA:
            interpretation = "stable"
        else:
            interpretation = "material_change"
    return OrderedDict([
        ("from_window", from_window),
        ("to_window", to_window),
        ("metric", metric),
        ("from_value", from_value),
        ("to_value", to_value),
        ("absolute_delta", absolute_delta),
        ("relative_delta", relative_delta),
        ("direction", direction),
        ("interpretation", interpretation),
    ])


def _temporal_delta_tables(values_by_window: Mapping[int, Mapping[str, float | None]]) -> OrderedDict[str, list[OrderedDict[str, Any]]]:
    tables: OrderedDict[str, list[OrderedDict[str, Any]]] = OrderedDict()
    for group, metrics in METRIC_GROUPS.items():
        rows: list[OrderedDict[str, Any]] = []
        for from_window, to_window in DELTA_WINDOW_PAIRS:
            for metric in metrics:
                rows.append(_delta_row(from_window, to_window, metric, values_by_window))
        tables[group] = rows
    return tables


def _classification_for_sensitivity(total_abs: float | None, max_rel: float | None, volatility: float | None) -> str:
    if total_abs is None or max_rel is None or volatility is None:
        return "insufficient_signal"
    signal = max(max_rel, volatility)
    if total_abs <= STABLE_TOLERANCE and signal <= STABLE_TOLERANCE:
        return "stable"
    if signal < 0.05:
        return "stable"
    if signal < 0.25:
        return "mildly_sensitive"
    if signal < 0.75:
        return "sensitive"
    return "highly_sensitive"


def _sensitivity_ranking(values_by_window: Mapping[int, Mapping[str, float | None]]) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    metrics = [metric for group in METRIC_GROUPS.values() for metric in group]
    for metric in metrics:
        values = [values_by_window[window][metric] for window in REQUIRED_WINDOWS]
        if any(value is None for value in values):
            rows.append(OrderedDict([("metric", metric), ("total_absolute_change", None), ("max_relative_change", None), ("volatility_score", None), ("stability_score", None), ("classification", "insufficient_signal")]))
            continue
        adjacent = [abs(values[1] - values[0]), abs(values[2] - values[1])]  # type: ignore[operator]
        relatives = [abs(_relative_delta(values[0], values[1]) or 0.0), abs(_relative_delta(values[1], values[2]) or 0.0)]
        total_abs = round(sum(adjacent), 6)
        max_rel = round(max(relatives), 6)
        scale = max(abs(value) for value in values if value is not None) or 1.0
        volatility = round(abs((values[2] - values[1]) - (values[1] - values[0])) / scale, 6)  # type: ignore[operator]
        classification = _classification_for_sensitivity(total_abs, max_rel, volatility)
        stability_score = None if classification == "insufficient_signal" else round(max(0.0, 1.0 - max(max_rel, volatility)), 6)
        rows.append(OrderedDict([("metric", metric), ("total_absolute_change", total_abs), ("max_relative_change", max_rel), ("volatility_score", volatility), ("stability_score", stability_score), ("classification", classification)]))
    rows.sort(key=lambda row: (-(row["stability_score"] is not None), -(row["max_relative_change"] or -1), -(row["volatility_score"] or -1), row["metric"]))
    for rank, row in enumerate(rows, start=1):
        row["sensitivity_rank"] = rank
    return rows


def _structure_classification(values: Sequence[float | None]) -> str:
    if len(values) != 3 or any(value is None for value in values):
        return "insufficient_signal"
    deltas = [values[1] - values[0], values[2] - values[1]]  # type: ignore[operator]
    if all(abs(delta) <= STABLE_TOLERANCE for delta in deltas):
        return "stable"
    total = abs(values[2] - values[0])  # type: ignore[operator]
    if all(delta >= -STABLE_TOLERANCE for delta in deltas) and any(delta > STABLE_TOLERANCE for delta in deltas):
        return "emerging"
    if all(delta <= STABLE_TOLERANCE for delta in deltas) and any(delta < -STABLE_TOLERANCE for delta in deltas):
        return "decaying"
    return "volatile"


def _structural_persistence(values_by_window: Mapping[int, Mapping[str, float | None]]) -> OrderedDict[str, str]:
    rows: OrderedDict[str, str] = OrderedDict()
    for metric in [metric for group in METRIC_GROUPS.values() for metric in group]:
        rows[metric] = _structure_classification([values_by_window[window][metric] for window in REQUIRED_WINDOWS])
    return rows


def _aggregate_evolution(values_by_window: Mapping[int, Mapping[str, float | None]], metrics: Sequence[str], labels: Mapping[str, str]) -> OrderedDict[str, Any]:
    classes = [_structure_classification([values_by_window[window][metric] for window in REQUIRED_WINDOWS]) for metric in metrics]
    if any(item == "insufficient_signal" for item in classes):
        classification = labels["insufficient"]
    elif all(item == "stable" for item in classes):
        classification = labels["stable"]
    elif all(item in {"stable", "emerging"} for item in classes) and any(item == "emerging" for item in classes):
        classification = labels["up"]
    elif all(item in {"stable", "decaying"} for item in classes) and any(item == "decaying" for item in classes):
        classification = labels["down"]
    else:
        classification = labels["volatile"]
    return OrderedDict([("classification", classification), ("metric_classifications", OrderedDict(zip(metrics, classes)))])


def _foxa_assessment(windows: Sequence[Mapping[str, Any]], values_by_window: Mapping[int, Mapping[str, float | None]]) -> OrderedDict[str, Any]:
    present = [row.get("foxa_present") for row in windows]
    weak_windows = [int(row["window_trading_days"]) for row in windows if row.get("foxa_weak") is True or "FOXA" in {str(symbol).upper() for symbol in row.get("weak_symbols", []) or []}]
    contribution_values = []
    for row in windows:
        value = _nested_number(row.get("foxa_contribution"), ("score", "contribution", "ratio"))
        contribution_values.append(value)
    contribution_consistency = _structure_classification(contribution_values) if any(value is not None for value in contribution_values) else "insufficient granular signal"
    stability = _structure_classification([values_by_window[window]["foxa_weak_window_count"] for window in REQUIRED_WINDOWS])
    insufficient = contribution_consistency == "insufficient granular signal"
    assessment = "FOXA is present across all windows and not weak." if all(present) and not weak_windows else "FOXA weakness requires observation only; no replay or trading action is authorized."
    if insufficient:
        assessment += " Source lacks symbol-level FOXA contribution data."
    return OrderedDict([
        ("present_all_windows", all(value is True for value in present)),
        ("weak_window_count", len(weak_windows)),
        ("weak_windows", weak_windows),
        ("stability_classification", stability),
        ("contribution_consistency", contribution_consistency),
        ("insufficient_granular_signal", insufficient),
        ("supervisor_assessment", assessment),
    ])


def _fragility(values_by_window: Mapping[int, Mapping[str, float | None]]) -> OrderedDict[str, Any]:
    fragile_by_window: OrderedDict[int, list[str]] = OrderedDict()
    for window in REQUIRED_WINDOWS:
        metrics = values_by_window[window]
        reasons = []
        if (metrics["weak_symbol_count"] or 0) > 0:
            reasons.append("weak_symbols")
        if (metrics["provider_degradation_count"] or 0) > 0:
            reasons.append("provider_degradation")
        if (metrics["contradiction_burden"] or 0) > 0:
            reasons.append("contradiction_burden")
        if (metrics["replay_saturation"] or 0) >= 0.98:
            reasons.append("replay_saturation")
        fragile_by_window[window] = reasons
    windows = [window for window, reasons in fragile_by_window.items() if reasons]
    tags: list[str]
    if not windows:
        tags = ["no_fragility_detected"]
    elif windows == [20]:
        tags = ["short-window-only fragility"]
    elif windows == [120]:
        tags = ["long-window-only fragility", "newly emerging fragility"]
    elif len(windows) >= 2:
        tags = ["recurrent fragility"]
        if 120 in windows and 20 not in windows:
            tags.append("newly emerging fragility")
    else:
        tags = ["newly emerging fragility"]
    return OrderedDict([("classification", tags), ("fragile_windows", windows), ("reasons_by_window", fragile_by_window)])


def build_blocked_artifact(*, source_path: str, reason: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("schema_version", HIST_LONG5B_SCHEMA_VERSION),
        ("status", "blocked"),
        ("review_date", date.today().isoformat()),
        ("source_artifacts", [source_path]),
        ("completed_windows", []),
        ("source_verification", _verification_failure(reason, source_path)),
        ("temporal_delta_tables", OrderedDict((group, []) for group in METRIC_GROUPS)),
        ("sensitivity_ranking", []),
        ("structural_persistence_classification", OrderedDict()),
        ("replay_evolution_classification", OrderedDict([("classification", "insufficient_signal")])),
        ("concentration_evolution_classification", OrderedDict([("classification", "insufficient_signal")])),
        ("foxa_longitudinal_assessment", OrderedDict([("present_all_windows", False), ("weak_window_count", 0), ("stability_classification", "insufficient_signal"), ("contribution_consistency", "insufficient granular signal"), ("insufficient_granular_signal", True), ("supervisor_assessment", "Blocked before FOXA longitudinal assessment.")])),
        ("fragility_emergence_detection", OrderedDict([("classification", ["no_fragility_detected"]), ("fragile_windows", []), ("reasons_by_window", OrderedDict())])),
        ("governance_certification", _governance()),
        ("recommendation_for_hist_long6", "Blocked: HIST-LONG-6 should not proceed until HIST-LONG-4 source verification succeeds."),
    ])


def build_hist_long5b(source: Mapping[str, Any], *, source_path: str = DEFAULT_SOURCE_ARTIFACT_PATH) -> OrderedDict[str, Any]:
    verification = verify_source(source, source_path=source_path)
    if not verification["verified"]:
        return build_blocked_artifact(source_path=source_path, reason=str(verification["reason"]))
    windows = sorted(list(source.get("window_level_results", []) or []), key=lambda row: int(row["window_trading_days"]))
    recurring = _recurring_symbols(windows)
    values_by_window: OrderedDict[int, OrderedDict[str, float | None]] = OrderedDict((int(row["window_trading_days"]), _extract_metrics(row, recurring)) for row in windows)
    replay_evolution = _aggregate_evolution(values_by_window, ("replay_density", "replay_saturation", "temporal_persistence", "contradiction_burden", "topology_richness"), {"stable": "stable", "up": "expanding", "down": "contracting", "volatile": "volatile", "insufficient": "insufficient_signal"})
    if replay_evolution["classification"] == "expanding" and all(_structure_classification([values_by_window[window][metric] for window in REQUIRED_WINDOWS]) == "stable" for metric in ("replay_saturation", "temporal_persistence")):
        replay_evolution["classification"] = "plateaued"
    concentration_evolution = _aggregate_evolution(values_by_window, ("sector_hhi", "subsector_hhi"), {"stable": "stable_balanced", "up": "increasing_concentration", "down": "decreasing_concentration", "volatile": "volatile_concentration", "insufficient": "insufficient_signal"})
    return OrderedDict([
        ("schema_version", HIST_LONG5B_SCHEMA_VERSION),
        ("status", "completed"),
        ("review_date", date.today().isoformat()),
        ("source_artifacts", [source_path]),
        ("completed_windows", list(REQUIRED_WINDOWS)),
        ("source_verification", verification),
        ("metric_values_by_window", values_by_window),
        ("thresholds", OrderedDict([("stable_tolerance", STABLE_TOLERANCE), ("material_relative_delta", MATERIAL_RELATIVE_DELTA), ("sensitivity_thresholds", OrderedDict([("stable", "<0.05"), ("mildly_sensitive", "0.05-<0.25"), ("sensitive", "0.25-<0.75"), ("highly_sensitive", ">=0.75")]))])),
        ("temporal_delta_tables", _temporal_delta_tables(values_by_window)),
        ("sensitivity_ranking", _sensitivity_ranking(values_by_window)),
        ("structural_persistence_classification", _structural_persistence(values_by_window)),
        ("replay_evolution_classification", replay_evolution),
        ("concentration_evolution_classification", concentration_evolution),
        ("foxa_longitudinal_assessment", _foxa_assessment(windows, values_by_window)),
        ("fragility_emergence_detection", _fragility(values_by_window)),
        ("governance_certification", _governance()),
        ("recommendation_for_hist_long6", "Proceed only as observational analysis if HIST-LONG-6 continues; preserve no-provider-call and no-replay-activation governance."),
    ])


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = ["| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |", "|---:|---:|---|---:|---:|---:|---:|---|---|"]
    for row in rows:
        lines.append(f"| {row['from_window']} | {row['to_window']} | {row['metric']} | {row['from_value']} | {row['to_value']} | {row['absolute_delta']} | {row['relative_delta']} | {row['direction']} | {row['interpretation']} |")
    return lines


def render_markdown(artifact: Mapping[str, Any]) -> str:
    lines = [
        "# HIST-LONG-5B Temporal Delta & Sensitivity Classification",
        "",
        "## Executive Summary",
        f"- Status: {artifact['status']}",
        f"- Completed windows: {artifact['completed_windows']}",
        f"- Recommendation: {artifact['recommendation_for_hist_long6']}",
        "",
        "## Source Artifact Verification",
        f"- `{json.dumps(artifact['source_verification'], sort_keys=True)}`",
        "",
        "## Temporal Delta Tables",
    ]
    for group, rows in (artifact.get("temporal_delta_tables", {}) or {}).items():
        lines.extend(["", f"### {group}"])
        lines.extend(_markdown_table(rows))
    lines.extend(["", "## Sensitivity Ranking", "| rank | metric | classification | total absolute change | max relative change | volatility score | stability score |", "|---:|---|---|---:|---:|---:|---:|"])
    for row in artifact.get("sensitivity_ranking", []) or []:
        lines.append(f"| {row.get('sensitivity_rank')} | {row.get('metric')} | {row.get('classification')} | {row.get('total_absolute_change')} | {row.get('max_relative_change')} | {row.get('volatility_score')} | {row.get('stability_score')} |")
    lines.extend([
        "",
        "## Structural Persistence Classification",
        f"- `{json.dumps(artifact['structural_persistence_classification'], sort_keys=True)}`",
        "",
        "## Replay Evolution Classification",
        f"- `{json.dumps(artifact['replay_evolution_classification'], sort_keys=True)}`",
        "",
        "## Concentration Evolution Classification",
        f"- `{json.dumps(artifact['concentration_evolution_classification'], sort_keys=True)}`",
        "",
        "## FOXA Longitudinal Assessment",
        f"- `{json.dumps(artifact['foxa_longitudinal_assessment'], sort_keys=True)}`",
        "",
        "## Fragility Emergence Detection",
        f"- `{json.dumps(artifact['fragility_emergence_detection'], sort_keys=True)}`",
        "",
        "## Governance Certification",
    ])
    for key, value in (artifact.get("governance_certification", {}) or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Recommendation For HIST-LONG-6",
        f"- {artifact['recommendation_for_hist_long6']}",
    ])
    return "\n".join(lines) + "\n"


def _resolve_source_artifact_path(source_artifact_path: str = DEFAULT_SOURCE_ARTIFACT_PATH, completed_source_artifact_path: str | None = None) -> str:
    explicit_path = completed_source_artifact_path or os.environ.get(COMPLETED_SOURCE_ARTIFACT_ENV)
    return explicit_path or source_artifact_path


def write_hist_long5b(*, source_artifact_path: str = DEFAULT_SOURCE_ARTIFACT_PATH, completed_source_artifact_path: str | None = None, report_path: str = DEFAULT_REPORT_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH) -> OrderedDict[str, Any]:
    effective_source_path = _resolve_source_artifact_path(source_artifact_path, completed_source_artifact_path)
    try:
        source: Mapping[str, Any] | None = _load_json(effective_source_path)
    except FileNotFoundError:
        artifact = build_blocked_artifact(source_path=effective_source_path, reason="HIST-LONG-4 JSON missing")
    else:
        artifact = build_hist_long5b(source, source_path=effective_source_path)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_markdown(artifact), encoding="utf-8")
    return artifact
