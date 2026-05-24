from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Mapping

CERTIFIED_HISTORICAL_FINDINGS_NARRATIVE = "CERTIFIED_HISTORICAL_FINDINGS_NARRATIVE"
DEGRADED_HISTORICAL_FINDINGS_NARRATIVE = "DEGRADED_HISTORICAL_FINDINGS_NARRATIVE"
BLOCKED_HISTORICAL_FINDINGS_NARRATIVE = "BLOCKED_HISTORICAL_FINDINGS_NARRATIVE"


def _text(value: Any, default: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def _contains_forbidden_language(payload: Any) -> bool:
    text = _text(payload).lower()
    forbidden = ("buy", "sell", "trade", "position", "entry", "exit", "predict", "forecast", "autonomous", "execute order")
    return any(re.search(rf"\\b{re.escape(token)}\\b", text) for token in forbidden)


def build_d16_historical_finding_inventory(*, d11_report_payload: Mapping[str, Any] | None, d12_report_payload: Mapping[str, Any] | None, d13_report_payload: Mapping[str, Any] | None, d14_report_payload: Mapping[str, Any] | None, d15_dashboard_enrichment_payload: Mapping[str, Any] | None, d9_report_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    d11, d12, d13, d14, d15, d9 = _dict(d11_report_payload), _dict(d12_report_payload), _dict(d13_report_payload), _dict(d14_report_payload), _dict(d15_dashboard_enrichment_payload), _dict(d9_report_payload)
    recurring = sorted({_text(item.get("pattern_classification") or item.get("event")) for item in _list(d12.get("cross_window_patterns")) if isinstance(item, Mapping) and _text(item.get("pattern_classification") or item.get("event"))})
    constraints = sorted({_text(x) for x in _list(_dict(d12.get("expectation_intelligence_synthesis")).get("unresolved_constraints")) if _text(x)})
    d9_findings = _list(_dict(d9.get("operational_findings")) if isinstance(d9.get("operational_findings"), Mapping) else d9.get("operational_findings"))
    d9_titles = sorted({_text(item.get("finding_title") or item.get("finding_type")) for item in d9_findings if isinstance(item, Mapping) and _text(item.get("finding_title") or item.get("finding_type"))})
    regime = _text(_dict(d13.get("current_snapshot")).get("historical_expectation_regime") or _dict(d12.get("regime_classification")).get("historical_expectation_regime") or d15.get("historical_expectation_regime"), "UNSPECIFIED_REGIME")
    lineage_refs = sorted({
        *[_text(x) for x in _list(_dict(d11.get("historical_replay_windows")).get("lineage_refs")) if _text(x)],
        *[_text(x) for x in _list(_dict(d12.get("historical_expectation_inventory")).get("lineage_refs")) if _text(x)],
        *[_text(x) for x in _list(_dict(d13.get("current_snapshot")).get("lineage_refs")) if _text(x)],
        *[_text(x) for x in _list(_dict(d15.get("governance_debug_details")).get("lineage_refs")) if _text(x)],
    })
    inventory = OrderedDict([
        ("historical_replay_depth", _text(d15.get("historical_replay_depth"), "INSUFFICIENT")),
        ("historical_expectation_regime", regime),
        ("recurring_historical_findings", recurring),
        ("recurring_confidence_constraints", constraints),
        ("d9_operational_findings", d9_titles),
        ("lineage_refs", lineage_refs),
    ])
    inventory["inventory_checksum"] = _checksum([inventory["historical_replay_depth"], regime, ",".join(recurring), ",".join(constraints), ",".join(d9_titles), ",".join(lineage_refs)])
    return inventory


def build_d16_recurring_finding_clusters(*, historical_finding_inventory: Mapping[str, Any], d12_report_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    inv = _dict(historical_finding_inventory)
    patterns = _list(_dict(_dict(d12_report_payload).get("expectation_intelligence_synthesis")).get("cross_window_pattern_summary"))
    clusters: list[OrderedDict[str, Any]] = []
    seen = sorted({_text(x) for x in _list(inv.get("recurring_historical_findings")) + patterns if _text(x)})
    for idx, finding in enumerate(seen):
        clusters.append(OrderedDict([
            ("cluster_id", f"D16_CLUSTER_{idx:03d}"),
            ("finding", finding),
            ("recurrence_class", "RECURRING"),
            ("evidence_basis", "historical_replay_pattern"),
        ]))
    return clusters


def build_d16_regime_linked_finding_narratives(*, recurring_finding_clusters: list[Mapping[str, Any]], d13_report_payload: Mapping[str, Any] | None, d14_report_payload: Mapping[str, Any] | None) -> list[OrderedDict[str, Any]]:
    d13, d14 = _dict(d13_report_payload), _dict(d14_report_payload)
    regime = _text(_dict(d13.get("current_snapshot")).get("historical_expectation_regime"), "UNSPECIFIED_REGIME")
    evolution = _text(_dict(d13.get("delta_comparison")).get("evolution_signal") or _dict(d14.get("orchestration_inventory")).get("regime_evolution_class"), "REGIME_INSUFFICIENT_HISTORY")
    narratives: list[OrderedDict[str, Any]] = []
    for cluster in sorted([_dict(x) for x in recurring_finding_clusters], key=lambda x: _text(x.get("cluster_id"))):
        narratives.append(OrderedDict([
            ("cluster_id", _text(cluster.get("cluster_id"))),
            ("historical_expectation_regime", regime),
            ("regime_evolution_signal", evolution),
            ("narrative", f"{_text(cluster.get('finding'), 'finding')} recurred under {regime} with evolution context {evolution}."),
        ]))
    return narratives


def build_d16_operator_narrative_summary(*, historical_finding_inventory: Mapping[str, Any], recurring_finding_clusters: list[Mapping[str, Any]], regime_linked_finding_narratives: list[Mapping[str, Any]], d15_dashboard_enrichment_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    inv = _dict(historical_finding_inventory)
    d15 = _dict(d15_dashboard_enrichment_payload)
    cluster_findings = [_text(_dict(x).get("finding")) for x in recurring_finding_clusters if _text(_dict(x).get("finding"))]
    changed = sorted({_text(_dict(x).get("regime_evolution_signal")) for x in regime_linked_finding_narratives if _text(_dict(x).get("regime_evolution_signal")) and "INSUFFICIENT" not in _text(_dict(x).get("regime_evolution_signal"))})
    persisted = sorted(set(cluster_findings[:5]))
    degraded = sorted({_text(x) for x in _list(inv.get("recurring_confidence_constraints")) if _text(x)})
    improved = sorted({_text(x) for x in _list(d15.get("strongest_historical_patterns")) if _text(x) and x not in degraded})[:5]
    attention = sorted({*degraded[:3], *persisted[:3], *_list(inv.get("d9_operational_findings"))[:2]})
    return OrderedDict([
        ("what_changed", changed or ["No high-confidence regime-linked change signal available."]),
        ("what_persisted", persisted or ["No recurring findings available."]),
        ("what_degraded", degraded or ["No recurring degradation constraints identified."]),
        ("what_improved", improved or ["No explicit historical improvement signal available."]),
        ("recurrent_confidence_constraints", degraded),
        ("operator_attention_next", attention or ["Preserve lineage continuity and monitor recurring constraints."]),
        ("summary_narrative", "Historical findings were replayed deterministically; operator focus remains on repeated constraints and regime-linked continuity without predictive actioning."),
    ])


def build_d16_dashboard_payload(*, historical_finding_inventory: Mapping[str, Any], recurring_finding_clusters: list[Mapping[str, Any]], regime_linked_finding_narratives: list[Mapping[str, Any]], operator_narrative_summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv, summary = _dict(historical_finding_inventory), _dict(operator_narrative_summary)
    lineage_refs = _list(inv.get("lineage_refs"))
    payload = OrderedDict([
        ("recurring_historical_findings", [OrderedDict(_dict(x)) for x in recurring_finding_clusters]),
        ("regime_linked_findings", [OrderedDict(_dict(x)) for x in regime_linked_finding_narratives]),
        ("what_changed", _list(summary.get("what_changed"))),
        ("what_persisted", _list(summary.get("what_persisted"))),
        ("what_degraded", _list(summary.get("what_degraded"))),
        ("what_improved", _list(summary.get("what_improved"))),
        ("recurrent_confidence_constraints", _list(summary.get("recurrent_confidence_constraints"))),
        ("operator_narrative_summary", _text(summary.get("summary_narrative"), "Unavailable")),
        ("operator_attention_next", _list(summary.get("operator_attention_next"))),
        ("governance_lineage_details", OrderedDict([("lineage_refs", lineage_refs), ("read_only", True), ("append_only_semantics_preserved", True), ("deterministic_replay_lineage_preserved", True)])),
    ])
    payload["payload_checksum"] = _checksum([",".join(lineage_refs), str(len(_list(payload.get("recurring_historical_findings")))), str(len(_list(payload.get("regime_linked_findings")))), ",".join(_list(payload.get("what_changed"))), ",".join(_list(payload.get("recurrent_confidence_constraints")))])
    return payload


def certify_d16_historical_findings_narrative(*, historical_finding_inventory: Mapping[str, Any], recurring_finding_clusters: list[Mapping[str, Any]], regime_linked_finding_narratives: list[Mapping[str, Any]], operator_narrative_summary: Mapping[str, Any], dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv, summary, payload = _dict(historical_finding_inventory), _dict(operator_narrative_summary), _dict(dashboard_payload)
    blocking: list[str] = []
    degraded: list[str] = []
    if not _list(inv.get("lineage_refs")):
        blocking.append("MISSING_LINEAGE_REFERENCES")
    if not _list(inv.get("recurring_historical_findings")):
        blocking.append("MISSING_HISTORICAL_FINDINGS_INVENTORY")
    if not recurring_finding_clusters:
        degraded.append("RECURRING_CLUSTERS_EMPTY")
    if not regime_linked_finding_narratives:
        degraded.append("REGIME_LINKED_NARRATIVES_EMPTY")
    if not _text(summary.get("summary_narrative")):
        degraded.append("OPERATOR_SUMMARY_INCOMPLETE")
    if _contains_forbidden_language(payload):
        blocking.append("FORBIDDEN_PREDICTIVE_TRADING_OR_AUTONOMOUS_LANGUAGE")
    status = BLOCKED_HISTORICAL_FINDINGS_NARRATIVE if blocking else (DEGRADED_HISTORICAL_FINDINGS_NARRATIVE if degraded else CERTIFIED_HISTORICAL_FINDINGS_NARRATIVE)
    return OrderedDict([("certification_status", status), ("blocking_reasons", sorted(blocking)), ("degraded_reasons", sorted(degraded)), ("lineage_intact", bool(_list(inv.get("lineage_refs"))))])


def build_d16_report_payload(*, historical_finding_inventory: Mapping[str, Any], recurring_finding_clusters: list[Mapping[str, Any]], regime_linked_finding_narratives: list[Mapping[str, Any]], operator_narrative_summary: Mapping[str, Any], dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any], objective: str = "D16 Historical Findings Replay & Operator Narrative Generation") -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", objective),
        ("historical_finding_inventory", OrderedDict(deepcopy(dict(historical_finding_inventory)))),
        ("recurring_finding_clusters", [OrderedDict(deepcopy(dict(x))) for x in recurring_finding_clusters if isinstance(x, Mapping)]),
        ("regime_linked_finding_narratives", [OrderedDict(deepcopy(dict(x))) for x in regime_linked_finding_narratives if isinstance(x, Mapping)]),
        ("operator_narrative_summary", OrderedDict(deepcopy(dict(operator_narrative_summary)))),
        ("dashboard_payload", OrderedDict(deepcopy(dict(dashboard_payload)))),
        ("certification", OrderedDict(deepcopy(dict(certification)))),
        ("no_direct_sql_bypass_used", True),
        ("no_writes_performed", True),
        ("no_predictive_behavior", True),
        ("no_trading_advice", True),
        ("no_autonomous_actions", True),
    ])


def build_d16_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    report = _dict(report_payload)
    return "\n".join([
        "# D16 Historical Findings Replay & Operator Narrative Generation",
        "",
        f"## Objective\n- {_text(report.get('objective'))}",
        "## Governance",
        "- Read-only additive intelligence layer only.",
        "- Append-only semantics preserved.",
        "- Deterministic replay lineage preserved.",
        "- No direct SQL bypass, writes, predictive, trading, or autonomous behavior.",
        f"## Certification\n- {_text(_dict(report.get('certification')).get('certification_status'), 'UNKNOWN')}",
        f"## Historical Finding Inventory\n- {_dict(report.get('historical_finding_inventory'))}",
        f"## Operator Narrative Summary\n- {_dict(report.get('operator_narrative_summary'))}",
    ])
