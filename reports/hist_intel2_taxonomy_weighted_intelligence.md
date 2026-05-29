# HIST-INTEL-2 Taxonomy-Weighted Intelligence Engine

## Objective
Prioritize ecosystem-significant facts over operational telemetry using deterministic fact taxonomy weights.

## Governance certification
- analysis_only: true
- local_only: true
- no_provider_calls: true
- no_supabase_writes: true
- no_prediction: true
- no_trading: true
- no_portfolio_recommendation: true
- no_governed_activation: true

## Taxonomy design
- tier_a: Ecosystem Intelligence weight=3.0 purpose=drives executive findings
- tier_b: Supporting Ecosystem Context weight=1.5 purpose=supports ecosystem sections below Tier A priority
- tier_c: Operational / Pipeline Telemetry weight=0.1 purpose=suppressed from executive findings when Tier A facts exist

## Executive Summary
- Ecosystem hub: group commodities scored 2.29275 with Tier A weight 3.0, 9 evidence units, 0 windows, and HIGH confidence.
- Ecosystem hub: group consumer_discretionary scored 2.28979 with Tier A weight 3.0, 9 evidence units, 0 windows, and HIGH confidence.
- Ecosystem hub: group semiconductors scored 2.289 with Tier A weight 3.0, 9 evidence units, 0 windows, and HIGH confidence.
- Structural anchor: group semiconductors scored 2.522308 with Tier A weight 3.0, 39 evidence units, 0 windows, and HIGH confidence.
- Structural anchor: group consumer_discretionary scored 2.521807 with Tier A weight 3.0, 39 evidence units, 0 windows, and HIGH confidence.
- Structural anchor: group commodities scored 2.480625 with Tier A weight 3.0, 36 evidence units, 0 windows, and HIGH confidence.
- Structural anchor: window window_120 scored 2.136 with Tier A weight 3.0, 2 evidence units, 1 windows, and MEDIUM confidence.
- Structural anchor: window window_20 scored 2.136 with Tier A weight 3.0, 2 evidence units, 1 windows, and MEDIUM confidence.
- Structural anchor: window window_60 scored 2.136 with Tier A weight 3.0, 2 evidence units, 1 windows, and MEDIUM confidence.
- Structural anchor: metric concentration_stability_drift scored 0.222 with Tier A weight 3.0, 1 evidence units, 0 windows, and LOW confidence.

## Highest-Ranked Ecosystem Hubs
- group commodities: hub_score=2.29275 tier=A weight=3.0 evidence_count=9 window_coverage=0 recurrence=2 confidence=HIGH
- group consumer_discretionary: hub_score=2.28979 tier=A weight=3.0 evidence_count=9 window_coverage=0 recurrence=2 confidence=HIGH
- group semiconductors: hub_score=2.289 tier=A weight=3.0 evidence_count=9 window_coverage=0 recurrence=2 confidence=HIGH

## Strongest Structural Anchors
- group semiconductors: anchor_score=2.522308 tier=A weight=3.0 evidence_count=39 window_coverage=0 recurrence=12 confidence=HIGH
- group consumer_discretionary: anchor_score=2.521807 tier=A weight=3.0 evidence_count=39 window_coverage=0 recurrence=12 confidence=HIGH
- group commodities: anchor_score=2.480625 tier=A weight=3.0 evidence_count=36 window_coverage=0 recurrence=11 confidence=HIGH
- window window_120: anchor_score=2.136 tier=A weight=3.0 evidence_count=2 window_coverage=1 recurrence=1 confidence=MEDIUM
- window window_20: anchor_score=2.136 tier=A weight=3.0 evidence_count=2 window_coverage=1 recurrence=1 confidence=MEDIUM
- window window_60: anchor_score=2.136 tier=A weight=3.0 evidence_count=2 window_coverage=1 recurrence=1 confidence=MEDIUM
- metric concentration_stability_drift: anchor_score=0.222 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW

## Replay Concentration Leaders
- window window_120: replay_score=2.136 tier=A weight=3.0 evidence_count=2 window_coverage=1 recurrence=1 confidence=MEDIUM
- window window_20: replay_score=2.136 tier=A weight=3.0 evidence_count=2 window_coverage=1 recurrence=1 confidence=MEDIUM
- window window_60: replay_score=2.136 tier=A weight=3.0 evidence_count=2 window_coverage=1 recurrence=1 confidence=MEDIUM
- metric replay_density: replay_score=1.956 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW
- metric replay_saturation: replay_score=1.956 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW

