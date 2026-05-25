"""D7 thin read-only Streamlit dashboard viewer over persisted operationalization records."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from urllib.parse import urlparse
from typing import Any, Mapping

from transmission_layers.expectation_failure.expectation_intelligence import build_e1_expectation_intelligence_payload, build_e2_evidence_interpretation_payload, build_e3_temporal_drift_report, build_e4_semantic_narrative_drift_report, build_e5_expectation_intelligence_envelope, build_d8_evidence_priority_inventory, build_d8_dashboard_view_model, build_d8_1_operational_card_render_model, build_d8_2_payload, build_d8_2_dashboard_view_model, build_d8_5_operational_intelligence_density_verification, assess_d8_5_supabase_backfill_readiness, build_d8_6_evidence_graph_enrichment_linkage_density, build_d8_6_dashboard_view_model, build_d8_b1_controlled_replay_expansion, build_d8_b1_replay_reinforcement_diagnostics, build_d8_b1_controlled_backfill_plan, build_d8_a1_explainability_causal_narratives, build_d8_a1_dashboard_view_model, build_e7_expectation_capability_inventory, build_e7_governance_boundary_inventory, build_d15_backfill_execution_inventory, build_d15_historical_execution_timeline, build_d15_dashboard_enrichment_payload, certify_d15_dashboard_enrichment, build_d16_historical_finding_inventory, build_d16_recurring_finding_clusters, build_d16_regime_linked_finding_narratives, build_d16_operator_narrative_summary, build_d16_dashboard_payload, certify_d16_historical_findings_narrative, build_d17_confidence_attribution_inventory, build_d17_constraint_weight_summary, build_d17_lineage_trace_compression, build_d17_historical_confidence_overlays, build_d17_operator_drilldown_payload, build_d17_dashboard_payload, certify_d17_confidence_lineage_enrichment, build_d18_cross_run_confidence_inventory, build_d18_confidence_delta_summary, build_d18_constraint_persistence_summary, build_d18_regime_transition_confidence_delta, build_d18_operator_triage_queue, build_d18_priority_drilldown_cards, build_d18_dashboard_payload, certify_d18_cross_run_triage

from transmission_layers.expectation_failure.expectation_intelligence.d19_triage_explainability_continuity_taxonomy import build_d19_triage_explainability_inventory, build_d19_rank_change_rationale, build_d19_continuity_degradation_taxonomy, build_d19_constraint_escalation_summary, build_d19_regime_transition_impact_explanations, build_d19_operator_adjudication_notes, build_d19_dashboard_payload, certify_d19_triage_explainability
from transmission_layers.expectation_failure.expectation_intelligence.h1_historical_density_expansion import build_h1_density_expansion_inventory, build_h1_density_gap_analysis, build_h1_expansion_plan, build_h1_operational_density_summary, build_h1_dashboard_payload, certify_h1_density_expansion
from transmission_layers.expectation_failure.expectation_intelligence.h2_governed_replay_expansion_cycle import build_h2_pre_expansion_baseline, build_h2_governed_expansion_recommendation, build_h2_operator_execution_checklist, build_h2_d21_command_template, build_h2_post_expansion_comparison, build_h2_cycle_dashboard_payload, certify_h2_governed_replay_expansion_cycle

D7_SCHEMA_VERSION = "d7_streamlit_dashboard_viewer_v1"
D7_MODULE_VERSION = "1.3.0"
D7_RENDER_SECTION_ORDER = (
    "e6_expectation_executive_summary",
    "d15_historical_operational_intelligence",
    "d16_historical_findings_operator_narrative",
    "d17_historical_confidence_lineage",
    "d18_cross_run_confidence_delta_operator_triage",
    "d19_triage_explainability_continuity_taxonomy",
    "h1_historical_density_expansion",
    "h2_governed_replay_expansion_cycle",
    "intelligence_overview",
    "supervisor_interpretation",
    "key_finding_cards",
    "narrative_sections",
    "evidence_highlights",
    "operational_integrity_overview",
    "replay_evidence_density_summary",
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


def build_d7_historical_runs_from_integrity(*, replay_rows: list[Mapping[str, Any]], findings: list[Mapping[str, Any]], narratives: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    history: list[OrderedDict[str, Any]] = []
    for row in replay_rows:
        if not isinstance(row, Mapping):
            continue
        payload = _payload_map(row)
        replay_metadata = row.get("replay_metadata") if isinstance(row.get("replay_metadata"), Mapping) else {}
        semantic = payload.get("semantic") if isinstance(payload.get("semantic"), Mapping) else {}
        contradictions = payload.get("contradictions") if isinstance(payload.get("contradictions"), Mapping) else {}
        run_id = _as_text(payload.get("run_id") or payload.get("replay_id") or replay_metadata.get("run_id") or replay_metadata.get("replay_id") or row.get("replay_id") or row.get("record_id"))
        run_timestamp = _as_text(payload.get("run_timestamp") or payload.get("timestamp") or replay_metadata.get("run_timestamp") or row.get("created_at"))
        if not (run_id and run_timestamp):
            continue
        history.append(OrderedDict([
            ("run_id", run_id),
            ("run_timestamp", run_timestamp),
            ("timestamp", run_timestamp),
            ("semantic", OrderedDict([("themes", _as_list(semantic.get("themes")))])),
            ("contradictions", OrderedDict([("claims", _as_list(contradictions.get("claims")))])),
            ("findings", deepcopy(findings)),
            ("narratives", deepcopy(narratives)),
            ("evidence_highlights", deepcopy(evidence_maps)),
        ]))
    history.sort(key=lambda r: (_as_text(r.get("run_timestamp")), _as_text(r.get("run_id"))))
    return history


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
        ("raw_d8_2_payload", deepcopy(view_model.get("d8_2_replay_density_expansion") or {})),
        ("raw_d8_5_density_payload", deepcopy(view_model.get("d8_5_operational_intelligence_density_verification") or {})),
        ("raw_d8_5_backfill_payload", deepcopy(view_model.get("d8_5_supabase_backfill_readiness") or {})),
        ("raw_d8_b1_payload", deepcopy(view_model.get("d8_b1_controlled_replay_expansion") or {})),
        ("raw_d8_b1_reinforcement_payload", deepcopy(view_model.get("d8_b1_replay_reinforcement_diagnostics") or {})),
        ("raw_d8_b1_backfill_payload", deepcopy(view_model.get("d8_b1_controlled_backfill_plan") or {})),
        ("raw_d8_a1_payload", deepcopy(view_model.get("d8_a1_explainability_causal_narratives") or {})),
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
    derived_history = build_d7_historical_runs_from_integrity(replay_rows=replay, findings=findings, narratives=narratives, evidence_maps=evidence_maps)
    effective_history = historical_runs_payloads or derived_history
    e3_payload = build_e3_temporal_drift_report(effective_history)
    e4_payload = build_e4_semantic_narrative_drift_report(effective_history)
    e5_payload = build_e5_expectation_intelligence_envelope(e1_payload=e1_payload, e2_payload=e2_payload, e3_payload=e3_payload, e4_payload=e4_payload, d7_context=OrderedDict([("findings", findings), ("narratives", narratives), ("evidence_maps", evidence_maps)]), governance_metadata=OrderedDict([("read_only_surface", True)]))
    d8_payload = build_d8_evidence_priority_inventory(findings, evidence_maps, e2_payload, e3_payload, e4_payload, e5_payload)
    d8_dashboard = build_d8_dashboard_view_model(d8_payload)
    d8_2_payload = build_d8_2_payload(effective_history, findings, narratives, evidence_maps, e2_payload, e3_payload, e4_payload, e5_payload)
    d8_2_dashboard = build_d8_2_dashboard_view_model(d8_2_payload)
    d8_5_density = build_d8_5_operational_intelligence_density_verification(findings=findings, evidence_maps=evidence_maps, replay_metadata_rows=replay, historical_runs_payloads=effective_history, d8_payload=d8_payload, d8_2_payload=d8_2_payload, e2_payload=e2_payload)
    d8_5_backfill = assess_d8_5_supabase_backfill_readiness(density_verification=d8_5_density, findings=findings, historical_runs_payloads=effective_history, replay_metadata_rows=replay, evidence_maps=evidence_maps, e2_payload=e2_payload, d8_2_payload=d8_2_payload)
    d8_6_payload = build_d8_6_evidence_graph_enrichment_linkage_density(findings=findings, evidence_maps=evidence_maps, historical_runs_payloads=effective_history, e2_payload=e2_payload, d8_2_payload=d8_2_payload)
    d8_6_dashboard = build_d8_6_dashboard_view_model(d8_6_payload)
    d8_b1_payload = build_d8_b1_controlled_replay_expansion(replay_metadata_rows=replay, historical_runs_payloads=effective_history, evidence_maps=evidence_maps, e2_payload=e2_payload, d8_2_payload=d8_2_payload)
    d8_b1_reinforcement = build_d8_b1_replay_reinforcement_diagnostics(historical_runs_payloads=effective_history, e2_payload=e2_payload, d8_2_payload=d8_2_payload)
    d8_b1_backfill_plan = build_d8_b1_controlled_backfill_plan(replay_metadata_rows=replay, historical_runs_payloads=effective_history, governance_inventory=build_e7_governance_boundary_inventory(), dry_run=True)
    d8_a1_payload = build_d8_a1_explainability_causal_narratives(d8_2_payload=d8_2_payload, d8_5_payload=d8_5_density, d8_6_payload=d8_6_payload, d8_b1_payload=d8_b1_payload, d8_b1_reinforcement=d8_b1_reinforcement)
    d8_a1_dashboard = build_d8_a1_dashboard_view_model(d8_a1_payload)
    d15_inventory = build_d15_backfill_execution_inventory(d11_report_payload=d8_b1_payload.get("d11_report_payload"), d12_report_payload=d8_b1_payload.get("d12_report_payload"), d13_report_payload=d8_b1_payload.get("d13_report_payload"), d14_report_payload=d8_b1_payload.get("d14_report_payload"))
    d15_timeline = build_d15_historical_execution_timeline(d11_report_payload=d8_b1_payload.get("d11_report_payload"), d12_report_payload=d8_b1_payload.get("d12_report_payload"), d13_report_payload=d8_b1_payload.get("d13_report_payload"))
    d15_dashboard_enrichment = build_d15_dashboard_enrichment_payload(backfill_inventory=d15_inventory, historical_execution_timeline=d15_timeline, d14_report_payload=d8_b1_payload.get("d14_report_payload"))
    d15_certification = certify_d15_dashboard_enrichment(backfill_inventory=d15_inventory, dashboard_enrichment_payload=d15_dashboard_enrichment)
    d16_inventory = build_d16_historical_finding_inventory(d11_report_payload=d8_b1_payload.get("d11_report_payload"), d12_report_payload=d8_b1_payload.get("d12_report_payload"), d13_report_payload=d8_b1_payload.get("d13_report_payload"), d14_report_payload=d8_b1_payload.get("d14_report_payload"), d15_dashboard_enrichment_payload=d15_dashboard_enrichment, d9_report_payload=None)
    d16_clusters = build_d16_recurring_finding_clusters(historical_finding_inventory=d16_inventory, d12_report_payload=d8_b1_payload.get("d12_report_payload"))
    d16_regime_narratives = build_d16_regime_linked_finding_narratives(recurring_finding_clusters=d16_clusters, d13_report_payload=d8_b1_payload.get("d13_report_payload"), d14_report_payload=d8_b1_payload.get("d14_report_payload"))
    d16_summary = build_d16_operator_narrative_summary(historical_finding_inventory=d16_inventory, recurring_finding_clusters=d16_clusters, regime_linked_finding_narratives=d16_regime_narratives, d15_dashboard_enrichment_payload=d15_dashboard_enrichment)
    d16_dashboard_payload = build_d16_dashboard_payload(historical_finding_inventory=d16_inventory, recurring_finding_clusters=d16_clusters, regime_linked_finding_narratives=d16_regime_narratives, operator_narrative_summary=d16_summary)
    d16_certification = certify_d16_historical_findings_narrative(historical_finding_inventory=d16_inventory, recurring_finding_clusters=d16_clusters, regime_linked_finding_narratives=d16_regime_narratives, operator_narrative_summary=d16_summary, dashboard_payload=d16_dashboard_payload)
    d17_inventory = build_d17_confidence_attribution_inventory(d16_dashboard_payload=d16_dashboard_payload, d15_dashboard_enrichment_payload=d15_dashboard_enrichment, d12_report_payload=d8_b1_payload.get("d12_report_payload"), d13_report_payload=d8_b1_payload.get("d13_report_payload"))
    d17_constraints = build_d17_constraint_weight_summary(confidence_attribution_inventory=d17_inventory, d12_report_payload=d8_b1_payload.get("d12_report_payload"))
    d17_lineage = build_d17_lineage_trace_compression(d16_dashboard_payload=d16_dashboard_payload, d11_report_payload=d8_b1_payload.get("d11_report_payload"), d14_report_payload=d8_b1_payload.get("d14_report_payload"))
    d17_overlays = build_d17_historical_confidence_overlays(confidence_attribution_inventory=d17_inventory, constraint_weight_summary=d17_constraints, lineage_trace_compression=d17_lineage)
    d17_drilldowns = build_d17_operator_drilldown_payload(confidence_attribution_inventory=d17_inventory, lineage_trace_compression=d17_lineage, d16_dashboard_payload=d16_dashboard_payload)
    d17_dashboard_payload = build_d17_dashboard_payload(confidence_attribution_inventory=d17_inventory, constraint_weight_summary=d17_constraints, lineage_trace_compression=d17_lineage, historical_confidence_overlays=d17_overlays, operator_drilldown_payload=d17_drilldowns)
    d17_certification = certify_d17_confidence_lineage_enrichment(d16_dashboard_payload=d16_dashboard_payload, historical_confidence_overlays=d17_overlays, lineage_trace_compression=d17_lineage, dashboard_payload=d17_dashboard_payload)
    d18_inventory = build_d18_cross_run_confidence_inventory(current_run_payload=d17_dashboard_payload, prior_run_payload=None, d17_confidence_overlays=d17_overlays, d17_operator_drilldowns=d17_drilldowns)
    d18_delta_summary = build_d18_confidence_delta_summary(comparison_inventory=d18_inventory)
    d18_constraint_summary = build_d18_constraint_persistence_summary(comparison_inventory=d18_inventory)
    d18_regime_delta = build_d18_regime_transition_confidence_delta(comparison_inventory=d18_inventory, d16_dashboard_payload=d16_dashboard_payload)
    d18_triage_queue = build_d18_operator_triage_queue(comparison_inventory=d18_inventory, constraint_persistence_summary=d18_constraint_summary, regime_transition_confidence_delta=d18_regime_delta)
    d18_cards = build_d18_priority_drilldown_cards(triage_queue=d18_triage_queue)
    d18_dashboard_payload = build_d18_dashboard_payload(comparison_inventory=d18_inventory, delta_summary=d18_delta_summary, constraint_persistence_summary=d18_constraint_summary, regime_transition_confidence_delta=d18_regime_delta, operator_triage_queue=d18_triage_queue, priority_drilldown_cards=d18_cards)
    d18_certification = certify_d18_cross_run_triage(comparison_inventory=d18_inventory, delta_summary=d18_delta_summary, triage_queue=d18_triage_queue, dashboard_payload=d18_dashboard_payload)

    d19_inventory = build_d19_triage_explainability_inventory(d18_triage_queue=d18_triage_queue, d18_cross_run_confidence_inventory=d18_inventory, d17_confidence_overlays=d17_overlays, d16_dashboard_payload=d16_dashboard_payload)
    d19_rationales = build_d19_rank_change_rationale(triage_explainability_inventory=d19_inventory)
    d19_taxonomy = build_d19_continuity_degradation_taxonomy(triage_explainability_inventory=d19_inventory, d18_cross_run_confidence_inventory=d18_inventory)
    d19_constraints = build_d19_constraint_escalation_summary(triage_explainability_inventory=d19_inventory, continuity_taxonomy=d19_taxonomy)
    d19_regime = build_d19_regime_transition_impact_explanations(triage_explainability_inventory=d19_inventory, d18_regime_transition_confidence_delta=d18_regime_delta)
    d19_notes = build_d19_operator_adjudication_notes(triage_explainability_inventory=d19_inventory, continuity_taxonomy=d19_taxonomy)
    d19_dashboard = build_d19_dashboard_payload(triage_explainability_inventory=d19_inventory, rank_change_rationales=d19_rationales, continuity_taxonomy=d19_taxonomy, constraint_escalation_summary=d19_constraints, regime_transition_impact_explanations=d19_regime, operator_adjudication_notes=d19_notes)
    d19_certification = certify_d19_triage_explainability(triage_explainability_inventory=d19_inventory, rank_change_rationales=d19_rationales, continuity_taxonomy=d19_taxonomy, dashboard_payload=d19_dashboard)
    h1_inventory = build_h1_density_expansion_inventory(historical_runs=effective_history, d16_dashboard_payload=d16_dashboard_payload, d17_dashboard_payload=d17_dashboard_payload, d18_dashboard_payload=d18_dashboard_payload)
    h1_gap_analysis = build_h1_density_gap_analysis(density_inventory=h1_inventory)
    h1_plan = build_h1_expansion_plan(density_inventory=h1_inventory, density_gap_analysis=h1_gap_analysis)
    h1_summary = build_h1_operational_density_summary(density_inventory=h1_inventory, density_gap_analysis=h1_gap_analysis)
    h1_dashboard = build_h1_dashboard_payload(density_inventory=h1_inventory, density_gap_analysis=h1_gap_analysis, expansion_plan=h1_plan, operational_density_summary=h1_summary)
    h1_certification = certify_h1_density_expansion(density_inventory=h1_inventory, density_gap_analysis=h1_gap_analysis, expansion_plan=h1_plan, dashboard_payload=h1_dashboard)
    h2_baseline = build_h2_pre_expansion_baseline(h1_dashboard_payload=h1_dashboard, h1_inventory=h1_inventory, d7_view_model=None, h1_certification=h1_certification)
    h2_recommendation = build_h2_governed_expansion_recommendation(h1_expansion_plan=h1_plan, pre_expansion_baseline=h2_baseline)
    h2_checklist = build_h2_operator_execution_checklist(recommendation=h2_recommendation)
    h2_command_template = build_h2_d21_command_template(recommendation=h2_recommendation)
    h2_post = build_h2_post_expansion_comparison(pre_expansion_baseline=h2_baseline, post_h1_inventory=None)
    h2_dashboard = build_h2_cycle_dashboard_payload(pre_expansion_baseline=h2_baseline, governed_expansion_recommendation=h2_recommendation, operator_execution_checklist=h2_checklist, d21_command_template=h2_command_template, post_expansion_comparison=h2_post)
    h2_certification = certify_h2_governed_replay_expansion_cycle(pre_expansion_baseline=h2_baseline, governed_expansion_recommendation=h2_recommendation, operator_execution_checklist=h2_checklist, d21_command_template=h2_command_template, cycle_dashboard_payload=h2_dashboard)
    if isinstance(d8_6_payload.get("strongest_supporting_evidence"), Mapping) and _as_text((d8_6_payload.get("strongest_supporting_evidence") or {}).get("evidence_ref")):
        d8_dashboard["strongest_supporting_evidence_panel"] = deepcopy(d8_6_payload.get("strongest_supporting_evidence"))
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
        ("d8_2_replay_density_expansion", d8_2_payload),
        ("d8_2_dashboard", d8_2_dashboard),
        ("d8_5_operational_intelligence_density_verification", d8_5_density),
        ("d8_5_supabase_backfill_readiness", d8_5_backfill),
        ("d8_6_evidence_graph_enrichment", d8_6_payload),
        ("d8_6_dashboard", d8_6_dashboard),
        ("d8_b1_controlled_replay_expansion", d8_b1_payload),
        ("d8_b1_replay_reinforcement_diagnostics", d8_b1_reinforcement),
        ("d8_b1_controlled_backfill_plan", d8_b1_backfill_plan),
        ("d8_a1_explainability_causal_narratives", d8_a1_payload),
        ("d8_a1_dashboard", d8_a1_dashboard),
        ("d15_historical_backfill_execution_enrichment", d15_dashboard_enrichment),
        ("d15_historical_execution_timeline", d15_timeline),
        ("d15_dashboard_enrichment_certification", d15_certification),
        ("d16_historical_findings_operator_narrative", d16_dashboard_payload),
        ("d16_historical_findings_narrative_certification", d16_certification),
        ("d17_historical_confidence_lineage", d17_dashboard_payload),
        ("d17_confidence_lineage_certification", d17_certification),
        ("d18_cross_run_confidence_delta_operator_triage", d18_dashboard_payload),
        ("d18_cross_run_triage_certification", d18_certification),
        ("d19_triage_explainability_continuity_taxonomy", d19_dashboard),
        ("d19_triage_explainability_certification", d19_certification),
        ("h1_historical_density_expansion", h1_dashboard),
        ("h1_historical_density_expansion_certification", h1_certification),
        ("h2_governed_replay_expansion_cycle", h2_dashboard),
        ("h2_governed_replay_expansion_cycle_certification", h2_certification),
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


def render_d8_1_operational_insight_cards(view_model: Mapping[str, Any], *, st: Any) -> None:
    st.markdown("### D8.1 Operational Insight Cards")
    card_model = build_d8_1_operational_card_render_model(view_model.get("d8_evidence_prioritization") if isinstance(view_model, Mapping) else {})
    if not card_model.get("available"):
        st.caption(card_model.get("message") or "D8.1 cards unavailable.")
        return
    support = card_model.get("supporting_evidence", {})
    contradiction = card_model.get("contradiction", {})
    cols = st.columns(3)
    cols[0].metric("Strongest Supporting Evidence", _render_value(support.get("strongest_supporting_evidence_ref"), fallback="Unavailable"))
    cols[1].metric("Contradiction Severity", _render_value(contradiction.get("severity"), fallback="Unavailable"))
    cols[2].metric("Evidence Priority", _render_value(support.get("priority_score"), fallback="Unavailable"))
    st.markdown(f"**Strongest Contradicting Evidence:** {_render_value(', '.join(str(x) for x in _as_list(contradiction.get('strongest_contradicting_evidence_refs'))), fallback='Unavailable')}")
    st.markdown(f"**Operational Interpretation:** {_render_value(card_model.get('operational_interpretation'), fallback='Unavailable')}")
    caveats = _as_list(card_model.get("confidence_caveats"))
    st.markdown("**Confidence Caveats:**")
    if caveats:
        for caveat in caveats:
            st.markdown(f"- {caveat}")
    else:
        st.caption("No caveats were provided.")
    st.caption(f"Lineage summary: {_render_value(card_model.get('lineage_summary'), fallback='Unavailable')}")
    for card in _as_list(card_model.get("cards")):
        st.markdown(f"**{_render_value(card.get('section'), fallback='Insight')}:** {_render_value(card.get('content'))}")
    with st.expander("D8.1 Debug/Archive Payload"):
        st.json(card_model.get("debug", {}))


def render_d8_2_replay_evidence_density_summary(view_model: Mapping[str, Any], *, st: Any) -> None:
    st.markdown("### D8.2 Replay & Evidence Density")
    dashboard = view_model.get("d8_2_dashboard") if isinstance(view_model, Mapping) else {}
    dashboard = dashboard if isinstance(dashboard, Mapping) else {}
    if not dashboard:
        st.caption("D8.2 replay/evidence density summaries are unavailable.")
        return

    semantic = dashboard.get("semantic_persistence_summary") if isinstance(dashboard.get("semantic_persistence_summary"), Mapping) else {}
    density = dashboard.get("evidence_density_indicators") if isinstance(dashboard.get("evidence_density_indicators"), Mapping) else {}
    replay = dashboard.get("replay_continuity_summary") if isinstance(dashboard.get("replay_continuity_summary"), Mapping) else {}
    regime = dashboard.get("regime_transition_history") if isinstance(dashboard.get("regime_transition_history"), Mapping) else {}
    contradiction = dashboard.get("persistent_contradiction_tracking") if isinstance(dashboard.get("persistent_contradiction_tracking"), Mapping) else {}
    evolution = dashboard.get("thematic_evolution_summary") if isinstance(dashboard.get("thematic_evolution_summary"), Mapping) else {}

    cols = st.columns(3)
    cols[0].metric("Semantic Persistence", _render_value(semantic.get("persistence_status"), fallback="insufficient_history"))
    cols[1].metric("Evidence Density", _render_value(density.get("evidence_density_classification"), fallback="sparse"))
    cols[2].metric("Replay Continuity", _render_value(replay.get("continuity_status"), fallback="NO_HISTORY_AVAILABLE"))
    st.markdown(f"**Regime Transitions:** {_render_value(regime.get('transition_count'), fallback='0')} observed.")
    st.markdown(f"**Persistent Contradictions:** {_render_value(', '.join(str(x) for x in _as_list(contradiction.get('persistent_contradiction_themes'))), fallback='None observed')}")
    st.markdown(f"**Theme Evolution:** {_render_value(evolution.get('evolution_interpretation'), fallback='No evolution summary available.')}")
    st.markdown(f"**Replay-linked Evidence Lineage:** {_render_value(', '.join(str(x) for x in _as_list(density.get('replay_linked_evidence_refs'))), fallback='Unavailable')}")
    with st.expander("D8.2 Debug/Archive Payload"):
        st.json(OrderedDict([
            ("d8_2_dashboard", deepcopy(dashboard)),
            ("d8_2_raw_payload", deepcopy(view_model.get("d8_2_replay_density_expansion") if isinstance(view_model, Mapping) else {})),
        ]))


def build_d7_render_plan(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    supervisor = view_model.get("supervisor_summary") if isinstance(view_model.get("supervisor_summary"), Mapping) else {}
    integrity = view_model.get("integrity_overview") if isinstance(view_model.get("integrity_overview"), Mapping) else {}
    e6_plan = build_e6_executive_summary_render_plan(view_model)
    return OrderedDict([
        ("section_order", list(D7_RENDER_SECTION_ORDER)),
        ("e6_expectation_executive_summary", e6_plan),
        ("d15_historical_operational_intelligence", build_d15_historical_operational_intelligence_render_plan(view_model)),
        ("d16_historical_findings_operator_narrative", build_d16_historical_findings_operator_narrative_render_plan(view_model)),
        ("d17_historical_confidence_lineage", build_d17_historical_confidence_lineage_render_plan(view_model)),
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


def build_d15_historical_operational_intelligence_render_plan(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    enrichment = view_model.get("d15_historical_backfill_execution_enrichment") if isinstance(view_model, Mapping) else {}
    timeline = _as_list(view_model.get("d15_historical_execution_timeline")) if isinstance(view_model, Mapping) else []
    certification = view_model.get("d15_dashboard_enrichment_certification") if isinstance(view_model, Mapping) else {}
    enrichment = enrichment if isinstance(enrichment, Mapping) else {}
    certification = certification if isinstance(certification, Mapping) else {}
    if not enrichment:
        return OrderedDict([
            ("available", False),
            ("message", "Historical backfill execution enrichment is unavailable for this run."),
            ("primary_sections", OrderedDict()),
            ("governance_debug_details", OrderedDict()),
        ])
    return OrderedDict([
        ("available", True),
        ("message", ""),
        ("primary_sections", OrderedDict([
            ("Historical Replay Depth", _render_value(enrichment.get("historical_replay_depth"), fallback="Unavailable")),
            ("Historical Expectation Regime", _render_value(enrichment.get("historical_expectation_regime"), fallback="Unavailable")),
            ("Regime Evolution Timeline / Cards", _as_list(enrichment.get("regime_evolution_timeline_cards"))),
            ("Strongest Recurring Constraints", _as_list(enrichment.get("strongest_recurring_constraints"))),
            ("Strongest Historical Patterns", _as_list(enrichment.get("strongest_historical_patterns"))),
            ("Continuity Status", _render_value(enrichment.get("historical_continuity_status"), fallback="Unavailable")),
            ("Supervisory Operational Summary", _render_value(enrichment.get("supervisory_operational_summary"), fallback="Unavailable")),
            ("Supervisory Risk Band", _render_value(enrichment.get("supervisory_risk_band"), fallback="Unavailable")),
            ("Operational Recommendation", _render_value(enrichment.get("operational_recommendation"), fallback="Unavailable")),
        ])),
        ("governance_debug_details", OrderedDict([
            ("dashboard_enrichment_certification", deepcopy(certification)),
            ("governance_debug_details", deepcopy(enrichment.get("governance_debug_details") or {})),
            ("payload_checksum", enrichment.get("payload_checksum")),
            ("timeline_events", deepcopy(timeline)),
        ])),
    ])


def render_d15_historical_operational_intelligence(view_model: Mapping[str, Any], *, st: Any) -> None:
    plan = build_d15_historical_operational_intelligence_render_plan(view_model)
    st.markdown("### D15 Historical Operational Intelligence")
    if not plan.get("available"):
        st.caption(plan.get("message") or "Historical operational intelligence is unavailable.")
        return
    primary = plan.get("primary_sections", {})
    cols = st.columns(3)
    cols[0].metric("Historical Replay Depth", primary.get("Historical Replay Depth"))
    cols[1].metric("Historical Expectation Regime", primary.get("Historical Expectation Regime"))
    cols[2].metric("Continuity Status", primary.get("Continuity Status"))
    st.markdown(f"**Supervisory Operational Summary:** {primary.get('Supervisory Operational Summary')}")
    st.markdown(f"**Supervisory Risk Band:** {primary.get('Supervisory Risk Band')}")
    st.markdown(f"**Operational Recommendation:** {primary.get('Operational Recommendation')}")
    for section in ("Regime Evolution Timeline / Cards", "Strongest Recurring Constraints", "Strongest Historical Patterns"):
        st.markdown(f"**{section}:**")
        values = _as_list(primary.get(section))
        if values:
            for value in values:
                st.markdown(f"- {_render_value(value)}")
        else:
            st.caption("Unavailable")
    with st.expander("D15 Governance / Checksum / Audit Details"):
        st.json(plan.get("governance_debug_details", {}))


def build_d16_historical_findings_operator_narrative_render_plan(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    payload = view_model.get("d16_historical_findings_operator_narrative") if isinstance(view_model, Mapping) else {}
    cert = view_model.get("d16_historical_findings_narrative_certification") if isinstance(view_model, Mapping) else {}
    payload = payload if isinstance(payload, Mapping) else {}
    cert = cert if isinstance(cert, Mapping) else {}
    if not payload:
        return OrderedDict([("available", False), ("message", "D16 historical findings/operator narrative is unavailable for this run."), ("primary_sections", OrderedDict()), ("governance_debug_details", OrderedDict())])
    return OrderedDict([
        ("available", True),
        ("message", ""),
        ("primary_sections", OrderedDict([
            ("Recurring historical findings", _as_list(payload.get("recurring_historical_findings"))),
            ("Regime-linked findings", _as_list(payload.get("regime_linked_findings"))),
            ("What changed", _as_list(payload.get("what_changed"))),
            ("What persisted", _as_list(payload.get("what_persisted"))),
            ("What degraded", _as_list(payload.get("what_degraded"))),
            ("What improved", _as_list(payload.get("what_improved"))),
            ("Recurrent confidence constraints", _as_list(payload.get("recurrent_confidence_constraints"))),
            ("Operator narrative summary", _render_value(payload.get("operator_narrative_summary"), fallback="Unavailable")),
            ("Operator attention next", _as_list(payload.get("operator_attention_next"))),
        ])),
        ("governance_debug_details", OrderedDict([("certification", deepcopy(cert)), ("governance_lineage_details", deepcopy(payload.get("governance_lineage_details") or {})), ("payload_checksum", payload.get("payload_checksum"))])),
    ])


def render_d16_historical_findings_operator_narrative(view_model: Mapping[str, Any], *, st: Any) -> None:
    plan = build_d16_historical_findings_operator_narrative_render_plan(view_model)
    st.markdown("### D16 Historical Findings & Operator Narrative")
    if not plan.get("available"):
        st.caption(plan.get("message") or "D16 historical findings/operator narrative unavailable.")
        return
    primary = plan.get("primary_sections", {})
    for section in ("Recurring historical findings", "Regime-linked findings", "What changed", "What persisted", "What degraded", "What improved", "Recurrent confidence constraints", "Operator attention next"):
        st.markdown(f"**{section}:**")
        values = _as_list(primary.get(section))
        if values:
            for value in values:
                st.markdown(f"- {_render_value(value)}")
        else:
            st.caption("Unavailable")
    st.markdown(f"**Operator narrative summary:** {primary.get('Operator narrative summary')}")
    with st.expander("D16 Governance / Lineage Details"):
        st.json(plan.get("governance_debug_details", {}))


def build_d17_historical_confidence_lineage_render_plan(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    payload = view_model.get("d17_historical_confidence_lineage") if isinstance(view_model, Mapping) else {}
    cert = view_model.get("d17_confidence_lineage_certification") if isinstance(view_model, Mapping) else {}
    payload = payload if isinstance(payload, Mapping) else {}
    cert = cert if isinstance(cert, Mapping) else {}
    if not payload:
        return OrderedDict([("available", False), ("message", "D17 historical confidence/lineage enrichment is unavailable for this run."), ("primary_sections", OrderedDict()), ("governance_debug_details", OrderedDict())])
    return OrderedDict([("available", True), ("message", ""), ("primary_sections", OrderedDict([
        ("Historical Finding Confidence Overview", _as_list(payload.get("Historical Finding Confidence"))),
        ("Confidence-Limiting Constraints", payload.get("Confidence-Limiting Constraints") if isinstance(payload.get("Confidence-Limiting Constraints"), Mapping) else {}),
        ("Structural Fragility Drivers", _as_list(payload.get("Structural Fragility Drivers"))),
        ("Replay Sufficiency Summary", _as_list(payload.get("Replay Sufficiency Summary"))),
        ("Regime Stability Summary", _as_list(payload.get("Regime Stability Summary"))),
        ("Operator Drilldowns", payload.get("Lineage Drilldowns") if isinstance(payload.get("Lineage Drilldowns"), Mapping) else {}),
        ("Compressed Lineage References", payload.get("Compressed Lineage References") if isinstance(payload.get("Compressed Lineage References"), Mapping) else {}),
    ])), ("governance_debug_details", OrderedDict([("certification", deepcopy(cert)), ("governance_lineage_details", deepcopy(payload.get("governance_lineage_details") or {}))]))])


def render_d17_historical_confidence_lineage(view_model: Mapping[str, Any], *, st: Any) -> None:
    plan = build_d17_historical_confidence_lineage_render_plan(view_model)
    st.markdown("### D17 Historical Confidence Attribution & Lineage Compression")
    if not plan.get("available"):
        st.caption(plan.get("message") or "D17 historical confidence/lineage unavailable.")
        return
    primary = plan.get("primary_sections", {})
    for section in ("Historical Finding Confidence Overview", "Confidence-Limiting Constraints", "Structural Fragility Drivers", "Replay Sufficiency Summary", "Regime Stability Summary"):
        st.markdown(f"**{section}:**")
        value = primary.get(section)
        if isinstance(value, list):
            for item in value:
                st.markdown(f"- {_render_value(item)}")
        elif isinstance(value, Mapping):
            st.json(value)
    st.markdown("**Operator Drilldowns:**")
    st.json(primary.get("Operator Drilldowns") or {})
    st.markdown("**Compressed Lineage References:**")
    st.json(primary.get("Compressed Lineage References") or {})
    with st.expander("D17 Governance / Lineage Details"):
        st.json(plan.get("governance_debug_details", {}))


def render_d18_cross_run_confidence_delta_operator_triage(view_model: Mapping[str, Any], *, st: Any) -> None:
    payload = view_model.get("d18_cross_run_confidence_delta_operator_triage") if isinstance(view_model, Mapping) else {}
    if not isinstance(payload, Mapping) or not payload:
        st.markdown("### D18 Cross-Run Confidence Delta & Operator Triage")
        st.caption("D18 cross-run triage is unavailable for this run.")
        return
    st.markdown("### D18 Cross-Run Confidence Delta & Operator Triage")
    triage = _as_list(payload.get("Operator Triage Queue"))
    if triage:
        st.markdown("**Operator Triage Queue**")
        for row in triage[:5]:
            item = _payload_map(row)
            st.markdown(f"- P{_render_value(item.get('priority_rank'))} [{_render_value(item.get('priority_band'))}] {_render_value(item.get('finding_or_cluster_ref'))}: {_render_value(item.get('review_reason'))}")
    st.markdown(f"**Strengthened / Weakened / Stable:** {len(_as_list(payload.get('Strengthened Findings')))} / {len(_as_list(payload.get('Weakened Findings')))} / {len(_as_list(payload.get('Stable Findings')))}")
    st.markdown(f"**Newly Observed / No Longer Observed:** {len(_as_list(payload.get('Newly Observed Findings')))} / {len(_as_list(payload.get('No Longer Observed Findings')))}")
    cards = _as_list(payload.get("Priority Drilldown Cards"))
    if cards:
        st.markdown("**Priority Drilldown Cards**")
        for c in cards[:3]:
            card = _payload_map(c)
            st.caption(f"{_render_value(card.get('title'))} — {_render_value(card.get('operator_review_hint'))}")
    with st.expander("D18 Governance / Lineage Details"):
        st.json(payload.get("Governance/Lineage Details", {}))


def render_d19_triage_explainability_continuity_taxonomy(view_model: Mapping[str, Any], *, st: Any) -> None:
    payload = view_model.get("d19_triage_explainability_continuity_taxonomy") if isinstance(view_model, Mapping) else {}
    if not isinstance(payload, Mapping) or not payload:
        st.markdown("### D19 Triage Explainability & Continuity Degradation Taxonomy")
        st.caption("D19 explainability/taxonomy is unavailable for this run.")
        return
    st.markdown("### D19 Triage Explainability & Continuity Degradation Taxonomy")
    st.markdown("**Triage Explainability Overview**")
    for row in _as_list(payload.get("Triage Explainability Overview"))[:5]:
        r = _payload_map(row)
        st.markdown(f"- {_render_value(r.get('explanation_key'))} [{_render_value(r.get('triage_priority_band'))}] rank {_render_value(r.get('rank_position'))} ({_render_value(r.get('rank_change_direction'))})")
    st.markdown("**Rank Change Rationales**")
    for row in _as_list(payload.get("Rank Change Rationales"))[:5]:
        r = _payload_map(row)
        st.caption(f"{_render_value(r.get('explanation_key'))}: {_render_value(r.get('rank_change_rationale'))}")
    st.markdown("**Continuity Degradation Taxonomy**")
    for row in _as_list(payload.get("Continuity Degradation Taxonomy"))[:5]:
        r = _payload_map(row)
        st.markdown(f"- {_render_value(r.get('category'))} ({_render_value(r.get('severity_band'))})")
    st.markdown("**Constraint Escalation / De-escalation**")
    st.json(payload.get("Constraint Escalation / De-escalation") or {})
    st.markdown("**Regime Transition Impact Explanations**")
    for row in _as_list(payload.get("Regime Transition Impact Explanations"))[:3]:
        r = _payload_map(row)
        st.markdown(f"- {_render_value(r.get('transition_id'))}: {_render_value(r.get('impact_explanation'))}")
    st.markdown("**Operator Adjudication Notes**")
    for row in _as_list(payload.get("Operator Adjudication Notes"))[:5]:
        r = _payload_map(row)
        st.markdown(f"- {_render_value(r.get('note_type'))}: {_render_value(r.get('note'))}")
    with st.expander("D19 Governance/Lineage Details"):
        st.json(payload.get("Governance / Lineage Details", {}))


def render_h1_historical_density_expansion(view_model: Mapping[str, Any], *, st: Any) -> None:
    payload = view_model.get("h1_historical_density_expansion") if isinstance(view_model, Mapping) else {}
    if not isinstance(payload, Mapping):
        st.markdown("### H1 Historical Density Expansion")
        st.caption("H1 historical density expansion is unavailable for this run.")
        return
    st.markdown("### H1 Historical Density Expansion")
    for section in (
        "Historical Density Overview",
        "Replay Coverage",
        "Regime Diversity",
        "Contradiction Evolution Richness",
        "Continuity Linkage Density",
        "Recurring Finding Density",
        "Confidence Movement Density",
        "Density Gap Analysis",
        "Recommended Expansion Plan",
    ):
        st.markdown(f"**{section}**")
        st.json(payload.get(section, {}))
    with st.expander("H1 Governance/Lineage Details"):
        st.json(payload.get("Governance/Lineage Details", {}))


def render_h2_governed_replay_expansion_cycle(view_model: Mapping[str, Any], *, st: Any) -> None:
    payload = view_model.get("h2_governed_replay_expansion_cycle") if isinstance(view_model, Mapping) else {}
    if not isinstance(payload, Mapping) or not payload:
        st.markdown("### H2 Governed Replay Expansion Execution Cycle")
        st.caption("H2 governed replay expansion cycle is unavailable for this run.")
        return
    st.markdown("### H2 Governed Replay Expansion Execution Cycle")
    st.markdown("**Governed Expansion Recommendation**")
    st.json(payload.get("Governed Expansion Recommendation", {}))
    st.markdown("**Pre-Expansion Baseline**")
    st.json(payload.get("Pre-Expansion Baseline", {}))
    st.markdown("**Operator Execution Checklist**")
    for item in _as_list(payload.get("Operator Execution Checklist")):
        row = _payload_map(item)
        st.markdown(f"- {_render_value(row.get('step'))}: {_render_value(row.get('required'))}")
    st.markdown("**D21 Command Template**")
    st.code(_render_value(payload.get("D21 Command Template"), fallback="Unavailable"), language="bash")
    post = _payload_map(payload.get("Post-Expansion Comparison"))
    if post:
        st.markdown("**Post-Expansion Comparison**")
        st.json(post)
    with st.expander("H2 Governance/Lineage Controls"):
        st.json(payload.get("Governance/Lineage Controls", {}))


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
    "render_d8_1_operational_insight_cards",
    "render_d8_2_replay_evidence_density_summary",
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
    "build_d15_historical_operational_intelligence_render_plan",
    "render_d15_historical_operational_intelligence",
    "build_d16_historical_findings_operator_narrative_render_plan",
    "render_d16_historical_findings_operator_narrative",
    "build_d17_historical_confidence_lineage_render_plan",
    "render_d17_historical_confidence_lineage",
    "render_d18_cross_run_confidence_delta_operator_triage",
    "render_h1_historical_density_expansion",
    "render_h2_governed_replay_expansion_cycle",
    "render_d7_intelligence_overview",
    "render_d7_supervisor_interpretation",
    "render_d7_finding_cards",
    "render_d7_narrative_sections",
    "render_d7_evidence_highlights",
    "render_d7_integrity_overview",
    "render_d7_debug_archive",
]
