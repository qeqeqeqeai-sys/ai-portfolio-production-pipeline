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
D7_MODULE_VERSION = "1.2.0"

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
    manifests = _safe_rows(client, table="dashboard_export_manifests", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_export_manifests"], limit=50)
    audits = _safe_rows(client, table="dashboard_persistence_audit_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_persistence_audit_records"], limit=50)
    replay = _safe_rows(client, table="dashboard_replay_metadata_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_replay_metadata_records"], limit=50)
    governance = _safe_rows(client, table="dashboard_governance_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_governance_records"], limit=50)
    supervisor = _safe_rows(client, table="dashboard_supervisor_panel_records", columns=D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_supervisor_panel_records"], limit=50)
    return OrderedDict([("manifests", manifests), ("audits", audits), ("replay", replay), ("governance", governance), ("supervisor", supervisor)])


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


def _nested_get(source: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = source
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _status_rank(status: str | None) -> int:
    precedence = {
        "EXECUTED_WITH_FAILURES": 4,
        "EXECUTED": 3,
        "PERSISTED": 2,
        "PLANNED": 1,
        "UNKNOWN": 0,
    }
    return precedence.get(str(status or "").strip().upper(), 0)


def _extract_persistence(audits: list[Mapping[str, Any]]) -> tuple[str, str | None, list[str], Mapping[str, Any] | None]:
    seen_statuses: list[str] = []
    selected_source: str | None = None
    best_row: Mapping[str, Any] | None = None
    best_status = "UNKNOWN"
    best_rank = -1
    for row in audits:
        payload = _payload_map(row)
        result_summary = _nested_get(payload, ("result_summary",)) if isinstance(_nested_get(payload, ("result_summary",)), Mapping) else {}
        table_results = list(_nested_get(payload, ("result_summary", "table_results")) or []) if isinstance(_nested_get(payload, ("result_summary", "table_results")), list) else []
        table_statuses = [str(item.get("write_status") or item.get("status") or "").strip().upper() for item in table_results if isinstance(item, Mapping)]
        any_failed = any(x in {"FAILED", "ERROR", "EXECUTED_WITH_FAILURES", "PARTIAL_FAILURE"} for x in table_statuses)
        all_persisted = bool(table_statuses) and all(x in {"EXECUTED", "PERSISTED", "SUCCESS", "SUCCEEDED", "COMPLETED"} for x in table_statuses)

        candidates = [
            ("dashboard_persistence_audit_records.write_status", row.get("write_status")),
            ("dashboard_persistence_audit_records.payload.persistence_status", payload.get("persistence_status")),
            ("dashboard_persistence_audit_records.payload.execution_status", payload.get("execution_status")),
            ("dashboard_persistence_audit_records.payload.result_summary.persistence_status", _nested_get(payload, ("result_summary", "persistence_status"))),
        ]
        if any_failed:
            candidates.append(("dashboard_persistence_audit_records.payload.result_summary.table_results", "EXECUTED_WITH_FAILURES"))
        elif all_persisted:
            candidates.append(("dashboard_persistence_audit_records.payload.result_summary.table_results", "EXECUTED"))

        row_best_status = "UNKNOWN"
        row_best_source = None
        row_best_rank = -1
        for candidate_source, candidate in candidates:
            if not candidate:
                continue
            normalized = str(candidate).strip().upper()
            seen_statuses.append(normalized)
            rank = _status_rank(normalized)
            if rank > row_best_rank:
                row_best_rank = rank
                row_best_status = normalized
                row_best_source = candidate_source
        record_type = str(row.get("record_type") or "")
        row_priority = 1 if record_type == "d3_execution_summary_record" else 0
        best_priority = 1 if str((best_row or {}).get("record_type") or "") == "d3_execution_summary_record" else 0
        created_at = str(row.get("created_at") or "")
        if (
            row_best_rank > best_rank
            or (row_best_rank == best_rank and row_priority > best_priority)
            or (row_best_rank == best_rank and row_priority == best_priority and created_at > str((best_row or {}).get("created_at") or ""))
        ):
            best_rank = row_best_rank
            best_status = row_best_status
            selected_source = row_best_source
            best_row = row
    if best_rank < 0:
        return "PLANNED", None, seen_statuses, None
    return best_status if best_status != "UNKNOWN" else "PLANNED", selected_source, seen_statuses, best_row


def _extract_readback(replay: list[Mapping[str, Any]]) -> tuple[str, str | None, Mapping[str, Any] | None]:
    lookup_paths = [
        ("dashboard_replay_metadata_records.payload.effective_readback_verification_status", ("payload", "effective_readback_verification_status")),
        ("dashboard_replay_metadata_records.payload.readback_verification_status", ("payload", "readback_verification_status")),
        ("dashboard_replay_metadata_records.payload.raw_readback_verification_status", ("payload", "raw_readback_verification_status")),
        ("dashboard_replay_metadata_records.payload.verification_status", ("payload", "verification_status")),
        ("dashboard_replay_metadata_records.replay_metadata.readback_verification_status", ("replay_metadata", "readback_verification_status")),
        ("dashboard_replay_metadata_records.payload.verification_handoff_status", ("payload", "verification_handoff_status")),
    ]
    best = ("unknown", None, None, -1, "")
    for row in replay:
        for source_name, path in lookup_paths:
            value = _nested_get(row, path)
            if value:
                row_score = 2 if "effective_" in source_name else 1
                created_at = str(row.get("created_at") or "")
                if row_score > best[3] or (row_score == best[3] and created_at > best[4]):
                    best = (str(value), source_name, row, row_score, created_at)
                break
    return best[0], best[1], best[2]


def _extract_checksum_chain(manifests: list[Mapping[str, Any]], replay: list[Mapping[str, Any]], audits: list[Mapping[str, Any]]) -> tuple[OrderedDict[str, Any], str, list[str], str]:
    fields = ["source_payload_checksum", "export_checksum", "manifest_checksum", "replay_checksum", "cycle_checksum", "o5_checksum", "o6_checksum", "d3_checksum", "d4_checksum"]
    groups: dict[tuple[str, str], OrderedDict[str, Any]] = {}
    for row in manifests + replay + audits:
        payload = _payload_map(row)
        replay_metadata = row.get("replay_metadata") if isinstance(row.get("replay_metadata"), Mapping) else {}
        source = row.get("source_payload_checksum") or payload.get("source_payload_checksum") or ""
        export = row.get("export_checksum") or payload.get("export_checksum") or ""
        key = (str(source), str(export))
        bucket = groups.setdefault(key, OrderedDict((k, None) for k in fields))
        bucket["source_payload_checksum"] = bucket["source_payload_checksum"] or source
        bucket["export_checksum"] = bucket["export_checksum"] or export
        bucket["manifest_checksum"] = bucket["manifest_checksum"] or row.get("manifest_checksum") or payload.get("manifest_checksum")
        bucket["replay_checksum"] = bucket["replay_checksum"] or row.get("replay_checksum") or payload.get("replay_checksum")
        bucket["cycle_checksum"] = bucket["cycle_checksum"] or payload.get("cycle_checksum") or replay_metadata.get("cycle_checksum")
        bucket["o5_checksum"] = bucket["o5_checksum"] or payload.get("o5_checksum") or replay_metadata.get("o5_checksum")
        bucket["o6_checksum"] = bucket["o6_checksum"] or payload.get("o6_checksum") or replay_metadata.get("o6_checksum")
        bucket["d3_checksum"] = bucket["d3_checksum"] or payload.get("d3_checksum") or payload.get("d3_summary_checksum") or replay_metadata.get("d3_checksum")
        bucket["d4_checksum"] = bucket["d4_checksum"] or payload.get("d4_checksum") or payload.get("d4_verification_checksum") or replay_metadata.get("d4_checksum")

    selected_integrity_strategy = "latest_available"
    if groups:
        latest_key = max(groups.keys(), key=lambda k: (bool(k[0] or k[1]), k[0], k[1]))
        chain = groups[latest_key]
        full_count = sum(1 for k in fields if chain.get(k))
        if full_count < 6:
            chain = max(groups.values(), key=lambda g: sum(1 for k in fields if g.get(k)))
            selected_integrity_strategy = "latest_full_checksum_chain"
        else:
            selected_integrity_strategy = "latest_successful"
    else:
        chain = OrderedDict((k, None) for k in fields)
        selected_integrity_strategy = "fallback_partial"

    warnings: list[str] = []
    primary = ["source_payload_checksum", "export_checksum", "manifest_checksum", "replay_checksum"]
    discovered = [k for k, v in chain.items() if v]
    primary_count = sum(1 for key in primary if chain[key])
    full_d6_chain = all(chain[k] for k in ("o5_checksum", "o6_checksum", "d3_checksum", "d4_checksum", "cycle_checksum"))
    if primary_count == len(primary) or full_d6_chain:
        continuity = "yes"
    elif primary_count >= 2 or any(chain[k] for k in ("cycle_checksum", "o5_checksum", "o6_checksum", "d3_checksum", "d4_checksum")):
        continuity = "partial"
        warnings.append("checksum_continuity_inferred_from_partial_chain")
    else:
        continuity = "no"
        warnings.append("insufficient_checksum_chain_evidence")
    warnings.append(f"checksum_fields_discovered={','.join(discovered) if discovered else 'none'}")
    return chain, continuity, warnings, selected_integrity_strategy


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

    persistence_status, persistence_source, persistence_candidates, selected_audit = _extract_persistence(audits)
    readback_status, readback_source, selected_readback = _extract_readback(replay)
    checksum_chain, continuity, continuity_warnings, selected_integrity_strategy = _extract_checksum_chain(manifests, replay, audits)
    if not latest_run:
        latest_run = (
            (latest_replay.get("replay_id") if latest_replay else None)
            or _payload_map(latest_replay).get("replay_id")
            or (str(checksum_chain.get("cycle_checksum"))[:12] if checksum_chain.get("cycle_checksum") else None)
            or (str(checksum_chain.get("replay_checksum"))[:12] if checksum_chain.get("replay_checksum") else None)
            or (str(checksum_chain.get("manifest_checksum"))[:12] if checksum_chain.get("manifest_checksum") else None)
            or (str(checksum_chain.get("source_payload_checksum"))[:12] if checksum_chain.get("source_payload_checksum") else None)
        )

    normalized_integrity = OrderedDict([
        ("latest_run", latest_run),
        ("certification", "AVAILABLE" if findings else "DEGRADED_OR_EMPTY"),
        ("persistence_status", persistence_status),
        ("readback_status", readback_status),
        ("checksum_continuity", continuity),
        ("checksum_chain", checksum_chain),
        ("integrity_sources", OrderedDict([
            ("persistence_status_source", persistence_source),
            ("readback_status_source", readback_source),
            ("persistence_candidates_seen", persistence_candidates),
            ("selected_persistence_record_id", (selected_audit or {}).get("record_id")),
            ("selected_persistence_created_at", (selected_audit or {}).get("created_at")),
            ("selected_readback_record_id", (selected_readback or {}).get("record_id")),
            ("selected_readback_created_at", (selected_readback or {}).get("created_at")),
            ("audit_rows_inspected", len(audits)),
            ("selected_integrity_strategy", selected_integrity_strategy),
        ])),
        ("integrity_warnings", continuity_warnings),
    ])

    overview = OrderedDict([
        ("latest_operational_run", latest_run),
        ("certification_status", normalized_integrity["certification"]),
        ("persistence_execution_status", normalized_integrity["persistence_status"]),
        ("readback_verification_status", normalized_integrity["readback_status"]),
        ("replay_checksum_continuity", normalized_integrity["checksum_continuity"]),
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
            ("latest_persistence_audit_status", (selected_audit or latest_audit).get("write_status")),
            ("record_counts", _payload_map(latest_manifest).get("record_counts") or {}),
            ("verification_continuity", _derive_continuity_status(latest_replay) or "unknown"),
            ("normalized", normalized_integrity),
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
