# CLEAN-2 Dependency Verification

Generated: 2026-05-29T12:24:12.519081+00:00

## Scope and method
Analysis-only static verification. No runtime logic was changed, no files were archived/deleted/moved, and generated output/report directories were not used as dependency evidence beyond writing the requested deliverables.

## Workflow entrypoint inventory

Enumerated 52 `.github/workflows/*.yml` files. Extracted Python/shell invocations conservatively from run lines and script path references.

| Workflow | Triggers | Entrypoints |
|---|---|---|
| `.github/workflows/ai_transmission_evidence_pipeline.yml` | cron, schedule, workflow_dispatch | `ai_transmission/ai_transmission_evidence_ingestion_v1.py` (L87)<br>`scripts/write_observability_history.py` (L188) |
| `.github/workflows/ai_transmission_phase2a_pipeline_phase2d_revised.yml` | cron, schedule, workflow_dispatch | `ai_transmission/ai_transmission_evidence_ingestion_v1.py` (L43)<br>`ai_transmission/ai_transmission_scoring_v2_phase1_refactor_built.py` (L47)<br>`ai_transmission/phase2a_validation_telemetry.py` (L51)<br>`transmission_layers/ai_transmission/phase2b_explainability_layer.py` (L55)<br>`transmission_layers/ai_transmission/phase2b_explainability_layer.py` (L56)<br>`ai_transmission/phase2b_explainability_layer.py` (L58)<br>`transmission_layers/shared/structural_theme_historical_analytics_phase2d.py` (L66)<br>`transmission_layers/shared/structural_theme_historical_analytics_phase2d.py` (L67)<br>`ai_transmission/structural_theme_historical_analytics_phase2d.py` (L69)<br>`archive_production_reports.py` (L79)<br>`notify_archival_failure.py` (L88)<br>`scripts/write_observability_history.py` (L209) |
| `.github/workflows/ai_transmission_phase2d2_reconstruction.yml` | workflow_dispatch | `transmission_layers/ai_transmission/phase2d2_historical_reconstruction_engine_schema_aligned_revised.py` (L168)<br>`utils/paginated_rest_loader.py` (L170)<br>`utils/streaming_observation_loader.py` (L171)<br>`utils/rolling_reconstruction_aggregators.py` (L172)<br>`transmission_layers/ai_transmission/phase2d2_historical_reconstruction_engine_schema_aligned_revised.py` (L183)<br>`utils/paginated_rest_loader.py` (L185)<br>`utils/streaming_observation_loader.py` (L186)<br>`utils/rolling_reconstruction_aggregators.py` (L187)<br>`transmission_layers/ai_transmission/phase2d2_historical_reconstruction_engine_schema_aligned_revised.py` (L197)<br>`scripts/write_observability_history.py` (L278) |
| `.github/workflows/continuity_engine_pipeline.yml` | workflow_dispatch | `transmission_layers/graph_foundation/continuity/continuity_engine.py` (L34)<br>`scripts/write_observability_history.py` (L129) |
| `.github/workflows/d21_limited_governed_backfill.yml` | workflow_dispatch | `scripts/run_d21_limited_governed_backfill.py` (L131) |
| `.github/workflows/d8_b2_real_supabase_dry_run_retry.yml` | workflow_dispatch | `scripts/run_d8_b2_real_supabase_dry_run_retry.py` (L37) |
| `.github/workflows/d8_b2r_supabase_diagnostics.yml` | workflow_dispatch | `scripts/run_d8_b2r_real_supabase_diagnostics.py` (L42) |
| `.github/workflows/d8_b3_replay_persistence_audit.yml` | workflow_dispatch | None detected |
| `.github/workflows/d8_b4_governed_replay_persistence_execution.yml` | workflow_dispatch | None detected |
| `.github/workflows/daily_ai_portfolio_pipeline.yml` | cron, schedule, workflow_dispatch | `scripts/ai_signal_scoring_v7_alpha_model_efficiency_github_actions.py` (L133)<br>`scripts/ai_portfolio_engine_v7_alpha_score_github_actions.py` (L137)<br>`scripts/ai_portfolio_monitoring_v1_github_actions.py` (L141)<br>`scripts/run_production_validation_gates.py` (L282)<br>`scripts/write_pipeline_metrics.py` (L304)<br>`scripts/write_pipeline_failure_metrics.py` (L315)<br>`scripts/write_observability_history.py` (L444)<br>`scripts/archive_production_reports.py` (L451)<br>`scripts/notify_archival_failure.py` (L457) |
| `.github/workflows/hist_density1_90d_pilot.yml` | workflow_dispatch | `scripts/run_hist_density1_controlled_historical_density.py` (L50) |
| `.github/workflows/hist_density2_180d_pilot.yml` | workflow_dispatch | `scripts/run_hist_density_2_180d_pilot.py` (L105) |
| `.github/workflows/hist_density3_curated_241_pilot.yml` | workflow_dispatch | `scripts/run_hist_density_3_curated_241_pilot.py` (L101) |
| `.github/workflows/hist_long3_updated_universe_validation.yml` | workflow_dispatch | `scripts/run_hist_long3_updated_universe_validation.py` (L106) |
| `.github/workflows/hist_long4_real_multi_window_ecology.yml` | workflow_dispatch | `scripts/run_hist_long4_real_multi_window_ecology.py` (L85) |
| `.github/workflows/historical_source_backfill.yml` | workflow_dispatch | `transmission_layers/ai_transmission/historical_backfill/historical_ai_transmission_backfill.py` (L38)<br>`transmission_layers/ai_transmission/historical_backfill/historical_backfill_validation_gates.py` (L45)<br>`scripts/write_observability_history.py` (L139) |
| `.github/workflows/lr5_first_governed_replay_wave.yml` | workflow_dispatch | `scripts/run_d21_limited_governed_backfill.py` (L72)<br>`scripts/run_lr5_first_governed_replay_wave_review.py` (L74) |
| `.github/workflows/lr6_live5_first_approved_non_dry_persistence_execution.yml` | workflow_dispatch | `scripts/run_lr6_live5_first_approved_non_dry_persistence_execution.py` (L45) |
| `.github/workflows/multi_theme_graph_pass1.yml` | workflow_dispatch | `scripts/write_observability_history.py` (L150) |
| `.github/workflows/observability_coverage_lint.yml` | pull_request, workflow_dispatch | `scripts/lint_workflow_observability.py` (L8)<br>`scripts/validate_observability_artifacts.py` (L9)<br>`scripts/lint_workflow_observability.py` (L27)<br>`scripts/validate_observability_artifacts.py` (L32) |
| `.github/workflows/ops_live1b_daily_observation.yml` | cron, schedule, workflow_dispatch | `scripts/run_ops_live1b_50_symbol_operational_ingest.py` (L85)<br>`scripts/run_ops_live1b_snapshot_observation_review.py` (L94) |
| `.github/workflows/phase1_ai_transmission_dual_write.yml` | cron, schedule, workflow_dispatch | `ai_transmission/ai_transmission_scoring_v2_phase1_refactor_built.py` (L110)<br>`scripts/write_observability_history.py` (L179) |
| `.github/workflows/phase3a1_evidence_density_expansion.yml` | workflow_dispatch | `phase3a1_evidence_density_expansion.py` (L48)<br>`scripts/write_observability_history.py` (L166) |
| `.github/workflows/phase3a2_cross_theme_relationship_expansion.yml` | workflow_dispatch | `phase3a2_cross_theme_relationship_expansion.py` (L53)<br>`scripts/write_observability_history.py` (L171) |
| `.github/workflows/phase3a_evidence_graph_expansion.yml` | workflow_dispatch | `phase3a_evidence_graph_expansion.py` (L48)<br>`scripts/write_observability_history.py` (L167) |
| `.github/workflows/phase3b_relationship_persistence.yml` | workflow_dispatch | `phase3b_relationship_persistence.py` (L60)<br>`scripts/write_observability_history.py` (L180) |
| `.github/workflows/phase3c_regime_transition_structural_drift.yml` | workflow_dispatch | `phase3c_regime_transition_structural_drift.py` (L64)<br>`scripts/write_observability_history.py` (L158) |
| `.github/workflows/phase3d_structural_pressure_accumulation.yml` | workflow_dispatch | `phase3d_structural_pressure_accumulation.py` (L64)<br>`scripts/write_observability_history.py` (L164) |
| `.github/workflows/phase3e_transmission_potential_surface.yml` | workflow_dispatch | `phase3e_transmission_potential_surface.py` (L46)<br>`scripts/write_observability_history.py` (L142) |
| `.github/workflows/phase4a_controlled_single_hop_propagation.yml` | workflow_dispatch | `phase4a_controlled_single_hop_propagation.py` (L63)<br>`scripts/write_observability_history.py` (L158) |
| `.github/workflows/phase4b_propagation_memory_decay.yml` | workflow_dispatch | `phase4b_propagation_memory_decay.py` (L63)<br>`scripts/write_observability_history.py` (L157) |
| `.github/workflows/phase4d_daily_graph_evolution.yml` | cron, schedule, workflow_dispatch | `start_graph_evolution_run.py` (L77)<br>`write_graph_evolution_phase_event.py` (L85)<br>`phase3a1_evidence_density_expansion.py` (L86)<br>`write_graph_evolution_phase_event.py` (L87)<br>`write_graph_evolution_phase_event.py` (L98)<br>`phase3a_evidence_graph_expansion.py` (L99)<br>`write_graph_evolution_phase_event.py` (L100)<br>`write_graph_evolution_phase_event.py` (L111)<br>`phase3a2_cross_theme_relationship_expansion.py` (L112)<br>`write_graph_evolution_phase_event.py` (L113)<br>`write_graph_evolution_phase_event.py` (L124)<br>`phase3b_relationship_persistence.py` (L125)<br>`write_graph_evolution_phase_event.py` (L126)<br>`write_graph_evolution_phase_event.py` (L137)<br>`phase3c_regime_transition_structural_drift.py` (L138)<br>`write_graph_evolution_phase_event.py` (L139)<br>`write_graph_evolution_phase_event.py` (L150)<br>`phase3d_structural_pressure_accumulation.py` (L151)<br>`write_graph_evolution_phase_event.py` (L152)<br>`write_graph_evolution_phase_event.py` (L163)<br>`phase3e_transmission_potential_surface.py` (L164)<br>`write_graph_evolution_phase_event.py` (L165)<br>`write_graph_evolution_phase_event.py` (L176)<br>`phase4a_controlled_single_hop_propagation.py` (L177)<br>`write_graph_evolution_phase_event.py` (L178)<br>`write_graph_evolution_phase_event.py` (L189)<br>`phase4b_propagation_memory_decay.py` (L190)<br>`write_graph_evolution_phase_event.py` (L191)<br>`finish_graph_evolution_run.py` (L197)<br>`scripts/write_observability_history.py` (L275) |
| `.github/workflows/phase4e_historical_propagation_replay.yml` | workflow_dispatch | `phase4e_historical_propagation_replay.py` (L63)<br>`scripts/write_observability_history.py` (L131) |
| `.github/workflows/phase5a2_structural_intermediaries.yml` | cron, schedule, workflow_dispatch | `intermediary_detection_engine.py` (L55)<br>`scripts/write_observability_history.py` (L148) |
| `.github/workflows/phase5a3_directed_intermediary_seeding.yml` | workflow_dispatch | `directed_intermediary_seeding_engine.py` (L46)<br>`scripts/write_observability_history.py` (L135) |
| `.github/workflows/phase5a4_canonical_structural_ontology.yml` | workflow_dispatch | `canonical_structural_ontology_engine.py` (L40)<br>`scripts/write_observability_history.py` (L130) |
| `.github/workflows/phase5a_two_hop_pipeline.yml` | cron, schedule, workflow_dispatch | `transmission_layers/phase5a_two_hop/phase5a_two_hop_propagation.py` (L116)<br>`transmission_layers/phase5a_two_hop/phase5a_validate_two_hop.py` (L170)<br>`scripts/write_observability_history.py` (L267) |
| `.github/workflows/phase5b_propagation_corridor_pipeline.yml` | cron, schedule, workflow_dispatch | `transmission_layers/graph_foundation/phase5b_propagation_corridor_engine.py` (L71)<br>`scripts/write_observability_history.py` (L148) |
| `.github/workflows/phase5c_regime_corridor_dynamics_pipeline.yml` | cron, schedule, workflow_dispatch | `transmission_layers/graph_foundation/phase5c_regime_corridor_dynamics_engine.py` (L76)<br>`scripts/write_observability_history.py` (L147) |
| `.github/workflows/phase5d_structural_propagation_regime_forecasting_pipeline.yml` | cron, schedule, workflow_dispatch | `transmission_layers/graph_foundation/phase5d_structural_propagation_regime_forecasting_engine.py` (L68)<br>`scripts/write_observability_history.py` (L142) |
| `.github/workflows/run-d1-dashboard-seed.yml` | workflow_dispatch | `scripts/run_d1_dashboard_sample_seed.py` (L54) |
| `.github/workflows/run_d6_proving_cycle.yml` | workflow_dispatch | `scripts/run_d6_real_proving_cycle.py` (L35) |
| `.github/workflows/sefi_live_daily.yml` | cron, schedule, workflow_dispatch | `scripts/run_ops_live1b_50_symbol_operational_ingest.py` (L83)<br>`scripts/run_ops_live2_observation_fact_accumulation.py` (L162)<br>`scripts/run_ops_live3_structural_state_snapshot.py` (L176) |
| `.github/workflows/sefi_monthly_ecology_review.yml` | cron, schedule, workflow_dispatch | `scripts/run_hist_long4_real_multi_window_ecology.py` (L66)<br>`scripts/run_hist_long5b_temporal_delta_sensitivity_classification.py` (L79)<br>`scripts/run_hist_long6_cross_sectional_ecology_differentiation.py` (L89)<br>`scripts/run_hist_long7_intra_group_structural_contrast.py` (L99) |
| `.github/workflows/sefi_operational_health.yml` | cron, schedule, workflow_dispatch | None detected |
| `.github/workflows/sefi_universe_source_check.yml` | workflow_dispatch | `scripts/load_sefi_observation_universe.py` (L37)<br>`scripts/check_sefi_universe_source.py` (L41)<br>`scripts/validate_sefi_observation_universe.py` (L45) |
| `.github/workflows/sefi_weekly_observation_review.yml` | cron, schedule, workflow_dispatch | `scripts/run_hist_long8_cross_window_persistence.py` (L40)<br>`scripts/run_hist_long9_persistence_drift.py` (L47) |
| `.github/workflows/tier3h4_dynamic_entity_discovery.yml` | cron, schedule, workflow_dispatch | `transmission_layers/asset_discovery/tier3h4_dynamic_entity_discovery.py` (L53)<br>`transmission_layers/asset_discovery/entity_resolution/resolve_discovered_entities.py` (L62) |
| `.github/workflows/tier3h5_registry_foundations.yml` | push, workflow_dispatch | `transmission_layers/asset_discovery/tier3h4_dynamic_entity_discovery.py` (L8)<br>`transmission_layers/asset_discovery/tier3h5/registry_propagation_governance.py` (L34)<br>`transmission_layers/asset_discovery/tier3h5/registry_propagation_governance_cli.py` (L36)<br>`transmission_layers/asset_discovery/tier3h5/phase2a_coverage_telemetry.py` (L46)<br>`transmission_layers/asset_discovery/tier3h5/normalization_diagnostics.py` (L52)<br>`transmission_layers/asset_discovery/tier3h5/registry_quality_freshness_governance.py` (L61)<br>`transmission_layers/asset_discovery/tier3h5/registry_replay_governance.py` (L70)<br>`transmission_layers/asset_discovery/tier3h5/registry_snapshot_archive.py` (L79)<br>`transmission_layers/asset_discovery/tier3h5/registry_snapshot_time_travel.py` (L85)<br>`transmission_layers/asset_discovery/tier3h5/cross_registry_identity_governance.py` (L94)<br>`transmission_layers/asset_discovery/tier3h5/governance_operational_intelligence.py` (L103)<br>`transmission_layers/asset_discovery/tier3h5/canonical_graph_governance.py` (L110)<br>`transmission_layers/asset_discovery/tier3h5/canonical_graph_governance_cli.py` (L112)<br>`transmission_layers/asset_discovery/tier3h5/canonical_propagation_memory.py` (L119)<br>`transmission_layers/asset_discovery/tier3h5/canonical_propagation_memory_cli.py` (L121)<br>`transmission_layers/asset_discovery/tier3h5/governance_risk_intelligence.py` (L130)<br>`transmission_layers/asset_discovery/tier3h5/governance_history/artifacts.py` (L139)<br>`transmission_layers/asset_discovery/tier3h5/governance_bi/artifacts.py` (L148)<br>`transmission_layers/asset_discovery/tier3h5/governance_explainability_api.py` (L157) |
| `.github/workflows/tier3h_transmission_candidate_discovery.yml` | workflow_dispatch | `transmission_layers/asset_discovery/tier3h_transmission_candidate_discovery.py` (L30) |
| `.github/workflows/tier3i_transmission_intelligence_tests.yml` | pull_request, workflow_dispatch | None detected |
| `.github/workflows/tier4_structural_simulation.yml` | pull_request, push, workflow_dispatch | None detected |

