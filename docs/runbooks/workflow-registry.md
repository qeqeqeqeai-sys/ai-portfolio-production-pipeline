# Workflow Registry

**Status:** Initial governance baseline  
**Owner:** Platform Orchestration Team  
**Last reviewed:** 2026-05-14  
**Scope:** GitHub Actions workflows, n8n workflows, scheduled jobs, replay/backfill pipelines, validation pipelines.

---

## 1. Purpose

This registry provides a single operational inventory of all workflows used by the modular structural transmission research platform.

It is intended to answer:

- What workflows exist?
- Which workflows are active, legacy, archived, or research-only?
- What triggers each workflow?
- Which systems and tables are affected?
- Who owns the workflow?
- What breaks if the workflow fails?

This document should be updated whenever a workflow is added, retired, renamed, rescheduled, or materially changed.

---

## 2. Workflow status definitions

| Status | Meaning | Operational treatment |
|---|---|---|
| Active | Production-used and expected to run normally | Monitor and maintain |
| Supported Legacy | Not preferred, but retained for fallback or compatibility | Do not modify unless needed |
| Research | Experimental or one-off analytical workflow | Must not be treated as production |
| Validation | QA, diagnostics, checks, or health monitoring | Used to support production confidence |
| Archived | Retained for reference or rollback only | Must not be scheduled |
| Retired | No longer used and pending deletion or already superseded | Keep replacement documented |

---

## 3. GitHub Actions workflow registry

| Workflow file | Status | Owner | Trigger | Primary purpose | Upstream dependencies | Downstream outputs / tables | Failure impact | Notes |
|---|---|---|---|---|---|---|---|---|
| `.github/workflows/daily_ai_portfolio_pipeline.yml` | Active | Platform Orchestration Team | Scheduled / manual | Main daily operational spine | API providers, Supabase secrets, Python scripts | AI portfolio scores, telemetry, validations | High | Treat as primary production pipeline until replaced |
| `.github/workflows/phase4e_historical_propagation_replay.yml` | Active / Backfill | Graph Intelligence Team | Manual / scheduled if enabled | Historical propagation replay and memory backfill | Supabase historical tables, graph foundation scripts | Replay outputs, propagation memory tables | Medium to High | Confirm whether scheduled or manual before changes |
| `.github/workflows/<add_workflow_name>.yml` | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Add each discovered workflow here |

---

## 4. n8n workflow registry

| Workflow export | Status | Owner | Trigger | Primary purpose | Upstream dependencies | Downstream outputs / tables | Failure impact | Notes |
|---|---|---|---|---|---|---|---|---|
| `n8n/Production - Get Daily Fundamental Data From FMP and Do Quant Scoring.json` | Active | Workflow Automation Team | n8n schedule / manual | Daily fundamental data ingestion and quant scoring | FMP API, Supabase credentials | Fundamental metrics, quant scores | High | Avoid changing scoring logic inside Code nodes until migrated safely |
| `n8n/Production - Fetch Daily EOD Price Data From FMP and Compute Stock_Subsector Metrics.json` | Active | Workflow Automation Team | n8n schedule / manual | Daily EOD price ingestion and stock/subsector metrics | FMP API, Supabase credentials | Market observations, stock/subsector metrics | High | Core market data input flow |
| `n8n/Production - Merge Price and Fundamental Data and Compute Reversal Scores.json` | Active | Workflow Automation Team | n8n schedule / manual | Cross-dataset merge and reversal score calculation | Price data, fundamental data, Supabase | Reversal scores, merged scoring tables | High | Cross-dataset dependency point |
| `n8n/Production - Get News and Price and Compute Hype Scores.json` | Active | Workflow Automation Team | n8n schedule / manual | News, sentiment, price and hype signal computation | News/search APIs, market APIs, Supabase | Hype scores, sentiment-derived signals | Medium to High | Candidate for later Python extraction of scoring logic |
| `n8n/Production Support - Macro Regime and Stress Signal Engine.json` | Active / Support | Workflow Automation Team | n8n schedule / manual | Macro regime and stress signal support | FRED / macro APIs, Supabase | Macro regime and stress indicators | Medium | Support layer, not necessarily primary scoring spine |
| `n8n/Archive - Legacy AI Sector Monitor.json` | Archived | Workflow Automation Team | None expected | Legacy AI sector monitoring reference | Historical connector setup | None expected | Low unless reactivated | Must remain unscheduled |
| `n8n/Research - Historical Fundamental Factor Builder.json` | Research | Workflow Automation Team / Research Owner | Manual | Research/backfill of historical fundamental factors | FMP API, Supabase | Historical factor tables | Medium if used for backfill | Confirm scope before production use |
| `n8n/<add_workflow_name>.json` | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Add each discovered workflow here |

---

## 5. Python job / script registry

| Script / module | Status | Owner | Invoked by | Primary purpose | Reads from | Writes to | Failure impact | Notes |
|---|---|---|---|---|---|---|---|---|
| `scripts/run_production_validation_gates.py` | Active | Platform Orchestration Team | GitHub Actions | Production validation gate execution | Supabase / pipeline outputs | Validation tables / logs | High | Used to block or warn on production issues |
| `scripts/write_pipeline_metrics.py` | Active | Platform Orchestration Team | GitHub Actions | Persist pipeline telemetry | Runtime metadata | Pipeline metrics table | Medium | Important for operational monitoring |
| `transmission_layers/graph_foundation/phase4e_historical_propagation_replay.py` | Active / Backfill | Graph Intelligence Team | GitHub Actions / manual | Historical propagation replay | Graph/source historical tables | Replay/memory outputs | Medium to High | Avoid import path changes without workflow update |
| `transmission_layers/graph_foundation/<add_module>.py` | TBD | Graph Intelligence Team | TBD | TBD | TBD | TBD | TBD | Add graph propagation engines here |
| `transmission_layers/ai_transmission/<add_module>.py` | TBD | AI Transmission Team | TBD | TBD | TBD | TBD | TBD | Add AI transmission engines here |

---

## 6. Workflow dependency checklist

For each workflow, record:

- Runtime owner
- Trigger type
- Schedule frequency
- Required secrets
- Required external APIs
- Required Supabase tables
- Tables written
- Tables read
- Downstream dashboards affected
- Notification channel, if any
- Failure severity
- Rollback procedure

---

## 7. Failure impact levels

| Level | Definition | Example |
|---|---|---|
| High | Breaks daily scoring, key dashboards, or core research outputs | Main daily pipeline failure |
| Medium | Degrades support signals, backfills, or non-critical diagnostics | Macro support signal delay |
| Low | Affects archived, research, or non-production artifacts only | Archived workflow unavailable |

---

## 8. Update policy

Update this registry when:

- A workflow is added
- A workflow trigger changes
- A workflow is archived or retired
- A workflow starts writing to a new table
- A workflow starts using a new secret
- A workflow becomes production-critical
- A workflow is moved, renamed, or split

No workflow should be treated as production-ready unless it appears in this registry.
