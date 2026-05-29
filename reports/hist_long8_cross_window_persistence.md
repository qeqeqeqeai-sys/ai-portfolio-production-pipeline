# HIST-LONG-8 Cross-Window Persistence & Structural Stability Analysis
## Objective
Identify persistent, decaying, and structurally unstable ecosystem characteristics across the 20d, 60d, and 120d windows.
## Inspected Inputs
- artifacts/hist_long4_real_multi_window_ecology_review.json
## Cross-Window Comparison
- replay_density: score=1.0 class=STABLE values={'20': 1.0, '60': 1.0, '120': 1.0}
- replay_saturation: score=1.0 class=STABLE values={'20': 1.0, '60': 1.0, '120': 1.0}
- contradiction_burden: score=1.0 class=STABLE values={'20': 0.0, '60': 0.0, '120': 0.0}
- sector_hhi: score=1.0 class=STABLE values={'20': 0.06107, '60': 0.06107, '120': 0.06107}
- subsector_hhi: score=1.0 class=STABLE values={'20': 0.06107, '60': 0.06107, '120': 0.06107}
- effective_symbol_count: score=1.0 class=STABLE values={'20': 241.0, '60': 241.0, '120': 241.0}
## Persistence Analysis
- sector_morphology_persistence: score=1.0 class=STABLE
- subsector_morphology_persistence: score=1.0 class=STABLE
- weak_symbol_persistence: score=None class=INSUFFICIENT_DATA
- foxa_persistence: score=None class=INSUFFICIENT_DATA
## Stability Classifications
- Overall: INSUFFICIENT_DATA (score=1.0)
## Notable Recurring Structures
- sector_morphology_persistence: cloud_software_infrastructure, commodities, consumer_discretionary, energy_utilities, financials, healthcare_biotech, industrials_automation, semiconductors
- subsector_morphology_persistence: cloud_software_infrastructure, commodities, consumer_discretionary, energy_utilities, financials, healthcare_biotech, industrials_automation, semiconductors
## Weak-Symbol Persistence
- INSUFFICIENT_DATA recurring=none
## FOXA Persistence
- INSUFFICIENT_DATA values={'20': None, '60': None, '120': None}
## Confidence Assessment
- medium
## Governance Review
- fmp_calls_enabled: False
- provider_api_calls_enabled: False
- live_ingestion_enabled: False
- replay_execution_enabled: False
- prediction_enabled: False
- trading_execution_enabled: False
- topology_persistence_enabled: False
- schema_changes_enabled: False
- destructive_database_operations_enabled: False
## Limitations
- FOXA and weak-symbol persistence are INSUFFICIENT_DATA when source rows are absent.
- Analysis is observational and uses completed local/read-model outputs only.
## Next-Step Recommendation
- Use emitted sefi_observation_facts as the source of truth for downstream HIST-LONG phases.
