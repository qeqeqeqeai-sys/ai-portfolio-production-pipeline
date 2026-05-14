# Naming Conventions

**Purpose:** Define practical naming rules for new and touched assets without breaking existing working paths.

**Last reviewed:** 2026-05-14  
**Status:** Initial governance baseline  
**Scope:** Python, n8n, GitHub Actions, SQL, documentation, database tables

---

## 1. Core Rule

Do not mass-rename working files yet.

Apply these conventions to:

1. new files,
2. files that are already being touched for functional reasons,
3. documentation and governance artifacts,
4. future cleanup phases with tested migration paths.

---

## 2. Python File Naming

### Recommended pattern

```text
phase<phase><subphase>_<domain>_<action>.py
```

### Examples

```text
phase3a_evidence_graph_expansion.py
phase4e_historical_propagation_replay.py
phase5b_propagation_corridor_engine.py
phase5c_regime_aware_corridor_dynamics.py
phase5d_structural_propagation_regime_forecasting.py
```

### Rules

- Use `snake_case`.
- Keep names descriptive but not excessive.
- Avoid adding repeated version suffixes such as `_v1_phase1_refactor_final_revised` unless needed for migration safety.
- Preserve existing working filenames until import paths and GitHub Actions references are mapped.
- Prefer stable module boundaries over versioning in filenames.

### Avoid

```text
ai_transmission_streamlit_app_v1_phase2d1_historical_analytics_REST_RLS_SAFE_final_revised_latest.py
```

### Prefer eventually

```text
historical_analytics_dashboard.py
```

Only rename when workflow references and imports are confirmed safe.

---

## 3. n8n Workflow Naming

### Current-compatible pattern

```text
<Tier> - <Domain> - <Action>.json
```

### Allowed tiers

```text
Production
Production Support
Validation
Research
Archive
```

### Examples

```text
Production - AI Transmission - Daily Evidence Ingestion.json
Production - Market Data - Daily EOD Price Fetch.json
Production Support - Macro Regime - Stress Signal Engine.json
Validation - Supabase - Daily Table Health Check.json
Research - Historical Fundamentals - Factor Builder.json
Archive - Legacy AI Sector Monitor.json
```

### Rules

- Keep tier at the start of the filename.
- Use human-readable names for exported n8n workflows.
- Do not move active workflows until registry and trigger ownership are documented.
- Archived workflows should be marked in workflow registry.

---

## 4. GitHub Actions Workflow Naming

### Recommended pattern

```text
<phase_or_domain>_<purpose>.yml
```

### Examples

```text
daily_ai_portfolio_pipeline.yml
phase4e_historical_propagation_replay.yml
phase5b_corridor_intelligence.yml
validation_supabase_table_health.yml
```

### Rules

- Use lowercase snake_case.
- Keep current workflow names unchanged unless migration is planned.
- New workflow names should clearly indicate domain and purpose.
- Avoid ambiguous names such as `pipeline.yml` or `run.yml`.

---

## 5. SQL File Naming

### Recommended pattern

```text
YYYYMMDDHHMM_<domain>_<change>.sql
```

### Examples

```text
202605141030_graph_add_corridor_index.sql
202605141100_ai_transmission_add_replay_checkpoint.sql
202605141130_telemetry_create_pipeline_metrics.sql
```

### Rules

- Use timestamp prefix for ordering.
- Use snake_case.
- Use clear domain and change description.
- Keep destructive migrations clearly labelled and reviewed.

### Suggested folders

```text
database/
  migrations/
  views/
  functions/
  policies/
  seeds/
```

Do not move existing SQL assets until inventory is complete.

---

## 6. Documentation Naming

### Recommended pattern

```text
<topic>-<artifact>.md
```

### Examples

```text
repo-ownership.md
source-of-truth.md
orchestration-boundaries.md
naming-conventions.md
secrets-governance.md
github-actions-ops.md
n8n-ops.md
incident-response.md
```

### Rules

- Use lowercase kebab-case.
- Keep documents short enough to maintain.
- Put governance rules under `docs/governance/`.
- Put operational runbooks under `docs/runbooks/`.
- Put table/data contracts under `docs/data-contracts/`.

---

## 7. Database Table Naming

### Recommended pattern

```text
<domain>_<entity>_<purpose>
```

### Examples

```text
structural_theme_graph_edges
structural_theme_graph_corridors
structural_theme_graph_regime_forecasts
ai_transmission_scores
ai_transmission_evidence
pipeline_execution_metrics
```

### Rules

- Use lowercase snake_case.
- Avoid ambiguous abbreviations.
- Keep historical/replay tables clearly marked.
- Prefer stable table names over phase-specific names when the table is long-lived.

---

## 8. Column Naming

### Recommended rules

- Use lowercase snake_case.
- Use `_sgt` suffix for Singapore-time date/time fields where relevant.
- Use `_score` for normalized scoring outputs.
- Use `_regime` for categorical state labels.
- Use `_at` for timestamps.
- Use `_id` for identifiers.

### Examples

```text
run_date_sgt
created_at
theme_name
source_theme
target_theme
propagation_score
regime_label
confidence_score
```

---

## 9. Versioning Guidance

Avoid uncontrolled filename versioning.

### Acceptable temporary migration names

```text
phase2d2_historical_reconstruction_engine_schema_aligned_revised.py
```

This is acceptable while debugging schema alignment.

### Long-term target

Once stable, the canonical file should become clearer:

```text
phase2d2_historical_reconstruction_engine.py
```

Document canonical entrypoints before renaming.

---

## 10. Naming Review Checklist

Before adding a new file:

1. Is the filename clear without being excessive?
2. Does it match the folder purpose?
3. Is it obvious whether the file is production, support, validation, research, archive, or legacy?
4. Is the phase/domain/action visible?
5. Could this name still make sense six months from now?
6. Does another file already do the same thing?

---

## 11. Current Policy

For now:

- keep active working paths stable,
- apply conventions only to new files,
- document canonical files before cleanup,
- avoid mass renames,
- prefer operational safety over cosmetic consistency.