## Protected active paths

Protected paths include every workflow file, every existing workflow-invoked script/shell entrypoint, recursively imported in-scope dependencies of those entrypoints, and active paths explicitly named in `docs/runbooks/workflow-registry.md`.
- `.github/workflows/ai_transmission_evidence_pipeline.yml`
- `.github/workflows/ai_transmission_phase2a_pipeline_phase2d_revised.yml`
- `.github/workflows/ai_transmission_phase2d2_reconstruction.yml`
- `.github/workflows/continuity_engine_pipeline.yml`
- `.github/workflows/d21_limited_governed_backfill.yml`
- `.github/workflows/d8_b2_real_supabase_dry_run_retry.yml`
- `.github/workflows/d8_b2r_supabase_diagnostics.yml`
- `.github/workflows/d8_b3_replay_persistence_audit.yml`
- `.github/workflows/d8_b4_governed_replay_persistence_execution.yml`
- `.github/workflows/daily_ai_portfolio_pipeline.yml`
- `.github/workflows/hist_density1_90d_pilot.yml`
- `.github/workflows/hist_density2_180d_pilot.yml`
- `.github/workflows/hist_density3_curated_241_pilot.yml`
- `.github/workflows/hist_long3_updated_universe_validation.yml`
- `.github/workflows/hist_long4_real_multi_window_ecology.yml`
- `.github/workflows/historical_source_backfill.yml`
- `.github/workflows/lr5_first_governed_replay_wave.yml`
- `.github/workflows/lr6_live5_first_approved_non_dry_persistence_execution.yml`
- `.github/workflows/multi_theme_graph_pass1.yml`
- `.github/workflows/observability_coverage_lint.yml`
- `.github/workflows/ops_live1b_daily_observation.yml`
- `.github/workflows/phase1_ai_transmission_dual_write.yml`
- `.github/workflows/phase3a1_evidence_density_expansion.yml`
- `.github/workflows/phase3a2_cross_theme_relationship_expansion.yml`
- `.github/workflows/phase3a_evidence_graph_expansion.yml`
- `.github/workflows/phase3b_relationship_persistence.yml`
- `.github/workflows/phase3c_regime_transition_structural_drift.yml`
- `.github/workflows/phase3d_structural_pressure_accumulation.yml`
- `.github/workflows/phase3e_transmission_potential_surface.yml`
- `.github/workflows/phase4a_controlled_single_hop_propagation.yml`
- `.github/workflows/phase4b_propagation_memory_decay.yml`
- `.github/workflows/phase4d_daily_graph_evolution.yml`
- `.github/workflows/phase4e_historical_propagation_replay.yml`
- `.github/workflows/phase5a2_structural_intermediaries.yml`
- `.github/workflows/phase5a3_directed_intermediary_seeding.yml`
- `.github/workflows/phase5a4_canonical_structural_ontology.yml`
- `.github/workflows/phase5a_two_hop_pipeline.yml`
- `.github/workflows/phase5b_propagation_corridor_pipeline.yml`
- `.github/workflows/phase5c_regime_corridor_dynamics_pipeline.yml`
- `.github/workflows/phase5d_structural_propagation_regime_forecasting_pipeline.yml`
- `.github/workflows/run-d1-dashboard-seed.yml`
- `.github/workflows/run_d6_proving_cycle.yml`
- `.github/workflows/sefi_live_daily.yml`
- `.github/workflows/sefi_monthly_ecology_review.yml`
- `.github/workflows/sefi_operational_health.yml`
- `.github/workflows/sefi_universe_source_check.yml`
- `.github/workflows/sefi_weekly_observation_review.yml`
- `.github/workflows/tier3h4_dynamic_entity_discovery.yml`
- `.github/workflows/tier3h5_registry_foundations.yml`
- `.github/workflows/tier3h_transmission_candidate_discovery.yml`
- `.github/workflows/tier3i_transmission_intelligence_tests.yml`
- `.github/workflows/tier4_structural_simulation.yml`
- `ai_transmission/ai_transmission_evidence_ingestion_v1.py`
- `ai_transmission/ai_transmission_scoring_v2_phase1_refactor_built.py`
- `ai_transmission/phase2a_validation_telemetry.py`
- `scripts/ai_portfolio_engine_v7_alpha_score_github_actions.py`
- `scripts/ai_portfolio_monitoring_v1_github_actions.py`
- `scripts/ai_signal_scoring_v7_alpha_model_efficiency_github_actions.py`
- `scripts/archive_production_reports.py`
- `scripts/check_sefi_universe_source.py`
- `scripts/lint_workflow_observability.py`
- `scripts/load_sefi_observation_universe.py`
- `scripts/notify_archival_failure.py`
- `scripts/run_d1_dashboard_sample_seed.py`
- `scripts/run_d21_limited_governed_backfill.py`
- `scripts/run_d6_real_proving_cycle.py`
- `scripts/run_d8_b2_real_supabase_dry_run_retry.py`
- `scripts/run_d8_b2r_real_supabase_diagnostics.py`
- `scripts/run_hist_density1_controlled_historical_density.py`
- `scripts/run_hist_density_2_180d_pilot.py`
- `scripts/run_hist_density_3_curated_241_pilot.py`
- `scripts/run_hist_long3_updated_universe_validation.py`
- `scripts/run_hist_long4_real_multi_window_ecology.py`
- `scripts/run_hist_long5b_temporal_delta_sensitivity_classification.py`
- `scripts/run_hist_long6_cross_sectional_ecology_differentiation.py`
- `scripts/run_hist_long7_intra_group_structural_contrast.py`
- `scripts/run_hist_long8_cross_window_persistence.py`
- `scripts/run_hist_long9_persistence_drift.py`
- `scripts/run_lr5_first_governed_replay_wave_review.py`
- `scripts/run_lr6_live5_first_approved_non_dry_persistence_execution.py`
- `scripts/run_ops_live1b_50_symbol_operational_ingest.py`
- `scripts/run_ops_live1b_snapshot_observation_review.py`
- `scripts/run_ops_live2_observation_fact_accumulation.py`
- `scripts/run_ops_live3_structural_state_snapshot.py`
- `scripts/run_production_validation_gates.py`
- `scripts/validate_observability_artifacts.py`
- `scripts/validate_sefi_observation_universe.py`
- `scripts/write_observability_history.py`
- `scripts/write_pipeline_failure_metrics.py`
- `scripts/write_pipeline_metrics.py`
- `transmission_layers/ai_transmission/historical_backfill/historical_ai_transmission_backfill.py`
- `transmission_layers/ai_transmission/historical_backfill/historical_backfill_validation_gates.py`
- `transmission_layers/ai_transmission/phase2b_explainability_layer.py`
- `transmission_layers/ai_transmission/phase2d2_historical_reconstruction_engine_schema_aligned_revised.py`
- `transmission_layers/asset_discovery/entity_resolution/audit_writer.py`
- `transmission_layers/asset_discovery/entity_resolution/canonical_normalizer.py`
- `transmission_layers/asset_discovery/entity_resolution/canonical_registry.py`
- `transmission_layers/asset_discovery/entity_resolution/confidence_scoring.py`
- `transmission_layers/asset_discovery/entity_resolution/disambiguation_rules.py`
- `transmission_layers/asset_discovery/entity_resolution/duplicate_consolidator.py`
- `transmission_layers/asset_discovery/entity_resolution/exchange_normalizer.py`
- `transmission_layers/asset_discovery/entity_resolution/resolve_discovered_entities.py`
- `transmission_layers/asset_discovery/entity_resolution/ticker_normalizer.py`
- `transmission_layers/asset_discovery/security_identifier_extraction.py`
- `transmission_layers/asset_discovery/tier3h4_dynamic_entity_discovery.py`
- `transmission_layers/asset_discovery/tier3h5/advisory_registry_hooks.py`
- `transmission_layers/asset_discovery/tier3h5/advisory_registry_observability.py`
- `transmission_layers/asset_discovery/tier3h5/canonical_graph_governance.py`
- `transmission_layers/asset_discovery/tier3h5/canonical_propagation_memory.py`
- `transmission_layers/asset_discovery/tier3h5/canonical_registry_normalization.py`
- `transmission_layers/asset_discovery/tier3h5/canonical_registry_resolution.py`
- `transmission_layers/asset_discovery/tier3h5/canonical_registry_resolution_observability.py`
- `transmission_layers/asset_discovery/tier3h5/canonical_registry_sample_sources.py`
- `transmission_layers/asset_discovery/tier3h5/cross_registry_identity_governance.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi/artifacts.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi/contracts.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi/exports.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi/measures.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi/semantic_layer.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi/validation.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_smoke/__init__.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_smoke/artifact_inventory.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_smoke/artifact_smoke_test.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_smoke/dashboard_smoke_test.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_smoke/measure_smoke_test.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_smoke/operational_readiness.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_smoke/semantic_smoke_test.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_validation/__init__.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_validation/artifact_validator.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_validation/determinism_validator.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_validation/export_validator.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_validation/measure_validator.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_validation/operational_summary.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_validation/relationship_validator.py`
- `transmission_layers/asset_discovery/tier3h5/governance_bi_validation/semantic_validator.py`
- `transmission_layers/asset_discovery/tier3h5/governance_contracts.py`
- `transmission_layers/asset_discovery/tier3h5/governance_explainability_api.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/artifact_trend_analysis.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/artifacts.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/continuity.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/drift_frequency_analysis.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/escalation_history.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/explainability.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/hashing.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/incident_history.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/orchestration_trend_analysis.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/persistence.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/readiness_trend_analysis.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/trend_analytics.py`
- `transmission_layers/asset_discovery/tier3h5/governance_history/watchlist_history.py`
- `transmission_layers/asset_discovery/tier3h5/governance_operational_intelligence.py`
- `transmission_layers/asset_discovery/tier3h5/governance_query/base.py`
- `transmission_layers/asset_discovery/tier3h5/governance_query/dashboard_views.py`
- `transmission_layers/asset_discovery/tier3h5/governance_query/serialization.py`
- `transmission_layers/asset_discovery/tier3h5/governance_risk_intelligence.py`
- `transmission_layers/asset_discovery/tier3h5/registry_quality_freshness_governance.py`
- `transmission_layers/asset_discovery/tier3h5/registry_replay_governance.py`
- `transmission_layers/asset_discovery/tier3h5/registry_snapshot_archive.py`
- `transmission_layers/asset_discovery/tier3h5/registry_snapshot_time_travel.py`
- `transmission_layers/asset_discovery/tier3h_transmission_candidate_discovery.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/d2_dashboard_supabase_schema.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/d3_controlled_dashboard_persistence_execution.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/d4_real_persistence_readback_verification.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/d6_operational_proving_cycle.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/d7_streamlit_dashboard_viewer.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/dashboard_d1_sample_data_seed.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/dashboard_d1_seed_manifests.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/dashboard_o2_supabase_contracts.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/dashboard_o3_supabase_write_adapter.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/dashboard_o6_supabase_read_adapter.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/dashboard_o7_streamlit_supabase_runtime.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/o3_real_market_semantic_inputs.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/o4_real_market_semantic_dashboard_integration.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/o5_semantic_finding_generation.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/o6_finding_persistence_export_contract.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/o7_dashboard_persistence_adapter.py`
- `transmission_layers/expectation_failure/dashboard_operationalization/o8_dashboard_persistence_readback_verification.py`
- `transmission_layers/expectation_failure/expectation_intelligence/__init__.py`
- `transmission_layers/expectation_failure/expectation_intelligence/cd1_candidate_diversity_strengthening.py`
- `transmission_layers/expectation_failure/expectation_intelligence/cd2_replay_novelty_prioritization.py`
- `transmission_layers/expectation_failure/expectation_intelligence/cd3_governed_novelty_guided_replay_expansion_plan.py`
- `transmission_layers/expectation_failure/expectation_intelligence/cd4_expectation_drift_and_replay_saturation_intelligence.py`
- `transmission_layers/expectation_failure/expectation_intelligence/cd5_operator_adjudication_assist.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d10_longitudinal_finding_monitoring_alerting_readiness.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d11_historical_replay_evidence_backfill.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d12_historical_expectation_intelligence_synthesis.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d13_historical_expectation_delta_regime_evolution.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d14_governance_integrated_historical_evolution_orchestration.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d15_historical_backfill_execution_dashboard_enrichment.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d16_historical_findings_replay_operator_narrative.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d17_historical_confidence_attribution_lineage_compression.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d18_cross_run_confidence_delta_operator_triage.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d19_triage_explainability_continuity_taxonomy.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d21_limited_governed_non_dry_historical_backfill.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_2_evidence_density_historical_replay_expansion.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_5_operational_intelligence_density_verification.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_6_evidence_graph_enrichment_linkage_density.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_a1_explainability_causal_narratives.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_b1_controlled_replay_expansion.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_b2_controlled_replay_backfill_execution.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_b2_real_supabase_dry_run_retry.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_b2r2_supabase_runtime_connectivity.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_b2r3_operator_rerun_harness.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_b2r_replay_candidate_source_repair_audit.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_b3_replay_persistence_activation_audit.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_b4_governed_replay_persistence_execution.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_c_persisted_replay_readback_dashboard_certification.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d8_evidence_prioritization_operational_insight.py`
- `transmission_layers/expectation_failure/expectation_intelligence/d9_persisted_evidence_finding_generation.py`
- `transmission_layers/expectation_failure/expectation_intelligence/e1_expectation_intelligence.py`
- `transmission_layers/expectation_failure/expectation_intelligence/e2_evidence_interpretation.py`
- `transmission_layers/expectation_failure/expectation_intelligence/e3_temporal_expectation_memory.py`
- `transmission_layers/expectation_failure/expectation_intelligence/e4_semantic_theme_memory.py`
- `transmission_layers/expectation_failure/expectation_intelligence/e5_expectation_supervisor_closeout.py`
- `transmission_layers/expectation_failure/expectation_intelligence/e7_expectation_closeout_certification.py`
- `transmission_layers/expectation_failure/expectation_intelligence/h1_historical_density_expansion.py`
- `transmission_layers/expectation_failure/expectation_intelligence/h2_governed_replay_expansion_cycle.py`
- `transmission_layers/expectation_failure/expectation_intelligence/h3_cross_replay_structural_transition_intelligence.py`
- `transmission_layers/expectation_failure/expectation_intelligence/ix1_structural_insight_extraction.py`
- `transmission_layers/expectation_failure/expectation_intelligence/ix2_evidence_linked_insight_attribution.py`
- `transmission_layers/expectation_failure/expectation_intelligence/ix3_structural_narrative_compression.py`
- `transmission_layers/expectation_failure/expectation_intelligence/ix4_interpretability_hardening.py`
- `transmission_layers/expectation_failure/expectation_intelligence/ix5_explainability_continuity_calibration.py`
- `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py`
- `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py`
- `transmission_layers/expectation_failure/real_data/hist_density3_curated_ecology_expansion.py`
- `transmission_layers/expectation_failure/real_data/hist_density4_findings_review.py`
- `transmission_layers/expectation_failure/real_data/hist_long1_longitudinal_ecology.py`
- `transmission_layers/expectation_failure/real_data/hist_long3_updated_universe_validation.py`
- `transmission_layers/expectation_failure/real_data/hist_long4_real_multi_window_ecology.py`
- `transmission_layers/expectation_failure/real_data/hist_long5b_temporal_delta_sensitivity_classification.py`
- `transmission_layers/expectation_failure/real_data/hist_long6_cross_sectional_ecology_differentiation.py`
- `transmission_layers/expectation_failure/real_data/hist_long7_intra_group_structural_contrast.py`
- `transmission_layers/expectation_failure/real_data/ops_hist1_controlled_historical_observation.py`
- `transmission_layers/expectation_failure/real_data/ops_hist2_historical_continuity_intelligence.py`
- `transmission_layers/expectation_failure/real_data/ops_hist3_historical_continuity_archetypes.py`
- `transmission_layers/expectation_failure/real_data/ops_hist4_archetype_recurrence_ecology.py`
- `transmission_layers/expectation_failure/real_data/ops_hist5_temporal_continuity_regimes.py`
- `transmission_layers/expectation_failure/real_data/ops_hist6_regime_morphology_observation.py`
- `transmission_layers/expectation_failure/real_data/ops_hist7_regime_ecology_saturation.py`
- `transmission_layers/expectation_failure/real_data/ops_hist_cache_raw_fmp.py`
- `transmission_layers/expectation_failure/real_data/ops_live1_controlled_ecosystem_ingestion.py`
- `transmission_layers/expectation_failure/real_data/ops_live1b_snapshot_observation_review.py`
- `transmission_layers/expectation_failure/real_data/sde2_curated_symbol_ecology_expansion.py`
- `transmission_layers/expectation_failure/real_data/sefi_observation_universe.py`
- `transmission_layers/expectation_failure/replay_ecology/__init__.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid10_first_real_replay_metric_payload_emission_design.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid11_first_real_replay_richness_payload_builder.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid12_real_replay_richness_payload_validation_harness.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid13_dry_run_replay_richness_payload_attachment.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid14_first_replay_richness_payload_supervisor_review.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid1_pre_post_replay_delta_evidence.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid1a_evidence_source_mapping.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid2_measurable_replay_evidence_capture_design.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid3_measurable_evidence_capture_adapter.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid4_first_real_evidence_record_emission_review.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid5_replay_metrics_emission_hook_design.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid6_minimal_in_memory_metrics_emission_hook.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid9_real_replay_metric_payload_production_plan.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_exec1_first_governed_bounded_enriched_replay_wave.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_live0_governed_live_replay_ingestion_readiness_plan.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_live1_first_tiny_governed_replay_ingestion_dry_run_wave.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_live2_first_tiny_governed_replay_ingestion_non_dry_readiness_review.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_live3_first_tiny_governed_replay_ingestion_non_dry_execution.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_live4_first_non_dry_execution_result_verification.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_live5_first_approved_non_dry_persistence_execution_attempt.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_live7_deterministic_shared_wave_id_remediation.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_live8_replay_cohort_integrity_monitoring_and_regression_safeguards.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_obs3_controlled_ecological_enrichment.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_obs4_enriched_replay_candidate_universe.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_obs5_enriched_universe_readiness_review.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_obs6_first_enriched_replay_wave_design.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_obs7_dry_run_enriched_replay_observation_simulation.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_obs8_governed_enriched_replay_observation_proposal.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_obs9_execution_review_framework.py`
- `transmission_layers/expectation_failure/replay_ecology/lr6_run1_single_governed_observation_wave.py`
- `transmission_layers/graph_foundation/continuity/continuity_engine.py`
- `transmission_layers/graph_foundation/phase4e_historical_propagation_replay.py`
- `transmission_layers/graph_foundation/phase5b_propagation_corridor_engine.py`
- `transmission_layers/graph_foundation/phase5c_regime_corridor_dynamics_engine.py`
- `transmission_layers/graph_foundation/phase5d_structural_propagation_regime_forecasting_engine.py`
- `transmission_layers/history_long/hist_long8_cross_window_persistence.py`
- `transmission_layers/history_long/hist_long9_persistence_drift.py`
- `transmission_layers/history_read_model/fact_emitter.py`
- `transmission_layers/history_read_model/loader.py`
- `transmission_layers/history_read_model/observation_query.py`
- `transmission_layers/history_read_model/queries.py`
- `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`
- `transmission_layers/live_ops/ops_live3_structural_state_snapshot.py`
- `transmission_layers/phase5a_two_hop/phase5a_two_hop_propagation.py`
- `transmission_layers/phase5a_two_hop/phase5a_validate_two_hop.py`
- `transmission_layers/shared/structural_theme_historical_analytics_phase2d.py`
- `utils/paginated_rest_loader.py`
- `utils/rolling_reconstruction_aggregators.py`
- `utils/streaming_observation_loader.py`

