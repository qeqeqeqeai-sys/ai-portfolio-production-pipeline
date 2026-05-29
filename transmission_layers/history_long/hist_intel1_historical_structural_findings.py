from __future__ import annotations

import json
from collections import Counter, OrderedDict, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

PHASE_ID = "HIST-INTEL-1"
PHASE_NAME = "HIST-INTEL-1_historical_structural_findings"
SCHEMA_VERSION = "hist_intel1_v1"
DEFAULT_JSON_REPORT_PATH = "reports/hist_intel1_historical_structural_findings.json"
DEFAULT_MARKDOWN_REPORT_PATH = "reports/hist_intel1_historical_structural_findings.md"
DEFAULT_SOURCE_PATHS = (
    "artifacts/hist_long4_real_multi_window_ecology_review.json",
    "artifacts/hist_long5b_temporal_delta_sensitivity_classification.json",
    "artifacts/hist_long6_cross_sectional_ecology_differentiation.json",
    "artifacts/hist_long7_intra_group_structural_contrast.json",
)
DEFAULT_TOP_N = 10
CONFIDENCE_LABELS = {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT"}


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Mapping):
        for key in ("value", "score", "metric_value", "share", "density", "ratio", "universe_hhi", "stability_score"):
            found = _number(value.get(key))
            if found is not None:
                return found
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _text(value).lower()


def _bounded_limit(top_n: int | None) -> int:
    return max(0, min(int(top_n if top_n is not None else DEFAULT_TOP_N), DEFAULT_TOP_N))


def _source_digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def governance_certification() -> OrderedDict[str, bool]:
    return OrderedDict([
        ("analysis_only", True),
        ("no_provider_calls", True),
        ("no_supabase_writes", True),
        ("no_prediction", True),
        ("no_trading", True),
        ("no_portfolio_recommendation", True),
        ("no_governed_activation", True),
    ])


def _confidence(evidence_count: int, window_count: int = 0, independent_sources: int = 0) -> str:
    if evidence_count <= 0:
        return "INSUFFICIENT"
    if window_count >= 2 or independent_sources >= 2 or evidence_count >= 3:
        return "HIGH"
    if evidence_count >= 2:
        return "MEDIUM"
    return "LOW"


def _load_sources(source_paths: Sequence[str | Path]) -> tuple[OrderedDict[str, Any], list[str]]:
    sources: OrderedDict[str, Any] = OrderedDict()
    missing: list[str] = []
    for raw_path in source_paths:
        path = Path(raw_path)
        key = path.as_posix()
        if not path.exists():
            missing.append(key)
            sources[key] = OrderedDict([("status", "missing")])
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources[key] = OrderedDict([
            ("status", "loaded"),
            ("schema_version", payload.get("schema_version") if isinstance(payload, Mapping) else None),
            ("phase_status", payload.get("status") if isinstance(payload, Mapping) else None),
            ("digest", _source_digest(payload)),
            ("payload", payload),
        ])
    return sources, missing


