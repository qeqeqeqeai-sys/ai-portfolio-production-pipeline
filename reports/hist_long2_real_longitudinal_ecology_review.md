# HIST-LONG-2 — Real Multi-Window Longitudinal Ecology Review

## Real Artifact Sources
- Real completed telemetry used: True
- New real execution run: False
- Execution mode: completed_artifact_ingestion_only
- hist_density4_completed_241_symbol_20d_baseline: window_days=20, kind=completed_review_artifact, path=`artifacts/hist_density4_241_symbol_findings_review.json`

## Window-Level Ingestion Quality
- hist_density4_completed_241_symbol_20d_baseline: days=20, chunks=5, snapshots=100, normalized=4700/4820, completeness=0.975104, exact_ratio=0.95, reconciled_ratio=0.05, partial_failed={"failed_count_total": 20, "missing_dates_total": 20, "partial_count_total": 20}, weak=['PARA']

## Weak Symbol Recurrence
- [{"symbol": "PARA", "window_count": 1}]

## Provider Degradation Recurrence
- [{"reason": "HTTP_403", "window_count": 1}, {"reason": "zero_records_returned", "window_count": 1}]

## Replay/Topology Ecology Findings
- Replay density: {"activation_status": "not_activated", "trend": "insufficient_windows", "values": [0.975104]}
- Topology richness: {"persistence_status": "report_local_not_persisted", "trend": "insufficient_windows", "values": [2.0]}
- Morphology persistence: {"assessment": "single_window_or_mixed", "posture_recurrence": [{"posture": "stable_single_posture", "window_count": 1}]}

## Sector/Subsector Concentration Drift
- Sector HHI drift: {"trend": "insufficient_windows", "values": [0.582731]}
- Subsector HHI drift: {"trend": "insufficient_windows", "values": [0.582731]}
- Monoculture risk: ["Chunk density concentration requires follow-up review."]

## Temporal Stability and Decay
- {"assessment": "insufficient_real_multi_window_evidence", "density_decay": "insufficient_windows"}
- Historical date alignment: {"exact_date_ratio_values": [0.95], "exact_trend": "insufficient_windows", "reconciled_date_ratio_values": [0.05], "reconciled_trend": "insufficient_windows"}
- Contradiction persistence: {"burden_values": [0.012448], "trend": "insufficient_windows", "volatility": null}

## Operational Stability Assessment
- real_multi_window_status: only_one_completed_real_window_available
- foxa_validation_status: not_validated_by_completed_real_window
- provider_degradation_trend: [{"reason": "HTTP_403", "window_count": 1}, {"reason": "zero_records_returned", "window_count": 1}]
- recommendation: Run the next bounded real updated-universe 20d/60d windows before longer accumulation.

## Governance Certification
- Governance mode: observational_only
- Prediction enabled: False
- Trading execution enabled: False
- Replay activation enabled: False
- Replay execution enabled: False
- Topology persistence enabled: False
- Supabase writes enabled: False
- Raw cache writes enabled: False
- Local artifacts only: True

## Recommendation for next phase
- Proceed to a bounded real updated-universe validation window before 60d/120d accumulation; do not activate replay/topology/trading.
