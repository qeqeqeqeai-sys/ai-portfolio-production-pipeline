# Workflow Integration Checklist

Use this checklist before adding Tier 3B guardrails to any GitHub Actions workflow.

## 1. Workflow identity

- [ ] Workflow name is stable.
- [ ] Workflow has known owner.
- [ ] Workflow has known trigger type: scheduled, manual, dispatch, or chained.
- [ ] Workflow has documented run mode.

## 2. Upstream dependencies

- [ ] Required upstream tables identified.
- [ ] Required upstream workflows identified.
- [ ] Same-date partition requirements identified.
- [ ] Minimum row count requirements identified.
- [ ] Freshness SLA identified.

## 3. Downstream outputs

- [ ] Tables written are identified.
- [ ] Expected row count range is known.
- [ ] Output partition date logic is known.
- [ ] Consumers of outputs are identified.

## 4. Guardrail insertion

- [ ] Preflight step inserted before first mutating step.
- [ ] Lineage start hook inserted before main execution.
- [ ] Completion hook inserted with `if: always()`.
- [ ] Failure summary is captured.
- [ ] Guardrail mode starts as advisory.

## 5. Secrets and environment

- [ ] `SUPABASE_URL` is available.
- [ ] `SUPABASE_SERVICE_ROLE_KEY` is available.
- [ ] No secrets are printed.
- [ ] Manual runs expose safe input defaults.

## 6. Rollback

- [ ] Guardrail steps can be disabled by environment flag.
- [ ] Existing core script entrypoint remains unchanged.
- [ ] No file path rename is required.
- [ ] No schema change is required beyond Tier 3A tables/functions.

## 7. First-run validation

- [ ] Workflow runs successfully in advisory mode.
- [ ] Preflight summary appears in logs.
- [ ] No existing output behavior changes.
- [ ] Lineage row is created or simulated as expected.
- [ ] Completion/failure hook does not mask the original failure.
