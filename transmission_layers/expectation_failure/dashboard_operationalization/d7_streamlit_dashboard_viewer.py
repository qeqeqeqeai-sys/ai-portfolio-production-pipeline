"""D7 thin read-only Streamlit dashboard viewer over persisted operationalization records."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from urllib.parse import urlparse
from typing import Any, Mapping

D7_SCHEMA_VERSION = "d7_streamlit_dashboard_viewer_v1"
D7_MODULE_VERSION = "1.1.0"

D7_PHYSICAL_COLUMNS_BY_TABLE = {
    "dashboard_finding_records": [
        "record_id", "record_type", "source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata", "created_at", "updated_at",
        "finding_id", "finding_type", "finding_title", "finding_severity", "finding_direction", "confidence_label",
    ],
    "dashboard_narrative_records": [
        "record_id", "record_type", "source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata", "created_at", "updated_at",
        "narrative_section", "related_finding_ids",
    ],
    "dashboard_evidence_map_records": [
        "record_id", "record_type", "source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata", "created_at", "updated_at",
        "finding_id", "evidence_ref",
    ],
    "dashboard_supervisor_panel_records": [
        "record_id", "record_type", "source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata", "created_at", "updated_at",
        "panel_name", "panel_status",
    ],
    "dashboard_export_manifests": [
        "record_id", "record_type", "source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata", "created_at", "updated_at",
        "manifest_id", "manifest_checksum",
    ],
    "dashboard_governance_records": [
        "record_id", "record_type", "source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata", "created_at", "updated_at",
        "governance_status", "forbidden_capabilities",
    ],
    "dashboard_replay_metadata_records": [
        "record_id", "record_type", "source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata", "created_at", "updated_at",
        "replay_id", "replay_checksum",
    ],
    "dashboard_persistence_audit_records": [
        "record_id", "record_type", "source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata", "created_at", "updated_at",
        "audit_id", "batch_id", "target_table", "write_status",
    ],
}
_D7_TABLES = (
    "dashboard_finding_records",
    "dashboard_narrative_records",
    "dashboard_evidence_map_records",
    "dashboard_export_manifests",
    "dashboard_persistence_audit_records",
    "dashboard_replay_metadata_records",
)


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _safe_rows(client: Any, *, table: str, columns: list[str], limit: int = 500, order_by: str = "created_at", desc: bool = True) -> OrderedDict[str, Any]:
    degraded = OrderedDict([("table", table), ("status", "degraded"), ("row_count", 0), ("rows", []), ("error", None)])
    if client is None:
        degraded["error"] = "client_not_provided"
        return degraded
    try:
        query = client.table(table).select(",".join(columns)).order(order_by, desc=desc).limit(limit)
        result = query.execute()
        data = list(getattr(result, "data", []) or [])
        rows = [OrderedDict((k, r.get(k)) for k in columns) for r in data if isinstance(r, Mapping)]
        status = "ok" if rows else "empty"
        return OrderedDict([("table", table), ("status", status), ("row_count", len(rows)), ("rows", rows), ("error", None)])
    except Exception as exc:
        degraded["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        return degraded


def load_d7_dashboard_findings(client: Any, *, limit: int = 500) -> OrderedDict[str, Any]:
    return _safe_rows(client, table="dashboard_finding_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_finding_records"], limit=limit, order_by="created_at", desc=True)


def load_d7_dashboard_narratives(client: Any, *, limit: int = 200) -> OrderedDict[str, Any]:
    return _safe_rows(client, table="dashboard_narrative_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_narrative_records"], limit=limit, order_by="created_at", desc=True)


def load_d7_dashboard_evidence_maps(client: Any, *, limit: int = 500) -> OrderedDict[str, Any]:
    return _safe_rows(client, table="dashboard_evidence_map_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_evidence_map_records"], limit=limit, order_by="created_at", desc=True)


def load_d7_dashboard_operational_integrity(client: Any) -> OrderedDict[str, Any]:
    manifests = _safe_rows(client, table="dashboard_export_manifests", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_export_manifests"], limit=100)
    audits = _safe_rows(client, table="dashboard_persistence_audit_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_persistence_audit_records"], limit=200)
    replay = _safe_rows(client, table="dashboard_replay_metadata_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_replay_metadata_records"], limit=100)
    return OrderedDict([("manifests", manifests), ("audits", audits), ("replay", replay)])


def _safe_project_host(url: Any) -> tuple[str | None, str | None]:
    raw = str(url or "").strip()
    if not raw:
        return None, None
    parsed = urlparse(raw)
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return None, None
    return host, (host.split(".")[0] if "." in host else None)


def _classify_supabase_key(key: Any) -> str:
    text = str(key or "").strip()
    if not text:
        return "missing"
    if "service_role" in text:
        return "service_role"
    if "anon" in text:
        return "anon"
    return "unknown_non_empty"


def build_d7_runtime_diagnostics(*, runtime_config: Mapping[str, Any], client_resolution: Mapping[str, Any], table_payloads: Mapping[str, Mapping[str, Any]]) -> OrderedDict[str, Any]:
    host, project_id = _safe_project_host(runtime_config.get("supabase_url"))
    key_kind = _classify_supabase_key(runtime_config.get("supabase_key"))
    source = "env"
    if runtime_config.get("supabase_url_source") or runtime_config.get("supabase_key_source"):
        source = "streamlit_or_env"
    table_diagnostics = OrderedDict()
    for table in _D7_TABLES:
        payload = table_payloads.get(table, {})
        rows = list(payload.get("rows", [])) if isinstance(payload, Mapping) else []
        sample_identifier = None
        for field in ("record_id", "finding_id", "manifest_id", "audit_id", "replay_id"):
            if rows and rows[0].get(field):
                sample_identifier = str(rows[0].get(field))
                break
        table_diagnostics[table] = OrderedDict([
            ("status", payload.get("status")),
            ("row_count", int(payload.get("row_count") or 0)),
            ("latest_created_at", rows[0].get("created_at") if rows else None),
            ("sample_record_id_preview", sample_identifier[:16] if sample_identifier else None),
            ("derived_run_or_replay_preview", (str(derived_id)[:16] if (derived_id := _derived_run_or_replay_id(rows[0])) else None) if rows else None),
            ("error", payload.get("error")),
        ])

    gha_url = runtime_config.get("github_actions_supabase_url")
    gha_host, gha_project = _safe_project_host(gha_url)
    project_mismatch = bool(project_id and gha_project and project_id != gha_project)
    return OrderedDict([
        ("supabase_url_host", host),
        ("supabase_project_id_prefix", project_id),
        ("github_actions_supabase_url_host", gha_host),
        ("github_actions_project_id_prefix", gha_project),
        ("project_id_mismatch_vs_github_actions", project_mismatch),
        ("key_classification", key_kind),
        ("using_service_role_key", key_kind == "service_role"),
        ("using_anon_key", key_kind == "anon"),
        ("client_resolved", bool(client_resolution.get("client_resolved"))),
        ("client_factory_source", client_resolution.get("client_factory_source")),
        ("credentials_present", bool(runtime_config.get("credentials_present"))),
        ("environment_source", source),
        ("table_diagnostics", table_diagnostics),
    ])


def _derived_run_or_replay_id(row: Mapping[str, Any]) -> str | None:
    replay_metadata = row.get("replay_metadata") if isinstance(row.get("replay_metadata"), Mapping) else {}
    payload = row.get("payload") if isinstance(row.get("payload"), Mapping) else {}
    for source in (replay_metadata, payload):
        value = source.get("replay_id") or source.get("run_id")
        if value:
            return str(value)
    checksum = row.get("source_payload_checksum") or row.get("export_checksum")
    if checksum:
        return str(checksum)[:12]
    return None


def _latest_run_id(*sections: Mapping[str, Any]) -> str | None:
    runs = []
    for section in sections:
        for row in section.get("rows", []):
            created_at = str(row.get("created_at") or "")
            run_like_id = _derived_run_or_replay_id(row)
            if run_like_id:
                runs.append((created_at, run_like_id))
    return sorted(runs, reverse=True)[0][1] if runs else None




def _payload_map(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload")
    return payload if isinstance(payload, Mapping) else {}


def _derive_continuity_status(row: Mapping[str, Any]) -> str | None:
    payload = _payload_map(row)
    replay_metadata = row.get("replay_metadata") if isinstance(row.get("replay_metadata"), Mapping) else {}
    for source in (payload, replay_metadata):
        val = source.get("continuity_status")
        if val:
            return str(val)
    return "VERIFIED" if row.get("replay_checksum") else None


def _transform_findings(rows: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    out=[]
    for r in rows:
        payload=_payload_map(r)
        out.append(OrderedDict(r)|OrderedDict([("severity", r.get("finding_severity")),("direction", r.get("finding_direction")),("confidence", r.get("confidence_label") or payload.get("confidence")),("finding_summary", payload.get("finding_summary"))]))
    return out


def _transform_narratives(rows: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    out=[]
    for r in rows:
        payload=_payload_map(r)
        out.append(OrderedDict(r)|OrderedDict([("narrative_text", payload.get("narrative_text") or payload.get("finding_summary")),("related_findings", r.get("related_finding_ids") or payload.get("related_findings") or [])]))
    return out


def _transform_evidence(rows: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    out=[]
    for r in rows:
        payload=_payload_map(r)
        out.append(OrderedDict(r)|OrderedDict([("evidence_metadata", payload.get("evidence_metadata") or payload)]))
    return out

def build_d7_dashboard_view_model(*, findings_payload: Mapping[str, Any], narratives_payload: Mapping[str, Any], evidence_payload: Mapping[str, Any], integrity_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    findings = _transform_findings(list(findings_payload.get("rows", [])))
    narratives = _transform_narratives(list(narratives_payload.get("rows", [])))
    evidence_maps = _transform_evidence(list(evidence_payload.get("rows", [])))
    manifests = list(integrity_payload.get("manifests", {}).get("rows", []))
    audits = list(integrity_payload.get("audits", {}).get("rows", []))
    replay = list(integrity_payload.get("replay", {}).get("rows", []))

    latest_run = _latest_run_id(findings_payload, narratives_payload, evidence_payload, integrity_payload.get("manifests", {}), integrity_payload.get("audits", {}), integrity_payload.get("replay", {}))
    latest_manifest = manifests[0] if manifests else {}
    latest_replay = replay[0] if replay else {}
    latest_audit = audits[0] if audits else {}

    overview = OrderedDict([
        ("latest_operational_run", latest_run),
        ("certification_status", "AVAILABLE" if findings else "DEGRADED_OR_EMPTY"),
        ("persistence_execution_status", str(latest_audit.get("write_status") or "unknown")),
        ("readback_verification_status", str(_derive_continuity_status(latest_replay) or "unknown")),
        ("replay_checksum_continuity", bool(latest_replay.get("replay_checksum") and latest_manifest.get("manifest_checksum"))),
    ])

    interpretation = OrderedDict([
        ("operational_usefulness_interpretation", "Useful for inspection and fragility triage when findings are present; limited when evidence metadata is sparse."),
        ("limitations", ["Read-only surface; no drill-through lineage graph.", "Narratives may remain template-like.", "Cross-sectional ranking depth depends on upstream finding richness."]),
        ("next_recommended_step", "E1 — Cross-Sectional Relative Fragility Intelligence."),
        ("governance_status", "READ_ONLY_BOUNDARY_PRESERVED"),
    ])

    payload = OrderedDict([
        ("schema_version", D7_SCHEMA_VERSION),
        ("module_version", D7_MODULE_VERSION),
        ("generated_at_utc", datetime.utcnow().isoformat(timespec="seconds") + "Z"),
        ("overview", overview),
        ("findings", findings),
        ("narratives", narratives),
        ("evidence_maps", evidence_maps),
        ("integrity", OrderedDict([
            ("latest_export_manifest_checksum", latest_manifest.get("manifest_checksum")),
            ("latest_replay_checksum", latest_replay.get("replay_checksum")),
            ("latest_persistence_audit_status", latest_audit.get("write_status")),
            ("record_counts", _payload_map(latest_manifest).get("record_counts") or {}),
            ("verification_continuity", _derive_continuity_status(latest_replay) or "unknown"),
        ])),
        ("runtime_sections", OrderedDict([
            ("findings_payload", deepcopy(findings_payload)),
            ("narratives_payload", deepcopy(narratives_payload)),
            ("evidence_payload", deepcopy(evidence_payload)),
            ("integrity_payload", deepcopy(integrity_payload)),
        ])),
        ("supervisor_interpretation", interpretation),
        ("invariant_flags", OrderedDict([("read_only", True), ("no_writes", True), ("no_hidden_client_creation", True), ("explicit_client_injection", True)])),
    ])
    payload["view_model_checksum"] = _stable_checksum(payload)
    return payload


__all__ = [
    "load_d7_dashboard_findings",
    "load_d7_dashboard_narratives",
    "load_d7_dashboard_evidence_maps",
    "load_d7_dashboard_operational_integrity",
    "build_d7_dashboard_view_model",
    "build_d7_runtime_diagnostics",
    "D7_PHYSICAL_COLUMNS_BY_TABLE",
]
