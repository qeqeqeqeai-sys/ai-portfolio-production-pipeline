# HIST-FACT-2 — Historical Regime Evidence Expansion

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
- source_fact_count: 266
- eligible_source_fact_count: 110
- expanded_fact_count: 23
- net_new_fact_count: 23
- transition_relevant_fact_count: 23
- multi_window_fact_count: 22
- bounded_output: true

## Fact Type Distribution
- concentration_inflection_fact: 18
- participation_shift_fact: 1
- replay_inflection_fact: 2
- topology_inflection_fact: 1
- transition_rejection_fact: 1

## Confidence Distribution
- HIGH: 22
- LOW: 1

## Boundary Statement
HIST-FACT-2 is a deterministic local fact-generation layer. It emits evidence facts only and does not call providers, write Supabase, ingest live data, predict, trade, recommend portfolios, or activate governed workflows.
