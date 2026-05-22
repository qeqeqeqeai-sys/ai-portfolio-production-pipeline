"""Deterministic D1 guardrail contract freeze for controlled sample-data seeding."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

from .dashboard_d1_sample_data_seed import FIXED_TIMESTAMP
from .dashboard_d1_seed_manifests import SCHEMA_VERSION as D1_MANIFEST_SCHEMA_VERSION
from .dashboard_d1_seed_manifests import stable_checksum

D1_GUARDRAIL_SCHEMA_VERSION = "dashboard_d1_guardrail_contracts_v1"
D1_GUARDRAIL_MODULE_VERSION = "1.0.0"
APPROVED_DECISION = "APPROVED_FOR_D1_GUARDRAIL_CONTRACT_FREEZE"
D1_ID_NAMESPACE_PREFIXES = (
    "D1-RUN-",
    "D1-ENTITY-",
    "D1-SUBSECTOR-",
    "D1-ALERT-",
    "D1-REPLAY-",
    "D1-EVIDENCE-",
    "D1-BENCHMARK-",
    "D1-REPORT-",
)
D1_TABLE_INVENTORY = (
    "dashboard_entity_facts",
    "dashboard_subsector_facts",
    "dashboard_alert_facts",
    "dashboard_replay_facts",
    "dashboard_benchmark_facts",
    "dashboard_evidence_facts",
    "dashboard_report_metadata",
    "dashboard_export_manifest",
)
SCORE_FIELDS = (
    "expectation_failure_score",
    "subsector_score",
    "alert_score",
    "replay_score",
    "confidence_score",
    "benchmark_score",
)
ALLOWED_LABELS = OrderedDict([
    ("risk_label", ("low", "medium", "high")),
    ("severity", ("low", "medium", "high")),
])
FORBIDDEN_LANGUAGE = (
    "buy", "sell", "short", "hold", "target price", "price target",
    "portfolio optimization", "rebalance", "execute trade", "trade signal",
    "investment recommendation", "actionable signal",
)
ID_FIELDS = (
    "run_id", "entity_id", "subsector_id", "alert_state", "replay_sequence", "evidence_id", "benchmark_id", "report_id",
)


def build_d1_guardrail_inventory() -> OrderedDict:
    return OrderedDict([
        ("fixed_timestamp", FIXED_TIMESTAMP),
        ("id_namespace_prefixes", list(D1_ID_NAMESPACE_PREFIXES)),
        ("manifest_schema", D1_MANIFEST_SCHEMA_VERSION),
        ("checksum_method", "sha256(canonical_json_sort_keys_true)"),
        ("table_inventory_expectations", list(D1_TABLE_INVENTORY)),
        ("bounded_score_range", OrderedDict([("min", 0), ("max", 100)])),
        ("allowed_labels", deepcopy(ALLOWED_LABELS)),
        ("required_sample_data_flag", True),
        ("forbidden_language_inventory", list(FORBIDDEN_LANGUAGE)),
        ("dry_run_default_policy", True),
        ("explicit_execution_confirmation_policy", "confirm_execute_true_and_dry_run_false_required"),
        ("o3_only_controlled_persistence_policy", True),
        ("no_dashboard_write_path_expansion", True),
        ("no_predictive_actionable_synthetic_behavior", True),
        ("immutable_input_safety", True),
    ])


def _is_allowed_id(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(D1_ID_NAMESPACE_PREFIXES)


def validate_d1_seed_payload_against_guardrails(seed_payload: Mapping[str, Any]) -> OrderedDict:
    materialized = deepcopy(dict(seed_payload))
    violations: list[str] = []
    if materialized.get("fixed_timestamp") != FIXED_TIMESTAMP:
        violations.append("fixed_timestamp_mismatch")

    for table_name in D1_TABLE_INVENTORY:
        if table_name not in materialized:
            violations.append(f"missing_table:{table_name}")

    for table_name in D1_TABLE_INVENTORY:
        for record in materialized.get(table_name, []):
            if isinstance(record, Mapping):
                if record.get("sample_data_flag") is not True:
                    violations.append(f"sample_data_flag_missing:{table_name}")
                if record.get("as_of_sgt") is not None and record.get("as_of_sgt") != FIXED_TIMESTAMP:
                    violations.append(f"timestamp_mismatch:{table_name}")
                for field in SCORE_FIELDS:
                    if field in record and not (0 <= record[field] <= 100):
                        violations.append(f"score_out_of_range:{table_name}:{field}")
                for label_field, allowed in ALLOWED_LABELS.items():
                    if label_field in record and record[label_field] not in allowed:
                        violations.append(f"label_not_allowed:{table_name}:{label_field}")
                for id_field in ID_FIELDS:
                    if id_field in record and not _is_allowed_id(record[id_field]):
                        violations.append(f"id_namespace_violation:{table_name}:{id_field}")
                lowered = str(record).lower()
                if any(term in lowered for term in FORBIDDEN_LANGUAGE):
                    violations.append(f"forbidden_language:{table_name}")

    return OrderedDict([
        ("valid", len(violations) == 0),
        ("violation_count", len(violations)),
        ("violations", sorted(set(violations))),
    ])


def build_d1_guardrail_contract() -> OrderedDict:
    inventory = build_d1_guardrail_inventory()
    contract = OrderedDict([
        ("schema_version", D1_GUARDRAIL_SCHEMA_VERSION),
        ("module_version", D1_GUARDRAIL_MODULE_VERSION),
        ("guardrail_inventory", inventory),
        ("policy_flags", OrderedDict([
            ("deterministic_only", True),
            ("additive_only", True),
            ("no_runtime_database_writes", True),
            ("no_network_calls", True),
            ("no_random_generation", True),
            ("no_uuid_generation", True),
            ("no_datetime_now_usage", True),
            ("no_llm_reasoning", True),
        ])),
    ])
    contract["contract_checksum"] = stable_checksum(contract)
    return contract


def build_d1_guardrail_manifest() -> OrderedDict:
    contract = build_d1_guardrail_contract()
    manifest = OrderedDict([
        ("schema_version", "dashboard_d1_guardrail_manifest_v1"),
        ("contract_schema_version", contract["schema_version"]),
        ("deterministic_table_order", list(D1_TABLE_INVENTORY)),
        ("checksum_method", "sha256"),
        ("contract_checksum", contract["contract_checksum"]),
    ])
    manifest["manifest_checksum"] = stable_checksum(manifest)
    return manifest


def build_d1_guardrail_certification() -> OrderedDict:
    contract = build_d1_guardrail_contract()
    manifest = build_d1_guardrail_manifest()
    return OrderedDict([
        ("schema_version", "dashboard_d1_guardrail_certification_v1"),
        ("contract_checksum", contract["contract_checksum"]),
        ("manifest_checksum", manifest["manifest_checksum"]),
        ("supervisor_decision", APPROVED_DECISION),
        ("status", "certified"),
    ])


def build_d1_guardrail_report_payload() -> OrderedDict:
    return OrderedDict([
        ("objective", "Freeze and certify deterministic D1 sample-data guardrails as enforceable contracts."),
        ("scope", "D1 guardrail contract freeze only; additive enforcement layer."),
        ("non_goals", ["new intelligence", "new dashboard functionality", "new sample-data generation"]),
        ("frozen_guardrails", build_d1_guardrail_inventory()),
        ("validation_rules", ["scores_0_to_100", "sample_data_flag_required", "fixed_timestamp_required", "namespace_prefix_required", "allowed_label_inventory_only", "forbidden_language_absent"]),
        ("forbidden_behaviors", ["predictive_modeling", "investment_recommendations", "target_prices", "portfolio_optimization", "autonomous_notifications", "trade_execution", "dashboard_ui_mutation"]),
        ("deterministic_guarantees", ["stable_ordering", "stable_checksum", "immutable_input_validation"]),
        ("safety_boundaries", ["dry_run_default", "explicit_execution_confirmation", "o3_only_controlled_persistence", "no_dashboard_write_path_expansion"]),
        ("test_coverage", ["api_exports", "determinism", "checksum", "validation_contracts", "non_regression_smokes"]),
        ("supervisor_decision", APPROVED_DECISION),
    ])


__all__ = [
    "build_d1_guardrail_inventory",
    "build_d1_guardrail_contract",
    "validate_d1_seed_payload_against_guardrails",
    "build_d1_guardrail_manifest",
    "build_d1_guardrail_certification",
    "build_d1_guardrail_report_payload",
]
