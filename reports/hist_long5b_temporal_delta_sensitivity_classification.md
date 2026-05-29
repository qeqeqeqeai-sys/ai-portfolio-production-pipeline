# HIST-LONG-5B Temporal Delta & Sensitivity Classification

## Executive Summary
- Status: blocked
- Completed windows: []
- Recommendation: Blocked: HIST-LONG-6 should not proceed until HIST-LONG-4 source verification succeeds.

## Source Artifact Verification
- `{"reason": "source status is not completed/success", "source_path": "artifacts/hist_long4_real_multi_window_ecology_review.json", "verified": false}`

## Temporal Delta Tables

### ingestion_continuity
| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |
|---:|---:|---|---:|---:|---:|---:|---|---|

### replay_ecology
| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |
|---:|---:|---|---:|---:|---:|---:|---|---|

### concentration_diversity
| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |
|---:|---:|---|---:|---:|---:|---:|---|---|

### weak_symbol_provider_quality
| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |
|---:|---:|---|---:|---:|---:|---:|---|---|

## Sensitivity Ranking
| rank | metric | classification | total absolute change | max relative change | volatility score | stability score |
|---:|---|---|---:|---:|---:|---:|

## Structural Persistence Classification
- `{}`

## Replay Evolution Classification
- `{"classification": "insufficient_signal"}`

## Concentration Evolution Classification
- `{"classification": "insufficient_signal"}`

## FOXA Longitudinal Assessment
- `{"contribution_consistency": "insufficient granular signal", "insufficient_granular_signal": true, "present_all_windows": false, "stability_classification": "insufficient_signal", "supervisor_assessment": "Blocked before FOXA longitudinal assessment.", "weak_window_count": 0}`

## Fragility Emergence Detection
- `{"classification": ["no_fragility_detected"], "fragile_windows": [], "reasons_by_window": {}}`

## Governance Certification
- governance_mode: observational_only
- phase: HIST-LONG-5B_temporal_delta_sensitivity_classification
- source_artifact_only: True
- fmp_calls_enabled: False
- provider_api_calls_enabled: False
- hist_long4_reexecution_enabled: False
- prediction_enabled: False
- trading_execution_enabled: False
- replay_activation_enabled: False
- replay_execution_enabled: False
- topology_persistence_enabled: False
- supabase_write_enabled: False
- raw_cache_write_enabled: False
- local_artifacts_only: True

## Recommendation For HIST-LONG-6
- Blocked: HIST-LONG-6 should not proceed until HIST-LONG-4 source verification succeeds.
