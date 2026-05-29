# HIST-LONG-7 Intra-Group Structural Contrast & Sector Morphology Decomposition

## Objective
- Intra-group structural contrast and sector morphology decomposition for the three HIST-LONG-6 differentiated groups.

## Inspected Source Artifacts
- `artifacts/hist_long4_real_multi_window_ecology_review.json`
- `artifacts/hist_long5b_temporal_delta_sensitivity_classification.json`
- `artifacts/hist_long6_cross_sectional_ecology_differentiation.json`

## Prerequisite Verification
- Status: ok
- Verified: True
- Windows: [20, 60, 120]
- Baseline: no partial rows, failed rows, provider degradation, replay activation, API calls, Supabase writes, prediction, or trading paths.

## Group-by-Group Morphology Decomposition
### semiconductors
- Classifications: `broad_coherent, persistent_concentration_pocket`
- Internal structure: Differentiation is broad and structurally coherent: 20 observed names persist across every window, sector and subsector signals collapse to the same block, and the hidden concentration pocket is therefore a wide topology pocket rather than a one/two-symbol anchor.
- Leader/tail contrast: leader_tail_gap=0.05, anchor_dependency_score=0.1; values are cardinality-derived upper-bound proxies because sources do not expose symbol contribution weights.
- Hidden concentration interpretation: intensity=0.112772, breadth=1.0, coherence=1.0.
- Persistence across 20d/60d/120d: morphology_persistence=1.0, window_alignment=1.0, observations=`[{"sector_rank": 1, "sector_share": 0.082988, "subsector_rank": 1, "subsector_share": 0.082988, "symbol_count": 20, "window": 20}, {"sector_rank": 1, "sector_share": 0.082988, "subsector_rank": 1, "subsector_share": 0.082988, "symbol_count": 20, "window": 60}, {"sector_rank": 1, "sector_share": 0.082988, "subsector_rank": 1, "subsector_share": 0.082988, "symbol_count": 20, "window": 120}]`.
- Fragility assessment: `{"commodity_shock_like_concentration": false, "high_leader_tail_gap": false, "one_two_symbol_dominance": false, "sector_strength_with_weak_breadth": false, "strong_20d_but_weak_120d_support": false, "unstable_subgroup_ranking": false}`
- Persistence indicators: `{"broad_support_across_windows": true, "low_rank_churn": true, "persistent_concentration_pockets": true, "stable_leaders_across_20_60_120": true, "stable_subgroup_ordering": true}`

### consumer_discretionary
- Classifications: `broad_coherent, persistent_concentration_pocket`
- Internal structure: Differentiation is broad but slightly less intense than semiconductors: 19 persistent names support the pocket, with no observed internal subcluster split or window rank churn.
- Leader/tail contrast: leader_tail_gap=0.052632, anchor_dependency_score=0.105263; values are cardinality-derived upper-bound proxies because sources do not expose symbol contribution weights.
- Hidden concentration interpretation: intensity=0.101768, breadth=0.95, coherence=0.9875.
- Persistence across 20d/60d/120d: morphology_persistence=1.0, window_alignment=1.0, observations=`[{"sector_rank": 2, "sector_share": 0.078838, "subsector_rank": 2, "subsector_share": 0.078838, "symbol_count": 19, "window": 20}, {"sector_rank": 2, "sector_share": 0.078838, "subsector_rank": 2, "subsector_share": 0.078838, "symbol_count": 19, "window": 60}, {"sector_rank": 2, "sector_share": 0.078838, "subsector_rank": 2, "subsector_share": 0.078838, "symbol_count": 19, "window": 120}]`.
- Fragility assessment: `{"commodity_shock_like_concentration": false, "high_leader_tail_gap": false, "one_two_symbol_dominance": false, "sector_strength_with_weak_breadth": false, "strong_20d_but_weak_120d_support": false, "unstable_subgroup_ranking": false}`
- Persistence indicators: `{"broad_support_across_windows": true, "low_rank_churn": true, "persistent_concentration_pockets": true, "stable_leaders_across_20_60_120": true, "stable_subgroup_ordering": true}`

### commodities
- Classifications: `broad_coherent, macro_regime_sensitive`
- Internal structure: Differentiation is persistent but lower-breadth and macro/regime-sensitive: 16 names remain stable across windows, yet the group is underrepresented versus the strongest pockets and is best read as a broad commodity regime block, not an equity-topology anchor pocket.
- Leader/tail contrast: leader_tail_gap=0.0625, anchor_dependency_score=0.125; values are cardinality-derived upper-bound proxies because sources do not expose symbol contribution weights.
- Hidden concentration interpretation: intensity=0.072179, breadth=0.8, coherence=0.95.
- Persistence across 20d/60d/120d: morphology_persistence=1.0, window_alignment=1.0, observations=`[{"sector_rank": 8, "sector_share": 0.06639, "subsector_rank": 8, "subsector_share": 0.06639, "symbol_count": 16, "window": 20}, {"sector_rank": 8, "sector_share": 0.06639, "subsector_rank": 8, "subsector_share": 0.06639, "symbol_count": 16, "window": 60}, {"sector_rank": 8, "sector_share": 0.06639, "subsector_rank": 8, "subsector_share": 0.06639, "symbol_count": 16, "window": 120}]`.
- Fragility assessment: `{"commodity_shock_like_concentration": false, "high_leader_tail_gap": false, "one_two_symbol_dominance": false, "sector_strength_with_weak_breadth": false, "strong_20d_but_weak_120d_support": false, "unstable_subgroup_ranking": false}`
- Persistence indicators: `{"broad_support_across_windows": true, "low_rank_churn": true, "persistent_concentration_pockets": false, "stable_leaders_across_20_60_120": true, "stable_subgroup_ordering": true}`

## Expected Next Insight Layer
- Add symbol-level constituent contribution artifacts before asserting true anchors, leader tails, or subclusters.

## Explicit Boundary Certification
- governance_mode: observational_only
- phase: HIST-LONG-7_intra_group_structural_contrast
- local_artifacts_only: True
- source_artifacts_only: True
- fmp_calls_enabled: False
- provider_api_calls_enabled: False
- hist_long4_reexecution_enabled: False
- hist_long5b_reexecution_enabled: False
- hist_long6_reexecution_enabled: False
- replay_activation_enabled: False
- replay_execution_enabled: False
- topology_persistence_enabled: False
- supabase_write_enabled: False
- raw_cache_write_enabled: False
- prediction_enabled: False
- trading_execution_enabled: False
- analysis_only: True

## Recommendation After HIST-LONG-7
- Proceed to a symbol-level, local-artifact-only constituent decomposition only if prior artifacts expose constituents; otherwise keep morphology conclusions at bounded group-level resolution.
