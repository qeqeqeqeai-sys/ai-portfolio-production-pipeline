from __future__ import annotations

import json
from collections import Counter, OrderedDict
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

PHASE_ID = "HIST-INTEL-1B"
PHASE_NAME = "HIST-INTEL-1B_fact_native_historical_findings"
SCHEMA_VERSION = "hist_intel1b_v1"
DEFAULT_JSON_REPORT_PATH = "reports/hist_intel1b_fact_native_historical_findings.json"
DEFAULT_MARKDOWN_REPORT_PATH = "reports/hist_intel1b_fact_native_historical_findings.md"
DEFAULT_COMPACT_SOURCE_PATHS = (
    "artifacts/hist_long4_real_multi_window_ecology_review.json",
    "artifacts/hist_long5b_temporal_delta_sensitivity_classification.json",
    "artifacts/hist_long6_cross_sectional_ecology_differentiation.json",
    "artifacts/hist_long7_intra_group_structural_contrast.json",
    "artifacts/hist_intel1_historical_structural_findings.json",
)
DEFAULT_TOP_N = 10
MAX_TOP_N = 10
MAX_LOCAL_FACT_ROWS = 5000
CONFIDENCE_LABELS = {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT"}

PIPELINE_METRIC_NAMES = {
    "normalized_rows",
    "reconciled_date_ratio",
    "row_count",
    "rows_loaded",
    "records_loaded",
    "loaded_rows",
    "input_rows",
    "output_rows",
    "coverage_ratio",
    "schema_version",
    "artifact_count",
    "missing_sources",
    "runtime_seconds",
}
PIPELINE_TERMS = (
    "normalized",
    "reconciled",
    "row",
    "rows",
    "schema",
    "artifact",
    "load",
    "loaded",
    "runtime",
    "diagnostic",
    "pipeline",
)
PERSISTENCE_TERMS = ("persistence", "persistent", "centrality", "hub", "concentration", "importance", "leader")
FRAGILITY_TERMS = ("fragility", "fragile", "weak", "risk", "instability", "unstable", "tail_gap", "thin")
DRIFT_TERMS = ("drift", "delta", "change", "decay", "deteriorating", "morphology", "churn", "sensitivity", "volatile")
REPLAY_TERMS = ("replay", "recurrence", "recurring", "co_occurrence", "co-occurrence", "density", "narrative")
STABILITY_TERMS = ("stable", "stability", "anchor", "coherence", "coherent", "durable")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _text(value).lower()


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Mapping):
        for key in ("metric_value", "value", "score", "share", "density", "ratio", "persistence_score", "stability_score", "centrality_score", "fragility_score"):
            found = _number(value.get(key))
            if found is not None:
                return found
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _bounded_top_n(top_n: int | None) -> int:
    return max(0, min(int(top_n if top_n is not None else DEFAULT_TOP_N), MAX_TOP_N))


def _source_digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def governance_certification() -> OrderedDict[str, bool]:
    return OrderedDict([
        ("analysis_only", True),
        ("local_only", True),
        ("no_provider_calls", True),
        ("no_supabase_writes", True),
        ("no_prediction", True),
        ("no_trading", True),
        ("no_portfolio_recommendation", True),
        ("no_governed_activation", True),
    ])


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb") or row.get("payload")
    return payload if isinstance(payload, Mapping) else {}


def _window(row: Mapping[str, Any]) -> str | None:
    value = row.get("window_days") or row.get("window_trading_days") or row.get("window") or _payload(row).get("window_days")
    return None if value in (None, "") else str(value)


