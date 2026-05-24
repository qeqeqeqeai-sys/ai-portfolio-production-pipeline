from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

D8_5_VERSION = "d8_5_operational_intelligence_density_verification_v1"


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _theme_lists(d8_2_payload: Mapping[str, Any]) -> tuple[list[str], list[str], list[str], list[str]]:
    semantic = d8_2_payload.get("semantic_persistence_summary") if isinstance(d8_2_payload.get("semantic_persistence_summary"), Mapping) else {}
    evolution = d8_2_payload.get("theme_evolution_summary") if isinstance(d8_2_payload.get("theme_evolution_summary"), Mapping) else {}
    recurring = sorted({_as_text(x) for x in _as_list(semantic.get("recurring_themes")) if _as_text(x)})
    emerging = sorted({_as_text(x) for x in _as_list(evolution.get("emerging_themes")) if _as_text(x)})
    fading = sorted({_as_text(x) for x in _as_list(evolution.get("decaying_themes")) if _as_text(x)})
    observed = sorted({_as_text(x) for x in _as_list(semantic.get("themes_observed")) if _as_text(x)})
    return recurring, emerging, fading, observed


def build_d8_5_operational_intelligence_density_verification(*, findings: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]], replay_metadata_rows: list[Mapping[str, Any]], historical_runs_payloads: list[Mapping[str, Any]], d8_payload: Mapping[str, Any], d8_2_payload: Mapping[str, Any], e2_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    findings_rows = [f for f in _as_list(findings) if isinstance(f, Mapping)]
    evidence_rows = [e for e in _as_list(evidence_maps) if isinstance(e, Mapping)]
    replay_rows = [r for r in _as_list(replay_metadata_rows) if isinstance(r, Mapping)]
    history_rows = [r for r in _as_list(historical_runs_payloads) if isinstance(r, Mapping)]

    evidence_refs = set()
    findings_with_linkage = set()
    for row in evidence_rows:
        fid = _as_text(row.get("finding_id"))
        refs = [_as_text(row.get("evidence_ref"))] + [_as_text(x) for x in _as_list(row.get("supporting_evidence_refs"))]
        payload = row.get("payload") if isinstance(row.get("payload"), Mapping) else {}
        refs += [_as_text(x) for x in _as_list(payload.get("supporting_evidence_refs"))]
        refs = [r for r in refs if r]
        if refs:
            evidence_refs.update(refs)
            if fid:
                findings_with_linkage.add(fid)

    contradiction_rows = [r for r in _as_list(e2_payload.get("contradiction_evidence_map")) if isinstance(r, Mapping)]
    contradiction_claims = sorted({_as_text(r.get("contradiction_claim")) for r in contradiction_rows if _as_text(r.get("contradiction_claim"))})
    contradiction_clusters = sorted({tuple(sorted({_as_text(x) for x in _as_list(r.get("affected_findings")) if _as_text(x)})) for r in contradiction_rows if _as_list(r.get("affected_findings"))})

    recurring, emerging, fading, observed_themes = _theme_lists(d8_2_payload)
    strongest_support = (d8_payload.get("supporting_evidence_rankings") or {}).get("strongest_supporting_evidence") if isinstance(d8_payload.get("supporting_evidence_rankings"), Mapping) else None

    caveat_reasons = sorted({_as_text(x) for x in _as_list(((d8_2_payload.get("replay_density_inventory") or {}).get("caveats"))) if _as_text(x)})
    caveat_reasons.extend(["no_history_rows" for _ in [0] if not history_rows])
    caveat_reasons.extend(["no_replay_metadata_rows" for _ in [0] if not replay_rows])
    caveat_reasons = sorted(set(caveat_reasons))

    if not history_rows:
        readiness = "DENSITY_BLOCKED_BY_NO_HISTORY"
    elif not findings_rows and evidence_refs:
        readiness = "DENSITY_BLOCKED_BY_SHAPE_GAP"
    elif len(findings_rows) >= 2 and len(evidence_refs) >= 2 and recurring:
        readiness = "DENSITY_OPERATIONAL"
    else:
        readiness = "DENSITY_SPARSE_BUT_VALID"

    payload = OrderedDict([
        ("d8_5_version", D8_5_VERSION),
        ("findings_loaded", len(findings_rows)),
        ("unique_evidence_refs_loaded", len(evidence_refs)),
        ("findings_with_evidence_linkage", len(findings_with_linkage)),
        ("replay_metadata_rows_loaded", len(replay_rows)),
        ("historical_runs_derived", len(history_rows)),
        ("recurring_semantic_themes_detected", len(recurring)),
        ("contradiction_claims_detected", len(contradiction_claims)),
        ("contradiction_clusters_detected", len(contradiction_clusters)),
        ("strongest_supporting_evidence_available", bool(strongest_support and _as_text(strongest_support.get("evidence_ref")))),
        ("persistent_theme_availability", bool(recurring)),
        ("emerging_theme_availability", bool(emerging)),
        ("fading_theme_availability", bool(fading)),
        ("caveat_count", len(caveat_reasons)),
        ("caveat_reasons", caveat_reasons),
        ("readiness_status", readiness),
    ])
    payload["d8_5_density_checksum"] = _stable_checksum(payload)
    return payload


