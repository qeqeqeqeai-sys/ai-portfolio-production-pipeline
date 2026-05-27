# OPS-LIVE-1B Daily Observation GitHub Actions Workflow

## Workflow file
- `.github/workflows/ops_live1b_daily_observation.yml`

## Purpose
Run a bounded, controlled daily 50-symbol OPS-LIVE-1B ingestion and immediate OPS-LIVE-1B-OBS snapshot review in GitHub Actions, then publish generated outputs as artifacts.

## Trigger model
- `workflow_dispatch` for manual execution.
  - Optional `snapshot_date` input in `YYYY-MM-DD` for deterministic backtesting-style reproducibility within the bounded observation routine.
- `schedule` daily cron at `20 2 * * *` (02:20 UTC).

## Workflow metadata variables (informational only)
- `OBSERVATION_MODE=controlled_operational_observation`
- `OPS_PHASE=OPS_LIVE_1B_DAILY`
- `GOVERNANCE_MODE=observational_only`
- `SNAPSHOT_OUTPUT_DIR=reports/ops_live1b_runs`

These metadata variables are traceability-only and do not alter ingestion/review behavior, persistence, or scheduling boundaries.

## Runtime sequence
1. Checkout repository and set up Python 3.11.
2. Resolve `SNAPSHOT_DATE`:
   - Uses `workflow_dispatch.inputs.snapshot_date` when provided.
   - Otherwise defaults to current UTC date (`date -u +%F`).
3. Execute OPS-LIVE-1B controlled ingest:
   - `scripts/run_ops_live1b_50_symbol_operational_ingest.py`
   - Output: `reports/ops_live1b_runs/ops_live1b_<SNAPSHOT_DATE>.json`
4. Execute OPS-LIVE-1B-OBS review:
   - `scripts/run_ops_live1b_snapshot_observation_review.py`
   - Outputs:
     - `reports/ops_live1b_snapshot_observation_review.json`
     - `reports/ops_live1b_snapshot_observation_review.md`
5. Generate lightweight deterministic manifest:
   - `reports/ops_live1b_daily_artifact_manifest.json`
6. Upload all generated outputs as GitHub Actions artifacts.

## Artifact retention guidance
- Upload step sets explicit bounded retention:
  - `retention-days: 14`
- No automatic repo cleanup is implemented.
- No local report deletion behavior is implemented.

## Artifact manifest purpose and fields
`reports/ops_live1b_daily_artifact_manifest.json` captures bounded run metadata for traceability only:
- workflow name
- ops phase
- observation mode
- governance mode
- snapshot date
- generated artifact paths
- snapshot output path
- review JSON path
- review markdown path
- retention guidance
- governance booleans:
  - `no_supabase_write=true`
  - `no_repo_writeback=true`
  - `no_replay=true`
  - `no_topology_activation=true`
  - `no_prediction_or_trading_execution=true`
  - `no_streaming=true`

Manifest guarantees:
- local artifact output only,
- deterministic for given date and paths,
- no secret values,
- no `FMP_API_KEY` payload,
- no additional workflow behavior.

## Secrets and credentials
- Reads `FMP_API_KEY` **only** from GitHub repository secrets via workflow env:
  - `FMP_API_KEY: ${{ secrets.FMP_API_KEY }}`
- Workflow fails fast if `FMP_API_KEY` is missing.

## Governance boundaries (explicit)
This workflow is intentionally bounded and does **not**:
- write to Supabase,
- commit or push generated outputs,
- trigger replay,
- activate topology workflows,
- introduce orchestration beyond this single workflow,
- introduce streaming behavior,
- execute prediction/trading logic.

## Artifact outputs
- `reports/ops_live1b_runs/ops_live1b_<SNAPSHOT_DATE>.json`
- `reports/ops_live1b_snapshot_observation_review.json`
- `reports/ops_live1b_snapshot_observation_review.md`
- `reports/ops_live1b_daily_artifact_manifest.json`

Artifact name pattern:
- `ops-live1b-daily-observation-<github.run_id>`

Generated outputs are uploaded as artifacts only and are **not** committed back to the repository.
