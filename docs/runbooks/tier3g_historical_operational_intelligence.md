# Tier 3G — Historical Operational Intelligence

## Purpose

Tier 3G introduces historical persistence for workflow observability telemetry.

This layer extends:

- Tier 3E operational aggregation
- Tier 3F operational trend intelligence

into long-term operational analytics.

---

## Objectives

Persist historical workflow telemetry for:

- runtime drift analysis
- recurring warning detection
- workflow reliability scoring
- operational anomaly detection
- governance trend analysis
- orchestration stability analytics

---

## Initial Scope

Initial rollout is intentionally advisory.

Current implementation:

- does not modify production orchestration behavior
- does not block workflows
- tolerates missing observability artifacts
- tolerates persistence failures
- establishes persistence infrastructure only

---

## Table

```text
platform_workflow_observability_history
```

Schema file:

```text
sql/platform_workflow_observability_history.sql
```

---

## Persistence Writer

Script:

```text
scripts/write_observability_history.py
```

Behavior:

- reads observability JSON artifacts under `logs/`
- constructs historical telemetry payload
- writes advisory snapshot to Supabase
- exits safely in advisory mode on persistence failures

---

## Expected Observability Sources

Current Tier 3G ingestion targets:

- execution_context.json
- validation_summary.json
- telemetry_context_snapshot.json
- platform_operational_summary.json
- platform_operational_trend_summary.json
- platform_workflow_health_score.json

---

## Recommended Future Metrics

Potential future additions:

- workflow reliability percentile
- runtime acceleration/degradation
- instability clustering
- recurring failure motifs
- dependency fragility scoring
- orchestration resilience scoring
- operational centrality
- governance compliance trend scoring

---

## Recommended Visualization Layer

Suggested downstream integrations:

- Power BI operational dashboards
- workflow health heatmaps
- runtime drift charts
- recurring warning distributions
- governance trend analytics
- orchestration anomaly monitoring

---

## Rollout Strategy

### Phase 1

Advisory persistence only.

### Phase 2

Selected workflow integration.

### Phase 3

Platform-wide persistence rollout.

### Phase 4

Governance threshold enforcement.

### Phase 5

Automated orchestration intelligence.

---

## Governance Note

Tier 3G persistence is intended to evolve into:

- orchestration governance intelligence
- operational reliability analytics
- workflow health intelligence
- self-monitoring platform infrastructure
