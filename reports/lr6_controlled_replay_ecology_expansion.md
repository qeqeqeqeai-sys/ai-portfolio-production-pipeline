# Phase LR6 — Controlled Replay Ecology Expansion

## LR5 saturation findings review
LR5 used novelty-weighted bounded selection with saturation penalty and anti-monoculture guard. LR6 confirms these constraints should remain active.

## replay ecology analysis
- diagnostics: `{
  "replay_family_diversity_score": 1.0,
  "semantic_breadth_score": 2.0,
  "contradiction_family_distribution_score": 1.0,
  "regime_transition_diversity_score": 1.0,
  "continuity_transition_richness_score": 1.0,
  "replay_ecological_saturation_indicator": 0.25,
  "replay_monoculture_detected": false,
  "replay_redundancy_density_detected": false,
  "structural_contrast_score": 0.85,
  "marginal_novelty_contribution_estimate": 0.808333,
  "status": "success"
}`
- selected planning batch: `[
  {
    "candidate_id": "LR6-C2",
    "semantic_family": "regime_diversifier",
    "contradiction_novelty": 0.62,
    "continuity_transition_novelty": 0.75,
    "semantic_theme_novelty": 0.9,
    "regime_transition_novelty": 0.91,
    "structural_info_gain": 0.82,
    "saturation_risk": 0.24
  },
  {
    "candidate_id": "LR6-C3",
    "semantic_family": "contradiction_resolver",
    "contradiction_novelty": 0.88,
    "continuity_transition_novelty": 0.69,
    "semantic_theme_novelty": 0.83,
    "regime_transition_novelty": 0.77,
    "structural_info_gain": 0.79,
    "saturation_risk": 0.36
  }
]`

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
All outputs are deterministic from static inputs with stable checksum lineage: `3272a24449c8a2b6fd00b82b0efd2669a0992716ef761851288937e24c55a4f5`.

## expected longitudinal intelligence benefits
Higher replay ecology richness should improve transition recurrence observability and reduce replay-density-without-richness.

## risks of replay over-expansion
Over-expansion can increase redundancy density, monoculture concentration, and diminishing novelty yield.

## recommendation on whether another small replay wave is justified
Yes, only a small bounded wave is justified, and only after explicit governance approval under unchanged D8.B4/D21 gates.
