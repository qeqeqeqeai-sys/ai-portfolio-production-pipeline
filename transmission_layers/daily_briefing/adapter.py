"""Thin Daily Briefing adapter over existing SEFI intelligence outputs.

This module is intentionally read-only and presentation-only. It normalizes existing
OBS-QUERY / HIST-INTEL style JSON artifacts into a compact analyst briefing view
model without creating facts, writing data, or generating new intelligence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_ARTIFACT_PATHS: tuple[str, ...] = (
    "artifacts/obs_query4_ecosystem_briefing.json",
    "artifacts/obs_query4_investigation_queue.json",
    "artifacts/obs_query3_historical_live_comparison.json",
    "artifacts/hist_intel4_ecosystem_intelligence_synthesis.json",
    "outputs/obs_query4_ecosystem_briefing.json",
    "outputs/obs_query4_investigation_queue.json",
    "outputs/obs_query3_historical_live_comparison.json",
    "reports/hist_intel4_ecosystem_intelligence_synthesis.json",
)

INVESTIGATION_TYPES = {"anomaly", "emergence", "structural_change", "continuity", "validation"}
PRIORITIES = {"critical", "high", "medium", "low"}
SECTION_CAPS = {
    "major_developments": 5,
    "investigation_candidates": 7,
    "historical_live_deviation_highlights": 5,
    "emerging_themes": 5,
    "persistence_watchlist": 5,
    "evolution_highlights": 5,
}
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_PRIORITY_STRENGTH = {"critical": 3, "high": 2, "medium": 1, "low": 0}
_CONFIDENCE_STRENGTH = {"high": 2, "medium": 1, "low": 0}
_TYPE_BY_SOURCE = {
    "live_only_anomaly": "anomaly",
    "historical_live_deviation": "structural_change",
    "persistent_weakening_live": "continuity",
    "historically_weak_strengthening_live": "emergence",
}
_QUESTIONS_BY_TYPE = {
    "anomaly": [
        "What live observations make this item different from historical context?",
        "Which evidence IDs should be reviewed before analyst escalation?",
    ],
    "emergence": [
        "Is the live strengthening visible across more than one source phase?",
        "Which historical weak-state comparisons best explain the change?",
    ],
    "structural_change": [
        "Which historical and live facts account for the deviation?",
        "Does the change persist across related structures or remain isolated?",
    ],
    "continuity": [
        "Which persistent structure is weakening relative to live observations?",
        "Is the current state still consistent with the historical pattern?",
    ],
    "validation": [
        "Which supporting facts require validation before interpretation?",
        "Are source phases and evidence IDs sufficient for analyst review?",
    ],
}

LIFECYCLE_STATES = {"new", "developing", "stable", "weakening", "resolved"}
NARRATIVE_ARCHETYPES = {"continuation", "acceleration", "emergence", "breakdown", "transition"}
EVOLUTION_DIRECTIONS = {"rising", "stable", "falling", "reappearing", "unknown"}
_LIFECYCLE_STRENGTH = {"resolved": 0, "weakening": 1, "stable": 2, "new": 3, "developing": 4}


def _signal_values(item: Mapping[str, Any], *, section_name: str | None = None) -> set[str]:
    values: set[str] = set()
    for key in ("classification", "queue_source", "source_comparison_type", "source_query_type", "source_type"):
        value = item.get(key)
        if value is not None:
            values.add(str(value).strip().lower())
    if section_name:
        values.add(section_name.strip().lower())
    return {value for value in values if value}


def _has_signal(signals: set[str], *needles: str) -> bool:
    return any(needle in signal for signal in signals for needle in needles)


def infer_lifecycle_state(item: Mapping[str, Any], *, section_name: str | None = None) -> str:
    """Infer a deterministic story lifecycle state from existing artifact fields only."""

    signals = _signal_values(item, section_name=section_name)
    if _has_signal(signals, "resolved", "closed", "normalized", "normalised"):
        return "resolved"
    if _has_signal(signals, "persistent_weakening_live", "live_weaker_than_historical", "weakening live"):
        return "weakening"
    if _has_signal(signals, "historically_weak_strengthening_live"):
        return "developing"
    if _has_signal(signals, "live_deviates_from_historical", "baseline_deviation", "historical_live_deviation"):
        return "developing"
    if _has_signal(signals, "live_only_anomaly", "live_only"):
        return "new"
    if _has_signal(signals, "persistent", "recurring", "persisted"):
        return "stable"
    if item.get("delta") not in (None, ""):
        return "developing"
    if len(_fact_ids(item)) >= 2 or len(_evidence_ids(item)) >= 2:
        return "stable"
    return "new"


def infer_narrative_archetype(item: Mapping[str, Any], *, section_name: str | None = None) -> str:
    """Infer a deterministic narrative archetype from existing artifact fields only."""

    signals = _signal_values(item, section_name=section_name)
    if _has_signal(signals, "persistent_weakening_live", "live_weaker_than_historical", "weakening live"):
        return "breakdown"
    if _has_signal(signals, "historically_weak_strengthening_live"):
        return "acceleration"
    if _has_signal(signals, "live_deviates_from_historical", "baseline_deviation", "historical_live_deviation"):
        return "transition"
    if _has_signal(signals, "live_only_anomaly", "live_only"):
        return "emergence"
    if _has_signal(signals, "persistent", "recurring", "persisted"):
        return "continuation"
    if item.get("delta") not in (None, ""):
        return "transition"
    if len(_fact_ids(item)) >= 2 or len(_evidence_ids(item)) >= 2:
        return "continuation"
    return "emergence"


def continuity_explanation(item: Mapping[str, Any], *, section_name: str | None = None) -> str:
    """Return a short read-only explanation for the inferred narrative continuity."""

    lifecycle_state = infer_lifecycle_state(item, section_name=section_name)
    archetype = infer_narrative_archetype(item, section_name=section_name)
    source = _source_label(item)
    classification = _clean_text(item.get("classification"), default="unspecified classification")
    fact_count = len(_fact_ids(item))
    evidence_count = len(_evidence_ids(item))
    metric_value = item.get("ranking_metric", {}).get("value") if isinstance(item.get("ranking_metric"), Mapping) else None
    metric_clause = f"; ranking metric={metric_value}" if metric_value is not None else ""
    delta_clause = f"; delta={item.get('delta')}" if item.get("delta") not in (None, "") else ""
    section_clause = f" in {section_name}" if section_name else ""
    return (
        f"Marked {lifecycle_state}/{archetype} from existing {source}{section_clause} signals "
        f"({classification}) with {fact_count} fact IDs and {evidence_count} evidence IDs"
        f"{metric_clause}{delta_clause}."
    )


@dataclass(frozen=True)
class BriefingLoadResult:
    """Result wrapper for a Daily Briefing load attempt."""

    briefing: dict[str, Any]
    inspected_paths: list[str]
    loaded_paths: list[str]
    missing_paths: list[str]
    warnings: list[str]


def _clean_text(value: Any, default: str = "Not available") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _normalize_date(value: str | date | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date().isoformat()
    except ValueError:
        return text[:10]


def _metric_value(item: Mapping[str, Any]) -> float:
    metric = item.get("ranking_metric") or {}
    value = metric.get("value") if isinstance(metric, Mapping) else None
    try:
        return abs(float(value)) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _evidence_ids(item: Mapping[str, Any]) -> list[str]:
    return sorted({str(value) for value in item.get("supporting_evidence_ids") or [] if str(value)})


def _fact_ids(item: Mapping[str, Any]) -> list[str]:
    ids = [*(item.get("supporting_fact_ids") or [])]
    ids.extend(item.get("historical_supporting_fact_ids") or [])
    ids.extend(item.get("live_supporting_fact_ids") or [])
    return sorted({str(value) for value in ids if str(value)})


def _confidence_label(item: Mapping[str, Any]) -> str:
    evidence_count = len(_evidence_ids(item))
    fact_count = len(_fact_ids(item))
    if evidence_count >= 3 or fact_count >= 4:
        return "high"
    if evidence_count >= 1 or fact_count >= 2:
        return "medium"
    return "low"


def _metric_context(value: Any) -> str:
    if not isinstance(value, Mapping) or not value:
        return "Historical metric context is available only when supplied by the source artifact."
    parts = []
    for key in ("representative_value", "fact_count", "numeric_values"):
        if key in value and value.get(key) not in (None, [], ""):
            parts.append(f"{key}={value.get(key)}")
    return "; ".join(parts) if parts else "Historical metric context is available only when supplied by the source artifact."


def _source_label(item: Mapping[str, Any]) -> str:
    return _clean_text(
        item.get("queue_source")
        or item.get("source_comparison_type")
        or item.get("source_query_type")
        or item.get("source_type"),
        default="existing_intelligence_output",
    )


def _section_map(payloads: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    sections: dict[str, list[Mapping[str, Any]]] = {}
    for payload in payloads:
        for section in payload.get("sections") or []:
            if not isinstance(section, Mapping):
                continue
            name = _clean_text(section.get("section_name"), default="Unnamed Section")
            items = [item for item in section.get("items") or [] if isinstance(item, Mapping)]
            sections.setdefault(name, []).extend(items)
    return sections


def _payload_intrinsic_date(payload: Mapping[str, Any], fallback: str | date | datetime | None = None) -> str:
    params = payload.get("query_parameters") if isinstance(payload.get("query_parameters"), Mapping) else {}
    return _normalize_date(params.get("snapshot_date") or payload.get("briefing_date") or payload.get("run_date") or fallback) or "not dated"


def _dated_section_rows(payloads: Sequence[Mapping[str, Any]], selected_date: str | date | datetime | None = None) -> list[tuple[str, str, Mapping[str, Any]]]:
    rows: list[tuple[str, str, Mapping[str, Any]]] = []
    for payload in payloads:
        payload_date = _payload_intrinsic_date(payload, selected_date)
        for section in payload.get("sections") or []:
            if not isinstance(section, Mapping):
                continue
            section_name = _clean_text(section.get("section_name"), default="Unnamed Section")
            for item in section.get("items") or []:
                if isinstance(item, Mapping):
                    rows.append((payload_date, section_name, item))
    return rows


def _date_sort_key(value: str) -> tuple[int, str]:
    normalized = _normalize_date(value)
    if normalized and re.match(r"^\d{4}-\d{2}-\d{2}$", normalized):
        return (0, normalized)
    return (1, str(value))


def _history_source_rows(payloads: Sequence[Mapping[str, Any]], selected_date: str | date | datetime | None = None) -> list[tuple[str, str, Mapping[str, Any]]]:
    rows: list[tuple[str, str, Mapping[str, Any]]] = []
    for row_date, section_name, item in _dated_section_rows(payloads, selected_date):
        if not _has_meaningful_identifier(item) or _is_evidence_only(item):
            continue
        if _is_internal_artifact(item, section_name=section_name):
            continue
        rows.append((row_date, section_name, item))
    return rows


def _priority_seen(item: Mapping[str, Any]) -> str:
    priority = item.get("priority")
    if str(priority) in PRIORITIES:
        return str(priority)
    return _raw_priority(item)


def _highest_priority(priorities: Sequence[str]) -> str:
    if not priorities:
        return "not available"
    return sorted(priorities, key=lambda value: _PRIORITY_ORDER.get(str(value), 99))[0]


def _consecutive_appearances(dates: Sequence[str]) -> int:
    ordered = sorted({_normalize_date(value) or str(value) for value in dates}, key=_date_sort_key)
    if not ordered:
        return 0
    if not all(re.match(r"^\d{4}-\d{2}-\d{2}$", value) for value in ordered):
        last = ordered[-1]
        count = 0
        for value in reversed(ordered):
            if value == last:
                count += 1
            else:
                break
        return count
    parsed = [datetime.strptime(value, "%Y-%m-%d").date() for value in ordered]
    count = 1
    for previous, current in zip(reversed(parsed[:-1]), reversed(parsed[1:])):
        if (current - previous).days == 1:
            count += 1
        else:
            break
    return count


def build_story_histories(
    payloads: Sequence[Mapping[str, Any]],
    *,
    selected_date: str | date | datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Build deterministic cross-day story histories from existing briefing artifacts only."""

    grouped: dict[str, list[tuple[str, str, Mapping[str, Any]]]] = {}
    for row_date, section_name, item in _history_source_rows(payloads, selected_date):
        grouped.setdefault(story_key(item, section_name=section_name), []).append((row_date, section_name, item))

    histories: dict[str, dict[str, Any]] = {}
    for key, rows in grouped.items():
        ordered = sorted(
            rows,
            key=lambda row: (
                _date_sort_key(row[0]),
                _normalized_title(row[2].get("identifier") or row[2].get("title")),
                row[1],
                _metric_value(row[2]),
                _support_count(row[2]),
            ),
        )
        dates = [row[0] for row in ordered]
        confidence_trend = [_confidence_label(row[2]) for row in ordered]
        lifecycle_history = [infer_lifecycle_state(row[2], section_name=row[1]) for row in ordered]
        archetype_history = [infer_narrative_archetype(row[2], section_name=row[1]) for row in ordered]
        priorities = [_priority_seen(row[2]) for row in ordered]
        histories[key] = {
            "first_seen": dates[0],
            "last_seen": dates[-1],
            "appearance_count": len(ordered),
            "consecutive_appearances": _consecutive_appearances(dates),
            "highest_priority_seen": _highest_priority(priorities),
            "confidence_trend": confidence_trend,
            "lifecycle_history": lifecycle_history,
            "archetype_history": archetype_history,
            "priority_history": priorities,
            "seen_dates": dates,
        }
    return histories


