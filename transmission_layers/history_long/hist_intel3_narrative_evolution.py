from __future__ import annotations

import json
from collections import Counter, OrderedDict, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from transmission_layers.history_long.hist_intel2_taxonomy_weighted_intelligence import (
    CONFIDENCE_LABELS,
    DEFAULT_EXPANDED_FACTS_PATH,
    taxonomy_for_fact,
)

PHASE_ID = "HIST-INTEL-3"
PHASE_NAME = "HIST-INTEL-3_narrative_evolution_and_regime_transition_mapping"
SCHEMA_VERSION = "hist_intel3_v1"
DEFAULT_JSON_REPORT_PATH = "reports/hist_intel3_narrative_evolution.json"
DEFAULT_MARKDOWN_REPORT_PATH = "reports/hist_intel3_narrative_evolution.md"
DEFAULT_INTEL2_PATH = "reports/hist_intel2_taxonomy_weighted_intelligence.json"
DEFAULT_TOP_N = 20
MAX_NARRATIVES = 20
MAX_FACT_ROWS = 7500
MIN_TRANSITION_ABS_DELTA = 0.05
LOW_THRESHOLD = 0.35
HIGH_THRESHOLD = 0.65

DIMENSION_TERMS: OrderedDict[str, tuple[str, ...]] = OrderedDict(
    [
        ("persistence", ("persistence", "persistent", "decay", "cross_window", "durable")),
        ("replay", ("replay", "recurrence", "density", "saturation")),
        ("concentration", ("concentration", "hhi", "share", "dominant", "narrow")),
        ("topology", ("topology", "coherence", "stability", "fragmentation", "morphology", "structural")),
        ("fragility", ("fragility", "fragile", "instability", "failed", "weak", "failure")),
    ]
)

