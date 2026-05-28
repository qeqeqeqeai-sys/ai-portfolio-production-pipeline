# Stage 3 Failure/Missing-Date Audit (Quick)

Date: 2026-05-28 (UTC)
Scope: Stage 3 staged chunk pilot failure/missing-date audit only.

## Artifacts/logs inspected
- `reports/hist_density3_stage3_chunk_pilot_execution_report.md`
- `transmission_layers/expectation_failure/real_data/ops_hist1_controlled_historical_observation.py`

## Evidence status
The repository does **not** contain Stage 3 runtime artifacts for a completed 50x20 execution (e.g., no `ops_hist1_YYYY-MM-DD.json` snapshot files under a Stage 3 output directory, and no committed Stage 3 telemetry JSON with symbol/date-level failures).

The only Stage 3 report in-repo states Stage 3 was fail-closed / not executed in that environment.

## What can be concluded from implementation semantics
From `ops_hist1_controlled_historical_observation.py` telemetry logic:
- `missing_dates` is incremented per **symbol-date row** when no exact/prior-date reconciliation is available after endpoint attempts.
- `reconciled_prior_dates` is incremented per **symbol-date row** where prior-date reconciliation succeeded.
- `endpoint_failure_counts` is incremented both:
  1. once for the terminal failure in rows with no successful attempt, and
  2. once for **each failed endpoint attempt** across all attempts.

Therefore endpoint failure counters can exceed final missing rows and represent attempt-level accounting, not necessarily final-row failure counts.

## Requested symbol/date attribution
### missing_dates = 20
Unable to enumerate exact symbols/dates from in-repo artifacts (missing symbol/date-level Stage 3 runtime telemetry).

### HTTP_403 = 40
Unable to enumerate exact symbols/dates from in-repo artifacts.

### zero_records_returned = 40
Unable to enumerate exact symbols/dates from in-repo artifacts.

## Interpretation of provided counters (conditional)
If external telemetry values are accurate (`planned=1000`, `successful=980`, `missing_dates=20`, `reconciled_prior_dates=98`, failure counts 40/40):
- Final missing symbol-date rows are likely 20 (1000 - 980), consistent with row-level `missing_dates` semantics.
- `HTTP_403=40` and `zero_records_returned=40` likely represent **failed endpoint attempts**, potentially multiple attempts per some rows, not necessarily 80 distinct final missing rows.

## Governance checks (from available report)
The in-repo Stage 3 execution report certifies (for that recorded environment):
- no cache writes
- no replay/topology activation
- no cognition/replay/topology persistence
- no Supabase writes

## Acceptability & Stage 4 gate
Given missing Stage 3 symbol/date-level runtime artifacts in this repository, Stage 3 data-quality certification is **incomplete** for expansion-governance purposes.

Recommendation:
- Stage 4 should **not** proceed on the basis of current in-repo evidence alone.
- Stage 4 may proceed only after bounded telemetry completion proving symbol/date-level attribution for missing and failed attempts.

## Smallest bounded telemetry enhancement required
Add one append-only Stage 3 artifact containing one row per symbol-date with:
- `symbol`, `requested_date`, `resolved_date`, `resolution_type` (`exact|prior|missing`)
- `attempt_count`
- `attempt_chain` (ordered endpoint family + failure reason per attempt)
- `final_status` (`normalized|missing`)

This can be emitted from existing `historical_price_symbol_diagnostics` during Stage 3 run finalization, without architecture changes, replay/topology/cognition activation, cache writes, or Supabase persistence.

## Stage 4 sizing once telemetry is present
- Conservative: 50 symbols x 20 trading days (repeat Stage 3 settings for one more verified run).
- Normal: 100 symbols x 20 trading days, with same governance flags and mandatory symbol/date telemetry export.
