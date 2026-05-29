from __future__ import annotations

import json
from collections import Counter, OrderedDict
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

from transmission_layers.history_read_model.fact_emitter import (
    build_fact_emission_context,
    build_observation_fact_rows,
    emit_observation_facts,
)
from transmission_layers.history_read_model.queries import get_observation_facts, get_sector_morphology, get_window_metrics

PHASE_ID = "HIST-LONG-8"
PHASE_NAME = "HIST-LONG-8_cross_window_persistence_structural_stability"
SCHEMA_VERSION = "hist_long8_v1"
REQUIRED_WINDOWS = (20, 60, 120)
DEFAULT_HIST_LONG4_SOURCE_PATH = "artifacts/hist_long4_real_multi_window_ecology_review.json"
DEFAULT_REPORT_PATH = "reports/hist_long8_cross_window_persistence.md"
NUMERIC_METRICS = (
    "replay_density",
    "replay_saturation",
    "contradiction_burden",
    "sector_hhi",
    "subsector_hhi",
    "effective_symbol_count",
)
OBSERVATION_METRICS = (
    "persistence_score",
    "stability_class",
    *NUMERIC_METRICS,
    "weak_symbol_persistence",
    "sector_morphology_persistence",
    "subsector_morphology_persistence",
    "foxa_persistence",
)
_CLASS_VALUE = {"INSUFFICIENT_DATA": 0, "VOLATILE": 1, "PARTIALLY_STABLE": 2, "STABLE": 3}


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Mapping):
        for key in ("value", "universe_hhi", "metric_value", "score", "ratio", "density", "saturation", "burden"):
            found = _number(value.get(key))
            if found is not None:
                return found
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _window_days(row: Mapping[str, Any]) -> int | None:
    for key in ("window_days", "window_trading_days", "window"):
        if row.get(key) is not None:
            try:
                return int(row[key])
            except (TypeError, ValueError):
                return None
    return None


