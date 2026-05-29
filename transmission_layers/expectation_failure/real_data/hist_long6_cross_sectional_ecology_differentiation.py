from __future__ import annotations

import json
from collections import OrderedDict
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

REQUIRED_WINDOWS = [20, 60, 120]
HIST_LONG6_SCHEMA_VERSION = "hist_long6_v1"
DEFAULT_HIST_LONG4_SOURCE_PATH = "artifacts/hist_long4_real_multi_window_ecology_review.json"
DEFAULT_HIST_LONG5B_SOURCE_PATH = "artifacts/hist_long5b_temporal_delta_sensitivity_classification.json"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_long6_cross_sectional_ecology_differentiation.json"
DEFAULT_REPORT_PATH = "reports/hist_long6_cross_sectional_ecology_differentiation.md"
PRIMARY_BASELINE_WINDOW = 120

FORBIDDEN_GOVERNANCE_FLAGS = (
    "fmp_calls_enabled",
    "provider_api_calls_enabled",
    "hist_long4_reexecution_enabled",
    "prediction_enabled",
    "trading_execution_enabled",
    "replay_activation_enabled",
    "replay_execution_enabled",
    "topology_persistence_enabled",
    "supabase_write_enabled",
    "raw_cache_write_enabled",
)

SOURCE_FORBIDDEN_FLAGS = (
    "prediction_enabled",
    "trading_execution_enabled",
    "replay_activation_enabled",
    "replay_execution_enabled",
    "topology_persistence_enabled",
    "supabase_write_enabled",
    "raw_cache_write_enabled",
)


def _governance() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("governance_mode", "observational_only"),
        ("phase", "HIST-LONG-6_cross_sectional_ecology_differentiation"),
        ("local_artifacts_only", True),
        ("fmp_calls_enabled", False),
        ("provider_api_calls_enabled", False),
        ("hist_long4_reexecution_enabled", False),
        ("replay_activation_enabled", False),
        ("replay_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("supabase_write_enabled", False),
        ("raw_cache_write_enabled", False),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("analysis_only", True),
    ])


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _window_id(row: Mapping[str, Any]) -> int | None:
    value = row.get("window_trading_days", row.get("window_days", row.get("window")))
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _status_ok(value: Any) -> bool:
    return str(value).lower() in {"ok", "success"}


def _enabled_flags(governance: Mapping[str, Any], flags: Sequence[str]) -> list[str]:
    return [flag for flag in flags if governance.get(flag) is True]