## Cross-Window Persistence Leaders
- group consumer_discretionary: persistence_score=2.874 tier=A weight=3.0 evidence_count=9 window_coverage=0 recurrence=2 confidence=HIGH
- group semiconductors: persistence_score=2.874 tier=A weight=3.0 evidence_count=9 window_coverage=0 recurrence=2 confidence=HIGH
- group commodities: persistence_score=2.574 tier=A weight=3.0 evidence_count=9 window_coverage=0 recurrence=2 confidence=HIGH
- metric replay_density: persistence_score=1.902 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW
- metric replay_saturation: persistence_score=1.902 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW

## Fragility Sources
- group commodities: fragility_score=1.53075 tier=A weight=3.0 evidence_count=15 window_coverage=0 recurrence=4 confidence=HIGH
- sector commodities: fragility_score=1.491982 tier=A weight=3.0 evidence_count=9 window_coverage=1 recurrence=2 confidence=HIGH
- group consumer_discretionary: fragility_score=1.471421 tier=A weight=3.0 evidence_count=12 window_coverage=0 recurrence=3 confidence=HIGH
- group semiconductors: fragility_score=1.46925 tier=A weight=3.0 evidence_count=12 window_coverage=0 recurrence=3 confidence=HIGH
- subsector commodities: fragility_score=1.293982 tier=A weight=3.0 evidence_count=6 window_coverage=1 recurrence=1 confidence=HIGH
- metric concentration_stability_drift: fragility_score=0.222 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW

## Drift / Morphology Change Leaders
- group commodities: drift_score=2.73 tier=A weight=3.0 evidence_count=6 window_coverage=0 recurrence=1 confidence=HIGH
- group consumer_discretionary: drift_score=2.73 tier=A weight=3.0 evidence_count=6 window_coverage=0 recurrence=1 confidence=HIGH
- group semiconductors: drift_score=2.73 tier=A weight=3.0 evidence_count=6 window_coverage=0 recurrence=1 confidence=HIGH
- metric concentration_stability_drift: drift_score=0.222 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW

## Topology Findings
- group semiconductors: topology_score=2.401845 tier=A weight=2.8125 evidence_count=48 window_coverage=0 recurrence=15 confidence=HIGH
- group consumer_discretionary: topology_score=2.398247 tier=A weight=2.8125 evidence_count=48 window_coverage=0 recurrence=15 confidence=HIGH
- group commodities: topology_score=2.335105 tier=A weight=2.8125 evidence_count=48 window_coverage=0 recurrence=15 confidence=HIGH
- window window_120: topology_score=2.01 tier=A weight=3.0 evidence_count=1 window_coverage=1 recurrence=0 confidence=LOW
- window window_20: topology_score=2.01 tier=A weight=3.0 evidence_count=1 window_coverage=1 recurrence=0 confidence=LOW
- window window_60: topology_score=2.01 tier=A weight=3.0 evidence_count=1 window_coverage=1 recurrence=0 confidence=LOW
- metric replay_density: topology_score=1.956 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW
- metric replay_saturation: topology_score=1.956 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW
- metric concentration_stability_drift: topology_score=0.222 tier=A weight=3.0 evidence_count=1 window_coverage=0 recurrence=0 confidence=LOW

## Suppressed Operational Diagnostics
- absolute_delta (replay_recurrence_fact/metric): suppressed_count=58 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- classification_code (persistence_fact/metric): suppressed_count=12 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- markdown_report_score (structural_instability_fact/metric): suppressed_count=8 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- markdown_report_score (topology_persistence_fact/metric): suppressed_count=7 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- absolute_delta (morphology_drift_fact/metric): suppressed_count=5 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- effective_symbol_count (breadth_expansion_fact/window): suppressed_count=3 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- failed_count (breadth_fragility_fact/window): suppressed_count=3 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- classification_code (structural_instability_fact/metric): suppressed_count=3 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- classification_code (replay_stability_fact/metric): suppressed_count=2 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist
- classification_code (sector_concentration_fact/metric): suppressed_count=2 weight=0.1 reason=Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist

## Limitations
- Analysis is deterministic, local-only, and bounded to supplied HIST-FACT-1/observation fact rows; it does not collect live data or activate governed workflows.
- Taxonomy weights prioritize Tier A ecosystem intelligence over Tier B support context and suppress Tier C operational telemetry from executive intelligence whenever Tier A facts exist.
- Tier C operational diagnostics were detected and reported only in the suppressed diagnostics section.
