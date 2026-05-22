"""Deterministic manifest builders for Dashboard D1 sample-data seeding."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "dashboard_d1_seed_manifest_v1"
MODULE_VERSION = "1.0.0"


def canonical_json_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_checksum(payload: Any) -> str:
    return hashlib.sha256(canonical_json_dumps(payload).encode("utf-8")).hexdigest()


def build_d1_seed_manifest(seed_payload: Mapping[str, Any]) -> OrderedDict:
    materialized = deepcopy(dict(seed_payload))
    table_counts = OrderedDict([
        ("dashboard_entity_facts", len(materialized.get("dashboard_entity_facts", []))),
        ("dashboard_subsector_facts", len(materialized.get("dashboard_subsector_facts", []))),
        ("dashboard_alert_facts", len(materialized.get("dashboard_alert_facts", []))),
        ("dashboard_replay_facts", len(materialized.get("dashboard_replay_facts", []))),
        ("dashboard_benchmark_facts", len(materialized.get("dashboard_benchmark_facts", []))),
        ("dashboard_evidence_facts", len(materialized.get("dashboard_evidence_facts", []))),
        ("dashboard_report_metadata", len(materialized.get("dashboard_report_metadata", []))),
    ])
    manifest = OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("run_id", materialized.get("run_id", "D1-RUN-20260101-0001")),
        ("fixed_timestamp", materialized.get("fixed_timestamp", "2026-01-01T00:00:00+08:00")),
        ("table_counts", table_counts),
        ("total_records", sum(table_counts.values())),
        ("deterministic_table_order", list(table_counts.keys())),
        ("invariant_flags", OrderedDict([
            ("deterministic_only", True),
            ("dry_run_default", True),
            ("immutable_input_safe", True),
            ("additive_only", True),
            ("controlled_adapter_only", True),
            ("no_network_calls", True),
            ("no_raw_supabase_client", True),
        ])),
    ])
    manifest["checksum"] = stable_checksum(manifest)
    return manifest


__all__ = ["canonical_json_dumps", "stable_checksum", "build_d1_seed_manifest"]