## Import graph summary

Scanned 783 Python files across `scripts`, `transmission_layers`, `governance`, `replay`, `persistence`, `topology`, `utils`. Found 1094 in-scope import edges from scoped files; inbound evidence also considered tests and other non-generated Python sources.

| Subsystem | Files | Classification counts | External inbound examples |
|---|---:|---|---|
| `transmission_layers/live_ops` | 3 | {"ACTIVE_REFERENCED": 1, "PROTECTED_ACTIVE": 2} | `transmission_layers/live_ops/__init__.py` <= tests/test_ops_live2_observation_fact_accumulation.py<br>`transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py` <= scripts/run_ops_live2_observation_fact_accumulation.py, tests/test_ops_live2_observation_fact_accumulation.py<br>`transmission_layers/live_ops/ops_live3_structural_state_snapshot.py` <= scripts/run_ops_live3_structural_state_snapshot.py, tests/test_ops_live3_structural_state_snapshot.py |
| `transmission_layers/history_read_model` | 5 | {"PROTECTED_ACTIVE": 4, "UNREFERENCED_CANDIDATE": 1} | `transmission_layers/history_read_model/fact_emitter.py` <= tests/test_db2_direct_fact_emission.py, tests/test_hist_long8_cross_window_persistence.py, tests/test_hist_long9_persistence_drift.py<br>`transmission_layers/history_read_model/loader.py` <= scripts/run_db1_supabase_read_model_load.py, tests/test_db1_supabase_read_model.py, transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py<br>`transmission_layers/history_read_model/observation_query.py` <= scripts/run_obs_query1_observation_fact_intelligence.py, tests/test_obs_query1_observation_fact_intelligence.py, transmission_layers/live_ops/ops_live3_structural_state_snapshot.py<br>`transmission_layers/history_read_model/queries.py` <= tests/test_db1_supabase_read_model.py, transmission_layers/history_long/hist_long8_cross_window_persistence.py, transmission_layers/history_long/hist_long9_persistence_drift.py |
| `transmission_layers/history_long` | 5 | {"ACTIVE_REFERENCED": 2, "PROTECTED_ACTIVE": 2, "UNREFERENCED_CANDIDATE": 1} | `transmission_layers/history_long/hist_intel1_historical_structural_findings.py` <= scripts/run_hist_intel1_historical_structural_findings.py, tests/test_hist_intel1_historical_structural_findings.py<br>`transmission_layers/history_long/hist_intel1b_fact_native_historical_findings.py` <= scripts/run_hist_intel1b_fact_native_historical_findings.py, tests/test_hist_intel1b_fact_native_historical_findings.py<br>`transmission_layers/history_long/hist_long8_cross_window_persistence.py` <= scripts/run_hist_long8_cross_window_persistence.py, tests/test_hist_long8_cross_window_persistence.py, tests/test_hist_long9_persistence_drift.py<br>`transmission_layers/history_long/hist_long9_persistence_drift.py` <= scripts/run_hist_long9_persistence_drift.py, tests/test_hist_long9_persistence_drift.py |
| `transmission_layers/expectation_failure/real_data` | 51 | {"ACTIVE_REFERENCED": 15, "PROTECTED_ACTIVE": 22, "UNKNOWN_REQUIRES_REVIEW": 14} | `transmission_layers/expectation_failure/real_data/__init__.py` <= tests/test_b2_ingestion_certification.py, tests/test_b3_snapshot_assembly_certification.py, tests/test_b4_snapshot_persistence_certification.py<br>`transmission_layers/expectation_failure/real_data/b1_benchmark_registry.py` <= tests/test_b2_ingestion_certification.py<br>`transmission_layers/expectation_failure/real_data/b1_fragility_payload_builder.py` <= tests/test_b1_snapshot_certification.py<br>`transmission_layers/expectation_failure/real_data/b1_market_snapshot_builder.py` <= tests/test_b1_market_snapshot_builder.py, tests/test_b1_snapshot_certification.py, tests/test_b2_ingestion_certification.py<br>`transmission_layers/expectation_failure/real_data/b1_real_entity_registry.py` <= tests/test_b1_real_entity_registry.py, tests/test_b2_ingestion_certification.py |
| `transmission_layers/graph_foundation` | 36 | {"ACTIVE_REFERENCED": 1, "LEGACY_REFERENCED": 1, "PROTECTED_ACTIVE": 5, "UNKNOWN_REQUIRES_REVIEW": 6, "UNREFERENCED_CANDIDATE": 23} | `transmission_layers/graph_foundation/continuity/continuity_engine.py` <= .github/workflows/continuity_engine_pipeline.yml<br>`transmission_layers/graph_foundation/phase5b_propagation_corridor_engine.py` <= .github/workflows/phase5b_propagation_corridor_pipeline.yml<br>`transmission_layers/graph_foundation/phase5c_regime_corridor_dynamics_engine.py` <= .github/workflows/phase5c_regime_corridor_dynamics_pipeline.yml<br>`transmission_layers/graph_foundation/phase5d_structural_propagation_regime_forecasting_engine.py` <= .github/workflows/phase5d_structural_propagation_regime_forecasting_pipeline.yml |
| `transmission_layers/alpha` | 11 | {"ACTIVE_REFERENCED": 3, "UNKNOWN_REQUIRES_REVIEW": 8} | `transmission_layers/alpha/__init__.py` <= tests/test_alpha_layer_c_structural_divergence.py, tests/test_alpha_layer_d_narrative_fragility.py, tests/test_alpha_layer_e_signal_interaction_effects.py<br>`transmission_layers/alpha/layer_a/__init__.py` <= tests/test_alpha_layer_a_predictive_validation.py<br>`transmission_layers/alpha/layer_b/__init__.py` <= tests/test_alpha_layer_b_regime_conditional_efficacy.py |
| `transmission_layers/intelligence` | 204 | {"ACTIVE_REFERENCED": 179, "UNKNOWN_REQUIRES_REVIEW": 23, "UNREFERENCED_CANDIDATE": 2} | `transmission_layers/intelligence/tier3i/contagion_mapping.py` <= tests/test_tier3i_contagion_mapping.py<br>`transmission_layers/intelligence/tier3i/edge_quality.py` <= tests/test_tier3i_edge_quality.py<br>`transmission_layers/intelligence/tier3i/historical_replay.py` <= tests/test_tier3i_historical_replay.py<br>`transmission_layers/intelligence/tier3i/intelligence_summary.py` <= tests/test_tier3i_intelligence_summary.py<br>`transmission_layers/intelligence/tier3i/multi_hop_quality.py` <= tests/test_tier3i_multi_hop_quality.py |

