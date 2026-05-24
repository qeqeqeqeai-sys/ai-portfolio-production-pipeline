from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def _replay_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (_text(row.get("replay_timestamp")), _text(row.get("replay_id")))


def build_d11_backfill_inventory(*, replay_rows: list[Mapping[str, Any]] | None, manifest_rows: list[Mapping[str, Any]] | None, replay_snapshots: list[Mapping[str, Any]] | None = None, historical_finding_payloads: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    replays = sorted([_dict(x) for x in _list(replay_rows) if isinstance(x, Mapping)], key=_replay_sort_key)
    manifests = sorted([_dict(x) for x in _list(manifest_rows) if isinstance(x, Mapping)], key=lambda m: _text(m.get("manifest_checksum")))
    snapshots = [_dict(x) for x in _list(replay_snapshots) if isinstance(x, Mapping)]
    findings = [_dict(x) for x in _list(historical_finding_payloads) if isinstance(x, Mapping)]

    replay_ids = sorted({_text(r.get("replay_id")) for r in replays if _text(r.get("replay_id"))})
    manifest_checksums = sorted({_text(m.get("manifest_checksum")) for m in manifests if _text(m.get("manifest_checksum"))})
    ts = [_text(r.get("replay_timestamp")) for r in replays if _text(r.get("replay_timestamp"))]
    time_cov = OrderedDict([("start", min(ts) if ts else ""), ("end", max(ts) if ts else ""), ("span_observed", bool(ts))])
    categories = sorted({_text(x) for f in findings for x in _list(f.get("evidence_categories")) if _text(x)})
    if not categories:
        categories = sorted({_text(r.get("evidence_category")) for r in replays if _text(r.get("evidence_category"))})

    hcount = len(snapshots) if snapshots else max(1, len(ts)) if ts else 0
    status = "BACKFILL_INVENTORY_READY" if replays and manifests else "BACKFILL_INVENTORY_BLOCKED"
    if status == "BACKFILL_INVENTORY_READY" and (not categories or not ts):
        status = "BACKFILL_INVENTORY_DEGRADED"

    chk = _checksum([str(len(replays)), str(len(manifests)), str(hcount), ",".join(replay_ids), ",".join(manifest_checksums), ",".join(categories), _text(time_cov["start"]), _text(time_cov["end"]), status])
    return OrderedDict([
        ("replay_row_count", len(replays)),
        ("manifest_row_count", len(manifests)),
        ("historical_window_count", hcount),
        ("replay_ids", replay_ids),
        ("manifest_checksums", manifest_checksums),
        ("replay_time_coverage", time_cov),
        ("evidence_category_coverage", categories),
        ("inventory_status", status),
        ("inventory_checksum", chk),
    ])


def validate_d11_backfill_eligibility(*, replay_rows: list[Mapping[str, Any]] | None, manifest_rows: list[Mapping[str, Any]] | None) -> OrderedDict[str, Any]:
    replays = [_dict(x) for x in _list(replay_rows) if isinstance(x, Mapping)]
    manifests = [_dict(x) for x in _list(manifest_rows) if isinstance(x, Mapping)]
    blocking, degraded = [], []
    if not replays:
        blocking.append("REPLAY_ROWS_MISSING")
    if not manifests:
        blocking.append("MANIFEST_ROWS_MISSING")
    if replays and not all(_text(r.get("manifest_checksum")) for r in replays):
        blocking.append("CHECKSUM_LINEAGE_MISSING")
    replay_ids = [_text(r.get("replay_id")) for r in replays if _text(r.get("replay_id"))]
    if len(replay_ids) != len(set(replay_ids)):
        degraded.append("DUPLICATE_PREVENTION_DEGRADED")
    if replays and not all(bool(r.get("append_only", True)) for r in replays):
        degraded.append("APPEND_ONLY_GOVERNANCE_DEGRADED")
    status = "BACKFILL_BLOCKED" if blocking else ("BACKFILL_DEGRADED" if degraded else "BACKFILL_READY")
    return OrderedDict([("eligibility_status", status), ("blocking_reasons", sorted(set(blocking))), ("degraded_reasons", sorted(set(degraded)))])


def build_d11_historical_replay_windows(*, replay_rows: list[Mapping[str, Any]] | None, manifest_rows: list[Mapping[str, Any]] | None, historical_finding_payloads: list[Mapping[str, Any]] | None = None, window_size: int = 3) -> list[OrderedDict[str, Any]]:
    replays = sorted([_dict(x) for x in _list(replay_rows) if isinstance(x, Mapping)], key=_replay_sort_key)
    m_by = {_text(m.get("manifest_checksum")): _dict(m) for m in _list(manifest_rows) if isinstance(m, Mapping) and _text(_dict(m).get("manifest_checksum"))}
    f_by_replay: dict[str, list[str]] = {}
    for f in _list(historical_finding_payloads):
        ff = _dict(f); fid = _text(ff.get("finding_id"))
        for rid in _list(ff.get("replay_ids")):
            ridt = _text(rid)
            if ridt:
                f_by_replay.setdefault(ridt, []).append(fid)
    out: list[OrderedDict[str, Any]] = []
    for idx in range(0, len(replays), max(1, int(window_size))):
        chunk = replays[idx: idx + max(1, int(window_size))]
        replay_ids = [_text(r.get("replay_id")) for r in chunk if _text(r.get("replay_id"))]
        tss = [_text(r.get("replay_timestamp")) for r in chunk if _text(r.get("replay_timestamp"))]
        mrefs = sorted({_text(r.get("manifest_checksum")) for r in chunk if _text(r.get("manifest_checksum"))})
        lineage = sorted({m_by.get(m, {}).get("lineage_ref") for m in mrefs if _text(m_by.get(m, {}).get("lineage_ref"))})
        finding_refs = sorted({fid for rid in replay_ids for fid in f_by_replay.get(rid, []) if _text(fid)})
        completeness = round((sum(1 for r in chunk if _text(r.get("manifest_checksum"))) / len(chunk)), 3) if chunk else 0.0
        out.append(OrderedDict([
            ("replay_window_id", f"D11-WINDOW-{idx // max(1, int(window_size)) + 1:03d}"),
            ("replay_ids", replay_ids),
            ("replay_timestamp_range", OrderedDict([("start", min(tss) if tss else ""), ("end", max(tss) if tss else "")])),
            ("manifest_refs", mrefs),
            ("lineage_refs", lineage),
            ("finding_refs", finding_refs),
            ("replay_density", len(chunk)),
            ("evidence_completeness", completeness),
            ("deterministic_rank", idx // max(1, int(window_size)) + 1),
        ]))
    return out


def build_d11_backfill_reconstruction(*, replay_rows: list[Mapping[str, Any]] | None, manifest_rows: list[Mapping[str, Any]] | None, historical_finding_payloads: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    windows = build_d11_historical_replay_windows(replay_rows=replay_rows, manifest_rows=manifest_rows, historical_finding_payloads=historical_finding_payloads)
    seq = [OrderedDict([("replay_window_id", w["replay_window_id"]), ("replay_ids", list(w["replay_ids"])), ("replay_timestamp_range", OrderedDict(w["replay_timestamp_range"]))]) for w in windows]
    lineage = OrderedDict((w["replay_window_id"], OrderedDict([("manifest_refs", list(w["manifest_refs"])), ("lineage_refs", list(w["lineage_refs"]))])) for w in windows)
    refs = sorted({x for w in windows for x in w["finding_refs"]})
    total = sum(len(w["replay_ids"]) for w in windows) or 1
    lineage_cov = sum(len(w["manifest_refs"]) for w in windows) / total
    confidence = round(min(1.0, 0.5 + (lineage_cov / 2.0)), 3)
    constraints = []
    continuity = "CONTINUITY_OK"
    if not windows:
        continuity = "CONTINUITY_FRAGMENTED"; constraints.append("REPLAY_TIMELINE_EMPTY")
    elif any(not w["manifest_refs"] for w in windows):
        continuity = "CONTINUITY_DEGRADED"; constraints.append("MANIFEST_GAPS_PRESENT")
    if any(not w["lineage_refs"] for w in windows):
        continuity = "CONTINUITY_FRAGMENTED" if not windows or all(not w["lineage_refs"] for w in windows) else "CONTINUITY_DEGRADED"
        constraints.append("LINEAGE_REFS_INCOMPLETE")
    return OrderedDict([
        ("reconstructed_replay_sequences", seq),
        ("reconstructed_lineage_map", lineage),
        ("reconstructed_finding_refs", refs),
        ("reconstruction_confidence", confidence),
        ("reconstruction_constraints", sorted(set(constraints))),
        ("replay_continuity_status", continuity),
    ])


def build_d11_historical_evidence_summary(*, backfill_inventory: Mapping[str, Any], replay_windows: list[Mapping[str, Any]], reconstruction: Mapping[str, Any]) -> OrderedDict[str, Any]:
    window_count = len(_list(replay_windows))
    continuity = _text(reconstruction.get("replay_continuity_status"))
    depth = "REPLAY_DEPTH_SUFFICIENT" if window_count >= 2 else ("REPLAY_DEPTH_LIMITED" if window_count == 1 else "REPLAY_DEPTH_INSUFFICIENT")
    state = "HISTORICAL_OPERATIONAL_READY" if continuity == "CONTINUITY_OK" else ("HISTORICAL_OPERATIONAL_DEGRADED" if continuity == "CONTINUITY_DEGRADED" else "HISTORICAL_OPERATIONAL_BLOCKED")
    integrity = "CHECKSUM_LINEAGE_RECURRING" if _list(backfill_inventory.get("manifest_checksums")) else "CHECKSUM_LINEAGE_WEAK"
    constraints = _list(reconstruction.get("reconstruction_constraints"))
    strongest_constraint = constraints[0] if constraints else "NO_RECURRENT_CONSTRAINT"
    conf = "HIGH" if float(reconstruction.get("reconstruction_confidence") or 0) >= 0.85 else ("MEDIUM" if float(reconstruction.get("reconstruction_confidence") or 0) >= 0.65 else "LOW")
    interp = "Historical replay depth supports governed expectation-intelligence enrichment." if depth == "REPLAY_DEPTH_SUFFICIENT" else "Historical replay depth is improving but constrained; continue controlled backfill."
    return OrderedDict([
        ("dominant_historical_operational_state", state),
        ("strongest_recurring_integrity_signal", integrity),
        ("strongest_recurrent_constraint", strongest_constraint),
        ("replay_depth_assessment", depth),
        ("evidence_history_confidence", conf),
        ("historical_window_count", window_count),
        ("unresolved_historical_constraints", constraints),
        ("historical_interpretation", interp),
    ])


def certify_d11_backfill(*, inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any], replay_windows: list[Mapping[str, Any]], reconstruction: Mapping[str, Any], historical_summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    elig = _text(eligibility_validation.get("eligibility_status"))
    continuity = _text(reconstruction.get("replay_continuity_status"))
    has_windows = len(_list(replay_windows)) > 0
    depth_ok = _text(historical_summary.get("replay_depth_assessment")) in {"REPLAY_DEPTH_SUFFICIENT", "REPLAY_DEPTH_LIMITED"}
    lineage_ok = bool(_list(inventory.get("manifest_checksums")))
    blocked = int(inventory.get("replay_row_count") or 0) == 0 or int(inventory.get("manifest_row_count") or 0) == 0 or continuity == "CONTINUITY_FRAGMENTED" or not lineage_ok
    if blocked or elig == "BACKFILL_BLOCKED":
        status = "BLOCKED_HISTORICAL_BACKFILL"
    elif elig == "BACKFILL_READY" and has_windows and continuity in {"CONTINUITY_OK", "CONTINUITY_DEGRADED"} and depth_ok and lineage_ok:
        status = "CERTIFIED_HISTORICAL_BACKFILL"
    else:
        status = "DEGRADED_HISTORICAL_BACKFILL"
    return OrderedDict([("certification_status", status), ("continuity_status", continuity), ("lineage_intact", lineage_ok), ("replay_windows_present", has_windows)])


def build_d11_dashboard_backfill_cards(*, historical_summary: Mapping[str, Any], certification: Mapping[str, Any], inventory: Mapping[str, Any], reconstruction: Mapping[str, Any]) -> OrderedDict[str, Any]:
    rec = "Proceed to D12 governed historical interpretation uplift." if _text(certification.get("certification_status")) == "CERTIFIED_HISTORICAL_BACKFILL" else "Resolve continuity/lineage constraints before deeper historical interpretation."
    return OrderedDict([
        ("historical_backfill_status", certification.get("certification_status")),
        ("replay_depth_assessment", historical_summary.get("replay_depth_assessment")),
        ("historical_window_count", historical_summary.get("historical_window_count")),
        ("replay_time_coverage", OrderedDict(deepcopy(dict(_dict(inventory.get("replay_time_coverage")))))),
        ("strongest_recurring_integrity_signal", historical_summary.get("strongest_recurring_integrity_signal")),
        ("strongest_recurrent_constraint", historical_summary.get("strongest_recurrent_constraint")),
        ("continuity_status", reconstruction.get("replay_continuity_status")),
        ("evidence_history_confidence", historical_summary.get("evidence_history_confidence")),
        ("recommendation", rec),
    ])


def build_d11_report_payload(*, objective: str = "D11 Historical Replay / Evidence Backfill", backfill_inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any], replay_windows: list[Mapping[str, Any]], reconstruction: Mapping[str, Any], historical_summary: Mapping[str, Any], dashboard_cards: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", objective), ("backfill_inventory", OrderedDict(deepcopy(dict(backfill_inventory)))), ("eligibility_validation", OrderedDict(deepcopy(dict(eligibility_validation)))),
        ("replay_windows", [OrderedDict(deepcopy(dict(x))) for x in _list(replay_windows)]), ("reconstruction", OrderedDict(deepcopy(dict(reconstruction)))),
        ("historical_summary", OrderedDict(deepcopy(dict(historical_summary)))), ("dashboard_cards", OrderedDict(deepcopy(dict(dashboard_cards)))), ("certification", OrderedDict(deepcopy(dict(certification)))),
        ("no_direct_sql_bypass_used", True), ("no_writes_performed", True), ("recommendation", dashboard_cards.get("recommendation") or certification.get("certification_status")),
    ])


def build_d11_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    i = _dict(report_payload.get("backfill_inventory")); e = _dict(report_payload.get("eligibility_validation")); r = _dict(report_payload.get("reconstruction")); s = _dict(report_payload.get("historical_summary")); c = _dict(report_payload.get("certification")); d = _dict(report_payload.get("dashboard_cards"))
    return "\n".join([
        "# D11 Historical Replay / Evidence Backfill", "", f"## Objective\n- {report_payload.get('objective')}",
        "## Scope\n- Deterministic, governed historical replay/evidence backfill from persisted structures only.",
        "## Non-goals\n- No live fetching.\n- No direct SQL bypass.\n- No writes.\n- No predictive/trading behavior.",
        f"## Historical Backfill Inventory\n- Replay rows: {i.get('replay_row_count')}\n- Manifest rows: {i.get('manifest_row_count')}\n- Inventory status: {i.get('inventory_status')}",
        f"## Eligibility Validation\n- Status: {e.get('eligibility_status')}\n- Blocking reasons: {e.get('blocking_reasons')}\n- Degraded reasons: {e.get('degraded_reasons')}",
        f"## Replay Window Construction\n- Window count: {len(_list(report_payload.get('replay_windows')))}",
        f"## Replay Reconstruction\n- Continuity: {r.get('replay_continuity_status')}\n- Confidence: {r.get('reconstruction_confidence')}",
        f"## Historical Evidence Summary\n- Dominant state: {s.get('dominant_historical_operational_state')}\n- Depth: {s.get('replay_depth_assessment')}",
        f"## Dashboard Cards\n- Backfill status: {d.get('historical_backfill_status')}\n- Recommendation: {d.get('recommendation')}",
        f"## Certification\n- {c.get('certification_status')}",
        "## Governance Boundaries\n- no_direct_sql_bypass_used: True\n- no_writes_performed: True\n- Deterministic ordering and lineage continuity preserved.",
        f"## Final Recommendation\n- {report_payload.get('recommendation')}",
    ])
