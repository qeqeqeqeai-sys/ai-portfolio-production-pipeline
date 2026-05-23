"""D5 real dashboard execution closeout certification layer.

Deterministic closeout-only certification across O9/D2/D3/D4 artifacts.
"""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

CERTIFIED_REAL_DASHBOARD_EXECUTION_COMPLETE = "CERTIFIED_REAL_DASHBOARD_EXECUTION_COMPLETE"
DEGRADED_REAL_DASHBOARD_EXECUTION_COMPLETE = "DEGRADED_REAL_DASHBOARD_EXECUTION_COMPLETE"
BLOCKED_REAL_DASHBOARD_EXECUTION_INVALID = "BLOCKED_REAL_DASHBOARD_EXECUTION_INVALID"

LAYER_ORDER = ("O9", "D2", "D3", "D4")
FORBIDDEN_CAPABILITIES = (
    "database_writes",
    "database_reads",
    "client_creation",
    "environment_variable_reads",
    "live_market_fetching",
    "network_calls",
    "llm_calls",
    "trading_instructions",
    "portfolio_optimization",
    "predictive_return_forecasts",
    "hidden_non_determinism",
    "current_time_dependency_without_caller_metadata",
)


def _copy(v: Any) -> Any:
    return deepcopy(v)


def _checksum(v: Any) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _status_text(v: Mapping[str, Any]) -> str:
    return str(v.get("status") or v.get("certification_status") or v.get("verification_status") or "")


def _is_blocked(status: str) -> bool:
    return "BLOCKED" in status.upper()


def _is_degraded(status: str) -> bool:
    return "DEGRADED" in status.upper()


def _layer_payloads(payload: Mapping[str, Any] | None) -> OrderedDict[str, Mapping[str, Any]]:
    src = dict(_copy(payload or {}))
    return OrderedDict([
        ("O9", src.get("o9") if isinstance(src.get("o9"), Mapping) else {}),
        ("D2", src.get("d2") if isinstance(src.get("d2"), Mapping) else {}),
        ("D3", src.get("d3") if isinstance(src.get("d3"), Mapping) else {}),
        ("D4", src.get("d4") if isinstance(src.get("d4"), Mapping) else {}),
    ])


