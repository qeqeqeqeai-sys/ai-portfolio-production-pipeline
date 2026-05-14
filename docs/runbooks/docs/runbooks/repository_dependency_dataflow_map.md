# Repository Dependency & Dataflow Map

_Last generated: 2026-05-14 (UTC)_

## Scope and method

This map is an architecture-visibility artifact only (no code refactoring). It is derived from:

- GitHub Actions workflow manifests under `.github/workflows/`
- n8n exports under `n8n/`
- orchestration/governance runbooks in `docs/governance/` and `docs/runbooks/`
- Python entrypoints in `scripts/`, `ai_transmission/`, and `transmission_layers/`

---

## 1) GitHub Actions execution order

There are **no explicit `needs:` job graphs** in current workflows; orchestration is mostly single-job workflows with sequencing controlled by **cron offsets + table/state dependencies**.

### 1.1 Portfolio + AI-transmission cadence

| Order | Workflow | Trigger | Effective dependency |
|---|---|---|---|
| 1 | `daily_ai_portfolio_pipeline.yml` | Weekday cron 21:30 UTC | Base scoring + telemetry producers |
| 2 | `phase1_ai_transmission_dual_write.yml` | Daily cron 23:30 UTC | Depends on core AI scoring outputs |
| 3 | `ai_transmission_evidence_pipeline.yml` | 00:00/12:00 UTC | Depends on prior-day or same-day scoring state |
| 4 | `ai_transmission_phase2a_pipeline_phase2d_revised.yml` | Weekday cron 23:00 UTC | Validation/telemetry pipeline on phase outputs |
| 5 | `ai_transmission_phase2d2_reconstruction.yml` | Manual | Historical reconstruction/backtest pass |

### 1.2 Graph propagation cadence (chronological chain)

| Order | Workflow | Trigger | Effective dependency |
|---|---|---|---|
| 1 | `phase4d_daily_graph_evolution.yml` | Daily cron 23:15 UTC | Establishes run/session context for graph phases |
| 2 | `phase5a2_structural_intermediaries.yml` | Daily cron 23:25 UTC | Requires evolved graph snapshot |
| 3 | `phase5a_two_hop_pipeline.yml` | Daily cron 23:30 UTC | Uses intermediary/graph state |
| 4 | `phase5b_propagation_corridor_pipeline.yml` | Daily cron 23:35 UTC | Consumes two-hop propagation outputs |
| 5 | `phase5c_regime_corridor_dynamics_pipeline.yml` | Daily cron 23:45 UTC | Consumes corridor outputs |
| 6 | `phase5d_structural_propagation_regime_forecasting_pipeline.yml` | Daily cron 01:40 UTC | Consumes regime corridor dynamics |

### 1.3 Manual/specialized workflows

Research/backfill/phase workflows (`phase3*`, `phase4a`, `phase4b`, `phase4e`, `historical_source_backfill`, `multi_theme_graph_pass1`, `continuity_engine_pipeline`) are mostly `workflow_dispatch` driven and rely on table readiness rather than YAML job DAGs.

---

## 2) n8n workflow dependencies

## 2.1 Production ingestion/scoring spine

| Stage | n8n workflow | Main upstream | Main downstream |
|---|---|---|---|
| Fundamental ingest | `Production - Get Daily Fundamental Data From FMP and Do Quant Scoring.json` | FMP API | Fundamental factor + quant score tables |
| Price ingest | `Production - Fetch Daily EOD Price Data From FMP and Compute Stock_Subsector Metrics.json` | FMP API | EOD price + stock/subsector metrics tables |
| Merge/reversal | `Production - Merge Price and Fundamental Data and Compute Reversal Scores.json` | Fundamental + price tables | Reversal score tables |
| News/hype | `Production - Get News and Price and Compute Hype Scores.json` | News + market APIs | Sentiment/hype score tables |

## 2.2 Support/validation/research dependencies

| Category | Workflow(s) | Dependency role |
|---|---|---|
| Macro support | `Production Support - Macro Regime and Stress Signal Engine.json`, `...Commodity Prices and Compute Stress Scores.json` | Auxiliary macro/stress enrichments consumed by risk layers/alerts |
| Alerts | `Production Support - Send AI Overheating Alerts.json` | Reads derived risk/heat outputs; sends notifications |
| Validation | `Validation - AI Stock Backtest QA Layer.json` | Reads scoring/backtest outputs to gate confidence |
| Historical/research | `Research - Historical Fundamental Factor Builder.json`, `Research - Historical AI Score Reconstruction with Reversal Filter.json` | Replay/backfill source builders |
| Archived legacy | `Archive - ...` workflows | Must remain unscheduled; used for rollback/reference only |

