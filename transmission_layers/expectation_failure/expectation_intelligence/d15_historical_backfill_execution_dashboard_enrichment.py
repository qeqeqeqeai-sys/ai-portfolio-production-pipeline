from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping


CERTIFIED_DASHBOARD_ENRICHMENT = "CERTIFIED_DASHBOARD_ENRICHMENT"
DEGRADED_DASHBOARD_ENRICHMENT = "DEGRADED_DASHBOARD_ENRICHMENT"
BLOCKED_DASHBOARD_ENRICHMENT = "BLOCKED_DASHBOARD_ENRICHMENT"


def _text(value: Any, default: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def build_d15_backfill_execution_inventory(*, d11_report_payload: Mapping[str, Any] | None, d12_report_payload: Mapping[str, Any] | None, d13_report_payload: Mapping[str, Any] | None, d14_report_payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    d11, d12, d13, d14 = _dict(d11_report_payload), _dict(d12_report_payload), _dict(d13_report_payload), _dict(d14_report_payload)
    d11_cert = _text(_dict(d11.get("certification")).get("certification_status"), "UNKNOWN")
    d12_cert = _text(_dict(d12.get("certification")).get("certification_status"), "UNKNOWN")
    d13_cert = _text(_dict(d13.get("certification")).get("certification_status"), "UNKNOWN")
    d14_cert = _text(_dict(d14.get("certification")).get("certification_status"), "UNKNOWN")
    regime = _text(_dict(d13.get("current_snapshot")).get("historical_expectation_regime") or _dict(d12.get("regime_classification")).get("historical_expectation_regime"), "UNSPECIFIED_REGIME")
    replay_depth = _text(_dict(d13.get("current_snapshot")).get("replay_depth_interpretation") or _dict(d12.get("expectation_intelligence_synthesis")).get("replay_depth_interpretation"), "INSUFFICIENT")
    unresolved = sorted({_text(x) for x in _list(_dict(d12.get("expectation_intelligence_synthesis")).get("unresolved_constraints")) if _text(x)})
    lineage_refs = sorted({
        *[_text(x) for x in _list(_dict(d11.get("historical_replay_windows")).get("lineage_refs")) if _text(x)],
        *[_text(x) for x in _list(_dict(d12.get("historical_expectation_inventory")).get("lineage_refs")) if _text(x)],
        *[_text(x) for x in _list(_dict(d13.get("current_snapshot")).get("lineage_refs")) if _text(x)],
    })
    blocked = not (d11 and d12 and d13 and d14) or not lineage_refs or d14_cert.startswith("BLOCKED") or "insufficient" in replay_depth.lower()
    degraded = d11_cert.startswith("DEGRADED") or d12_cert.startswith("DEGRADED") or d13_cert.startswith("DEGRADED") or d14_cert.startswith("DEGRADED") or bool(unresolved)
    status = "BACKFILL_EXECUTION_BLOCKED" if blocked else ("BACKFILL_EXECUTION_DEGRADED" if degraded else "BACKFILL_EXECUTION_READY")
    checksum = _checksum([d11_cert, d12_cert, d13_cert, d14_cert, regime, replay_depth, ",".join(unresolved), ",".join(lineage_refs), status])
    return OrderedDict([
        ("d11_certification_status", d11_cert),
        ("d12_certification_status", d12_cert),
        ("d13_certification_status", d13_cert),
        ("d14_certification_status", d14_cert),
        ("historical_replay_depth", replay_depth),
        ("historical_expectation_regime", regime),
        ("lineage_refs", lineage_refs),
        ("strongest_recurring_constraints", unresolved[:5]),
        ("inventory_status", status),
        ("inventory_checksum", checksum),
    ])


def build_d15_historical_execution_timeline(*, d11_report_payload: Mapping[str, Any] | None, d12_report_payload: Mapping[str, Any] | None, d13_report_payload: Mapping[str, Any] | None) -> list[OrderedDict[str, Any]]:
    d11, d12, d13 = _dict(d11_report_payload), _dict(d12_report_payload), _dict(d13_report_payload)
    windows = _list(_dict(d11.get("historical_replay_windows")).get("replay_windows"))
    patterns = _list(d12.get("cross_window_patterns"))
    deltas = _dict(d13.get("delta_comparison"))
    timeline: list[OrderedDict[str, Any]] = []
    for idx, item in enumerate(windows):
        entry = _dict(item)
        timeline.append(OrderedDict([
            ("sequence", idx),
            ("phase", "D11_REPLAY_WINDOW"),
            ("window_label", _text(entry.get("window_label") or entry.get("window_id"), f"window_{idx:03d}")),
            ("event", _text(entry.get("replay_window_status"), "REPLAY_WINDOW_OBSERVED")),
            ("lineage_ref", _text(entry.get("lineage_ref") or entry.get("source_lineage_ref"))),
        ]))
    for idx, item in enumerate(patterns):
        entry = _dict(item)
        timeline.append(OrderedDict([
            ("sequence", len(timeline) + idx),
            ("phase", "D12_PATTERN"),
            ("window_label", _text(entry.get("window_label"), f"pattern_{idx:03d}")),
            ("event", _text(entry.get("pattern_classification"), "PATTERN_OBSERVED")),
            ("lineage_ref", _text(entry.get("lineage_ref"))),
        ]))
    if deltas:
        timeline.append(OrderedDict([
            ("sequence", len(timeline)),
            ("phase", "D13_DELTA"),
            ("window_label", "regime_evolution"),
            ("event", _text(deltas.get("evolution_signal") or d13.get("regime_evolution_classification", {}).get("regime_evolution_class"), "EVOLUTION_OBSERVED")),
            ("lineage_ref", _text(deltas.get("lineage_ref"))),
        ]))
    timeline.sort(key=lambda r: (_text(r.get("phase")), _text(r.get("window_label")), _text(r.get("event")), _text(r.get("lineage_ref")), int(r.get("sequence") or 0)))
    return timeline


def build_d15_dashboard_enrichment_payload(*, backfill_inventory: Mapping[str, Any], historical_execution_timeline: list[Mapping[str, Any]], d14_report_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    inv = _dict(backfill_inventory)
    d14 = _dict(d14_report_payload)
    timeline = [OrderedDict(_dict(x)) for x in historical_execution_timeline if isinstance(x, Mapping)]
    regime_evolution = _dict(d14.get("orchestration_inventory")).get("regime_evolution_class") or "REGIME_INSUFFICIENT_HISTORY"
    supervisory_rollup = _dict(d14.get("supervisory_rollup"))
    summary = OrderedDict([
        ("historical_replay_depth", inv.get("historical_replay_depth", "INSUFFICIENT")),
        ("historical_expectation_regime", inv.get("historical_expectation_regime", "UNSPECIFIED_REGIME")),
        ("regime_evolution_timeline_cards", timeline[:12]),
        ("strongest_recurring_constraints", _list(inv.get("strongest_recurring_constraints"))),
        ("strongest_historical_patterns", sorted({_text(x.get("event")) for x in timeline if _text(x.get("phase")) == "D12_PATTERN"})[:5]),
        ("supervisory_operational_summary", OrderedDict([
            ("supervisory_state", supervisory_rollup.get("supervisory_operational_state", "UNKNOWN")),
            ("risk_band", supervisory_rollup.get("supervisory_risk_band", "UNKNOWN")),
            ("regime_evolution", regime_evolution),
        ])),
        ("operational_recommendation", "Proceed with governed replay persistence orchestration." if _text(inv.get("inventory_status")).endswith("READY") else "Address historical lineage continuity and unresolved constraints prior to further operationalization."),
        ("governance_debug_details", OrderedDict([
            ("inventory_checksum", inv.get("inventory_checksum")),
            ("lineage_refs", _list(inv.get("lineage_refs"))),
            ("d14_certification_status", _dict(d14.get("certification")).get("certification_status")),
            ("read_only", True),
            ("append_only_semantics_preserved", True),
            ("deterministic_replay_lineage_preserved", True),
        ])),
    ])
    summary["payload_checksum"] = _checksum([_text(summary.get("historical_replay_depth")), _text(summary.get("historical_expectation_regime")), _text(regime_evolution), ",".join(_list(summary.get("strongest_recurring_constraints"))), ",".join(_list(inv.get("lineage_refs"))), str(len(timeline))])
    return summary


def certify_d15_dashboard_enrichment(*, backfill_inventory: Mapping[str, Any], dashboard_enrichment_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = _dict(backfill_inventory)
    payload = _dict(dashboard_enrichment_payload)
    blocking: list[str] = []
    degraded: list[str] = []
    if not _list(inv.get("lineage_refs")):
        blocking.append("MISSING_LINEAGE_REFS")
    if _text(inv.get("inventory_status")).endswith("BLOCKED"):
        blocking.append("INVENTORY_BLOCKED")
    if not _list(payload.get("regime_evolution_timeline_cards")):
        degraded.append("TIMELINE_EMPTY")
    if not _text(payload.get("historical_replay_depth")) or "insufficient" in _text(payload.get("historical_replay_depth")).lower():
        degraded.append("REPLAY_DEPTH_INSUFFICIENT")
    if not _list(payload.get("strongest_historical_patterns")):
        degraded.append("PATTERN_SIGNAL_SPARSE")
    if blocking:
        status = BLOCKED_DASHBOARD_ENRICHMENT
    elif degraded:
        status = DEGRADED_DASHBOARD_ENRICHMENT
    else:
        status = CERTIFIED_DASHBOARD_ENRICHMENT
    return OrderedDict([("certification_status", status), ("blocking_reasons", sorted(blocking)), ("degraded_reasons", sorted(degraded)), ("lineage_intact", bool(_list(inv.get("lineage_refs"))))])


def build_d15_report_payload(*, backfill_inventory: Mapping[str, Any], historical_execution_timeline: list[Mapping[str, Any]], dashboard_enrichment_payload: Mapping[str, Any], certification: Mapping[str, Any], objective: str = "D15 Historical Backfill Execution & D7 Dashboard Enrichment") -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", objective),
        ("backfill_execution_inventory", OrderedDict(deepcopy(dict(backfill_inventory)))),
        ("historical_execution_timeline", [OrderedDict(deepcopy(dict(x))) for x in historical_execution_timeline if isinstance(x, Mapping)]),
        ("dashboard_enrichment_payload", OrderedDict(deepcopy(dict(dashboard_enrichment_payload)))),
        ("certification", OrderedDict(deepcopy(dict(certification)))),
        ("no_direct_sql_bypass_used", True),
        ("no_writes_performed", True),
        ("no_live_fetches_performed", True),
        ("no_predictive_behavior", True),
        ("recommendation", _text(_dict(dashboard_enrichment_payload).get("operational_recommendation"), _text(_dict(certification).get("certification_status")))),
    ])


def build_d15_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    report = _dict(report_payload)
    return "\n".join([
        "# D15 Historical Backfill Execution & D7 Dashboard Enrichment",
        "",
        f"## Objective\n- {_text(report.get('objective'))}",
        "## Governance",
        "- Append-only semantics preserved.",
        "- Deterministic replay lineage preserved.",
        "- No direct SQL bypass.",
        "- No writes performed.",
        "- No predictive/trading/autonomous behavior.",
        f"## Certification\n- {_text(_dict(report.get('certification')).get('certification_status'), 'UNKNOWN')}",
        f"## Inventory\n- {_dict(report.get('backfill_execution_inventory'))}",
        f"## Dashboard Enrichment\n- {_dict(report.get('dashboard_enrichment_payload'))}",
    ])
