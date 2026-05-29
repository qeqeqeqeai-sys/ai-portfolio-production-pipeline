from __future__ import annotations

import json
from collections import Counter, OrderedDict
from hashlib import sha256
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

PHASE_ID = "HIST-FACT-1"
PHASE_NAME = "HIST-FACT-1_historical_observation_fact_expansion"
SCHEMA_VERSION = "hist_fact1_v1"
VALID_CONFIDENCE_LABELS = ("HIGH", "MEDIUM", "LOW", "INSUFFICIENT")
DEFAULT_MAX_FACTS = 750
DEFAULT_JSON_REPORT_PATH = "reports/hist_fact1_observation_fact_expansion.json"
DEFAULT_MARKDOWN_REPORT_PATH = "reports/hist_fact1_observation_fact_expansion.md"
DEFAULT_EXPANDED_FACTS_PATH = "reports/hist_fact1_expanded_observation_facts.json"
DEFAULT_SOURCE_PATHS: OrderedDict[str, str] = OrderedDict(
    [
        ("HIST-LONG-4", "artifacts/hist_long4_real_multi_window_ecology_review.json"),
        ("HIST-LONG-5B", "artifacts/hist_long5b_temporal_delta_sensitivity_classification.json"),
        ("HIST-LONG-6", "artifacts/hist_long6_cross_sectional_ecology_differentiation.json"),
        ("HIST-LONG-7", "artifacts/hist_long7_intra_group_structural_contrast.json"),
        ("HIST-LONG-8", "reports/hist_long8_cross_window_persistence.md"),
        ("HIST-LONG-9", "reports/hist_long9_persistence_drift.md"),
    ]
)
GOVERNANCE_CERTIFICATION: OrderedDict[str, bool] = OrderedDict(
    [
        ("analysis_only", True),
        ("local_only", True),
        ("no_provider_calls", True),
        ("no_supabase_writes", True),
        ("no_prediction", True),
        ("no_trading", True),
        ("no_portfolio_recommendation", True),
        ("no_governed_activation", True),
    ]
)


def _as_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Mapping):
        for key in ("value", "metric_value", "score", "density", "ratio", "share", "universe_hhi", "count"):
            found = _as_number(value.get(key))
            if found is not None:
                return found
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _round(value: Any) -> float | None:
    number = _as_number(value)
    return None if number is None else round(number, 6)


def _clean(value: Any) -> str:
    return "_".join(str(value).strip().lower().split())


def _window(value: Any) -> int | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _source_digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _stable_fact_id(parts: Sequence[Any]) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return f"histfact1_{sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _confidence(evidence_count: int, window_count: int = 0) -> str:
    if evidence_count <= 0:
        return "INSUFFICIENT"
    if evidence_count >= 3 or window_count >= 3:
        return "HIGH"
    if evidence_count >= 2 or window_count >= 2:
        return "MEDIUM"
    return "LOW"


