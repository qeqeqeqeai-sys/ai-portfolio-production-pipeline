# Initial Tier 3B Workflow Contracts

These are starter contracts for the first three recommended workflows.

## 1. `daily_ai_portfolio_pipeline.yml`

| Field | Value |
|---|---|
| Runtime layer | GitHub Actions |
| Run mode | scheduled |
| Criticality | high |
| Primary role | Daily portfolio scoring / monitoring spine |

### Upstream dependencies

| Type | Name | Requirement |
|---|---|---|
| table | market/fundamental source tables | latest expected trading date available |
| table | internal signal inputs | non-empty for target run date |
| secret | provider + Supabase secrets | available before execution |

### Guardrails

- Preflight should run after secret validation and before the first mutating script.
- Start in advisory mode.
- Later promote stale source-market data to hard-fail.

## 2. `phase1_ai_transmission_dual_write.yml`

| Field | Value |
|---|---|
| Runtime layer | GitHub Actions |
| Run mode | scheduled |
| Criticality | critical |
| Primary role | AI transmission scoring + structural theme dual write |

### Upstream dependencies

| Type | Name | Requirement |
|---|---|---|
| table | AI evidence observations | same `run_date_sgt` or accepted lookback |
| table | transmission map | latest partition exists |
| workflow | evidence ingestion | completed successfully when same-day evidence is required |

### Guardrails

- Preflight should confirm evidence availability.
- Lineage start should occur before scoring.
- Completion hook should record writes to legacy AI score outputs and structural theme tables.

## 3. `phase5a_two_hop_pipeline.yml`

| Field | Value |
|---|---|
| Runtime layer | GitHub Actions |
| Run mode | scheduled |
| Criticality | high |
| Primary role | Two-hop propagation generation |

### Upstream dependencies

| Type | Name | Requirement |
|---|---|---|
| table | phase4a single-hop propagation | same run date; non-empty |
| table | graph edge/snapshot tables | same run date or approved latest snapshot |
| workflow | phase4d / phase4a chain | completed successfully before 5A |

### Guardrails

- Preflight must validate same-date single-hop partition.
- Lock should prevent overlap with replay/backfill jobs touching propagation history.
- Completion hook should record two-hop output row counts.
