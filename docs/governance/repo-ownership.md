# Repository Ownership

**Purpose:** Define ownership boundaries for the modular structural transmission research platform.

**Last reviewed:** 2026-05-14  
**Status:** Initial governance baseline  
**Scope:** Repository-wide

---

## 1. Ownership Principles

This repository contains multiple operating layers:

- Python engines
- n8n workflow exports
- GitHub Actions orchestration
- Supabase persistence
- Streamlit dashboards
- Structural graph and propagation layers
- AI transmission scoring and replay components

Ownership should follow system responsibility, not file age or implementation history.

Core principles:

1. Every production-facing component must have an owner.
2. Each owner is responsible for correctness, change review, and operational risk.
3. Cross-layer changes require explicit review of downstream effects.
4. Legacy components should remain documented until retired.
5. Working execution paths should not be renamed or moved without migration review.

---

## 2. Ownership Boundaries

| Layer | Scope | Owner Role | Responsibility |
|---|---|---|---|
| AI Transmission | `ai_transmission/`, `transmission_layers/ai_transmission/` | AI Transmission Owner | Scoring logic, evidence ingestion, replay integrity, legacy compatibility |
| Structural Graph | `transmission_layers/graph_foundation/`, `transmission_layers/phase5a_two_hop/` | Graph Intelligence Owner | Graph evolution, propagation layers, corridor/regime engines |
| Orchestration | `.github/workflows/`, `pipelines/`, selected `scripts/` | Platform Orchestration Owner | Trigger sequencing, scheduled jobs, retries, execution gates |
| n8n Workflows | `n8n/` | Workflow Automation Owner | API connectors, ingestion automations, workflow exports, n8n operational health |
| Data Platform | `database/`, Supabase schema/policies | Data Platform Owner | Table contracts, migrations, RLS, indexes, schema compatibility |
| Dashboards | Streamlit apps under project folders | Analytics Experience Owner | Read-only observability, dashboard stability, presentation logic |
| Shared Utilities | `utils/`, `transmission_layers/shared/` | Shared Platform Owner | Reusable REST clients, retry logic, telemetry utilities, helper functions |
| Documentation | `docs/` | Repository Governance Owner | Architecture docs, governance rules, runbooks, registries |

---

## 3. Change Ownership Rules

### Python engine changes

Requires review from the relevant domain owner if the change affects:

- scoring output
- propagation logic
- historical replay results
- database writes
- telemetry generation
- API fetch behaviour

### n8n workflow changes

Requires review if the change affects:

- workflow trigger timing
- external API calls
- item merge/split logic
- Supabase writes
- credential usage
- production workflow activation state

### GitHub Actions changes

Requires review if the change affects:

- schedule frequency
- workflow dependencies
- secrets usage
- script paths
- failure behaviour
- notification behaviour

### Supabase/database changes

Requires review if the change affects:

- table schemas
- unique constraints
- indexes
- RLS policies
- stored functions
- views used by Streamlit or workflows

---

## 4. Suggested CODEOWNERS Baseline

This can be added later as `.github/CODEOWNERS` when ready.

```text
# Governance and docs
/docs/ @repo-governance-owner

# GitHub Actions and orchestration
/.github/workflows/ @platform-orchestration-owner
/scripts/ @platform-orchestration-owner
/pipelines/ @platform-orchestration-owner

# n8n workflow exports
/n8n/ @workflow-automation-owner

# AI transmission
/ai_transmission/ @ai-transmission-owner
/transmission_layers/ai_transmission/ @ai-transmission-owner

# Structural graph and propagation layers
/transmission_layers/graph_foundation/ @graph-intelligence-owner
/transmission_layers/phase5a_two_hop/ @graph-intelligence-owner

# Database assets
/database/ @data-platform-owner

# Shared utilities
/utils/ @shared-platform-owner
/transmission_layers/shared/ @shared-platform-owner
```

Replace placeholder owner handles with real GitHub usernames or team names later.

---

## 5. Escalation Rules

Use escalation when:

- production workflows fail repeatedly
- schema changes break dashboards or workflows
- API credentials appear exposed
- scoring results change materially without explanation
- replay/backfill output diverges from expected historical records
- GitHub Actions and n8n both appear to control the same schedule

Escalation path:

1. Identify affected layer.
2. Identify owner from this document.
3. Check workflow registry and source-of-truth document.
4. Review recent commits affecting the layer.
5. Roll back only after confirming runtime path and downstream tables.

---

## 6. Current Governance Status

| Area | Status | Notes |
|---|---|---|
| Ownership model | Initial | Needs real GitHub owner handles later |
| CODEOWNERS | Not yet active | Recommended after docs are stable |
| Workflow registry | Pending | Should be created under `docs/runbooks/` |
| Data contracts | Pending | Supabase table docs should be added later |
| Migration process | Pending | Add `database/migrations/` when ready |

---

## 7. Near-Term Actions

1. Keep this document updated when new major layers are added.
2. Add real owner names or GitHub handles when the repository has collaborators.
3. Create workflow registry for GitHub Actions and n8n workflows.
4. Add CODEOWNERS only after ownership rules are accepted.
5. Revisit ownership boundaries after each major phase.