DIMENSION_FACT_TYPES: OrderedDict[str, tuple[str, ...]] = OrderedDict(
    [
        ("persistence", ("persistence", "decay")),
        ("replay", ("replay", "recurrence")),
        ("concentration", ("concentration",)),
        ("topology", ("topology", "morphology", "structural")),
        ("fragility", ("fragility", "instability")),
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


def _text(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return "_".join(_text(value).lower().replace("-", "_").split())


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Mapping):
        for key in ("metric_value", "value", "score", "share", "density", "ratio", "persistence_score", "fragility_score", "drift_score"):
            found = _number(value.get(key))
            if found is not None:
                return found
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb") or row.get("payload") or {}
    return payload if isinstance(payload, Mapping) else {}


def _entity_name(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    for key in ("entity_id", "dimension", "structure", "sector", "subsector", "symbol", "group", "name"):
        value = row.get(key) if key in row else payload.get(key)
        if _text(value):
            return _norm(value)
    return _norm(row.get("metric_name") or "unknown")


def _window(row: Mapping[str, Any]) -> int | None:
    payload = _payload(row)
    for key in ("window_days", "window_trading_days", "window", "lookback_days"):
        value = row.get(key) if key in row else payload.get(key)
        number = _number(value)
        if number is not None:
            return int(number)
    return None


def _metric_value(row: Mapping[str, Any]) -> float | None:
    payload = _payload(row)
    for key in ("metric_value", "value", "score", "share", "density", "ratio"):
        value = row.get(key) if key in row else payload.get(key)
        number = _number(value)
        if number is not None:
            return number
    return None


def _evidence_count(row: Mapping[str, Any]) -> int:
    value = row.get("evidence_count") or row.get("evidence") or _payload(row).get("evidence_count")
    number = _number(value)
    return max(1, int(number)) if number is not None else 1


def _confidence_points(label: str | None) -> float:
    return {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4, "INSUFFICIENT": 0.1}.get(_text(label).upper(), 0.4)


def _fact_text(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    parts = [row.get("fact_type"), row.get("entity_type"), row.get("entity_id"), row.get("metric_name"), row.get("source_phase")]
    for key in ("label", "description", "narrative", "finding", "summary", "source_key"):
        parts.append(payload.get(key))
    return _norm(" ".join(_text(part) for part in parts if part is not None))


def _dimension(row: Mapping[str, Any]) -> str | None:
    text = _fact_text(row)
    fact_type = _norm(row.get("fact_type"))
    metric = _norm(row.get("metric_name"))
    haystack = f"{fact_type} {metric} {text}"
    matches: list[str] = []
    for dimension, terms in DIMENSION_FACT_TYPES.items():
        if any(term in fact_type for term in terms):
            matches.append(dimension)
    for dimension, terms in DIMENSION_TERMS.items():
        if any(term in haystack for term in terms):
            matches.append(dimension)
    if not matches:
        return None
    return sorted(set(matches), key=lambda item: list(DIMENSION_TERMS).index(item))[0]


def _source_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _stable_id(parts: Sequence[Any]) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return f"histintel3_{sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def _load_local_facts(path: str | Path | None) -> tuple[list[Mapping[str, Any]], OrderedDict[str, Any]]:
    if not path:
        return [], OrderedDict([("path", None), ("status", "not_requested")])
    fact_path = Path(path)
    if not fact_path.exists():
        return [], OrderedDict([("path", fact_path.as_posix()), ("status", "missing")])
    payload = json.loads(fact_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)], OrderedDict([("path", fact_path.as_posix()), ("status", "loaded"), ("row_count", len(payload))])
    if isinstance(payload, Mapping) and isinstance(payload.get("expanded_facts"), list):
        rows = payload["expanded_facts"]
        return [row for row in rows if isinstance(row, Mapping)], OrderedDict([("path", fact_path.as_posix()), ("status", "loaded"), ("row_count", len(rows))])
    raise ValueError("local facts input must be a JSON list or an object with expanded_facts")


def _load_intel2_context(path: str | Path | None) -> OrderedDict[str, Any]:
    if not path:
        return OrderedDict([("path", None), ("status", "not_requested")])
    intel_path = Path(path)
    if not intel_path.exists():
        return OrderedDict([("path", intel_path.as_posix()), ("status", "missing")])
    payload = json.loads(intel_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        return OrderedDict([("path", intel_path.as_posix()), ("status", "ignored_non_object")])
    return OrderedDict(
        [
            ("path", intel_path.as_posix()),
            ("status", "loaded"),
            ("phase_id", payload.get("phase_id")),
            ("source_digest", payload.get("source_digest")),
            ("taxonomy_tier_counts", payload.get("taxonomy_tier_counts") or {}),
        ]
    )


def _classify_rows(facts: Iterable[Mapping[str, Any]], max_fact_rows: int) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    for index, row in enumerate(facts):
        if index >= max(0, min(int(max_fact_rows), MAX_FACT_ROWS)):
            break
        if not isinstance(row, Mapping):
            continue
        dimension = _dimension(row)
        value = _metric_value(row)
        window = _window(row)
        if dimension is None or value is None or window is None:
            continue
        taxonomy = taxonomy_for_fact(row)
        if taxonomy["tier"] == "C":
            continue
        confidence_label = _text(row.get("confidence_label") or row.get("confidence") or _payload(row).get("confidence_label")).upper() or "LOW"
        if confidence_label not in CONFIDENCE_LABELS:
            confidence_label = "LOW"
        rows.append(
            OrderedDict(
                [
                    ("index", index),
                    ("fact_id", row.get("fact_id")),
                    ("source_phase", row.get("source_phase")),
                    ("fact_type", _norm(row.get("fact_type")) or "unspecified_fact"),
                    ("entity_type", _norm(row.get("entity_type")) or "fact_entity"),
                    ("entity_id", _entity_name(row)),
                    ("metric_name", _norm(row.get("metric_name"))),
                    ("dimension", dimension),
                    ("window_days", window),
                    ("metric_value", _round(value)),
                    ("evidence_count", _evidence_count(row)),
                    ("confidence_label", confidence_label),
                    ("taxonomy_tier", taxonomy["tier"]),
                    ("taxonomy_weight", taxonomy["weight"]),
                ]
            )
        )
    return rows


def _state_for(dimension: str, value: float) -> str:
    if dimension == "persistence":
        return "Persistent" if value >= HIGH_THRESHOLD else "Low Persistence" if value <= LOW_THRESHOLD else "Moderate Persistence"
    if dimension == "replay":
        return "High Replay" if value >= HIGH_THRESHOLD else "Low Replay" if value <= LOW_THRESHOLD else "Moderate Replay"
    if dimension == "concentration":
        return "Concentrated" if value >= HIGH_THRESHOLD else "Broad Participation" if value <= LOW_THRESHOLD else "Mixed Participation"
    if dimension == "topology":
        return "Coherent" if value >= HIGH_THRESHOLD else "Fragmented" if value <= LOW_THRESHOLD else "Mixed Topology"
    if dimension == "fragility":
        return "Fragile" if value >= HIGH_THRESHOLD else "Resilient" if value <= LOW_THRESHOLD else "Moderate Fragility"
    return "Observed"


def _narrative_type(dimension: str, delta: float) -> str:
    if dimension == "persistence":
        return "Persistence Expansion" if delta > 0 else "Persistence Decay"
    if dimension == "replay":
        return "Replay Intensification" if delta > 0 else "Replay Dissipation"
    if dimension == "concentration":
        return "Concentration Expansion" if delta > 0 else "Concentration Relaxation"
    if dimension == "topology":
        return "Topology Stabilization" if delta > 0 else "Topology Fragmentation"
    if dimension == "fragility":
        return "Fragility Escalation" if delta > 0 else "Fragility Recovery"
    return "Narrative Evolution"


def _transition_label(starting_state: str, ending_state: str) -> str | None:
    if starting_state == ending_state:
        return None
    supported = {
        ("Mixed Participation", "Concentrated"): "Stable → Concentrated",
        ("Broad Participation", "Concentrated"): "Broad Participation → Narrow Participation",
        ("Coherent", "Fragmented"): "Coherent → Fragmented",
        ("Mixed Topology", "Fragmented"): "Stable → Fragmented",
        ("Persistent", "Moderate Persistence"): "Persistent → Decaying",
        ("Persistent", "Low Persistence"): "Persistent → Decaying",
        ("Low Replay", "High Replay"): "Low Replay → High Replay",
        ("Low Replay", "Moderate Replay"): "Low Replay → High Replay",
    }
    return supported.get((starting_state, ending_state)) or f"{starting_state} → {ending_state}"


def _confidence_label(fact_count: int, window_count: int, confidence_points: float) -> str:
    if fact_count <= 0:
        return "INSUFFICIENT"
    if fact_count >= 2 and window_count >= 2 and confidence_points >= 0.75:
        return "HIGH"
    if (fact_count >= 2 and window_count >= 2) or confidence_points >= 0.55:
        return "MEDIUM"
    return "LOW"


def _score(*, taxonomy_weight: float, fact_count: int, window_count: int, recurrence_count: int, persistence: float, confidence_points: float, delta: float) -> float:
    support = min(1.0, min(fact_count, 8) * 0.08 + min(window_count, 5) * 0.12 + min(recurrence_count, 5) * 0.06)
    movement = min(1.0, abs(delta))
    raw = taxonomy_weight * (0.30 * support + 0.25 * persistence + 0.25 * confidence_points + 0.20 * movement)
    return round(raw, 6)


def _base_narrative(
    *,
    narrative_type: str,
    dimension: str,
    entity_id: str,
    group: Sequence[Mapping[str, Any]],
    windows: Sequence[int],
    starting_state: str,
    ending_state: str,
    transition_label: str | None,
    start_value: float,
    end_value: float,
    delta: float,
) -> OrderedDict[str, Any]:
    fact_count = sum(int(row["evidence_count"]) for row in group)
    confidence_points = sum(_confidence_points(str(row["confidence_label"])) for row in group) / len(group)
    taxonomy_weight = max(float(row["taxonomy_weight"]) for row in group)
    score = _score(
        taxonomy_weight=taxonomy_weight,
        fact_count=fact_count,
        window_count=len(windows),
        recurrence_count=len(group),
        persistence=min(1.0, len(windows) / 5.0),
        confidence_points=confidence_points,
        delta=delta,
    )
    return OrderedDict(
        [
            ("narrative_id", _stable_id([narrative_type, dimension, entity_id, starting_state, ending_state])),
            ("narrative_type", narrative_type),
            ("dimension", dimension),
            ("starting_state", starting_state),
            ("ending_state", ending_state),
            ("transition_label", transition_label),
            ("supporting_entities", [entity_id]),
            ("supporting_fact_count", fact_count),
            ("supporting_windows", list(windows)),
            ("confidence_label", _confidence_label(fact_count, len(windows), confidence_points)),
            ("narrative_score", score),
            ("taxonomy_weight", taxonomy_weight),
            ("start_value", _round(start_value)),
            ("end_value", _round(end_value)),
            ("delta", _round(delta)),
            ("source_phases", sorted({_text(row.get("source_phase")) for row in group if _text(row.get("source_phase"))})),
        ]
    )


def _dedupe_narratives(rows: Sequence[OrderedDict[str, Any]]) -> list[OrderedDict[str, Any]]:
    selected: OrderedDict[tuple[str, str, str, str, str], OrderedDict[str, Any]] = OrderedDict()
    for row in sorted(rows, key=lambda item: (-float(item["narrative_score"]), str(item["narrative_type"]), str(item["supporting_entities"][0]), str(item["narrative_id"]))):
        key = (
            str(row.get("dimension")),
            str((row.get("supporting_entities") or [""])[0]),
            str(row.get("starting_state")),
            str(row.get("ending_state")),
            str(row.get("narrative_type")),
        )
        selected.setdefault(key, row)
    return list(selected.values())


def _build_narrative_sets(rows: Sequence[Mapping[str, Any]]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], OrderedDict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["dimension"]), str(row["entity_id"]))].append(row)

    transitions: list[OrderedDict[str, Any]] = []
    stable: list[OrderedDict[str, Any]] = []
    suppressed_same_state: list[OrderedDict[str, Any]] = []
    rejected_insufficient_fact_count = 0
    rejected_insufficient_window_count = 0
    rejected_same_state_count = 0

    for (dimension, entity_id), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        windows = sorted({int(row["window_days"]) for row in group})
        if len(group) < 2:
            rejected_insufficient_fact_count += 1
            continue
        if len(windows) < 2:
            rejected_insufficient_window_count += 1
            continue

        by_window: OrderedDict[int, list[Mapping[str, Any]]] = OrderedDict((window, []) for window in windows)
        for row in sorted(group, key=lambda item: (int(item["window_days"]), int(item["index"]))):
            by_window[int(row["window_days"])].append(row)
        start_window = windows[0]
        end_window = windows[-1]
        start_value = sum(float(row["metric_value"]) for row in by_window[start_window]) / len(by_window[start_window])
        end_value = sum(float(row["metric_value"]) for row in by_window[end_window]) / len(by_window[end_window])
        delta = end_value - start_value
        starting_state = _state_for(dimension, start_value)
        ending_state = _state_for(dimension, end_value)

        if starting_state != ending_state:
            narrative_type = _narrative_type(dimension, delta)
            transitions.append(
                _base_narrative(
                    narrative_type=narrative_type,
                    dimension=dimension,
                    entity_id=entity_id,
                    group=group,
                    windows=windows,
                    starting_state=starting_state,
                    ending_state=ending_state,
                    transition_label=_transition_label(starting_state, ending_state),
                    start_value=start_value,
                    end_value=end_value,
                    delta=delta,
                )
            )
            continue

        rejected_same_state_count += 1
        if abs(delta) < MIN_TRANSITION_ABS_DELTA:
            stable_row = _base_narrative(
                narrative_type="Stable Long-Term Narrative",
                dimension=dimension,
                entity_id=entity_id,
                group=group,
                windows=windows,
                starting_state=starting_state,
                ending_state=ending_state,
                transition_label=None,
                start_value=start_value,
                end_value=end_value,
                delta=delta,
            )
            stable_row["average_value"] = _round(sum(float(row["metric_value"]) for row in group) / len(group))
            stable_row["value_spread"] = _round(max(float(row["metric_value"]) for row in group) - min(float(row["metric_value"]) for row in group))
            stable.append(stable_row)
        else:
            suppressed = _base_narrative(
                narrative_type="Suppressed Same-State Evolution",
                dimension=dimension,
                entity_id=entity_id,
                group=group,
                windows=windows,
                starting_state=starting_state,
                ending_state=ending_state,
                transition_label=None,
                start_value=start_value,
                end_value=end_value,
                delta=delta,
            )
            suppressed["rejection_reason"] = "same_state_magnitude_change"
            suppressed_same_state.append(suppressed)

    transitions = _dedupe_narratives(transitions)
    stable = _dedupe_narratives(stable)
    suppressed_same_state = _dedupe_narratives(suppressed_same_state)
    candidate_transitions_found = len(grouped)
    candidate_transitions_emitted = len(transitions)
    diagnostics = OrderedDict(
        [
            ("candidate_transitions_found", candidate_transitions_found),
            ("candidate_transitions_emitted", candidate_transitions_emitted),
            ("candidate_transitions_rejected", max(0, candidate_transitions_found - candidate_transitions_emitted)),
            ("rejected_same_state_count", rejected_same_state_count),
            ("rejected_insufficient_window_count", rejected_insufficient_window_count),
            ("rejected_insufficient_fact_count", rejected_insufficient_fact_count),
            ("suppressed_same_state_examples", suppressed_same_state[:5]),
        ]
    )
    return transitions, stable, suppressed_same_state, diagnostics


def _section(rows: Sequence[Mapping[str, Any]], dimension: str) -> list[Mapping[str, Any]]:
    return [row for row in rows if row.get("dimension") == dimension][:MAX_NARRATIVES]


def _summary(narratives: Sequence[Mapping[str, Any]], stable: Sequence[Mapping[str, Any]], suppressed_same_state: Sequence[Mapping[str, Any]], diagnostics: Mapping[str, Any]) -> list[str]:
    if not narratives and not stable and not suppressed_same_state:
        return ["No supported multi-window narrative transitions were detected from available local fact rows."]
    counts = Counter(str(row.get("narrative_type")) for row in narratives)
    lines = [
        f"Detected {len(narratives)} true state transition(s), {len(stable)} stable long-term narrative(s), and {len(suppressed_same_state)} suppressed same-state movement(s) from local multi-window evidence.",
        f"Candidate transition review: found={diagnostics.get('candidate_transitions_found')} emitted={diagnostics.get('candidate_transitions_emitted')} rejected={diagnostics.get('candidate_transitions_rejected')}.",
    ]
    for narrative_type, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]:
        lines.append(f"{narrative_type}: {count} true transition(s).")
    return lines


