# Tier 3B — Workflow Integration Pass

_Last updated: 2026-05-14_

## Purpose

Tier 3B introduces low-risk workflow integration patterns for the Tier 3A orchestration guardrails.

The goal is to gradually add:

- preflight freshness checks
- lineage start hooks
- lineage completion hooks
- dependency declarations
- same-date partition validation
- concurrency / replay safety locks

without rewriting existing GitHub Actions workflows.

## Operating principle

This pass is additive.

Do not change business logic, scoring formulas, graph algorithms, replay logic, or existing runtime entrypoints.

## Recommended rollout sequence

### Phase 1 — Low-risk operational workflows

1. `daily_ai_portfolio_pipeline.yml`
2. `phase1_ai_transmission_dual_write.yml`
3. `phase5a_two_hop_pipeline.yml`

### Phase 2 — Propagation chain workflows

4. `phase5a2_structural_intermediaries.yml`
5. `phase5b_propagation_corridor_pipeline.yml`
6. `phase5c_regime_corridor_dynamics_pipeline.yml`
7. `phase5d_structural_propagation_regime_forecasting_pipeline.yml`

### Phase 3 — Historical / replay workflows

8. `phase4e_historical_propagation_replay.yml`
9. `ai_transmission_phase2d2_reconstruction.yml`
10. `historical_source_backfill.yml`

Historical/replay workflows should be integrated later because they have higher collision risk.

## Integration pattern

Each workflow should eventually have this structure:

```yaml
steps:
  - name: Preflight orchestration guardrails
    run: |
      python -m core.orchestration_guardrails.cli preflight \
        --workflow-name "${{ github.workflow }}" \
        --run-id "${{ github.run_id }}" \
        --run-mode "${{ github.event_name }}"

  - name: Existing workflow logic
    run: |
      echo "Run existing production script here"

  - name: Finish lineage registration
    if: always()
    run: |
      python -m core.orchestration_guardrails.cli finish \
        --workflow-name "${{ github.workflow }}" \
        --run-id "${{ github.run_id }}" \
        --status "${{ job.status }}"
```

If the current CLI only supports `preflight`, add only the preflight step first and treat finish hooks as reserved placeholders.

## Required secrets

Recommended names:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Optional:

- `SUPABASE_ANON_KEY`
- `RUN_DATE_SGT`
- `GUARDRAILS_STRICT_MODE`

## Strictness levels

### Advisory mode

- Logs warnings.
- Does not fail the workflow.
- Best for first deployment.

### Soft-fail mode

- Fails only on critical errors.
- Warns on missing optional dependencies.

### Strict mode

- Fails on stale upstream data, missing same-date partitions, missing lineage, or lock collision.
- Use after several clean runs.

Recommended start:

```text
GUARDRAILS_STRICT_MODE=false
```

## Success criteria

Tier 3B is considered complete when:

- the first three workflows include preflight calls
- lineage registration has at least workflow-level start/completion coverage
- dependency guardrails are running in advisory mode
- no production pipeline behavior changes unexpectedly
- failures are understandable from the logs
