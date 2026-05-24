from __future__ import annotations

from collections import OrderedDict
from typing import Any, Mapping

APPROVED_REPLAY_TABLE = "dashboard_replay_metadata_records"
APPROVED_MANIFEST_TABLE = "dashboard_export_manifests"
APPROVED_TABLES = (APPROVED_REPLAY_TABLE, APPROVED_MANIFEST_TABLE)


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted({v for v in values if _text(v)})


def _read_table(client: Any, table_name: str) -> list[Mapping[str, Any]]:
    response = client.table(table_name).select("*").execute()
    rows = _as_list(getattr(response, "data", []) or [])
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def build_d8c_persisted_readback_inventory(*, client: Any = None, replay_rows: list[Mapping[str, Any]] | None = None, manifest_rows: list[Mapping[str, Any]] | None = None, latest_window: int = 5) -> OrderedDict[str, Any]:
    if replay_rows is None and client is not None:
        replay_rows = _read_table(client, APPROVED_REPLAY_TABLE)
    if manifest_rows is None and client is not None:
        manifest_rows = _read_table(client, APPROVED_MANIFEST_TABLE)
    replay_copy = [dict(r) for r in _as_list(replay_rows)]
    manifest_copy = [dict(r) for r in _as_list(manifest_rows)]

    replay_ids = _sorted_unique([_text(r.get("replay_id") or r.get("record_id")) for r in replay_copy if isinstance(r, Mapping)])
    manifest_checksums = _sorted_unique([_text(r.get("export_checksum") or r.get("manifest_checksum")) for r in manifest_copy if isinstance(r, Mapping)])
    status = "READBACK_OK" if replay_copy or manifest_copy else "READBACK_EMPTY"

    return OrderedDict([
        ("replay_row_count", len(replay_copy)),
        ("manifest_row_count", len(manifest_copy)),
        ("replay_ids", replay_ids),
        ("manifest_checksums", manifest_checksums),
        ("latest_replay_ids", replay_ids[-max(1, int(latest_window)):]),
        ("latest_manifest_checksums", manifest_checksums[-max(1, int(latest_window)):]),
        ("approved_tables", list(APPROVED_TABLES)),
        ("readback_status", status),
    ])


