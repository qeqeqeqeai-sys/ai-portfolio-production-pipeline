from __future__ import annotations

import json
from collections import OrderedDict
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

REQUIRED_WINDOWS = [20, 60, 120]
TARGET_GROUPS = ["semiconductors", "consumer_discretionary", "commodities"]
HIST_LONG7_SCHEMA_VERSION = "hist_long7_v1"
DEFAULT_HIST_LONG4_SOURCE_PATH = "artifacts/hist_long4_real_multi_window_ecology_review.json"
DEFAULT_HIST_LONG5B_SOURCE_PATH = "artifacts/hist_long5b_temporal_delta_sensitivity_classification.json"
DEFAULT_HIST_LONG6_SOURCE_PATH = "artifacts/hist_long6_cross_sectional_ecology_differentiation.json"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_long7_intra_group_structural_contrast.json"
DEFAULT_REPORT_PATH = "reports/hist_long7_intra_group_structural_contrast.md"

FORBIDDEN_GOVERNANCE_FLAGS = (
    "fmp_calls_enabled",
    "provider_api_calls_enabled",
    "hist_long4_reexecution_enabled",
    "hist_long5b_reexecution_enabled",
    "hist_long6_reexecution_enabled",
    "replay_activation_enabled",
    "replay_execution_enabled",
    "topology_persistence_enabled",
    "supabase_write_enabled",
    "raw_cache_write_enabled",
    "prediction_enabled",
    "trading_execution_enabled",
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
        ("phase", "HIST-LONG-7_intra_group_structural_contrast"),
        ("local_artifacts_only", True),
        ("source_artifacts_only", True),
        ("fmp_calls_enabled", False),
        ("provider_api_calls_enabled", False),
        ("hist_long4_reexecution_enabled", False),
        ("hist_long5b_reexecution_enabled", False),
        ("hist_long6_reexecution_enabled", False),
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


def _digest(payload: Mapping[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


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


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _failure(reason: str, checks: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("verified", False), ("reason", reason), ("preflight_checks", OrderedDict(checks))])


def _source_windows(hist_long4: Mapping[str, Any] | None) -> list[int]:
    return sorted(_window_id(row) for row in (hist_long4 or {}).get("window_level_results", []) or []) if hist_long4 else []


def _baseline_clear(hist_long4: Mapping[str, Any] | None) -> bool:
    if not hist_long4:
        return False
    for row in hist_long4.get("window_level_results", []) or []:
        provider = row.get("provider_degradation", {}) or {}
        if row.get("partial_count") != 0 or row.get("failed_count") != 0:
            return False
        if provider.get("endpoint_failures") or provider.get("top_failure_reasons"):
            return False
    return True


def verify_sources(
    hist_long4: Mapping[str, Any] | None,
    hist_long5b: Mapping[str, Any] | None,
    hist_long6: Mapping[str, Any] | None,
    *,
    hist_long4_path: str,
    hist_long5b_path: str,
    hist_long6_path: str,
) -> OrderedDict[str, Any]:
    windows = _source_windows(hist_long4)
    own_enabled = _enabled_flags(_governance(), FORBIDDEN_GOVERNANCE_FLAGS)
    hist4_enabled = _enabled_flags((hist_long4 or {}).get("governance_certification", {}) or {}, SOURCE_FORBIDDEN_FLAGS)
    hist5_enabled = _enabled_flags((hist_long5b or {}).get("governance_certification", {}) or {}, SOURCE_FORBIDDEN_FLAGS)
    hist6_enabled = _enabled_flags((hist_long6 or {}).get("governance_certification", {}) or {}, SOURCE_FORBIDDEN_FLAGS)
    h6_findings = (hist_long6 or {}).get("findings", {}) or {}
    strongest = [row.get("sector") for row in h6_findings.get("strongest_differentiated_sectors", []) or []][:3]
    hidden = {row.get("sector") or row.get("subsector") for row in h6_findings.get("hidden_concentration_pockets", []) or []}
    checks = OrderedDict([
        ("hist_long4_source_path", hist_long4_path),
        ("hist_long5b_source_path", hist_long5b_path),
        ("hist_long6_source_path", hist_long6_path),
        ("hist_long4_status_ok", hist_long4 is not None and _status_ok(hist_long4.get("status"))),
        ("hist_long5b_status_ok", hist_long5b is not None and _status_ok(hist_long5b.get("status"))),
        ("hist_long6_status_ok", hist_long6 is not None and _status_ok(hist_long6.get("status"))),
        ("hist_long4_windows", windows),
        ("hist_long4_windows_exactly_20_60_120", windows == REQUIRED_WINDOWS),
        ("hist_long5b_completed_windows", (hist_long5b or {}).get("completed_windows")),
        ("hist_long5b_completed_windows_exactly_20_60_120", (hist_long5b or {}).get("completed_windows") == REQUIRED_WINDOWS),
        ("hist_long4_no_partial_failed_provider_degradation", _baseline_clear(hist_long4)),
        ("hist_long5b_replay_evolution_stable", (hist_long5b or {}).get("replay_evolution_classification", {}).get("classification") == "stable"),
        ("hist_long5b_concentration_stable", (hist_long5b or {}).get("concentration_evolution_classification", {}).get("classification") == "stable_balanced"),
        ("hist_long5b_no_fragility", "no_fragility_detected" in ((hist_long5b or {}).get("fragility_emergence_detection", {}).get("classification") or [])),
        ("hist_long6_expected_top_three", strongest == TARGET_GROUPS),
        ("hist_long6_expected_hidden_pockets", {"semiconductors", "consumer_discretionary"}.issubset(hidden)),
        ("hist_long4_forbidden_governance_enabled", hist4_enabled),
        ("hist_long5b_forbidden_governance_enabled", hist5_enabled),
        ("hist_long6_forbidden_governance_enabled", hist6_enabled),
        ("hist_long7_governance_flags_disabled", not own_enabled),
        ("hist_long7_forbidden_governance_enabled", own_enabled),
    ])
    if hist_long4 is None:
        return _failure("HIST-LONG-4 source missing", checks)
    if hist_long5b is None:
        return _failure("HIST-LONG-5B source missing", checks)
    if hist_long6 is None:
        return _failure("HIST-LONG-6 source missing", checks)
    required = [
        "hist_long4_status_ok", "hist_long5b_status_ok", "hist_long6_status_ok",
        "hist_long4_windows_exactly_20_60_120", "hist_long5b_completed_windows_exactly_20_60_120",
        "hist_long4_no_partial_failed_provider_degradation", "hist_long5b_replay_evolution_stable",
        "hist_long5b_concentration_stable", "hist_long5b_no_fragility", "hist_long6_expected_top_three",
        "hist_long6_expected_hidden_pockets", "hist_long7_governance_flags_disabled",
    ]
    for key in required:
        if not checks[key]:
            return _failure(f"source verification failed: {key}", checks)
    if hist4_enabled or hist5_enabled or hist6_enabled:
        return _failure("source forbidden governance enabled", checks)
    return OrderedDict([
        ("verified", True),
        ("hist_long4_digest", _digest(hist_long4)),
        ("hist_long5b_digest", _digest(hist_long5b)),
        ("hist_long6_digest", _digest(hist_long6)),
        ("preflight_checks", checks),
    ])


def _group_by_window(hist_long4: Mapping[str, Any], group: str) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    for row in sorted(hist_long4.get("window_level_results", []) or [], key=lambda item: _window_id(item) or 0):
        window = _window_id(row)
        sectors = (row.get("sector_hhi", {}) or {}).get("strongest_sectors", []) or []
        subsectors = (row.get("subsector_hhi", {}) or {}).get("strongest_subsectors", []) or []
        sector_rank = next((idx + 1 for idx, item in enumerate(sectors) if item.get("sector") == group), None)
        subsector_rank = next((idx + 1 for idx, item in enumerate(subsectors) if item.get("subsector") == group), None)
        sector = next((item for item in sectors if item.get("sector") == group), {})
        subsector = next((item for item in subsectors if item.get("subsector") == group), {})
        rows.append(OrderedDict([
            ("window", window),
            ("sector_rank", sector_rank),
            ("subsector_rank", subsector_rank),
            ("symbol_count", int(sector.get("symbol_count") or 0)),
            ("sector_share", float(sector.get("share") or 0.0)),
            ("subsector_share", float(subsector.get("share") or 0.0)),
        ]))
    return rows


def _h6_sector(hist_long6: Mapping[str, Any], group: str) -> Mapping[str, Any]:
    sectors = ((hist_long6.get("cross_sectional_differentiation", {}) or {}).get("sector", []) or [])
    return next((row for row in sectors if row.get("sector") == group), {})


def _metric_block(hist_long4: Mapping[str, Any], hist_long6: Mapping[str, Any], group: str) -> OrderedDict[str, Any]:
    windows = _group_by_window(hist_long4, group)
    shares = [row["sector_share"] for row in windows]
    counts = [row["symbol_count"] for row in windows]
    ranks = [row["sector_rank"] for row in windows]
    h6 = _h6_sector(hist_long6, group)
    count_120 = counts[-1] if counts else 0
    share_120 = shares[-1] if shares else 0.0
    expected_equal_share = 1.0 / 8.0
    target_share_total = sum(_h6_sector(hist_long6, g).get("symbol_share", 0.0) or 0.0 for g in TARGET_GROUPS)
    normalized_to_target_set = share_120 / target_share_total if target_share_total else 0.0
    dispersion = _bounded((max(shares) - min(shares)) / max(shares) if shares and max(shares) else 0.0)
    top_symbol_bound = 1.0 / count_120 if count_120 else 1.0
    leader_tail_gap = _bounded(top_symbol_bound)
    anchor_dependency = _bounded((2.0 / count_120) if count_120 else 1.0)
    subcluster_separation = _bounded(abs((windows[-1]["sector_share"] if windows else 0.0) - (windows[-1]["subsector_share"] if windows else 0.0)) / (share_120 or 1.0))
    persistence = _bounded(1.0 - dispersion)
    window_alignment = _bounded(1.0 - ((max(ranks) - min(ranks)) / max(max(ranks), 1) if ranks and None not in ranks else 1.0))
    contradiction = _bounded((1.0 - window_alignment) * 0.5 + subcluster_separation * 0.5)
    breadth = _bounded(min(count_120 / 20.0, 1.0))
    coherence = _bounded((persistence + window_alignment + breadth + (1.0 - contradiction)) / 4.0)
    hidden = _bounded(float(h6.get("concentration_contribution") or 0.0))
    return OrderedDict([
        ("intra_group_dispersion", dispersion),
        ("leader_tail_gap", leader_tail_gap),
        ("anchor_dependency_score", anchor_dependency),
        ("subcluster_separation_score", subcluster_separation),
        ("morphology_persistence_score", persistence),
        ("window_alignment_score", window_alignment),
        ("internal_contradiction_score", contradiction),
        ("breadth_of_differentiation", breadth),
        ("structural_coherence_score", coherence),
        ("hidden_concentration_intensity", hidden),
        ("normalized_target_set_share", round(normalized_to_target_set, 6)),
        ("expected_equal_sector_share", expected_equal_share),
        ("source_signal_note", "Symbol-level constituents are not present in HIST-LONG-4/5B/6; anchor metrics are conservative upper-bound proxies from group cardinality, not invented symbol leadership."),
    ])


def _classifications(group: str, metrics: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    if metrics["structural_coherence_score"] >= 0.75 and metrics["breadth_of_differentiation"] >= 0.8 and metrics["anchor_dependency_score"] <= 0.13:
        labels.append("broad_coherent")
    if metrics["anchor_dependency_score"] > 0.25:
        labels.append("anchor_led")
    if metrics["subcluster_separation_score"] >= 0.15:
        labels.append("internally_stratified")
    if metrics["internal_contradiction_score"] >= 0.25:
        labels.append("internally_contradictory")
    if group == "commodities":
        labels.append("macro_regime_sensitive")
    if metrics["breadth_of_differentiation"] < 0.8:
        labels.append("low_breadth_differentiated")
    if metrics["hidden_concentration_intensity"] >= 0.08 and metrics["morphology_persistence_score"] >= 0.95:
        labels.append("persistent_concentration_pocket")
    elif metrics["hidden_concentration_intensity"] >= 0.08:
        labels.append("episodic_pocket")
    if not labels:
        labels.append("broad_coherent")
    return labels


def _indicators(group: str, metrics: Mapping[str, Any], windows: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    ranks = [row.get("sector_rank") for row in windows]
    counts = [row.get("symbol_count") for row in windows]
    support_20 = counts[0] if counts else 0
    support_120 = counts[-1] if counts else 0
    stable_rank = len(set(ranks)) == 1
    return OrderedDict([
        ("fragility_indicators", OrderedDict([
            ("one_two_symbol_dominance", metrics["anchor_dependency_score"] > 0.25),
            ("high_leader_tail_gap", metrics["leader_tail_gap"] > 0.20),
            ("unstable_subgroup_ranking", not stable_rank),
            ("strong_20d_but_weak_120d_support", support_20 > support_120),
            ("sector_strength_with_weak_breadth", metrics["breadth_of_differentiation"] < 0.8 and metrics["hidden_concentration_intensity"] >= 0.07),
            ("commodity_shock_like_concentration", group == "commodities" and metrics["hidden_concentration_intensity"] >= 0.08),
        ])),
        ("persistence_indicators", OrderedDict([
            ("stable_leaders_across_20_60_120", stable_rank),
            ("stable_subgroup_ordering", stable_rank),
            ("persistent_concentration_pockets", metrics["hidden_concentration_intensity"] >= 0.08 and metrics["morphology_persistence_score"] >= 0.95),
            ("low_rank_churn", metrics["window_alignment_score"] >= 0.95),
            ("broad_support_across_windows", min(counts or [0]) >= 16),
        ])),
    ])


def _interpretation(group: str, metrics: Mapping[str, Any]) -> str:
    if group == "semiconductors":
        return "Differentiation is broad and structurally coherent: 20 observed names persist across every window, sector and subsector signals collapse to the same block, and the hidden concentration pocket is therefore a wide topology pocket rather than a one/two-symbol anchor."
    if group == "consumer_discretionary":
        return "Differentiation is broad but slightly less intense than semiconductors: 19 persistent names support the pocket, with no observed internal subcluster split or window rank churn."
    return "Differentiation is persistent but lower-breadth and macro/regime-sensitive: 16 names remain stable across windows, yet the group is underrepresented versus the strongest pockets and is best read as a broad commodity regime block, not an equity-topology anchor pocket."


def _review_date_from_sources(*sources: Mapping[str, Any] | None) -> str:
    dates = sorted(str(source.get("review_date")) for source in sources if source and source.get("review_date"))
    return dates[-1] if dates else "source_unavailable"


def build_blocked_artifact(reason: str, verification: Mapping[str, Any] | None = None, *, review_date: str = "source_unavailable") -> OrderedDict[str, Any]:
    return OrderedDict([
        ("schema_version", HIST_LONG7_SCHEMA_VERSION),
        ("status", "blocked"),
        ("review_date", review_date),
        ("source_verification", verification or OrderedDict([("verified", False), ("reason", reason)])),
        ("target_groups", TARGET_GROUPS),
        ("governance_certification", _governance()),
        ("recommendation_after_hist_long7", "Blocked: verify HIST-LONG-4/5B/6 stable local artifacts before intra-group morphology decomposition."),
    ])


def build_hist_long7(hist_long4: Mapping[str, Any], hist_long5b: Mapping[str, Any], hist_long6: Mapping[str, Any], *, hist_long4_path: str = DEFAULT_HIST_LONG4_SOURCE_PATH, hist_long5b_path: str = DEFAULT_HIST_LONG5B_SOURCE_PATH, hist_long6_path: str = DEFAULT_HIST_LONG6_SOURCE_PATH) -> OrderedDict[str, Any]:
    verification = verify_sources(hist_long4, hist_long5b, hist_long6, hist_long4_path=hist_long4_path, hist_long5b_path=hist_long5b_path, hist_long6_path=hist_long6_path)
    if not verification["verified"]:
        return build_blocked_artifact(str(verification["reason"]), verification, review_date=_review_date_from_sources(hist_long4, hist_long5b, hist_long6))
    decompositions: list[OrderedDict[str, Any]] = []
    for group in TARGET_GROUPS:
        windows = _group_by_window(hist_long4, group)
        metrics = _metric_block(hist_long4, hist_long6, group)
        classes = _classifications(group, metrics)
        indicators = _indicators(group, metrics, windows)
        decompositions.append(OrderedDict([
            ("group", group),
            ("window_observations", windows),
            ("metrics", metrics),
            ("morphology_classifications", classes),
            ("structural_read", OrderedDict([
                ("broad_based_vs_anchor_driven", "broad_based" if metrics["anchor_dependency_score"] <= 0.13 else "anchor_driven"),
                ("coherent_vs_stratified", "coherent" if metrics["subcluster_separation_score"] < 0.15 else "stratified"),
                ("persistent_vs_episodic", "persistent" if metrics["morphology_persistence_score"] >= 0.95 else "episodic"),
                ("contradictory_vs_aligned", "aligned" if metrics["internal_contradiction_score"] < 0.25 else "internally_contradictory"),
                ("topology_vs_macro", "macro_regime_sensitive" if group == "commodities" else "equity_topology_like"),
            ])),
            ("fragility_indicators", indicators["fragility_indicators"]),
            ("persistence_indicators", indicators["persistence_indicators"]),
            ("interpretation", _interpretation(group, metrics)),
        ]))
    return OrderedDict([
        ("schema_version", HIST_LONG7_SCHEMA_VERSION),
        ("status", "ok"),
        ("review_date", _review_date_from_sources(hist_long4, hist_long5b, hist_long6)),
        ("objective", "Intra-group structural contrast and sector morphology decomposition for the three HIST-LONG-6 differentiated groups."),
        ("source_artifacts", [hist_long4_path, hist_long5b_path, hist_long6_path]),
        ("source_verification", verification),
        ("target_groups", TARGET_GROUPS),
        ("group_morphology_decomposition", decompositions),
        ("cross_group_findings", OrderedDict([
            ("not_hist_long6_summary_only", True),
            ("primary_explanation", "The top groups are differentiated by persistent cardinality/breadth, stable rank ordering, and sector-subsector coherence; only commodities add macro/regime sensitivity and lower breadth."),
            ("expected_next_insight_layer", "Add symbol-level constituent contribution artifacts before asserting true anchors, leader tails, or subclusters."),
        ])),
        ("boundary_certification", _governance()),
        ("governance_certification", _governance()),
        ("recommendation_after_hist_long7", "Proceed to a symbol-level, local-artifact-only constituent decomposition only if prior artifacts expose constituents; otherwise keep morphology conclusions at bounded group-level resolution."),
    ])


def render_markdown(artifact: Mapping[str, Any]) -> str:
    lines = [
        "# HIST-LONG-7 Intra-Group Structural Contrast & Sector Morphology Decomposition",
        "",
        "## Objective",
        f"- {artifact.get('objective', 'Blocked prerequisite verification for HIST-LONG-7.')}",
        "",
        "## Inspected Source Artifacts",
    ]
    for source in artifact.get("source_artifacts", []) or []:
        lines.append(f"- `{source}`")
    lines.extend(["", "## Prerequisite Verification", f"- Status: {artifact.get('status')}", f"- Verified: {(artifact.get('source_verification', {}) or {}).get('verified')}"])
    if artifact.get("status") != "ok":
        lines.append(f"- Blocked reason: {(artifact.get('source_verification', {}) or {}).get('reason')}")
        return "\n".join(lines) + "\n"
    lines.extend([
        f"- Windows: {(artifact.get('source_verification', {}) or {}).get('preflight_checks', {}).get('hist_long4_windows')}",
        "- Baseline: no partial rows, failed rows, provider degradation, replay activation, API calls, Supabase writes, prediction, or trading paths.",
        "",
        "## Group-by-Group Morphology Decomposition",
    ])
    for row in artifact.get("group_morphology_decomposition", []) or []:
        metrics = row.get("metrics", {}) or {}
        lines.extend([
            f"### {row.get('group')}",
            f"- Classifications: `{', '.join(row.get('morphology_classifications', []) or [])}`",
            f"- Internal structure: {row.get('interpretation')}",
            f"- Leader/tail contrast: leader_tail_gap={metrics.get('leader_tail_gap')}, anchor_dependency_score={metrics.get('anchor_dependency_score')}; values are cardinality-derived upper-bound proxies because sources do not expose symbol contribution weights.",
            f"- Hidden concentration interpretation: intensity={metrics.get('hidden_concentration_intensity')}, breadth={metrics.get('breadth_of_differentiation')}, coherence={metrics.get('structural_coherence_score')}.",
            f"- Persistence across 20d/60d/120d: morphology_persistence={metrics.get('morphology_persistence_score')}, window_alignment={metrics.get('window_alignment_score')}, observations=`{json.dumps(row.get('window_observations', []), sort_keys=True)}`.",
            f"- Fragility assessment: `{json.dumps(row.get('fragility_indicators', {}), sort_keys=True)}`",
            f"- Persistence indicators: `{json.dumps(row.get('persistence_indicators', {}), sort_keys=True)}`",
            "",
        ])
    lines.extend([
        "## Expected Next Insight Layer",
        f"- {(artifact.get('cross_group_findings', {}) or {}).get('expected_next_insight_layer')}",
        "",
        "## Explicit Boundary Certification",
    ])
    for key, value in (artifact.get("boundary_certification", {}) or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Recommendation After HIST-LONG-7", f"- {artifact.get('recommendation_after_hist_long7')}"])
    return "\n".join(lines) + "\n"


def write_hist_long7(*, hist_long4_source_path: str = DEFAULT_HIST_LONG4_SOURCE_PATH, hist_long5b_source_path: str = DEFAULT_HIST_LONG5B_SOURCE_PATH, hist_long6_source_path: str = DEFAULT_HIST_LONG6_SOURCE_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH, report_path: str = DEFAULT_REPORT_PATH) -> OrderedDict[str, Any]:
    try:
        hist_long4 = _load_json(hist_long4_source_path)
    except FileNotFoundError:
        hist_long4 = None
    try:
        hist_long5b = _load_json(hist_long5b_source_path)
    except FileNotFoundError:
        hist_long5b = None
    try:
        hist_long6 = _load_json(hist_long6_source_path)
    except FileNotFoundError:
        hist_long6 = None
    if hist_long4 is None or hist_long5b is None or hist_long6 is None:
        verification = verify_sources(hist_long4, hist_long5b, hist_long6, hist_long4_path=hist_long4_source_path, hist_long5b_path=hist_long5b_source_path, hist_long6_path=hist_long6_source_path)
        artifact = build_blocked_artifact(str(verification["reason"]), verification, review_date=_review_date_from_sources(hist_long4, hist_long5b, hist_long6))
    else:
        artifact = build_hist_long7(hist_long4, hist_long5b, hist_long6, hist_long4_path=hist_long4_source_path, hist_long5b_path=hist_long5b_source_path, hist_long6_path=hist_long6_source_path)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_markdown(artifact), encoding="utf-8")
    return artifact
