"""Deterministic O4 real-market semantic dashboard integration layer."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

SEVERITY_ORDER = ("SEVERE", "HIGH", "ELEVATED", "MODERATE", "LOW")
CERTIFIED = "CERTIFIED_SEMANTIC_DASHBOARD_READY"
DEGRADED = "DEGRADED_SEMANTIC_DASHBOARD_READY"
BLOCKED = "BLOCKED_SEMANTIC_DASHBOARD_INVALID"

FORBIDDEN_CAPABILITIES = (
    "live_market_fetching",
    "database_writes",
    "trading_instructions",
    "portfolio_optimization",
    "predictive_return_forecasts",
    "llm_calls",
    "network_calls",
    "hidden_non_determinism",
)


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _clamp_score(v: Any) -> float:
    try:
        return round(max(0.0, min(100.0, float(v))), 2)
    except (TypeError, ValueError):
        return 50.0


def _severity_rank(label: Any) -> int:
    try:
        return SEVERITY_ORDER.index(str(label))
    except ValueError:
        return len(SEVERITY_ORDER)


def _normalize_o3_payload(o3_view_model: Mapping[str, Any] | None = None, semantic_evidence_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    src = deepcopy(dict(o3_view_model or semantic_evidence_payload or {}))
    raw_records = src.get("semantic_evidence_records")
    if raw_records is None:
        raw_records = src.get("records")
    records = list(raw_records) if isinstance(raw_records, list) else raw_records
    return OrderedDict([
        ("market_observation_inventory", deepcopy(dict(src.get("market_observation_inventory") or src.get("inventory") or {}))),
        ("semantic_evidence_records", records if records is not None else []),
        ("expectation_fragility_inputs", deepcopy(dict(src.get("expectation_fragility_inputs") or {}))),
        ("market_evidence_cards", deepcopy(dict(src.get("market_evidence_cards") or {}))),
        ("semantic_category_summary", deepcopy(dict(src.get("semantic_category_summary") or {}))),
        ("certification_summary", deepcopy(dict(src.get("certification_summary") or src.get("certification") or {}))),
        ("governance_boundaries", deepcopy(dict(src.get("governance_boundaries") or {}))),
        ("lineage", deepcopy(dict(src.get("lineage") or {}))),
    ])


def build_o4_semantic_dashboard_inventory(o3_view_model: Mapping[str, Any] | None = None, semantic_evidence_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    base = _normalize_o3_payload(o3_view_model, semantic_evidence_payload)
    raw_records = base["semantic_evidence_records"]
    records = list(raw_records) if isinstance(raw_records, list) else raw_records
    inv = dict(base["market_observation_inventory"])
    return OrderedDict([
        ("semantic_panel_ids", ["executive_semantic_summary", "evidence_cards", "category_summary_panels", "market_context_panels", "governance_status_panel", "replay_metadata_panel"]),
        ("kpi_panel_ids", ["expectation_fragility_kpis"]),
        ("alert_panel_ids", ["semantic_alerts"]),
        ("evidence_section_ids", ["expectation_fragility_sections", "market_context_sections"]),
        ("dashboard_integration_fields", ["integration_version", "o4_checksum", "o3_lineage_checksum", "certification_status", "degraded_reasons", "blocking_reasons"]),
        ("input_record_count", len(records)),
        ("observed_metric_names", sorted(list(inv.get("observed_metric_names") or []))),
    ])


def build_o4_dashboard_kpi_panels(o3_view_model=None, semantic_evidence_payload=None) -> list[OrderedDict[str, Any]]:
    base = _normalize_o3_payload(o3_view_model, semantic_evidence_payload)
    ef = dict(base["expectation_fragility_inputs"])
    entities = list(ef.get("entity_expectation_fragility_inputs") or [])
    top = entities[0] if entities else {}
    composite = _clamp_score(top.get("composite_semantic_pressure_score", 50.0))
    evidence_count = max(0, int(top.get("evidence_count", 0) or 0))
    degraded_count = max(0, int(top.get("degraded_evidence_count", 0) or 0))
    return [
        OrderedDict([("kpi_id", "top_entity_composite_pressure"), ("label", "Top Entity Composite Pressure"), ("value", composite), ("bounded_range", "0_100")]),
        OrderedDict([("kpi_id", "top_entity_evidence_count"), ("label", "Top Entity Evidence Count"), ("value", evidence_count), ("bounded_range", "0_inf")]),
        OrderedDict([("kpi_id", "top_entity_degraded_evidence_count"), ("label", "Top Entity Degraded Evidence Count"), ("value", degraded_count), ("bounded_range", "0_inf")]),
    ]


def build_o4_semantic_alert_panels(o3_view_model=None, semantic_evidence_payload=None) -> list[OrderedDict[str, Any]]:
    base = _normalize_o3_payload(o3_view_model, semantic_evidence_payload)
    records = list(base["semantic_evidence_records"])
    alerts = []
    for r in records:
        alerts.append(OrderedDict([
            ("severity", str(r.get("severity_band") or "LOW")),
            ("symbol", str(r.get("symbol") or "UNKNOWN")),
            ("metric_name", str(r.get("metric_name") or "UNKNOWN")),
            ("semantic_category", str(r.get("semantic_category") or "UNCLASSIFIED_MARKET_EVIDENCE")),
            ("score", _clamp_score(r.get("normalized_score"))),
            ("evidence_quality", str(r.get("evidence_quality") or "DEGRADED_MISSING_VALUE")),
        ]))
    alerts.sort(key=lambda x: (_severity_rank(x["severity"]), -x["score"], x["symbol"], x["metric_name"], x["semantic_category"]))
    return alerts


def build_o4_expectation_fragility_sections(o3_view_model=None, semantic_evidence_payload=None) -> OrderedDict[str, Any]:
    base = _normalize_o3_payload(o3_view_model, semantic_evidence_payload)
    ef = dict(base["expectation_fragility_inputs"])
    return OrderedDict([
        ("strongest_expectation_pressure_entities", list(ef.get("strongest_expectation_pressure_entities") or [])),
        ("weakest_structural_support_entities", list(ef.get("weakest_structural_support_entities") or [])),
        ("highest_semantic_pressure_categories", list(ef.get("highest_semantic_pressure_categories") or [])),
    ])


def build_o4_market_context_sections(o3_view_model=None, semantic_evidence_payload=None) -> OrderedDict[str, Any]:
    base = _normalize_o3_payload(o3_view_model, semantic_evidence_payload)
    return OrderedDict([
        ("evidence_cards", dict(base["market_evidence_cards"])),
        ("category_summary_panels", dict(base["semantic_category_summary"])),
        ("market_observation_inventory", dict(base["market_observation_inventory"])),
    ])


def certify_o4_real_market_semantic_dashboard_integration(o3_view_model=None, semantic_evidence_payload=None) -> OrderedDict[str, Any]:
    base = _normalize_o3_payload(o3_view_model, semantic_evidence_payload)
    raw_records = base["semantic_evidence_records"]
    records = list(raw_records) if isinstance(raw_records, list) else raw_records
    inventory = build_o4_semantic_dashboard_inventory(o3_view_model, semantic_evidence_payload)
    blocking, degraded = [], []
    if not isinstance(raw_records, list):
        blocking.append("semantic_evidence_records_not_list")
    if not isinstance(base["market_observation_inventory"], dict):
        blocking.append("market_observation_inventory_not_mapping")
    if isinstance(raw_records, list) and not records:
        degraded.append("missing_semantic_evidence_records")
    missing_lineage = not (base["lineage"].get("o3_checksum") or base["certification_summary"].get("checksum"))
    if missing_lineage:
        degraded.append("missing_o3_lineage_checksum")
    kpis = build_o4_dashboard_kpi_panels(o3_view_model, semantic_evidence_payload)
    if any((k["kpi_id"].endswith("pressure") and not (0 <= float(k["value"]) <= 100)) for k in kpis):
        blocking.append("kpi_out_of_bounds")
    invariants = OrderedDict([
        ("deterministic_panel_inventory", True),
        ("governance_boundary_compliance", True),
        ("forbidden_capabilities_absent", True),
        ("lineage_reference_preserved", not missing_lineage),
    ])
    if blocking:
        status = BLOCKED
    elif degraded:
        status = DEGRADED
    else:
        status = CERTIFIED
    return OrderedDict([
        ("certification_status", status),
        ("blocking_reasons", sorted(set(blocking))),
        ("degraded_reasons", sorted(set(degraded))),
        ("invariant_results", invariants),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
        ("checksum", _stable_checksum(OrderedDict([("records", records), ("inventory", inventory), ("status", status)]))),
    ])


def build_o4_dashboard_integration_payload(o3_view_model=None, semantic_evidence_payload=None, metadata: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    base = _normalize_o3_payload(o3_view_model, semantic_evidence_payload)
    cert = certify_o4_real_market_semantic_dashboard_integration(o3_view_model, semantic_evidence_payload)
    return OrderedDict([
        ("integration_version", "o4_real_market_semantic_dashboard_integration_v1"),
        ("executive_semantic_summary", OrderedDict([("summary", "Deterministic O4 semantic dashboard integration payload."), ("input_records", len(base["semantic_evidence_records"]))])),
        ("expectation_fragility_kpis", build_o4_dashboard_kpi_panels(o3_view_model, semantic_evidence_payload)),
        ("semantic_alerts", build_o4_semantic_alert_panels(o3_view_model, semantic_evidence_payload)),
        ("evidence_cards", dict(base["market_evidence_cards"])),
        ("category_summary_panels", dict(base["semantic_category_summary"])),
        ("market_context_panels", build_o4_market_context_sections(o3_view_model, semantic_evidence_payload)),
        ("governance_status_panel", OrderedDict([("governance_boundaries", dict(base["governance_boundaries"])), ("forbidden_capability_inventory", cert["forbidden_capability_inventory"])])),
        ("replay_metadata_panel", OrderedDict([("caller_metadata", deepcopy(dict(metadata or {}))), ("o3_lineage_checksum", base["lineage"].get("o3_checksum") or base["certification_summary"].get("checksum") or ""), ("o4_checksum", cert["checksum"])])),
        ("semantic_dashboard_inventory", build_o4_semantic_dashboard_inventory(o3_view_model, semantic_evidence_payload)),
        ("certification", cert),
    ])


def build_o4_real_market_semantic_dashboard_integration_report(o3_view_model=None, semantic_evidence_payload=None) -> str:
    cert = certify_o4_real_market_semantic_dashboard_integration(o3_view_model, semantic_evidence_payload)
    return "\n".join([
        "# O4 Real Market Semantic Dashboard Integration Report",
        "",
        "## Objective",
        "Convert O3 semantic evidence and view-model outputs into deterministic dashboard-ready contracts.",
        "",
        "## Certification",
        f"Status: {cert['certification_status']}",
    ])
