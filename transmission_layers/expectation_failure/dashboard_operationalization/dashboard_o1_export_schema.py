"""Deterministic Dashboard O1 Streamlit/Supabase export schema builders."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence

SCHEMA_VERSION = "dashboard_o1_schema_v1"
MODULE_VERSION = "1.0.0"
UNKNOWN = "UNKNOWN"

PAYLOAD_KEY_ORDER = [
    "dashboard_entity_facts",
    "dashboard_subsector_facts",
    "dashboard_alert_facts",
    "dashboard_replay_facts",
    "dashboard_benchmark_facts",
    "dashboard_evidence_facts",
    "dashboard_report_metadata",
    "dashboard_export_manifest",
]


def _clamp_score(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = float(default)
    return round(max(0.0, min(100.0, numeric)), 4)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if value is None:
        return default
    return bool(value)


def _stable_text(value: Any, default: str = UNKNOWN) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _stable_checksum(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ordered_record(field_order: Sequence[str], values: Mapping[str, Any]) -> OrderedDict:
    return OrderedDict((field, values.get(field)) for field in field_order)


def build_dashboard_entity_facts(entity_rows: Iterable[Mapping[str, Any]] | None = None, *, run_id: str = UNKNOWN, run_date_sgt: str = UNKNOWN, certification_status: str = "pending") -> List[OrderedDict]:
    rows = deepcopy(list(entity_rows or []))
    order = ["run_id", "run_date_sgt", "entity_id", "entity_name", "ticker", "subsector", "composite_score", "valuation_stretch_score", "fundamental_support_score", "narrative_saturation_score", "certainty_fragility_score", "structural_weakness_score", "relative_fragility_rank", "relative_fragility_band", "asymmetry_label", "benchmark_relative_label", "alert_state", "dominant_driver", "evidence_quality_flag", "certification_status", "replay_checksum"]
    built = []
    for row in rows:
        record = {
            "run_id": _stable_text(row.get("run_id"), run_id),
            "run_date_sgt": _stable_text(row.get("run_date_sgt"), run_date_sgt),
            "entity_id": _stable_text(row.get("entity_id")),
            "entity_name": _stable_text(row.get("entity_name")),
            "ticker": _stable_text(row.get("ticker")),
            "subsector": _stable_text(row.get("subsector")),
            "composite_score": _clamp_score(row.get("composite_score")),
            "valuation_stretch_score": _clamp_score(row.get("valuation_stretch_score")),
            "fundamental_support_score": _clamp_score(row.get("fundamental_support_score")),
            "narrative_saturation_score": _clamp_score(row.get("narrative_saturation_score")),
            "certainty_fragility_score": _clamp_score(row.get("certainty_fragility_score")),
            "structural_weakness_score": _clamp_score(row.get("structural_weakness_score")),
            "relative_fragility_rank": _to_int(row.get("relative_fragility_rank"), 0),
            "relative_fragility_band": _stable_text(row.get("relative_fragility_band"), "unclassified"),
            "asymmetry_label": _stable_text(row.get("asymmetry_label"), "unclassified"),
            "benchmark_relative_label": _stable_text(row.get("benchmark_relative_label"), "neutral"),
            "alert_state": _stable_text(row.get("alert_state"), "normal"),
            "dominant_driver": _stable_text(row.get("dominant_driver"), "none"),
            "evidence_quality_flag": _stable_text(row.get("evidence_quality_flag"), "insufficient"),
            "certification_status": _stable_text(row.get("certification_status"), certification_status),
        }
        record["replay_checksum"] = _stable_checksum(record)
        built.append(_ordered_record(order, record))
    return sorted(built, key=lambda r: (r["composite_score"] * -1, r["entity_id"], r["ticker"]))


def build_dashboard_subsector_facts(entity_facts: Iterable[Mapping[str, Any]] | None = None, *, run_id: str = UNKNOWN, run_date_sgt: str = UNKNOWN) -> List[OrderedDict]:
    facts = deepcopy(list(entity_facts or []))
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for row in facts:
        grouped.setdefault(_stable_text(row.get("subsector")), []).append(row)
    order = ["run_id", "run_date_sgt", "subsector", "entity_count", "avg_composite_score", "max_composite_score", "fragile_entity_count", "alert_entity_count", "dominant_subsector_driver", "subsector_fragility_band", "cluster_label", "evidence_quality_summary", "replay_checksum"]
    out = []
    for subsector in sorted(grouped.keys()):
        rows = grouped[subsector]
        scores = [_clamp_score(r.get("composite_score")) for r in rows]
        alerts = [_stable_text(r.get("alert_state"), "normal") for r in rows]
        drivers = sorted(_stable_text(r.get("dominant_driver"), "none") for r in rows)
        record = {
            "run_id": _stable_text(run_id),
            "run_date_sgt": _stable_text(run_date_sgt),
            "subsector": subsector,
            "entity_count": len(rows),
            "avg_composite_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
            "max_composite_score": max(scores) if scores else 0.0,
            "fragile_entity_count": sum(1 for s in scores if s >= 70),
            "alert_entity_count": sum(1 for a in alerts if a != "normal"),
            "dominant_subsector_driver": drivers[0] if drivers else "none",
            "subsector_fragility_band": "elevated" if (sum(scores) / len(scores) if scores else 0) >= 70 else "contained",
            "cluster_label": f"{subsector.lower().replace(' ', '_')}_cluster",
            "evidence_quality_summary": "sufficient" if rows else "insufficient",
        }
        record["replay_checksum"] = _stable_checksum(record)
        out.append(_ordered_record(order, record))
    return out


def _table_builder(rows: Iterable[Mapping[str, Any]] | None, order: Sequence[str], defaults: Mapping[str, Any], sort_key):
    materialized = deepcopy(list(rows or []))
    out = []
    for row in materialized:
        record: Dict[str, Any] = {}
        for key in order:
            v = row.get(key, defaults.get(key))
            if key.endswith("_score") or key in {"relative_gap", "normalized_score", "source_value"}:
                v = _clamp_score(v)
            elif key in {"replay_sequence", "evidence_chain_position"}:
                v = _to_int(v, 0)
            elif key.endswith("_flag"):
                if isinstance(defaults.get(key), bool):
                    v = _to_bool(v, bool(defaults.get(key)))
                else:
                    v = _stable_text(v, _stable_text(defaults.get(key)))
            elif isinstance(defaults.get(key), str):
                v = _stable_text(v, defaults.get(key))
            record[key] = v
        record["replay_checksum"] = _stable_checksum(record)
        out.append(_ordered_record(order, record))
    return sorted(out, key=sort_key)


def build_dashboard_alert_facts(alert_rows=None, *, run_id=UNKNOWN, run_date_sgt=UNKNOWN):
    order = ["run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "alert_state", "alert_severity_band", "deterioration_label", "active_alert_flag", "dominant_alert_driver", "alert_explanation_template_id", "evidence_quality_flag", "replay_checksum"]
    defaults = {"run_id": run_id, "run_date_sgt": run_date_sgt, "entity_id": UNKNOWN, "ticker": UNKNOWN, "subsector": UNKNOWN, "alert_state": "normal", "alert_severity_band": "low", "deterioration_label": "stable", "active_alert_flag": False, "dominant_alert_driver": "none", "alert_explanation_template_id": "alert_template_default", "evidence_quality_flag": "insufficient", "replay_checksum": ""}
    return _table_builder(alert_rows, order, defaults, lambda r: (r["entity_id"], r["ticker"], r["alert_state"]))


def build_dashboard_replay_facts(replay_rows=None, *, run_id=UNKNOWN):
    order = ["run_id", "replay_date_sgt", "entity_id", "ticker", "subsector", "composite_score", "alert_state", "fragility_band", "deterioration_label", "benchmark_relative_label", "replay_sequence", "replay_checksum"]
    defaults = {"run_id": run_id, "replay_date_sgt": UNKNOWN, "entity_id": UNKNOWN, "ticker": UNKNOWN, "subsector": UNKNOWN, "composite_score": 0.0, "alert_state": "normal", "fragility_band": "contained", "deterioration_label": "stable", "benchmark_relative_label": "neutral", "replay_sequence": 0, "replay_checksum": ""}
    return _table_builder(replay_rows, order, defaults, lambda r: (r["entity_id"], r["replay_sequence"], r["replay_date_sgt"]))


def build_dashboard_benchmark_facts(benchmark_rows=None, *, run_id=UNKNOWN, run_date_sgt=UNKNOWN):
    order = ["run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "benchmark_id", "entity_fragility_score", "benchmark_fragility_score", "relative_gap", "relative_gap_band", "benchmark_relative_label", "outlier_flag", "replay_checksum"]
    defaults = {"run_id": run_id, "run_date_sgt": run_date_sgt, "entity_id": UNKNOWN, "ticker": UNKNOWN, "subsector": UNKNOWN, "benchmark_id": "benchmark_default", "entity_fragility_score": 0.0, "benchmark_fragility_score": 0.0, "relative_gap": 0.0, "relative_gap_band": "neutral", "benchmark_relative_label": "neutral", "outlier_flag": False, "replay_checksum": ""}
    return _table_builder(benchmark_rows, order, defaults, lambda r: (r["entity_id"], r["benchmark_id"], r["ticker"]))


def build_dashboard_evidence_facts(evidence_rows=None, *, run_id=UNKNOWN, run_date_sgt=UNKNOWN):
    order = ["run_id", "run_date_sgt", "entity_id", "ticker", "evidence_id", "evidence_type", "source_metric", "source_value", "normalized_score", "quality_flag", "evidence_chain_position", "template_id", "replay_checksum"]
    defaults = {"run_id": run_id, "run_date_sgt": run_date_sgt, "entity_id": UNKNOWN, "ticker": UNKNOWN, "evidence_id": UNKNOWN, "evidence_type": "metric", "source_metric": UNKNOWN, "source_value": 0.0, "normalized_score": 0.0, "quality_flag": "insufficient", "evidence_chain_position": 0, "template_id": "evidence_template_default", "replay_checksum": ""}
    return _table_builder(evidence_rows, order, defaults, lambda r: (r["entity_id"], r["evidence_chain_position"], r["evidence_id"]))


def build_dashboard_export_manifest(*, run_id: str, record_counts: Mapping[str, int], checksum_input: Mapping[str, Any], deterministic_sort_keys: Mapping[str, Sequence[str]] | None = None) -> OrderedDict:
    export_groups = list(PAYLOAD_KEY_ORDER[:-2])
    manifest = OrderedDict([
        ("run_id", _stable_text(run_id)),
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("export_groups", export_groups),
        ("record_counts", OrderedDict((k, _to_int(record_counts.get(k), 0)) for k in export_groups)),
        ("deterministic_sort_keys", deterministic_sort_keys or {}),
        ("checksum", ""),
        ("invariant_flags", OrderedDict([
            ("deterministic_only", True),
            ("bounded_scores", True),
            ("immutable_input_safety", True),
            ("no_side_effect_io", True),
        ])),
    ])
    manifest["checksum"] = _stable_checksum(checksum_input)
    return manifest


def build_dashboard_report_metadata(*, run_id: str, run_date_sgt: str, export_manifest_checksum: str, record_counts: Mapping[str, int], report_id: str = "dashboard_o1_report", report_type: str = "institutional_dashboard", certification_status: str = "provisional", generated_at_sgt: str | None = None) -> OrderedDict:
    return OrderedDict([
        ("run_id", _stable_text(run_id)),
        ("run_date_sgt", _stable_text(run_date_sgt)),
        ("report_id", _stable_text(report_id)),
        ("report_type", _stable_text(report_type)),
        ("certification_status", _stable_text(certification_status)),
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("entity_fact_count", _to_int(record_counts.get("dashboard_entity_facts"), 0)),
        ("subsector_fact_count", _to_int(record_counts.get("dashboard_subsector_facts"), 0)),
        ("alert_fact_count", _to_int(record_counts.get("dashboard_alert_facts"), 0)),
        ("replay_fact_count", _to_int(record_counts.get("dashboard_replay_facts"), 0)),
        ("benchmark_fact_count", _to_int(record_counts.get("dashboard_benchmark_facts"), 0)),
        ("evidence_fact_count", _to_int(record_counts.get("dashboard_evidence_facts"), 0)),
        ("export_manifest_checksum", _stable_text(export_manifest_checksum)),
        ("generated_at_sgt", _stable_text(generated_at_sgt, run_date_sgt)),
    ])


def build_dashboard_o1_export_payload(*, run_id: str, run_date_sgt: str, entity_rows=None, alert_rows=None, replay_rows=None, benchmark_rows=None, evidence_rows=None, generated_at_sgt: str | None = None, certification_status: str = "provisional") -> OrderedDict:
    entity = build_dashboard_entity_facts(entity_rows, run_id=run_id, run_date_sgt=run_date_sgt, certification_status=certification_status)
    subsector = build_dashboard_subsector_facts(entity, run_id=run_id, run_date_sgt=run_date_sgt)
    alert = build_dashboard_alert_facts(alert_rows, run_id=run_id, run_date_sgt=run_date_sgt)
    replay = build_dashboard_replay_facts(replay_rows, run_id=run_id)
    benchmark = build_dashboard_benchmark_facts(benchmark_rows, run_id=run_id, run_date_sgt=run_date_sgt)
    evidence = build_dashboard_evidence_facts(evidence_rows, run_id=run_id, run_date_sgt=run_date_sgt)

    payload_core = OrderedDict([
        ("dashboard_entity_facts", entity),
        ("dashboard_subsector_facts", subsector),
        ("dashboard_alert_facts", alert),
        ("dashboard_replay_facts", replay),
        ("dashboard_benchmark_facts", benchmark),
        ("dashboard_evidence_facts", evidence),
    ])
    record_counts = {k: len(v) for k, v in payload_core.items()}
    manifest = build_dashboard_export_manifest(
        run_id=run_id,
        record_counts=record_counts,
        checksum_input=payload_core,
        deterministic_sort_keys={
            "dashboard_entity_facts": ["composite_score(desc)", "entity_id", "ticker"],
            "dashboard_subsector_facts": ["subsector"],
            "dashboard_alert_facts": ["entity_id", "ticker", "alert_state"],
            "dashboard_replay_facts": ["entity_id", "replay_sequence", "replay_date_sgt"],
            "dashboard_benchmark_facts": ["entity_id", "benchmark_id", "ticker"],
            "dashboard_evidence_facts": ["entity_id", "evidence_chain_position", "evidence_id"],
        },
    )
    metadata = build_dashboard_report_metadata(
        run_id=run_id,
        run_date_sgt=run_date_sgt,
        export_manifest_checksum=manifest["checksum"],
        record_counts=record_counts,
        certification_status=certification_status,
        generated_at_sgt=generated_at_sgt,
    )

    return OrderedDict([
        ("dashboard_entity_facts", entity),
        ("dashboard_subsector_facts", subsector),
        ("dashboard_alert_facts", alert),
        ("dashboard_replay_facts", replay),
        ("dashboard_benchmark_facts", benchmark),
        ("dashboard_evidence_facts", evidence),
        ("dashboard_report_metadata", metadata),
        ("dashboard_export_manifest", manifest),
    ])


__all__ = [
    "build_dashboard_entity_facts",
    "build_dashboard_subsector_facts",
    "build_dashboard_alert_facts",
    "build_dashboard_replay_facts",
    "build_dashboard_benchmark_facts",
    "build_dashboard_evidence_facts",
    "build_dashboard_report_metadata",
    "build_dashboard_export_manifest",
    "build_dashboard_o1_export_payload",
]