## Inbound dependency summary by subsystem

### `transmission_layers/live_ops`
- File count: 3
- Classification counts: `{"ACTIVE_REFERENCED": 1, "PROTECTED_ACTIVE": 2}`
- Subsystem-level textual references: `scripts/run_ops_live2_observation_fact_accumulation.py`, `scripts/run_ops_live3_structural_state_snapshot.py`, `tests/test_ops_live2_observation_fact_accumulation.py`, `tests/test_ops_live3_structural_state_snapshot.py`
- Active/protected inbound signals:
  - `transmission_layers/live_ops/__init__.py` (ACTIVE_REFERENCED): `tests/test_ops_live2_observation_fact_accumulation.py`
  - `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py` (PROTECTED_ACTIVE): `scripts/run_ops_live2_observation_fact_accumulation.py`, `tests/test_ops_live2_observation_fact_accumulation.py`, `scripts/run_ops_live2_observation_fact_accumulation.py`, `tests/test_ops_live2_observation_fact_accumulation.py`
  - `transmission_layers/live_ops/ops_live3_structural_state_snapshot.py` (PROTECTED_ACTIVE): `scripts/run_ops_live3_structural_state_snapshot.py`, `tests/test_ops_live3_structural_state_snapshot.py`, `scripts/run_ops_live3_structural_state_snapshot.py`, `tests/test_ops_live3_structural_state_snapshot.py`

### `transmission_layers/history_read_model`
- File count: 5
- Classification counts: `{"PROTECTED_ACTIVE": 4, "UNREFERENCED_CANDIDATE": 1}`
- Subsystem-level textual references: `scripts/run_db1_supabase_read_model_load.py`, `scripts/run_obs_query1_observation_fact_intelligence.py`, `tests/test_db1_supabase_read_model.py`, `tests/test_db2_direct_fact_emission.py`, `tests/test_hist_long8_cross_window_persistence.py`, `tests/test_hist_long9_persistence_drift.py`, `tests/test_obs_query1_observation_fact_intelligence.py`, `tests/test_ops_live2_observation_fact_accumulation.py`, `transmission_layers/history_long/hist_long8_cross_window_persistence.py`, `transmission_layers/history_long/hist_long9_persistence_drift.py`, `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`, `transmission_layers/live_ops/ops_live3_structural_state_snapshot.py`
- Active/protected inbound signals:
  - `transmission_layers/history_read_model/fact_emitter.py` (PROTECTED_ACTIVE): `tests/test_db2_direct_fact_emission.py`, `tests/test_hist_long8_cross_window_persistence.py`, `tests/test_hist_long9_persistence_drift.py`, `tests/test_ops_live2_observation_fact_accumulation.py`, `transmission_layers/history_long/hist_long8_cross_window_persistence.py`, `transmission_layers/history_long/hist_long9_persistence_drift.py`, `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`, `tests/test_db2_direct_fact_emission.py`
  - `transmission_layers/history_read_model/loader.py` (PROTECTED_ACTIVE): `scripts/run_db1_supabase_read_model_load.py`, `tests/test_db1_supabase_read_model.py`, `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`, `scripts/run_db1_supabase_read_model_load.py`, `tests/test_db1_supabase_read_model.py`, `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`
  - `transmission_layers/history_read_model/observation_query.py` (PROTECTED_ACTIVE): `scripts/run_obs_query1_observation_fact_intelligence.py`, `tests/test_obs_query1_observation_fact_intelligence.py`, `transmission_layers/live_ops/ops_live3_structural_state_snapshot.py`, `scripts/run_obs_query1_observation_fact_intelligence.py`, `tests/test_obs_query1_observation_fact_intelligence.py`, `transmission_layers/live_ops/ops_live3_structural_state_snapshot.py`
  - `transmission_layers/history_read_model/queries.py` (PROTECTED_ACTIVE): `tests/test_db1_supabase_read_model.py`, `transmission_layers/history_long/hist_long8_cross_window_persistence.py`, `transmission_layers/history_long/hist_long9_persistence_drift.py`, `tests/test_db1_supabase_read_model.py`, `transmission_layers/history_long/hist_long8_cross_window_persistence.py`, `transmission_layers/history_long/hist_long9_persistence_drift.py`
- Unreferenced candidates (verification queue, not cleanup approval):
  - `transmission_layers/history_read_model/__init__.py`

