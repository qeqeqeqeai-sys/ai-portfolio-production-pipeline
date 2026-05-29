# HIST-INTEL-1 Historical Structural Findings Engine

## Objective
Convert existing local SEFI historical observation facts and structural artifacts into concise, ranked, human-readable historical structural findings.

## Source artifacts inspected
- artifacts/hist_long4_real_multi_window_ecology_review.json: status=loaded schema=hist_long4_v1 digest=ccb37a3969309734
- artifacts/hist_long5b_temporal_delta_sensitivity_classification.json: status=loaded schema=hist_long5b_v1 digest=a9c950582a0647b9
- artifacts/hist_long6_cross_sectional_ecology_differentiation.json: status=loaded schema=hist_long6_v1 digest=612aa07c3c9a3d17
- artifacts/hist_long7_intra_group_structural_contrast.json: status=loaded schema=hist_long7_v1 digest=64ac23bba623d16c

## Governance certification
- analysis_only: true
- no_provider_calls: true
- no_supabase_writes: true
- no_prediction: true
- no_trading: true
- no_portfolio_recommendation: true
- no_governed_activation: true

## Executive summary
- Persistent hub: group commodities scored 1.0 with 1 evidence rows (LOW confidence).
- Persistent hub: group consumer_discretionary scored 1.0 with 1 evidence rows (LOW confidence).
- Fragility source: metric normalized_rows scored 1.0 with 1 evidence rows (LOW confidence).
- Fragility source: metric reconciled_date_ratio scored 0.66668 with 1 evidence rows (LOW confidence).
- Recurrent structural pattern: cloud_software_infrastructure / cloud_software_infrastructure co-occurrence recurred 3 times with HIGH confidence.
- Recurrent structural pattern: commodities remained persistent and coherent recurred 3 times with HIGH confidence.
- Stable anchor: group consumer_discretionary scored 1.0 with 3 evidence rows (HIGH confidence).
- Stable anchor: group semiconductors scored 1.0 with 3 evidence rows (HIGH confidence).
- Drifting structure: metric reconciled_date_ratio scored 0.66668 with 1 evidence rows (LOW confidence).
- Drifting structure: metric normalized_rows scored 0.166667 with 1 evidence rows (LOW confidence).

## Persistent structural hubs
- group commodities: persistence_score=1.0 window_coverage=1 evidence_count=1 confidence=LOW
- group consumer_discretionary: persistence_score=1.0 window_coverage=1 evidence_count=1 confidence=LOW
- group semiconductors: persistence_score=1.0 window_coverage=1 evidence_count=1 confidence=LOW
- sector cloud_software_infrastructure: persistence_score=0.306017 window_coverage=4 evidence_count=4 confidence=HIGH
- subsector cloud_software_infrastructure: persistence_score=0.306017 window_coverage=4 evidence_count=4 confidence=HIGH
- sector healthcare_biotech: persistence_score=0.302904 window_coverage=4 evidence_count=4 confidence=HIGH
- sector industrials_automation: persistence_score=0.302904 window_coverage=4 evidence_count=4 confidence=HIGH
- subsector healthcare_biotech: persistence_score=0.302904 window_coverage=4 evidence_count=4 confidence=HIGH
- subsector industrials_automation: persistence_score=0.302904 window_coverage=4 evidence_count=4 confidence=HIGH
- sector semiconductors: persistence_score=0.252832 window_coverage=4 evidence_count=5 confidence=HIGH

## Persistent fragility sources
- metric normalized_rows: fragility_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW
- metric reconciled_date_ratio: fragility_score=0.66668 window_coverage=0 evidence_count=1 confidence=LOW

## Recurrent propagation paths
- cloud_software_infrastructure / cloud_software_infrastructure co-occurrence: recurrence_count=3 windows=['120', '20', '60'] confidence=HIGH
- commodities remained persistent and coherent: recurrence_count=3 windows=['120', '20', '60'] confidence=HIGH
- consumer_discretionary / consumer_discretionary co-occurrence: recurrence_count=3 windows=['120', '20', '60'] confidence=HIGH
- consumer_discretionary remained persistent and coherent: recurrence_count=3 windows=['120', '20', '60'] confidence=HIGH
- semiconductors / semiconductors co-occurrence: recurrence_count=3 windows=['120', '20', '60'] confidence=HIGH
- semiconductors remained persistent and coherent: recurrence_count=3 windows=['120', '20', '60'] confidence=HIGH

## Stable structural anchors
- group consumer_discretionary: stability_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- group semiconductors: stability_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- metric completeness_ratio: stability_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW
- metric contradiction_burden: stability_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW
- metric diversity_retention: stability_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW
- metric endpoint_failure_count: stability_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW
- metric failed_count: stability_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW
- metric foxa_weak_window_count: stability_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW
- metric monoculture_risk: stability_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW
- metric morphology_persistence: stability_score=1.0 window_coverage=0 evidence_count=1 confidence=LOW

## Unstable / drifting structures
- metric reconciled_date_ratio: drift_score=0.66668 window_coverage=0 evidence_count=1 confidence=LOW
- metric normalized_rows: drift_score=0.166667 window_coverage=0 evidence_count=1 confidence=LOW

## Replay-density leaders
- sector cloud_software_infrastructure: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- sector commodities: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- sector consumer_discretionary: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- sector energy_utilities: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- sector financials: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- sector healthcare_biotech: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- sector industrials_automation: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- sector semiconductors: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- subsector cloud_software_infrastructure: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH
- subsector commodities: replay_density_score=1.0 window_coverage=3 evidence_count=3 confidence=HIGH

## Limitations
- Analysis is limited to existing local artifacts and supplied observation facts; no live collection is performed.

## Recommended next phase
- Review the bounded findings and, if needed, add a fact-native adapter for additional historical observation fact snapshots without enabling live collection or activation.
