from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _as_text(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def _to_history(rows: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    history: list[OrderedDict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        payload = row.get("payload") if isinstance(row.get("payload"), Mapping) else {}
        replay_metadata = row.get("replay_metadata") if isinstance(row.get("replay_metadata"), Mapping) else {}
        semantic = payload.get("semantic") if isinstance(payload.get("semantic"), Mapping) else {}
        contradictions = payload.get("contradictions") if isinstance(payload.get("contradictions"), Mapping) else {}
        run_id = _as_text(payload.get("run_id") or row.get("run_id") or row.get("replay_id") or replay_metadata.get("run_id") or row.get("record_id"))
        if not run_id:
            continue
        history.append(OrderedDict([
            ("run_id", run_id),
            ("semantic", OrderedDict([("themes", _as_list(semantic.get("themes")))])),
            ("contradictions", OrderedDict([("claims", _as_list(contradictions.get("claims")))])),
            ("evidence_highlights", deepcopy(_as_list(payload.get("evidence_highlights")) or _as_list(row.get("evidence_refs")))),
            ("lineage_refs", deepcopy(_as_list(row.get("lineage_refs")))),
        ]))
    return history


def _score(history: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    run_ids = []
    evidence_refs = []
    contradiction_claims = []
    themes = []
    lineage_refs = []
    for row in history:
        if not isinstance(row, Mapping):
            continue
        run_ids.append(_as_text(row.get("run_id")))
        for ev in _as_list(row.get("evidence_highlights")):
            if isinstance(ev, Mapping):
                evidence_refs.append(_as_text(ev.get("evidence_ref")))
                evidence_refs.extend(_as_text(x) for x in _as_list(ev.get("supporting_evidence_refs")))
            else:
                evidence_refs.append(_as_text(ev))
        contradiction_claims.extend(_as_text(x) for x in _as_list((row.get("contradictions") or {}).get("claims")))
        themes.extend(_as_text(x) for x in _as_list((row.get("semantic") or {}).get("themes")))
        lineage_refs.extend(_as_text(x) for x in _as_list(row.get("lineage_refs")))
    clean = lambda xs: [x for x in xs if x]
    runs = clean(run_ids)
    evidence = clean(evidence_refs)
    contradictions = clean(contradiction_claims)
    theme_refs = clean(themes)
    lineages = clean(lineage_refs)
    return OrderedDict([
        ("run_count", len(runs)),
        ("unique_run_count", len(set(runs))),
        ("replay_continuity_score", round(min(1.0, len(runs) / 5), 3)),
        ("evidence_reinforcement_score", round(min(1.0, len(set(evidence)) / 8), 3)),
        ("linkage_density", round((len(lineages) / max(1, len(runs))), 3)),
        ("semantic_persistence_count", len(set(theme_refs))),
        ("contradiction_continuity_count", len(set(contradictions))),
        ("strongest_evidence_availability", max(1 if evidence else 0, max((evidence.count(x) for x in set(evidence)), default=0))),
        ("explainability_confidence", round(min(1.0, (len(set(evidence)) + len(set(theme_refs)) + len(set(contradictions))) / 18), 3)),
        ("duplicate_run_count", max(0, len(runs) - len(set(runs)))),
    ])


def compare_d8_b2_backfill_readback(*, before_rows: list[Mapping[str, Any]], after_rows: list[Mapping[str, Any]], dry_run: bool = True) -> OrderedDict[str, Any]:
    if not dry_run:
        return OrderedDict([("status", "BLOCKED_NON_DRY_RUN"), ("no_write_governance", False), ("reason", "readback_verification_requires_dry_run_true")])
    before_score = _score(_to_history(before_rows))
    after_score = _score(_to_history(after_rows))
    deltas = OrderedDict((k + "_delta", round(float(after_score.get(k, 0)) - float(before_score.get(k, 0)), 3)) for k in (
        "replay_continuity_score",
        "evidence_reinforcement_score",
        "linkage_density",
        "semantic_persistence_count",
        "contradiction_continuity_count",
        "strongest_evidence_availability",
        "explainability_confidence",
    ))
    return OrderedDict([
        ("status", "READBACK_VERIFICATION_DRY_RUN"),
        ("no_write_governance", True),
        ("before", before_score),
        ("after", after_score),
        ("deltas", deltas),
        ("sparse_history", bool(before_score["run_count"] < 2 or after_score["run_count"] < 2)),
        ("duplicate_replay_ids_detected", bool(after_score["duplicate_run_count"] > 0)),
    ])


__all__ = ["compare_d8_b2_backfill_readback"]
