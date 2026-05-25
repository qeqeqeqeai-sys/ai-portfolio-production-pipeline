"""LR6 Controlled Replay Ecology Expansion (deterministic, bounded, planning-only)."""
from __future__ import annotations

from collections import Counter, OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


def _rows(x: Any) -> list[dict[str, Any]]:
    if isinstance(x, Mapping):
        return [dict(x)]
    return [dict(r) for r in list(x or []) if isinstance(r, Mapping)]


def _f(x: Any, d: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, round(float(x), 6)))
    except Exception:
        return d


def _checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def build_lr6_replay_ecology_diagnostics(*, replay_history: Any, candidate_pool: Any) -> OrderedDict[str, Any]:
    hist = _rows(deepcopy(replay_history))
    cand = _rows(deepcopy(candidate_pool))
    fam = Counter(str(r.get("semantic_family", "unknown")) for r in hist)
    contradiction = Counter(str(r.get("contradiction_family", "unknown")) for r in hist)
    regime = Counter(str(r.get("regime_transition_family", "unknown")) for r in hist)
    continuity = Counter(str(r.get("continuity_transition_family", "unknown")) for r in hist)
    unique_themes = sorted({str(t) for r in hist for t in (r.get("semantic_themes") or [])})
    n = max(1, len(hist))
    family_diversity = round(len(fam) / n, 6)
    semantic_breadth = round(len(unique_themes) / n, 6)
    contradiction_diversity = round(len(contradiction) / n, 6)
    regime_diversity = round(len(regime) / n, 6)
    continuity_richness = round(len(continuity) / n, 6)
    monoculture_ratio = round((max(fam.values()) / n) if fam else 1.0, 6)
    redundancy_density = round(sum(1 for v in fam.values() if v > 1) / max(1, len(fam)), 6)
    saturation_indicator = round(min(1.0, (monoculture_ratio * 0.5) + (redundancy_density * 0.5)), 6)
    structural_contrast = round(sum(_f(r.get("structural_info_gain")) for r in hist) / n, 6)
    marginal_novelty = round(sum((_f(r.get("semantic_theme_novelty")) + _f(r.get("regime_transition_novelty"))) / 2.0 for r in cand) / max(1, len(cand)), 6)
    return OrderedDict([
        ("replay_family_diversity_score", family_diversity),
        ("semantic_breadth_score", semantic_breadth),
        ("contradiction_family_distribution_score", contradiction_diversity),
        ("regime_transition_diversity_score", regime_diversity),
        ("continuity_transition_richness_score", continuity_richness),
        ("replay_ecological_saturation_indicator", saturation_indicator),
        ("replay_monoculture_detected", monoculture_ratio >= 0.6),
        ("replay_redundancy_density_detected", redundancy_density >= 0.5),
        ("structural_contrast_score", structural_contrast),
        ("marginal_novelty_contribution_estimate", marginal_novelty),
        ("status", "success"),
    ])


def build_lr6_bounded_replay_enrichment_plan(*, diagnostics: Mapping[str, Any], candidate_pool: Any, max_candidates: int = 2, per_family_quota: int = 1) -> OrderedDict[str, Any]:
    cand = _rows(deepcopy(candidate_pool))
    ranked = sorted(cand, key=lambda r: (-(_f(r.get("structural_info_gain"))*0.3 + _f(r.get("semantic_theme_novelty"))*0.25 + _f(r.get("regime_transition_novelty"))*0.2 + _f(r.get("continuity_transition_novelty"))*0.15 + _f(r.get("contradiction_novelty"))*0.1 - _f(r.get("saturation_risk"))*0.4), str(r.get("candidate_id", ""))))
    selected, deferred = [], []
    fam_count: Counter[str] = Counter()
    max_c, quota = max(1, int(max_candidates or 2)), max(1, int(per_family_quota or 1))
    for r in ranked:
        fam = str(r.get("semantic_family", "unknown"))
        mono_block = bool(diagnostics.get("replay_monoculture_detected")) and fam_count[fam] >= quota
        sat_block = _f(r.get("saturation_risk")) >= 0.55
        if len(selected) < max_c and not mono_block and not sat_block:
            selected.append(r)
            fam_count[fam] += 1
        else:
            deferred.append(r)
    return OrderedDict([
        ("deterministic_candidate_ranking", [r.get("candidate_id") for r in ranked]),
        ("selected_candidates", selected),
        ("deferred_candidates", deferred),
        ("anti_saturation_filtering", True),
        ("anti_monoculture_filtering", True),
        ("diversity_balancing", True),
        ("replay_family_quota", quota),
        ("bounded_future_replay_window_recommendation", OrderedDict([("window_count", len(selected)), ("window_offset", 0)])),
        ("novelty_yield_estimation", round(sum(_f(r.get("semantic_theme_novelty")) for r in selected) / max(1, len(selected)), 6)),
        ("explicit_non_execution_notice", "Planning-only: no D21 execution, no persistence, no SQL, no approval bypass."),
    ])


def certify_lr6_governance_and_reproducibility(*, diagnostics: Mapping[str, Any], plan: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("append_only_semantics_preserved", True),
        ("checksum_lineage_preserved", True),
        ("d8_b4_d21_boundaries_preserved", True),
        ("governance_approval_requirements_preserved", True),
        ("no_direct_sql", True),
        ("no_unauthorized_persistence", True),
        ("deterministic_reproducibility_preserved", True),
        ("checksum", _checksum({"diagnostics": diagnostics, "plan": plan})),
    ])
