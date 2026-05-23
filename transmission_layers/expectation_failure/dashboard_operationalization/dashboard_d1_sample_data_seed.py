"""Deterministic controlled sample-data seeding for dashboard tables."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

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
SEVERITY_LABELS = ("low", "medium", "high")
SAMPLE_SCHEMA_VERSION = "dashboard_schema_deployment_v1"


def build_d1_sample_entities() -> list[OrderedDict]:
    return [
        OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("entity_name", "Institutional Platform Node A"), ("ticker", "D1TICKA"), ("subsector", "AI Infrastructure"), ("expectation_failure_score", 68), ("risk_label", "medium"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)]),
        OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-002"), ("entity_name", "Institutional Platform Node B"), ("ticker", "D1TICKB"), ("subsector", "Semiconductor Supply"), ("expectation_failure_score", 42), ("risk_label", "low"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)]),
    ]


def build_d1_sample_subsectors() -> list[OrderedDict]:
    return [
        OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("subsector_id", "D1-SUBSECTOR-001"), ("subsector", "AI Infrastructure"), ("entity_count", 1), ("subsector_score", 61), ("risk_label", "medium"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)]),
        OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("subsector_id", "D1-SUBSECTOR-002"), ("subsector", "Semiconductor Supply"), ("entity_count", 1), ("subsector_score", 47), ("risk_label", "low"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)]),
    ]


def build_d1_sample_alerts() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("ticker", "D1TICKA"), ("alert_state", "D1-ALERT-001"), ("severity", "high"), ("alert_score", 72), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_sample_replay_metadata() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("replay_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("ticker", "D1TICKA"), ("replay_sequence", 1), ("replay_batch_id", REPLAY_BATCH_ID), ("replay_score", 66), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_sample_evidence_chains() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("ticker", "D1TICKA"), ("evidence_id", "D1-EVIDENCE-001"), ("evidence_type", "filing_linkage"), ("confidence_score", 85), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_sample_benchmarks() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("entity_id", "D1-ENTITY-001"), ("ticker", "D1TICKA"), ("benchmark_id", "D1-BENCHMARK-001"), ("benchmark_score", 59), ("benchmark_label", "institutional_reference"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


def build_d1_sample_certification_reports() -> list[OrderedDict]:
    return [OrderedDict([("run_id", RUN_ID), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("report_id", "D1-REPORT-001"), ("report_type", "sample_data_seed"), ("certification_status", "certified_deterministic_seed"), ("certification_state", "supervisor_review_required"), ("as_of_sgt", FIXED_TIMESTAMP), ("sample_data_flag", True)])]


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
    payload["dashboard_run_manifests"] = [OrderedDict([("run_id", RUN_ID), ("checksum", stable_checksum(payload)), ("run_date_sgt", FIXED_RUN_DATE_SGT), ("schema_version", SAMPLE_SCHEMA_VERSION), ("sample_data_flag", True)])]
    return payload


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
    "run_d1_controlled_seed", "build_d1_seed_report_payload",
]
