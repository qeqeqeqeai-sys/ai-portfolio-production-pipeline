"""Deterministic Dashboard O4 read-only Streamlit view-model builders."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "dashboard_o4_streamlit_view_model_v1"
MODULE_VERSION = "1.0.0"

FORBIDDEN_TERMS = (
    "buy", "sell", "short", "target price"
)

REQUIRED_TOP_LEVEL_KEYS = [
    "schema_version",
    "module_version",
    "page_registry",
    "filter_options",
    "kpi_cards",
    "executive_overview",
    "entity_table",
    "subsector_table",
    "alert_table",
    "benchmark_table",
    "replay_table",
    "evidence_table",
    "certification_panel",
    "ui_manifest",
    "invariant_flags",
]


def _stable_checksum(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _as_rows(rows: Any) -> list[dict[str, Any]]:
    if isinstance(rows, Mapping):
        return [dict(rows)]
    return [dict(r) for r in list(rows or []) if isinstance(r, Mapping)]


def _table(rows: Iterable[Mapping[str, Any]], keys: list[str], sort_keys: list[str]) -> list[OrderedDict]:
    out = []
    for row in rows:
        rec = OrderedDict((k, row.get(k)) for k in keys)
        out.append(rec)
    return sorted(out, key=lambda r: tuple(str(r.get(k, "")) for k in sort_keys))


def build_dashboard_o4_page_registry() -> list[OrderedDict]:
    allowed = ["filter", "sort", "drilldown", "inspect_evidence"]
    forbidden = ["trade_execution", "recommendation_generation", "portfolio_allocation", "target_price_generation", "backtest_execution", "predictive_modelling", "database_write"]
    pages = [
        ("executive_overview", "Executive Fragility Overview", ["kpi_cards", "executive_overview"]),
        ("entity_fragility_table", "Entity Fragility Table", ["entity_table"]),
        ("subsector_concentration", "Subsector Concentration", ["subsector_table"]),
        ("alert_monitoring", "Alert Monitoring", ["alert_table"]),
        ("benchmark_outliers", "Benchmark-Relative Outliers", ["benchmark_table"]),
        ("replay_timeline", "Replay Timeline", ["replay_table"]),
        ("evidence_audit_appendix", "Evidence Audit Appendix", ["evidence_table"]),
        ("report_export_certification", "Report / Export Certification", ["certification_panel", "ui_manifest"]),
    ]
    return [OrderedDict([
        ("page_id", pid),
        ("page_title", title),
        ("source_tables", list(sources)),
        ("allowed_interactions", list(allowed)),
        ("read_only", True),
        ("forbidden_interactions", list(forbidden)),
        ("page_sequence", idx),
    ]) for idx, (pid, title, sources) in enumerate(pages, start=1)]


def build_dashboard_o4_filter_options(payload: Mapping[str, Any]) -> OrderedDict:
    p = deepcopy(dict(payload))
    entity, alert, benchmark = _as_rows(p.get("dashboard_entity_facts")), _as_rows(p.get("dashboard_alert_facts")), _as_rows(p.get("dashboard_benchmark_facts"))
    report = dict(p.get("dashboard_report_metadata") or {})
    return OrderedDict([
        ("run_id", sorted({str(r.get("run_id", "")) for r in entity if r.get("run_id")}) or ([report.get("run_id")] if report.get("run_id") else [])),
        ("run_date_sgt", sorted({str(r.get("run_date_sgt", "")) for r in entity if r.get("run_date_sgt")}) or ([report.get("run_date_sgt")] if report.get("run_date_sgt") else [])),
        ("subsector", sorted({str(r.get("subsector", "")) for r in entity if r.get("subsector")})),
        ("alert_state", sorted({str(r.get("alert_state", "")) for r in alert if r.get("alert_state")})),
        ("benchmark_id", sorted({str(r.get("benchmark_id", "")) for r in benchmark if r.get("benchmark_id")})),
        ("certification_status", sorted({str(report.get("certification_status", "provisional"))})),
        ("evidence_quality_flag", sorted({str(r.get("evidence_quality_flag", "")) for r in entity if r.get("evidence_quality_flag")})),
    ])


def build_dashboard_o4_kpi_cards(payload: Mapping[str, Any]) -> OrderedDict:
    p = deepcopy(dict(payload))
    entity, subsector = _as_rows(p.get("dashboard_entity_facts")), _as_rows(p.get("dashboard_subsector_facts"))
    alert, benchmark, evidence = _as_rows(p.get("dashboard_alert_facts")), _as_rows(p.get("dashboard_benchmark_facts")), _as_rows(p.get("dashboard_evidence_facts"))
    report = dict(p.get("dashboard_report_metadata") or {})
    latest_run_id = report.get("run_id") or (entity[0].get("run_id") if entity else "UNKNOWN")
    return OrderedDict([
        ("total_entities", len(entity)),
        ("fragile_entity_count", sum(1 for r in entity if float(r.get("composite_score", 0) or 0) >= 70.0)),
        ("active_alert_count", sum(1 for r in alert if bool(r.get("active_alert_flag")) or str(r.get("alert_state", "normal")).lower() != "normal")),
        ("fragile_subsector_count", sum(1 for r in subsector if int(r.get("fragile_entity_count", 0) or 0) > 0)),
        ("benchmark_outlier_count", sum(1 for r in benchmark if bool(r.get("outlier_flag")) or str(r.get("benchmark_relative_label", "neutral")).lower() == "outlier")),
        ("evidence_quality_issue_count", sum(1 for r in evidence if str(r.get("quality_flag", "sufficient")).lower() != "sufficient")),
        ("certification_status", str(report.get("certification_status", "provisional"))),
        ("latest_run_id", str(latest_run_id)),
    ])


def build_dashboard_o4_entity_table(payload: Mapping[str, Any]) -> list[OrderedDict]:
    keys = ["run_id", "run_date_sgt", "entity_id", "entity_name", "ticker", "subsector", "composite_score", "relative_fragility_band", "alert_state", "benchmark_relative_label", "evidence_quality_flag", "certification_status", "replay_checksum"]
    return _table(_as_rows(payload.get("dashboard_entity_facts")), keys, ["entity_id", "ticker"])


def build_dashboard_o4_subsector_table(payload: Mapping[str, Any]) -> list[OrderedDict]:
    keys = ["run_id", "run_date_sgt", "subsector", "entity_count", "avg_composite_score", "fragile_entity_count", "alert_entity_count", "subsector_fragility_band", "evidence_quality_summary", "replay_checksum"]
    return _table(_as_rows(payload.get("dashboard_subsector_facts")), keys, ["subsector"])


def build_dashboard_o4_alert_table(payload: Mapping[str, Any]) -> list[OrderedDict]:
    keys = ["run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "alert_state", "alert_severity_band", "active_alert_flag", "dominant_alert_driver", "evidence_quality_flag", "replay_checksum"]
    return _table(_as_rows(payload.get("dashboard_alert_facts")), keys, ["entity_id", "ticker", "alert_state"])


def build_dashboard_o4_benchmark_table(payload: Mapping[str, Any]) -> list[OrderedDict]:
    keys = ["run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "benchmark_id", "entity_fragility_score", "benchmark_fragility_score", "relative_gap", "relative_gap_band", "benchmark_relative_label", "outlier_flag", "replay_checksum"]
    return _table(_as_rows(payload.get("dashboard_benchmark_facts")), keys, ["entity_id", "benchmark_id"])


def build_dashboard_o4_replay_table(payload: Mapping[str, Any]) -> list[OrderedDict]:
    keys = ["run_id", "replay_date_sgt", "entity_id", "ticker", "subsector", "composite_score", "fragility_band", "alert_state", "deterioration_label", "replay_sequence", "replay_checksum"]
    return _table(_as_rows(payload.get("dashboard_replay_facts")), keys, ["entity_id", "replay_sequence", "replay_date_sgt"])


def build_dashboard_o4_evidence_table(payload: Mapping[str, Any]) -> list[OrderedDict]:
    keys = ["run_id", "run_date_sgt", "entity_id", "ticker", "evidence_id", "evidence_type", "source_metric", "source_value", "normalized_score", "quality_flag", "evidence_chain_position", "template_id", "replay_checksum"]
    return _table(_as_rows(payload.get("dashboard_evidence_facts")), keys, ["entity_id", "evidence_chain_position", "evidence_id"])


def build_dashboard_o4_certification_panel(payload: Mapping[str, Any]) -> OrderedDict:
    p = deepcopy(dict(payload))
    report = dict(p.get("dashboard_report_metadata") or {})
    export_manifest = dict(p.get("dashboard_export_manifest") or {})
    o2_manifest = dict(p.get("dashboard_o2_persistence_manifest") or {})
    o3_manifest = dict(p.get("dashboard_o3_write_result_manifest") or {})
    return OrderedDict([
        ("run_id", report.get("run_id", "UNKNOWN")),
        ("run_date_sgt", report.get("run_date_sgt", "UNKNOWN")),
        ("certification_status", report.get("certification_status", "provisional")),
        ("report_type", report.get("report_type", "institutional_dashboard")),
        ("export_manifest_checksum", report.get("export_manifest_checksum", export_manifest.get("checksum", ""))),
        ("o2_validation_status", o2_manifest.get("validation_status", "not_provided")),
        ("o3_validation_status", o3_manifest.get("validation_status", "not_provided")),
        ("read_only_ui", True),
        ("deterministic_only", True),
    ])


def build_dashboard_o4_ui_manifest(view_model: Mapping[str, Any]) -> OrderedDict:
    payload = OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("page_count", len(view_model.get("page_registry", []))),
        ("filter_keys", list((view_model.get("filter_options") or {}).keys())),
        ("kpi_keys", list((view_model.get("kpi_cards") or {}).keys())),
        ("table_keys", ["entity_table", "subsector_table", "alert_table", "benchmark_table", "replay_table", "evidence_table"]),
        ("read_only", True),
    ])
    payload["checksum"] = _stable_checksum(payload)
    return payload


def build_dashboard_o4_view_model(payload: Mapping[str, Any]) -> OrderedDict:
    safe = deepcopy(dict(payload))
    out = OrderedDict()
    out["schema_version"] = SCHEMA_VERSION
    out["module_version"] = MODULE_VERSION
    out["page_registry"] = build_dashboard_o4_page_registry()
    out["filter_options"] = build_dashboard_o4_filter_options(safe)
    out["kpi_cards"] = build_dashboard_o4_kpi_cards(safe)
    out["executive_overview"] = OrderedDict([("summary", "Read-only expectation-fragility visibility panel."), ("record_counts", OrderedDict([
        ("entity", len(_as_rows(safe.get("dashboard_entity_facts")))),
        ("subsector", len(_as_rows(safe.get("dashboard_subsector_facts")))),
        ("alert", len(_as_rows(safe.get("dashboard_alert_facts")))),
        ("benchmark", len(_as_rows(safe.get("dashboard_benchmark_facts")))),
        ("replay", len(_as_rows(safe.get("dashboard_replay_facts")))),
        ("evidence", len(_as_rows(safe.get("dashboard_evidence_facts")))),
    ]))])
    out["entity_table"] = build_dashboard_o4_entity_table(safe)
    out["subsector_table"] = build_dashboard_o4_subsector_table(safe)
    out["alert_table"] = build_dashboard_o4_alert_table(safe)
    out["benchmark_table"] = build_dashboard_o4_benchmark_table(safe)
    out["replay_table"] = build_dashboard_o4_replay_table(safe)
    out["evidence_table"] = build_dashboard_o4_evidence_table(safe)
    out["certification_panel"] = build_dashboard_o4_certification_panel(safe)
    out["ui_manifest"] = build_dashboard_o4_ui_manifest(out)
    out["invariant_flags"] = OrderedDict([
        ("deterministic_only", True), ("read_only_ui", True), ("no_database_writes", True), ("no_network_calls", True),
        ("no_file_writes", True), ("no_new_intelligence_logic", True), ("no_trading_recommendations", True),
        ("no_target_prices", True), ("no_portfolio_allocation", True), ("no_backtesting", True),
        ("no_predictive_modelling", True), ("immutable_input_safe", True), ("streamlit_shell_only", True),
    ])
    return out


def _contains_forbidden_value_text(value: Any) -> bool:
    if isinstance(value, str):
        low = value.lower()
        return any(term in low for term in FORBIDDEN_TERMS)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_value_text(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_value_text(v) for v in value)
    return False


def validate_dashboard_o4_view_model(view_model: Mapping[str, Any]) -> OrderedDict:
    vm = deepcopy(dict(view_model))
    errors = []
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in vm:
            errors.append(f"missing top-level key: {key}")
    if _contains_forbidden_value_text(vm):
        errors.append("forbidden language detected")
    return OrderedDict([("validation_status", "valid" if not errors else "invalid"), ("error_count", len(errors)), ("errors", errors)])


__all__ = [
    "build_dashboard_o4_view_model",
    "build_dashboard_o4_page_registry",
    "build_dashboard_o4_filter_options",
    "build_dashboard_o4_kpi_cards",
    "build_dashboard_o4_entity_table",
    "build_dashboard_o4_subsector_table",
    "build_dashboard_o4_alert_table",
    "build_dashboard_o4_benchmark_table",
    "build_dashboard_o4_replay_table",
    "build_dashboard_o4_evidence_table",
    "build_dashboard_o4_certification_panel",
    "validate_dashboard_o4_view_model",
    "build_dashboard_o4_ui_manifest",
]