def evolution_direction(history: Mapping[str, Any]) -> str:
    """Classify deterministic story movement from a story history summary."""

    if int(history.get("appearance_count") or 0) < 2:
        return "unknown"
    priorities = list(history.get("priority_history") or [])
    confidences = list(history.get("confidence_trend") or [])
    lifecycles = list(history.get("lifecycle_history") or [])
    seen_dates = list(history.get("seen_dates") or [])
    if int(history.get("consecutive_appearances") or 0) == 1 and len(set(seen_dates)) > 1:
        return "reappearing"
    previous_priority = _PRIORITY_STRENGTH.get(str(priorities[-2]), 0) if len(priorities) >= 2 else 0
    current_priority = _PRIORITY_STRENGTH.get(str(priorities[-1]), 0) if priorities else 0
    previous_confidence = _CONFIDENCE_STRENGTH.get(str(confidences[-2]), 0) if len(confidences) >= 2 else 0
    current_confidence = _CONFIDENCE_STRENGTH.get(str(confidences[-1]), 0) if confidences else 0
    previous_lifecycle = _LIFECYCLE_STRENGTH.get(str(lifecycles[-2]), 0) if len(lifecycles) >= 2 else 0
    current_lifecycle = _LIFECYCLE_STRENGTH.get(str(lifecycles[-1]), 0) if lifecycles else 0
    if current_priority > previous_priority or current_confidence > previous_confidence or current_lifecycle > previous_lifecycle:
        return "rising"
    if current_priority < previous_priority or current_lifecycle < previous_lifecycle:
        return "falling"
    return "stable"