### `transmission_layers/history_long`
- File count: 5
- Classification counts: `{"ACTIVE_REFERENCED": 2, "PROTECTED_ACTIVE": 2, "UNREFERENCED_CANDIDATE": 1}`
- Subsystem-level textual references: `scripts/run_hist_intel1_historical_structural_findings.py`, `scripts/run_hist_intel1b_fact_native_historical_findings.py`, `scripts/run_hist_long8_cross_window_persistence.py`, `scripts/run_hist_long9_persistence_drift.py`, `tests/test_hist_intel1_historical_structural_findings.py`, `tests/test_hist_intel1b_fact_native_historical_findings.py`, `tests/test_hist_long8_cross_window_persistence.py`, `tests/test_hist_long9_persistence_drift.py`
- Active/protected inbound signals:
  - `transmission_layers/history_long/hist_intel1_historical_structural_findings.py` (ACTIVE_REFERENCED): `scripts/run_hist_intel1_historical_structural_findings.py`, `tests/test_hist_intel1_historical_structural_findings.py`, `scripts/run_hist_intel1_historical_structural_findings.py`, `tests/test_hist_intel1_historical_structural_findings.py`
  - `transmission_layers/history_long/hist_intel1b_fact_native_historical_findings.py` (ACTIVE_REFERENCED): `scripts/run_hist_intel1b_fact_native_historical_findings.py`, `tests/test_hist_intel1b_fact_native_historical_findings.py`, `scripts/run_hist_intel1b_fact_native_historical_findings.py`, `tests/test_hist_intel1b_fact_native_historical_findings.py`
  - `transmission_layers/history_long/hist_long8_cross_window_persistence.py` (PROTECTED_ACTIVE): `scripts/run_hist_long8_cross_window_persistence.py`, `tests/test_hist_long8_cross_window_persistence.py`, `tests/test_hist_long9_persistence_drift.py`, `scripts/run_hist_long8_cross_window_persistence.py`, `tests/test_hist_long8_cross_window_persistence.py`, `tests/test_hist_long9_persistence_drift.py`
  - `transmission_layers/history_long/hist_long9_persistence_drift.py` (PROTECTED_ACTIVE): `scripts/run_hist_long9_persistence_drift.py`, `tests/test_hist_long9_persistence_drift.py`, `scripts/run_hist_long9_persistence_drift.py`, `tests/test_hist_long9_persistence_drift.py`
- Unreferenced candidates (verification queue, not cleanup approval):
  - `transmission_layers/history_long/__init__.py`

### `transmission_layers/expectation_failure/real_data`
- File count: 51
- Classification counts: `{"ACTIVE_REFERENCED": 15, "PROTECTED_ACTIVE": 22, "UNKNOWN_REQUIRES_REVIEW": 14}`
- Subsystem-level textual references: `scripts/check_sefi_universe_source.py`, `scripts/load_sefi_observation_universe.py`, `scripts/run_hist_density1_controlled_historical_density.py`, `scripts/run_hist_density4_findings_review.py`, `scripts/run_hist_density_2_180d_pilot.py`, `scripts/run_hist_density_3_curated_241_pilot.py`, `scripts/run_hist_long1_longitudinal_ecology.py`, `scripts/run_hist_long2_real_longitudinal_ecology.py`, `scripts/run_hist_long3_updated_universe_validation.py`, `scripts/run_hist_long4_real_multi_window_ecology.py`, `scripts/run_hist_long5_analysis_only_review.py`, `scripts/run_hist_long5b_temporal_delta_sensitivity_classification.py`, `scripts/run_hist_long6_cross_sectional_ecology_differentiation.py`, `scripts/run_hist_long7_intra_group_structural_contrast.py`, `scripts/run_ops_hist1_historical_backfill.py`, `scripts/run_ops_hist1_observation_review.py`, `scripts/run_ops_hist2_continuity_intelligence.py`, `scripts/run_ops_hist3_archetype_observation.py`, `scripts/run_ops_hist4_recurrence_ecology.py`, `scripts/run_ops_hist5_temporal_regime_observation.py`
- Active/protected inbound signals:
  - `transmission_layers/expectation_failure/real_data/__init__.py` (ACTIVE_REFERENCED): `tests/test_b2_ingestion_certification.py`, `tests/test_b3_snapshot_assembly_certification.py`, `tests/test_b4_snapshot_persistence_certification.py`, `tests/test_b4_snapshot_persistence_contract.py`, `tests/test_b4_snapshot_persistence_validator.py`, `tests/test_b4_supabase_snapshot_repository.py`, `tests/test_t1_temporal_snapshot_sequencing.py`, `tests/test_t2_structural_delta_intelligence.py`
  - `transmission_layers/expectation_failure/real_data/b1_benchmark_registry.py` (ACTIVE_REFERENCED): `tests/test_b2_ingestion_certification.py`, `tests/test_b2_ingestion_certification.py`, `transmission_layers/expectation_failure/real_data/b1_market_snapshot_builder.py`
  - `transmission_layers/expectation_failure/real_data/b1_fragility_payload_builder.py` (ACTIVE_REFERENCED): `tests/test_b1_snapshot_certification.py`, `tests/test_b1_snapshot_certification.py`
  - `transmission_layers/expectation_failure/real_data/b1_market_snapshot_builder.py` (ACTIVE_REFERENCED): `tests/test_b1_market_snapshot_builder.py`, `tests/test_b1_snapshot_certification.py`, `tests/test_b2_ingestion_certification.py`, `tests/test_b1_market_snapshot_builder.py`, `tests/test_b1_snapshot_certification.py`, `tests/test_b2_ingestion_certification.py`
  - `transmission_layers/expectation_failure/real_data/b1_real_entity_registry.py` (ACTIVE_REFERENCED): `tests/test_b1_real_entity_registry.py`, `tests/test_b2_ingestion_certification.py`, `tests/test_b1_real_entity_registry.py`, `tests/test_b2_ingestion_certification.py`, `transmission_layers/expectation_failure/real_data/b1_market_snapshot_builder.py`
  - `transmission_layers/expectation_failure/real_data/b1_snapshot_certification.py` (ACTIVE_REFERENCED): `tests/test_b1_snapshot_certification.py`, `tests/test_b1_snapshot_certification.py`
  - `transmission_layers/expectation_failure/real_data/b2_ingestion_candidate_builder.py` (ACTIVE_REFERENCED): `tests/test_b2_ingestion_certification.py`, `tests/test_b2_ingestion_certification.py`
  - `transmission_layers/expectation_failure/real_data/b2_ingestion_certification.py` (ACTIVE_REFERENCED): `tests/test_b2_ingestion_certification.py`, `tests/test_b2_ingestion_certification.py`
  - `transmission_layers/expectation_failure/real_data/b2_market_ingestion_adapter.py` (ACTIVE_REFERENCED): `tests/test_b2_market_ingestion_adapter.py`, `tests/test_b3_snapshot_assembler.py`, `tests/test_b2_market_ingestion_adapter.py`, `tests/test_b3_snapshot_assembler.py`
  - `transmission_layers/expectation_failure/real_data/b2_market_input_normalizer.py` (ACTIVE_REFERENCED): `tests/test_b2_market_input_normalizer.py`, `tests/test_b2_market_input_normalizer.py`
  - `transmission_layers/expectation_failure/real_data/b3_snapshot_assembler.py` (ACTIVE_REFERENCED): `tests/test_b3_snapshot_assembler.py`, `tests/test_b3_snapshot_assembler.py`
  - `transmission_layers/expectation_failure/real_data/b3_snapshot_input_mapper.py` (ACTIVE_REFERENCED): `tests/test_b3_snapshot_input_mapper.py`, `tests/test_b3_snapshot_input_mapper.py`
  - `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py` (PROTECTED_ACTIVE): `scripts/run_hist_density1_controlled_historical_density.py`, `scripts/run_hist_density_2_180d_pilot.py`, `scripts/run_hist_density_3_curated_241_pilot.py`, `scripts/run_hist_long1_longitudinal_ecology.py`, `tests/test_hist_density1_controlled_historical_density_expansion.py`, `tests/test_hist_density2_180d_pilot.py`, `tests/test_ops_hist_cache_validation_audit.py`, `scripts/run_hist_density1_controlled_historical_density.py`
  - `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py` (PROTECTED_ACTIVE): `scripts/run_hist_density_2_180d_pilot.py`, `tests/test_hist_density2_180d_pilot.py`, `tests/test_ops_hist_cache_validation_audit.py`, `scripts/run_hist_density_2_180d_pilot.py`, `tests/test_hist_density2_180d_pilot.py`, `tests/test_ops_hist_cache_validation_audit.py`, `transmission_layers/expectation_failure/real_data/hist_density3_curated_ecology_expansion.py`
  - `transmission_layers/expectation_failure/real_data/hist_density3_curated_ecology_expansion.py` (PROTECTED_ACTIVE): `scripts/run_hist_density_3_curated_241_pilot.py`, `tests/test_hist_density3_curated_241_pilot.py`, `scripts/run_hist_density_3_curated_241_pilot.py`, `tests/test_hist_density3_curated_241_pilot.py`, `tests/test_sefi_observation_universe_db_migration.py`, `transmission_layers/expectation_failure/real_data/hist_density4_findings_review.py`, `transmission_layers/expectation_failure/real_data/hist_long1_longitudinal_ecology.py`, `transmission_layers/expectation_failure/real_data/hist_long2_real_longitudinal_ecology.py`
  - `transmission_layers/expectation_failure/real_data/hist_density4_findings_review.py` (PROTECTED_ACTIVE): `scripts/run_hist_density4_findings_review.py`, `tests/test_hist_density4_findings_review.py`, `scripts/run_hist_density4_findings_review.py`, `tests/test_hist_density4_findings_review.py`, `transmission_layers/expectation_failure/real_data/hist_long1_longitudinal_ecology.py`, `transmission_layers/expectation_failure/real_data/hist_long2_real_longitudinal_ecology.py`, `transmission_layers/expectation_failure/real_data/hist_long3_updated_universe_validation.py`, `transmission_layers/expectation_failure/real_data/hist_long4_real_multi_window_ecology.py`
  - `transmission_layers/expectation_failure/real_data/hist_long1_longitudinal_ecology.py` (PROTECTED_ACTIVE): `scripts/run_hist_long1_longitudinal_ecology.py`, `tests/test_hist_long1_longitudinal_ecology.py`, `scripts/run_hist_long1_longitudinal_ecology.py`, `tests/test_hist_long1_longitudinal_ecology.py`, `transmission_layers/expectation_failure/real_data/hist_long2_real_longitudinal_ecology.py`, `transmission_layers/expectation_failure/real_data/hist_long4_real_multi_window_ecology.py`, `transmission_layers/expectation_failure/real_data/hist_long5_analysis_only_review.py`
  - `transmission_layers/expectation_failure/real_data/hist_long2_real_longitudinal_ecology.py` (ACTIVE_REFERENCED): `scripts/run_hist_long2_real_longitudinal_ecology.py`, `tests/test_hist_long2_real_longitudinal_ecology.py`, `scripts/run_hist_long2_real_longitudinal_ecology.py`, `tests/test_hist_long2_real_longitudinal_ecology.py`
  - `transmission_layers/expectation_failure/real_data/hist_long3_updated_universe_validation.py` (PROTECTED_ACTIVE): `scripts/run_hist_long3_updated_universe_validation.py`, `tests/test_hist_long3_updated_universe_validation.py`, `scripts/run_hist_long3_updated_universe_validation.py`, `tests/test_hist_long3_updated_universe_validation.py`
  - `transmission_layers/expectation_failure/real_data/hist_long4_real_multi_window_ecology.py` (PROTECTED_ACTIVE): `scripts/run_hist_long4_real_multi_window_ecology.py`, `tests/test_hist_long4_real_multi_window_ecology.py`, `scripts/run_hist_long4_real_multi_window_ecology.py`, `tests/test_hist_long4_real_multi_window_ecology.py`, `transmission_layers/expectation_failure/real_data/hist_long5_analysis_only_review.py`, `transmission_layers/expectation_failure/real_data/hist_long5b_temporal_delta_sensitivity_classification.py`
  - `transmission_layers/expectation_failure/real_data/hist_long5_analysis_only_review.py` (ACTIVE_REFERENCED): `scripts/run_hist_long5_analysis_only_review.py`, `tests/test_hist_long5_analysis_only_review.py`, `scripts/run_hist_long5_analysis_only_review.py`, `tests/test_hist_long5_analysis_only_review.py`
  - `transmission_layers/expectation_failure/real_data/hist_long5b_temporal_delta_sensitivity_classification.py` (PROTECTED_ACTIVE): `scripts/run_hist_long5b_temporal_delta_sensitivity_classification.py`, `tests/test_hist_long5b_temporal_delta_sensitivity_classification.py`, `scripts/run_hist_long5b_temporal_delta_sensitivity_classification.py`, `tests/test_hist_long5b_temporal_delta_sensitivity_classification.py`
  - `transmission_layers/expectation_failure/real_data/hist_long6_cross_sectional_ecology_differentiation.py` (PROTECTED_ACTIVE): `scripts/run_hist_long6_cross_sectional_ecology_differentiation.py`, `tests/test_hist_long6_cross_sectional_ecology_differentiation.py`, `scripts/run_hist_long6_cross_sectional_ecology_differentiation.py`, `tests/test_hist_long6_cross_sectional_ecology_differentiation.py`
  - `transmission_layers/expectation_failure/real_data/hist_long7_intra_group_structural_contrast.py` (PROTECTED_ACTIVE): `scripts/run_hist_long7_intra_group_structural_contrast.py`, `tests/test_hist_long7_intra_group_structural_contrast.py`, `scripts/run_hist_long7_intra_group_structural_contrast.py`, `tests/test_hist_long7_intra_group_structural_contrast.py`
  - `transmission_layers/expectation_failure/real_data/ops_hist1_controlled_historical_observation.py` (PROTECTED_ACTIVE): `scripts/run_ops_hist1_historical_backfill.py`, `scripts/run_ops_hist1_observation_review.py`, `tests/test_ops_hist1_controlled_historical_observation.py`, `scripts/run_ops_hist1_historical_backfill.py`, `scripts/run_ops_hist1_observation_review.py`, `tests/test_ops_hist1_controlled_historical_observation.py`, `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py`, `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py`
  - `transmission_layers/expectation_failure/real_data/ops_hist2_historical_continuity_intelligence.py` (PROTECTED_ACTIVE): `scripts/run_ops_hist2_continuity_intelligence.py`, `tests/test_ops_hist2_historical_continuity_intelligence.py`, `scripts/run_ops_hist2_continuity_intelligence.py`, `tests/test_ops_hist2_historical_continuity_intelligence.py`, `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py`, `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py`, `transmission_layers/expectation_failure/real_data/ops_hist3_historical_continuity_archetypes.py`
  - `transmission_layers/expectation_failure/real_data/ops_hist3_historical_continuity_archetypes.py` (PROTECTED_ACTIVE): `scripts/run_ops_hist3_archetype_observation.py`, `tests/test_ops_hist3_historical_continuity_archetypes.py`, `scripts/run_ops_hist3_archetype_observation.py`, `tests/test_ops_hist3_historical_continuity_archetypes.py`, `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py`, `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py`, `transmission_layers/expectation_failure/real_data/ops_hist4_archetype_recurrence_ecology.py`
  - `transmission_layers/expectation_failure/real_data/ops_hist4_archetype_recurrence_ecology.py` (PROTECTED_ACTIVE): `scripts/run_ops_hist4_recurrence_ecology.py`, `tests/test_ops_hist4_archetype_recurrence_ecology.py`, `scripts/run_ops_hist4_recurrence_ecology.py`, `tests/test_ops_hist4_archetype_recurrence_ecology.py`, `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py`, `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py`, `transmission_layers/expectation_failure/real_data/ops_hist5_temporal_continuity_regimes.py`
  - `transmission_layers/expectation_failure/real_data/ops_hist5_temporal_continuity_regimes.py` (PROTECTED_ACTIVE): `scripts/run_ops_hist5_temporal_regime_observation.py`, `tests/test_ops_hist5_temporal_continuity_regimes.py`, `scripts/run_ops_hist5_temporal_regime_observation.py`, `tests/test_ops_hist5_temporal_continuity_regimes.py`, `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py`, `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py`, `transmission_layers/expectation_failure/real_data/ops_hist6_regime_morphology_observation.py`
  - `transmission_layers/expectation_failure/real_data/ops_hist6_regime_morphology_observation.py` (PROTECTED_ACTIVE): `scripts/run_ops_hist6_regime_morphology_observation.py`, `tests/test_ops_hist6_regime_morphology_observation.py`, `scripts/run_ops_hist6_regime_morphology_observation.py`, `tests/test_ops_hist6_regime_morphology_observation.py`, `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py`, `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py`, `transmission_layers/expectation_failure/real_data/ops_hist7_regime_ecology_saturation.py`