def validate_d8c_replay_manifest_lineage(*, replay_rows: list[Mapping[str, Any]] | None = None, manifest_rows: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    replay_copy = [dict(r) for r in _as_list(replay_rows)]
    manifest_copy = [dict(r) for r in _as_list(manifest_rows)]
    blocking: list[str] = []
    degraded: list[str] = []

    if not replay_copy:
        blocking.append("missing_replay_rows")
    if not manifest_copy:
        blocking.append("missing_manifest_rows")

    replay_ids = [_text(r.get("replay_id") or r.get("record_id")) for r in replay_copy]
    if replay_copy and any(not rid for rid in replay_ids):
        degraded.append("empty_replay_id_detected")

    lineage_present = bool(replay_copy) and all(_text(r.get("source_payload_checksum") or r.get("replay_checksum") or r.get("export_checksum")) for r in replay_copy)
    if replay_copy and not lineage_present:
        degraded.append("missing_replay_checksum_lineage")

    manifest_present = bool(manifest_copy) and all(_text(r.get("export_checksum") or r.get("manifest_checksum")) for r in manifest_copy)
    if manifest_copy and not manifest_present:
        degraded.append("missing_manifest_checksum")

    if replay_copy and any(not bool(r) for r in replay_copy):
        degraded.append("malformed_empty_replay_payload")
    if manifest_copy and any(not bool(r) for r in manifest_copy):
        degraded.append("malformed_empty_manifest_payload")

    if blocking:
        lineage_status = "LINEAGE_BLOCKED"
    elif degraded:
        lineage_status = "LINEAGE_DEGRADED"
    else:
        lineage_status = "LINEAGE_OK"

    return OrderedDict([
        ("lineage_status", lineage_status),
        ("blocking_reasons", sorted(set(blocking))),
        ("degraded_reasons", sorted(set(degraded))),
        ("lineage_checksum_present", lineage_present),
        ("manifest_checksum_present", manifest_present),
    ])


def build_d8c_dashboard_consumption_model(*, readback_inventory: Mapping[str, Any], lineage_validation: Mapping[str, Any]) -> OrderedDict[str, Any]:
    replay_count = int(readback_inventory.get("replay_row_count") or 0)
    manifest_count = int(readback_inventory.get("manifest_row_count") or 0)
    lineage_status = _text(lineage_validation.get("lineage_status")) or "LINEAGE_BLOCKED"

    readiness = "READY" if replay_count > 0 and manifest_count > 0 and lineage_status == "LINEAGE_OK" else "NOT_READY"
    dashboard_status = "DASHBOARD_MODEL_READY" if readiness == "READY" else "DASHBOARD_MODEL_PARTIAL"
    recommendation = "D8C_CERTIFY_DASHBOARD_CONSUMPTION" if readiness == "READY" else "D8C_REMEDIATE_LINEAGE_OR_READBACK"

    return OrderedDict([
        ("replay_persistence_status", "REPLAY_PERSISTENCE_OPERATIONAL" if replay_count > 0 else "REPLAY_PERSISTENCE_NOT_OBSERVED"),
        ("replay_row_count", replay_count),
        ("manifest_row_count", manifest_count),
        ("latest_replay_ids", list(readback_inventory.get("latest_replay_ids") or [])),
        ("latest_manifest_checksums", list(readback_inventory.get("latest_manifest_checksums") or [])),
        ("lineage_status", lineage_status),
        ("replay_candidate_readiness", readiness),
        ("dashboard_consumption_status", dashboard_status),
        ("recommendation", recommendation),
        ("lineage_audit_details", OrderedDict([
            ("manifest_checksum_count", len(readback_inventory.get("manifest_checksums") or [])),
            ("lineage_checksum_present", bool(lineage_validation.get("lineage_checksum_present"))),
            ("manifest_checksum_present", bool(lineage_validation.get("manifest_checksum_present"))),
        ])),
    ])


def certify_d8c_dashboard_consumption(*, readback_inventory: Mapping[str, Any], lineage_validation: Mapping[str, Any], dashboard_consumption_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    replay_count = int(readback_inventory.get("replay_row_count") or 0)
    manifest_count = int(readback_inventory.get("manifest_row_count") or 0)
    lineage_status = _text(lineage_validation.get("lineage_status"))
    required_fields = {
        "replay_persistence_status", "replay_row_count", "manifest_row_count", "latest_replay_ids",
        "latest_manifest_checksums", "lineage_status", "replay_candidate_readiness", "dashboard_consumption_status", "recommendation",
    }
    model_complete = required_fields.issubset(set(dashboard_consumption_model.keys()))

    if replay_count <= 0 or manifest_count <= 0:
        status = "BLOCKED_DASHBOARD_CONSUMPTION"
    elif lineage_status == "LINEAGE_OK" and model_complete:
        status = "CERTIFIED_DASHBOARD_CONSUMABLE"
    else:
        status = "DEGRADED_DASHBOARD_CONSUMABLE"

    return OrderedDict([
        ("certification_status", status),
        ("model_complete", model_complete),
        ("lineage_status", lineage_status),
        ("replay_row_count", replay_count),
        ("manifest_row_count", manifest_count),
    ])


def build_d8c_certification_report_payload(*, objective: str = "D8.C Persisted Replay Readback & Dashboard Consumption Certification", readback_inventory: Mapping[str, Any], lineage_validation: Mapping[str, Any], dashboard_consumption_model: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    recommendation = dashboard_consumption_model.get("recommendation") or certification.get("certification_status")
    return OrderedDict([
        ("objective", objective),
        ("approved_tables", list(APPROVED_TABLES)),
        ("no_direct_sql_bypass_used", True),
        ("readback_inventory", OrderedDict(readback_inventory)),
        ("lineage_validation", OrderedDict(lineage_validation)),
        ("dashboard_consumption_model", OrderedDict(dashboard_consumption_model)),
        ("certification", OrderedDict(certification)),
        ("recommendation", recommendation),
    ])


def build_d8c_certification_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    inv = report_payload.get("readback_inventory") or {}
    lineage = report_payload.get("lineage_validation") or {}
    model = report_payload.get("dashboard_consumption_model") or {}
    cert = report_payload.get("certification") or {}
    lines = [
        "# D8.C Persisted Replay Readback & Dashboard Consumption Certification",
        "",
        f"## Objective\n- {report_payload.get('objective')}",
        "## Scope\n- Read-only replay/manifest readback through injected client adapters.\n- Deterministic inventory, lineage validation, and dashboard-consumable view model.",
        "## Non-goals\n- No live writes.\n- No direct SQL.\n- No governance bypass.",
        f"## Readback Inventory\n- Replay rows: {inv.get('replay_row_count', 0)}\n- Manifest rows: {inv.get('manifest_row_count', 0)}\n- Latest replay IDs: {', '.join(inv.get('latest_replay_ids', [])) or 'none'}",
        f"## Lineage Validation\n- Lineage status: {lineage.get('lineage_status')}\n- Blocking reasons: {', '.join(lineage.get('blocking_reasons', [])) or 'none'}\n- Degraded reasons: {', '.join(lineage.get('degraded_reasons', [])) or 'none'}",
        f"## Dashboard Consumption\n- Status: {model.get('dashboard_consumption_status')}\n- Candidate readiness: {model.get('replay_candidate_readiness')}\n- Recommendation: {model.get('recommendation')}",
        f"## Certification Result\n- {cert.get('certification_status')}",
        "## Governance/Safety Boundaries\n- Approved tables only: dashboard_replay_metadata_records, dashboard_export_manifests\n- no_direct_sql_bypass_used: True",
        f"## Final Recommendation\n- {report_payload.get('recommendation')}",
    ]
    return "\n".join(lines)