def why_now(history: Mapping[str, Any]) -> str:
    direction = evolution_direction(history)
    if direction == "unknown":
        return "insufficient prior history for cross-day comparison"
    if direction == "reappearing":
        return "first appearance after absence"
    priorities = list(history.get("priority_history") or [])
    confidences = list(history.get("confidence_trend") or [])
    if len(priorities) >= 2 and _PRIORITY_STRENGTH.get(str(priorities[-1]), 0) > _PRIORITY_STRENGTH.get(str(priorities[-2]), 0):
        return "priority increased versus previous appearance"
    if len(confidences) >= 2 and _CONFIDENCE_STRENGTH.get(str(confidences[-1]), 0) > _CONFIDENCE_STRENGTH.get(str(confidences[-2]), 0):
        return "confidence improved versus previous appearance"
    if direction == "falling":
        return "priority or lifecycle weakened versus previous appearance"
    if direction == "stable":
        return "no material change detected"
    return "persistence continuing"


def _visible_history(history: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "first_seen": history.get("first_seen"),
        "last_seen": history.get("last_seen"),
        "appearance_count": history.get("appearance_count", 0),
        "consecutive_appearances": history.get("consecutive_appearances", 0),
        "highest_priority_seen": history.get("highest_priority_seen", "not available"),
    }


