from __future__ import annotations

from collections import OrderedDict
from typing import Any, Mapping

from transmission_layers.expectation_failure.dashboard_operationalization.o7_dashboard_persistence_adapter import (
    build_o7_persistence_table_contract,
    build_o7_write_batch_plan,
)
from transmission_layers.expectation_failure.expectation_intelligence.d8_b2r_replay_candidate_source_repair_audit import (
    _safe_table_rows,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    D7_PHYSICAL_COLUMNS_BY_TABLE,
    build_d7_historical_runs_from_integrity,
)

STATUSES = {
    "OPERATIONAL": "REPLAY_PERSISTENCE_OPERATIONAL",
    "DISABLED": "REPLAY_PERSISTENCE_DISABLED",
    "DRY_RUN_BLOCKED": "REPLAY_PERSISTENCE_DRY_RUN_BLOCKED",
    "EMPTY_OUTPUT": "REPLAY_PERSISTENCE_EMPTY_OUTPUT",
    "SHAPE_INVALID": "REPLAY_PERSISTENCE_SHAPE_INVALID",
    "NOT_WIRED": "REPLAY_PERSISTENCE_NOT_WIRED",
    "READY_FOR_SEEDING": "REPLAY_PERSISTENCE_READY_FOR_SEEDING",
}

APPROVED_TABLES = ("dashboard_replay_metadata_records", "dashboard_export_manifests")

def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []

def _txt(v: Any) -> str:
    return str(v).strip() if v is not None else ""

def audit_replay_persistence_pipeline() -> OrderedDict[str, Any]:
    contract = build_o7_persistence_table_contract()
    approved = set(_as_list(contract.get("approved_tables")))
    missing = [t for t in APPROVED_TABLES if t not in approved]
    return OrderedDict([
        ("producer_modules", [
            "dashboard_operationalization.o7_dashboard_persistence_adapter",
            "dashboard_operationalization.d3_controlled_dashboard_persistence_execution",
            "dashboard_operationalization.d6_operational_proving_cycle",
        ]),
        ("approved_target_tables", sorted(approved)),
        ("required_replay_tables", list(APPROVED_TABLES)),
        ("is_wired", not missing),
        ("missing_tables", missing),
    ])

def audit_replay_manifest_generation(*, o6_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    plan = build_o7_write_batch_plan(o6_payload or {})
    batches = [b for b in _as_list(plan.get("batches")) if isinstance(b, Mapping)]
    manifest = next((b for b in batches if b.get("target_table") == "dashboard_export_manifests"), {})
    replay = next((b for b in batches if b.get("target_table") == "dashboard_replay_metadata_records"), {})
    return OrderedDict([
        ("plan_checksum", _txt(plan.get("plan_checksum"))),
        ("manifest_batch_present", bool(manifest)),
        ("replay_batch_present", bool(replay)),
        ("manifest_payload_count", int(manifest.get("record_count") or 0)),
        ("replay_payload_count", int(replay.get("record_count") or 0)),
    ])

def audit_replay_record_production(*, client: Any, findings: list[Mapping[str, Any]] | None = None, narratives: list[Mapping[str, Any]] | None = None, evidence_maps: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    replay_payload = _safe_table_rows(client, "dashboard_replay_metadata_records", D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_replay_metadata_records"])
    manifest_payload = _safe_table_rows(client, "dashboard_export_manifests", D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_export_manifests"])
    history = build_d7_historical_runs_from_integrity(
        replay_rows=_as_list(replay_payload.get("rows")), findings=_as_list(findings), narratives=_as_list(narratives), evidence_maps=_as_list(evidence_maps)
    )
    completeness_missing = []
    for row in _as_list(replay_payload.get("rows")):
        if not isinstance(row, Mapping):
            continue
        if not _txt(row.get("record_id")):
            completeness_missing.append("missing_record_id")
        if not (_txt(row.get("replay_checksum")) or _txt(row.get("source_payload_checksum"))):
            completeness_missing.append("missing_checksum_lineage")
    return OrderedDict([
        ("replay_table_state", _txt(replay_payload.get("status"))),
        ("manifest_table_state", _txt(manifest_payload.get("status"))),
        ("replay_payload_count", int(replay_payload.get("row_count") or 0)),
        ("manifest_payload_count", int(manifest_payload.get("row_count") or 0)),
        ("candidate_inventory_potential", len([h for h in history if isinstance(h, Mapping)])),
        ("deterministic_checksum_lineage_present", not completeness_missing),
        ("replay_payload_rejection_reasons", sorted(set(completeness_missing))),
        ("table_diagnostics", OrderedDict([("replay", replay_payload), ("manifest", manifest_payload)])),
    ])

def audit_replay_persistence_gates(*, dry_run: bool = True, persistence_enabled: bool = True, client_resolved: bool = True) -> OrderedDict[str, Any]:
    blocked = []
    if not persistence_enabled:
        blocked.append("persistence_disabled")
    if dry_run:
        blocked.append("dry_run_no_write_gate")
    if not client_resolved:
        blocked.append("client_not_resolved")
    return OrderedDict([
        ("persistence_enabled", persistence_enabled),
        ("dry_run", dry_run),
        ("client_resolved", client_resolved),
        ("blocked_reasons", blocked),
    ])

def build_d8_b3_replay_activation_report_payload(*, client: Any = None, o6_payload: Mapping[str, Any] | None = None, findings: list[Mapping[str, Any]] | None = None, narratives: list[Mapping[str, Any]] | None = None, evidence_maps: list[Mapping[str, Any]] | None = None, dry_run: bool = True, persistence_enabled: bool = True) -> OrderedDict[str, Any]:
    pipeline = audit_replay_persistence_pipeline()
    manifest = audit_replay_manifest_generation(o6_payload=o6_payload)
    production = audit_replay_record_production(client=client, findings=findings, narratives=narratives, evidence_maps=evidence_maps)
    gates = audit_replay_persistence_gates(dry_run=dry_run, persistence_enabled=persistence_enabled, client_resolved=client is not None)
    preview = OrderedDict([
        ("replay_inventory_generation_preview_count", int(manifest.get("replay_payload_count") or 0)),
        ("manifest_generation_preview_count", int(manifest.get("manifest_payload_count") or 0)),
        ("expected_insert_count", int(manifest.get("replay_payload_count") or 0) + int(manifest.get("manifest_payload_count") or 0)),
        ("duplicate_detection_supported", True),
        ("no_write_confirmation", bool(dry_run)),
    ])
    if not pipeline.get("is_wired"):
        status = STATUSES["NOT_WIRED"]
    elif not persistence_enabled:
        status = STATUSES["DISABLED"]
    elif int(production.get("replay_payload_count") or 0) == 0 and int(manifest.get("replay_payload_count") or 0) == 0:
        status = STATUSES["EMPTY_OUTPUT"]
    elif bool(production.get("replay_payload_rejection_reasons")):
        status = STATUSES["SHAPE_INVALID"]
    elif dry_run:
        status = STATUSES["DRY_RUN_BLOCKED"]
    else:
        status = STATUSES["READY_FOR_SEEDING"]
    return OrderedDict([
        ("status", status),
        ("pipeline", pipeline),
        ("manifest_generation", manifest),
        ("record_production", production),
        ("persistence_gates", gates),
        ("dry_run_seeding_preview", preview),
    ])