def _bounded_payload(payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    ordered = OrderedDict((str(key), payload[key]) for key in sorted(payload, key=str))
    raw = json.dumps(ordered, sort_keys=True, default=str)
    if len(raw.encode("utf-8")) <= 4096:
        return ordered
    compact = OrderedDict()
    for key, value in ordered.items():
        compact[key] = value if not isinstance(value, (list, dict)) else f"{type(value).__name__}[{len(value)}]"
    return compact


def _fact(
    *,
    fact_type: str,
    entity_type: str,
    entity_id: Any,
    metric_name: str,
    metric_value: Any,
    window_days: int | None,
    evidence_count: int,
    source_phase: str,
    source_artifact: str,
    payload_jsonb: Mapping[str, Any] | None = None,
    window_count: int = 0,
) -> OrderedDict[str, Any]:
    entity = _clean(entity_id) if entity_id is not None else "unknown"
    metric = _clean(metric_name)
    confidence_label = _confidence(evidence_count, window_count)
    row = OrderedDict(
        [
            ("phase_id", PHASE_ID),
            ("fact_type", _clean(fact_type)),
            ("entity_type", _clean(entity_type)),
            ("entity_id", entity.upper() if _clean(entity_type) == "symbol" else entity),
            ("metric_name", metric),
            ("metric_value", _round(metric_value)),
            ("window_days", window_days),
            ("evidence_count", int(max(0, evidence_count))),
            ("confidence_label", confidence_label),
            ("source_phase", source_phase),
            ("source_artifact", source_artifact),
            ("payload_jsonb", _bounded_payload(payload_jsonb or {})),
        ]
    )
    row["fact_id"] = _stable_fact_id(
        [
            row["phase_id"],
            row["fact_type"],
            row["entity_type"],
            row["entity_id"],
            row["metric_name"],
            row["window_days"],
            row["source_phase"],
            row["source_artifact"],
            json.dumps(row["payload_jsonb"], sort_keys=True, default=str),
        ]
    )
    return row


def _artifact_path(source_paths: Mapping[str, str | Path] | None) -> OrderedDict[str, Path]:
    selected = source_paths or DEFAULT_SOURCE_PATHS
    return OrderedDict((phase, Path(path)) for phase, path in selected.items())


def _load_sources(source_paths: Mapping[str, str | Path] | None = None) -> tuple[OrderedDict[str, Mapping[str, Any]], list[str], list[str]]:
    loaded: OrderedDict[str, Mapping[str, Any]] = OrderedDict()
    loaded_artifacts: list[str] = []
    missing_artifacts: list[str] = []
    for phase, path in _artifact_path(source_paths).items():
        if not path.exists():
            missing_artifacts.append(path.as_posix())
            continue
        if path.suffix.lower() == ".md":
            loaded[phase] = OrderedDict([("markdown_report_text", path.read_text(encoding="utf-8"))])
        else:
            loaded[phase] = json.loads(path.read_text(encoding="utf-8"))
        loaded_artifacts.append(path.as_posix())
    return loaded, loaded_artifacts, missing_artifacts


def _count_original_facts(value: Any) -> int:
    if isinstance(value, Mapping):
        total = 0
        for key, nested in value.items():
            if str(key) in {"fact_rows", "facts", "observation_facts", "rows"} and isinstance(nested, list):
                total += len([row for row in nested if isinstance(row, Mapping)])
            else:
                total += _count_original_facts(nested)
        return total
    if isinstance(value, list):
        return sum(_count_original_facts(item) for item in value)
    return 0


def _window_rows(hist4: Mapping[str, Any], source_artifact: str) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    for item in hist4.get("window_level_results") or []:
        if not isinstance(item, Mapping):
            continue
        window = _window(item.get("window_trading_days") or item.get("window_days") or item.get("window"))
        metric_pairs = [
            ("replay_density_fact", "window", f"window_{window}", "replay_density", item.get("replay_density")),
            ("replay_stability_fact", "window", f"window_{window}", "replay_saturation", item.get("replay_saturation")),
            ("breadth_expansion_fact", "window", f"window_{window}", "effective_symbol_count", item.get("effective_symbol_count")),
            ("breadth_fragility_fact", "window", f"window_{window}", "failed_count", item.get("failed_count")),
            ("topology_coherence_fact", "window", f"window_{window}", "completeness", item.get("completeness")),
        ]
        for fact_type, entity_type, entity_id, metric, value in metric_pairs:
            rows.append(_fact(fact_type=fact_type, entity_type=entity_type, entity_id=entity_id, metric_name=metric, metric_value=value, window_days=window, evidence_count=1, source_phase="HIST-LONG-4", source_artifact=source_artifact, payload_jsonb={"source_key": metric}))
        for group_type, hhi_key, names_key in (("sector", "sector_hhi", "strongest_sectors"), ("subsector", "subsector_hhi", "strongest_subsectors")):
            hhi = item.get(hhi_key)
            hhi_value = _as_number(hhi)
            rows.append(_fact(fact_type=f"{group_type}_concentration_fact", entity_type="window", entity_id=f"window_{window}", metric_name=hhi_key, metric_value=hhi_value, window_days=window, evidence_count=1, source_phase="HIST-LONG-4", source_artifact=source_artifact, payload_jsonb={"source_key": hhi_key}))
            if isinstance(hhi, Mapping):
                for rank, ranked in enumerate(hhi.get(names_key) or [], start=1):
                    if not isinstance(ranked, Mapping):
                        continue
                    name = ranked.get(group_type)
                    if name:
                        rows.append(_fact(fact_type=f"{group_type}_concentration_fact", entity_type=group_type, entity_id=name, metric_name="window_share", metric_value=ranked.get("share"), window_days=window, evidence_count=1, source_phase="HIST-LONG-4", source_artifact=source_artifact, payload_jsonb={"rank": rank, "symbol_count": ranked.get("symbol_count")}))
    return rows


def _hist5b_rows(hist5b: Mapping[str, Any], source_artifact: str) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    values_by_window = hist5b.get("metric_values_by_window") or {}
    for metric, label in sorted((hist5b.get("structural_persistence_classification") or {}).items()):
        by_window = {str(w): _round(v.get(metric)) for w, v in values_by_window.items() if isinstance(v, Mapping) and v.get(metric) is not None}
        windows = [_window(w) for w in by_window]
        non_null_windows = [w for w in windows if w is not None]
        fact_type = "sector_concentration_fact" if "hhi" in metric else "replay_stability_fact" if metric.startswith("replay") else "topology_persistence_fact" if "topology" in metric or "morphology" in metric else "persistence_fact"
        if label in {"volatile", "emerging", "decaying"}:
            fact_type = "morphology_drift_fact" if "morphology" in metric or "topology" in metric else "structural_instability_fact"
        rows.append(_fact(fact_type=fact_type, entity_type="metric", entity_id=metric, metric_name="classification_code", metric_value={"stable": 1, "emerging": 0.75, "volatile": 0.25, "decaying": 0.1}.get(str(label), 0.5), window_days=None, evidence_count=len(by_window), window_count=len(non_null_windows), source_phase="HIST-LONG-5B", source_artifact=source_artifact, payload_jsonb={"classification": label, "values_by_window": by_window}))
    for table_name, deltas in sorted((hist5b.get("temporal_delta_tables") or {}).items()):
        if not isinstance(deltas, list):
            continue
        for row in deltas[:100]:
            if not isinstance(row, Mapping):
                continue
            metric = row.get("metric")
            if not metric:
                continue
            direction = row.get("direction") or row.get("interpretation")
            fact_type = "persistence_decay_fact" if direction in {"down", "declining", "decaying"} else "replay_recurrence_fact" if row.get("interpretation") == "stable" else "morphology_drift_fact"
            rows.append(_fact(fact_type=fact_type, entity_type="metric", entity_id=metric, metric_name="absolute_delta", metric_value=row.get("absolute_delta"), window_days=_window(row.get("to_window")), evidence_count=2, source_phase="HIST-LONG-5B", source_artifact=source_artifact, payload_jsonb={"table": table_name, "from_window": row.get("from_window"), "to_window": row.get("to_window"), "direction": direction, "interpretation": row.get("interpretation")}))
    return rows


def _hist6_rows(hist6: Mapping[str, Any], source_artifact: str) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    findings = hist6.get("findings") or {}
    for key, items in sorted(findings.items()):
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, Mapping):
                continue
            group_type = item.get("group_type") or ("subsector" if item.get("subsector") else "sector" if item.get("sector") else "group")
            name = item.get(group_type) or item.get("group") or item.get("name")
            if not name:
                continue
            label = str(item.get("representation_label") or item.get("stability_label") or "observed")
            fact_type = f"{group_type}_fragility_fact" if "under" in label or "frag" in key else f"{group_type}_persistence_fact" if "stable" in label else f"{group_type}_concentration_fact"
            rows.append(_fact(fact_type=fact_type, entity_type=group_type, entity_id=name, metric_name="differentiation_score", metric_value=item.get("differentiation_score"), window_days=_window(hist6.get("primary_baseline_window")), evidence_count=3 if str(item.get("confidence", "")).lower() == "high" else 1, source_phase="HIST-LONG-6", source_artifact=source_artifact, payload_jsonb={"finding_bucket": key, "representation_label": item.get("representation_label"), "stability_label": item.get("stability_label"), "symbol_count": item.get("symbol_count"), "symbol_share": item.get("symbol_share")}))
    return rows


