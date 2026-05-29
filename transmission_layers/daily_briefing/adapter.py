"""Thin Daily Briefing adapter over existing SEFI intelligence outputs.

This module is intentionally read-only and presentation-only. It normalizes existing
OBS-QUERY / HIST-INTEL style JSON artifacts into a compact analyst briefing view
model without creating facts, writing data, or generating new intelligence.
"""

from __future__ import annotations

import json
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
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
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


def _make_summary_item(item: Mapping[str, Any], *, section_name: str) -> dict[str, Any]:
    identifier = _clean_text(item.get("identifier"), default="Unidentified structure")
    classification = _clean_text(item.get("classification"), default="observed")
    source = _source_label(item)
    metric = item.get("ranking_metric") if isinstance(item.get("ranking_metric"), Mapping) else {}
    metric_name = _clean_text(metric.get("name"), default="ranking metric")
    metric_display = metric.get("value")
    lifecycle_state = infer_lifecycle_state(item, section_name=section_name)
    narrative_archetype = infer_narrative_archetype(item, section_name=section_name)
    what_changed = f"{identifier}: {classification} in {section_name}."
    why_it_matters = f"Source view: {source}; {metric_name}={metric_display if metric_display is not None else 'not available'}."
    return {
        "title": identifier,
        "what_changed": what_changed,
        "why_it_matters": why_it_matters,
        "source_section": section_name,
        "source_view": source,
        "classification": classification,
        "lifecycle_state": lifecycle_state,
        "narrative_archetype": narrative_archetype,
        "continuity_explanation": continuity_explanation(item, section_name=section_name),
        "confidence": _confidence_label(item),
        "historical_live_deviation": item.get("delta"),
    }


def _top_items(sections: Mapping[str, list[Mapping[str, Any]]], names: Iterable[str], *, limit: int) -> list[dict[str, Any]]:
    candidates: list[tuple[float, str, str, Mapping[str, Any]]] = []
    for section_name in names:
        for item in sections.get(section_name, []):
            candidates.append((-_metric_value(item), section_name, str(item.get("identifier") or ""), item))
    candidates.sort(key=lambda row: (row[0], row[1], row[2]))
    return [_make_summary_item(item, section_name=section_name) for _score, section_name, _identifier, item in candidates[:limit]]


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


def _investigation_item(item: Mapping[str, Any], *, rank_hint: int) -> dict[str, Any]:
    investigation_type = _type_for(item)
    priority = _priority_for(item, investigation_type)
    identifier = _clean_text(item.get("identifier"), default=f"investigation-{rank_hint}")
    classification = _clean_text(item.get("classification"), default="requires analyst review")
    source = _source_label(item)
    facts = _fact_ids(item)
    evidence = _evidence_ids(item)
    lifecycle_state = infer_lifecycle_state(item)
    narrative_archetype = infer_narrative_archetype(item)
    return {
        "id": f"{source}:{identifier}",
        "rank": rank_hint,
        "title": identifier,
        "investigation_type": investigation_type,
        "priority": priority,
        "lifecycle_state": lifecycle_state,
        "narrative_archetype": narrative_archetype,
        "continuity_explanation": continuity_explanation(item),
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


def _investigation_source_items(sections: Mapping[str, list[Mapping[str, Any]]]) -> list[Mapping[str, Any]]:
    items: list[Mapping[str, Any]] = []
    for name in ("Investigation Candidates", "Investigation Queue"):
        items.extend(sections.get(name, []))
    if items:
        return items
    for name in ("Significant Deviations", "Historical-Live Deviations", "Live-Only Anomalies"):
        items.extend(sections.get(name, []))
    return items


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


def build_daily_briefing(
    payloads: Sequence[Mapping[str, Any]],
    *,
    selected_date: str | date | datetime | None = None,
    source_paths: Sequence[str] = (),
) -> dict[str, Any]:
    """Normalize existing intelligence payloads into the Daily Briefing view model."""

    sections = _section_map(payloads)
    investigations = rank_investigations(_investigation_source_items(sections), limit=7)
    deviations = _top_items(sections, ("Significant Deviations", "Historical-Live Deviations"), limit=7)
    major = _top_items(
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
        limit=7,
    )
    themes = _top_items(sections, ("Changed Structures", "Transitioning Structures", "Live-Only Anomalies"), limit=7)
    persistence = _top_items(sections, ("Persistent Structures", "Recurring Structures", "Persistent Structures Weakening Live"), limit=7)
    return {
        "briefing_date": _payload_date(payloads, selected_date),
        "attention_level": _attention_level(investigations, deviations),
        "major_developments": major[:7],
        "investigation_candidates": investigations[:7],
        "historical_live_deviation_highlights": deviations[:7],
        "emerging_themes": themes[:7],
        "persistence_watchlist": persistence[:7],
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
