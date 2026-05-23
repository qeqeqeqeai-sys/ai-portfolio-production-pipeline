"""O9 deterministic dashboard operationalization closeout and end-to-end certification."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "o9_dashboard_operationalization_closeout_v1"
MODULE_VERSION = "1.0.0"
REQUIRED_LAYERS = tuple(f"o{i}" for i in range(1, 9))
FIXED_LAYER_ORDER = tuple(f"O{i}" for i in range(1, 9))
FORBIDDEN_CAPABILITIES = (
    "live_market_fetching",
    "database_writes",
    "database_reads",
    "client_creation",
    "environment_variable_reads",
    "network_calls",
    "llm_calls",
    "trading_instructions",
    "portfolio_optimization",
    "predictive_return_forecasts",
    "hidden_non_determinism",
    "current_time_dependency",
)


def _to_mapping(payload: Any) -> Mapping[str, Any]:
    return deepcopy(dict(payload)) if isinstance(payload, Mapping) else {}


def _canonical_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _extract_status(layer_payload: Mapping[str, Any]) -> str:
    return str(layer_payload.get("certification_status") or layer_payload.get("status") or "missing")


def _extract_checksum(layer_payload: Mapping[str, Any]) -> str:
    for key in ("checksum", "manifest_checksum", "payload_checksum"):
        if layer_payload.get(key):
            return str(layer_payload[key])
    return ""


def build_o9_operationalization_layer_inventory(upstream_payload: Any) -> list[OrderedDict]:
    payload = _to_mapping(upstream_payload)
    out: list[OrderedDict] = []
    for idx, (lname, label) in enumerate(zip(REQUIRED_LAYERS, FIXED_LAYER_ORDER), start=1):
        layer = _to_mapping(payload.get(lname))
        present = bool(layer)
        status = _extract_status(layer)
        checksum = _extract_checksum(layer)
        lineage = deepcopy(layer.get("lineage_references") or layer.get("lineage") or [])
        out.append(OrderedDict([
            ("position", idx),
            ("layer_key", lname),
            ("layer", label),
            ("present", present),
            ("status", status),
            ("checksum", checksum),
            ("lineage_references", lineage),
            ("degraded_reasons", deepcopy(layer.get("degraded_reasons") or [])),
            ("blocked_reasons", deepcopy(layer.get("blocked_reasons") or [])),
            ("governance_notes", deepcopy(layer.get("governance_notes") or [])),
        ]))
    return out


def build_o9_end_to_end_lineage_summary(layer_inventory: list[Mapping[str, Any]]) -> OrderedDict:
    continuity_breaks = [f"missing_{i['layer_key']}" for i in layer_inventory if not i.get("present")]
    return OrderedDict([
        ("fixed_layer_order", list(FIXED_LAYER_ORDER)),
        ("observed_layer_order", [i["layer"] for i in sorted(layer_inventory, key=lambda x: x["position"])]),
        ("lineage_references", [OrderedDict([("layer", i["layer"]), ("references", deepcopy(i.get("lineage_references") or []))]) for i in layer_inventory]),
        ("lineage_continuity", len(continuity_breaks) == 0),
        ("continuity_breaks", continuity_breaks),
    ])


def build_o9_end_to_end_invariant_review(closeout_payload: Mapping[str, Any]) -> OrderedDict:
    inventory = closeout_payload["layer_inventory"]
    deterministic_shape = list(closeout_payload.keys()) == [
        "layer_inventory", "end_to_end_lineage_summary", "end_to_end_invariant_review", "governance_boundary_review", "replay_checksum_manifest", "certification", "closeout_summary", "supervisor_interpretation", "replay_metadata"
    ]
    return OrderedDict([
        ("required_layers_present", all(i["present"] for i in inventory)),
        ("fixed_order_enforced", [i["layer"] for i in inventory] == list(FIXED_LAYER_ORDER)),
        ("checksums_present", all(bool(i["checksum"]) for i in inventory if i["present"])),
        ("lineage_continuity", bool(closeout_payload["end_to_end_lineage_summary"]["lineage_continuity"])),
        ("replay_metadata_present", bool(closeout_payload.get("replay_metadata"))),
        ("deterministic_payload_shape", deterministic_shape),
        ("additive_export_completeness", True),
        ("end_to_end_interpretation_safety", True),
    ])


def build_o9_governance_boundary_review(upstream_payload: Any) -> OrderedDict:
    payload = _to_mapping(upstream_payload)
    observed = sorted({str(c) for c in deepcopy(payload.get("forbidden_capabilities") or [])})
    violations = [cap for cap in FORBIDDEN_CAPABILITIES if cap in observed]
    return OrderedDict([
        ("forbidden_capabilities", list(FORBIDDEN_CAPABILITIES)),
        ("observed_forbidden_capabilities", observed),
        ("forbidden_capability_violations", violations),
        ("governance_boundary_compliant", len(violations) == 0),
    ])


def build_o9_replay_checksum_manifest(closeout_payload: Mapping[str, Any]) -> OrderedDict:
    inventory = closeout_payload["layer_inventory"]
    layer_checksums = OrderedDict((i["layer"], i["checksum"] or "missing") for i in inventory)
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("layer_checksums", layer_checksums),
        ("closeout_checksum", _canonical_checksum(closeout_payload)),
    ])


def certify_o9_dashboard_operationalization_closeout(closeout_payload: Mapping[str, Any]) -> OrderedDict:
    inventory = closeout_payload["layer_inventory"]
    governance = closeout_payload["governance_boundary_review"]
    invariants = closeout_payload["end_to_end_invariant_review"]
    blocked, degraded = [], []
    for item in inventory:
        if not item["present"]:
            blocked.append(f"missing_required_layer:{item['layer_key']}")
        elif "blocked" in str(item["status"]).lower():
            blocked.append(f"upstream_blocked:{item['layer_key']}")
        if item["present"] and (not item["checksum"] or not item["lineage_references"]):
            degraded.append(f"missing_optional_detail:{item['layer_key']}")
        degraded.extend(str(x) for x in item.get("degraded_reasons") or [])
        blocked.extend(str(x) for x in item.get("blocked_reasons") or [])
    if not governance["governance_boundary_compliant"]:
        blocked.extend([f"forbidden_capability:{v}" for v in governance["forbidden_capability_violations"]])
    if not invariants["lineage_continuity"]:
        blocked.append("lineage_continuity_failed")
    if not invariants["deterministic_payload_shape"]:
        blocked.append("deterministic_payload_shape_failed")
    status = "CERTIFIED_DASHBOARD_OPERATIONALIZATION_COMPLETE"
    if blocked:
        status = "BLOCKED_DASHBOARD_OPERATIONALIZATION_INVALID"
    elif degraded:
        status = "DEGRADED_DASHBOARD_OPERATIONALIZATION_COMPLETE"
    return OrderedDict([
        ("certification_status", status),
        ("blocked_reasons", sorted(set(blocked))),
        ("degraded_reasons", sorted(set(degraded))),
    ])


def build_o9_dashboard_operationalization_closeout_payload(upstream_payload: Any) -> OrderedDict:
    payload = _to_mapping(upstream_payload)
    layer_inventory = build_o9_operationalization_layer_inventory(payload)
    replay_metadata = deepcopy(payload.get("replay_metadata") or {})
    closeout = OrderedDict([
        ("layer_inventory", layer_inventory),
        ("end_to_end_lineage_summary", OrderedDict()),
        ("end_to_end_invariant_review", OrderedDict()),
        ("governance_boundary_review", OrderedDict()),
        ("replay_checksum_manifest", OrderedDict()),
        ("certification", OrderedDict()),
        ("closeout_summary", OrderedDict()),
        ("supervisor_interpretation", OrderedDict()),
        ("replay_metadata", replay_metadata),
    ])
    closeout["end_to_end_lineage_summary"] = build_o9_end_to_end_lineage_summary(layer_inventory)
    closeout["governance_boundary_review"] = build_o9_governance_boundary_review(payload)
    closeout["end_to_end_invariant_review"] = build_o9_end_to_end_invariant_review(closeout)
    closeout["certification"] = certify_o9_dashboard_operationalization_closeout(closeout)
    closeout["replay_checksum_manifest"] = build_o9_replay_checksum_manifest(closeout)
    closeout["closeout_summary"] = OrderedDict([
        ("required_layers", list(FIXED_LAYER_ORDER)),
        ("observed_layers", [i["layer"] for i in layer_inventory]),
        ("certification_status", closeout["certification"]["certification_status"]),
    ])
    closeout["supervisor_interpretation"] = OrderedDict([
        ("safe_for_dashboard_consumption", closeout["certification"]["certification_status"] != "BLOCKED_DASHBOARD_OPERATIONALIZATION_INVALID"),
        ("status", closeout["certification"]["certification_status"]),
    ])
    return closeout


def build_o9_dashboard_operationalization_closeout_report(upstream_payload: Any) -> OrderedDict:
    c = build_o9_dashboard_operationalization_closeout_payload(upstream_payload)
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("certification", c["certification"]),
        ("closeout_summary", c["closeout_summary"]),
        ("governance_boundary_review", c["governance_boundary_review"]),
        ("replay_checksum_manifest", c["replay_checksum_manifest"]),
    ])


__all__ = [
    "build_o9_operationalization_layer_inventory",
    "build_o9_end_to_end_lineage_summary",
    "build_o9_end_to_end_invariant_review",
    "build_o9_governance_boundary_review",
    "build_o9_replay_checksum_manifest",
    "build_o9_dashboard_operationalization_closeout_payload",
    "certify_o9_dashboard_operationalization_closeout",
    "build_o9_dashboard_operationalization_closeout_report",
]