def _hist7_rows(hist7: Mapping[str, Any], source_artifact: str) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    for group in hist7.get("group_morphology_decomposition") or []:
        if not isinstance(group, Mapping):
            continue
        name = group.get("group")
        if not name:
            continue
        windows = [_window((row or {}).get("window")) for row in group.get("window_observations") or [] if isinstance(row, Mapping)]
        window_count = len([w for w in windows if w is not None])
        metrics = group.get("metrics") or {}
        reads = group.get("structural_read") or {}
        for metric, fact_type in (
            ("morphology_persistence_score", "entity_persistence_fact"),
            ("structural_coherence_score", "topology_coherence_fact"),
            ("breadth_of_differentiation", "participation_fact"),
            ("hidden_concentration_intensity", "ecosystem_concentration_fact"),
            ("anchor_dependency_score", "structural_anchor_fact"),
            ("leader_tail_gap", "concentration_fragility_fact"),
        ):
            if metric in metrics:
                rows.append(_fact(fact_type=fact_type, entity_type="group", entity_id=name, metric_name=metric, metric_value=metrics.get(metric), window_days=None, evidence_count=max(1, window_count), window_count=window_count, source_phase="HIST-LONG-7", source_artifact=source_artifact, payload_jsonb={"structural_read": reads, "morphology_classifications": group.get("morphology_classifications", [])}))
        for key, flag in sorted((group.get("persistence_indicators") or {}).items()):
            if isinstance(flag, bool):
                rows.append(_fact(fact_type="topology_stability_fact" if flag else "topology_fragmentation_fact", entity_type="group", entity_id=name, metric_name=key, metric_value=1.0 if flag else 0.0, window_days=None, evidence_count=max(1, window_count), window_count=window_count, source_phase="HIST-LONG-7", source_artifact=source_artifact, payload_jsonb={"indicator": key}))
        for key, flag in sorted((group.get("fragility_indicators") or {}).items()):
            if isinstance(flag, bool):
                rows.append(_fact(fact_type="breadth_fragility_fact" if flag else "topology_coherence_fact", entity_type="group", entity_id=name, metric_name=key, metric_value=1.0 if flag else 0.0, window_days=None, evidence_count=max(1, window_count), window_count=window_count, source_phase="HIST-LONG-7", source_artifact=source_artifact, payload_jsonb={"indicator": key}))
    return rows