def _ordered_windows(rows: Iterable[Mapping[str, Any]], required_windows: Sequence[int]) -> OrderedDict[int, Mapping[str, Any]]:
    latest: dict[int, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        window = _window_days(row)
        if window in required_windows and window not in latest:
            latest[window] = row
    return OrderedDict((window, latest[window]) for window in required_windows if window in latest)


def _metric_from_window(row: Mapping[str, Any], metric: str) -> float | None:
    value = _number(row.get(metric))
    if value is not None:
        return value
    payload = row.get("payload_jsonb")
    if isinstance(payload, Mapping):
        return _number(payload.get(metric))
    return None


def _persistence_score(values: Sequence[float | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    if len(present) < 2:
        return None
    spread = max(present) - min(present)
    denominator = max(max(abs(value) for value in present), 1.0)
    return _round(max(0.0, 1.0 - (spread / denominator)))


def _classify(score: float | None, present_count: int) -> str:
    if score is None or present_count < 2:
        return "INSUFFICIENT_DATA"
    if score >= 0.9:
        return "STABLE"
    if score >= 0.65:
        return "PARTIALLY_STABLE"
    return "VOLATILE"


def _stable_label_score(label: str) -> int:
    return _CLASS_VALUE.get(label, 0)


def _ranked_names(value: Any, key: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    rows = [row for row in value if isinstance(row, Mapping)]
    rows.sort(key=lambda row: (int(row.get("rank", 9999) or 9999), -float(_number(row.get("share")) or _number(row.get("symbol_share")) or _number(row.get("concentration_contribution")) or 0.0), str(row.get(key, ""))))
    return [str(row[key]).strip().lower() for row in rows if str(row.get(key, "")).strip()]


def _ranked_from_window(row: Mapping[str, Any], group: str) -> list[str]:
    if group == "sector":
        hhi = row.get("sector_hhi")
        candidates = ("strongest_sectors", "sectors")
        key = "sector"
    else:
        hhi = row.get("subsector_hhi")
        candidates = ("strongest_subsectors", "subsectors")
        key = "subsector"
    if isinstance(hhi, Mapping):
        for candidate in candidates:
            names = _ranked_names(hhi.get(candidate), key)
            if names:
                return names
    payload = row.get("payload_jsonb")
    if isinstance(payload, Mapping):
        return _ranked_from_window(payload, group)
    return []


def _ranked_from_morphology(rows: Iterable[Mapping[str, Any]], required_windows: Sequence[int], group: str) -> OrderedDict[int, list[str]]:
    by_window: dict[int, list[tuple[int, str]]] = {window: [] for window in required_windows}
    key = "sector" if group == "sector" else "subsector"
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        window = _window_days(row)
        name = str(row.get(key, "")).strip().lower()
        if window in by_window and name:
            by_window[window].append((int(row.get("rank", 9999) or 9999), name))
    return OrderedDict((window, [name for _, name in sorted(values)]) for window, values in by_window.items() if values)


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float | None:
    a, b = set(left), set(right)
    if not a or not b:
        return None
    return len(a & b) / len(a | b)


def _ranking_score(ranked_by_window: Mapping[int, Sequence[str]]) -> tuple[float | None, list[str]]:
    available = [list(ranked_by_window[window]) for window in REQUIRED_WINDOWS if ranked_by_window.get(window)]
    if len(available) < 2:
        return None, []
    scores = [_jaccard(available[index], available[index + 1]) for index in range(len(available) - 1)]
    scores = [score for score in scores if score is not None]
    recurring = sorted(set.intersection(*(set(items) for items in available))) if available else []
    return (_round(mean(scores)) if scores else None), recurring[:10]


def _window_symbols(row: Mapping[str, Any]) -> list[str]:
    values = row.get("weak_symbols")
    if values is None and isinstance(row.get("payload_jsonb"), Mapping):
        values = row["payload_jsonb"].get("weak_symbols")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return sorted({str(item).strip().upper() for item in values if str(item).strip()})


def _symbol_persistence(windows: Mapping[int, Mapping[str, Any]]) -> OrderedDict[str, Any]:
    counter: Counter[str] = Counter()
    windows_with_data = 0
    for row in windows.values():
        symbols = _window_symbols(row)
        if symbols:
            windows_with_data += 1
            counter.update(symbols)
    recurring = sorted(symbol for symbol, count in counter.items() if count >= 2)
    score = None if windows_with_data < 2 else _round(len(recurring) / max(len(counter), 1))
    return OrderedDict([
        ("values_by_window", OrderedDict()),
        ("persistence_score", score),
        ("stability_class", _classify(score, windows_with_data)),
        ("recurring_symbols", recurring[:25]),
        ("windows_with_data", windows_with_data),
    ])


def _foxa_persistence(observation_facts: Iterable[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    values: OrderedDict[int, float] = OrderedDict()
    for row in observation_facts:
        if not isinstance(row, Mapping) or str(row.get("entity_id", "")).upper() != "FOXA":
            continue
        window = _window_days(row)
        value = _number(row.get("metric_value"))
        if value is None and isinstance(row.get("payload_jsonb"), Mapping):
            value = _number(row["payload_jsonb"].get("value"))
        if window in REQUIRED_WINDOWS and value is not None and window not in values:
            values[window] = value
    ordered = [_round(values[window]) if window in values else None for window in REQUIRED_WINDOWS]
    score = _persistence_score(ordered)
    return OrderedDict([
        ("values_by_window", OrderedDict((str(window), ordered[index]) for index, window in enumerate(REQUIRED_WINDOWS))),
        ("persistence_score", score),
        ("stability_class", _classify(score, len([value for value in ordered if value is not None]))),
    ])


def _extract_from_hist_long4(source: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = source.get("window_level_results", [])
    return [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []


def _source_digest(rows: Any) -> str:
    return sha256(json.dumps(rows, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def build_hist_long8_analysis(
    *,
    window_metrics: Iterable[Mapping[str, Any]] | None = None,
    sector_morphology: Iterable[Mapping[str, Any]] | None = None,
    observation_facts: Iterable[Mapping[str, Any]] | None = None,
    hist_long4_source: Mapping[str, Any] | None = None,
    inspected_inputs: Sequence[str] | None = None,
) -> OrderedDict[str, Any]:
    """Build deterministic cross-window persistence analysis from normalized read-model rows."""
    raw_windows = list(window_metrics or [])
    if not raw_windows and hist_long4_source is not None:
        raw_windows = _extract_from_hist_long4(hist_long4_source)
    morphology_rows = list(sector_morphology or [])
    fact_rows = list(observation_facts or [])
    windows = _ordered_windows(raw_windows, REQUIRED_WINDOWS)

    metrics = OrderedDict()
    for metric in NUMERIC_METRICS:
        ordered_values = [_round(_metric_from_window(windows[window], metric)) if window in windows else None for window in REQUIRED_WINDOWS]
        score = _persistence_score(ordered_values)
        metrics[metric] = OrderedDict([
            ("values_by_window", OrderedDict((str(window), ordered_values[index]) for index, window in enumerate(REQUIRED_WINDOWS))),
            ("persistence_score", score),
            ("stability_class", _classify(score, len([value for value in ordered_values if value is not None]))),
        ])

    morphology = OrderedDict()
    for group in ("sector", "subsector"):
        ranked = _ranked_from_morphology(morphology_rows, REQUIRED_WINDOWS, group)
        if not ranked:
            ranked = OrderedDict((window, _ranked_from_window(row, group)) for window, row in windows.items() if _ranked_from_window(row, group))
        score, recurring = _ranking_score(ranked)
        morphology[f"{group}_morphology_persistence"] = OrderedDict([
            ("ranked_by_window", OrderedDict((str(window), list(ranked.get(window, []))[:10]) for window in REQUIRED_WINDOWS)),
            ("persistence_score", score),
            ("stability_class", _classify(score, len([1 for values in ranked.values() if values]))),
            ("recurring_structures", recurring),
        ])

    weak_symbols = _symbol_persistence(windows)
    foxa = _foxa_persistence(fact_rows)
    dimension_scores = [row["persistence_score"] for row in [*metrics.values(), *morphology.values(), weak_symbols, foxa] if row.get("persistence_score") is not None]
    overall_score = _round(mean(dimension_scores)) if dimension_scores else None
    classes = [row["stability_class"] for row in [*metrics.values(), *morphology.values(), weak_symbols, foxa]]
    overall_class = "INSUFFICIENT_DATA" if not dimension_scores else min(classes, key=_stable_label_score)

    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("phase_id", PHASE_ID),
        ("phase_name", PHASE_NAME),
        ("status", "ok" if set(windows) == set(REQUIRED_WINDOWS) else "blocked"),
        ("required_windows", list(REQUIRED_WINDOWS)),
        ("completed_windows", list(windows.keys())),
        ("inspected_inputs", list(inspected_inputs or [])),
        ("source_digest", _source_digest({"window_metrics": raw_windows, "sector_morphology": morphology_rows, "observation_facts": fact_rows})),
        ("cross_window_comparison", metrics),
        ("persistence_analysis", OrderedDict([*morphology.items(), ("weak_symbol_persistence", weak_symbols), ("foxa_persistence", foxa)])),
        ("overall_persistence_score", overall_score),
        ("overall_stability_class", overall_class),
        ("confidence_assessment", "medium" if set(windows) == set(REQUIRED_WINDOWS) else "low_insufficient_required_windows"),
        ("governance_review", _governance_review()),
        ("limitations", ["FOXA and weak-symbol persistence are INSUFFICIENT_DATA when source rows are absent.", "Analysis is observational and uses completed local/read-model outputs only."]),
        ("next_step_recommendation", "Use emitted sefi_observation_facts as the source of truth for downstream HIST-LONG phases."),
    ])


def _governance_review() -> OrderedDict[str, bool]:
    return OrderedDict([
        ("fmp_calls_enabled", False),
        ("provider_api_calls_enabled", False),
        ("live_ingestion_enabled", False),
        ("replay_execution_enabled", False),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("schema_changes_enabled", False),
        ("destructive_database_operations_enabled", False),
    ])


def build_hist_long8_observations(analysis: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    observations: list[OrderedDict[str, Any]] = []

    def add(metric_name: str, dimension: str, row: Mapping[str, Any], value: float | int | None = None) -> None:
        observations.append(OrderedDict([
            ("entity_type", "phase"),
            ("entity_id", f"{PHASE_ID}:{dimension}"),
            ("metric_name", metric_name),
            ("metric_value", value if value is not None else row.get("persistence_score")),
            ("window_days", None),
            ("payload_jsonb", OrderedDict([
                ("dimension", dimension),
                ("persistence_score", row.get("persistence_score")),
                ("stability_class", row.get("stability_class")),
                ("values_by_window", row.get("values_by_window", OrderedDict())),
            ])),
        ]))
        observations.append(OrderedDict([
            ("entity_type", "phase"),
            ("entity_id", f"{PHASE_ID}:{dimension}"),
            ("metric_name", "stability_class"),
            ("metric_value", _stable_label_score(str(row.get("stability_class")))),
            ("window_days", None),
            ("payload_jsonb", OrderedDict([("dimension", dimension), ("stability_class", row.get("stability_class"))])),
        ]))

    for metric_name, row in (analysis.get("cross_window_comparison") or {}).items():
        add(metric_name, metric_name, row)
    for metric_name, row in (analysis.get("persistence_analysis") or {}).items():
        add(metric_name, metric_name, row)
    observations.insert(0, OrderedDict([
        ("entity_type", "phase"),
        ("entity_id", PHASE_ID),
        ("metric_name", "persistence_score"),
        ("metric_value", analysis.get("overall_persistence_score")),
        ("window_days", None),
        ("payload_jsonb", OrderedDict([("dimension", "overall"), ("stability_class", analysis.get("overall_stability_class"))])),
    ]))
    return observations


def build_hist_long8_fact_rows(
    analysis: Mapping[str, Any],
    *,
    enabled: bool = False,
    dry_run: bool = True,
    artifact_id: str | None = None,
    run_id: str | None = None,
) -> list[OrderedDict[str, Any]]:
    context = build_fact_emission_context(
        enabled=enabled,
        dry_run=dry_run,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        artifact_id=artifact_id or f"{PHASE_ID.lower()}-{analysis.get('source_digest', 'unknown')}",
        run_id=run_id or f"{PHASE_ID.lower()}-{analysis.get('source_digest', 'unknown')}",
    )
    return build_observation_fact_rows(context=context, observations=build_hist_long8_observations(analysis))


def _line(text: str = "") -> str:
    return f"{text}\n"


def build_hist_long8_report(analysis: Mapping[str, Any]) -> str:
    lines = []
    lines.append(_line("# HIST-LONG-8 Cross-Window Persistence & Structural Stability Analysis"))
    lines.append(_line("## Objective"))
    lines.append(_line("Identify persistent, decaying, and structurally unstable ecosystem characteristics across the 20d, 60d, and 120d windows."))
    lines.append(_line("## Inspected Inputs"))
    for item in analysis.get("inspected_inputs") or ["normalized read-model inputs"]:
        lines.append(_line(f"- {item}"))
    lines.append(_line("## Cross-Window Comparison"))
    for metric, row in (analysis.get("cross_window_comparison") or {}).items():
        lines.append(_line(f"- {metric}: score={row.get('persistence_score')} class={row.get('stability_class')} values={dict(row.get('values_by_window', {}))}"))
    lines.append(_line("## Persistence Analysis"))
    for metric, row in (analysis.get("persistence_analysis") or {}).items():
        lines.append(_line(f"- {metric}: score={row.get('persistence_score')} class={row.get('stability_class')}"))
    lines.append(_line("## Stability Classifications"))
    lines.append(_line(f"- Overall: {analysis.get('overall_stability_class')} (score={analysis.get('overall_persistence_score')})"))
    lines.append(_line("## Notable Recurring Structures"))
    for key in ("sector_morphology_persistence", "subsector_morphology_persistence"):
        row = (analysis.get("persistence_analysis") or {}).get(key, {})
        lines.append(_line(f"- {key}: {', '.join(row.get('recurring_structures', []) or ['none'])}"))
    lines.append(_line("## Weak-Symbol Persistence"))
    weak = (analysis.get("persistence_analysis") or {}).get("weak_symbol_persistence", {})
    lines.append(_line(f"- {weak.get('stability_class')} recurring={', '.join(weak.get('recurring_symbols', []) or ['none'])}"))
    lines.append(_line("## FOXA Persistence"))
    foxa = (analysis.get("persistence_analysis") or {}).get("foxa_persistence", {})
    lines.append(_line(f"- {foxa.get('stability_class')} values={dict(foxa.get('values_by_window', {}))}"))
    lines.append(_line("## Confidence Assessment"))
    lines.append(_line(f"- {analysis.get('confidence_assessment')}"))
    lines.append(_line("## Governance Review"))
    for key, value in (analysis.get("governance_review") or {}).items():
        lines.append(_line(f"- {key}: {value}"))
    lines.append(_line("## Limitations"))
    for item in analysis.get("limitations") or []:
        lines.append(_line(f"- {item}"))
    lines.append(_line("## Next-Step Recommendation"))
    lines.append(_line(f"- {analysis.get('next_step_recommendation')}"))
    return "".join(lines)


def _read_json(path: str | Path) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_hist_long8(
    *,
    client: Any | None = None,
    source_phase_id: str = "HIST-LONG-4",
    hist_long4_source_path: str | None = DEFAULT_HIST_LONG4_SOURCE_PATH,
    report_path: str | None = DEFAULT_REPORT_PATH,
    enabled: bool = False,
    dry_run: bool = True,
) -> OrderedDict[str, Any]:
    inspected_inputs: list[str] = []
    window_rows: list[Mapping[str, Any]] = []
    morphology_rows: list[Mapping[str, Any]] = []
    fact_rows: list[Mapping[str, Any]] = []
    hist4: Mapping[str, Any] | None = None

    if client is not None:
        for window in REQUIRED_WINDOWS:
            window_rows.extend(get_window_metrics(client, source_phase_id, window) or [])
        morphology_rows = list(get_sector_morphology(client, source_phase_id) or [])
        fact_rows = list(get_observation_facts(client, source_phase_id) or [])
        inspected_inputs.append(f"read_model:{source_phase_id}")
    elif hist_long4_source_path and Path(hist_long4_source_path).exists():
        hist4 = _read_json(hist_long4_source_path)
        inspected_inputs.append(hist_long4_source_path)
    else:
        inspected_inputs.append("no completed source input found")

    analysis = build_hist_long8_analysis(
        window_metrics=window_rows,
        sector_morphology=morphology_rows,
        observation_facts=fact_rows,
        hist_long4_source=hist4,
        inspected_inputs=inspected_inputs,
    )
    observations = build_hist_long8_observations(analysis)
    effective_dry_run = True if client is None else dry_run
    rows = build_hist_long8_fact_rows(analysis, enabled=enabled, dry_run=effective_dry_run)
    emission_result = emit_observation_facts(client, rows, dry_run=effective_dry_run) if enabled else OrderedDict([("table", "sefi_observation_facts"), ("dry_run", True), ("attempted_rows", 0), ("inserted_rows", 0)])
    report = build_hist_long8_report(analysis)
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
    return OrderedDict([("analysis", analysis), ("observations", observations), ("fact_rows", rows), ("fact_emission", emission_result), ("report", report)])