def _empty_suppression_summary() -> dict[str, int]:
    return {
        "total_candidates_seen": 0,
        "total_items_suppressed": 0,
        "duplicates_suppressed": 0,
        "low_confidence_suppressed": 0,
        "low_priority_suppressed": 0,
        "internal_artifacts_suppressed": 0,
        "final_items_shown": 0,
    }


def _add_suppression_summary(target: dict[str, int], source: Mapping[str, int]) -> None:
    for key in target:
        target[key] += int(source.get(key, 0))


def _normalized_title(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def story_key(item: Mapping[str, Any], *, section_name: str | None = None) -> str:
    """Return a stable deterministic story identity from existing artifact fields."""

    primary = _normalized_title(item.get("identifier") or item.get("title"))
    if primary and primary not in {"not available", "unidentified structure", "untitled item", "none", "null"}:
        return f"story:{primary}"
    lifecycle_state = _normalized_title(item.get("lifecycle_state") or infer_lifecycle_state(item, section_name=section_name))
    archetype = _normalized_title(item.get("narrative_archetype") or infer_narrative_archetype(item, section_name=section_name))
    source = _normalized_title(_source_label(item))
    classification = _normalized_title(item.get("classification"))
    fallback = ":".join(part for part in (classification, lifecycle_state, archetype, source) if part)
    return f"story:{fallback or 'unknown'}"


def _has_meaningful_identifier(item: Mapping[str, Any]) -> bool:
    title = _normalized_title(item.get("identifier") or item.get("title"))
    return bool(title) and title not in {"not available", "unidentified structure", "untitled item", "none", "null"}


def _text_blob(item: Mapping[str, Any], *, section_name: str | None = None) -> str:
    values = [section_name or ""]
    for key in (
        "identifier",
        "title",
        "classification",
        "queue_source",
        "source_comparison_type",
        "source_query_type",
        "source_type",
        "validation_status",
        "artifact_type",
    ):
        value = item.get(key)
        if value is not None:
            values.append(str(value))
    return " ".join(values).lower()


def _is_internal_artifact(item: Mapping[str, Any], *, section_name: str | None = None) -> bool:
    blob = _text_blob(item, section_name=section_name)
    internal_terms = (
        "internal governance",
        "governance",
        "pipeline",
        "validation-only",
        "validation only",
        "schema validation",
        "artifact validation",
        "smoke test",
        "runbook",
        "orchestration",
        "auditability",
        "lineage manifest",
        "operational readiness",
    )
    return any(term in blob for term in internal_terms)


def _is_evidence_only(item: Mapping[str, Any]) -> bool:
    if _clean_text(item.get("classification"), default="") or _metric_value(item) or item.get("delta") not in (None, ""):
        return False
    return bool(_fact_ids(item) or _evidence_ids(item))


def _duplicate_key(item: Mapping[str, Any], *, section_name: str) -> tuple[str, str, str, str]:
    return (
        _normalized_title(item.get("identifier") or item.get("title")),
        infer_lifecycle_state(item, section_name=section_name),
        infer_narrative_archetype(item, section_name=section_name),
        section_name.strip().lower(),
    )


def _support_count(item: Mapping[str, Any]) -> int:
    return len(_fact_ids(item)) + len(_evidence_ids(item))


def _raw_priority(item: Mapping[str, Any]) -> str:
    return _priority_for(item, _type_for(item))


def _strength_key(item: Mapping[str, Any], *, section_name: str, investigation: bool = False) -> tuple[int, int, float, int, str]:
    priority = _raw_priority(item) if investigation else "medium"
    return (
        _PRIORITY_STRENGTH.get(priority, 0),
        _CONFIDENCE_STRENGTH.get(_confidence_label(item), 0),
        _metric_value(item),
        _support_count(item),
        _normalized_title(item.get("identifier") or item.get("title")),
    )


def _better_item(
    current: tuple[Mapping[str, Any], str],
    candidate: tuple[Mapping[str, Any], str],
    *,
    investigation: bool = False,
) -> tuple[Mapping[str, Any], str]:
    current_key = _strength_key(current[0], section_name=current[1], investigation=investigation)
    candidate_key = _strength_key(candidate[0], section_name=candidate[1], investigation=investigation)
    if candidate_key[:-1] > current_key[:-1]:
        return candidate
    if candidate_key[:-1] == current_key[:-1] and candidate_key[-1] < current_key[-1]:
        return candidate
    return current


def _quality_gate_raw_items(
    rows: Sequence[tuple[str, Mapping[str, Any]]],
    *,
    limit: int,
    investigation: bool = False,
) -> tuple[list[tuple[str, Mapping[str, Any]]], dict[str, int]]:
    summary = _empty_suppression_summary()
    summary["total_candidates_seen"] = len(rows)
    usable: list[tuple[str, Mapping[str, Any]]] = []
    for section_name, item in rows:
        if not _has_meaningful_identifier(item) or _is_evidence_only(item):
            summary["total_items_suppressed"] += 1
            continue
        if _is_internal_artifact(item, section_name=section_name):
            summary["internal_artifacts_suppressed"] += 1
            summary["total_items_suppressed"] += 1
            continue
        usable.append((section_name, item))

    collapsed: dict[tuple[str, str, str, str], tuple[Mapping[str, Any], str]] = {}
    for section_name, item in usable:
        key = _duplicate_key(item, section_name=section_name)
        candidate = (item, section_name)
        if key in collapsed:
            summary["duplicates_suppressed"] += 1
            summary["total_items_suppressed"] += 1
            collapsed[key] = _better_item(collapsed[key], candidate, investigation=investigation)
        else:
            collapsed[key] = candidate

    deduped = [(section_name, item) for item, section_name in collapsed.values()]
    has_medium_or_high = any(_confidence_label(item) in {"medium", "high"} for section_name, item in deduped)
    if has_medium_or_high:
        retained: list[tuple[str, Mapping[str, Any]]] = []
        for row in deduped:
            if _confidence_label(row[1]) == "low":
                summary["low_confidence_suppressed"] += 1
                summary["total_items_suppressed"] += 1
            else:
                retained.append(row)
        deduped = retained

    if investigation and any(_raw_priority(item) != "low" for _section_name, item in deduped):
        retained = []
        for row in deduped:
            if _raw_priority(row[1]) == "low":
                summary["low_priority_suppressed"] += 1
                summary["total_items_suppressed"] += 1
            else:
                retained.append(row)
        deduped = retained

    deduped = _sort_summary_rows(deduped)

    overflow = max(0, len(deduped) - limit)
    if overflow:
        summary["total_items_suppressed"] += overflow
    shown = deduped[:limit]
    summary["final_items_shown"] = len(shown)
    return shown, summary


def _make_summary_item(
    item: Mapping[str, Any],
    *,
    section_name: str,
    history: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    identifier = _clean_text(item.get("identifier"), default="Unidentified structure")
    classification = _clean_text(item.get("classification"), default="observed")
    source = _source_label(item)
    metric = item.get("ranking_metric") if isinstance(item.get("ranking_metric"), Mapping) else {}
    metric_name = _clean_text(metric.get("name"), default="ranking metric")
    metric_display = metric.get("value")
    lifecycle_state = infer_lifecycle_state(item, section_name=section_name)
    narrative_archetype = infer_narrative_archetype(item, section_name=section_name)
    key = story_key(item, section_name=section_name)
    history = history or {
        "first_seen": "not available",
        "last_seen": "not available",
        "appearance_count": 1,
        "consecutive_appearances": 1,
        "highest_priority_seen": _priority_seen(item),
        "confidence_trend": [_confidence_label(item)],
        "lifecycle_history": [lifecycle_state],
        "archetype_history": [narrative_archetype],
        "priority_history": [_priority_seen(item)],
        "seen_dates": [],
    }
    what_changed = f"{identifier}: {classification} in {section_name}."
    why_it_matters = f"Source view: {source}; {metric_name}={metric_display if metric_display is not None else 'not available'}."
    return {
        "title": identifier,
        "story_key": key,
        "what_changed": what_changed,
        "why_it_matters": why_it_matters,
        "source_section": section_name,
        "source_view": source,
        "classification": classification,
        "lifecycle_state": lifecycle_state,
        "narrative_archetype": narrative_archetype,
        "continuity_explanation": continuity_explanation(item, section_name=section_name),
        "story_history": _visible_history(history),
        "evolution_direction": evolution_direction(history),
        "why_now": why_now(history),
        "confidence": _confidence_label(item),
        "historical_live_deviation": item.get("delta"),
    }


def _candidate_rows(sections: Mapping[str, list[Mapping[str, Any]]], names: Iterable[str]) -> list[tuple[str, Mapping[str, Any]]]:
    rows: list[tuple[str, Mapping[str, Any]]] = []
    for section_name in names:
        for item in sections.get(section_name, []):
            rows.append((section_name, item))
    return rows


def _sort_summary_rows(rows: Sequence[tuple[str, Mapping[str, Any]]]) -> list[tuple[str, Mapping[str, Any]]]:
    return sorted(rows, key=lambda row: (-_metric_value(row[1]), row[0], _normalized_title(row[1].get("identifier") or row[1].get("title"))))


def _top_items(sections: Mapping[str, list[Mapping[str, Any]]], names: Iterable[str], *, limit: int) -> list[dict[str, Any]]:
    rows, _summary = _quality_gate_raw_items(_sort_summary_rows(_candidate_rows(sections, names)), limit=limit)
    return [_make_summary_item(item, section_name=section_name) for section_name, item in rows]


def _priority_for(item: Mapping[str, Any], investigation_type: str) -> str:
    source = str(item.get("queue_source") or item.get("source_comparison_type") or "")
    value = _metric_value(item)
    if source == "live_only_anomaly":
        return "critical" if value >= 3 else "high"
    if source in {"historical_live_deviation", "baseline_deviation"}:
        return "critical" if value >= 25 else "high"
    if investigation_type in {"continuity", "emergence"}:
        return "high" if value >= 10 else "medium"
    return "medium" if value else "low"


def _type_for(item: Mapping[str, Any]) -> str:
    source = str(item.get("queue_source") or "")
    if source in _TYPE_BY_SOURCE:
        return _TYPE_BY_SOURCE[source]
    classification = str(item.get("classification") or "").lower()
    if "live_only" in classification:
        return "anomaly"
    if "deviat" in classification:
        return "structural_change"
    if "recurr" in classification or "persistent" in classification:
        return "continuity"
    return "validation"


def _investigation_item(
    item: Mapping[str, Any],
    *,
    rank_hint: int,
    section_name: str | None = None,
    history: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    investigation_type = _type_for(item)
    priority = _priority_for(item, investigation_type)
    identifier = _clean_text(item.get("identifier"), default=f"investigation-{rank_hint}")
    classification = _clean_text(item.get("classification"), default="requires analyst review")
    source = _source_label(item)
    facts = _fact_ids(item)
    evidence = _evidence_ids(item)
    lifecycle_state = infer_lifecycle_state(item, section_name=section_name)
    narrative_archetype = infer_narrative_archetype(item, section_name=section_name)
    key = story_key(item, section_name=section_name)
    history = history or {
        "first_seen": "not available",
        "last_seen": "not available",
        "appearance_count": 1,
        "consecutive_appearances": 1,
        "highest_priority_seen": priority,
        "confidence_trend": [_confidence_label(item)],
        "lifecycle_history": [lifecycle_state],
        "archetype_history": [narrative_archetype],
        "priority_history": [priority],
        "seen_dates": [],
    }
    direction = evolution_direction(history)
    why_now_text = why_now(history)
    return {
        "id": f"{source}:{identifier}",
        "story_key": key,
        "rank": rank_hint,
        "title": identifier,
        "investigation_type": investigation_type,
        "priority": priority,
        "lifecycle_state": lifecycle_state,
        "narrative_archetype": narrative_archetype,
        "continuity_explanation": continuity_explanation(item, section_name=section_name),
        "story_history": _visible_history(history),
        "evolution_direction": direction,
        "why_now": why_now_text,
        "why_it_appears": f"{classification} surfaced by {source}.",
        "analyst_value": "Focuses review on an existing SEFI item with historical/live context and bounded evidence references.",
        "recommended_questions": list(_QUESTIONS_BY_TYPE[investigation_type]),
        "confidence": _confidence_label(item),
        "current_state": classification,
        "historical_context": _metric_context(item.get("historical_metric")),
        "similarities": "Review overlapping historical and live supporting facts in the drill-down section.",
        "differences": f"Historical/live deviation: {item.get('delta') if item.get('delta') is not None else 'not available'}.",
        "analyst_significance": "Helps determine whether the existing observation should receive deeper analyst review.",
        "next_questions": list(_QUESTIONS_BY_TYPE[investigation_type]),
        "evidence": {
            "supporting_fact_ids": facts,
            "supporting_evidence_ids": evidence,
            "source_phases": list(item.get("source_phases") or []),
            "historical_supporting_fact_ids": list(item.get("historical_supporting_fact_ids") or []),
            "live_supporting_fact_ids": list(item.get("live_supporting_fact_ids") or []),
        },
        "sort_metric": _metric_value(item),
    }


def rank_investigations(items: Iterable[Mapping[str, Any]], *, limit: int = 7) -> list[dict[str, Any]]:
    """Return deterministic ranked investigation items."""

    normalized = [_investigation_item(item, rank_hint=index + 1) for index, item in enumerate(items)]
    normalized.sort(
        key=lambda item: (
            _PRIORITY_ORDER.get(str(item["priority"]), 99),
            str(item["investigation_type"]),
            -float(item.get("sort_metric") or 0.0),
            str(item["title"]),
            str(item["id"]),
        )
    )
    ranked: list[dict[str, Any]] = []
    for index, item in enumerate(normalized[:limit], start=1):
        clean_item = dict(item)
        clean_item["rank"] = index
        clean_item.pop("sort_metric", None)
        ranked.append(clean_item)
    return ranked


def _rank_investigation_rows(
    rows: Sequence[tuple[str, Mapping[str, Any]]],
    *,
    limit: int,
    histories: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    histories = histories or {}
    normalized = [
        _investigation_item(
            item,
            rank_hint=index + 1,
            section_name=section_name,
            history=histories.get(story_key(item, section_name=section_name)),
        )
        for index, (section_name, item) in enumerate(rows)
    ]
    normalized.sort(
        key=lambda item: (
            _PRIORITY_ORDER.get(str(item["priority"]), 99),
            str(item["investigation_type"]),
            -float(item.get("sort_metric") or 0.0),
            str(item["title"]),
            str(item["id"]),
        )
    )
    ranked: list[dict[str, Any]] = []
    for index, item in enumerate(normalized[:limit], start=1):
        clean_item = dict(item)
        clean_item["rank"] = index
        clean_item.pop("sort_metric", None)
        ranked.append(clean_item)
    return ranked


def _investigation_source_items(sections: Mapping[str, list[Mapping[str, Any]]]) -> list[Mapping[str, Any]]:
    return [item for _section_name, item in _investigation_source_rows(sections)]


def _investigation_source_rows(sections: Mapping[str, list[Mapping[str, Any]]]) -> list[tuple[str, Mapping[str, Any]]]:
    rows = _candidate_rows(sections, ("Investigation Candidates", "Investigation Queue"))
    if rows:
        return rows
    return _candidate_rows(sections, ("Significant Deviations", "Historical-Live Deviations", "Live-Only Anomalies"))


def _attention_level(investigations: Sequence[Mapping[str, Any]], deviations: Sequence[Mapping[str, Any]]) -> str:
    priorities = {str(item.get("priority")) for item in investigations}
    if "critical" in priorities:
        return "critical"
    if "high" in priorities or len(deviations) >= 3:
        return "high"
    if investigations or deviations:
        return "medium"
    return "low"


def _payload_date(payloads: Sequence[Mapping[str, Any]], selected_date: str | date | datetime | None) -> str:
    selected = _normalize_date(selected_date)
    if selected:
        return selected
    for payload in payloads:
        params = payload.get("query_parameters") if isinstance(payload.get("query_parameters"), Mapping) else {}
        candidate = _normalize_date(params.get("snapshot_date") or payload.get("briefing_date") or payload.get("run_date"))
        if candidate:
            return candidate
    return "not selected"


def _display_payloads(
    payloads: Sequence[Mapping[str, Any]],
    selected_date: str | date | datetime | None,
) -> Sequence[Mapping[str, Any]]:
    selected = _normalize_date(selected_date)
    if not selected:
        return payloads
    matched = [payload for payload in payloads if _payload_intrinsic_date(payload, selected_date) == selected]
    return matched or payloads


def _history_for(histories: Mapping[str, Mapping[str, Any]], item: Mapping[str, Any], section_name: str) -> Mapping[str, Any] | None:
    return histories.get(story_key(item, section_name=section_name))


def _summary_items_from_rows(
    rows: Sequence[tuple[str, Mapping[str, Any]]],
    histories: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _make_summary_item(item, section_name=section_name, history=_history_for(histories, item, section_name))
        for section_name, item in rows
    ]


def _evolution_highlight_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("title"),
        "story_key": item.get("story_key"),
        "priority": item.get("priority", "not available"),
        "confidence": item.get("confidence"),
        "evolution_direction": item.get("evolution_direction"),
        "why_now": item.get("why_now"),
        "story_history": item.get("story_history"),
    }


def build_evolution_highlights(items: Sequence[Mapping[str, Any]], *, limit: int = 5) -> dict[str, list[dict[str, Any]]]:
    grouped = {
        "rising_stories": [],
        "stable_stories": [],
        "falling_stories": [],
        "reappearing_stories": [],
    }
    names = {
        "rising": "rising_stories",
        "stable": "stable_stories",
        "falling": "falling_stories",
        "reappearing": "reappearing_stories",
    }
    seen: set[str] = set()
    ordered = sorted(
        items,
        key=lambda item: (
            _PRIORITY_ORDER.get(str(item.get("priority", "medium")), 99),
            -_CONFIDENCE_STRENGTH.get(str(item.get("confidence")), 0),
            str(item.get("title", "")),
            str(item.get("story_key", "")),
        ),
    )
    for item in ordered:
        direction = str(item.get("evolution_direction") or "unknown")
        group_name = names.get(direction)
        key = str(item.get("story_key") or item.get("title") or "")
        if not group_name or not key or key in seen or len(grouped[group_name]) >= limit:
            continue
        grouped[group_name].append(_evolution_highlight_item(item))
        seen.add(key)
    return grouped


def _briefing_quality_status(
    *,
    major: Sequence[Mapping[str, Any]],
    investigations: Sequence[Mapping[str, Any]],
    deviations: Sequence[Mapping[str, Any]],
    themes: Sequence[Mapping[str, Any]],
    persistence: Sequence[Mapping[str, Any]],
    suppression_summary: Mapping[str, int],
) -> str:
    shown_count = sum(len(items) for items in (major, investigations, deviations, themes, persistence))
    if shown_count == 0:
        return "empty"
    noisy_suppressed = (
        int(suppression_summary.get("duplicates_suppressed", 0))
        + int(suppression_summary.get("low_confidence_suppressed", 0))
        + int(suppression_summary.get("internal_artifacts_suppressed", 0))
    )
    if noisy_suppressed >= 3 and noisy_suppressed >= max(1, shown_count // 2):
        return "noisy"
    strong_items = [
        item
        for item in [*major, *investigations]
        if item.get("confidence") in {"medium", "high"}
    ]
    if len(strong_items) >= 3:
        return "strong"
    return "thin"


def build_daily_briefing(
    payloads: Sequence[Mapping[str, Any]],
    *,
    selected_date: str | date | datetime | None = None,
    source_paths: Sequence[str] = (),
) -> dict[str, Any]:
    """Normalize existing intelligence payloads into the Daily Briefing view model."""

    histories = build_story_histories(payloads, selected_date=selected_date)
    display_payloads = _display_payloads(payloads, selected_date)
    sections = _section_map(display_payloads)
    suppression_summary = _empty_suppression_summary()

    investigation_rows, investigation_summary = _quality_gate_raw_items(
        _sort_summary_rows(_investigation_source_rows(sections)),
        limit=SECTION_CAPS["investigation_candidates"],
        investigation=True,
    )
    _add_suppression_summary(suppression_summary, investigation_summary)
    investigations = _rank_investigation_rows(
        investigation_rows,
        limit=SECTION_CAPS["investigation_candidates"],
        histories=histories,
    )

    deviation_rows, deviation_summary = _quality_gate_raw_items(
        _sort_summary_rows(_candidate_rows(sections, ("Significant Deviations", "Historical-Live Deviations"))),
        limit=SECTION_CAPS["historical_live_deviation_highlights"],
    )
    _add_suppression_summary(suppression_summary, deviation_summary)
    deviations = _summary_items_from_rows(deviation_rows, histories)

    major_rows, major_summary = _quality_gate_raw_items(
        _sort_summary_rows(
            _candidate_rows(
                sections,
                (
                    "Significant Deviations",
                    "Live-Only Anomalies",
                    "Changed Structures",
                    "Persistent Structures",
                    "Dominant Structures",
                    "Recurring Structures",
                    "Investigation Candidates",
                ),
            )
        ),
        limit=SECTION_CAPS["major_developments"],
    )
    _add_suppression_summary(suppression_summary, major_summary)
    major = _summary_items_from_rows(major_rows, histories)

    theme_rows, theme_summary = _quality_gate_raw_items(
        _sort_summary_rows(_candidate_rows(sections, ("Changed Structures", "Transitioning Structures", "Live-Only Anomalies"))),
        limit=SECTION_CAPS["emerging_themes"],
    )
    _add_suppression_summary(suppression_summary, theme_summary)
    themes = _summary_items_from_rows(theme_rows, histories)

    persistence_rows, persistence_summary = _quality_gate_raw_items(
        _sort_summary_rows(_candidate_rows(sections, ("Persistent Structures", "Recurring Structures", "Persistent Structures Weakening Live"))),
        limit=SECTION_CAPS["persistence_watchlist"],
    )
    _add_suppression_summary(suppression_summary, persistence_summary)
    persistence = _summary_items_from_rows(persistence_rows, histories)

    evolution_highlights = build_evolution_highlights(
        [*investigations, *major, *deviations, *themes, *persistence],
        limit=SECTION_CAPS["evolution_highlights"],
    )
    suppression_summary["final_items_shown"] = sum(
        len(items) for items in (major, investigations, deviations, themes, persistence)
    )
    briefing_quality_status = _briefing_quality_status(
        major=major,
        investigations=investigations,
        deviations=deviations,
        themes=themes,
        persistence=persistence,
        suppression_summary=suppression_summary,
    )
    return {
        "briefing_date": _payload_date(payloads, selected_date),
        "attention_level": _attention_level(investigations, deviations),
        "briefing_quality_status": briefing_quality_status,
        "suppression_summary": suppression_summary,
        "major_developments": major,
        "investigation_candidates": investigations,
        "historical_live_deviation_highlights": deviations,
        "emerging_themes": themes,
        "persistence_watchlist": persistence,
        "evolution_highlights": evolution_highlights,
        "confidence_labels": sorted({item.get("confidence") for item in [*major, *investigations, *deviations] if item.get("confidence")}),
        "stories": investigations,
        "source_paths": list(source_paths),
        "empty": not any([major, investigations, deviations, themes, persistence]),
    }


def _read_json(path: Path) -> Mapping[str, Any] | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else None


def load_daily_briefing(
    *,
    selected_date: str | date | datetime | None = None,
    artifact_paths: Sequence[str | Path] = DEFAULT_ARTIFACT_PATHS,
    project_root: str | Path | None = None,
) -> BriefingLoadResult:
    """Load existing local SEFI JSON artifacts and return a Daily Briefing view model."""

    root = Path(project_root) if project_root is not None else Path.cwd()
    inspected: list[str] = []
    missing: list[str] = []
    loaded: list[str] = []
    warnings: list[str] = []
    payloads: list[Mapping[str, Any]] = []
    for raw_path in artifact_paths:
        path = Path(raw_path)
        candidate = path if path.is_absolute() else root / path
        display = str(path)
        inspected.append(display)
        if not candidate.exists():
            missing.append(display)
            continue
        try:
            payload = _read_json(candidate)
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"Skipped {display}: {exc.__class__.__name__}")
            continue
        if payload is None:
            warnings.append(f"Skipped {display}: JSON root is not an object")
            continue
        payloads.append(payload)
        loaded.append(display)
    briefing = build_daily_briefing(payloads, selected_date=selected_date, source_paths=loaded)
    return BriefingLoadResult(
        briefing=briefing,
        inspected_paths=inspected,
        loaded_paths=loaded,
        missing_paths=missing,
        warnings=warnings,
    )