def build_narrative_evolution_report(
    *,
    observation_facts: Iterable[Mapping[str, Any]] | None = None,
    local_facts_path: str | Path | None = DEFAULT_EXPANDED_FACTS_PATH,
    intel2_path: str | Path | None = DEFAULT_INTEL2_PATH,
    top_n: int = DEFAULT_TOP_N,
    max_fact_rows: int = MAX_FACT_ROWS,
) -> OrderedDict[str, Any]:
    supplied = [row for row in (observation_facts or []) if isinstance(row, Mapping)]
    loaded_rows, input_status = _load_local_facts(local_facts_path)
    intel2_status = _load_intel2_context(intel2_path)
    all_rows = (supplied + loaded_rows)[: max(0, min(int(max_fact_rows), MAX_FACT_ROWS))]
    classified = _classify_rows(all_rows, max_fact_rows)
    limit = max(0, min(int(top_n), MAX_NARRATIVES))
    transitions_all, stable_all, suppressed_all, diagnostics = _build_narrative_sets(classified)
    transitions = transitions_all[:limit]
    stable = stable_all[:limit]
    suppressed_same_state = suppressed_all[:limit]
    transition_candidates = [
        row
        for row in transitions
        if row.get("starting_state") != row.get("ending_state")
        and row.get("transition_label") is not None
        and int(row.get("supporting_fact_count") or 0) >= 2
        and len(row.get("supporting_windows") or []) >= 2
    ][:limit]
    narrative_types = sorted({str(row.get("narrative_type")) for row in transitions + stable})
    findings: OrderedDict[str, Any] = OrderedDict(
        [
            ("executive_narrative_summary", _summary(transitions, stable, suppressed_same_state, diagnostics)),
            ("major_narrative_evolutions", transitions),
            ("regime_transition_candidates", transition_candidates),
            ("persistence_evolution", _section(transitions, "persistence")),
            ("replay_evolution", _section(transitions, "replay")),
            ("concentration_evolution", _section(transitions, "concentration")),
            ("topology_evolution", _section(transitions, "topology")),
            ("fragility_evolution", _section(transitions, "fragility")),
            ("stable_long_term_narratives", stable),
            ("suppressed_same_state_evolutions", suppressed_same_state),
        ]
    )
    limitations = [
        "Analysis is local-only and uses available historical fact artifacts or supplied fact rows; it does not refresh or ingest external data.",
        "Major narrative evolutions require a true starting-state to ending-state change across at least two facts and two windows.",
        "Same-state magnitude changes are suppressed from major transitions and reported separately as diagnostics.",
    ]
    if not classified:
        limitations.append("No eligible ecosystem fact rows with numeric values and windows were available after taxonomy filtering.")
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("phase_id", PHASE_ID),
            ("phase_name", PHASE_NAME),
            ("status", "ok" if transitions or stable or suppressed_same_state else "limited"),
            ("top_n", limit),
            ("fact_rows_supplied", len(supplied)),
            ("fact_rows_loaded", len(loaded_rows)),
            ("fact_rows_considered", len(all_rows)),
            ("eligible_ecosystem_fact_rows", len(classified)),
            ("local_input_status", input_status),
            ("hist_intel2_context_status", intel2_status),
            ("source_digest", _source_digest({"facts": all_rows, "input_status": input_status, "intel2_status": intel2_status})),
            ("governance_certification", GOVERNANCE_CERTIFICATION.copy()),
            ("transition_diagnostics", diagnostics),
            ("narrative_types_generated", narrative_types),
            ("findings", findings),
            ("limitations", limitations),
        ]
    )

