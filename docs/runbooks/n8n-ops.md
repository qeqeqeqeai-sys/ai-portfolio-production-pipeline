# n8n Operations Runbook

**Status:** Initial governance baseline  
**Owner:** Workflow Automation Team  
**Last reviewed:** 2026-05-14  
**Scope:** n8n workflow exports, production automations, research workflows, archived workflows, connector dependencies, and workflow lifecycle governance.

---

## 1. Purpose

This runbook defines how n8n workflows should be governed, documented, reviewed, and operated in this repository.

n8n is used primarily as an ingestion and automation layer. It connects external APIs, prepares payloads, and coordinates lightweight automation steps.

---

## 2. n8n role in the platform

n8n should act as the connector and workflow edge layer.

### n8n should handle

- External API polling
- Lightweight payload normalization
- API connector orchestration
- Scheduled or manual ingestion workflows
- Notification routing
- Calling stable Python or HTTP entrypoints where appropriate

### n8n should avoid

- Heavy scoring formulas
- Multi-hop propagation logic
- Complex regime classification
- Large embedded business logic in Code nodes
- Long-lived source-of-truth computation logic
- Hardcoded secret values or project-specific credentials in exported JSON

---

## 3. Workflow lifecycle states

| State | Meaning | Scheduling rule |
|---|---|---|
| Production | Active and operationally relied upon | May be scheduled |
| Production Support | Supports production but is not the main spine | May be scheduled with documentation |
| Validation | Used for QA, checks, or diagnostics | Scheduled or manual depending on purpose |
| Research | Experimental or exploratory | Manual only unless promoted |
| Archive | Legacy reference or rollback artifact | Must not be scheduled |
| Retired | No longer used | Should have replacement documented |

---

## 4. Recommended n8n workflow header convention

Every exported workflow should have a corresponding entry in `docs/runbooks/workflow-registry.md`.

Where possible, add an internal Sticky Note or documentation node in n8n with:

```text
Purpose:
Owner:
Status:
Trigger:
Inputs:
Outputs:
Supabase tables read:
Supabase tables written:
Secrets / credentials used:
External APIs:
Failure impact:
Replacement / successor:
```

---

## 5. Naming convention

Current workflow names may remain unchanged to avoid operational disruption.

For new workflows, use:

```text
<Tier> - <Domain> - <Action>.json
```

Allowed tiers:

- `Production`
- `Production Support`
- `Validation`
- `Research`
- `Archive`

Examples:

```text
Production - AI Transmission - Daily Evidence Ingestion.json
Production Support - Macro Regime - Stress Signal Engine.json
Research - Fundamentals - Historical Factor Builder.json
Archive - AI Transmission - Legacy Sector Monitor.json
```

---

## 6. Credential and secret governance

Rules:

1. Do not commit real API keys in exported JSON.
2. Use n8n credentials wherever possible.
3. Use placeholder names only in repository exports.
4. Document required credentials in `docs/governance/secrets-governance.md`.
5. Do not manually paste real keys into Code nodes.
6. Avoid direct header construction with secrets inside Code nodes where credential nodes can be used.

High-risk patterns:

- `apiKey = "..."`
- `Authorization: Bearer <real token>`
- Supabase service-role keys in HTTP headers inside JSON exports
- Provider keys embedded in Code node JavaScript

---

## 7. Code node policy

Code nodes are allowed, but should be treated carefully.

### Acceptable Code node usage

- Lightweight field normalization
- Simple fallback handling
- Payload reshaping
- Small calculations for routing
- Defensive null handling

### Avoid in Code nodes

- Canonical scoring formulas
- Multi-step regime logic
- Graph propagation algorithms
- Backtest logic
- Large repeated transformations
- Logic that should be unit-tested in Python

### Migration direction

Over time, repeated or high-value business logic should move from n8n Code nodes into Python modules, while n8n remains the orchestration/connector layer.

---

## 8. Trigger governance

For every n8n workflow, document:

- Manual trigger availability
- Schedule trigger frequency
- Whether a GitHub Actions workflow also triggers related logic
- Whether dual execution is possible
- Whether duplicate writes are safe

Avoid hidden dual-run situations where both GitHub Actions and n8n independently trigger the same logical pipeline.

---

## 9. Archive policy

Archived workflows should remain available for reference, but must not be scheduled.

For each archived workflow, document:

- Why it was archived
- Last known working date, if known
- Replacement workflow or module
- Whether it can be safely reactivated
- Required credentials, if reactivation is needed

Archived workflows should appear in `docs/runbooks/workflow-registry.md` with status `Archived`.

---

## 10. Promotion policy

Before a Research workflow becomes Production:

- [ ] Add it to the workflow registry
- [ ] Document owner and trigger
- [ ] Document required credentials
- [ ] Confirm no real secrets are in JSON export
- [ ] Confirm Supabase tables read/written
- [ ] Confirm failure impact
- [ ] Confirm duplicate-run behavior
- [ ] Confirm whether logic belongs in Python instead
- [ ] Test with non-production or bounded inputs

---

## 11. Operational failure checklist

When an n8n production workflow fails:

1. Identify whether the failure is caused by API limits, credentials, payload shape, Supabase write errors, or Code node logic.
2. Check whether partial writes occurred.
3. Check whether retry is idempotent.
4. Review external API rate limits before rerunning.
5. Confirm downstream dashboards or GitHub Actions pipelines are not relying on incomplete data.
6. Update the registry if the failure reveals an undocumented dependency.

---

## 12. Governance rule

No n8n workflow should be considered production-governed unless it has:

- Registry entry
- Owner
- Status
- Trigger documentation
- Credential documentation
- Downstream write documentation
- Failure impact classification
