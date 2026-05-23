"""Deterministic O6 finding persistence/export contract layer.

O6 operationalizes O5 finding payloads into stable flat records for dashboard/export
pipelines. This layer defines export contracts only and never performs persistence.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

CERTIFIED = "CERTIFIED_FINDING_EXPORT_READY"
DEGRADED = "DEGRADED_FINDING_EXPORT_READY"
BLOCKED = "BLOCKED_FINDING_EXPORT_INVALID"

FORBIDDEN_CAPABILITIES = (
    "database_writes",
    "file_writes",
    "live_market_fetching",
    "network_calls",
    "llm_calls",
    "trading_instructions",
    "portfolio_optimization",
    "predictive_return_forecasts",
    "hidden_non_determinism",
    "current_time_dependency",
)


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _ordered_str_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(v) for v in values if str(v)})


def _normalize_payload(o5_payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = deepcopy(dict(o5_payload or {}))
    findings = src.get("semantic_findings", [])
    if not isinstance(findings, list):
        findings = findings
    narratives = src.get("dashboard_insight_narratives", {})
    evidence_map = src.get("finding_evidence_map", {})
    supervisor = src.get("supervisor_interpretation_panel", {})
    cert = src.get("certification", {})
    return OrderedDict([
        ("o5_version", str(src.get("o5_version") or "")),
        ("o5_checksum", str(src.get("o5_checksum") or "")),
        ("finding_inventory", dict(src.get("finding_inventory") or {})),
        ("semantic_findings", findings),
        ("dashboard_insight_narratives", dict(narratives) if isinstance(narratives, Mapping) else narratives),
        ("executive_summary", dict(src.get("executive_summary") or {})),
        ("finding_evidence_map", dict(evidence_map) if isinstance(evidence_map, Mapping) else evidence_map),
        ("supervisor_interpretation_panel", dict(supervisor) if isinstance(supervisor, Mapping) else supervisor),
        ("certification", dict(cert) if isinstance(cert, Mapping) else cert),
    ])


def _record_id(prefix: str, seed: Any) -> str:
    return f"{prefix}-{_stable_checksum(seed)[:16].upper()}"


def build_o6_finding_export_inventory(o5_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    base = _normalize_payload(o5_payload)
    findings = base["semantic_findings"] if isinstance(base["semantic_findings"], list) else []
    return OrderedDict([
        ("record_groups", [
            "finding_records",
            "narrative_records",
            "evidence_map_records",
            "supervisor_panel_records",
            "export_manifest",
            "governance_export_record",
            "replay_metadata_record",
        ]),
        ("required_o5_payload_fields", [
            "o5_version",
            "semantic_findings",
            "dashboard_insight_narratives",
            "finding_evidence_map",
            "supervisor_interpretation_panel",
            "certification",
        ]),
        ("finding_count", len(findings)),
        ("narrative_count", len(base["dashboard_insight_narratives"]) if isinstance(base["dashboard_insight_narratives"], Mapping) else 0),
        ("evidence_map_count", len(base["finding_evidence_map"]) if isinstance(base["finding_evidence_map"], Mapping) else 0),
    ])


def build_o6_finding_records(o5_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    base = _normalize_payload(o5_payload)
    findings = base["semantic_findings"]
    if not isinstance(findings, list):
        return []
    records: list[OrderedDict[str, Any]] = []
    for finding in findings:
        if not isinstance(finding, Mapping):
            continue
        fid = str(finding.get("finding_id") or "")
        seed = OrderedDict([("record_type", "finding_record"), ("finding_id", fid), ("finding_type", str(finding.get("finding_type") or ""))])
        rec = OrderedDict([
            ("record_id", _record_id("O6FR", seed)),
            ("record_type", "finding_record"),
            ("finding_id", fid),
            ("finding_type", str(finding.get("finding_type") or "")),
            ("finding_title", str(finding.get("finding_title") or "")),
            ("finding_severity", str(finding.get("finding_severity") or "")),
            ("finding_direction", str(finding.get("finding_direction") or "")),
            ("confidence_label", str(finding.get("confidence_label") or "")),
            ("finding_summary", str(finding.get("finding_summary") or "")),
            ("supporting_evidence_refs", _ordered_str_list(finding.get("supporting_evidence_refs"))),
            ("semantic_category_refs", _ordered_str_list(finding.get("semantic_category_refs"))),
            ("kpi_refs", _ordered_str_list(finding.get("kpi_refs"))),
            ("alert_refs", _ordered_str_list(finding.get("alert_refs"))),
            ("lineage_refs", OrderedDict(sorted(dict(finding.get("lineage_refs") or {}).items()))),
            ("source_payload_checksum", str(base["o5_checksum"] or base["certification"].get("checksum") or "")),
        ])
        rec["export_checksum"] = _stable_checksum(rec)
        records.append(rec)
    records.sort(key=lambda r: (r["finding_id"], r["record_id"]))
    return records


def build_o6_narrative_records(o5_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    base = _normalize_payload(o5_payload)
    narratives = base["dashboard_insight_narratives"]
    findings = build_o6_finding_records(base)
    finding_ids = [r["finding_id"] for r in findings]
    if not isinstance(narratives, Mapping):
        return []
    records: list[OrderedDict[str, Any]] = []
    for section in sorted(narratives.keys()):
        seed = OrderedDict([("record_type", "narrative_record"), ("section", section)])
        rec = OrderedDict([
            ("record_id", _record_id("O6NR", seed)),
            ("record_type", "narrative_record"),
            ("narrative_section", str(section)),
            ("narrative_text", str(narratives.get(section) or "")),
            ("related_finding_ids", sorted(finding_ids)),
            ("source_payload_checksum", str(base["o5_checksum"] or base["certification"].get("checksum") or "")),
        ])
        rec["export_checksum"] = _stable_checksum(rec)
        records.append(rec)
    return records


def build_o6_evidence_map_records(o5_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    base = _normalize_payload(o5_payload)
    fmap = base["finding_evidence_map"]
    if not isinstance(fmap, Mapping):
        return []
    records: list[OrderedDict[str, Any]] = []
    for finding_id in sorted(str(k) for k in fmap.keys()):
        seed = OrderedDict([("record_type", "evidence_map_record"), ("finding_id", finding_id)])
        rec = OrderedDict([
            ("record_id", _record_id("O6ER", seed)),
            ("record_type", "evidence_map_record"),
            ("finding_id", finding_id),
            ("supporting_evidence_refs", _ordered_str_list(fmap.get(finding_id))),
            ("source_payload_checksum", str(base["o5_checksum"] or base["certification"].get("checksum") or "")),
        ])
        rec["export_checksum"] = _stable_checksum(rec)
        records.append(rec)
    return records


def build_o6_supervisor_panel_records(o5_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    base = _normalize_payload(o5_payload)
    panel = base["supervisor_interpretation_panel"]
    if not isinstance(panel, Mapping):
        return []
    seed = OrderedDict([("record_type", "supervisor_panel_record"), ("status", str(panel.get("certification_status") or ""))])
    rec = OrderedDict([
        ("record_id", _record_id("O6SR", seed)),
        ("record_type", "supervisor_panel_record"),
        ("certification_status", str(panel.get("certification_status") or "")),
        ("blocking_reasons", _ordered_str_list(panel.get("blocking_reasons"))),
        ("degraded_reasons", _ordered_str_list(panel.get("degraded_reasons"))),
        ("forbidden_capability_inventory", OrderedDict(sorted(dict(panel.get("forbidden_capability_inventory") or {}).items()))),
        ("source_payload_checksum", str(base["o5_checksum"] or base["certification"].get("checksum") or "")),
    ])
    rec["export_checksum"] = _stable_checksum(rec)
    return [rec]


def build_o6_dashboard_export_bundle(o5_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    base = _normalize_payload(o5_payload)
    inventory = build_o6_finding_export_inventory(base)
    finding_records = build_o6_finding_records(base)
    narrative_records = build_o6_narrative_records(base)
    evidence_records = build_o6_evidence_map_records(base)
    supervisor_records = build_o6_supervisor_panel_records(base)

    export_manifest = OrderedDict([
        ("record_group_order", list(inventory["record_groups"])),
        ("finding_records_count", len(finding_records)),
        ("narrative_records_count", len(narrative_records)),
        ("evidence_map_records_count", len(evidence_records)),
        ("supervisor_panel_records_count", len(supervisor_records)),
    ])
    governance_export_record = OrderedDict([
        ("record_id", _record_id("O6GV", FORBIDDEN_CAPABILITIES)),
        ("record_type", "governance_export_record"),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
        ("boundary_mode", "contract_only_no_persistence_execution"),
    ])
    governance_export_record["export_checksum"] = _stable_checksum(governance_export_record)

    replay_metadata_record = OrderedDict([
        ("record_id", _record_id("O6RM", OrderedDict([("o5_version", base["o5_version"]), ("o5_checksum", base["o5_checksum"])]))),
        ("record_type", "replay_metadata_record"),
        ("o5_version", base["o5_version"]),
        ("o5_checksum", base["o5_checksum"]),
        ("source_certification_checksum", str(base["certification"].get("checksum") or "")),
    ])
    replay_metadata_record["export_checksum"] = _stable_checksum(replay_metadata_record)

    bundle = OrderedDict([
        ("o6_version", "o6_finding_persistence_export_contract_v1"),
        ("export_inventory", inventory),
        ("finding_records", finding_records),
        ("narrative_records", narrative_records),
        ("evidence_map_records", evidence_records),
        ("supervisor_panel_records", supervisor_records),
        ("export_manifest", export_manifest),
        ("governance_export_record", governance_export_record),
        ("replay_metadata_record", replay_metadata_record),
    ])
    bundle["o6_checksum"] = _stable_checksum(bundle)
    return bundle


def certify_o6_finding_persistence_export_contract(o5_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    base = _normalize_payload(o5_payload)
    blocking: list[str] = []
    degraded: list[str] = []
    if not isinstance(o5_payload or {}, Mapping):
        blocking.append("o5_payload_not_mapping")
    if not isinstance(base["semantic_findings"], list):
        blocking.append("semantic_findings_not_list")
    if not isinstance(base["dashboard_insight_narratives"], Mapping):
        blocking.append("dashboard_insight_narratives_not_mapping")
    if not isinstance(base["finding_evidence_map"], Mapping):
        blocking.append("finding_evidence_map_not_mapping")
    if not base["o5_version"]:
        degraded.append("missing_o5_version")

    bundle = build_o6_dashboard_export_bundle(base)
    if not bundle["finding_records"]:
        degraded.append("no_finding_records_generated")
    for rec in bundle["finding_records"]:
        if not rec["finding_id"]:
            blocking.append("missing_finding_id_in_record")
        if not rec["export_checksum"]:
            blocking.append("missing_export_checksum")
        if not rec["lineage_refs"]:
            degraded.append("missing_lineage_refs")
    for rec in bundle["evidence_map_records"]:
        if rec["finding_id"] not in {x["finding_id"] for x in bundle["finding_records"]}:
            degraded.append("evidence_map_unmatched_finding_id")
    if not base["o5_checksum"]:
        degraded.append("missing_o5_checksum")
    if set(bundle["export_manifest"]["record_group_order"]) != set(bundle["export_inventory"]["record_groups"]):
        blocking.append("export_manifest_record_group_mismatch")

    status = BLOCKED if blocking else DEGRADED if degraded else CERTIFIED
    cert = OrderedDict([
        ("certification_status", status),
        ("blocking_reasons", sorted(set(blocking))),
        ("degraded_reasons", sorted(set(degraded))),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
        ("governance_boundary_compliance", "contract_only_no_persistence_execution"),
    ])
    cert["checksum"] = _stable_checksum(cert)
    return cert


def build_o6_finding_persistence_export_contract_report(o5_payload: Mapping[str, Any] | None = None) -> str:
    cert = certify_o6_finding_persistence_export_contract(o5_payload)
    return "\n".join([
        "# O6 Finding Persistence Export Contract Report",
        "",
        "## Objective",
        "Define deterministic export/persistence-ready contract records from O5 finding payloads without executing persistence.",
        "",
        "## Certification",
        f"Status: {cert['certification_status']}",
    ])
