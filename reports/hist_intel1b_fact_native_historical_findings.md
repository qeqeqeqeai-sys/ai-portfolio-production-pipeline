# HIST-INTEL-1B Fact-Native Historical Findings Expansion

## Objective
Mine local SEFI observation facts and compact local artifacts for ecosystem findings while preserving analysis-only governance.

## Governance certification
- analysis_only: true
- local_only: true
- no_provider_calls: true
- no_supabase_writes: true
- no_prediction: true
- no_trading: true
- no_portfolio_recommendation: true
- no_governed_activation: true

## Executive summary
- Persistent hub: sector cloud infrastructure scored 1.0 with 2 fact rows across 2 windows (HIGH confidence).
- Cross-window persistence leader: sector cloud infrastructure scored 1.0 with 2 fact rows across 2 windows (HIGH confidence).
- Stable ecosystem anchor: sector cloud infrastructure scored 1.0 with 2 fact rows across 2 windows (HIGH confidence).
- Stable ecosystem anchor: subsector edge ai scored 0.92 with 1 fact rows across 1 windows (LOW confidence).
- Replay-density leader: subsector edge ai scored 0.92 with 1 fact rows across 1 windows (LOW confidence).
- Fragility source: symbol thin-breadth cohort scored 0.84 with 1 fact rows across 1 windows (LOW confidence).
- Drift/instability leader: sector legacy media scored 0.54 with 1 fact rows across 1 windows (LOW confidence).

## Fact-native persistent hubs
- sector cloud infrastructure: persistence_score=1.0 evidence_count=2 window_coverage=2 phase_coverage=1 confidence=HIGH

## Fact-native fragility sources
- symbol thin-breadth cohort: fragility_score=0.84 evidence_count=1 window_coverage=1 phase_coverage=1 confidence=LOW

## Cross-window persistence leaders
- sector cloud infrastructure: cross_window_score=1.0 evidence_count=2 window_coverage=2 phase_coverage=1 confidence=HIGH

## Drift and instability leaders
- sector legacy media: drift_score=0.54 evidence_count=1 window_coverage=1 phase_coverage=1 confidence=LOW

## Replay-density and recurrence leaders
- subsector edge ai: replay_density_score=0.92 evidence_count=1 window_coverage=1 phase_coverage=1 confidence=LOW

## Stable ecosystem anchors
- sector cloud infrastructure: stability_score=1.0 evidence_count=2 window_coverage=2 phase_coverage=1 confidence=HIGH
- subsector edge ai: stability_score=0.92 evidence_count=1 window_coverage=1 phase_coverage=1 confidence=LOW

## Observation-pattern clusters
- persistence_score / sector / hist-long-8: evidence_count=2 window_coverage=2 confidence=HIGH
- emerging_fragility_score / symbol / hist-long-9: evidence_count=1 window_coverage=1 confidence=LOW
- morphology_drift_score / sector / hist-long-9: evidence_count=1 window_coverage=1 confidence=LOW
- replay_density / subsector / hist-long-9: evidence_count=1 window_coverage=1 confidence=LOW

## Suppressed pipeline diagnostics
- normalized_rows (pipeline): suppressed_count=1 reason=pipeline diagnostic excluded from executive ecosystem findings
- reconciled_date_ratio (diagnostic): suppressed_count=1 reason=pipeline diagnostic excluded from executive ecosystem findings

## Limitations
- Analysis is local-only and bounded to supplied observation facts plus optional compact local artifacts; no live collection or governed workflow activation is performed.
- Pipeline diagnostics were detected and suppressed from the executive summary when ecosystem facts were available.