def _generic_rows(phase: str, payload: Mapping[str, Any], source_artifact: str) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    text = payload.get("markdown_report_text")
    if isinstance(text, str):
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- ") or ":" not in stripped:
                continue
            name = stripped[2:].split(":", 1)[0].strip()
            score_match = re.search(r"score=([-+0-9.]+|None)", stripped)
            delta_match = re.search(r"delta=([-+0-9.]+|None)", stripped)
            class_match = re.search(r"class=([A-Za-z_]+)", stripped)
            if not name or (not score_match and not delta_match and not class_match):
                continue
            numeric = None
            if score_match and score_match.group(1) != "None":
                numeric = score_match.group(1)
            elif delta_match and delta_match.group(1) != "None":
                numeric = delta_match.group(1)
            class_label = class_match.group(1) if class_match else None
            fact_type = "persistence_decay_fact" if "drift" in name or (delta_match and numeric not in (None, "0", "0.0")) else "topology_persistence_fact"
            if class_label == "INSUFFICIENT_DATA":
                fact_type = "structural_instability_fact"
            rows.append(_fact(fact_type=fact_type, entity_type="metric", entity_id=name, metric_name="markdown_report_score", metric_value=numeric, window_days=None, evidence_count=1 if numeric is not None else 0, source_phase=phase, source_artifact=source_artifact, payload_jsonb={"class_label": class_label, "source_line_prefix": stripped[:160]}))
    for section_name in ("persistence_analysis", "cross_window_comparison", "drift_analysis", "findings"):
        section = payload.get(section_name)
        if not isinstance(section, Mapping):
            continue
        for entity_id, row in sorted(section.items()):
            if not isinstance(row, Mapping):
                continue
            score = row.get("persistence_score") or row.get("drift_score") or row.get("metric_value")
            fact_type = "persistence_decay_fact" if "drift" in section_name or "decay" in str(row).lower() else "topology_persistence_fact"
            rows.append(_fact(fact_type=fact_type, entity_type="metric", entity_id=entity_id, metric_name="source_score", metric_value=score, window_days=None, evidence_count=len(row.get("values_by_window") or []) or 1, source_phase=phase, source_artifact=source_artifact, payload_jsonb={"section": section_name, "source_class": row.get("stability_class") or row.get("drift_class")}))
    return rows


def _dedupe_and_bound(rows: Iterable[OrderedDict[str, Any]], max_facts: int) -> list[OrderedDict[str, Any]]:
    unique: dict[str, OrderedDict[str, Any]] = {}
    for row in rows:
        unique.setdefault(row["fact_id"], row)
    ordered = sorted(unique.values(), key=lambda row: (row["fact_type"], row["entity_type"], row["entity_id"], row["metric_name"], row["window_days"] is None, row["window_days"] or -1, row["source_phase"], row["fact_id"]))
    return ordered[: max(0, int(max_facts))]