def _digest(payload: Mapping[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _failure(reason: str, checks: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("verified", False), ("reason", reason), ("preflight_checks", OrderedDict(checks))])


def verify_sources(hist_long4: Mapping[str, Any] | None, hist_long5b: Mapping[str, Any] | None, *, hist_long4_path: str, hist_long5b_path: str) -> OrderedDict[str, Any]:
    windows = sorted(_window_id(row) for row in (hist_long4 or {}).get("window_level_results", []) or []) if hist_long4 else []
    hist4_governance = (hist_long4 or {}).get("governance_certification", {}) or {}
    hist5_governance = (hist_long5b or {}).get("governance_certification", {}) or {}
    hist4_completed_count = (hist_long4 or {}).get("longitudinal_comparison", {}).get("completed_window_count") if hist_long4 else None
    hist4_enabled = _enabled_flags(hist4_governance, SOURCE_FORBIDDEN_FLAGS)
    hist5_enabled = _enabled_flags(hist5_governance, SOURCE_FORBIDDEN_FLAGS)
    own_governance = _governance()
    own_enabled = _enabled_flags(own_governance, FORBIDDEN_GOVERNANCE_FLAGS)
    checks = OrderedDict([
        ("hist_long4_source_path", hist_long4_path),
        ("hist_long5b_source_path", hist_long5b_path),
        ("hist_long4_status", (hist_long4 or {}).get("status")),
        ("hist_long4_status_ok", hist_long4 is not None and _status_ok(hist_long4.get("status"))),
        ("all_three_real_windows_completed", (hist_long4 or {}).get("all_three_real_windows_completed") is True),
        ("hist_long4_completed_window_count", hist4_completed_count),
        ("hist_long4_windows", windows),
        ("hist_long4_windows_exactly_20_60_120", windows == REQUIRED_WINDOWS),
        ("hist_long4_forbidden_governance_enabled", hist4_enabled),
        ("hist_long5b_status", (hist_long5b or {}).get("status")),
        ("hist_long5b_status_ok", hist_long5b is not None and _status_ok(hist_long5b.get("status"))),
        ("hist_long5b_completed_windows", (hist_long5b or {}).get("completed_windows")),
        ("hist_long5b_completed_windows_exactly_20_60_120", (hist_long5b or {}).get("completed_windows") == REQUIRED_WINDOWS),
        ("hist_long5b_forbidden_governance_enabled", hist5_enabled),
        ("hist_long6_governance_flags_disabled", not own_enabled),
        ("hist_long6_forbidden_governance_enabled", own_enabled),
    ])
    if hist_long4 is None:
        return _failure("HIST-LONG-4 source missing", checks)
    if hist_long5b is None:
        return _failure("HIST-LONG-5B source missing", checks)
    for key in ("hist_long4_status_ok", "all_three_real_windows_completed", "hist_long4_windows_exactly_20_60_120", "hist_long5b_status_ok", "hist_long5b_completed_windows_exactly_20_60_120", "hist_long6_governance_flags_disabled"):
        if not checks[key]:
            return _failure(f"source verification failed: {key}", checks)
    if hist4_enabled:
        return _failure(f"HIST-LONG-4 forbidden governance enabled: {', '.join(hist4_enabled)}", checks)
    if hist5_enabled:
        return _failure(f"HIST-LONG-5B forbidden governance enabled: {', '.join(hist5_enabled)}", checks)
    return OrderedDict([
        ("verified", True),
        ("hist_long4_source_path", hist_long4_path),
        ("hist_long5b_source_path", hist_long5b_path),
        ("hist_long4_digest", _digest(hist_long4)),
        ("hist_long5b_digest", _digest(hist_long5b)),
        ("preflight_checks", checks),
    ])


def _primary_window(hist_long4: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for row in hist_long4.get("window_level_results", []) or []:
        if _window_id(row) == PRIMARY_BASELINE_WINDOW:
            return row
    return None


def _extract_groups(row: Mapping[str, Any], metric_key: str, name_key: str) -> list[Mapping[str, Any]]:
    metric = row.get(metric_key, {}) or {}
    list_key = "strongest_sectors" if name_key == "sector" else "strongest_subsectors"
    return [item for item in metric.get(list_key, []) or [] if isinstance(item, Mapping)]


def _stability_label(hist_long4: Mapping[str, Any], metric_key: str, name_key: str, group_name: str, share: float) -> str:
    values: list[float] = []
    for row in hist_long4.get("window_level_results", []) or []:
        for item in _extract_groups(row, metric_key, name_key):
            if item.get(name_key) == group_name:
                values.append(float(item.get("share", 0.0) or 0.0))
    return "stable_distinct" if len(values) == 3 and max(abs(value - share) for value in values) <= 0.000001 else "insufficient_signal"


def _confidence(symbol_count: int | None, stability_label: str) -> str:
    if symbol_count is None:
        return "insufficient_signal"
    if symbol_count >= 10 and stability_label.startswith("stable"):
        return "high"
    if symbol_count > 0:
        return "medium"
    return "low"


def _differentiation_rows(hist_long4: Mapping[str, Any], row: Mapping[str, Any], metric_key: str, name_key: str) -> list[OrderedDict[str, Any]]:
    groups = _extract_groups(row, metric_key, name_key)
    if not groups:
        return []
    total_symbols = int(row.get("effective_symbol_count") or row.get("configured_symbol_count") or 0)
    total_rows = int(row.get("normalized_rows") or 0)
    hhi = float((row.get(metric_key, {}) or {}).get("universe_hhi") or 0.0)
    expected_share = round(sum(float(item.get("share", 0.0) or 0.0) for item in groups) / len(groups), 6) if groups else None
    out: list[OrderedDict[str, Any]] = []
    for item in groups:
        name = str(item.get(name_key))
        share = round(float(item.get("share", 0.0) or 0.0), 6)
        symbol_count = int(item.get("symbol_count") or round(share * total_symbols)) if total_symbols else None
        normalized_rows = None if symbol_count is None else symbol_count * PRIMARY_BASELINE_WINDOW
        concentration_raw = round(share * share, 6)
        contribution = round(concentration_raw / hhi, 6) if hhi else None
        relative = round((share - (expected_share or 0.0)) / (expected_share or 1.0), 6) if expected_share else None
        stability = _stability_label(hist_long4, metric_key, name_key, name, share)
        score = round(min(1.0, abs(relative or 0.0) * (contribution or 0.0)), 6) if contribution is not None and relative is not None else None
        out.append(OrderedDict([
            ("group_type", name_key),
            (name_key, name),
            ("symbol_count", symbol_count),
            ("symbol_share", share),
            ("normalized_rows", normalized_rows),
            ("normalized_row_share", share if total_rows else None),
            ("concentration_contribution", contribution),
            ("relative_over_under_representation", relative),
            ("representation_label", "overrepresented" if (relative or 0.0) > 0.05 else "underrepresented" if (relative or 0.0) < -0.05 else "balanced"),
            ("stability_label", stability),
            ("differentiation_score", score),
            ("confidence", _confidence(symbol_count, stability)),
        ]))
    out.sort(key=lambda r: (-(r["differentiation_score"] or 0.0), r[name_key]))
    return out


def _chunk_rows(row: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    count = int(row.get("chunk_count") or 0)
    density_range = row.get("chunk_density_range", {}) or {}
    if count <= 0:
        return [OrderedDict([("status", "insufficient_signal"), ("reason", "No chunk baseline available in source artifact.")])]
    share = round(1.0 / count, 6)
    rows = []
    for idx in range(1, count + 1):
        rows.append(OrderedDict([
            ("chunk", idx),
            ("symbol_count", None),
            ("symbol_share", None),
            ("normalized_row_share", share),
            ("concentration_contribution", round(share * share, 6)),
            ("relative_over_under_representation", 0.0 if density_range.get("min") == density_range.get("max") else None),
            ("stability_label", "balanced_density_stable" if density_range.get("min") == density_range.get("max") else "insufficient_signal"),
            ("differentiation_score", 0.0 if density_range.get("min") == density_range.get("max") else None),
            ("confidence", "medium" if density_range.get("min") == density_range.get("max") else "insufficient_signal"),
        ]))
    return rows


def _watchlists(row: Mapping[str, Any]) -> OrderedDict[str, Any]:
    weak = row.get("weak_symbols", []) or []
    provider = row.get("provider_degradation", {}) or {}
    endpoint_failures = provider.get("endpoint_failures", {}) or {}
    failure_reasons = provider.get("top_failure_reasons", []) or []
    return OrderedDict([
        ("weak_symbols", weak),
        ("weak_symbol_count", len(weak)),
        ("provider_endpoint_failures", endpoint_failures),
        ("provider_failure_reasons", failure_reasons),
        ("confidence", "high" if not weak and not endpoint_failures and not failure_reasons else "medium"),
        ("assessment", "No weak/provider watchlist differentiation present in 120d source." if not weak and not endpoint_failures and not failure_reasons else "Provider or weak-symbol watchlists require observation only."),
    ])


def _foxa(hist_long4: Mapping[str, Any], hist_long5b: Mapping[str, Any]) -> OrderedDict[str, Any]:
    windows = hist_long4.get("window_level_results", []) or []
    present = [_window_id(row) for row in windows if row.get("foxa_present") is True]
    weak = [_window_id(row) for row in windows if row.get("foxa_weak") is True or "FOXA" in {str(s).upper() for s in row.get("weak_symbols", []) or []}]
    source_foxa = hist_long5b.get("foxa_longitudinal_assessment", {}) or {}
    return OrderedDict([
        ("present_all_windows", sorted(present) == REQUIRED_WINDOWS),
        ("weak_window_count", len(weak)),
        ("weak_windows", sorted(w for w in weak if w is not None)),
        ("stability_status", "stable_not_weak" if sorted(present) == REQUIRED_WINDOWS and not weak else "observation_required"),
        ("symbol_level_signal", "insufficient_signal" if source_foxa.get("insufficient_granular_signal") is True else "available"),
        ("assessment", "FOXA is present across all windows and not weak; source lacks granular symbol contribution signal." if source_foxa.get("insufficient_granular_signal") is True else "FOXA symbol-level signal available in source."),
    ])


def _fragility(row: Mapping[str, Any], hist_long5b: Mapping[str, Any]) -> OrderedDict[str, Any]:
    weak = bool(row.get("weak_symbols") or [])
    provider = row.get("provider_degradation", {}) or {}
    source_fragility = hist_long5b.get("fragility_emergence_detection", {}) or {}
    has_provider = bool((provider.get("endpoint_failures", {}) or {}) or (provider.get("top_failure_reasons", []) or []))
    appears = weak or has_provider or source_fragility.get("classification") not in (None, ["no_fragility_detected"])
    return OrderedDict([
        ("cross_sectional_fragility_appears", bool(appears)),
        ("source_longitudinal_classification", source_fragility.get("classification", ["no_fragility_detected"])),
        ("assessment", "No cross-sectional fragility appears inside the stable 120d baseline." if not appears else "Observation-only fragility signal present; no symbol-level fragility is invented."),
    ])


def _findings(sectors: Sequence[Mapping[str, Any]], subsectors: Sequence[Mapping[str, Any]], chunks: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    def take(rows: Sequence[Mapping[str, Any]], label: str | None = None, limit: int = 5) -> list[Mapping[str, Any]]:
        filtered = [row for row in rows if label is None or row.get("representation_label") == label]
        return list(filtered[:limit])
    hidden = [row for row in list(sectors) + list(subsectors) if (row.get("concentration_contribution") or 0) >= 0.08]
    hidden.sort(key=lambda r: (-(r.get("concentration_contribution") or 0), str(r.get("sector", r.get("subsector", "")))))
    return OrderedDict([
        ("strongest_differentiated_sectors", take(sectors)),
        ("strongest_differentiated_subsectors", take(subsectors)),
        ("balanced_groups", take(sectors, "balanced") + take(subsectors, "balanced")),
        ("overrepresented_groups", take(sectors, "overrepresented") + take(subsectors, "overrepresented")),
        ("underrepresented_groups", take(sectors, "underrepresented") + take(subsectors, "underrepresented")),
        ("hidden_concentration_pockets", hidden[:8]),
        ("stable_but_distinct_ecology_groups", [row for row in list(sectors) + list(subsectors) if row.get("stability_label") == "stable_distinct"][:10]),
        ("groups_needing_deeper_observation", [row for row in list(sectors) + list(subsectors) if row.get("confidence") in {"medium", "low", "insufficient_signal"}][:10]),
        ("chunk_balance_summary", chunks),
    ])


def build_blocked_artifact(reason: str, verification: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("schema_version", HIST_LONG6_SCHEMA_VERSION),
        ("status", "blocked"),
        ("review_date", date.today().isoformat()),
        ("source_verification", verification or OrderedDict([("verified", False), ("reason", reason)])),
        ("primary_baseline_window", PRIMARY_BASELINE_WINDOW),
        ("governance_certification", _governance()),
        ("recommendation_for_hist_long7", "Blocked: verify HIST-LONG-4 and HIST-LONG-5B before intra-group structural contrast."),
    ])


def build_hist_long6(hist_long4: Mapping[str, Any], hist_long5b: Mapping[str, Any], *, hist_long4_path: str = DEFAULT_HIST_LONG4_SOURCE_PATH, hist_long5b_path: str = DEFAULT_HIST_LONG5B_SOURCE_PATH) -> OrderedDict[str, Any]:
    verification = verify_sources(hist_long4, hist_long5b, hist_long4_path=hist_long4_path, hist_long5b_path=hist_long5b_path)
    if not verification["verified"]:
        return build_blocked_artifact(str(verification["reason"]), verification)
    primary = _primary_window(hist_long4)
    if primary is None:
        return build_blocked_artifact("120d primary baseline window missing", verification)
    sectors = _differentiation_rows(hist_long4, primary, "sector_hhi", "sector")
    subsectors = _differentiation_rows(hist_long4, primary, "subsector_hhi", "subsector")
    chunks = _chunk_rows(primary)
    return OrderedDict([
        ("schema_version", HIST_LONG6_SCHEMA_VERSION),
        ("status", "ok"),
        ("review_date", date.today().isoformat()),
        ("source_artifacts", [hist_long4_path, hist_long5b_path]),
        ("source_verification", verification),
        ("primary_baseline_window", PRIMARY_BASELINE_WINDOW),
        ("baseline_summary", OrderedDict([
            ("effective_symbol_count", primary.get("effective_symbol_count")),
            ("normalized_rows", primary.get("normalized_rows")),
            ("partial_count", primary.get("partial_count")),
            ("failed_count", primary.get("failed_count")),
            ("sector_hhi", (primary.get("sector_hhi", {}) or {}).get("universe_hhi")),
            ("subsector_hhi", (primary.get("subsector_hhi", {}) or {}).get("universe_hhi")),
        ])),
        ("cross_sectional_differentiation", OrderedDict([
            ("sector", sectors),
            ("subsector", subsectors),
            ("chunk", chunks),
            ("weak_provider_watchlists", _watchlists(primary)),
        ])),
        ("findings", _findings(sectors, subsectors, chunks)),
        ("foxa_assessment", _foxa(hist_long4, hist_long5b)),
        ("fragility_assessment", _fragility(primary, hist_long5b)),
        ("governance_certification", _governance()),
        ("recommendation_for_hist_long7", "Proceed with an analysis-only intra-group structural contrast / sector-subsector morphology decomposition phase; keep provider calls, replay activation, topology persistence, Supabase writes, raw-cache writes, prediction, and trading disabled."),
    ])


def _rows_table(rows: Sequence[Mapping[str, Any]], name_key: str) -> list[str]:
    lines = [f"| {name_key} | symbols | share | row share | concentration contribution | relative representation | stability | score | confidence |", "|---|---:|---:|---:|---:|---:|---|---:|---|"]
    for row in rows:
        lines.append(f"| {row.get(name_key)} | {row.get('symbol_count')} | {row.get('symbol_share')} | {row.get('normalized_row_share')} | {row.get('concentration_contribution')} | {row.get('relative_over_under_representation')} | {row.get('stability_label')} | {row.get('differentiation_score')} | {row.get('confidence')} |")
    return lines


def render_markdown(artifact: Mapping[str, Any]) -> str:
    lines = [
        "# HIST-LONG-6 Cross-Sectional Ecology Differentiation",
        "",
        "## Executive Summary",
        f"- Status: {artifact.get('status')}",
        f"- Primary baseline window: {artifact.get('primary_baseline_window')}d",
        f"- Recommendation: {artifact.get('recommendation_for_hist_long7')}",
        "",
        "## Source Verification",
        f"- Verified: {(artifact.get('source_verification', {}) or {}).get('verified')}",
        f"- Checks: `{json.dumps((artifact.get('source_verification', {}) or {}).get('preflight_checks', {}), sort_keys=True)}`",
    ]
    if artifact.get("status") != "ok":
        lines.append(f"- Blocked reason: {(artifact.get('source_verification', {}) or {}).get('reason')}")
        return "\n".join(lines) + "\n"
    diff = artifact.get("cross_sectional_differentiation", {}) or {}
    lines.extend(["", "## 120d Baseline Summary", f"- `{json.dumps(artifact.get('baseline_summary', {}), sort_keys=True)}`", "", "## Sector Differentiation"])
    lines.extend(_rows_table(diff.get("sector", []) or [], "sector"))
    lines.extend(["", "## Subsector Differentiation"])
    lines.extend(_rows_table(diff.get("subsector", []) or [], "subsector"))
    lines.extend(["", "## Chunk Differentiation", f"- `{json.dumps(diff.get('chunk', []), sort_keys=True)}`", "", "## Weak/Provider Watchlists", f"- `{json.dumps(diff.get('weak_provider_watchlists', {}), sort_keys=True)}`", "", "## Findings", f"- `{json.dumps(artifact.get('findings', {}), sort_keys=True)}`", "", "## FOXA Assessment", f"- `{json.dumps(artifact.get('foxa_assessment', {}), sort_keys=True)}`", "", "## Fragility Assessment", f"- `{json.dumps(artifact.get('fragility_assessment', {}), sort_keys=True)}`", "", "## Governance Certification"])
    for key, value in (artifact.get("governance_certification", {}) or {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def write_hist_long6(*, hist_long4_source_path: str = DEFAULT_HIST_LONG4_SOURCE_PATH, hist_long5b_source_path: str = DEFAULT_HIST_LONG5B_SOURCE_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH, report_path: str = DEFAULT_REPORT_PATH) -> OrderedDict[str, Any]:
    try:
        hist_long4 = _load_json(hist_long4_source_path)
    except FileNotFoundError:
        hist_long4 = None
    try:
        hist_long5b = _load_json(hist_long5b_source_path)
    except FileNotFoundError:
        hist_long5b = None
    if hist_long4 is None or hist_long5b is None:
        verification = verify_sources(hist_long4, hist_long5b, hist_long4_path=hist_long4_source_path, hist_long5b_path=hist_long5b_source_path)
        artifact = build_blocked_artifact(str(verification["reason"]), verification)
    else:
        artifact = build_hist_long6(hist_long4, hist_long5b, hist_long4_path=hist_long4_source_path, hist_long5b_path=hist_long5b_source_path)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_markdown(artifact), encoding="utf-8")
    return artifact