def _metric_value(row: Mapping[str, Any]) -> float | None:
    value = _number(row.get("metric_value"))
    if value is not None:
        return value
    payload = _payload(row)
    for key in ("persistence_score", "stability_score", "centrality_score", "fragility_score", "replay_density", "score", "value"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    return None


def _fact_text(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    compact_payload = " ".join(_text(payload.get(k)) for k in sorted(payload) if k in {"dimension", "structure", "class", "stability_class", "drift_class", "fragility_class", "label"})
    return " ".join([_text(row.get("phase_id")), _text(row.get("entity_type")), _text(row.get("entity_id")), _text(row.get("metric_name")), compact_payload]).lower()


def _is_pipeline_metric(row: Mapping[str, Any]) -> bool:
    metric = _norm(row.get("metric_name"))
    if metric in PIPELINE_METRIC_NAMES:
        return True
    entity_type = _norm(row.get("entity_type"))
    if entity_type in {"pipeline", "diagnostic", "artifact", "schema", "row_count"}:
        return True
    return any(term in metric for term in PIPELINE_TERMS) and not any(term in metric for term in PERSISTENCE_TERMS + FRAGILITY_TERMS + DRIFT_TERMS + REPLAY_TERMS + STABILITY_TERMS)


def _is_ecosystem_fact(row: Mapping[str, Any]) -> bool:
    if _is_pipeline_metric(row):
        return False
    text = _fact_text(row)
    return any(term in text for term in PERSISTENCE_TERMS + FRAGILITY_TERMS + DRIFT_TERMS + REPLAY_TERMS + STABILITY_TERMS)


def _categories(row: Mapping[str, Any]) -> set[str]:
    text = _fact_text(row)
    categories: set[str] = set()
    if any(term in text for term in PERSISTENCE_TERMS):
        categories.add("hubs")
        categories.add("cross_window")
    if any(term in text for term in FRAGILITY_TERMS):
        categories.add("fragility")
    if any(term in text for term in DRIFT_TERMS):
        categories.add("drift")
    if any(term in text for term in REPLAY_TERMS):
        categories.add("replay")
    if any(term in text for term in STABILITY_TERMS):
        categories.add("anchors")
    return categories


def _entity_name(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    for key in ("entity_id", "dimension", "structure", "sector", "subsector", "symbol", "group"):
        value = row.get(key) if key in row else payload.get(key)
        if _text(value):
            return _norm(value)
    return _norm(row.get("metric_name") or "unknown")


def _confidence(evidence_count: int, window_coverage: int, phase_coverage: int) -> str:
    if evidence_count <= 0:
        return "INSUFFICIENT"
    if window_coverage >= 2 or phase_coverage >= 2 or evidence_count >= 3:
        return "HIGH"
    if evidence_count >= 2:
        return "MEDIUM"
    return "LOW"


def _score(category: str, values: Sequence[float], evidence_count: int, window_coverage: int, phase_coverage: int, recurrence_count: int) -> float:
    avg = sum(values) / len(values) if values else 0.0
    max_value = max(values) if values else 0.0
    if category == "drift":
        avg = abs(avg)
        max_value = max(abs(v) for v in values) if values else 0.0
    bounded_value = max(-1.0, min(1.0, (0.65 * avg) + (0.35 * max_value)))
    return _round(min(1.0, max(0.0, bounded_value) + min(evidence_count, 5) * 0.03 + min(window_coverage, 5) * 0.04 + min(phase_coverage, 5) * 0.04 + min(recurrence_count, 5) * 0.02)) or 0.0


def _classify_facts(facts: Iterable[Mapping[str, Any]]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    ecosystem: list[OrderedDict[str, Any]] = []
    diagnostics: list[OrderedDict[str, Any]] = []
    for index, row in enumerate(facts):
        if not isinstance(row, Mapping):
            continue
        classified = OrderedDict([
            ("index", index),
            ("phase_id", row.get("phase_id")),
            ("entity_type", row.get("entity_type")),
            ("entity_id", row.get("entity_id")),
            ("metric_name", row.get("metric_name")),
            ("window_days", _window(row)),
            ("metric_value", _round(_metric_value(row))),
            ("confidence", row.get("confidence") or row.get("confidence_label") or _payload(row).get("confidence_label")),
            ("evidence", row.get("evidence") or _payload(row).get("evidence") or _payload(row).get("evidence_count")),
            ("categories", sorted(_categories(row))),
        ])
        if _is_ecosystem_fact(row):
            ecosystem.append(classified)
        elif _is_pipeline_metric(row):
            diagnostics.append(classified)
    return ecosystem, diagnostics


def _aggregate(facts: Sequence[Mapping[str, Any]], *, category: str, top_n: int) -> list[OrderedDict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for row in facts:
        categories = set(row.get("categories") or [])
        if category not in categories:
            continue
        entity_type = _norm(row.get("entity_type") or "fact_entity")
        name = _entity_name(row)
        key = (entity_type, name)
        item = buckets.setdefault(key, {"entity_type": entity_type, "name": name, "values": [], "windows": set(), "phases": set(), "metrics": Counter(), "evidence": []})
        value = _number(row.get("metric_value"))
        if value is not None:
            item["values"].append(float(value))
        if row.get("window_days") not in (None, ""):
            item["windows"].add(str(row.get("window_days")))
        if row.get("phase_id"):
            item["phases"].add(str(row.get("phase_id")))
        if row.get("metric_name"):
            item["metrics"][_norm(row.get("metric_name"))] += 1
        item["evidence"].append(f"{row.get('phase_id')}:{row.get('metric_name')}:{row.get('window_days')}")
    rows: list[OrderedDict[str, Any]] = []
    for item in buckets.values():
        values = item["values"]
        evidence_count = len(item["evidence"])
        window_coverage = len(item["windows"])
        phase_coverage = len(item["phases"])
        recurrence_count = max(0, evidence_count - 1)
        score_name = {
            "hubs": "persistence_score",
            "fragility": "fragility_score",
            "cross_window": "cross_window_score",
            "drift": "drift_score",
            "replay": "replay_density_score",
            "anchors": "stability_score",
        }[category]
        rows.append(OrderedDict([
            ("entity_type", item["entity_type"]),
            ("name", item["name"]),
            (score_name, _score(category, values, evidence_count, window_coverage, phase_coverage, recurrence_count)),
            ("evidence_count", evidence_count),
            ("window_coverage", window_coverage),
            ("phase_coverage", phase_coverage),
            ("recurrence_count", recurrence_count),
            ("average_metric_value", _round(sum(values) / len(values)) if values else None),
            ("max_metric_value", _round(max(values)) if values else None),
            ("confidence_label", _confidence(evidence_count, window_coverage, phase_coverage)),
            ("dominant_metrics", [name for name, _ in sorted(item["metrics"].items(), key=lambda kv: (-kv[1], kv[0]))[:3]]),
            ("supporting_windows", sorted(item["windows"], key=str)),
            ("supporting_phases", sorted(item["phases"], key=str)),
            ("supporting_evidence", sorted(item["evidence"])[:5]),
        ]))
    score_key = {
        "hubs": "persistence_score",
        "fragility": "fragility_score",
        "cross_window": "cross_window_score",
        "drift": "drift_score",
        "replay": "replay_density_score",
        "anchors": "stability_score",
    }[category]
    return sorted(rows, key=lambda r: (-(r.get(score_key) or 0), -r["window_coverage"], -r["phase_coverage"], -r["evidence_count"], r["entity_type"], r["name"]))[: _bounded_top_n(top_n)]


def _pattern_clusters(facts: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    clusters: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in facts:
        key = (_norm(row.get("metric_name")), _norm(row.get("entity_type") or "fact_entity"), _norm(row.get("phase_id")))
        item = clusters.setdefault(key, {"metric_name": key[0], "entity_type": key[1], "phase_id": key[2], "windows": set(), "entities": set(), "values": [], "count": 0})
        item["count"] += 1
        if row.get("window_days"):
            item["windows"].add(str(row.get("window_days")))
        if row.get("entity_id"):
            item["entities"].add(_norm(row.get("entity_id")))
        value = _number(row.get("metric_value"))
        if value is not None:
            item["values"].append(float(value))
    rows = []
    for item in clusters.values():
        evidence_count = int(item["count"])
        values = item["values"]
        rows.append(OrderedDict([
            ("metric_name", item["metric_name"]),
            ("entity_type", item["entity_type"]),
            ("phase_id", item["phase_id"]),
            ("evidence_count", evidence_count),
            ("window_coverage", len(item["windows"])),
            ("phase_coverage", 1 if item["phase_id"] else 0),
            ("recurrence_count", max(0, evidence_count - 1)),
            ("entity_coverage", len(item["entities"])),
            ("average_metric_value", _round(sum(values) / len(values)) if values else None),
            ("max_metric_value", _round(max(values)) if values else None),
            ("confidence_label", _confidence(evidence_count, len(item["windows"]), 1 if item["phase_id"] else 0)),
        ]))
    return sorted(rows, key=lambda r: (-r["evidence_count"], -r["window_coverage"], r["metric_name"], r["entity_type"], r["phase_id"]))[: _bounded_top_n(top_n)]


def _load_compact_sources(source_paths: Sequence[str | Path]) -> tuple[list[OrderedDict[str, Any]], list[Mapping[str, Any]], list[str]]:
    inspected: list[OrderedDict[str, Any]] = []
    fallback_facts: list[Mapping[str, Any]] = []
    missing: list[str] = []
    for raw in source_paths:
        path = Path(raw)
        if not path.exists():
            missing.append(path.as_posix())
            inspected.append(OrderedDict([("path", path.as_posix()), ("status", "missing")]))
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        inspected.append(OrderedDict([("path", path.as_posix()), ("status", "loaded"), ("schema_version", payload.get("schema_version") if isinstance(payload, Mapping) else None), ("digest", _source_digest(payload))]))
        if isinstance(payload, Mapping):
            fallback_facts.extend(_compact_payload_to_facts(path.as_posix(), payload))
    return inspected, fallback_facts, missing


def _compact_payload_to_facts(path: str, payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    findings = payload.get("findings") if isinstance(payload.get("findings"), Mapping) else {}
    for section, metric_name in (("persistent_structural_hubs", "persistence_score"), ("stable_structural_anchors", "stability_score"), ("unstable_or_drifting_structures", "drift_score"), ("replay_density_leaders", "replay_density"), ("persistent_fragility_sources", "fragility_score")):
        for item in (findings.get(section) or [])[:MAX_TOP_N]:
            if isinstance(item, Mapping):
                rows.append({
                    "phase_id": payload.get("phase_id") or "compact_artifact",
                    "entity_type": item.get("entity_type") or "artifact_entity",
                    "entity_id": item.get("name") or item.get("entity_id"),
                    "metric_name": metric_name,
                    "metric_value": item.get(metric_name),
                    "window_days": (item.get("supporting_windows") or [None])[0] if isinstance(item.get("supporting_windows"), list) else None,
                    "payload_jsonb": {"source_artifact": path, "section": section, "confidence_label": item.get("confidence_label")},
                })
    return rows


def _suppressed_summary(diagnostics: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    counter: Counter[tuple[str, str]] = Counter((_norm(row.get("metric_name")), _norm(row.get("entity_type") or "diagnostic")) for row in diagnostics)
    return [OrderedDict([("metric_name", metric), ("entity_type", entity_type), ("suppressed_count", count), ("reason", "pipeline diagnostic excluded from executive ecosystem findings")]) for (metric, entity_type), count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))[: _bounded_top_n(top_n)]]


def _executive_summary(findings: Mapping[str, Sequence[Mapping[str, Any]]], has_ecosystem: bool) -> list[str]:
    if not has_ecosystem:
        return ["No fact-native ecosystem findings were produced; available inputs contained only missing or pipeline-diagnostic evidence."]
    templates = [
        ("fact_native_persistent_hubs", "Persistent hub", "persistence_score"),
        ("cross_window_persistence_leaders", "Cross-window persistence leader", "cross_window_score"),
        ("stable_ecosystem_anchors", "Stable ecosystem anchor", "stability_score"),
        ("replay_density_and_recurrence_leaders", "Replay-density leader", "replay_density_score"),
        ("fact_native_fragility_sources", "Fragility source", "fragility_score"),
        ("drift_and_instability_leaders", "Drift/instability leader", "drift_score"),
    ]
    lines: list[str] = []
    for section, label, score_key in templates:
        for row in (findings.get(section) or [])[:2]:
            lines.append(f"{label}: {row.get('entity_type')} {row.get('name')} scored {row.get(score_key)} with {row.get('evidence_count')} fact rows across {row.get('window_coverage')} windows ({row.get('confidence_label')} confidence).")
            if len(lines) >= 10:
                return lines
    return lines[:10]


def build_fact_native_historical_findings(*, observation_facts: Iterable[Mapping[str, Any]] | None = None, compact_source_paths: Sequence[str | Path] = (), top_n: int = DEFAULT_TOP_N, max_fact_rows: int = MAX_LOCAL_FACT_ROWS) -> OrderedDict[str, Any]:
    supplied = [row for row in (observation_facts or []) if isinstance(row, Mapping)][: max(0, min(int(max_fact_rows), MAX_LOCAL_FACT_ROWS))]
    inspected, fallback_rows, missing = _load_compact_sources(compact_source_paths) if compact_source_paths else ([], [], [])
    all_rows = (supplied + fallback_rows)[:MAX_LOCAL_FACT_ROWS]
    ecosystem_facts, diagnostics = _classify_facts(all_rows)
    limit = _bounded_top_n(top_n)
    has_ecosystem = bool(ecosystem_facts)
    findings: OrderedDict[str, Any] = OrderedDict([
        ("executive_summary", []),
        ("fact_native_persistent_hubs", _aggregate(ecosystem_facts, category="hubs", top_n=limit)),
        ("fact_native_fragility_sources", _aggregate(ecosystem_facts, category="fragility", top_n=limit)),
        ("cross_window_persistence_leaders", _aggregate(ecosystem_facts, category="cross_window", top_n=limit)),
        ("drift_and_instability_leaders", _aggregate(ecosystem_facts, category="drift", top_n=limit)),
        ("replay_density_and_recurrence_leaders", _aggregate(ecosystem_facts, category="replay", top_n=limit)),
        ("stable_ecosystem_anchors", _aggregate(ecosystem_facts, category="anchors", top_n=limit)),
        ("observation_pattern_clusters", _pattern_clusters(ecosystem_facts, limit)),
        ("suppressed_pipeline_diagnostics", _suppressed_summary(diagnostics, limit)),
    ])
    findings["executive_summary"] = _executive_summary(findings, has_ecosystem)
    limitations = ["Analysis is local-only and bounded to supplied observation facts plus optional compact local artifacts; no live collection or governed workflow activation is performed."]
    if not has_ecosystem:
        limitations.append("No fact-native ecosystem observations were available, so HIST-INTEL-1B fails gracefully rather than fabricating ecosystem findings.")
    if diagnostics:
        limitations.append("Pipeline diagnostics were detected and suppressed from the executive summary when ecosystem facts were available.")
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("phase_id", PHASE_ID),
        ("phase_name", PHASE_NAME),
        ("status", "ok" if has_ecosystem else "limited"),
        ("top_n", limit),
        ("fact_rows_supplied", len(supplied)),
        ("fact_rows_considered", len(all_rows)),
        ("fact_native_ecosystem_rows", len(ecosystem_facts)),
        ("pipeline_diagnostic_rows_suppressed", len(diagnostics)),
        ("compact_source_artifacts_inspected", inspected),
        ("missing_compact_sources", missing),
        ("source_digest", _source_digest({"facts": all_rows, "sources": inspected})),
        ("governance_certification", governance_certification()),
        ("findings", findings),
        ("limitations", limitations),
    ])


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# HIST-INTEL-1B Fact-Native Historical Findings Expansion\n\n",
        "## Objective\nMine local SEFI observation facts and compact local artifacts for ecosystem findings while preserving analysis-only governance.\n\n",
        "## Governance certification\n",
    ]
    for key, value in (report.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {str(value).lower()}\n")
    lines.append("\n## Executive summary\n")
    findings = report.get("findings") or {}
    for item in findings.get("executive_summary") or []:
        lines.append(f"- {item}\n")
    sections = [
        ("Fact-native persistent hubs", "fact_native_persistent_hubs", "persistence_score"),
        ("Fact-native fragility sources", "fact_native_fragility_sources", "fragility_score"),
        ("Cross-window persistence leaders", "cross_window_persistence_leaders", "cross_window_score"),
        ("Drift and instability leaders", "drift_and_instability_leaders", "drift_score"),
        ("Replay-density and recurrence leaders", "replay_density_and_recurrence_leaders", "replay_density_score"),
        ("Stable ecosystem anchors", "stable_ecosystem_anchors", "stability_score"),
    ]
    for title, key, score_key in sections:
        lines.append(f"\n## {title}\n")
        rows = findings.get(key) or []
        if not rows:
            lines.append("- No supported fact-native ecosystem findings from available inputs.\n")
            continue
        for row in rows:
            lines.append(f"- {row.get('entity_type')} {row.get('name')}: {score_key}={row.get(score_key)} evidence_count={row.get('evidence_count')} window_coverage={row.get('window_coverage')} phase_coverage={row.get('phase_coverage')} confidence={row.get('confidence_label')}\n")
    lines.append("\n## Observation-pattern clusters\n")
    for row in findings.get("observation_pattern_clusters") or []:
        lines.append(f"- {row.get('metric_name')} / {row.get('entity_type')} / {row.get('phase_id')}: evidence_count={row.get('evidence_count')} window_coverage={row.get('window_coverage')} confidence={row.get('confidence_label')}\n")
    lines.append("\n## Suppressed pipeline diagnostics\n")
    suppressed = findings.get("suppressed_pipeline_diagnostics") or []
    if not suppressed:
        lines.append("- No pipeline diagnostics detected in considered inputs.\n")
    for row in suppressed:
        lines.append(f"- {row.get('metric_name')} ({row.get('entity_type')}): suppressed_count={row.get('suppressed_count')} reason={row.get('reason')}\n")
    lines.append("\n## Limitations\n")
    for item in report.get("limitations") or []:
        lines.append(f"- {item}\n")
    return "".join(lines)


def write_reports(report: Mapping[str, Any], *, json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH, markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH) -> OrderedDict[str, str]:
    json_path = Path(json_report_path)
    markdown_path = Path(markdown_report_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return OrderedDict([("json_report_path", json_path.as_posix()), ("markdown_report_path", markdown_path.as_posix())])


def run_hist_intel1b(*, observation_facts: Iterable[Mapping[str, Any]] | None = None, compact_source_paths: Sequence[str | Path] = (), top_n: int = DEFAULT_TOP_N, json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH, markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH) -> OrderedDict[str, Any]:
    report = build_fact_native_historical_findings(observation_facts=observation_facts, compact_source_paths=compact_source_paths, top_n=top_n)
    paths = write_reports(report, json_report_path=json_report_path, markdown_report_path=markdown_report_path)
    report["output_paths"] = paths
    return report
