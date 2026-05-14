# Tier 3B GitHub Actions Rollout Runbook

## Objective

Safely integrate orchestration guardrails into GitHub Actions workflows.

## Rollout policy

Start in advisory mode.

```yaml
GUARDRAILS_STRICT_MODE: "false"
```

Do not promote to strict mode until at least three clean scheduled runs have completed.

## Step-by-step rollout

### Step 1 — Add preflight only

Add the preflight snippet to one workflow.

Recommended first workflow:

```text
daily_ai_portfolio_pipeline.yml
```

### Step 2 — Run manually

Use `workflow_dispatch` where available.

Check that:

- the workflow starts
- the preflight command runs
- logs show structured summary
- the workflow still completes
- no existing business logic changes

### Step 3 — Observe scheduled run

Let at least one scheduled run complete.

Check:

- no false hard failures
- warnings are understandable
- timing impact is small
- no secrets are printed

### Step 4 — Add to second workflow

Recommended second workflow:

```text
phase1_ai_transmission_dual_write.yml
```

### Step 5 — Add to first propagation workflow

Recommended third workflow:

```text
phase5a_two_hop_pipeline.yml
```

## Rollback

Remove or comment out only the Tier 3B preflight step.

No runtime files, core scripts, scoring modules, or SQL tables need to be rolled back.

## Promotion to strict mode

Promote only one workflow at a time.

Suggested order:

1. `daily_ai_portfolio_pipeline.yml`
2. `phase1_ai_transmission_dual_write.yml`
3. `phase5a_two_hop_pipeline.yml`

Strict mode should require:

- required upstream lineage exists
- required upstream partitions exist
- minimum row counts pass
- no lock collision
- same-date policy passes

## Do not use strict mode yet for

- historical replay
- reconstruction
- backfills
- manual graph repair workflows
- experimental research workflows
