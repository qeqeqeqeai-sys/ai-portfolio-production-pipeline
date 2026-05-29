from __future__ import annotations

import json
from collections import OrderedDict
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

from transmission_layers.history_read_model.fact_emitter import (
    build_fact_emission_context,
    build_observation_fact_rows,
    emit_observation_facts,
)
from transmission_layers.history_read_model.queries import get_observation_facts

PHASE_ID = "HIST-LONG-9"
PHASE_NAME = "HIST-LONG-9_persistence_evolution_stability_drift"
SOURCE_PHASE_ID = "HIST-LONG-8"
SCHEMA_VERSION = "hist_long9_v1"
DEFAULT_REPORT_PATH = "reports/hist_long9_persistence_drift.md"

DRIFT_CLASSES = ("IMPROVING", "STABLE", "DETERIORATING", "MIXED", "INSUFFICIENT_DATA")
_CLASS_VALUE = {"INSUFFICIENT_DATA": 0, "VOLATILE": 1, "PARTIALLY_STABLE": 2, "STABLE": 3}
_STABILITY_METRICS = (
    "replay_stability_drift",
    "contradiction_stability_drift",
    "concentration_stability_drift",
    "morphology_persistence_drift",
    "weak_symbol_persistence_drift",
    "foxa_persistence_drift",
)
_DIMENSION_MAP = OrderedDict([
    ("persistence_drift_score", ("overall",)),
    ("replay_stability_drift", ("replay_density",)),
    ("contradiction_stability_drift", ("contradiction_burden",)),
    ("concentration_stability_drift", ("sector_hhi", "subsector_hhi")),
    ("morphology_persistence_drift", ("sector_morphology_persistence", "subsector_morphology_persistence")),
    ("weak_symbol_persistence_drift", ("weak_symbol_persistence",)),
    ("foxa_persistence_drift", ("foxa_persistence",)),
])


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _source_digest(rows: Any) -> str:
    return sha256(json.dumps(rows, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _class_score(label: Any) -> int:
    return _CLASS_VALUE.get(str(label or "INSUFFICIENT_DATA"), 0)


def _dimension(row: Mapping[str, Any]) -> str:
    payload = row.get("payload_jsonb")
    if isinstance(payload, Mapping) and str(payload.get("dimension", "")).strip():
        return str(payload["dimension"]).strip()
    entity = str(row.get("entity_id", "")).strip()
    prefix = f"{SOURCE_PHASE_ID}:"
    if entity.startswith(prefix):
        return entity[len(prefix) :]
    if entity == SOURCE_PHASE_ID and row.get("metric_name") == "persistence_score":
        return "overall"
    return str(row.get("metric_name", "unknown")).strip() or "unknown"


def _stability_class(row: Mapping[str, Any]) -> str:
    payload = row.get("payload_jsonb")
    if isinstance(payload, Mapping) and payload.get("stability_class") is not None:
        return str(payload["stability_class"])
    return "INSUFFICIENT_DATA"


def _metric_value(row: Mapping[str, Any]) -> float | None:
    value = _number(row.get("metric_value"))
    if value is not None:
        return value
    payload = row.get("payload_jsonb")
    if isinstance(payload, Mapping):
        return _number(payload.get("persistence_score"))
    return None


def _snapshot_key(row: Mapping[str, Any], fallback: int) -> str:
    for key in ("run_id", "artifact_id", "loaded_at"):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return f"snapshot_{fallback:04d}"


def _ordered_snapshots(observation_facts: Iterable[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    order: dict[str, tuple[str, int]] = {}
    for index, row in enumerate(observation_facts):
        if not isinstance(row, Mapping):
            continue
        if str(row.get("phase_id", SOURCE_PHASE_ID)) != SOURCE_PHASE_ID:
            continue
        metric_name = str(row.get("metric_name", "")).strip().lower()
        if metric_name == "stability_class":
            continue
        dimension = _dimension(row)
        if not dimension:
            continue
        key = _snapshot_key(row, index)
        loaded = str(row.get("loaded_at") or row.get("completed_at") or row.get("created_at") or key)
        order.setdefault(key, (loaded, index))
        snapshot = grouped.setdefault(key, {"snapshot_id": key, "loaded_at": loaded, "artifact_id": row.get("artifact_id"), "run_id": row.get("run_id"), "metrics": {}})
        snapshot["metrics"][dimension] = OrderedDict([
            ("persistence_score", _round(_metric_value(row))),
            ("stability_class", _stability_class(row)),
        ])
    snapshots = [grouped[key] for key, _ in sorted(order.items(), key=lambda item: (item[1][0], item[1][1], item[0]))]
    return [OrderedDict((k, v) for k, v in snap.items()) for snap in snapshots]


def _series_for(snapshots: Sequence[Mapping[str, Any]], dimensions: Sequence[str]) -> tuple[list[float | None], list[str]]:
    scores: list[float | None] = []
    classes: list[str] = []
    for snapshot in snapshots:
        metrics = snapshot.get("metrics", {}) if isinstance(snapshot.get("metrics"), Mapping) else {}
        rows = [metrics[d] for d in dimensions if isinstance(metrics.get(d), Mapping)]
        values = [row.get("persistence_score") for row in rows if row.get("persistence_score") is not None]
        scores.append(_round(mean(values)) if values else None)
        class_values = [str(row.get("stability_class")) for row in rows]
        classes.append(min(class_values, key=_class_score) if class_values else "INSUFFICIENT_DATA")
    return scores, classes


def _classify_drift(delta: float | None, class_delta: int | None) -> str:
    if delta is None or class_delta is None:
        return "INSUFFICIENT_DATA"
    score_move = 1 if delta > 0.02 else -1 if delta < -0.02 else 0
    class_move = 1 if class_delta > 0 else -1 if class_delta < 0 else 0
    if score_move == 0 and class_move == 0:
        return "STABLE"
    if score_move >= 0 and class_move >= 0:
        return "IMPROVING"
    if score_move <= 0 and class_move <= 0:
        return "DETERIORATING"
    return "MIXED"


def _trend_row(metric_name: str, snapshots: Sequence[Mapping[str, Any]], dimensions: Sequence[str]) -> OrderedDict[str, Any]:
    scores, classes = _series_for(snapshots, dimensions)
    comparable = [(score, cls) for score, cls in zip(scores, classes) if score is not None and cls != "INSUFFICIENT_DATA"]
    if len(comparable) < 2:
        delta = None
        class_delta = None
        drift_class = "INSUFFICIENT_DATA"
        transition = "INSUFFICIENT_DATA"
        acceleration = None
    else:
        first_score, first_class = comparable[0]
        last_score, last_class = comparable[-1]
        delta = _round(last_score - first_score)
        class_delta = _class_score(last_class) - _class_score(first_class)
        drift_class = _classify_drift(delta, class_delta)
        transition = f"{first_class}->{last_class}"
        acceleration = None
        valid_scores = [score for score, _ in comparable]
        if len(valid_scores) >= 3:
            acceleration = _round((valid_scores[-1] - valid_scores[-2]) - (valid_scores[1] - valid_scores[0]))
    return OrderedDict([
        ("metric_name", metric_name),
        ("source_dimensions", list(dimensions)),
        ("scores_by_snapshot", [_round(score) for score in scores]),
        ("classes_by_snapshot", classes),
        ("score_delta", delta),
        ("persistence_score_acceleration", acceleration),
        ("stability_class_transition", transition),
        ("class_delta", class_delta),
        ("drift_class", drift_class),
    ])


def _overall_drift_class(metric_rows: Mapping[str, Mapping[str, Any]]) -> str:
    classes = [row.get("drift_class") for key, row in metric_rows.items() if key != "persistence_drift_score"]
    classes = [cls for cls in classes if cls != "INSUFFICIENT_DATA"]
    if not classes:
        return "INSUFFICIENT_DATA"
    if all(cls == "STABLE" for cls in classes):
        return "STABLE"
    if all(cls in {"IMPROVING", "STABLE"} for cls in classes):
        return "IMPROVING"
    if all(cls in {"DETERIORATING", "STABLE"} for cls in classes):
        return "DETERIORATING"
    return "MIXED"


def _fragility(metric_rows: Mapping[str, Mapping[str, Any]]) -> OrderedDict[str, Any]:
    considered = [row for key, row in metric_rows.items() if key in _STABILITY_METRICS and row.get("drift_class") != "INSUFFICIENT_DATA"]
    if not considered:
        score = None
        klass = "INSUFFICIENT_DATA"
    else:
        points = 0.0
        for row in considered:
            if row.get("drift_class") == "DETERIORATING":
                points += 1.0
            elif row.get("drift_class") == "MIXED":
                points += 0.5
            if (row.get("class_delta") or 0) < 0:
                points += 0.5
        score = _round(min(1.0, points / max(len(considered), 1)))
        klass = "DETERIORATING" if score >= 0.5 else "STABLE" if score == 0 else "MIXED"
    return OrderedDict([("emerging_fragility_score", score), ("emerging_fragility_class", klass)])


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


def build_hist_long9_analysis(*, observation_facts: Iterable[Mapping[str, Any]] | None = None, inspected_inputs: Sequence[str] | None = None) -> OrderedDict[str, Any]:
    """Build fact-native persistence evolution analysis from HIST-LONG-8 observation facts."""
    fact_rows = list(observation_facts or [])
    snapshots = _ordered_snapshots(fact_rows)
    comparable = len(snapshots) >= 2
    metric_rows = OrderedDict((name, _trend_row(name, snapshots, dims)) for name, dims in _DIMENSION_MAP.items())
    fragility = _fragility(metric_rows)
    overall_class = _overall_drift_class(metric_rows) if comparable else "INSUFFICIENT_DATA"
    limitations = ["Requires at least two comparable HIST-LONG-8 observation-fact snapshots/runs."]
    if not comparable:
        limitations.append("Fewer than two comparable fact snapshots were available; drift classifications fail closed.")
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("phase_id", PHASE_ID),
        ("phase_name", PHASE_NAME),
        ("source_phase_id", SOURCE_PHASE_ID),
        ("status", "ok" if comparable else "blocked"),
        ("inspected_fact_sources", list(inspected_inputs or ["sefi_observation_facts:HIST-LONG-8"])),
        ("source_digest", _source_digest(fact_rows)),
        ("snapshot_count", len(snapshots)),
        ("snapshots", [OrderedDict((k, snapshot[k]) for k in ("snapshot_id", "loaded_at", "artifact_id", "run_id")) for snapshot in snapshots]),
        ("drift_methodology", "Compare ordered HIST-LONG-8 observation-fact snapshots by persistence_score and stability_class; classify score/class movement deterministically."),
        ("metric_level_drift_analysis", metric_rows),
        ("stability_class_transitions", OrderedDict((name, row["stability_class_transition"]) for name, row in metric_rows.items())),
        ("overall_drift_class", overall_class),
        ("emerging_fragility_assessment", fragility),
        ("confidence_assessment", "medium" if comparable else "low_insufficient_fact_snapshots"),
        ("governance_review", _governance_review()),
        ("limitations", limitations),
        ("next_step_recommendation", "Continue emitting HIST-LONG-8 observation facts and rerun HIST-LONG-9 after additional comparable snapshots accumulate."),
    ])


def build_hist_long9_observations(analysis: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    observations: list[OrderedDict[str, Any]] = []
    for metric_name, row in (analysis.get("metric_level_drift_analysis") or {}).items():
        observations.append(OrderedDict([
            ("entity_type", "phase"),
            ("entity_id", f"{PHASE_ID}:{metric_name}"),
            ("metric_name", metric_name),
            ("metric_value", row.get("score_delta")),
            ("window_days", None),
            ("payload_jsonb", OrderedDict([
                ("drift_class", row.get("drift_class")),
                ("stability_class_transition", row.get("stability_class_transition")),
                ("persistence_score_acceleration", row.get("persistence_score_acceleration")),
                ("source_dimensions", row.get("source_dimensions", [])),
            ])),
        ]))
    observations.append(OrderedDict([
        ("entity_type", "phase"),
        ("entity_id", f"{PHASE_ID}:stability_class_transition"),
        ("metric_name", "stability_class_transition"),
        ("metric_value", None),
        ("window_days", None),
        ("payload_jsonb", OrderedDict([("transitions", analysis.get("stability_class_transitions", OrderedDict()))])),
    ]))
    fragility = analysis.get("emerging_fragility_assessment") or {}
    observations.append(OrderedDict([
        ("entity_type", "phase"),
        ("entity_id", f"{PHASE_ID}:emerging_fragility"),
        ("metric_name", "emerging_fragility_score"),
        ("metric_value", fragility.get("emerging_fragility_score")),
        ("window_days", None),
        ("payload_jsonb", OrderedDict([("emerging_fragility_class", fragility.get("emerging_fragility_class"))])),
    ]))
    observations.append(OrderedDict([
        ("entity_type", "phase"),
        ("entity_id", f"{PHASE_ID}:emerging_fragility"),
        ("metric_name", "emerging_fragility_class"),
        ("metric_value", None),
        ("window_days", None),
        ("payload_jsonb", OrderedDict([("emerging_fragility_class", fragility.get("emerging_fragility_class"))])),
    ]))
    observations.append(OrderedDict([
        ("entity_type", "phase"),
        ("entity_id", PHASE_ID),
        ("metric_name", "persistence_drift_class"),
        ("metric_value", None),
        ("window_days", None),
        ("payload_jsonb", OrderedDict([("drift_class", analysis.get("overall_drift_class")), ("snapshot_count", analysis.get("snapshot_count"))])),
    ]))
    return observations


def build_hist_long9_fact_rows(
    analysis: Mapping[str, Any], *, enabled: bool = False, dry_run: bool = True, artifact_id: str | None = None, run_id: str | None = None
) -> list[OrderedDict[str, Any]]:
    context = build_fact_emission_context(
        enabled=enabled,
        dry_run=dry_run,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        artifact_id=artifact_id or f"{PHASE_ID.lower()}-{analysis.get('source_digest', 'unknown')}",
        run_id=run_id or f"{PHASE_ID.lower()}-{analysis.get('source_digest', 'unknown')}",
    )
    return build_observation_fact_rows(context=context, observations=build_hist_long9_observations(analysis))


def _line(text: str = "") -> str:
    return f"{text}\n"


def build_hist_long9_report(analysis: Mapping[str, Any]) -> str:
    lines: list[str] = []
    lines.append(_line("# HIST-LONG-9 Persistence Evolution & Stability Drift Analysis"))
    lines.append(_line("## Objective"))
    lines.append(_line("Assess persistence evolution, stability-class transitions, and emerging fragility from normalized HIST-LONG-8 observation facts."))
    lines.append(_line("## Inspected Fact Sources"))
    for item in analysis.get("inspected_fact_sources") or ["sefi_observation_facts:HIST-LONG-8"]:
        lines.append(_line(f"- {item}"))
    lines.append(_line("## Drift Methodology"))
    lines.append(_line(f"- {analysis.get('drift_methodology')}"))
    lines.append(_line("## Metric-Level Drift Analysis"))
    for metric, row in (analysis.get("metric_level_drift_analysis") or {}).items():
        lines.append(_line(f"- {metric}: class={row.get('drift_class')} delta={row.get('score_delta')} transition={row.get('stability_class_transition')} acceleration={row.get('persistence_score_acceleration')}"))
    lines.append(_line("## Stability-Class Transitions"))
    for metric, transition in (analysis.get("stability_class_transitions") or {}).items():
        lines.append(_line(f"- {metric}: {transition}"))
    lines.append(_line("## Emerging Fragility Assessment"))
    fragility = analysis.get("emerging_fragility_assessment") or {}
    lines.append(_line(f"- score={fragility.get('emerging_fragility_score')} class={fragility.get('emerging_fragility_class')}"))
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


def run_hist_long9(
    *,
    client: Any | None = None,
    source_phase_id: str = SOURCE_PHASE_ID,
    observation_facts: Iterable[Mapping[str, Any]] | None = None,
    report_path: str | None = DEFAULT_REPORT_PATH,
    enabled: bool = False,
    dry_run: bool = True,
) -> OrderedDict[str, Any]:
    inspected_inputs: list[str] = []
    if client is not None:
        fact_rows = list(get_observation_facts(client, source_phase_id) or [])
        inspected_inputs.append(f"sefi_observation_facts:{source_phase_id}")
    else:
        fact_rows = list(observation_facts or [])
        inspected_inputs.append("bounded_local_observation_facts" if fact_rows else "no local observation facts supplied")

    analysis = build_hist_long9_analysis(observation_facts=fact_rows, inspected_inputs=inspected_inputs)
    observations = build_hist_long9_observations(analysis)
    effective_dry_run = True if client is None else dry_run
    rows = build_hist_long9_fact_rows(analysis, enabled=enabled, dry_run=effective_dry_run)
    emission_result = emit_observation_facts(client, rows, dry_run=effective_dry_run) if enabled else OrderedDict([
        ("table", "sefi_observation_facts"),
        ("dry_run", True),
        ("attempted_rows", 0),
        ("inserted_rows", 0),
    ])
    report = build_hist_long9_report(analysis)
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
    return OrderedDict([("analysis", analysis), ("observations", observations), ("fact_rows", rows), ("fact_emission", emission_result), ("report", report)])