---

## 3) Python execution dependencies

## 3.1 Entrypoint groups

| Group | Entrypoints | Typical dependencies |
|---|---|---|
| Orchestration scripts | `scripts/*github_actions*.py`, `run_production_validation_gates.py`, `archive_production_reports.py` | Supabase clients, validation config, telemetry writers |
| AI transmission core | `ai_transmission/*.py`, `transmission_layers/ai_transmission/*.py` | API loaders, scoring/reconstruction logic, telemetry modules |
| Graph foundation | `transmission_layers/graph_foundation/phase*.py`, `run_pass1_graph_foundation.py` | `graph_supabase_client.py`, `supabase_rest_client.py`, graph models/validation |
| Historical backfill | `transmission_layers/ai_transmission/historical_backfill/*.py`, `phase4e_historical_propagation_replay.py` | checkpointing, validation gates, telemetry, historical table readers |
| Streamlit/monitoring | `ai_transmission_monitoring_dashboard_phase2a.py`, `phase4c_propagation_monitoring_dashboard.py`, streamlit app in `transmission_layers/ai_transmission/` | Read-only analytics queries over production + telemetry tables |

---

## 4) Supabase table write/read relationships (logical)

> Table names vary by phase/workflow. Relationship classes below show the stable write/read topology visible from pipeline naming + module ownership.

| Producer layer | Writes (table classes) | Consumer layer | Reads for |
|---|---|---|---|
| n8n production ingest | raw_fundamental, raw_price, raw_news, macro_support | n8n merge/scoring + Python scoring | derived factor/signal construction |
| n8n merge/scoring | merged_features, reversal_scores, hype_scores | Python AI transmission + validation | AI transmission scoring inputs |
| Python AI transmission | ai_scores, explainability, reconstruction outputs | validation gates + Streamlit | QA + analytics dashboards |
| Graph foundation phases | graph_nodes, graph_edges, persistence/drift/pressure/potential outputs | phase4/5 propagation engines | propagation, corridor, regime forecasts |
| Historical replay/backfill | replay states, memory-decay snapshots, checkpoints | QA layers + dashboard | backtest comparability, historical diagnostics |
| Telemetry writers | pipeline_metrics, failure_metrics, phase telemetry | dashboards + alerting | ops observability and incident triage |

---

## 5) Streamlit dependencies

| App/module | Primary reads | Coupling notes |
|---|---|---|
| `ai_transmission/ai_transmission_monitoring_dashboard_phase2a.py` | AI transmission scores + validation telemetry | Tightly coupled to phase2 schema naming |
| `transmission_layers/graph_foundation/phase4c_propagation_monitoring_dashboard.py` | propagation and memory tables | Coupled to phase4/5 table contracts |
| `transmission_layers/ai_transmission/ai_transmission_streamlit_app_v1_phase2d1_historical_analytics_REST_RLS_SAFE.py` | historical reconstruction/replay outputs | Depends on replay table continuity + RLS-safe REST paths |

---

## 6) Historical replay dependencies

| Replay component | Upstream | Downstream |
|---|---|---|
| `phase4e_historical_propagation_replay.py` | historical graph/edge snapshots | replay outputs, memory state, telemetry |
| `phase2d2_historical_reconstruction_engine_schema_aligned_revised.py` | historical factor/score series | reconstructed AI transmission history |
| `historical_ai_transmission_backfill.py` + checkpointing | source history + checkpoints | resumable backfill artifacts + validation signals |

---

## 7) Propagation layer dependencies

Text diagram:

```text
Phase3A/3B/3C/3D/3E graph enrichment
   -> Phase4A single-hop propagation
      -> Phase4B memory decay
         -> Phase4E historical replay (backfill path)
         -> Phase5A two-hop propagation
            -> Phase5B corridor intelligence
               -> Phase5C regime corridor dynamics
                  -> Phase5D structural regime forecasting
```

Critical library dependencies in this path:
- `graph_supabase_client.py` / `supabase_rest_client.py`
- `graph_models.py`
- `graph_validation.py`
- intermediary subpackage (5A.2/5A.3/5A.4 chain)

---

## 8) Telemetry dependencies

