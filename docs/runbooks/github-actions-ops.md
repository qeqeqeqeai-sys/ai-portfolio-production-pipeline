# GitHub Actions Operations Runbook

**Status:** Initial governance baseline  
**Owner:** Platform Orchestration Team  
**Last reviewed:** 2026-05-14  
**Scope:** GitHub Actions workflows used for orchestration, validation, replay, telemetry, and scheduled platform jobs.

---

## 1. Purpose

This runbook defines operational expectations for GitHub Actions workflows in the modular structural transmission research platform.

GitHub Actions should act as the platform control plane for:

- Scheduled Python jobs
- Phase sequencing
- Validation gates
- Historical replay jobs
- Backfill jobs
- Pipeline telemetry
- Operational notifications

---

## 2. GitHub Actions role

GitHub Actions is responsible for orchestration, not business logic.

### GitHub Actions should handle

- Scheduling
- Manual dispatch
- Job sequencing
- Secret injection
- Environment setup
- Dependency installation
- Validation gates
- Notifications
- Failure visibility

### GitHub Actions should not handle

- Scoring formulas
- Graph propagation logic
- Regime classification logic
- Data model definitions
- Supabase schema changes without checked-in SQL
- Complex data transformation inside YAML

---

## 3. Current operational workflow categories

| Category | Description | Example |
|---|---|---|
| Daily production | Main recurring scoring and telemetry pipelines | `daily_ai_portfolio_pipeline.yml` |
| Historical replay | Manual or scheduled historical reconstruction/backfill | `phase4e_historical_propagation_replay.yml` |
| Validation | Data quality, runtime, schema, and telemetry checks | Validation gate workflows/scripts |
| Research/backfill | One-off or controlled batch jobs | Historical source loaders |
| Utility | Diagnostics, operational support, or maintenance | Pipeline metrics writers |

---

## 4. Minimum workflow header standard

Each GitHub Actions YAML file should include comments or nearby documentation covering:

```yaml
# Purpose:
# Owner:
# Trigger:
# Reads from:
# Writes to:
# Required secrets:
# Failure impact:
# Rollback:
```

If inline comments become too noisy, document the details in `docs/runbooks/workflow-registry.md`.

---

## 5. Required operational fields for each workflow

Each workflow should be documented with:

- Workflow filename
- Owner
- Trigger type
- Schedule frequency
- Manual dispatch availability
- Python entrypoint, if any
- Required secrets
- Required external APIs
- Supabase tables read
- Supabase tables written
- Expected runtime
- Failure severity
- Notification behavior
- Rollback or retry procedure

---

## 6. Secret handling expectations

Secrets should be read from GitHub Actions repository secrets, not hardcoded in YAML or Python files.

Recommended pattern:

```yaml
env:
  SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
  SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  FMP_API_KEY: ${{ secrets.FMP_API_KEY }}
```

Rules:

1. Never commit real secret values.
2. Use consistent variable names across workflows where possible.
3. Document every required secret in `docs/governance/secrets-governance.md`.
4. Fail early if a required secret is missing.
5. Avoid printing environment variables in logs.

---

## 7. Workflow change checklist

Before changing a GitHub Actions workflow, confirm:

- [ ] Does this change affect schedule timing?
- [ ] Does this change affect Python entrypoints?
- [ ] Does this change affect required secrets?
- [ ] Does this change affect Supabase tables written?
- [ ] Does this change affect downstream Streamlit dashboards?
- [ ] Does this change affect n8n dependencies?
- [ ] Has the workflow registry been updated?
- [ ] Is rollback simple?

---

## 8. Failure handling

### If a production workflow fails

1. Check whether the failure is dependency, secret, API, schema, or code-related.
2. Confirm whether Supabase tables were partially written.
3. Review logs for the first failing step, not only the final job status.
4. Check whether retry is safe.
5. Update the workflow registry if the failure reveals an undocumented dependency.

### Safe retry conditions

Retry is usually safe when:

- Writes are idempotent or upsert-based
- The failed step occurred before database writes
- The workflow has clear run-date isolation
- Duplicate key handling is already implemented

Retry requires caution when:

- The workflow appends rows without unique constraints
- The workflow performs multi-table writes
- The workflow updates stateful checkpoint tables
- The workflow sends external notifications

---

## 9. Rollback guidance

Preferred rollback order:

1. Revert the workflow YAML change.
2. Revert Python entrypoint changes if needed.
3. Disable the schedule temporarily if repeated failures occur.
4. Restore previous known-good workflow version.
5. Only perform database rollback if table corruption or bad writes occurred.

Avoid emergency renames or folder moves during incident response.

---

## 10. Governance rule

No GitHub Actions workflow should become production-critical unless it is documented in:

- `docs/runbooks/workflow-registry.md`
- `docs/governance/orchestration-boundaries.md`, if it changes control-plane responsibilities
- `docs/governance/secrets-governance.md`, if it uses new secrets