- Unknown/review signals:
  - `transmission_layers/expectation_failure/real_data/b2_market_input_validation.py`
  - `transmission_layers/expectation_failure/real_data/b3_certified_snapshot_envelope.py`
  - `transmission_layers/expectation_failure/real_data/b3_snapshot_assembly_certification.py`
  - `transmission_layers/expectation_failure/real_data/b3_snapshot_assembly_validation.py`
  - `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_certification.py`
  - `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_contract.py`
  - `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_orchestrator.py`
  - `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_validator.py`
  - `transmission_layers/expectation_failure/real_data/b4_supabase_snapshot_repository.py`
  - `transmission_layers/expectation_failure/real_data/t2_structural_delta_intelligence.py`
  - `transmission_layers/expectation_failure/real_data/t3_fragility_evolution_curves.py`
  - `transmission_layers/expectation_failure/real_data/t4_regime_transition_detection.py`
  - `transmission_layers/expectation_failure/real_data/t5_historical_explainability.py`
  - `transmission_layers/expectation_failure/real_data/t6_temporal_evolution_certification_closeout.py`

### `transmission_layers/graph_foundation`
- File count: 36
- Classification counts: `{"ACTIVE_REFERENCED": 1, "LEGACY_REFERENCED": 1, "PROTECTED_ACTIVE": 5, "UNKNOWN_REQUIRES_REVIEW": 6, "UNREFERENCED_CANDIDATE": 23}`
- Subsystem-level textual references: `.github/workflows/ai_transmission_phase2a_pipeline_phase2d_revised.yml`, `.github/workflows/continuity_engine_pipeline.yml`, `.github/workflows/multi_theme_graph_pass1.yml`, `.github/workflows/phase3a1_evidence_density_expansion.yml`, `.github/workflows/phase3a2_cross_theme_relationship_expansion.yml`, `.github/workflows/phase3a_evidence_graph_expansion.yml`, `.github/workflows/phase3b_relationship_persistence.yml`, `.github/workflows/phase3c_regime_transition_structural_drift.yml`, `.github/workflows/phase3d_structural_pressure_accumulation.yml`, `.github/workflows/phase3e_transmission_potential_surface.yml`, `.github/workflows/phase4a_controlled_single_hop_propagation.yml`, `.github/workflows/phase4b_propagation_memory_decay.yml`, `.github/workflows/phase4d_daily_graph_evolution.yml`, `.github/workflows/phase4e_historical_propagation_replay.yml`, `.github/workflows/phase5a2_structural_intermediaries.yml`, `.github/workflows/phase5a3_directed_intermediary_seeding.yml`, `.github/workflows/phase5a4_canonical_structural_ontology.yml`, `.github/workflows/phase5a_two_hop_pipeline.yml`, `.github/workflows/phase5b_propagation_corridor_pipeline.yml`, `.github/workflows/phase5c_regime_corridor_dynamics_pipeline.yml`
- Active/protected inbound signals:
  - `transmission_layers/graph_foundation/continuity/continuity_engine.py` (PROTECTED_ACTIVE): `.github/workflows/continuity_engine_pipeline.yml`, `.github/workflows/continuity_engine_pipeline.yml`
  - `transmission_layers/graph_foundation/phase4e_historical_propagation_replay.py` (PROTECTED_ACTIVE): `docs/runbooks/workflow-registry.md`
  - `transmission_layers/graph_foundation/phase5b_propagation_corridor_engine.py` (PROTECTED_ACTIVE): `.github/workflows/phase5b_propagation_corridor_pipeline.yml`, `.github/workflows/phase5b_propagation_corridor_pipeline.yml`, `docs/governance/orchestration-boundaries.md`
  - `transmission_layers/graph_foundation/phase5c_regime_corridor_dynamics_engine.py` (PROTECTED_ACTIVE): `.github/workflows/phase5c_regime_corridor_dynamics_pipeline.yml`, `.github/workflows/phase5c_regime_corridor_dynamics_pipeline.yml`
  - `transmission_layers/graph_foundation/phase5d_structural_propagation_regime_forecasting_engine.py` (PROTECTED_ACTIVE): `.github/workflows/phase5d_structural_propagation_regime_forecasting_pipeline.yml`, `.github/workflows/phase5d_structural_propagation_regime_forecasting_pipeline.yml`
  - `transmission_layers/graph_foundation/run_pass1_graph_foundation.py` (ACTIVE_REFERENCED): `.github/workflows/multi_theme_graph_pass1.yml`
- Unknown/review signals:
  - `transmission_layers/graph_foundation/ai_anchor_graph_seed.py`
  - `transmission_layers/graph_foundation/edge_scoring.py`
  - `transmission_layers/graph_foundation/graph_models.py`
  - `transmission_layers/graph_foundation/graph_snapshot_service.py`
  - `transmission_layers/graph_foundation/graph_validation.py`
  - `transmission_layers/graph_foundation/supabase_rest_client.py`
- Unreferenced candidates (verification queue, not cleanup approval):
  - `transmission_layers/graph_foundation/__init__.py`
  - `transmission_layers/graph_foundation/finish_graph_evolution_run.py`
  - `transmission_layers/graph_foundation/graph_supabase_client.py`
  - `transmission_layers/graph_foundation/intermediaries/canonical_structural_ontology_engine.py`
  - `transmission_layers/graph_foundation/intermediaries/directed_intermediary_seeding_engine.py`
  - `transmission_layers/graph_foundation/intermediaries/intermediary_classification.py`
  - `transmission_layers/graph_foundation/intermediaries/intermediary_detection_engine.py`
  - `transmission_layers/graph_foundation/intermediaries/intermediary_normalization.py`
  - `transmission_layers/graph_foundation/intermediaries/intermediary_scoring.py`
  - `transmission_layers/graph_foundation/intermediaries/intermediary_telemetry.py`
  - `transmission_layers/graph_foundation/intermediaries/intermediary_utils.py`
  - `transmission_layers/graph_foundation/intermediaries/intermediary_validation.py`
  - `transmission_layers/graph_foundation/phase3a1_evidence_density_expansion.py`
  - `transmission_layers/graph_foundation/phase3a2_cross_theme_relationship_expansion.py`
  - `transmission_layers/graph_foundation/phase3a_evidence_graph_expansion.py`
  - `transmission_layers/graph_foundation/phase3b_relationship_persistence.py`
  - `transmission_layers/graph_foundation/phase3c_regime_transition_structural_drift.py`
  - `transmission_layers/graph_foundation/phase3d_structural_pressure_accumulation.py`
  - `transmission_layers/graph_foundation/phase3e_transmission_potential_surface.py`
  - `transmission_layers/graph_foundation/phase4a_controlled_single_hop_propagation.py`
  - `transmission_layers/graph_foundation/phase4b_propagation_memory_decay.py`
  - `transmission_layers/graph_foundation/start_graph_evolution_run.py`
  - `transmission_layers/graph_foundation/write_graph_evolution_phase_event.py`

### `transmission_layers/alpha`
- File count: 11
- Classification counts: `{"ACTIVE_REFERENCED": 3, "UNKNOWN_REQUIRES_REVIEW": 8}`
- Subsystem-level textual references: `tests/test_alpha_layer_a_predictive_validation.py`, `tests/test_alpha_layer_b_regime_conditional_efficacy.py`, `tests/test_alpha_layer_c_structural_divergence.py`, `tests/test_alpha_layer_d_narrative_fragility.py`, `tests/test_alpha_layer_e_signal_interaction_effects.py`, `transmission_layers/alpha/layer_b/regime_conditional_efficacy.py`
- Active/protected inbound signals:
  - `transmission_layers/alpha/__init__.py` (ACTIVE_REFERENCED): `tests/test_alpha_layer_c_structural_divergence.py`, `tests/test_alpha_layer_d_narrative_fragility.py`, `tests/test_alpha_layer_e_signal_interaction_effects.py`
  - `transmission_layers/alpha/layer_a/__init__.py` (ACTIVE_REFERENCED): `tests/test_alpha_layer_a_predictive_validation.py`
  - `transmission_layers/alpha/layer_b/__init__.py` (ACTIVE_REFERENCED): `tests/test_alpha_layer_b_regime_conditional_efficacy.py`
- Unknown/review signals:
  - `transmission_layers/alpha/layer_a/predictive_validation.py`
  - `transmission_layers/alpha/layer_b/regime_conditional_efficacy.py`
  - `transmission_layers/alpha/layer_c/__init__.py`
  - `transmission_layers/alpha/layer_c/structural_divergence_intelligence.py`
  - `transmission_layers/alpha/layer_d/__init__.py`
  - `transmission_layers/alpha/layer_d/narrative_fragility_hype_decomposition.py`
  - `transmission_layers/alpha/layer_e/__init__.py`
  - `transmission_layers/alpha/layer_e/signal_interaction_effect_intelligence.py`