def _loaded_payloads(sources: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    loaded = []
    for path, row in sources.items():
        payload = row.get("payload") if isinstance(row, Mapping) else None
        if isinstance(payload, Mapping):
            loaded.append((path, payload))
    return loaded


def _fact_payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb")
    return payload if isinstance(payload, Mapping) else {}


def _window(row: Mapping[str, Any]) -> Any:
    return row.get("window_days") or row.get("window_trading_days") or row.get("window")


def _add_candidate(bucket: dict[tuple[str, str], dict[str, Any]], *, entity_type: str, name: str, score: float | None = None, window: Any = None, source: str, evidence: str) -> None:
    clean = _norm(name)
    if not clean:
        return
    key = (entity_type, clean)
    item = bucket.setdefault(key, {"entity_type": entity_type, "name": clean, "scores": [], "windows": set(), "sources": set(), "evidence": []})
    if score is not None:
        item["scores"].append(float(score))
    if window not in (None, ""):
        item["windows"].add(str(window))
    item["sources"].add(source)
    item["evidence"].append(evidence)


def _finish_ranked(bucket: Mapping[tuple[str, str], Mapping[str, Any]], *, top_n: int, score_name: str, default_score: float = 0.0) -> list[OrderedDict[str, Any]]:
    rows = []
    for item in bucket.values():
        evidence_count = len(item.get("evidence") or [])
        windows = sorted(item.get("windows") or [], key=str)
        sources = sorted(item.get("sources") or [])
        scores = item.get("scores") or []
        score = _round(sum(scores) / len(scores)) if scores else default_score
        if score is None:
            score = default_score
        rows.append(OrderedDict([
            ("entity_type", item["entity_type"]),
            ("name", item["name"]),
            (score_name, score),
            ("window_coverage", len(windows)),
            ("supporting_windows", windows),
            ("evidence_count", evidence_count),
            ("source_count", len(sources)),
            ("confidence_label", _confidence(evidence_count, len(windows), len(sources))),
            ("supporting_evidence", sorted(item.get("evidence") or [])[:5]),
        ]))
    return sorted(rows, key=lambda r: (-(r.get(score_name) or 0), -r["window_coverage"], -r["evidence_count"], r["entity_type"], r["name"]))[: _bounded_limit(top_n)]


def _extract_hubs(sources: Mapping[str, Any], facts: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    bucket: dict[tuple[str, str], dict[str, Any]] = {}
    for path, payload in _loaded_payloads(sources):
        if "hist_long4" in path:
            for row in payload.get("window_level_results") or []:
                if not isinstance(row, Mapping):
                    continue
                for group, container, key in (("sector", row.get("sector_hhi"), "sector"), ("subsector", row.get("subsector_hhi"), "subsector")):
                    for node in (container or {}).get(f"strongest_{group}s", []) if isinstance(container, Mapping) else []:
                        _add_candidate(bucket, entity_type=group, name=node.get(key), score=_number(node.get("share")), window=_window(row), source=path, evidence=f"{group} high-importance in {row.get('window_trading_days')}d")
            for group, key in (("sector", "strongest_recurring_sectors"), ("subsector", "strongest_recurring_subsectors")):
                name_key = group
                for node in ((payload.get("bounded_diagnostics") or {}).get(key) or []):
                    if isinstance(node, Mapping):
                        windows = int(node.get("window_count") or 0)
                        _add_candidate(bucket, entity_type=group, name=node.get(name_key), score=min(1.0, windows / 3), window=f"{windows}_windows", source=path, evidence=f"recurs across {windows} windows")
        if "hist_long6" in path:
            findings = payload.get("findings") or {}
            for group, list_key, name_key in (("sector", "strongest_differentiated_sectors", "sector"), ("subsector", "strongest_differentiated_subsectors", "subsector")):
                for node in findings.get(list_key) or []:
                    if isinstance(node, Mapping):
                        score = _number(node.get("differentiation_score")) or _number(node.get("concentration_contribution"))
                        _add_candidate(bucket, entity_type=group, name=node.get(name_key), score=score, source=path, evidence=f"cross-sectional {node.get('representation_label', 'differentiated')}")
        if "hist_long7" in path:
            for row in payload.get("group_morphology_decomposition") or []:
                if isinstance(row, Mapping):
                    metrics = row.get("metrics") or {}
                    _add_candidate(bucket, entity_type="group", name=row.get("group"), score=_number(metrics.get("morphology_persistence_score")), window="20_60_120", source=path, evidence="intra-group persistent morphology")
    for row in facts:
        payload = _fact_payload(row)
        name = row.get("entity_id") or payload.get("dimension")
        if row.get("metric_name") in {"persistence_score", "overall_persistence_score"} or "persistence_score" in payload:
            _add_candidate(bucket, entity_type=str(row.get("entity_type") or "fact_entity"), name=name, score=_number(row.get("metric_value")) or _number(payload.get("persistence_score")), window=_window(row), source="observation_facts", evidence=f"fact metric {row.get('metric_name')}")
    return _finish_ranked(bucket, top_n=top_n, score_name="persistence_score")


def _extract_fragility(sources: Mapping[str, Any], facts: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    bucket: dict[tuple[str, str], dict[str, Any]] = {}
    for path, payload in _loaded_payloads(sources):
        if "hist_long4" in path:
            for symbol in (payload.get("bounded_diagnostics") or {}).get("recurring_weak_symbols") or []:
                _add_candidate(bucket, entity_type="symbol", name=symbol, score=0.5, source=path, evidence="recurring weak symbol")
            for row in payload.get("window_level_results") or []:
                if isinstance(row, Mapping):
                    for symbol in row.get("weak_symbols") or []:
                        _add_candidate(bucket, entity_type="symbol", name=symbol, score=0.4, window=_window(row), source=path, evidence=f"weak in {row.get('window_trading_days')}d")
        if "hist_long5b" in path:
            frag = payload.get("fragility_emergence_detection") or {}
            for window, reasons in (frag.get("reasons_by_window") or {}).items():
                if isinstance(reasons, Sequence) and not isinstance(reasons, (str, bytes)):
                    for reason in reasons:
                        _add_candidate(bucket, entity_type="window", name=str(window), score=0.6, window=window, source=path, evidence=str(reason)[:96])
            for row in payload.get("sensitivity_ranking") or []:
                if isinstance(row, Mapping) and str(row.get("classification")) in {"highly_sensitive", "sensitive"}:
                    score = 1.0 - (_number(row.get("stability_score")) or 0.0)
                    _add_candidate(bucket, entity_type="metric", name=row.get("metric"), score=score, source=path, evidence=f"{row.get('classification')} temporal sensitivity")
        if "hist_long7" in path:
            for row in payload.get("group_morphology_decomposition") or []:
                if not isinstance(row, Mapping):
                    continue
                flags = row.get("fragility_indicators") or {}
                active = [key for key, value in flags.items() if value]
                if active:
                    _add_candidate(bucket, entity_type="group", name=row.get("group"), score=min(1.0, len(active) / max(len(flags), 1)), window="20_60_120", source=path, evidence="; ".join(sorted(active))[:96])
    for row in facts:
        payload = _fact_payload(row)
        score = _number(row.get("metric_value")) or _number(payload.get("emerging_fragility_score"))
        if row.get("metric_name") == "emerging_fragility_score" and score is not None:
            _add_candidate(bucket, entity_type=str(row.get("entity_type") or "fact_entity"), name=row.get("entity_id"), score=score, window=_window(row), source="observation_facts", evidence=f"fragility fact {payload.get('emerging_fragility_class', '')}")
    return _finish_ranked(bucket, top_n=top_n, score_name="fragility_score")


def _extract_paths(sources: Mapping[str, Any], facts: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    counter: Counter[str] = Counter()
    windows: dict[str, set[str]] = defaultdict(set)
    evidence: dict[str, set[str]] = defaultdict(set)
    for path, payload in _loaded_payloads(sources):
        if "hist_long4" in path:
            for row in payload.get("window_level_results") or []:
                if not isinstance(row, Mapping):
                    continue
                sectors = [n.get("sector") for n in ((row.get("sector_hhi") or {}).get("strongest_sectors") or [])[:3] if isinstance(n, Mapping)]
                subsectors = [n.get("subsector") for n in ((row.get("subsector_hhi") or {}).get("strongest_subsectors") or [])[:3] if isinstance(n, Mapping)]
                for sector, subsector in zip(sectors, subsectors):
                    if _norm(sector) and _norm(subsector):
                        label = f"{_norm(sector)} / {_norm(subsector)} co-occurrence"
                        counter[label] += 1; windows[label].add(str(_window(row))); evidence[label].add(path)
        if "hist_long7" in path:
            for row in payload.get("group_morphology_decomposition") or []:
                if isinstance(row, Mapping):
                    read = row.get("structural_read") or {}
                    label = f"{_norm(row.get('group'))} remained {read.get('persistent_vs_episodic', 'observed')} and {read.get('coherent_vs_stratified', 'classified')}"
                    counter[label] += len(row.get("window_observations") or [1]); evidence[label].add(path)
                    for obs in row.get("window_observations") or []:
                        if isinstance(obs, Mapping): windows[label].add(str(obs.get("window")))
    for row in facts:
        payload = _fact_payload(row)
        for item in payload.get("recurring_structures") or payload.get("morphologies") or []:
            label = f"{_norm(item)} recurrence"
            counter[label] += 1; windows[label].add(str(_window(row) or row.get("run_id") or "fact")); evidence[label].add("observation_facts")
    rows = []
    for label, count in counter.items():
        rows.append(OrderedDict([
            ("path", label),
            ("recurrence_count", count),
            ("supporting_windows", sorted(windows[label], key=str)),
            ("evidence_count", len(evidence[label])),
            ("confidence_label", _confidence(count, len(windows[label]), len(evidence[label]))),
            ("wording_note", "Directional wording is omitted unless direction is explicit in source facts."),
        ]))
    return sorted(rows, key=lambda r: (-r["recurrence_count"], -len(r["supporting_windows"]), r["path"]))[: _bounded_limit(top_n)]


def _extract_anchors(sources: Mapping[str, Any], facts: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    bucket: dict[tuple[str, str], dict[str, Any]] = {}
    for path, payload in _loaded_payloads(sources):
        if "hist_long7" in path:
            for row in payload.get("group_morphology_decomposition") or []:
                if isinstance(row, Mapping):
                    indicators = row.get("persistence_indicators") or {}
                    active = sum(1 for value in indicators.values() if value)
                    score = active / max(len(indicators), 1)
                    if score > 0:
                        windows = [obs.get("window") for obs in row.get("window_observations") or [] if isinstance(obs, Mapping)] or ["20_60_120"]
                        for window in windows:
                            _add_candidate(bucket, entity_type="group", name=row.get("group"), score=score, window=window, source=path, evidence="stable persistence indicators")
        if "hist_long5b" in path:
            for row in payload.get("sensitivity_ranking") or []:
                if isinstance(row, Mapping) and str(row.get("classification")) in {"stable", "low_sensitivity"}:
                    _add_candidate(bucket, entity_type="metric", name=row.get("metric"), score=_number(row.get("stability_score")), source=path, evidence="low temporal sensitivity")
    for row in facts:
        payload = _fact_payload(row)
        if payload.get("stability_class") == "STABLE":
            _add_candidate(bucket, entity_type=str(row.get("entity_type") or "fact_entity"), name=row.get("entity_id"), score=_number(row.get("metric_value")) or _number(payload.get("persistence_score")) or 1.0, window=_window(row), source="observation_facts", evidence="stable observation fact")
    return _finish_ranked(bucket, top_n=top_n, score_name="stability_score")


def _extract_drift(sources: Mapping[str, Any], facts: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    bucket: dict[tuple[str, str], dict[str, Any]] = {}
    for path, payload in _loaded_payloads(sources):
        if "hist_long5b" in path:
            for row in payload.get("sensitivity_ranking") or []:
                if isinstance(row, Mapping) and str(row.get("classification")) in {"highly_sensitive", "sensitive"}:
                    score = _number(row.get("volatility_score")) or (1.0 - (_number(row.get("stability_score")) or 0.0))
                    _add_candidate(bucket, entity_type="metric", name=row.get("metric"), score=score, source=path, evidence=f"{row.get('classification')} change across windows")
    for row in facts:
        payload = _fact_payload(row)
        drift = str(payload.get("drift_class") or "")
        delta = _number(row.get("metric_value"))
        if drift in {"DETERIORATING", "MIXED"} or (delta is not None and delta < 0):
            score = abs(delta) if delta is not None else 0.5
            _add_candidate(bucket, entity_type=str(row.get("entity_type") or "fact_entity"), name=row.get("entity_id") or row.get("metric_name"), score=min(1.0, score), window=_window(row), source="observation_facts", evidence=f"drift_class {drift or 'negative_delta'}")
    return _finish_ranked(bucket, top_n=top_n, score_name="drift_score")


def _extract_replay_density(sources: Mapping[str, Any], facts: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    bucket: dict[tuple[str, str], dict[str, Any]] = {}
    for path, payload in _loaded_payloads(sources):
        if "hist_long4" in path:
            for row in payload.get("window_level_results") or []:
                if isinstance(row, Mapping):
                    density = _number(row.get("replay_density"))
                    if density is not None:
                        _add_candidate(bucket, entity_type="window", name=f"{row.get('window_trading_days')}d replay ecology", score=density, window=_window(row), source=path, evidence="window replay density")
                    for group, container, key in (("sector", row.get("sector_hhi"), "sector"), ("subsector", row.get("subsector_hhi"), "subsector")):
                        for node in (container or {}).get(f"strongest_{group}s", []) if isinstance(container, Mapping) else []:
                            _add_candidate(bucket, entity_type=group, name=node.get(key), score=density, window=_window(row), source=path, evidence="replay-density concentration context")
    for row in facts:
        if row.get("metric_name") in {"replay_density", "replay_saturation"}:
            _add_candidate(bucket, entity_type=str(row.get("entity_type") or "fact_entity"), name=row.get("entity_id") or row.get("metric_name"), score=_number(row.get("metric_value")), window=_window(row), source="observation_facts", evidence=f"{row.get('metric_name')} fact")
    return _finish_ranked(bucket, top_n=top_n, score_name="replay_density_score")


def _summary(findings: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[str]:
    lines: list[str] = []
    templates = [
        ("persistent_structural_hubs", "Persistent hub"),
        ("persistent_fragility_sources", "Fragility source"),
        ("recurrent_propagation_paths", "Recurrent structural pattern"),
        ("stable_structural_anchors", "Stable anchor"),
        ("unstable_or_drifting_structures", "Drifting structure"),
        ("replay_density_leaders", "Replay-density leader"),
    ]
    for key, label in templates:
        for item in (findings.get(key) or [])[:2]:
            if key == "recurrent_propagation_paths":
                lines.append(f"{label}: {item.get('path')} recurred {item.get('recurrence_count')} times with {item.get('confidence_label')} confidence.")
            else:
                score_key = next((k for k in item if k.endswith("_score")), None)
                lines.append(f"{label}: {item.get('entity_type')} {item.get('name')} scored {item.get(score_key)} with {item.get('evidence_count')} evidence rows ({item.get('confidence_label')} confidence).")
            if len(lines) >= 10:
                return lines
    return lines[:10]


def build_historical_structural_findings(*, source_paths: Sequence[str | Path] = DEFAULT_SOURCE_PATHS, observation_facts: Iterable[Mapping[str, Any]] | None = None, top_n: int = DEFAULT_TOP_N) -> OrderedDict[str, Any]:
    sources, missing = _load_sources(source_paths)
    facts = [row for row in (observation_facts or []) if isinstance(row, Mapping)]
    inspected = [OrderedDict((k, v) for k, v in row.items() if k != "payload") for row in sources.values()]
    for path, row in zip(sources.keys(), inspected):
        row["path"] = path
    loaded_count = sum(1 for row in sources.values() if row.get("status") == "loaded")
    findings = OrderedDict()
    if missing or (loaded_count == 0 and not facts):
        status = "blocked"
        limitations = ["One or more expected source artifacts were missing; findings fail closed and no findings are fabricated."]
        if loaded_count == 0 and not facts:
            limitations.append("No local source artifact or observation fact rows were available.")
        for key in ("persistent_structural_hubs", "persistent_fragility_sources", "recurrent_propagation_paths", "stable_structural_anchors", "unstable_or_drifting_structures", "replay_density_leaders"):
            findings[key] = []
    else:
        status = "ok"
        limitations = ["Analysis is limited to existing local artifacts and supplied observation facts; no live collection is performed."]
        findings["persistent_structural_hubs"] = _extract_hubs(sources, facts, top_n)
        findings["persistent_fragility_sources"] = _extract_fragility(sources, facts, top_n)
        findings["recurrent_propagation_paths"] = _extract_paths(sources, facts, top_n)
        findings["stable_structural_anchors"] = _extract_anchors(sources, facts, top_n)
        findings["unstable_or_drifting_structures"] = _extract_drift(sources, facts, top_n)
        findings["replay_density_leaders"] = _extract_replay_density(sources, facts, top_n)
    findings["executive_summary"] = _summary(findings) if status == "ok" else ["HIST-INTEL-1 did not produce findings because expected local sources were unavailable."]
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("phase_id", PHASE_ID),
        ("phase_name", PHASE_NAME),
        ("status", status),
        ("top_n", _bounded_limit(top_n)),
        ("source_artifacts_inspected", inspected),
        ("missing_sources", missing),
        ("observation_fact_rows_supplied", len(facts)),
        ("source_digest", _source_digest({"sources": inspected, "facts": facts})),
        ("governance_certification", governance_certification()),
        ("findings", findings),
        ("limitations", limitations),
        ("recommended_next_phase", "Review the bounded findings and, if needed, add a fact-native adapter for additional historical observation fact snapshots without enabling live collection or activation."),
    ])


def render_markdown(report: Mapping[str, Any]) -> str:
    gov = report.get("governance_certification") or {}
    findings = report.get("findings") or {}
    lines = [
        "# HIST-INTEL-1 Historical Structural Findings Engine\n\n",
        "## Objective\nConvert existing local SEFI historical observation facts and structural artifacts into concise, ranked, human-readable historical structural findings.\n\n",
        "## Source artifacts inspected\n",
    ]
    for row in report.get("source_artifacts_inspected") or []:
        lines.append(f"- {row.get('path')}: status={row.get('status')} schema={row.get('schema_version')} digest={row.get('digest')}\n")
    if report.get("missing_sources"):
        lines.append(f"- missing_sources: {', '.join(report.get('missing_sources') or [])}\n")
    lines.append("\n## Governance certification\n")
    for key, value in gov.items():
        lines.append(f"- {key}: {str(value).lower()}\n")
    lines.append("\n## Executive summary\n")
    for item in findings.get("executive_summary") or []:
        lines.append(f"- {item}\n")

    sections = [
        ("Persistent structural hubs", "persistent_structural_hubs", "persistence_score"),
        ("Persistent fragility sources", "persistent_fragility_sources", "fragility_score"),
        ("Recurrent propagation paths", "recurrent_propagation_paths", "recurrence_count"),
        ("Stable structural anchors", "stable_structural_anchors", "stability_score"),
        ("Unstable / drifting structures", "unstable_or_drifting_structures", "drift_score"),
        ("Replay-density leaders", "replay_density_leaders", "replay_density_score"),
    ]
    for title, key, score_key in sections:
        lines.append(f"\n## {title}\n")
        rows = findings.get(key) or []
        if not rows:
            lines.append("- No supported findings from available sources.\n")
            continue
        for row in rows:
            if key == "recurrent_propagation_paths":
                lines.append(f"- {row.get('path')}: recurrence_count={row.get('recurrence_count')} windows={row.get('supporting_windows')} confidence={row.get('confidence_label')}\n")
            else:
                lines.append(f"- {row.get('entity_type')} {row.get('name')}: {score_key}={row.get(score_key)} window_coverage={row.get('window_coverage')} evidence_count={row.get('evidence_count')} confidence={row.get('confidence_label')}\n")
    lines.append("\n## Limitations\n")
    for item in report.get("limitations") or []:
        lines.append(f"- {item}\n")
    lines.append("\n## Recommended next phase\n")
    lines.append(f"- {report.get('recommended_next_phase')}\n")
    return "".join(lines)


def write_reports(report: Mapping[str, Any], *, json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH, markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH) -> OrderedDict[str, str]:
    json_path = Path(json_report_path)
    md_path = Path(markdown_report_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return OrderedDict([("json_report_path", json_path.as_posix()), ("markdown_report_path", md_path.as_posix())])


def run_hist_intel1(*, source_paths: Sequence[str | Path] = DEFAULT_SOURCE_PATHS, observation_facts: Iterable[Mapping[str, Any]] | None = None, top_n: int = DEFAULT_TOP_N, json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH, markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH) -> OrderedDict[str, Any]:
    report = build_historical_structural_findings(source_paths=source_paths, observation_facts=observation_facts, top_n=top_n)
    paths = write_reports(report, json_report_path=json_report_path, markdown_report_path=markdown_report_path)
    report["output_paths"] = paths
    return report
