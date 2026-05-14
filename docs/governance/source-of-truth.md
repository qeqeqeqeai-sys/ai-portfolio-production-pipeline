# Source of Truth Matrix

**Purpose:** Define which system owns each category of logic, configuration, and runtime behaviour.

**Last reviewed:** 2026-05-14  
**Status:** Initial governance baseline  
**Scope:** Python, n8n, GitHub Actions, Supabase, Streamlit, documentation

---

## 1. Core Rule

Each important concern should have one canonical source of truth.

When two systems appear to define the same thing, the repository should explicitly decide which system is primary and which system is downstream, trigger-only, or read-only.

---

## 2. Source of Truth Matrix

| Concern | Source of Truth | Secondary / Consumer Systems | Notes |
|---|---|---|---|
| Production job schedules | GitHub Actions YAML or n8n trigger, depending on workflow | Docs/runbooks | Avoid dual scheduling unless documented |
| Phase sequencing | GitHub Actions workflow files | Python scripts | Python should not secretly orchestrate unrelated phases |
| External API ingestion wiring | n8n workflow exports or Python fetch scripts | GitHub Actions | Depends on workflow design; document per workflow |
| Scoring formulas | Python modules | n8n, Streamlit | n8n should not become the canonical scoring layer |
| Structural propagation logic | Python modules under `transmission_layers/` | GitHub Actions | Python owns computation and graph logic |
| Corridor/regime intelligence | Python modules under graph/propagation folders | Streamlit | Streamlit should display, not compute canonical results |
| Historical replay/backfill logic | Python replay/backfill engines | GitHub Actions | Actions trigger replay; Python defines replay mechanics |
| Persistent state | Supabase tables | Python, n8n, Streamlit | Database schema should be documented under `database/` and `docs/data-contracts/` |
| Table schema and indexes | SQL files and Supabase schema docs | Python/n8n/Streamlit | Avoid undocumented schema edits |
| RLS and data access policy | Supabase policy definitions | Streamlit/Python | Dashboard access assumptions must be documented |
| Dashboard presentation | Streamlit app files | Supabase views/tables | Streamlit is read-focused observability |
| Environment variables | GitHub Secrets, n8n credentials, Streamlit secrets | `.env.example`, docs | Real secret values must not be committed |
| Operational runbooks | `docs/runbooks/` | GitHub issues/PR notes | Runbooks explain how to operate and recover |
| Governance policy | `docs/governance/` | CODEOWNERS, PR template | Governance docs define rules before automation enforces them |

---

## 3. Boundary Decisions

### n8n

n8n should primarily own:

- external connector wiring
- API request chains
- lightweight payload normalization
- routing between external services and stable internal entrypoints

n8n should not be the long-term source of truth for:

- scoring algorithms
- graph propagation mechanics
- replay methodology
- multi-step platform orchestration where GitHub Actions already controls the job

### GitHub Actions

GitHub Actions should primarily own:

- scheduled pipeline execution
- phase ordering
- CI-style validation
- production job control
- secret availability checks
- operational notifications

GitHub Actions should not own:

- scoring calculations
- business logic
- schema definitions beyond invoking checked-in SQL or scripts

### Python

Python should primarily own:

- scoring logic
- transformation logic
- graph evolution
- propagation mechanics
- regime/corridor inference
- replay/backfill computation
- validation gates

Python should avoid:

- hidden schedule ownership
- hardcoded secrets
- undocumented schema mutation

### Supabase

Supabase should primarily own:

- persistent state
- table constraints
- indexes
- RLS and access policies
- views/functions where appropriate

Supabase should avoid:

- becoming an undocumented computation layer
- receiving schema changes that are not captured in SQL or data-contract docs

### Streamlit

Streamlit should primarily own:

- read-focused dashboards
- diagnostics and operational visibility
- charts, filters, drilldowns
- user-facing monitoring views

Streamlit should avoid:

- writing to core production scoring tables
- defining canonical scoring logic
- hiding data quality corrections inside dashboard code

---

## 4. Overlap Risk Checklist

Before changing a file, ask:

1. Does another system already define this schedule, formula, table, or contract?
2. Will the change affect Supabase writes?
3. Will the change affect Streamlit outputs?
4. Will the change affect historical replay comparability?
5. Will the change affect n8n item-linking or merge behaviour?
6. Will the change affect GitHub Actions script paths?
7. Is the change documented in the relevant runbook or governance doc?

---

## 5. Current High-Risk Overlap Areas

| Area | Risk | Recommended Handling |
|---|---|---|
| n8n Code node scoring logic | Logic may drift from Python scoring | Gradually migrate canonical logic to Python when safe |
| GitHub Actions vs n8n triggers | Possible duplicate runs | Document trigger owner per workflow |
| Supabase schema changes | Runtime failures if table assumptions drift | Add SQL migration convention and data contracts |
| Long versioned Python filenames | Unclear canonical source | Do not mass rename yet; document active entrypoints first |
| Streamlit-derived calculations | Dashboard may diverge from stored metrics | Prefer persisted computed values or documented derived metrics |

---

## 6. Implementation Rules

1. New scoring logic should be implemented in Python first.
2. New production workflow schedules must be documented in workflow registry.
3. New tables or schema changes should have SQL files and data-contract notes.
4. New n8n workflows should state whether they are production, support, validation, research, or archive.
5. New Streamlit pages should state which tables/views they read from.

---

## 7. Review Cadence

Review this matrix after:

- every major phase implementation
- any new production workflow
- any new Supabase table group
- any migration from n8n Code node logic to Python
- any change to GitHub Actions scheduling
