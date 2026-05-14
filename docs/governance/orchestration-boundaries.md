# Orchestration Boundaries

**Purpose:** Define how n8n, GitHub Actions, Python, Supabase, and Streamlit should interact without creating duplicated control logic.

**Last reviewed:** 2026-05-14  
**Status:** Initial governance baseline  
**Scope:** Runtime orchestration and execution responsibilities

---

## 1. Architectural Principle

Each runtime layer should have a clear role:

```text
n8n            = connector and ingestion edge
GitHub Actions = orchestration and control plane
Python         = compute and transformation plane
Supabase       = persistence and policy plane
Streamlit      = observability and dashboard plane
```

The system should avoid having multiple layers independently control the same schedule, formula, state transition, or write path.

---

## 2. n8n Boundary

### n8n should do

- Call external APIs
- Handle connector-specific authentication through n8n credentials
- Perform lightweight payload shaping
- Route data into Supabase or stable Python/GitHub entrypoints
- Support operational ingestion workflows
- Provide manual research or diagnostic flows where appropriate

### n8n should avoid

- Long-term ownership of scoring formulas
- Heavy business logic in Code nodes
- Multi-phase orchestration that duplicates GitHub Actions
- Hardcoded API keys or secrets in workflow JSON
- Silent production writes from archived workflows

### Preferred n8n workflow states

| State | Meaning |
|---|---|
| Production | Active, monitored, production-impacting |
| Production Support | Operational support or auxiliary production workflow |
| Validation | QA/checking workflow |
| Research | Exploratory, not production-critical |
| Archive | Legacy or reference-only; should not have active triggers |

---

## 3. GitHub Actions Boundary

### GitHub Actions should do

- Schedule production jobs
- Sequence Python phase execution
- Run validation gates
- Check secret availability
- Send notifications
- Provide repeatable execution logs
- Trigger backfills or replay jobs when explicitly requested

### GitHub Actions should avoid

- Embedding business logic in shell/YAML
- Performing scoring calculations directly
- Becoming a hidden source of schema mutation
- Calling unstable script paths without documentation

### GitHub Actions review checklist

Before changing a workflow:

1. Does the script path still exist?
2. Are all required secrets present?
3. Is the schedule documented?
4. Is the workflow production, support, validation, research, or backfill?
5. Which Supabase tables can be affected?
6. Is there a rollback path?

---

## 4. Python Boundary

### Python should do

- Scoring
- Data transformation
- Historical replay
- Structural graph evolution
- Corridor/regime inference
- Validation gates
- Telemetry writing
- Shared API/database client logic

### Python should avoid

- Secret values in constants
- Hidden cron/schedule logic
- Undocumented table creation or schema mutation
- Reimplementing orchestration that GitHub Actions already controls

### Preferred Python execution style

Use stable entrypoint scripts called by GitHub Actions or n8n.

Example:

```text
GitHub Actions workflow
    -> python transmission_layers/graph_foundation/phase5b_propagation_corridor_engine.py
        -> reads Supabase inputs
        -> computes corridor intelligence
        -> writes results and telemetry
```

---

## 5. Supabase Boundary

### Supabase should do

- Store production state
- Store scoring outputs
- Store telemetry
- Store graph states
- Enforce constraints and indexes
- Manage RLS and access policies
- Provide views/functions when appropriate

### Supabase should avoid

- Undocumented schema changes
- Inconsistent table ownership
- Heavy hidden business logic without documentation
- Over-permissive read/write policies

### Database change checklist

1. Is there a SQL file or documented migration?
2. Which workflows/scripts read this table?
3. Which workflows/scripts write this table?
4. Does Streamlit depend on this table/view?
5. Are unique constraints and indexes documented?
6. Are RLS assumptions documented?

---

## 6. Streamlit Boundary

### Streamlit should do

- Display dashboards
- Provide drilldowns
- Show operational diagnostics
- Read Supabase tables or views
- Surface validation, telemetry, replay, and propagation results

### Streamlit should avoid

- Writing to core production scoring tables
- Defining canonical scoring logic
- Performing hidden data fixes
- Becoming the only place where a derived metric exists

### Dashboard review checklist

1. Which tables/views are read?
2. Are writes disabled or clearly isolated?
3. Are RLS/read permissions documented?
4. Are derived metrics documented?
5. Does the dashboard match persisted results?

---

## 7. Anti-Overlap Rules

1. No canonical scoring formula should live only in n8n.
2. No production schedule should exist in both n8n and GitHub Actions unless explicitly documented.
3. No schema mutation should occur without a checked-in SQL artifact or data-contract note.
4. No dashboard should write to core production tables unless intentionally designed and reviewed.
5. No archived workflow should remain active without explicit justification.
6. No secret should appear in Python, YAML, SQL, or exported JSON.

---

## 8. Recommended Runtime Pattern

For production-grade phases:

```text
External data source
    -> n8n or Python ingestion
    -> Supabase staging/core tables
    -> GitHub Actions scheduled phase runner
    -> Python scoring/propagation/replay engine
    -> Supabase output + telemetry tables
    -> Streamlit observability dashboard
```

---

## 9. Immediate Governance Actions

1. Create a workflow registry for n8n and GitHub Actions.
2. Mark each workflow as Production, Support, Validation, Research, Archive, or Retired.
3. For each production workflow, document trigger owner.
4. For each Python engine, document input tables and output tables.
5. For each Streamlit app, document read-only status and source tables.