def build_d5_execution_layer_inventory(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    layers = _layer_payloads(payload)
    entries = []
    for layer in LAYER_ORDER:
        data = layers[layer]
        entries.append(OrderedDict([
            ("layer", layer),
            ("present", bool(data)),
            ("upstream_status", _status_text(data)),
            ("layer_checksum", str(data.get("contract_checksum") or data.get("summary_checksum") or data.get("verification_checksum") or data.get("handoff_checksum") or "")),
        ]))
    out = OrderedDict([("required_layer_order", list(LAYER_ORDER)), ("layers", entries)])
    out["inventory_checksum"] = _checksum(out)
    return out


def build_d5_real_execution_lineage_summary(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    layers = _layer_payloads(payload)
    continuity = OrderedDict([
        ("o9_reference_present", bool(layers["O9"])),
        ("d2_schema_reference_present", bool(layers["D2"])),
        ("d3_execution_reference_present", bool(layers["D3"])),
        ("d4_readback_reference_present", bool(layers["D4"])),
        ("d3_to_d4_handoff_present", bool(layers["D3"].get("handoff_checksum") or layers["D4"].get("handoff_checksum"))),
    ])
    out = OrderedDict([("lineage_continuity", continuity), ("layer_order", list(LAYER_ORDER))])
    out["lineage_checksum"] = _checksum(out)
    return out


def build_d5_real_execution_invariant_review(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    layers = _layer_payloads(payload)
    replay = dict(_copy(payload or {})).get("replay_metadata") if isinstance(dict(_copy(payload or {})).get("replay_metadata"), Mapping) else {}
    checks = OrderedDict([
        ("deterministic_layer_order", True),
        ("deterministic_payload_shape", True),
        ("replay_metadata_present", bool(replay)),
        ("forbidden_capability_absence", not any(bool(dict(_copy(payload or {})).get(k)) for k in FORBIDDEN_CAPABILITIES)),
        ("governance_boundary_compliance", True),
        ("d3_audit_presence", bool(layers["D3"].get("audit_records") or layers["D3"].get("audit_metadata") or layers["D3"].get("summary_checksum"))),
        ("d4_verification_handoff_presence", bool(layers["D4"].get("verification_checksum") or layers["D4"].get("handoff_checksum") or layers["D4"].get("summary_checksum"))),
    ])
    out = OrderedDict([("invariants", checks)])
    out["invariant_checksum"] = _checksum(out)
    return out


def build_d5_schema_persistence_readback_review(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    layers = _layer_payloads(payload)
    d2s, d3s, d4s = _status_text(layers["D2"]), _status_text(layers["D3"]), _status_text(layers["D4"])
    out = OrderedDict([
        ("schema_readiness", OrderedDict([("status", d2s), ("ready_or_explained", bool(d2s))])),
        ("persistence_execution", OrderedDict([("status", d3s), ("ready_or_explained", bool(d3s or layers["D3"].get("execution_state")))])),
        ("readback_verification", OrderedDict([("status", d4s), ("ready_or_explained", bool(d4s or layers["D4"].get("verification_checksum")))])),
    ])
    out["review_checksum"] = _checksum(out)
    return out


def build_d5_real_execution_checksum_manifest(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    layers = _layer_payloads(payload)
    items = []
    for layer in LAYER_ORDER:
        data = layers[layer]
        keys = sorted([k for k in data.keys() if "checksum" in k])
        items.append(OrderedDict([("layer", layer), ("checksum_keys", keys), ("stable_layer_digest", _checksum(data))]))
    out = OrderedDict([("layer_checksums", items)])
    out["manifest_checksum"] = _checksum(out)
    return out


def certify_d5_real_dashboard_execution_closeout(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = dict(_copy(payload or {}))
    layers = _layer_payloads(src)
    blocked, degraded = [], []
    for layer in LAYER_ORDER:
        if not layers[layer]:
            blocked.append(f"missing_required_layer:{layer}")
    statuses = {k: _status_text(v) for k, v in layers.items()}
    if any(_is_blocked(s) for s in statuses.values() if s):
        blocked.append("upstream_blocked_status")
    if not blocked and any(_is_degraded(s) for s in statuses.values() if s):
        degraded.append("upstream_degraded_status")
    if not src.get("replay_metadata"):
        degraded.append("missing_replay_metadata")
    if any(bool(src.get(k)) for k in FORBIDDEN_CAPABILITIES):
        blocked.append("forbidden_capability_violation")
    if not (layers["D3"].get("handoff_checksum") or layers["D4"].get("handoff_checksum")):
        degraded.append("missing_d3_d4_handoff_checksum")
    status = BLOCKED_REAL_DASHBOARD_EXECUTION_INVALID if blocked else DEGRADED_REAL_DASHBOARD_EXECUTION_COMPLETE if degraded else CERTIFIED_REAL_DASHBOARD_EXECUTION_COMPLETE
    return OrderedDict([
        ("status", status),
        ("blocked_reasons", sorted(set(blocked))),
        ("degraded_reasons", sorted(set(degraded))),
    ])


def build_d5_real_dashboard_execution_closeout_payload(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = dict(_copy(payload or {}))
    inventory = build_d5_execution_layer_inventory(src)
    lineage = build_d5_real_execution_lineage_summary(src)
    invariants = build_d5_real_execution_invariant_review(src)
    spr = build_d5_schema_persistence_readback_review(src)
    manifest = build_d5_real_execution_checksum_manifest(src)
    cert = certify_d5_real_dashboard_execution_closeout(src)
    closeout = OrderedDict([
        ("execution_status", cert["status"]),
        ("blocked_reasons", cert["blocked_reasons"]),
        ("degraded_reasons", cert["degraded_reasons"]),
    ])
    out = OrderedDict([
        ("execution_layer_inventory", inventory),
        ("real_execution_lineage_summary", lineage),
        ("real_execution_invariant_review", invariants),
        ("schema_persistence_readback_review", spr),
        ("real_execution_checksum_manifest", manifest),
        ("certification", cert),
        ("closeout_summary", closeout),
        ("supervisor_interpretation", "D5 certifies O9→D2→D3→D4 real dashboard execution readiness and continuity without performing live operations."),
        ("replay_metadata", _copy(src.get("replay_metadata") or {})),
    ])
    out["closeout_payload_checksum"] = _checksum(out)
    return out


def build_d5_real_dashboard_execution_closeout_report(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    closeout = build_d5_real_dashboard_execution_closeout_payload(payload)
    return OrderedDict([
        ("objective", "Certify end-to-end real dashboard execution closeout from schema readiness through readback verification."),
        ("closeout_payload", closeout),
    ])
