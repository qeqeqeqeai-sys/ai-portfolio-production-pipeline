"""Deterministic O5 semantic finding generation and narrative layer."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

CERTIFIED = "CERTIFIED_FINDINGS_READY"
DEGRADED = "DEGRADED_FINDINGS_READY"
BLOCKED = "BLOCKED_FINDINGS_INVALID"

SEVERITY_ORDER = ("SEVERE", "HIGH", "ELEVATED", "MODERATE", "LOW")
ALLOWED_DIRECTIONS = ("ELEVATING", "CONTAINED", "SUPPORTIVE", "CONFLICTED", "LIMITED", "NEUTRAL")
ALLOWED_CONFIDENCE = ("HIGH", "MEDIUM", "LOW")
FORBIDDEN_TERMS = ("buy", "sell", "short", "long", "outperform", "underperform", "target price")
FORBIDDEN_CAPABILITIES = (
    "live_market_fetching",
    "database_writes",
    "trading_instructions",
    "portfolio_optimization",
    "predictive_return_forecasts",
    "llm_calls",
    "network_calls",
    "hidden_non_determinism",
)

FINDING_TYPE_PRIORITY = OrderedDict([
    ("GOVERNANCE_BLOCKED_OR_LIMITED", 0),
    ("EVIDENCE_QUALITY_DEGRADED", 1),
    ("EXPECTATION_FRAGILITY_ELEVATED", 2),
    ("SEMANTIC_PRESSURE_CONCENTRATED", 3),
    ("MARKET_CONTEXT_CONFLICTED", 4),
    ("MARKET_CONTEXT_SUPPORTIVE", 5),
])


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _severity_rank(label: Any) -> int:
    try:
        return SEVERITY_ORDER.index(str(label))
    except ValueError:
        return len(SEVERITY_ORDER)


def _normalize_o4_payload(o4_payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = deepcopy(dict(o4_payload or {}))
    return OrderedDict([
        ("integration_version", str(src.get("integration_version") or "")),
        ("expectation_fragility_kpis", src.get("expectation_fragility_kpis") if isinstance(src.get("expectation_fragility_kpis"), list) else src.get("expectation_fragility_kpis", [])),
        ("semantic_alerts", src.get("semantic_alerts") if isinstance(src.get("semantic_alerts"), list) else src.get("semantic_alerts", [])),
        ("evidence_cards", dict(src.get("evidence_cards") or {})),
        ("category_summary_panels", dict(src.get("category_summary_panels") or {})),
        ("market_context_panels", dict(src.get("market_context_panels") or {})),
        ("governance_status_panel", dict(src.get("governance_status_panel") or {})),
        ("replay_metadata_panel", dict(src.get("replay_metadata_panel") or {})),
        ("semantic_dashboard_inventory", dict(src.get("semantic_dashboard_inventory") or {})),
        ("certification", dict(src.get("certification") or {})),
    ])


def build_o5_finding_inventory(o4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    base = _normalize_o4_payload(o4_dashboard_payload)
    return OrderedDict([
        ("finding_types_supported", list(FINDING_TYPE_PRIORITY.keys())),
        ("required_finding_fields", [
            "finding_id", "finding_type", "finding_title", "finding_severity", "finding_direction", "finding_summary",
            "supporting_evidence_refs", "semantic_category_refs", "kpi_refs", "alert_refs", "confidence_label",
            "governance_notes", "lineage_refs", "replay_metadata",
        ]),
        ("severity_labels", list(SEVERITY_ORDER)),
        ("direction_labels", list(ALLOWED_DIRECTIONS)),
        ("confidence_labels", list(ALLOWED_CONFIDENCE)),
        ("o4_input_presence", OrderedDict([
            ("has_kpis", bool(base["expectation_fragility_kpis"])),
            ("has_alerts", bool(base["semantic_alerts"])),
            ("has_governance", bool(base["governance_status_panel"])),
            ("has_replay", bool(base["replay_metadata_panel"])),
        ])),
    ])


def _build_finding(ftype: str, severity: str, direction: str, summary: str, evidence: list[str], cats: list[str], kpis: list[str], alerts: list[str], confidence: str, governance_notes: list[str], lineage: dict[str, Any], replay: dict[str, Any]) -> OrderedDict[str, Any]:
    seed = OrderedDict([("type", ftype), ("severity", severity), ("direction", direction), ("evidence", sorted(evidence)), ("kpis", sorted(kpis)), ("alerts", sorted(alerts))])
    fid = f"O5F-{_stable_checksum(seed)[:12].upper()}"
    return OrderedDict([
        ("finding_id", fid),
        ("finding_type", ftype),
        ("finding_title", ftype.replace("_", " ").title()),
        ("finding_severity", severity),
        ("finding_direction", direction),
        ("finding_summary", summary),
        ("supporting_evidence_refs", sorted(evidence)),
        ("semantic_category_refs", sorted(cats)),
        ("kpi_refs", sorted(kpis)),
        ("alert_refs", sorted(alerts)),
        ("confidence_label", confidence),
        ("governance_notes", sorted(governance_notes)),
        ("lineage_refs", OrderedDict(sorted(lineage.items()))),
        ("replay_metadata", OrderedDict(sorted(replay.items()))),
    ])


def build_o5_semantic_findings(o4_dashboard_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    base = _normalize_o4_payload(o4_dashboard_payload)
    kpis = base["expectation_fragility_kpis"] if isinstance(base["expectation_fragility_kpis"], list) else []
    alerts = base["semantic_alerts"] if isinstance(base["semantic_alerts"], list) else []
    replay = base["replay_metadata_panel"]
    gov = base["governance_status_panel"]
    line = OrderedDict([
        ("o3_lineage_checksum", str(replay.get("o3_lineage_checksum") or "")),
        ("o4_checksum", str(replay.get("o4_checksum") or base["certification"].get("checksum") or "")),
    ])
    findings: list[OrderedDict[str, Any]] = []
    top_pressure = 50.0
    for k in kpis:
        if k.get("kpi_id") == "top_entity_composite_pressure":
            try:
                top_pressure = float(k.get("value", 50.0))
            except (TypeError, ValueError):
                top_pressure = 50.0
    severe_alerts = [a for a in alerts if str(a.get("severity") or "") in ("SEVERE", "HIGH")]
    categories = sorted({str(a.get("semantic_category") or "UNCLASSIFIED") for a in alerts})
    evidence_refs = sorted({f"alert:{a.get('symbol','UNKNOWN')}:{a.get('metric_name','UNKNOWN')}" for a in alerts})
    if severe_alerts or top_pressure >= 70.0:
        findings.append(_build_finding("EXPECTATION_FRAGILITY_ELEVATED", "HIGH" if top_pressure >= 70 else "ELEVATED", "ELEVATING", "Structural expectation fragility is elevated based on deterministic pressure and alert concentration signals.", evidence_refs[:12], categories, ["top_entity_composite_pressure"], [f"{i}" for i, _ in enumerate(alerts[:10])], "MEDIUM", ["Interpretation is structural and non-predictive."], line, replay))
    if len(categories) >= 2:
        findings.append(_build_finding("SEMANTIC_PRESSURE_CONCENTRATED", "ELEVATED", "CONFLICTED" if severe_alerts else "ELEVATING", "Semantic pressure is concentrated across a bounded category subset, indicating concentrated structural stress.", evidence_refs[:12], categories[:5], ["top_entity_evidence_count"], [f"{i}" for i, _ in enumerate(alerts[:10])], "MEDIUM", ["Category concentration is descriptive only."], line, replay))
    context_type = "MARKET_CONTEXT_SUPPORTIVE" if not severe_alerts and top_pressure < 60 else "MARKET_CONTEXT_CONFLICTED"
    findings.append(_build_finding(context_type, "MODERATE", "SUPPORTIVE" if context_type.endswith("SUPPORTIVE") else "CONFLICTED", "Market context is summarized from O4 panels and may contain mixed structural evidence without directional prediction.", evidence_refs[:8], categories[:5], ["top_entity_composite_pressure"], [f"{i}" for i, _ in enumerate(alerts[:6])], "LOW" if not alerts else "MEDIUM", ["Context interpretation avoids forecast language."], line, replay))
    degraded_evidence = any(str(a.get("evidence_quality") or "").startswith("DEGRADED") for a in alerts)
    if degraded_evidence or not alerts:
        findings.append(_build_finding("EVIDENCE_QUALITY_DEGRADED", "MODERATE", "LIMITED", "Evidence quality is degraded or sparse, so findings remain bounded and uncertainty is explicitly preserved.", evidence_refs[:8], categories[:5], ["top_entity_degraded_evidence_count"], [f"{i}" for i, _ in enumerate(alerts[:6])], "LOW", ["Degraded-state language is required for supervisor safety."], line, replay))
    capability_inventory = dict(gov.get("forbidden_capability_inventory") or {})
    if not capability_inventory or any(not bool(v) for v in capability_inventory.values()):
        findings.append(_build_finding("GOVERNANCE_BLOCKED_OR_LIMITED", "SEVERE", "LIMITED", "Governance inventory is missing or indicates limited boundary assurance; operational use should remain constrained.", [], [], [], [], "LOW", ["Governance limits prevent certification upgrades."], line, replay))

    findings.sort(key=lambda f: (_severity_rank(f["finding_severity"]), FINDING_TYPE_PRIORITY.get(f["finding_type"], 99), f["finding_id"]))
    return findings


def build_o5_dashboard_insight_narratives(o4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, str]:
    findings = build_o5_semantic_findings(o4_dashboard_payload)
    summary = build_o5_executive_finding_summary(o4_dashboard_payload)
    has_degraded = any(f["finding_type"] == "EVIDENCE_QUALITY_DEGRADED" for f in findings)
    return OrderedDict([
        ("executive_findings", f"Deterministic O5 generated {summary['finding_count']} findings with status {summary['status']} and fixed governance-safe templates."),
        ("expectation_fragility_interpretation", "Expectation fragility interpretation is structural, bounded, and non-predictive; it reflects observed semantic pressure only."),
        ("semantic_pressure_interpretation", "Semantic pressure interpretation summarizes concentration and breadth without prescribing trading actions."),
        ("market_context_interpretation", "Market context interpretation identifies supportive or conflicted structural context without return forecasts."),
        ("evidence_quality_interpretation", "Evidence quality interpretation explicitly preserves uncertainty due to degraded or partial evidence." if has_degraded else "Evidence quality interpretation indicates no explicit degradation flags in the processed O4 payload."),
        ("governance_interpretation", "Governance interpretation confirms forbidden capability boundaries and read-only deterministic operationalization."),
        ("supervisor_notes", "Supervisor note: findings are dashboard-readable semantic interpretations and are not investment advice."),
    ])


def build_o5_executive_finding_summary(o4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    findings = build_o5_semantic_findings(o4_dashboard_payload)
    status = certify_o5_semantic_finding_generation(o4_dashboard_payload)["certification_status"]
    return OrderedDict([("status", status), ("finding_count", len(findings)), ("top_finding_id", findings[0]["finding_id"] if findings else "NONE")])


def build_o5_finding_evidence_map(o4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, list[str]]:
    findings = build_o5_semantic_findings(o4_dashboard_payload)
    return OrderedDict((f["finding_id"], list(f["supporting_evidence_refs"])) for f in findings)


def build_o5_supervisor_interpretation_panel(o4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    cert = certify_o5_semantic_finding_generation(o4_dashboard_payload)
    return OrderedDict([
        ("certification_status", cert["certification_status"]),
        ("blocking_reasons", list(cert["blocking_reasons"])),
        ("degraded_reasons", list(cert["degraded_reasons"])),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
    ])


def build_o5_finding_generation_payload(o4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    findings = build_o5_semantic_findings(o4_dashboard_payload)
    narratives = build_o5_dashboard_insight_narratives(o4_dashboard_payload)
    cert = certify_o5_semantic_finding_generation(o4_dashboard_payload)
    payload = OrderedDict([
        ("o5_version", "o5_semantic_finding_generation_v1"),
        ("finding_inventory", build_o5_finding_inventory(o4_dashboard_payload)),
        ("semantic_findings", findings),
        ("dashboard_insight_narratives", narratives),
        ("executive_summary", build_o5_executive_finding_summary(o4_dashboard_payload)),
        ("finding_evidence_map", build_o5_finding_evidence_map(o4_dashboard_payload)),
        ("supervisor_interpretation_panel", build_o5_supervisor_interpretation_panel(o4_dashboard_payload)),
        ("certification", cert),
    ])
    payload["o5_checksum"] = _stable_checksum(payload)
    return payload


def certify_o5_semantic_finding_generation(o4_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    base = _normalize_o4_payload(o4_dashboard_payload)
    blocking: list[str] = []
    degraded: list[str] = []
    if not isinstance(o4_dashboard_payload or {}, Mapping):
        blocking.append("o4_payload_not_mapping")
    if not isinstance(base["expectation_fragility_kpis"], list):
        blocking.append("expectation_fragility_kpis_not_list")
    if not isinstance(base["semantic_alerts"], list):
        blocking.append("semantic_alerts_not_list")
    if not base["integration_version"]:
        degraded.append("missing_o4_integration_version")
    if not base["replay_metadata_panel"]:
        degraded.append("missing_replay_metadata_panel")
    findings = build_o5_semantic_findings(base)
    if not findings:
        degraded.append("empty_finding_set")
    for f in findings:
        if f["finding_severity"] not in SEVERITY_ORDER:
            blocking.append("finding_severity_out_of_bounds")
        if f["finding_direction"] not in ALLOWED_DIRECTIONS:
            blocking.append("finding_direction_out_of_bounds")
        if f["confidence_label"] not in ALLOWED_CONFIDENCE:
            blocking.append("confidence_label_out_of_bounds")
        text = json.dumps(f, ensure_ascii=True).lower()
        if any(term in text for term in FORBIDDEN_TERMS):
            blocking.append("forbidden_language_detected")
    if any(not f.get("lineage_refs", {}).get("o4_checksum") for f in findings):
        degraded.append("missing_o4_lineage_checksum")
    status = BLOCKED if blocking else DEGRADED if degraded else CERTIFIED
    cert_core = OrderedDict([
        ("certification_status", status),
        ("blocking_reasons", sorted(set(blocking))),
        ("degraded_reasons", sorted(set(degraded))),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
    ])
    cert_core["checksum"] = _stable_checksum(cert_core)
    return cert_core


def build_o5_semantic_finding_generation_report(o4_dashboard_payload: Mapping[str, Any] | None = None) -> str:
    cert = certify_o5_semantic_finding_generation(o4_dashboard_payload)
    return "\n".join([
        "# O5 Semantic Finding Generation Report",
        "",
        "## Objective",
        "Convert O4 dashboard payloads into deterministic semantic findings and fixed dashboard insight narratives.",
        "",
        "## Certification",
        f"Status: {cert['certification_status']}",
    ])