def assess_d8_5_supabase_backfill_readiness(*, density_verification: Mapping[str, Any], findings: list[Mapping[str, Any]], historical_runs_payloads: list[Mapping[str, Any]], replay_metadata_rows: list[Mapping[str, Any]], evidence_maps: list[Mapping[str, Any]], e2_payload: Mapping[str, Any], d8_2_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    findings_count = len([f for f in _as_list(findings) if isinstance(f, Mapping)])
    runs_count = len([r for r in _as_list(historical_runs_payloads) if isinstance(r, Mapping)])
    replay_count = len([r for r in _as_list(replay_metadata_rows) if isinstance(r, Mapping)])
    evidence_count = len([e for e in _as_list(evidence_maps) if isinstance(e, Mapping)])
    contradiction_input_count = len([r for r in _as_list(e2_payload.get("contradiction_evidence_map")) if isinstance(r, Mapping)])
    recurring, _emerging, _fading, observed = _theme_lists(d8_2_payload)

    gaps = []
    if replay_count == 0 or runs_count == 0:
        gaps.append("insufficient_historical_replay_rows")
    if findings_count <= 1 and runs_count <= 1:
        gaps.append("findings_not_accumulated_over_time")
    if evidence_count == 0 or int(density_verification.get("findings_with_evidence_linkage") or 0) == 0:
        gaps.append("evidence_maps_missing_or_disconnected")
    if runs_count > 0 and not observed:
        gaps.append("semantic_theme_fields_absent_in_historical_rows")
    if contradiction_input_count > 0 and int(density_verification.get("contradiction_claims_detected") or 0) == 0:
        gaps.append("contradiction_rows_absent_despite_inputs")
    if runs_count <= 1:
        gaps.append("retention_too_narrow")

    readiness = _as_text(density_verification.get("readiness_status"))
    if "DENSITY_BLOCKED_BY_SHAPE_GAP" == readiness:
        recommendation = "BACKFILL_NOT_ALLOWED_SCHEMA_GAP"
    elif findings_count == 0 and evidence_count == 0 and replay_count == 0:
        recommendation = "BACKFILL_NOT_NEEDED_SPARSE_INPUTS"
    elif "insufficient_historical_replay_rows" in gaps:
        recommendation = "BACKFILL_REQUIRED_FOR_HISTORY_CONTINUITY"
    elif gaps:
        recommendation = "BACKFILL_RECOMMENDED_READ_ONLY_FIRST"
    else:
        recommendation = "NO_BACKFILL_REQUIRED"

    payload = OrderedDict([
        ("recommendation", recommendation),
        ("gap_count", len(gaps)),
        ("gap_reasons", sorted(gaps)),
        ("write_path_enabled", False),
        ("dry_run_only", True),
    ])
    payload["d8_5_backfill_checksum"] = _stable_checksum(payload)
    return payload
