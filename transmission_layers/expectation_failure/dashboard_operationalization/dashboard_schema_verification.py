"""Deterministic dashboard schema deployment inventory and verification manifest helpers."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any

SCHEMA_VERSION = "dashboard_schema_deployment_v1"
MODULE_VERSION = "1.0.0"

_EXPECTED_COLUMNS = OrderedDict([
    ("dashboard_entity_facts", ["run_id", "run_date_sgt", "entity_id", "entity_name", "ticker", "subsector", "composite_score", "relative_fragility_band", "alert_state", "benchmark_relative_label", "evidence_quality_flag", "certification_status", "replay_checksum"]),
    ("dashboard_subsector_facts", ["run_id", "run_date_sgt", "subsector", "entity_count", "avg_composite_score", "fragile_entity_count", "alert_entity_count", "subsector_fragility_band", "evidence_quality_summary", "replay_checksum"]),
    ("dashboard_alert_facts", ["run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "alert_state", "alert_severity_band", "active_alert_flag", "dominant_alert_driver", "evidence_quality_flag", "replay_checksum"]),
    ("dashboard_replay_facts", ["run_id", "replay_date_sgt", "entity_id", "ticker", "subsector", "composite_score", "fragility_band", "alert_state", "deterioration_label", "replay_sequence", "replay_checksum"]),
    ("dashboard_benchmark_facts", ["run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "benchmark_id", "entity_fragility_score", "benchmark_fragility_score", "relative_gap", "relative_gap_band", "benchmark_relative_label", "outlier_flag", "replay_checksum"]),
    ("dashboard_evidence_facts", ["run_id", "run_date_sgt", "entity_id", "ticker", "evidence_id", "evidence_type", "source_metric", "source_value", "normalized_score", "quality_flag", "evidence_chain_position", "template_id", "replay_checksum"]),
    ("dashboard_certification_reports", ["run_id", "run_date_sgt", "certification_status", "report_type", "export_manifest_checksum"]),
    ("dashboard_run_manifests", ["run_id", "checksum", "run_date_sgt", "schema_version", "module_version"]),
])


def _stable_checksum(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_dashboard_expected_table_inventory() -> list[str]:
    return list(_EXPECTED_COLUMNS.keys())


def build_dashboard_expected_column_inventory() -> OrderedDict:
    return OrderedDict((table, list(columns)) for table, columns in _EXPECTED_COLUMNS.items())


def build_dashboard_schema_deployment_manifest() -> OrderedDict:
    column_inventory = build_dashboard_expected_column_inventory()
    table_inventory = list(column_inventory.keys())
    manifest = OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("table_inventory", table_inventory),
        ("column_inventory", column_inventory),
        ("table_count", len(table_inventory)),
        ("column_count", sum(len(cols) for cols in column_inventory.values())),
        ("invariant_flags", OrderedDict([
            ("deterministic_only", True),
            ("schema_support_only", True),
            ("additive_only", True),
            ("no_runtime_network_calls", True),
            ("no_database_mutation", True),
        ])),
    ])
    manifest["checksum"] = _stable_checksum(manifest)
    return manifest


def build_dashboard_schema_verification_report_payload() -> OrderedDict:
    manifest = build_dashboard_schema_deployment_manifest()
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("objective", "Schema/deployment support for dashboard Supabase read path (O4/O6)."),
        ("expected_table_inventory", manifest["table_inventory"]),
        ("expected_column_inventory", deepcopy(manifest["column_inventory"])),
        ("deployment_manifest", manifest),
        ("safety_boundaries", [
            "no intelligence/scoring logic changes",
            "no dashboard behavior changes",
            "no uncontrolled writes",
            "read-only dashboard boundary preserved",
        ]),
        ("final_decision", "APPROVED_FOR_DASHBOARD_SCHEMA_DEPLOYMENT_ARTIFACTS"),
    ])


__all__ = [
    "build_dashboard_expected_table_inventory",
    "build_dashboard_expected_column_inventory",
    "build_dashboard_schema_deployment_manifest",
    "build_dashboard_schema_verification_report_payload",
]