### `transmission_layers/intelligence`
- File count: 204
- Classification counts: `{"ACTIVE_REFERENCED": 179, "UNKNOWN_REQUIRES_REVIEW": 23, "UNREFERENCED_CANDIDATE": 2}`
- Subsystem-level textual references: `.github/workflows/tier3i_transmission_intelligence_tests.yml`, `.github/workflows/tier4_structural_simulation.yml`, `scripts/validate_tier4h_export.sh`, `tests/test_tier3i_contagion_mapping.py`, `tests/test_tier3i_edge_quality.py`, `tests/test_tier3i_historical_replay.py`, `tests/test_tier3i_intelligence_summary.py`, `tests/test_tier3i_multi_hop_quality.py`, `tests/test_tier3i_path_explainability.py`, `tests/test_tier3i_regime_drift.py`, `tests/test_tier3i_structural_influence.py`, `tests/test_tier3i_structural_regime.py`, `tests/test_tier4_adaptation_constraints.py`, `tests/test_tier4_adaptation_exhaustion.py`, `tests/test_tier4_cascade_boundaries.py`, `tests/test_tier4_cascade_corridors.py`, `tests/test_tier4_cascade_explanations.py`, `tests/test_tier4_cascade_signatures.py`, `tests/test_tier4_causal_lineage.py`, `tests/test_tier4_causal_replay.py`
- Active/protected inbound signals:
  - `transmission_layers/intelligence/tier3i/contagion_mapping.py` (ACTIVE_REFERENCED): `tests/test_tier3i_contagion_mapping.py`, `.github/workflows/tier3i_transmission_intelligence_tests.yml`, `tests/test_tier3i_contagion_mapping.py`
  - `transmission_layers/intelligence/tier3i/edge_quality.py` (ACTIVE_REFERENCED): `tests/test_tier3i_edge_quality.py`, `tests/test_tier3i_edge_quality.py`
  - `transmission_layers/intelligence/tier3i/historical_replay.py` (ACTIVE_REFERENCED): `tests/test_tier3i_historical_replay.py`, `.github/workflows/tier3i_transmission_intelligence_tests.yml`, `tests/test_tier3i_historical_replay.py`
  - `transmission_layers/intelligence/tier3i/intelligence_summary.py` (ACTIVE_REFERENCED): `tests/test_tier3i_intelligence_summary.py`, `.github/workflows/tier3i_transmission_intelligence_tests.yml`, `tests/test_tier3i_intelligence_summary.py`
  - `transmission_layers/intelligence/tier3i/multi_hop_quality.py` (ACTIVE_REFERENCED): `tests/test_tier3i_multi_hop_quality.py`, `.github/workflows/tier3i_transmission_intelligence_tests.yml`, `tests/test_tier3i_multi_hop_quality.py`
  - `transmission_layers/intelligence/tier3i/path_explainability.py` (ACTIVE_REFERENCED): `tests/test_tier3i_path_explainability.py`, `.github/workflows/tier3i_transmission_intelligence_tests.yml`, `tests/test_tier3i_path_explainability.py`
  - `transmission_layers/intelligence/tier3i/regime_drift.py` (ACTIVE_REFERENCED): `tests/test_tier3i_regime_drift.py`, `.github/workflows/tier3i_transmission_intelligence_tests.yml`, `tests/test_tier3i_regime_drift.py`
  - `transmission_layers/intelligence/tier3i/structural_influence.py` (ACTIVE_REFERENCED): `tests/test_tier3i_structural_influence.py`, `tests/test_tier3i_structural_influence.py`
  - `transmission_layers/intelligence/tier3i/structural_regime.py` (ACTIVE_REFERENCED): `tests/test_tier3i_structural_regime.py`, `.github/workflows/tier3i_transmission_intelligence_tests.yml`, `tests/test_tier3i_structural_regime.py`
  - `transmission_layers/intelligence/tier4/adaptation_constraints.py` (ACTIVE_REFERENCED): `tests/test_tier4_adaptation_constraints.py`, `tests/test_tier4_adaptation_constraints.py`
  - `transmission_layers/intelligence/tier4/adaptation_exhaustion.py` (ACTIVE_REFERENCED): `tests/test_tier4_adaptation_exhaustion.py`, `tests/test_tier4_adaptation_exhaustion.py`
  - `transmission_layers/intelligence/tier4/cascade_boundaries.py` (ACTIVE_REFERENCED): `tests/test_tier4_cascade_boundaries.py`, `tests/test_tier4_cascade_boundaries.py`
  - `transmission_layers/intelligence/tier4/cascade_corridors.py` (ACTIVE_REFERENCED): `tests/test_tier4_cascade_corridors.py`, `tests/test_tier4_cascade_corridors.py`
  - `transmission_layers/intelligence/tier4/cascade_explanations.py` (ACTIVE_REFERENCED): `tests/test_tier4_cascade_explanations.py`, `tests/test_tier4_cascade_explanations.py`
  - `transmission_layers/intelligence/tier4/cascade_signatures.py` (ACTIVE_REFERENCED): `tests/test_tier4_cascade_signatures.py`, `tests/test_tier4_cascade_signatures.py`
  - `transmission_layers/intelligence/tier4/causal_lineage.py` (ACTIVE_REFERENCED): `tests/test_tier4_causal_lineage.py`, `tests/test_tier4_causal_lineage.py`
  - `transmission_layers/intelligence/tier4/causal_replay.py` (ACTIVE_REFERENCED): `tests/test_tier4_causal_replay.py`, `tests/test_tier7_strategic_causality_replay.py`, `tests/test_tier4_causal_replay.py`, `tests/test_tier7_strategic_causality_replay.py`
  - `transmission_layers/intelligence/tier4/chronic_instability.py` (ACTIVE_REFERENCED): `tests/test_tier4_chronic_instability.py`, `tests/test_tier4_chronic_instability.py`
  - `transmission_layers/intelligence/tier4/contagion_boundaries.py` (ACTIVE_REFERENCED): `tests/test_tier4_contagion_boundaries.py`, `tests/test_tier4_contagion_boundaries.py`
  - `transmission_layers/intelligence/tier4/contagion_explanations.py` (ACTIVE_REFERENCED): `tests/test_tier4_contagion_explanations.py`, `tests/test_tier4_contagion_explanations.py`
  - `transmission_layers/intelligence/tier4/contagion_signatures.py` (ACTIVE_REFERENCED): `tests/test_tier4_contagion_signatures.py`, `tests/test_tier4_contagion_signatures.py`
  - `transmission_layers/intelligence/tier4/containment_integrity.py` (ACTIVE_REFERENCED): `tests/test_tier4_containment_integrity.py`, `tests/test_tier4_containment_integrity.py`
  - `transmission_layers/intelligence/tier4/dependency_concentration.py` (ACTIVE_REFERENCED): `tests/test_tier4_dependency_concentration.py`, `tests/test_tier4_dependency_concentration.py`
  - `transmission_layers/intelligence/tier4/durability_replay.py` (ACTIVE_REFERENCED): `tests/test_tier4_durability_replay.py`, `tests/test_tier4_durability_replay.py`
  - `transmission_layers/intelligence/tier4/failure_thresholds.py` (ACTIVE_REFERENCED): `tests/test_tier4_failure_thresholds.py`, `scripts/validate_tier4h_export.sh`, `tests/test_tier4_failure_thresholds.py`
  - `transmission_layers/intelligence/tier4/flexibility_collapse.py` (ACTIVE_REFERENCED): `tests/test_tier4_flexibility_collapse.py`, `tests/test_tier4_flexibility_collapse.py`
  - `transmission_layers/intelligence/tier4/fragility_analysis.py` (ACTIVE_REFERENCED): `tests/test_tier4_failure_thresholds.py`, `tests/test_tier4_fragility_analysis.py`, `scripts/validate_tier4h_export.sh`, `tests/test_tier4_failure_thresholds.py`, `tests/test_tier4_fragility_analysis.py`
  - `transmission_layers/intelligence/tier4/fragility_explanations.py` (ACTIVE_REFERENCED): `tests/test_tier4_fragility_explanations.py`, `scripts/validate_tier4h_export.sh`, `tests/test_tier4_fragility_explanations.py`
  - `transmission_layers/intelligence/tier4/fragility_replay.py` (ACTIVE_REFERENCED): `tests/test_tier4_fragility_replay.py`, `scripts/validate_tier4h_export.sh`, `tests/test_tier4_fragility_replay.py`
  - `transmission_layers/intelligence/tier4/fragility_signatures.py` (ACTIVE_REFERENCED): `tests/test_tier4_fragility_signatures.py`, `scripts/validate_tier4h_export.sh`, `tests/test_tier4_fragility_signatures.py`
- Unknown/review signals:
  - `transmission_layers/intelligence/tier4/attribution_metrics.py`
  - `transmission_layers/intelligence/tier4/causal_paths.py`
  - `transmission_layers/intelligence/tier4/regime_metrics.py`
  - `transmission_layers/intelligence/tier4/scenario_metrics.py`
  - `transmission_layers/intelligence/tier4/topology_drift.py`
  - `transmission_layers/intelligence/tier5/federation_diagnostics.py`
  - `transmission_layers/intelligence/tier6/propagation_distortion_diagnostics.py`
  - `transmission_layers/intelligence/tier6/transmission_governance_audit_trail.py`
  - `transmission_layers/intelligence/tier6/transmission_governance_finalization.py`
  - `transmission_layers/intelligence/tier6/transmission_governance_review_gate.py`
  - `transmission_layers/intelligence/tier6/transmission_governance_summary.py`
  - `transmission_layers/intelligence/tier6/transmission_path_integrity.py`
  - `transmission_layers/intelligence/tier6/transmission_reliability_diagnostics.py`
  - `transmission_layers/intelligence/tier6/transmission_risk_register.py`
  - `transmission_layers/intelligence/tier7/strategic_anomaly_attribution.py`
  - `transmission_layers/intelligence/tier7/strategic_causality_replay.py`
  - `transmission_layers/intelligence/tier7/strategic_coherence.py`
  - `transmission_layers/intelligence/tier7/strategic_continuity.py`
  - `transmission_layers/intelligence/tier7/strategic_drift_diagnostics.py`
  - `transmission_layers/intelligence/tier7/strategic_graph_state.py`
- Unreferenced candidates (verification queue, not cleanup approval):
  - `transmission_layers/intelligence/tier3i/__init__.py`
  - `transmission_layers/intelligence/tier4/__init__.py`

