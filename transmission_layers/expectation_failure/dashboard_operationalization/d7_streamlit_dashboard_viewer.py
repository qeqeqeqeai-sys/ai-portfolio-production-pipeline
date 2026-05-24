"""D7 thin read-only Streamlit dashboard viewer over persisted operationalization records."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from urllib.parse import urlparse
from typing import Any, Mapping

from transmission_layers.expectation_failure.expectation_intelligence import build_e1_expectation_intelligence_payload, build_e2_evidence_interpretation_payload, build_e3_temporal_drift_report, build_e4_semantic_narrative_drift_report, build_e5_expectation_intelligence_envelope, build_d8_evidence_priority_inventory, build_d8_dashboard_view_model, build_e7_expectation_capability_inventory, build_e7_governance_boundary_inventory

D7_SCHEMA_VERSION = "d7_streamlit_dashboard_viewer_v1"
D7_MODULE_VERSION = "1.3.0"
D7_RENDER_SECTION_ORDER = (
    "e6_expectation_executive_summary",
    "intelligence_overview",
    "supervisor_interpretation",
    "key_finding_cards",
    "narrative_sections",
    "evidence_highlights",
    "operational_integrity_overview",
    "governance_debug_archive",
)

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


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _as_text(value: Any, default: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text or default


def _badge_for(label: str) -> str:
    normalized = _as_text(label, "unknown").lower()
    return {"high": "🔴 high", "medium": "🟠 medium", "low": "🟢 low", "unknown": "⚪ unknown"}.get(normalized, f"⚪ {normalized}")


def build_d7_intelligence_cards(findings: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    evidence_by_finding: dict[str, list[str]] = {}
    for evidence in evidence_maps:
        finding_id = _as_text(evidence.get("finding_id"))
        if not finding_id:
            continue
        payload = _payload_map(evidence)
        summary = _as_text(payload.get("evidence_summary")) or _as_text(evidence.get("evidence_ref"))
        if summary:
            evidence_by_finding.setdefault(finding_id, []).append(summary)
    cards: list[OrderedDict[str, Any]] = []
    for finding in findings:
        payload = _payload_map(finding)
        finding_id = _as_text(finding.get("finding_id"))
        severity = _as_text(finding.get("severity") or finding.get("finding_severity"), "unknown")
        confidence = _as_text(finding.get("confidence") or finding.get("confidence_label") or payload.get("confidence"), "unknown")
        contradiction = _as_text(payload.get("contradiction_or_divergence_notes") or payload.get("divergence_notes") or payload.get("contradiction_notes"))
        cards.append(OrderedDict([
            ("finding_title", _as_text(finding.get("finding_title"), f"Finding {finding_id or 'unlabeled'}")),
            ("finding_type", _as_text(finding.get("finding_type"), "unspecified")),
            ("severity_label", severity),
            ("severity_badge", _badge_for(severity)),
            ("confidence_label", confidence),
            ("confidence_badge", _badge_for(confidence)),
            ("finding_summary", _as_text(finding.get("finding_summary") or payload.get("finding_summary"), "No finding summary was present in the persisted payload.")),
            ("expectation_fragility_interpretation", _as_text(payload.get("expectation_fragility_interpretation"), "No explicit expectation-fragility interpretation was present in the persisted payload.")),
            ("why_this_matters", _as_text(payload.get("why_this_matters"), "Operationally relevant because this persisted finding contributes to expectation-fragility monitoring.")),
            ("evidence_highlights", evidence_by_finding.get(finding_id, [])[:4]),
            ("contradiction_or_divergence_notes", contradiction or "No explicit contradiction/divergence notes were present in the persisted payload."),
        ]))
    return cards


def build_d7_narrative_sections(narratives: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    ordered_keys = ["expectation_pressure", "market_context", "semantic_pressure", "contradictions", "supervisor_interpretation"]
    grouped: dict[str, list[Mapping[str, Any]]] = {k: [] for k in ordered_keys}
    for row in narratives:
        section = _as_text(row.get("narrative_section") or _payload_map(row).get("narrative_section"), "market_context").lower()
        grouped[section if section in grouped else "market_context"].append(row)
    out: list[OrderedDict[str, Any]] = []
    for key in ordered_keys:
        rows = grouped[key]
        if not rows:
            continue
        text_parts: list[str] = []
        linked_findings: list[str] = []
        bullets: list[str] = []
        caveats: list[str] = []
        for row in rows:
            payload = _payload_map(row)
            text_parts.append(_as_text(row.get("narrative_text") or payload.get("narrative_text") or payload.get("finding_summary")))
            linked_findings.extend([str(x) for x in _as_list(row.get("related_findings") or row.get("related_finding_ids") or payload.get("related_findings"))])
            bullets.extend([str(x) for x in _as_list(payload.get("supporting_evidence_bullets"))])
            caveat = _as_text(payload.get("caveat") or payload.get("limitations"))
            if caveat:
                caveats.append(caveat)
        out.append(OrderedDict([
            ("section_key", key),
            ("section_title", key.replace("_", " ").title()),
            ("narrative_text", "\n\n".join([x for x in text_parts if x]) or "No narrative text was present in this persisted section."),
            ("linked_findings", sorted(set(linked_findings))),
            ("supporting_evidence_bullets", bullets),
            ("optional_caveats", caveats),
        ]))
    return out


def build_d7_evidence_highlights(evidence_maps: list[Mapping[str, Any]], findings: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    title_by_id = {_as_text(f.get("finding_id")): _as_text(f.get("finding_title"), _as_text(f.get("finding_id"))) for f in findings}
    out: list[OrderedDict[str, Any]] = []
    for row in evidence_maps:
        payload = _payload_map(row)
        finding_id = _as_text(row.get("finding_id"))
        out.append(OrderedDict([
            ("linked_finding", title_by_id.get(finding_id) or finding_id or "unlinked"),
            ("evidence_summary", _as_text(payload.get("evidence_summary") or row.get("evidence_ref"), "No evidence summary was present in the persisted payload.")),
            ("semantic_drivers", _as_list(payload.get("semantic_drivers"))),
            ("kpi_or_evidence_references", _as_list(payload.get("kpi_references") or payload.get("evidence_references") or ([row.get("evidence_ref")] if row.get("evidence_ref") else []))),
            ("confidence_or_caveat", _as_text(payload.get("confidence") or payload.get("caveat"), "No explicit confidence/caveat was present in the persisted payload.")),
        ]))
    return out


def build_d7_integrity_overview(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    normalized = _nested_get(view_model, ("integrity", "normalized")) if isinstance(view_model, Mapping) else {}
    persistence = _as_text((normalized or {}).get("persistence_status"), "unknown")
    readback = _as_text((normalized or {}).get("readback_status"), "unknown")
    continuity = _as_text((normalized or {}).get("checksum_continuity"), "unknown")
    governance = _as_text(_nested_get(view_model, ("supervisor_interpretation", "governance_status")), "READ_ONLY_BOUNDARY_PRESERVED")
    usefulness = "high" if persistence in {"EXECUTED", "PERSISTED"} and continuity in {"yes", "partial"} else "limited"
    return OrderedDict([("Persistence", persistence), ("Readback Verification", readback), ("Checksum Continuity", continuity), ("Governance Status", governance), ("Operational Usefulness", usefulness), ("operational_usefulness", usefulness)])


def build_d7_supervisor_summary(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    cards = _as_list(view_model.get("intelligence_cards"))
    integrity_overview = view_model.get("integrity_overview") if isinstance(view_model.get("integrity_overview"), Mapping) else {}
    high_severity_count = sum(1 for card in cards if _as_text(card.get("severity_label")).lower() == "high")
    themes = sorted({_as_text(card.get("finding_type"), "unspecified") for card in cards})
    e1 = view_model.get("e1_expectation_intelligence") if isinstance(view_model.get("e1_expectation_intelligence"), Mapping) else {}
    strategist = e1.get("strategist_summary") if isinstance(e1.get("strategist_summary"), Mapping) else {}
    return OrderedDict([
        ("what_sefi_currently_believes", f"{len(cards)} persisted findings are available for expectation-fragility review."),
        ("dominant_fragility_themes", themes),
        ("expectation_pressure_concentration", f"High-severity concentration: {high_severity_count}/{len(cards) if cards else 0} findings."),
        ("operational_usefulness", integrity_overview.get("operational_usefulness", "moderate")),
        ("current_limitations", ["Interpretation remains deterministic and bounded by persisted payload richness.", "No live fetches, runtime writes, or predictive expansion are used."]),
        ("e2_confidence_caveats", ((view_model.get("e2_evidence_interpretation") or {}).get("confidence_caveats") if isinstance(view_model.get("e2_evidence_interpretation"), Mapping) else [])),
        ("e3_temporal_history_sufficiency", ((view_model.get("e3_temporal_expectation_memory") or {}).get("history_sufficiency") if isinstance(view_model.get("e3_temporal_expectation_memory"), Mapping) else "insufficient_history")),
        ("confidence_caveats", "Confidence labels are rendered exactly from persisted records; missing labels appear as unknown."),
        ("e1_dominant_expectation_regime", strategist.get("dominant_expectation_regime", "unknown")),
        ("e1_primary_fragility_drivers", strategist.get("primary_fragility_drivers", [])),
        ("e5_operational_status", (((view_model.get("e5_expectation_supervisor_closeout") or {}).get("e5_operational_status") or {}).get("e5_operational_status", "unknown"))),
    ])


def build_d7_debug_payload_sections(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("checksum_chain", deepcopy(_nested_get(view_model, ("integrity", "normalized", "checksum_chain")) or {})),
        ("raw_replay_metadata", deepcopy(_nested_get(view_model, ("runtime_sections", "integrity_payload", "replay", "rows")) or [])),
        ("export_manifests", deepcopy(_nested_get(view_model, ("runtime_sections", "integrity_payload", "manifests", "rows")) or [])),
        ("audit_rows", deepcopy(_nested_get(view_model, ("runtime_sections", "integrity_payload", "audits", "rows")) or [])),
        ("internal_ids", OrderedDict([("latest_run", _nested_get(view_model, ("overview", "latest_operational_run")))])),
        ("raw_payload_json", deepcopy(view_model.get("runtime_sections", {}))),
    ])

def build_d7_dashboard_view_model(*, findings_payload: Mapping[str, Any], narratives_payload: Mapping[str, Any], evidence_payload: Mapping[str, Any], integrity_payload: Mapping[str, Any], historical_runs_payloads: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
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

    intelligence_cards = build_d7_intelligence_cards(findings, evidence_maps)
    e1_payload = build_e1_expectation_intelligence_payload(findings, narratives, evidence_maps)
    e2_payload = build_e2_evidence_interpretation_payload(findings, narratives, evidence_maps, e1_payload)
    e3_payload = build_e3_temporal_drift_report(historical_runs_payloads or [])
    e4_payload = build_e4_semantic_narrative_drift_report(historical_runs_payloads or [])
    e5_payload = build_e5_expectation_intelligence_envelope(e1_payload=e1_payload, e2_payload=e2_payload, e3_payload=e3_payload, e4_payload=e4_payload, d7_context=OrderedDict([("findings", findings), ("narratives", narratives), ("evidence_maps", evidence_maps)]), governance_metadata=OrderedDict([("read_only_surface", True)]))
    d8_payload = build_d8_evidence_priority_inventory(findings, evidence_maps, e2_payload, e3_payload, e4_payload, e5_payload)
    d8_dashboard = build_d8_dashboard_view_model(d8_payload)
    narrative_sections = build_d7_narrative_sections(narratives)
    evidence_highlights = build_d7_evidence_highlights(evidence_maps, findings)
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
        ("supervisor_interpretation", OrderedDict(list(interpretation.items()) + [("e1_supervisor_interpretation", e1_payload.get("supervisor_interpretation", {})), ("e2_strategist_evidence_brief", e2_payload.get("strategist_evidence_brief", {}))])),
        ("intelligence_cards", intelligence_cards),
        ("narrative_sections", narrative_sections),
        ("evidence_highlights", evidence_highlights),
        ("e1_expectation_intelligence", e1_payload),
        ("e2_evidence_interpretation", e2_payload),
        ("e3_temporal_expectation_memory", e3_payload),
        ("e4_semantic_theme_memory", e4_payload),
        ("e5_expectation_supervisor_closeout", e5_payload),
        ("d8_evidence_prioritization", d8_payload),
        ("d8_dashboard", d8_dashboard),
        ("e7_expectation_closeout_certification", OrderedDict([("capability_inventory", build_e7_expectation_capability_inventory()), ("governance_boundary_inventory", build_e7_governance_boundary_inventory())])),
        ("invariant_flags", OrderedDict([("read_only", True), ("no_writes", True), ("no_hidden_client_creation", True), ("explicit_client_injection", True)])),
    ])
    payload["integrity_overview"] = build_d7_integrity_overview(payload)
    payload["supervisor_summary"] = build_d7_supervisor_summary(payload)
    payload["debug_payload_sections"] = build_d7_debug_payload_sections(payload)
    payload["view_model_checksum"] = _stable_checksum(payload)
    return payload


def _render_value(value: Any, *, fallback: str = "N/A") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _extract_e5_closeout(view_model: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = view_model.get("e5_expectation_supervisor_closeout") if isinstance(view_model.get("e5_expectation_supervisor_closeout"), Mapping) else {}
    return payload if isinstance(payload, Mapping) else {}


def _e5_alias_get(e5: Mapping[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = _nested_get(e5, path)
        if value not in (None, "", []):
            return value
    return None


def _to_bullets(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _status_label(status: Any) -> str:
    token = str(status or "").strip().upper()
    mapping = {
        "OPERATIONALLY_USABLE": "Operationally Usable",
        "DEGRADED_OPERATIONAL_INTELLIGENCE": "Degraded Operational Intelligence",
        "LIMITED_INTERPRETABILITY": "Limited Interpretability",
        "BLOCKED_EXPECTATION_INTELLIGENCE": "Blocked Expectation Intelligence",
    }
    return mapping.get(token, _render_value(status, fallback="Unavailable"))


def build_e6_executive_summary_render_plan(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    e5 = _extract_e5_closeout(view_model)
    if not e5:
        return OrderedDict([("available", False), ("message", "E5 supervisor closeout is unavailable for this run."), ("panels", OrderedDict()), ("debug", OrderedDict())])
    dominant_regime = _e5_alias_get(e5, ("composite_regime_synthesis", "dominant_expectation_regime"), ("e5_expectation_intelligence_envelope", "e5_expectation_regime_synthesis", "dominant_expectation_regime"), ("e5_expectation_intelligence_envelope", "e5_supervisor_closeout", "dominant_expectation_regime"))
    confidence_band = _e5_alias_get(e5, ("composite_regime_synthesis", "regime_confidence_band"), ("e5_expectation_intelligence_envelope", "e5_expectation_regime_synthesis", "regime_confidence_band"))
    operational_status = _e5_alias_get(e5, ("e5_operational_status", "e5_operational_status"))
    readiness_score = _e5_alias_get(e5, ("e5_operational_status", "operational_readiness_score"))
    panels = OrderedDict([
        ("executive_summary", OrderedDict([
            ("dominant_expectation_regime", _render_value(dominant_regime, fallback="Unavailable")),
            ("regime_confidence_band", _render_value(confidence_band, fallback="Unavailable")),
            ("operational_usefulness_status", _status_label(operational_status)),
            ("operational_readiness_score", _render_value(readiness_score, fallback="Unavailable")),
            ("strongest_supporting_evidence_summary", _render_value(_e5_alias_get(e5, ("supervisor_closeout", "strongest_supporting_evidence_summary"), ("e5_expectation_intelligence_envelope", "e5_supervisor_closeout", "strongest_supporting_evidence")), fallback="Unavailable")),
            ("d8_top_supporting_evidence", _render_value(_nested_get(view_model, ("d8_dashboard", "strongest_supporting_evidence_panel", "evidence_ref")), fallback="Unavailable")),
            ("key_contradiction_summary", _render_value(_e5_alias_get(e5, ("supervisor_closeout", "key_contradiction_summary"), ("e5_expectation_intelligence_envelope", "e5_supervisor_closeout", "key_contradictions"), ("e5_expectation_intelligence_envelope", "e5_evidence_contradiction_synthesis", "contradiction_significance_summary")), fallback="Unavailable")),
            ("temporal_semantic_change_summary", _render_value(_e5_alias_get(e5, ("supervisor_closeout", "temporal_semantic_change_summary"), ("e5_expectation_intelligence_envelope", "e5_supervisor_closeout", "temporal_semantic_change")), fallback="Unavailable")),
            ("caveat_summary", _render_value(_e5_alias_get(e5, ("supervisor_closeout", "caveat_summary"), ("e5_expectation_intelligence_envelope", "e5_supervisor_closeout", "confidence_caveats")), fallback="Unavailable")),
            ("supervisor_closeout_interpretation", _render_value(_e5_alias_get(e5, ("supervisor_closeout", "supervisor_closeout_interpretation"), ("e5_expectation_intelligence_envelope", "e5_supervisor_closeout", "closeout_interpretation")), fallback="Unavailable")),
        ])),
        ("dominant_regime", OrderedDict([
            ("dominant_expectation_regime", _render_value(dominant_regime, fallback="Unavailable")),
            ("supporting_regimes", _to_bullets(_e5_alias_get(e5, ("composite_regime_synthesis", "supporting_regimes"), ("e5_expectation_intelligence_envelope", "e5_expectation_regime_synthesis", "supporting_regimes")))),
            ("regime_confidence_band", _render_value(confidence_band, fallback="Unavailable")),
            ("regime_interpretation", _render_value(_e5_alias_get(e5, ("composite_regime_synthesis", "regime_interpretation"), ("e5_expectation_intelligence_envelope", "e5_expectation_regime_synthesis", "regime_interpretation")), fallback="Unavailable")),
            ("supporting_signal_refs", _to_bullets(_e5_alias_get(e5, ("composite_regime_synthesis", "supporting_signal_refs"), ("e5_expectation_intelligence_envelope", "e5_expectation_regime_synthesis", "supporting_signal_refs")))),
            ("caveats", _to_bullets(_e5_alias_get(e5, ("composite_regime_synthesis", "caveats"), ("e5_expectation_intelligence_envelope", "e5_expectation_regime_synthesis", "caveats")))),
        ])),
        ("operational_usefulness", OrderedDict([
            ("e5_operational_status", _status_label(operational_status)),
            ("operational_readiness_score", _render_value(readiness_score, fallback="Unavailable")),
            ("operational_readiness_interpretation", _render_value(_e5_alias_get(e5, ("e5_operational_status", "operational_readiness_interpretation")), fallback="Unavailable")),
            ("degrading_or_blocking_factors", _to_bullets(_e5_alias_get(e5, ("e5_operational_status", "degrading_or_blocking_factors"), ("e5_operational_status", "blocking_or_degrading_factors")))),
        ])),
        ("contradiction_priority", OrderedDict([
            ("most_important_contradictions", _to_bullets(_e5_alias_get(e5, ("contradiction_priority_synthesis", "most_important_contradictions"), ("e5_expectation_intelligence_envelope", "e5_evidence_contradiction_synthesis", "contradiction_priority_inventory")))),
            ("unresolved_contradiction_clusters", _to_bullets(_e5_alias_get(e5, ("contradiction_priority_synthesis", "unresolved_contradiction_clusters"), ("e5_expectation_intelligence_envelope", "e5_evidence_contradiction_synthesis", "unresolved_contradiction_clusters")))),
            ("contradiction_significance_summary", _render_value(_e5_alias_get(e5, ("contradiction_priority_synthesis", "contradiction_significance_summary"), ("e5_expectation_intelligence_envelope", "e5_evidence_contradiction_synthesis", "contradiction_significance_summary")), fallback="Unavailable")),
            ("affected_themes_or_findings", _to_bullets(_nested_get(e5, ("contradiction_priority_synthesis", "affected_themes_or_findings")))),
        ])),
        ("strongest_evidence", OrderedDict([
            ("strongest_supporting_evidence_refs", _to_bullets(_e5_alias_get(e5, ("evidence_support_synthesis", "strongest_supporting_evidence_refs"), ("e5_expectation_intelligence_envelope", "e5_evidence_contradiction_synthesis", "strongest_supporting_evidence_refs")))),
            ("weakest_supporting_areas", _to_bullets(_e5_alias_get(e5, ("evidence_support_synthesis", "weakest_supporting_areas"), ("e5_expectation_intelligence_envelope", "e5_evidence_contradiction_synthesis", "weakest_supporting_areas")))),
            ("evidence_support_interpretation", _render_value(_e5_alias_get(e5, ("evidence_support_synthesis", "evidence_support_interpretation"), ("e5_expectation_intelligence_envelope", "e5_supervisor_closeout", "closeout_interpretation")), fallback="Unavailable")),
            ("caveats", _to_bullets(_nested_get(e5, ("evidence_support_synthesis", "caveats")))),
        ])),
        ("temporal_semantic_change", OrderedDict([
            ("persistent_themes", _to_bullets(_e5_alias_get(e5, ("temporal_semantic_synthesis", "persistent_themes"), ("e5_expectation_intelligence_envelope", "e5_temporal_semantic_synthesis", "persistent_theme_inventory")))),
            ("emerging_themes", _to_bullets(_e5_alias_get(e5, ("temporal_semantic_synthesis", "emerging_themes"), ("e5_expectation_intelligence_envelope", "e5_temporal_semantic_synthesis", "emerging_theme_inventory")))),
            ("fading_themes", _to_bullets(_e5_alias_get(e5, ("temporal_semantic_synthesis", "fading_themes"), ("e5_expectation_intelligence_envelope", "e5_temporal_semantic_synthesis", "fading_theme_inventory")))),
            ("semantic_drift_assessment", _render_value(_e5_alias_get(e5, ("temporal_semantic_synthesis", "semantic_drift_assessment"), ("e5_expectation_intelligence_envelope", "e5_temporal_semantic_synthesis", "semantic_drift_assessment")), fallback="Unavailable")),
            ("expectation_framing_assessment", _render_value(_e5_alias_get(e5, ("temporal_semantic_synthesis", "expectation_framing_assessment"), ("e5_expectation_intelligence_envelope", "e5_temporal_semantic_synthesis", "expectation_framing_assessment")), fallback="Unavailable")),
            ("temporal_semantic_interpretation", _render_value(_e5_alias_get(e5, ("temporal_semantic_synthesis", "temporal_semantic_interpretation"), ("e5_expectation_intelligence_envelope", "e5_temporal_semantic_synthesis", "temporal_semantic_interpretation")), fallback="Unavailable")),
        ])),
        ("caveat_inventory", OrderedDict([
            ("confidence_constraints", _to_bullets(_e5_alias_get(e5, ("caveat_inventory", "confidence_constraints"), ("e5_expectation_intelligence_envelope", "e5_caveat_inventory", "confidence_constraints")))),
            ("operational_limitations", _to_bullets(_e5_alias_get(e5, ("caveat_inventory", "operational_limitations"), ("e5_expectation_intelligence_envelope", "e5_caveat_inventory", "operational_limitations")))),
            ("consolidated_caveats", _to_bullets(_e5_alias_get(e5, ("caveat_inventory", "consolidated_caveats"), ("e5_expectation_intelligence_envelope", "e5_caveat_inventory", "consolidated_caveats")))),
            ("caveat_severity", _render_value(_e5_alias_get(e5, ("caveat_inventory", "caveat_severity"), ("e5_expectation_intelligence_envelope", "e5_caveat_inventory", "confidence_band")), fallback="Unavailable")),
        ])),
    ])
    debug = OrderedDict([
        ("raw_e5_envelope", deepcopy(e5)),
        ("checksum", e5.get("checksum")),
        ("governance_flags", deepcopy(e5.get("governance_flags") or {})),
        ("supporting_refs", deepcopy(e5.get("supporting_refs") or [])),
        ("full_synthesis_payloads", OrderedDict((k, deepcopy(e5.get(k))) for k in sorted(e5.keys()) if k not in {"checksum", "governance_flags", "supporting_refs"})),
    ])
    return OrderedDict([("available", True), ("message", ""), ("panels", panels), ("debug", debug)])


def render_e6_expectation_executive_summary(view_model: Mapping[str, Any], *, st: Any) -> None:
    plan = build_e6_executive_summary_render_plan(view_model)
    st.markdown("### E6 Expectation Intelligence Executive Summary")
    if not plan.get("available"):
        st.caption(plan.get("message") or "E5 supervisor closeout is unavailable for this run.")
        return
    panels = plan.get("panels", {})
    summary = panels.get("executive_summary", {})
    with st.container():
        cols = st.columns(4)
        cols[0].metric("Dominant Regime", summary.get("dominant_expectation_regime"))
        cols[1].metric("Confidence Band", summary.get("regime_confidence_band"))
        cols[2].metric("Operational Status", summary.get("operational_usefulness_status"))
        cols[3].metric("Readiness Score", summary.get("operational_readiness_score"))
        st.markdown(f"**Strongest Supporting Evidence:** {summary.get('strongest_supporting_evidence_summary')}")
        st.markdown(f"**Key Contradiction:** {summary.get('key_contradiction_summary')}")
        st.markdown(f"**Temporal-Semantic Change:** {summary.get('temporal_semantic_change_summary')}")
        st.markdown(f"**Caveat Summary:** {summary.get('caveat_summary')}")
        st.caption(f"Supervisor interpretation: {summary.get('supervisor_closeout_interpretation')}")
    for panel_key, panel_title in [("dominant_regime", "Dominant Expectation Regime"), ("operational_usefulness", "Operational Usefulness Certification"), ("contradiction_priority", "Contradiction Priority"), ("strongest_evidence", "Strongest Evidence & Weak Areas"), ("temporal_semantic_change", "Temporal-Semantic Change"), ("caveat_inventory", "Caveat Inventory")]:
        panel = panels.get(panel_key, {})
        with st.container():
            st.markdown(f"#### {panel_title}")
            for key, value in panel.items():
                label = key.replace("_", " ").capitalize()
                if isinstance(value, list):
                    st.markdown(f"**{label}:**")
                    if value:
                        for item in value:
                            st.markdown(f"- {item}")
                    else:
                        st.caption("Unavailable")
                else:
                    st.markdown(f"**{label}:** {value}")
    with st.expander("E5 Debug Envelope"):
        st.json(plan.get("debug", {}))


def build_d7_render_plan(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    supervisor = view_model.get("supervisor_summary") if isinstance(view_model.get("supervisor_summary"), Mapping) else {}
    integrity = view_model.get("integrity_overview") if isinstance(view_model.get("integrity_overview"), Mapping) else {}
    e6_plan = build_e6_executive_summary_render_plan(view_model)
    return OrderedDict([
        ("section_order", list(D7_RENDER_SECTION_ORDER)),
        ("e6_expectation_executive_summary", e6_plan),
        ("overview_metrics", OrderedDict([
            ("dominant_fragility_theme", _render_value(supervisor.get("dominant_fragility_theme"))),
            ("expectation_pressure_state", _render_value(supervisor.get("expectation_pressure_concentration"))),
            ("operational_usefulness", _render_value(supervisor.get("operational_usefulness"))),
            ("governance_status", _render_value(supervisor.get("governance_status"))),
            ("confidence_caveat_summary", _render_value(supervisor.get("confidence_caveat_summary"))),
        ])),
        ("integrity_metrics", OrderedDict([
            ("persistence", _render_value(integrity.get("persistence"))),
            ("readback_verification", _render_value(integrity.get("readback_verification"))),
            ("checksum_continuity", _render_value(integrity.get("checksum_continuity"))),
            ("governance_status", _render_value(integrity.get("governance_status"))),
            ("operational_usefulness", _render_value(integrity.get("operational_usefulness"))),
        ])),
    ])


def render_d7_intelligence_overview(view_model: Mapping[str, Any], *, st: Any) -> None:
    plan = build_d7_render_plan(view_model)
    metrics = plan["overview_metrics"]
    st.markdown("### Intelligence Overview")
    with st.container():
        st.caption("Institutional state snapshot across fragility, expectation pressure, governance, and confidence caveats.")
        cols = st.columns(5)
        cols[0].metric("Dominant Fragility Theme", metrics["dominant_fragility_theme"])
        cols[1].metric("Expectation Pressure", metrics["expectation_pressure_state"])
        cols[2].metric("Operational Usefulness", metrics["operational_usefulness"])
        cols[3].metric("Governance Status", metrics["governance_status"])
        cols[4].metric("Confidence Caveat", metrics["confidence_caveat_summary"])


def render_d7_supervisor_interpretation(supervisor_summary: Mapping[str, Any], *, st: Any) -> None:
    summary = supervisor_summary if isinstance(supervisor_summary, Mapping) else {}
    st.markdown("### Supervisor Interpretation")
    with st.container():
        st.markdown(f"**Current SEFI Belief:** {_render_value(summary.get('current_belief'))}")
        st.markdown(f"**Dominant Fragility Themes:** {_render_value(summary.get('dominant_fragility_theme'))}")
        st.markdown(f"**Expectation Pressure Concentration:** {_render_value(summary.get('expectation_pressure_concentration'))}")
        st.markdown(f"**Operational Usefulness:** {_render_value(summary.get('operational_usefulness'))}")
        st.markdown(f"**Current Limitations:** {_render_value(summary.get('current_limitations'))}")
        st.caption(f"Confidence caveat: {_render_value(summary.get('confidence_caveat_summary'))}")


def render_d7_finding_cards(intelligence_cards: list[Mapping[str, Any]], *, st: Any) -> None:
    st.markdown("### Key Finding Cards")
    cards = list(intelligence_cards or [])
    if not cards:
        st.caption("No intelligence finding cards currently available.")
        return
    for card in cards:
        with st.container():
            title = _render_value(card.get("finding_title"), fallback="Untitled Finding")
            st.markdown(f"#### {title}")
            cols = st.columns(3)
            cols[0].markdown(f"**Type:** {_render_value(card.get('finding_type'))}")
            cols[1].markdown(f"**Severity:** {_render_value(card.get('severity'))}")
            cols[2].markdown(f"**Confidence:** {_render_value(card.get('confidence'))}")
            st.markdown(f"**Summary:** {_render_value(card.get('summary'))}")
            st.markdown(f"**Expectation-Fragility Interpretation:** {_render_value(card.get('expectation_fragility_interpretation'))}")
            st.markdown(f"**Why This Matters:** {_render_value(card.get('why_this_matters'))}")
            evidence = list(card.get("evidence_highlights") or [])
            if evidence:
                st.markdown("**Evidence Highlights:**")
                for item in evidence:
                    st.markdown(f"- {_render_value(item)}")
            contradiction = _render_value(card.get("contradiction_or_divergence"), fallback="")
            if contradiction:
                st.caption(f"Contradiction/divergence: {contradiction}")
            with st.expander("Evidence & Debug Context"):
                st.json(OrderedDict([
                    ("internal_id", card.get("internal_id")),
                    ("checksum_ref", card.get("checksum_ref")),
                    ("raw_payload", card.get("raw_payload")),
                ]))
            st.divider()


def render_d7_narrative_sections(narrative_sections: Mapping[str, Any], *, st: Any) -> None:
    st.markdown("### Narrative Sections")
    sections = narrative_sections if isinstance(narrative_sections, Mapping) else {}
    if not sections:
        st.caption("No narrative sections currently available.")
        return
    for title in ("Expectation Pressure", "Market Context", "Semantic Pressure", "Contradictions", "Supervisor Interpretation"):
        section = sections.get(title) if isinstance(sections.get(title), Mapping) else {}
        with st.container():
            st.markdown(f"#### {title}")
            st.markdown(_render_value(section.get("narrative_text"), fallback="No narrative text available."))
            linked = list(section.get("linked_findings") or [])
            evidence = list(section.get("supporting_evidence") or [])
            caveats = list(section.get("caveats") or [])
            if linked:
                st.caption(f"Linked findings: {', '.join(str(x) for x in linked)}")
            if evidence:
                for item in evidence:
                    st.markdown(f"- {item}")
            if caveats:
                st.caption(f"Caveats: {'; '.join(str(x) for x in caveats)}")


def render_d7_evidence_highlights(evidence_highlights: list[Mapping[str, Any]], *, st: Any) -> None:
    st.markdown("### Evidence Highlights")
    items = list(evidence_highlights or [])
    if not items:
        st.caption("No evidence highlights currently available.")
        return
    for item in items:
        with st.container():
            st.markdown(f"- **Summary:** {_render_value(item.get('evidence_summary'))}")
            st.caption(f"Linked finding: {_render_value(item.get('linked_finding'))}")
            st.caption(f"Semantic drivers: {_render_value(item.get('semantic_drivers'))}")
            st.caption(f"KPI/evidence references: {_render_value(item.get('kpi_or_evidence_refs'))}")
            caveat = _render_value(item.get("caveat_or_confidence"), fallback="")
            if caveat:
                st.caption(f"Caveat/confidence: {caveat}")


def render_d7_integrity_overview(integrity_overview: Mapping[str, Any], *, st: Any) -> None:
    metrics = build_d7_render_plan({"integrity_overview": integrity_overview}).get("integrity_metrics", {})
    st.markdown("### Operational Integrity Overview")
    cols = st.columns(5)
    cols[0].metric("Persistence", metrics.get("persistence"))
    cols[1].metric("Readback Verification", metrics.get("readback_verification"))
    cols[2].metric("Checksum Continuity", metrics.get("checksum_continuity"))
    cols[3].metric("Governance Status", metrics.get("governance_status"))
    cols[4].metric("Operational Usefulness", metrics.get("operational_usefulness"))


def render_d7_debug_archive(debug_payload_sections: Mapping[str, Any], *, st: Any) -> None:
    st.markdown("### Expandable Governance / Debug Archive")
    sections = debug_payload_sections if isinstance(debug_payload_sections, Mapping) else {}
    for key, value in sections.items():
        label = key.replace("_", " ").title()
        with st.expander(label):
            st.json(value)


__all__ = [
    "build_e6_executive_summary_render_plan",
    "render_e6_expectation_executive_summary",
    "load_d7_dashboard_findings",
    "load_d7_dashboard_narratives",
    "load_d7_dashboard_evidence_maps",
    "load_d7_dashboard_operational_integrity",
    "build_d7_dashboard_view_model",
    "build_d7_runtime_diagnostics",
    "D7_PHYSICAL_COLUMNS_BY_TABLE",
    "build_d7_intelligence_cards",
    "build_d7_narrative_sections",
    "build_d7_evidence_highlights",
    "build_d7_supervisor_summary",
    "build_d7_integrity_overview",
    "build_d7_debug_payload_sections",
    "D7_RENDER_SECTION_ORDER",
    "build_d7_render_plan",
    "render_d7_intelligence_overview",
    "render_d7_supervisor_interpretation",
    "render_d7_finding_cards",
    "render_d7_narrative_sections",
    "render_d7_evidence_highlights",
    "render_d7_integrity_overview",
    "render_d7_debug_archive",
]
