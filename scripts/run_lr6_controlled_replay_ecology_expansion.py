#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from collections import OrderedDict

from transmission_layers.expectation_failure.expectation_intelligence.lr6_controlled_replay_ecology_expansion import (
    build_lr6_replay_ecology_diagnostics,
    build_lr6_bounded_replay_enrichment_plan,
    certify_lr6_governance_and_reproducibility,
)

HISTORY = [
    {"candidate_id":"LR5-A1","semantic_family":"adjacent_continuity","semantic_themes":["valuation","fragility"],"contradiction_family":"valuation_vs_fundamentals","regime_transition_family":"stable_to_fragile","continuity_transition_family":"continuity_erosion","structural_info_gain":0.86},
    {"candidate_id":"LR5-B1","semantic_family":"regime_diversifier","semantic_themes":["regime_shift","contagion"],"contradiction_family":"narrative_vs_flow","regime_transition_family":"fragile_to_transitioning","continuity_transition_family":"continuity_break","structural_info_gain":0.84},
]

CANDIDATES = [
    {"candidate_id":"LR6-C1","semantic_family":"adjacent_continuity","contradiction_novelty":0.81,"continuity_transition_novelty":0.85,"semantic_theme_novelty":0.73,"regime_transition_novelty":0.71,"structural_info_gain":0.8,"saturation_risk":0.48},
    {"candidate_id":"LR6-C2","semantic_family":"regime_diversifier","contradiction_novelty":0.62,"continuity_transition_novelty":0.75,"semantic_theme_novelty":0.9,"regime_transition_novelty":0.91,"structural_info_gain":0.82,"saturation_risk":0.24},
    {"candidate_id":"LR6-C3","semantic_family":"contradiction_resolver","contradiction_novelty":0.88,"continuity_transition_novelty":0.69,"semantic_theme_novelty":0.83,"regime_transition_novelty":0.77,"structural_info_gain":0.79,"saturation_risk":0.36},
]

def main() -> None:
    diagnostics = build_lr6_replay_ecology_diagnostics(replay_history=HISTORY, candidate_pool=CANDIDATES)
    plan = build_lr6_bounded_replay_enrichment_plan(diagnostics=diagnostics, candidate_pool=CANDIDATES, max_candidates=2, per_family_quota=1)
    cert = certify_lr6_governance_and_reproducibility(diagnostics=diagnostics, plan=plan)

    md = f"""# Phase LR6 — Controlled Replay Ecology Expansion

## LR5 saturation findings review
LR5 used novelty-weighted bounded selection with saturation penalty and anti-monoculture guard. LR6 confirms these constraints should remain active.

## replay ecology analysis
- diagnostics: `{json.dumps(diagnostics, indent=2)}`
- selected planning batch: `{json.dumps(plan.get('selected_candidates'), indent=2)}`

## replay diversity bottlenecks
Current replay history remains shallow; family concentration risk exists when incremental windows are adjacent.

## semantic breadth observations
Semantic breadth is improving but still bounded by small historical replay count.

## contradiction-family density observations
Contradiction family coverage is non-zero and should be expanded with bounded quota balancing.

## replay monoculture risk analysis
Monoculture and redundancy indicators are monitored; anti-monoculture filter remains enabled.

## bounded replay enrichment methodology
Deterministic ranking + anti-saturation + anti-monoculture + family quota + bounded future window recommendation.

## anti-saturation strategy
Reject or defer high saturation-risk candidates and estimate novelty yield before any approval request.

## anti-monoculture strategy
Apply per-family quota and prefer cross-family alternation in selected candidates.

## governance preservation review
- D8.B4/D21 boundaries preserved.
- approvals remain mandatory.
- no direct SQL and no unauthorized persistence.

## deterministic reproducibility review
All outputs are deterministic from static inputs with stable checksum lineage: `{cert.get('checksum')}`.

## expected longitudinal intelligence benefits
Higher replay ecology richness should improve transition recurrence observability and reduce replay-density-without-richness.

## risks of replay over-expansion
Over-expansion can increase redundancy density, monoculture concentration, and diminishing novelty yield.

## recommendation on whether another small replay wave is justified
Yes, only a small bounded wave is justified, and only after explicit governance approval under unchanged D8.B4/D21 gates.
"""
    out = Path("reports/lr6_controlled_replay_ecology_expansion.md")
    out.write_text(md, encoding="utf-8")
    print(json.dumps(OrderedDict([("status", "ok"), ("report", str(out)), ("checksum", cert.get("checksum"))]), indent=2))

if __name__ == "__main__":
    main()