def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# HIST-INTEL-3 Narrative Evolution & Regime Transition Mapping\n\n",
        "## Objective\nMap how the ecosystem evolved across historical windows using local, taxonomy-weighted facts.\n\n",
        "## Governance certification\n",
    ]
    for key, value in (report.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {str(value).lower()}\n")
    findings = report.get("findings") or {}
    lines.append("\n## Transition Diagnostics\n")
    for key, value in (report.get("transition_diagnostics") or {}).items():
        if key == "suppressed_same_state_examples":
            continue
        lines.append(f"- {key}: {value}\n")
    sections = [
        ("Executive Narrative Summary", "executive_narrative_summary"),
        ("Major Narrative Evolutions", "major_narrative_evolutions"),
        ("Regime Transition Candidates", "regime_transition_candidates"),
        ("Persistence Evolution", "persistence_evolution"),
        ("Replay Evolution", "replay_evolution"),
        ("Concentration Evolution", "concentration_evolution"),
        ("Topology Evolution", "topology_evolution"),
        ("Fragility Evolution", "fragility_evolution"),
        ("Stable Long-Term Narratives", "stable_long_term_narratives"),
        ("Suppressed Same-State Evolutions", "suppressed_same_state_evolutions"),
    ]
    for title, key in sections:
        lines.append(f"\n## {title}\n")
        rows = findings.get(key) or []
        if not rows:
            lines.append("- No supported findings from available local evidence.\n")
            continue
        for row in rows:
            if isinstance(row, str):
                lines.append(f"- {row}\n")
            elif isinstance(row, Mapping):
                lines.append(
                    f"- {row.get('narrative_id')}: {row.get('narrative_type')} | {row.get('starting_state')} → {row.get('ending_state')} | entities={','.join(row.get('supporting_entities') or [])} | windows={row.get('supporting_windows')} | facts={row.get('supporting_fact_count')} | confidence={row.get('confidence_label')} | score={row.get('narrative_score')}\n"
                )
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


def run_hist_intel3(
    *,
    observation_facts: Iterable[Mapping[str, Any]] | None = None,
    local_facts_path: str | Path | None = DEFAULT_EXPANDED_FACTS_PATH,
    intel2_path: str | Path | None = DEFAULT_INTEL2_PATH,
    top_n: int = DEFAULT_TOP_N,
    json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH,
    markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH,
) -> OrderedDict[str, Any]:
    report = build_narrative_evolution_report(observation_facts=observation_facts, local_facts_path=local_facts_path, intel2_path=intel2_path, top_n=top_n)
    paths = write_reports(report, json_report_path=json_report_path, markdown_report_path=markdown_report_path)
    report["output_paths"] = paths
    return report