## Table/reference summary
| Term | Referencing files | Total matches |
|---|---:|---:|
| `sefi_observation_facts` | 16 | 33 |
| ↳ `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py` |  | 1 |
| ↳ `transmission_layers/live_ops/ops_live3_structural_state_snapshot.py` |  | 1 |
| ↳ `transmission_layers/history_read_model/observation_query.py` |  | 1 |
| ↳ `transmission_layers/history_read_model/fact_emitter.py` |  | 2 |
| ↳ `transmission_layers/history_read_model/loader.py` |  | 3 |
| ↳ `transmission_layers/history_read_model/queries.py` |  | 1 |
| ↳ `transmission_layers/history_long/hist_long8_cross_window_persistence.py` |  | 2 |
| ↳ `transmission_layers/history_long/hist_long9_persistence_drift.py` |  | 4 |
| ↳ `.github/workflows/sefi_operational_health.yml` |  | 4 |
| ↳ `supabase/migrations/20260529000100_create_sefi_history_read_model.sql` |  | 4 |
| ↳ `scripts/run_ops_live3_structural_state_snapshot.py` |  | 1 |
| ↳ `scripts/run_obs_query1_observation_fact_intelligence.py` |  | 1 |
| ↳ `tests/test_ops_live3_structural_state_snapshot.py` |  | 1 |
| ↳ `tests/test_obs_query1_observation_fact_intelligence.py` |  | 2 |
| ↳ `tests/test_db1_supabase_read_model.py` |  | 4 |
| ↳ `tests/test_hist_long9_persistence_drift.py` |  | 1 |
| `OPS-LIVE` | 14 | 65 |
| ↳ `transmission_layers/expectation_failure/real_data/ops_live1_controlled_ecosystem_ingestion.py` |  | 2 |
| ↳ `transmission_layers/expectation_failure/real_data/sefi_observation_universe.py` |  | 1 |
| ↳ `transmission_layers/expectation_failure/real_data/ops_live1b_snapshot_observation_review.py` |  | 3 |
| ↳ `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py` |  | 10 |
| ↳ `transmission_layers/live_ops/ops_live3_structural_state_snapshot.py` |  | 5 |
| ↳ `.github/workflows/ops_live1b_daily_observation.yml` |  | 5 |
| ↳ `.github/workflows/sefi_live_daily.yml` |  | 10 |
| ↳ `scripts/run_ops_live2_observation_fact_accumulation.py` |  | 5 |
| ↳ `scripts/run_ops_live1b_snapshot_observation_review.py` |  | 1 |
| ↳ `scripts/run_ops_live3_structural_state_snapshot.py` |  | 4 |
| ↳ `scripts/run_ops_live1b_50_symbol_operational_ingest.py` |  | 1 |
| ↳ `scripts/run_ops_live1a_fmp_probe.py` |  | 1 |
| ↳ `tests/test_ops_live3_structural_state_snapshot.py` |  | 11 |
| ↳ `tests/test_ops_live2_observation_fact_accumulation.py` |  | 6 |
| `HIST-LONG` | 34 | 180 |
| ↳ `transmission_layers/expectation_failure/real_data/hist_long3_updated_universe_validation.py` |  | 3 |
| ↳ `transmission_layers/expectation_failure/real_data/hist_long4_real_multi_window_ecology.py` |  | 29 |
| ↳ `transmission_layers/expectation_failure/real_data/hist_long5_analysis_only_review.py` |  | 6 |
| ↳ `transmission_layers/expectation_failure/real_data/hist_long1_longitudinal_ecology.py` |  | 8 |
| ↳ `transmission_layers/expectation_failure/real_data/hist_long6_cross_sectional_ecology_differentiation.py` |  | 7 |
| ↳ `transmission_layers/expectation_failure/real_data/hist_long5b_temporal_delta_sensitivity_classification.py` |  | 7 |
| ↳ `transmission_layers/expectation_failure/real_data/hist_long7_intra_group_structural_contrast.py` |  | 10 |
| ↳ `transmission_layers/expectation_failure/real_data/hist_long2_real_longitudinal_ecology.py` |  | 17 |
| ↳ `transmission_layers/expectation_failure/real_data/sefi_observation_universe.py` |  | 1 |
| ↳ `transmission_layers/history_long/hist_long8_cross_window_persistence.py` |  | 5 |
| ↳ `transmission_layers/history_long/__init__.py` |  | 1 |
| ↳ `transmission_layers/history_long/hist_long9_persistence_drift.py` |  | 11 |
| ↳ `.github/workflows/hist_long3_updated_universe_validation.yml` |  | 6 |
| ↳ `.github/workflows/sefi_monthly_ecology_review.yml` |  | 10 |
| ↳ `.github/workflows/hist_long4_real_multi_window_ecology.yml` |  | 7 |
| ↳ `.github/workflows/sefi_weekly_observation_review.yml` |  | 2 |
| ↳ `scripts/run_hist_long8_cross_window_persistence.py` |  | 2 |
| ↳ `scripts/run_hist_long4_real_multi_window_ecology.py` |  | 2 |
| ↳ `scripts/run_hist_long5b_temporal_delta_sensitivity_classification.py` |  | 4 |
| ↳ `scripts/run_hist_long5_analysis_only_review.py` |  | 2 |
| `DB-2` | 4 | 8 |
| ↳ `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py` |  | 5 |
| ↳ `scripts/run_hist_long8_cross_window_persistence.py` |  | 1 |
| ↳ `scripts/run_ops_live2_observation_fact_accumulation.py` |  | 1 |
| ↳ `scripts/run_hist_long9_persistence_drift.py` |  | 1 |
| `OBS-QUERY` | 3 | 5 |
| ↳ `transmission_layers/history_read_model/observation_query.py` |  | 1 |
| ↳ `scripts/run_obs_query1_observation_fact_intelligence.py` |  | 2 |
| ↳ `tests/test_obs_query1_observation_fact_intelligence.py` |  | 2 |
| `HIST-INTEL` | 6 | 18 |
| ↳ `transmission_layers/history_long/hist_intel1b_fact_native_historical_findings.py` |  | 4 |
| ↳ `transmission_layers/history_long/hist_intel1_historical_structural_findings.py` |  | 4 |
| ↳ `scripts/run_hist_intel1b_fact_native_historical_findings.py` |  | 2 |
| ↳ `scripts/run_hist_intel1_historical_structural_findings.py` |  | 2 |
| ↳ `tests/test_hist_intel1b_fact_native_historical_findings.py` |  | 4 |
| ↳ `tests/test_hist_intel1_historical_structural_findings.py` |  | 2 |

## Workflow registry drift findings
- Actual workflow count: 52
- Workflows explicitly documented in workflow registry: 3
- Undocumented actual workflows: 50
  - `.github/workflows/ai_transmission_evidence_pipeline.yml`
  - `.github/workflows/ai_transmission_phase2a_pipeline_phase2d_revised.yml`
  - `.github/workflows/ai_transmission_phase2d2_reconstruction.yml`
  - `.github/workflows/continuity_engine_pipeline.yml`
  - `.github/workflows/d21_limited_governed_backfill.yml`
  - `.github/workflows/d8_b2_real_supabase_dry_run_retry.yml`
  - `.github/workflows/d8_b2r_supabase_diagnostics.yml`
  - `.github/workflows/d8_b3_replay_persistence_audit.yml`
  - `.github/workflows/d8_b4_governed_replay_persistence_execution.yml`
  - `.github/workflows/hist_density1_90d_pilot.yml`
  - `.github/workflows/hist_density2_180d_pilot.yml`
  - `.github/workflows/hist_density3_curated_241_pilot.yml`
  - `.github/workflows/hist_long3_updated_universe_validation.yml`
  - `.github/workflows/hist_long4_real_multi_window_ecology.yml`
  - `.github/workflows/historical_source_backfill.yml`
  - `.github/workflows/lr5_first_governed_replay_wave.yml`
  - `.github/workflows/lr6_live5_first_approved_non_dry_persistence_execution.yml`
  - `.github/workflows/multi_theme_graph_pass1.yml`
  - `.github/workflows/observability_coverage_lint.yml`
  - `.github/workflows/ops_live1b_daily_observation.yml`
  - `.github/workflows/phase1_ai_transmission_dual_write.yml`
  - `.github/workflows/phase3a1_evidence_density_expansion.yml`
  - `.github/workflows/phase3a2_cross_theme_relationship_expansion.yml`
  - `.github/workflows/phase3a_evidence_graph_expansion.yml`
  - `.github/workflows/phase3b_relationship_persistence.yml`
  - `.github/workflows/phase3c_regime_transition_structural_drift.yml`
  - `.github/workflows/phase3d_structural_pressure_accumulation.yml`
  - `.github/workflows/phase3e_transmission_potential_surface.yml`
  - `.github/workflows/phase4a_controlled_single_hop_propagation.yml`
  - `.github/workflows/phase4b_propagation_memory_decay.yml`
  - `.github/workflows/phase4d_daily_graph_evolution.yml`
  - `.github/workflows/phase5a2_structural_intermediaries.yml`
  - `.github/workflows/phase5a3_directed_intermediary_seeding.yml`
  - `.github/workflows/phase5a4_canonical_structural_ontology.yml`
  - `.github/workflows/phase5a_two_hop_pipeline.yml`
  - `.github/workflows/phase5b_propagation_corridor_pipeline.yml`
  - `.github/workflows/phase5c_regime_corridor_dynamics_pipeline.yml`
  - `.github/workflows/phase5d_structural_propagation_regime_forecasting_pipeline.yml`
  - `.github/workflows/run-d1-dashboard-seed.yml`
  - `.github/workflows/run_d6_proving_cycle.yml`
  - `.github/workflows/sefi_live_daily.yml`
  - `.github/workflows/sefi_monthly_ecology_review.yml`
  - `.github/workflows/sefi_operational_health.yml`
  - `.github/workflows/sefi_universe_source_check.yml`
  - `.github/workflows/sefi_weekly_observation_review.yml`
  - `.github/workflows/tier3h4_dynamic_entity_discovery.yml`
  - `.github/workflows/tier3h5_registry_foundations.yml`
  - `.github/workflows/tier3h_transmission_candidate_discovery.yml`
  - `.github/workflows/tier3i_transmission_intelligence_tests.yml`
  - `.github/workflows/tier4_structural_simulation.yml`
- Placeholder registry entries remain: `.github/workflows/<add_workflow_name>.yml`
- Dataflow map explicit workflow inventory present: False

## Candidate archive verification queue
These are conservative static-verification candidates only. They are not approved for archive/delete/move, and each requires owner review plus runtime/history checks before CLEAN-3.
- `transmission_layers/history_read_model/__init__.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/history_long/__init__.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/__init__.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/finish_graph_evolution_run.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/graph_supabase_client.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/canonical_structural_ontology_engine.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/directed_intermediary_seeding_engine.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/intermediary_classification.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/intermediary_detection_engine.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/intermediary_normalization.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/intermediary_scoring.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/intermediary_telemetry.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/intermediary_utils.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/intermediaries/intermediary_validation.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase3a1_evidence_density_expansion.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase3a2_cross_theme_relationship_expansion.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase3a_evidence_graph_expansion.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase3b_relationship_persistence.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase3c_regime_transition_structural_drift.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase3d_structural_pressure_accumulation.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase3e_transmission_potential_surface.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase4a_controlled_single_hop_propagation.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/phase4b_propagation_memory_decay.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/start_graph_evolution_run.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/graph_foundation/write_graph_evolution_phase_event.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/intelligence/tier3i/__init__.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.
- `transmission_layers/intelligence/tier4/__init__.py` — No workflow entrypoint, import inbound, or textual reference found in scoped non-generated inventory; requires manual review before archive.

## UNKNOWN_REQUIRES_REVIEW
- `transmission_layers/expectation_failure/real_data/b2_market_input_validation.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/b3_certified_snapshot_envelope.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/b3_snapshot_assembly_certification.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/b3_snapshot_assembly_validation.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_certification.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_contract.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_orchestrator.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_validator.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/b4_supabase_snapshot_repository.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/t2_structural_delta_intelligence.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/t3_fragility_evolution_curves.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/t4_regime_transition_detection.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/t5_historical_explainability.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/expectation_failure/real_data/t6_temporal_evolution_certification_closeout.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/graph_foundation/ai_anchor_graph_seed.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/graph_foundation/edge_scoring.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/graph_foundation/graph_models.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/graph_foundation/graph_snapshot_service.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/graph_foundation/graph_validation.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/graph_foundation/supabase_rest_client.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/alpha/layer_a/predictive_validation.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/alpha/layer_b/regime_conditional_efficacy.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/alpha/layer_c/__init__.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/alpha/layer_c/structural_divergence_intelligence.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/alpha/layer_d/__init__.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/alpha/layer_d/narrative_fragility_hype_decomposition.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/alpha/layer_e/__init__.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/alpha/layer_e/signal_interaction_effect_intelligence.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier4/attribution_metrics.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier4/causal_paths.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier4/regime_metrics.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier4/scenario_metrics.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier4/topology_drift.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier5/federation_diagnostics.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier6/propagation_distortion_diagnostics.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier6/transmission_governance_audit_trail.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier6/transmission_governance_finalization.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier6/transmission_governance_review_gate.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier6/transmission_governance_summary.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier6/transmission_path_integrity.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier6/transmission_reliability_diagnostics.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier6/transmission_risk_register.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_anomaly_attribution.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_causality_replay.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_coherence.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_continuity.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_drift_diagnostics.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_graph_state.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_regime_persistence.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_stability_resilience.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.
- `transmission_layers/intelligence/tier7/strategic_state_transition.py` — Reference signal is ambiguous or only internal/indirect; no archive decision made.

## CLEAN-3 readiness assessment
- Can proceed automatically: **False**
- Assessment: CLEAN-3 should not proceed automatically. Dependency verification found registry drift and conservative candidate/unknown queues that require owner review before any archive or cleanup action.
- Blocking factors:
  - 50 workflows are not documented in workflow-registry.md
  - 27 unreferenced candidates require manual verification
  - 51 modules remain UNKNOWN_REQUIRES_REVIEW