| Telemetry source | Writer | Consumer |
|---|---|---|
| Pipeline run metrics | `scripts/write_pipeline_metrics.py` | Ops dashboards, incident runbooks |
| Failure metrics | `scripts/write_pipeline_failure_metrics.py`, `notify_archival_failure.py` | Alerting + postmortems |
| Phase telemetry | phase-specific telemetry modules (e.g., phase2a, intermediary telemetry, historical_backfill_telemetry) | validation and streamlit diagnostics |

---

## 9) Shared utility usage

| Utility | Used by | Architectural effect |
|---|---|---|
| `utils/paginated_rest_loader.py` | ingestion/replay readers | Standardizes API pagination behavior |
| `utils/streaming_observation_loader.py` | signal/replay loaders | Shared observation normalization path |
| `utils/rolling_reconstruction_aggregators.py` | reconstruction/analytics phases | Shared rolling-window metric semantics |
| `scripts/api_retry_utils.py` | API-facing scripts | Common retry/backoff behavior |

---

## 10) Duplicated dependency patterns

1. **Dual schedulers**: both n8n and GitHub Actions can orchestrate daily production-adjacent flows.
2. **Per-phase Supabase access wrappers**: multiple modules implement similar read/write + retry + validation scaffolding.
3. **Telemetry fan-out**: telemetry written by script-level utilities and phase-level custom telemetry modules.
4. **Historical replay logic split**: replay/backfill logic exists in graph and AI transmission trees with parallel checkpoint/validation patterns.

---

## 11) Critical-path workflows

### 11.1 Daily scoring critical path

```text
n8n fundamental + price ingestion
   -> n8n merge/reversal/hype
      -> daily_ai_portfolio_pipeline (GitHub Actions)
         -> AI transmission phase workflows
            -> validation gates + telemetry
               -> Streamlit dashboards + alerts
```

### 11.2 Graph propagation critical path

```text
phase4d_daily_graph_evolution
   -> phase5a2_intermediaries
      -> phase5a_two_hop
         -> phase5b_corridors
            -> phase5c_regime_dynamics
               -> phase5d_forecasting
```

---

## 12) High-risk coupling points

| Coupling point | Why high risk | Impact if drift occurs |
|---|---|---|
| Cron-offset sequencing without explicit DAG | Hidden dependency order is time-based only | race conditions, partial data windows |
| Table-schema coupling across n8n + Python + Streamlit | Multiple runtimes consume shared table contracts | silent downstream breakages |
| Archived/research workflows co-located with production exports | Trigger/config mistakes can reactivate legacy logic | data contamination |
| Phase-specific script naming contracts in workflows | YAML paths tightly bound to long filenames | brittle deploys/renames |
| Telemetry schema fragmentation | multiple telemetry writers with different conventions | weak cross-phase observability |

---

## 13) Recommended observability gaps to close

1. Add an explicit **run-lineage table** linking workflow run IDs to phase outputs and table write batches.
2. Add a **dependency heartbeat dashboard** showing upstream freshness per critical table class.
3. Add automated **cross-layer contract checks** (n8n output schema vs Python expected columns).
4. Add **schedule collision monitoring** for cron windows that currently encode dependencies.
5. Standardize telemetry dimensions: `run_id`, `phase`, `workflow_name`, `table_written`, `row_count`, `latency_ms`, `error_class`.

---

## 14) Recommended future modularization boundaries

1. **Connector boundary module**: isolate external API pulls (currently split across n8n and Python).
2. **Feature-store boundary**: a canonical staging/feature contract between ingestion and scoring.
3. **Propagation core SDK**: shared graph read/write + validation + telemetry primitives for all phase3/4/5 engines.
4. **Replay platform module**: unify checkpointing, replay windows, and validation gates across graph + AI transmission backfills.
5. **Observability module**: one telemetry API and schema package used by scripts, phases, and dashboards.

---

## 15) Architecture diagrams (text)

### 15.1 Layered runtime architecture

```text
[External APIs]
   | 
   v
[n8n ingestion/support workflows] -----> [Supabase raw/support tables]
                                         |
                                         v
                              [GitHub Actions schedulers]
                                         |
                                         v
                         [Python scoring/propagation/replay engines]
                                         |
                     +-------------------+-------------------+
                     v                                       v
           [Supabase output tables]                 [Supabase telemetry tables]
                     |                                       |
                     +-------------------+-------------------+
                                         v
                             [Streamlit dashboards/ops views]
```

### 15.2 Dependency risk hotspots

```text
(time-based cron ordering)
        |
        v
 [workflow A writes table X] --> [workflow B reads table X] --> [dashboard C renders X]
        ^                             |
        |                             v
   [legacy/research workflow may also write X if mis-triggered]
```
