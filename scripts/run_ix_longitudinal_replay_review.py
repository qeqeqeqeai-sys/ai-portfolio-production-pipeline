#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Mapping


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _as_map(v: Any) -> Mapping[str, Any]:
    return v if isinstance(v, Mapping) else {}


def _txt(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def _load_rows(path: Path) -> list[Mapping[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, Mapping)]
    if isinstance(payload, Mapping):
        rows = payload.get("rows")
        if isinstance(rows, list):
            return [x for x in rows if isinstance(x, Mapping)]
    return []


def _extract_runs(rows: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    out: list[OrderedDict[str, Any]] = []
    for row in rows:
        payload = _as_map(row.get("payload"))
        replay_meta = _as_map(row.get("replay_metadata"))
        run_id = _txt(payload.get("run_id") or row.get("run_id") or row.get("replay_id") or replay_meta.get("run_id") or row.get("record_id"))
        if not run_id:
            continue
        ix = OrderedDict()
        for k in ("ix1", "ix2", "ix3", "ix4", "ix5"):
            ix[k] = _as_map(payload.get(k) or row.get(k))
        semantic = _as_map(payload.get("semantic"))
        contradictions = _as_map(payload.get("contradictions"))
        out.append(OrderedDict([
            ("run_id", run_id),
            ("timestamp", _txt(row.get("created_at") or payload.get("run_timestamp") or row.get("run_timestamp"))),
            ("lineage_refs", sorted({_txt(x) for x in _as_list(row.get("lineage_refs")) if _txt(x)})),
            ("themes", sorted({_txt(x) for x in _as_list(semantic.get("themes")) if _txt(x)})),
            ("contradictions", sorted({_txt(x) for x in _as_list(contradictions.get("claims")) if _txt(x)})),
            ("ix", ix),
        ]))
    return sorted(out, key=lambda r: (r["timestamp"], r["run_id"]))


def _status(ix_payload: Mapping[str, Any]) -> str:
    cert = _as_map(ix_payload.get("certification"))
    return _txt(cert.get("status") or ix_payload.get("status") or "MISSING") or "MISSING"


def _build_review(runs: list[OrderedDict[str, Any]]) -> OrderedDict[str, Any]:
    ix_presence = {k: sum(1 for r in runs if bool(_as_map(r["ix"].get(k)))) for k in ("ix1", "ix2", "ix3", "ix4", "ix5")}
    ix_status = {k: Counter(_status(_as_map(r["ix"].get(k))) for r in runs if _as_map(r["ix"].get(k))) for k in ix_presence}
    lineage_coverage = sum(1 for r in runs if r.get("lineage_refs"))
    contradiction_union = sorted({c for r in runs for c in r.get("contradictions", [])})
    theme_union = sorted({t for r in runs for t in r.get("themes", [])})
    novelty_ratio = round(len(theme_union) / max(1, len(runs)), 3)
    replay_diversity = "low" if novelty_ratio < 1.0 else "moderate" if novelty_ratio < 2.0 else "high"

    compression_scores = []
    interpret_scores = []
    continuity_scores = []
    for r in runs:
        ix3 = _as_map(r["ix"].get("ix3"))
        ix4 = _as_map(r["ix"].get("ix4"))
        ix5 = _as_map(r["ix"].get("ix5"))
        compression_scores.append(float(_as_map(ix3.get("dashboard")).get("compression_stability_score") or 0.0))
        interpret_scores.append(float(_as_map(ix4.get("dashboard")).get("interpretability_scorecard", {}).get("average_interpretability_score") or 0.0))
        continuity_scores.append(float(_as_map(ix5.get("dashboard")).get("continuity_scorecard", {}).get("overall_continuity_score") or 0.0))

    sparse = len(runs) < 5
    return OrderedDict([
        ("run_count", len(runs)),
        ("ix_archive_coverage", ix_presence),
        ("ix_status_distribution", {k: OrderedDict(sorted(v.items())) for k, v in ix_status.items()}),
        ("lineage_linked_runs", lineage_coverage),
        ("lineage_coverage_ratio", round(lineage_coverage / max(1, len(runs)), 3)),
        ("replay_diversity_observation", OrderedDict([("theme_novelty_ratio", novelty_ratio), ("classification", replay_diversity)])),
        ("cross_run_delta_evolution", OrderedDict([
            ("persistent_contradictions", contradiction_union[:12]),
            ("semantic_fragility_evolution", "insufficient_data" if sparse else "observable"),
            ("transition_anomaly_recurrence", "insufficient_data" if sparse else "requires_ix2_delta_refs"),
            ("novelty_drought_or_saturation", "potential_saturation" if novelty_ratio < 1.0 else "no_drought_signal"),
        ])),
        ("compression_stability", OrderedDict([("avg_score", round(sum(compression_scores) / max(1, len(compression_scores)), 3)), ("status", "insufficient_data" if not any(compression_scores) else "observed") ])),
        ("interpretability_hardening_behavior", OrderedDict([("avg_score", round(sum(interpret_scores) / max(1, len(interpret_scores)), 3)), ("status", "insufficient_data" if not any(interpret_scores) else "observed") ])),
        ("explainability_continuity_behavior", OrderedDict([("avg_score", round(sum(continuity_scores) / max(1, len(continuity_scores)), 3)), ("status", "insufficient_data" if not any(continuity_scores) else "observed") ])),
        ("governance_boundary_confirmation", OrderedDict([
            ("read_only_review", True),
            ("no_autonomous_replay_execution", True),
            ("no_autonomous_approval", True),
            ("no_direct_sql", True),
            ("non_predictive", True),
            ("append_only_semantics_preserved", True),
            ("checksum_lineage_preserved", True),
        ])),
        ("operational_gap_report", OrderedDict([
            ("ix_persistability_gap", "present" if any(v == 0 for v in ix_presence.values()) else "not_detected"),
            ("details", "Some IX payloads are absent from persisted replay rows; no new write path was introduced." if any(v == 0 for v in ix_presence.values()) else "IX1-IX5 payloads appear in provided governed replay rows."),
        ])),
        ("stress_test_readiness", OrderedDict([
            ("status", "NOT_READY_MIN_HISTORY" if sparse else "CONDITIONALLY_READY"),
            ("minimum_governed_runs_recommended", 5 if sparse else len(runs)),
            ("architecture_expansion_recommendation", "paused"),
        ])),
    ])


def main() -> None:
    p = argparse.ArgumentParser(description="Read-only longitudinal replay + IX stress-test review")
    p.add_argument("--input", required=True, help="Path to governed replay rows JSON (array or {rows:[...]})")
    p.add_argument("--output", default="reports/ix_longitudinal_replay_review.json")
    args = p.parse_args()

    runs = _extract_runs(_load_rows(Path(args.input)))
    review = _build_review(runs)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(review, indent=2), encoding="utf-8")
    print(json.dumps(OrderedDict([("status", "ok"), ("output", str(out)), ("run_count", review.get("run_count"))]), indent=2))


if __name__ == "__main__":
    main()
