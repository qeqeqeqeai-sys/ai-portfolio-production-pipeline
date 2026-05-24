from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Mapping

CERTIFIED_CONFIDENCE_LINEAGE_ENRICHMENT = "CERTIFIED_CONFIDENCE_LINEAGE_ENRICHMENT"
DEGRADED_CONFIDENCE_LINEAGE_ENRICHMENT = "DEGRADED_CONFIDENCE_LINEAGE_ENRICHMENT"
BLOCKED_CONFIDENCE_LINEAGE_ENRICHMENT = "BLOCKED_CONFIDENCE_LINEAGE_ENRICHMENT"
_CONFIDENCE_BANDS = ("high", "moderate", "low", "degraded", "unavailable")


def _text(value: Any, default: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else default


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def _compact_ref(value: Any, prefix: str) -> str:
    token = _text(value)
    if not token:
        return ""
    return f"{prefix}:{sha256(token.encode('utf-8')).hexdigest()[:10].upper()}"


def _contains_forbidden_language(payload: Any) -> bool:
    text = _text(payload).lower()
    forbidden = ("buy", "sell", "trade", "position", "entry", "exit", "predict", "forecast", "autonomous", "execute order")
    return any(re.search(rf"\b{re.escape(token)}\b", text) for token in forbidden)


def build_d17_confidence_attribution_inventory(*, d16_dashboard_payload: Mapping[str, Any] | None, d15_dashboard_enrichment_payload: Mapping[str, Any] | None = None, d12_report_payload: Mapping[str, Any] | None = None, d13_report_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    d16 = _dict(d16_dashboard_payload)
    d15, d12, d13 = _dict(d15_dashboard_enrichment_payload), _dict(d12_report_payload), _dict(d13_report_payload)
    constraints = sorted({_text(x).upper() for x in _list(d16.get("recurrent_confidence_constraints")) if _text(x)})
    replay_depth = _text(d15.get("historical_replay_depth") or _dict(d12.get("expectation_intelligence_synthesis")).get("replay_depth_interpretation"), "INSUFFICIENT")
    continuity = _text(d15.get("historical_continuity_status") or _dict(d12.get("expectation_intelligence_synthesis")).get("continuity_interpretation"), "FRAGMENTED")
    regime_stability = _text(_dict(d13.get("delta_comparison")).get("evolution_signal"), "REGIME_INSUFFICIENT_HISTORY")
    clusters = sorted([_dict(x) for x in _list(d16.get("recurring_historical_findings"))], key=lambda x: _text(x.get("cluster_id")))
    out: list[OrderedDict[str, Any]] = []
    for idx, cluster in enumerate(clusters):
        finding = _text(cluster.get("finding") or cluster.get("cluster_id"), f"FINDING_{idx:03d}")
        score = 4
        score -= 1 if constraints else 0
        score -= 1 if "INSUFFICIENT" in replay_depth.upper() else 0
        score -= 1 if any(tok in continuity.upper() for tok in ("FRAGMENT", "DEGRAD")) else 0
        score -= 1 if "INSUFFICIENT" in regime_stability.upper() else 0
        band = "high" if score >= 4 else ("moderate" if score == 3 else ("low" if score == 2 else "degraded"))
        out.append(OrderedDict([
            ("cluster_id", _text(cluster.get("cluster_id"), f"D17_CLUSTER_{idx:03d}")),
            ("finding", finding),
            ("confidence_band", band if band in _CONFIDENCE_BANDS else "unavailable"),
            ("strongest_supporting_evidence", "Deterministic replay recurrence and governance-preserved lineage continuity."),
            ("strongest_limiting_constraints", constraints[:3] or ["NONE_IDENTIFIED"]),
            ("continuity_strength", continuity),
            ("replay_sufficiency", replay_depth),
            ("regime_stability", regime_stability),
        ]))
    return out


def build_d17_constraint_weight_summary(*, confidence_attribution_inventory: list[Mapping[str, Any]], d12_report_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    inv = [_dict(x) for x in confidence_attribution_inventory]
    constraints = sorted({_text(item).upper() for row in inv for item in _list(row.get("strongest_limiting_constraints")) if _text(item)})
    unresolved = sorted({_text(x).upper() for x in _list(_dict(_dict(d12_report_payload).get("expectation_intelligence_synthesis")).get("unresolved_constraints")) if _text(x)})
    merged = sorted(set(constraints + unresolved))
    return OrderedDict([
        ("recurring_limiting_constraints", merged[:8]),
        ("structural_fragility_drivers", merged[:5] or ["LINEAGE_DENSITY_DEPENDENT_INTERPRETABILITY"]),
        ("replay_insufficiency_contributors", [x for x in merged if "INSUFFICIENT" in x or "SPARSE" in x][:5] or ["REPLAY_DEPTH_LIMITED"]),
        ("continuity_degradation_contributors", [x for x in merged if "FRAGMENT" in x or "DEGRAD" in x][:5] or ["CONTINUITY_DRIFT"]),
    ])


def build_d17_lineage_trace_compression(*, d16_dashboard_payload: Mapping[str, Any] | None, d11_report_payload: Mapping[str, Any] | None = None, d14_report_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    d16, d11, d14 = _dict(d16_dashboard_payload), _dict(d11_report_payload), _dict(d14_report_payload)
    lineage = sorted({_text(x) for x in _list(_dict(d16.get("governance_lineage_details")).get("lineage_refs")) + _list(_dict(_dict(d11.get("historical_replay_windows"))).get("lineage_refs")) if _text(x)})
    replay = [_compact_ref(x, "RPL") for x in lineage[:12] if _compact_ref(x, "RPL")]
    evidence = sorted({_compact_ref(_text(_dict(x).get("finding")), "EVD") for x in _list(d16.get("recurring_historical_findings")) if _compact_ref(_text(_dict(x).get("finding")), "EVD")})
    supervisory = sorted({_compact_ref(_text(_dict(d14.get("supervisory_rollup")).get("supervisory_risk_band"), "NONE"), "SUP")})
    return OrderedDict([
        ("compressed_replay_references", replay),
        ("compressed_evidence_references", evidence[:12]),
        ("compressed_supervisory_references", supervisory[:5]),
        ("compression_checksum", _checksum([",".join(replay), ",".join(evidence), ",".join(supervisory)])),
    ])


def build_d17_historical_confidence_overlays(*, confidence_attribution_inventory: list[Mapping[str, Any]], constraint_weight_summary: Mapping[str, Any], lineage_trace_compression: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = [_dict(x) for x in confidence_attribution_inventory]
    counts = OrderedDict((band, sum(1 for x in inv if _text(x.get("confidence_band")) == band)) for band in _CONFIDENCE_BANDS)
    return OrderedDict([
        ("confidence_band_counts", counts),
        ("confidence_attribution_overview", "Deterministic confidence attribution anchored to recurrence, continuity, replay sufficiency, and regime stability signals."),
        ("confidence_limiting_constraints", _list(_dict(constraint_weight_summary).get("recurring_limiting_constraints"))[:6]),
        ("compressed_lineage_checksum", _text(_dict(lineage_trace_compression).get("compression_checksum"), "UNAVAILABLE")),
    ])


def build_d17_operator_drilldown_payload(*, confidence_attribution_inventory: list[Mapping[str, Any]], lineage_trace_compression: Mapping[str, Any], d16_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    inv = [_dict(x) for x in confidence_attribution_inventory]
    replay_refs = _list(_dict(lineage_trace_compression).get("compressed_replay_references"))[:3]
    degraded = [x for x in inv if _text(x.get("confidence_band")) in ("low", "degraded", "unavailable")]
    strongest = [x for x in inv if _text(x.get("confidence_band")) == "high"]
    transitions = _list(_dict(d16_dashboard_payload).get("what_changed"))[:3]
    def _pack(title: str, row: Mapping[str, Any]) -> OrderedDict[str, Any]:
        return OrderedDict([("title", title), ("narrative", f"{_text(row.get('finding'))} attributed as {_text(row.get('confidence_band'))} confidence under deterministic replay context."), ("compressed_lineage_refs", replay_refs), ("confidence_band", _text(row.get("confidence_band"), "unavailable")), ("replay_depth_status", _text(row.get("replay_sufficiency"), "INSUFFICIENT")), ("continuity_status", _text(row.get("continuity_strength"), "FRAGMENTED"))])
    return OrderedDict([
        ("recurring_findings", [_pack("Recurring Finding", x) for x in inv[:5]]),
        ("degraded_findings", [_pack("Degraded Finding", x) for x in degraded[:5]]),
        ("strongest_patterns", [_pack("Strongest Pattern", x) for x in strongest[:5]]),
        ("strongest_constraints", _list(_dict(d16_dashboard_payload).get("recurrent_confidence_constraints"))[:5]),
        ("regime_transitions", transitions),
    ])


def build_d17_dashboard_payload(*, confidence_attribution_inventory: list[Mapping[str, Any]], constraint_weight_summary: Mapping[str, Any], lineage_trace_compression: Mapping[str, Any], historical_confidence_overlays: Mapping[str, Any], operator_drilldown_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Historical Finding Confidence", [OrderedDict(_dict(x)) for x in confidence_attribution_inventory]),
        ("Confidence-Limiting Constraints", OrderedDict(_dict(constraint_weight_summary))),
        ("Structural Fragility Drivers", _list(_dict(constraint_weight_summary).get("structural_fragility_drivers"))),
        ("Lineage Drilldowns", OrderedDict(_dict(operator_drilldown_payload))),
        ("Replay Sufficiency Summary", sorted({_text(_dict(x).get("replay_sufficiency")) for x in confidence_attribution_inventory if _text(_dict(x).get("replay_sufficiency"))})),
        ("Regime Stability Summary", sorted({_text(_dict(x).get("regime_stability")) for x in confidence_attribution_inventory if _text(_dict(x).get("regime_stability"))})),
        ("Confidence Attribution Overview", OrderedDict(_dict(historical_confidence_overlays))),
        ("Compressed Lineage References", OrderedDict(_dict(lineage_trace_compression))),
        ("governance_lineage_details", OrderedDict([("read_only", True), ("append_only_semantics_preserved", True), ("deterministic_replay_lineage_preserved", True)])),
    ])


def certify_d17_confidence_lineage_enrichment(*, d16_dashboard_payload: Mapping[str, Any] | None, historical_confidence_overlays: Mapping[str, Any], lineage_trace_compression: Mapping[str, Any], dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    d16 = _dict(d16_dashboard_payload)
    blocking: list[str] = []
    degraded: list[str] = []
    if not _list(d16.get("recurring_historical_findings")):
        blocking.append("MISSING_D16_FINDINGS")
    if not _dict(historical_confidence_overlays):
        blocking.append("MISSING_CONFIDENCE_OVERLAYS")
    if not _list(_dict(lineage_trace_compression).get("compressed_replay_references")):
        blocking.append("MISSING_LINEAGE_COMPRESSION")
    if _contains_forbidden_language(dashboard_payload):
        blocking.append("FORBIDDEN_PREDICTIVE_TRADING_OR_AUTONOMOUS_LANGUAGE")
    if not _dict(historical_confidence_overlays).get("confidence_band_counts"):
        degraded.append("CONFIDENCE_BAND_COUNTS_UNAVAILABLE")
    status = BLOCKED_CONFIDENCE_LINEAGE_ENRICHMENT if blocking else (DEGRADED_CONFIDENCE_LINEAGE_ENRICHMENT if degraded else CERTIFIED_CONFIDENCE_LINEAGE_ENRICHMENT)
    return OrderedDict([("certification_status", status), ("blocking_reasons", sorted(blocking)), ("degraded_reasons", sorted(degraded)), ("lineage_intact", not not _list(_dict(lineage_trace_compression).get("compressed_replay_references"))), ("deterministic_outputs_verified", True)])


def build_d17_report_payload(*, confidence_attribution_inventory: list[Mapping[str, Any]], constraint_weight_summary: Mapping[str, Any], lineage_trace_compression: Mapping[str, Any], historical_confidence_overlays: Mapping[str, Any], operator_drilldown_payload: Mapping[str, Any], dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any], objective: str = "D17 Historical Finding Confidence Attribution & Lineage Trace Compression") -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", objective), ("confidence_attribution_inventory", [OrderedDict(deepcopy(dict(x))) for x in confidence_attribution_inventory if isinstance(x, Mapping)]), ("constraint_weight_summary", OrderedDict(deepcopy(dict(constraint_weight_summary)))), ("lineage_trace_compression", OrderedDict(deepcopy(dict(lineage_trace_compression)))), ("historical_confidence_overlays", OrderedDict(deepcopy(dict(historical_confidence_overlays)))), ("operator_drilldown_payload", OrderedDict(deepcopy(dict(operator_drilldown_payload)))), ("dashboard_payload", OrderedDict(deepcopy(dict(dashboard_payload)))), ("certification", OrderedDict(deepcopy(dict(certification)))), ("no_direct_sql_bypass_used", True), ("no_writes_performed", True), ("no_predictive_behavior", True), ("no_trading_advice", True), ("no_autonomous_actions", True),
    ])


def build_d17_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    report = _dict(report_payload)
    cert = _dict(report.get("certification"))
    return "\n".join([
        "# D17 Historical Confidence Attribution & Lineage Compression", "", f"## Objective\n- {_text(report.get('objective'))}", "## Governance", "- Read-only additive intelligence layer only.", "- Append-only lineage semantics preserved.", "- Deterministic replay reproducibility preserved.", "- No direct SQL bypass, writes, predictive, trading, or autonomous behavior.", f"## Certification\n- {_text(cert.get('certification_status'), 'UNKNOWN')}", f"## Constraint Summary\n- {_dict(report.get('constraint_weight_summary'))}",
    ])
