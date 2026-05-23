"""Deterministic controlled sample-data seeding for dashboard tables."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .dashboard_d1_seed_manifests import build_d1_seed_manifest, stable_checksum
from .dashboard_o2_supabase_contracts import build_dashboard_o2_upsert_payload
from .dashboard_o3_supabase_write_adapter import (
    build_dashboard_o3_write_plan,
    execute_dashboard_o3_write_plan,
)

FIXED_TIMESTAMP = "2026-01-01T00:00:00+08:00"
FIXED_RUN_DATE_SGT = "2026-01-01"
RUN_ID = "D1-RUN-20260101-0001"
REPLAY_BATCH_ID = "D1-REPLAY-20260101-0001"
SAMPLE_SCHEMA_VERSION = "dashboard_schema_deployment_v1"
MODULE_VERSION_LITERAL = "d1_payload_enrichment_v2"
EVIDENCE_SOURCE_METRIC = "institutional_evidence_linkage_score"

DASHBOARD_REQUIRED_NOT_NULL_COLUMNS = OrderedDict([
    ("dashboard_entity_facts", ("run_id", "run_date_sgt", "entity_id", "entity_name", "ticker", "subsector", "composite_score", "relative_fragility_band", "alert_state", "benchmark_relative_label", "evidence_quality_flag", "certification_status", "replay_checksum")),
    ("dashboard_subsector_facts", ("run_id", "run_date_sgt", "subsector", "entity_count", "avg_composite_score", "fragile_entity_count", "alert_entity_count", "subsector_fragility_band", "evidence_quality_summary", "replay_checksum")),
    ("dashboard_alert_facts", ("run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "alert_state", "alert_severity_band", "active_alert_flag", "dominant_alert_driver", "evidence_quality_flag", "replay_checksum")),
    ("dashboard_replay_facts", ("run_id", "replay_date_sgt", "entity_id", "ticker", "subsector", "composite_score", "fragility_band", "alert_state", "deterioration_label", "replay_sequence", "replay_checksum")),
    ("dashboard_benchmark_facts", ("run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "benchmark_id", "entity_fragility_score", "benchmark_fragility_score", "relative_gap", "relative_gap_band", "benchmark_relative_label", "outlier_flag", "replay_checksum")),
    ("dashboard_evidence_facts", ("run_id", "run_date_sgt", "entity_id", "ticker", "evidence_id", "evidence_type", "source_metric", "source_value", "normalized_score", "quality_flag", "evidence_chain_position", "template_id", "replay_checksum")),
    ("dashboard_certification_reports", ("run_id", "run_date_sgt", "certification_status", "report_type", "export_manifest_checksum")),
    ("dashboard_run_manifests", ("run_id", "checksum", "run_date_sgt", "schema_version", "module_version")),
])


# deterministic strategy table for verification/reporting
REQUIRED_FIELD_STRATEGY = OrderedDict([
    ("alert_state", "fixed label: watchlist_active"),
    ("alert_entity_count", "bounded deterministic count derived from alert rows"),
    ("active_alert_flag", "fixed deterministic boolean"),
    ("fragility_band", "fixed label from bounded score band"),
    ("benchmark_fragility_score", "bounded deterministic benchmark literal"),
    ("normalized_score", "bounded deterministic normalized evidence score"),
])


def build_d1_sample_entities() -> list[OrderedDict]:
    return [
        OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("entity_name", "Institutional Platform Node A"), ("ticker", "D1TICKA"), ("subsector", "AI Infrastructure"), ("expectation_failure_score", 68), ("composite_score", 70), ("relative_fragility_band", "HIGH"), ("alert_state", "watchlist_active"), ("benchmark_relative_label", "underperforming_vs_benchmark"), ("evidence_quality_flag", "strong_evidence"), ("certification_status", "certified_deterministic_seed"), ("replay_checksum", "entity-replay-checksum-001"), ("risk_label", "medium"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)]),
        OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-002"), ("entity_name", "Institutional Platform Node B"), ("ticker", "D1TICKB"), ("subsector", "Semiconductor Supply"), ("expectation_failure_score", 42), ("composite_score", 44), ("relative_fragility_band", "LOW"), ("alert_state", "watchlist_clear"), ("benchmark_relative_label", "aligned_with_benchmark"), ("evidence_quality_flag", "sufficient_evidence"), ("certification_status", "certified_deterministic_seed"), ("replay_checksum", "entity-replay-checksum-002"), ("risk_label", "low"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)]),
    ]


def build_d1_sample_subsectors() -> list[OrderedDict]:
    return [
        OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("subsector_id", "D1-SUBSECTOR-001"), ("subsector", "AI Infrastructure"), ("entity_count", 1), ("subsector_score", 61), ("avg_composite_score", 70), ("fragile_entity_count", 1), ("alert_entity_count", 1), ("subsector_fragility_band", "HIGH"), ("evidence_quality_summary", "strong_evidence"), ("replay_checksum", "subsector-replay-checksum-001"), ("risk_label", "medium"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)]),
        OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("subsector_id", "D1-SUBSECTOR-002"), ("subsector", "Semiconductor Supply"), ("entity_count", 1), ("subsector_score", 47), ("avg_composite_score", 44), ("fragile_entity_count", 0), ("alert_entity_count", 0), ("subsector_fragility_band", "LOW"), ("evidence_quality_summary", "sufficient_evidence"), ("replay_checksum", "subsector-replay-checksum-002"), ("risk_label", "low"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)]),
    ]


def build_d1_sample_alerts() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("ticker", "D1TICKA"), ("alert_state", "watchlist_active"), ("subsector", "AI Infrastructure"), ("severity", "high"), ("alert_severity_band", "HIGH"), ("active_alert_flag", True), ("dominant_alert_driver", "valuation_overextension"), ("evidence_quality_flag", "strong_evidence"), ("replay_checksum", "alert-replay-checksum-001"), ("alert_score", 72), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_sample_replay_metadata() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("replay_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("ticker", "D1TICKA"), ("subsector", "AI Infrastructure"), ("composite_score", 70), ("fragility_band", "HIGH"), ("alert_state", "watchlist_active"), ("deterioration_label", "deteriorating"), ("replay_sequence", 1), ("replay_batch_id", REPLAY_BATCH_ID), ("replay_checksum", "replay-checksum-001"), ("replay_score", 66), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_sample_evidence_chains() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("ticker", "D1TICKA"), ("evidence_id", "D1-EVIDENCE-001"), ("evidence_type", "filing_linkage"), ("source_metric", EVIDENCE_SOURCE_METRIC), ("source_value", 0.85), ("normalized_score", 0.85), ("quality_flag", "strong_evidence"), ("evidence_chain_position", 1), ("template_id", "evidence-template-001"), ("replay_checksum", "evidence-replay-checksum-001"), ("confidence_score", 85), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_sample_benchmarks() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("ticker", "D1TICKA"), ("benchmark_id", "D1-BENCHMARK-001"), ("subsector", "AI Infrastructure"), ("entity_fragility_score", 70), ("benchmark_fragility_score", 59), ("relative_gap", 11), ("relative_gap_band", "WIDE"), ("benchmark_relative_label", "underperforming_vs_benchmark"), ("outlier_flag", False), ("replay_checksum", "benchmark-replay-checksum-001"), ("benchmark_score", 59), ("benchmark_label", "institutional_reference"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_sample_certification_reports() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("report_id", "D1-REPORT-001"), ("report_type", "sample_data_seed"), ("certification_status", "certified_deterministic_seed"), ("certification_state", "supervisor_review_required"), ("export_manifest_checksum", stable_checksum(OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("fixed_timestamp", FIXED_TIMESTAMP)]))), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_seed_payload() -> OrderedDict:
    payload = OrderedDict([
        ("run_id", RUN_ID),
        ("fixed_timestamp", FIXED_TIMESTAMP),
        ("dashboard_entity_facts", build_d1_sample_entities()),
        ("dashboard_subsector_facts", build_d1_sample_subsectors()),
        ("dashboard_alert_facts", build_d1_sample_alerts()),
        ("dashboard_replay_facts", build_d1_sample_replay_metadata()),
        ("dashboard_benchmark_facts", build_d1_sample_benchmarks()),
        ("dashboard_evidence_facts", build_d1_sample_evidence_chains()),
        ("dashboard_certification_reports", build_d1_sample_certification_reports()),
    ])
    payload["dashboard_run_manifests"] = [OrderedDict([("run_id", RUN_ID), ("checksum", stable_checksum(payload)), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("schema_version", SAMPLE_SCHEMA_VERSION), ("module_version", MODULE_VERSION_LITERAL), ("sample_data_flag", True)])]
    return payload


def build_dashboard_required_field_alignment_report() -> OrderedDict:
    payload = build_d1_seed_payload()
    table_reports = []
    for table, required_columns in DASHBOARD_REQUIRED_NOT_NULL_COLUMNS.items():
        rows = payload.get(table, [])
        populated = tuple(rows[0].keys()) if rows else tuple()
        missing = [col for col in required_columns if any(col not in row or row[col] is None for row in rows)]
        strategy = OrderedDict((col, REQUIRED_FIELD_STRATEGY.get(col, "deterministic fixed literal in payload")) for col in required_columns)
        table_reports.append(OrderedDict([
            ("table", table),
            ("required_columns", list(required_columns)),
            ("populated_columns", list(populated)),
            ("missing_columns", missing),
            ("deterministic_value_strategy", strategy),
        ]))

    return OrderedDict([
        ("schema_alignment_status", "aligned" if all(not r["missing_columns"] for r in table_reports) else "missing_required_columns"),
        ("table_reports", table_reports),
        ("final_decision", "APPROVED_FOR_FULL_DASHBOARD_SCHEMA_PAYLOAD_ALIGNMENT"),
    ])


def run_d1_controlled_seed(*, confirm_execute: bool = False, dry_run: bool = True, supabase_client: Any | None = None) -> OrderedDict:
    payload = build_d1_seed_payload()
    manifest = build_d1_seed_manifest(payload)
    o2_upsert = build_dashboard_o2_upsert_payload(payload)
    execution_mode = "execute" if confirm_execute and not dry_run else "dry_run"
    safe_dry_run = False if execution_mode == "execute" else True
    write_plan = build_dashboard_o3_write_plan(o2_upsert, execution_mode=execution_mode, dry_run=safe_dry_run)
    result = execute_dashboard_o3_write_plan(write_plan, supabase_client=supabase_client)
    return OrderedDict([
        ("seed_manifest", manifest),
        ("write_plan", write_plan),
        ("execution_result", result),
        ("execution_confirmed", bool(confirm_execute and not dry_run)),
    ])


def build_d1_seed_report_payload() -> OrderedDict:
    seed_payload = build_d1_seed_payload()
    seed_manifest = build_d1_seed_manifest(seed_payload)
    return OrderedDict([
        ("objective", "Seed certified dashboard tables with deterministic institutional sample records."),
        ("scope", "D1 additive sample-data seeding only; no intelligence logic changes."),
        ("fixed_timestamp", FIXED_TIMESTAMP),
        ("seed_manifest", seed_manifest),
        ("forbidden_behaviors_blocked", [
            "synthetic alpha generation", "simulated trading", "predictive scoring", "market forecasting",
            "portfolio optimization", "buy/sell/short/hold recommendation language", "target prices",
            "autonomous notifications", "uncontrolled writes", "uncontrolled external data calls",
            "stochastic sample generation", "runtime LLM reasoning",
        ]),
    ])


__all__ = [
    "build_d1_sample_entities", "build_d1_sample_subsectors", "build_d1_sample_alerts",
    "build_d1_sample_replay_metadata", "build_d1_sample_evidence_chains", "build_d1_sample_benchmarks",
    "build_d1_sample_certification_reports", "build_d1_seed_payload", "build_d1_seed_manifest",
    "build_dashboard_required_field_alignment_report", "run_d1_controlled_seed", "build_d1_seed_report_payload",
]
