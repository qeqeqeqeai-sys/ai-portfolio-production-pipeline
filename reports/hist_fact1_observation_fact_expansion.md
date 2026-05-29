# HIST-FACT-1 — Historical Observation Fact Expansion

## Governance Certification
- analysis_only: true
- local_only: true
- no_provider_calls: true
- no_supabase_writes: true
- no_prediction: true
- no_trading: true
- no_portfolio_recommendation: true
- no_governed_activation: true

## Metrics
- source_artifacts_loaded: 6
- source_artifacts_missing: 0
- original_fact_count: 0
- expanded_fact_count: 266
- net_new_fact_count: 266
- max_facts: 750
- bounded_output: true

## Fact Type Distribution
- breadth_expansion_fact: 3
- breadth_fragility_fact: 3
- concentration_fragility_fact: 3
- ecosystem_concentration_fact: 3
- entity_persistence_fact: 3
- morphology_drift_fact: 5
- participation_fact: 3
- persistence_fact: 12
- replay_density_fact: 3
- replay_recurrence_fact: 58
- replay_stability_fact: 5
- sector_concentration_fact: 51
- sector_fragility_fact: 3
- structural_anchor_fact: 3
- structural_instability_fact: 12
- subsector_concentration_fact: 44
- subsector_fragility_fact: 2
- topology_coherence_fact: 24
- topology_fragmentation_fact: 1
- topology_persistence_fact: 11
- topology_stability_fact: 14

## Entity Type Distribution
- group: 51
- metric: 102
- sector: 49
- subsector: 43
- window: 21

## Confidence Distribution
- HIGH: 116
- INSUFFICIENT: 9
- LOW: 78
- MEDIUM: 63

## Boundary Statement
HIST-FACT-1 is a deterministic fact-generation layer over existing local historical artifacts. It does not call providers, write Supabase, ingest live data, predict, trade, recommend portfolios, or activate governed workflows.