def build_hist_fact1_expansion(*, source_paths: Mapping[str, str | Path] | None = None, max_facts: int = DEFAULT_MAX_FACTS) -> OrderedDict[str, Any]:
    loaded, loaded_artifacts, missing_artifacts = _load_sources(source_paths)
    rows: list[OrderedDict[str, Any]] = []
    for phase, payload in loaded.items():
        source_artifact = _artifact_path(source_paths).get(phase, Path(phase)).as_posix()
        if phase == "HIST-LONG-4":
            rows.extend(_window_rows(payload, source_artifact))
        elif phase == "HIST-LONG-5B":
            rows.extend(_hist5b_rows(payload, source_artifact))
        elif phase == "HIST-LONG-6":
            rows.extend(_hist6_rows(payload, source_artifact))
        elif phase == "HIST-LONG-7":
            rows.extend(_hist7_rows(payload, source_artifact))
        else:
            rows.extend(_generic_rows(phase, payload, source_artifact))
    facts = _dedupe_and_bound(rows, max_facts)
    original_fact_count = sum(_count_original_facts(payload) for payload in loaded.values())
    fact_type_distribution = OrderedDict(sorted(Counter(row["fact_type"] for row in facts).items()))
    entity_type_distribution = OrderedDict(sorted(Counter(row["entity_type"] for row in facts).items()))
    confidence_distribution = OrderedDict(sorted(Counter(row["confidence_label"] for row in facts).items()))
    source_distribution = OrderedDict(sorted(Counter(row["source_phase"] for row in facts).items()))
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("phase_id", PHASE_ID),
            ("phase_name", PHASE_NAME),
            ("status", "ok" if loaded else "blocked"),
            ("source_digest", _source_digest({phase: payload for phase, payload in loaded.items()})),
            ("governance_certification", GOVERNANCE_CERTIFICATION.copy()),
            ("source_artifacts_loaded", loaded_artifacts),
            ("source_artifacts_missing", missing_artifacts),
            ("original_fact_count", original_fact_count),
            ("expanded_fact_count", len(facts)),
            ("net_new_fact_count", max(0, len(facts) - original_fact_count)),
            ("max_facts", int(max_facts)),
            ("bounded_output", len(facts) <= int(max_facts)),
            ("fact_type_distribution", fact_type_distribution),
            ("entity_type_distribution", entity_type_distribution),
            ("confidence_distribution", confidence_distribution),
            ("source_phase_distribution", source_distribution),
            ("expanded_facts", facts),
        ]
    )


def build_markdown_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# HIST-FACT-1 — Historical Observation Fact Expansion\n\n",
        "## Governance Certification\n",
    ]
    for key, value in report.get("governance_certification", {}).items():
        lines.append(f"- {key}: {str(value).lower()}\n")
    lines.extend(
        [
            "\n## Metrics\n",
            f"- source_artifacts_loaded: {len(report.get('source_artifacts_loaded') or [])}\n",
            f"- source_artifacts_missing: {len(report.get('source_artifacts_missing') or [])}\n",
            f"- original_fact_count: {report.get('original_fact_count')}\n",
            f"- expanded_fact_count: {report.get('expanded_fact_count')}\n",
            f"- net_new_fact_count: {report.get('net_new_fact_count')}\n",
            f"- max_facts: {report.get('max_facts')}\n",
            f"- bounded_output: {str(report.get('bounded_output')).lower()}\n",
            "\n## Fact Type Distribution\n",
        ]
    )
    for key, value in (report.get("fact_type_distribution") or {}).items():
        lines.append(f"- {key}: {value}\n")
    lines.append("\n## Entity Type Distribution\n")
    for key, value in (report.get("entity_type_distribution") or {}).items():
        lines.append(f"- {key}: {value}\n")
    lines.append("\n## Confidence Distribution\n")
    for key, value in (report.get("confidence_distribution") or {}).items():
        lines.append(f"- {key}: {value}\n")
    lines.append("\n## Boundary Statement\n")
    lines.append("HIST-FACT-1 is a deterministic fact-generation layer over existing local historical artifacts. It does not call providers, write Supabase, ingest live data, predict, trade, recommend portfolios, or activate governed workflows.\n")
    return "".join(lines)


def run_hist_fact1_expansion(
    *,
    source_paths: Mapping[str, str | Path] | None = None,
    json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH,
    markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH,
    expanded_facts_path: str | Path = DEFAULT_EXPANDED_FACTS_PATH,
    max_facts: int = DEFAULT_MAX_FACTS,
) -> OrderedDict[str, Any]:
    report = build_hist_fact1_expansion(source_paths=source_paths, max_facts=max_facts)
    json_path = Path(json_report_path)
    md_path = Path(markdown_report_path)
    facts_path = Path(expanded_facts_path)
    for path in (json_path, md_path, facts_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    facts_path.write_text(json.dumps(report["expanded_facts"], indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(build_markdown_report(report), encoding="utf-8")
    return report
