# Stage 5 — Full Bounded 241-Symbol Historical Ecology Rollout Report

## Workflow inputs used
- trading_days=120
- max_symbols=241
- symbol_chunk_size=50
- raw_cache_enabled=False
- raw_cache_write_enabled=False
- cache_validation_mode=False
- cache_only_validation=False
- include_high_risk_symbols=False
- apply_sde2_replacements=True
- dry_run_config_only=False

## Runtime
- elapsed_seconds=0
## Effective symbol count
- effective_symbol_count=241
## Chunk execution summary
- chunk_count=5
- chunk_sizes=[50, 50, 50, 50, 41]
## Endpoint success/failure summary
- top_failure_reasons=[]
## Final usable row count
- estimated_symbol_date_rows=28920
## Reconciliation summary
- exact/reconciled/missing available per chunk in artifact JSON chunk telemetry
## Affected symbols/dates
- affected_symbol_count=0
- affected_date_count=0
## Telemetry sample interpretation
- missing_record_sample_count=0
- endpoint_failure_sample_count=0
## Cache posture
- raw_cache_enabled=False, raw_cache_write_enabled=False
## Governance confirmation
- governance={"governance_mode": "observational_only", "no_cognition_replay_topology_persistence": true, "no_prediction_or_trading_execution": true, "persistence": "local_artifacts_only", "raw_input_cache_persistence_controlled_separately": true, "replay_execution_enabled": false, "topology_activation_enabled": false}
## Overall operational stability assessment
- Deterministic bounded chunk execution completed under fail-closed guards.
## Conclusion
- SEFI historical ecology rollout is operationally stable when guard conditions remain satisfied.
