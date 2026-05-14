# Incident Response Runbook

**Status:** Initial governance baseline  
**Owner:** Platform Orchestration Team  
**Last reviewed:** 2026-05-14  
**Scope:** Production-impacting workflow, data, scoring, ingestion, Supabase, Streamlit, and orchestration incidents.

---

## 1. Purpose

This runbook provides a lightweight incident response process for the modular structural transmission research platform.

It is designed for practical use during failures without requiring heavy enterprise incident management overhead.

---

## 2. Incident definition

An incident is any event that causes or may cause:

- Failed production scoring pipeline
- Missing daily data
- Corrupted or duplicated Supabase writes
- Incorrect dashboard output
- Failed historical replay or backfill
- Broken validation gates
- Accidental workflow dual-runs
- Secret exposure risk
- API quota exhaustion affecting production jobs

---

## 3. Severity levels

| Severity | Definition | Example | Response |
|---|---|---|---|
| SEV-1 | Core production pipeline broken or bad data written to core tables | Main daily scoring produces invalid outputs | Stop affected workflow, assess data writes, rollback if needed |
| SEV-2 | Important support signal or dashboard degraded | Macro stress signal missing | Retry or backfill when safe |
| SEV-3 | Research, archive, or non-critical job failed | Research backfill failed | Fix during normal development |
| SEV-4 | Documentation, naming, or governance issue only | Missing registry entry | Update docs |

---

## 4. First response checklist

When something fails:

- [ ] Identify affected workflow or script
- [ ] Identify whether it is GitHub Actions, n8n, Python, Supabase, or Streamlit
- [ ] Check the first failing step or node
- [ ] Determine whether any database writes occurred
- [ ] Determine whether retry is safe
- [ ] Check whether downstream dashboards are affected
- [ ] Check whether external API limits or credentials caused the issue
- [ ] Record the incident in the relevant runbook or notes

---

## 5. System-specific checks

### GitHub Actions

Check:

- Failed step
- Python traceback
- Missing secret errors
- Dependency installation errors
- Changed file paths
- Schedule/manual trigger behavior
- Whether previous run succeeded

### n8n

Check:

- Failed node
- Credential errors
- API rate limits
- HTTP response status
- Item-linking / merge issues
- Code node exceptions
- Partial Supabase writes

### Python

Check:

- Import path errors
- Schema mismatch errors
- Memory errors
- Pagination issues
- Retry/upsert behavior
- Environment variables

### Supabase

Check:

- Duplicate key violations
- RLS/policy issues
- Missing columns
- Type mismatches
- Constraint failures
- Partial writes

### Streamlit

Check:

- Query filters
- RLS/anon key access
- Missing data due to pipeline failure
- Broken import paths
- Dashboard-only issues vs data issues

---

## 6. Retry decision guide

Retry is usually safe when:

- Writes use upsert with unique keys
- Run date is fixed and idempotent
- Failure occurred before writes
- External API failure was temporary
- No schema or logic change occurred

Retry is risky when:

- Tables are append-only without unique constraints
- Workflow sends notifications
- Stateful checkpoints were updated
- Multi-step workflow partially completed
- Backfill jobs wrote only partial date ranges

---

## 7. Rollback order

Preferred rollback sequence:

1. Disable schedule or pause workflow if repeated failures occur.
2. Revert the most recent code/YAML/workflow change.
3. Restore previous known-good Python entrypoint.
4. Re-run validation gates.
5. Re-run affected workflow only if retry is safe.
6. Repair or delete bad data only after identifying exact affected rows.

Avoid broad table truncation unless the affected data range and downstream impact are clearly understood.

---

## 8. Bad data response

If bad data was written:

- Identify affected table(s)
- Identify affected `run_date_sgt` or timestamp range
- Identify affected symbols/themes/entities
- Check downstream derived tables
- Prefer targeted deletion or correction
- Document the repair query if SQL was used
- Re-run validation after repair

---

## 9. Secret exposure response

If a real secret may have been committed or exposed:

1. Treat it as compromised.
2. Rotate the secret at the provider.
3. Update GitHub Actions / n8n / Streamlit / Supabase secret stores.
4. Remove secret from repository history if necessary.
5. Review related logs.
6. Update `docs/governance/secrets-governance.md`.

Do not paste real secret values into incident notes.

---

## 10. Post-incident review

After resolution, record:

- What failed
- Root cause
- Affected workflows
- Affected tables
- Whether data was repaired
- Whether retry was safe
- What guardrail should be added
- Which documentation needs updating

Minimum updates after relevant incidents:

- `docs/runbooks/workflow-registry.md`
- `docs/runbooks/github-actions-ops.md`
- `docs/runbooks/n8n-ops.md`
- `docs/governance/secrets-governance.md`, if credentials were involved
