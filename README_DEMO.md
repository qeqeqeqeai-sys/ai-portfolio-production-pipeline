# Structural Transmission Project — Demo README

## Project Demo Identity
**Deterministic Institutional Expectation-Failure Intelligence Platform** focused on bounded, explainable structural interpretation and reviewer-visible evidence.

## What This Demo Shows
- Deterministic, certification-aligned dashboard demonstration flow.
- Architecture-to-visual continuity from P1A/P1B materials.
- Replay and visibility evidence through D2/D3 artifacts.
- Demo readiness posture anchored by D4 closeout.

## What This Demo Does Not Show
- no autonomous trading
- no target prices
- no portfolio optimization
- no trade execution
- no uncontrolled LLM reasoning
- no adaptive control systems
- no autonomous trading agents
- no predictive market forecasting
- no buy/sell/short recommendations

## Recommended Review Sequence
1. Read this file.
2. Review architecture materials (P1A, P1B, P1B1).
3. Review certification chain (O-series, D1, D1G, D2, D3, D4).
4. Review P2 demo checklist/runbook/interview guide.
5. Run dashboard using existing certified startup path.

## Key Files and Reports
- `reports/p1a_institutional_narrative_architecture.md`
- `reports/p1b_visual_architecture_package.md`
- `reports/p1c_interview_talk_track.md`
- `reports/dashboard_d4_demo_environment_closeout_report.md`
- `reports/p2_demo_readiness_checklist.md`
- `reports/p2_live_demo_runbook.md`
- `reports/p2_interview_delivery_guide.md`
- `reports/p2_reviewer_quickstart.md`

## Dashboard Demonstration Path
- Execute architecture-first opening.
- Transition to deterministic seeded-data visibility.
- Walk through certified dashboard views in stable sequence.
- Show replay/certification evidence trail.
- Close with boundaries and institutional framing.

## Certification Chain Summary
- O1–O10: operational dashboard certification baseline.
- D1/D1G: deterministic seed and guardrail contract baseline.
- D2/D3: visibility and playback validation.
- D4: demo environment closeout and readiness anchor.

## Visual Asset Summary
- P1B visual architecture package and companion one-pager support presentation-safe storytelling.
- P1C pitch/talk-track artifacts support interviewer and reviewer communication discipline.

## Interview / Portfolio Use
Use P2 artifacts to deliver consistent 5-minute and 10-minute demonstrations, architecture walkthroughs, and governance-safe interview responses.

## Safety and Boundary Notes
All demonstrations should preserve bounded-system framing and explicitly reaffirm non-autonomous scope, non-predictive scope, and non-execution scope.

## Local Streamlit Runtime Setup (Supabase)
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Run the Streamlit dashboard:
   - `streamlit run apps/streamlit_expectation_failure_dashboard.py`
3. Configure Supabase credentials before launch:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (recommended for Streamlit read-only runtime)
4. Verify runtime diagnostics before validating real-data rendering:
   - `supabase_package_available=True`
   - `client_resolved=True`

## D1 Dashboard Sample Seed Execution (Controlled O3 Path)
Use the deterministic seed runner to populate empty dashboard tables with certified sample rows through the existing O3 controlled write adapter.

**Warning:** This flow writes controlled sample data only when execution is explicitly confirmed.

Dry-run (default safe mode):
- `python scripts/run_d1_dashboard_sample_seed.py --dry-run`

Execute controlled writes:
- `python scripts/run_d1_dashboard_sample_seed.py --execute`

Execute controlled writes + read-only post-seed verification:
- `python scripts/run_d1_dashboard_sample_seed.py --execute --verify-readback`

Expected post-seed diagnostics:
- `supabase_project_host=<project-ref>.supabase.co`
- `credential_source=service_role_key|anon_key|supabase_key`
- `execution_status=completed` (or failure surfaced clearly)
- `planned_table_row_counts` emitted per canonical table
- `write_result_statuses` emitted when O3 returns table statuses
- `readback_table_results` emitted per canonical table with `row_count` and status
- `verification_status=verified_non_empty|verified_empty|verification_failed`
- `--execute --verify-readback` exits non-zero unless verification is `verified_non_empty`.

## GitHub Actions Controlled D1 Sample-Data Seeding
Workflow name:
- `Controlled D1 Dashboard Sample-Data Seeding`

Required repository secrets:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (optional, preferred for backend controlled writes)

Manual trigger steps:
1. Open **Actions** in GitHub.
2. Select workflow: **Controlled D1 Dashboard Sample-Data Seeding**.
3. Click **Run workflow** (manual trigger only).
4. Confirm logs include warning line:
   - `Executing deterministic controlled sample-data seed`

Expected post-seed diagnostics:
- `runtime_mode=read_only_supabase_mode`
- `payload_source=supabase_snapshot`
- `normalization_status=normalized`


## Canonical Physical Dashboard Tables
- `dashboard_entity_facts`
- `dashboard_subsector_facts`
- `dashboard_alert_facts`
- `dashboard_replay_facts`
- `dashboard_benchmark_facts`
- `dashboard_evidence_facts`
- `dashboard_certification_reports`
- `dashboard_run_manifests`

## One-off D6 real proving cycle runner

Use the one-off runner to execute D6 against real Supabase dashboard tables through an injected runtime-resolved client:

```bash
python scripts/run_d6_real_proving_cycle.py
```

It prints finding/narrative counts, persistence and readback verification statuses, per-table persisted counts, supervisor usefulness evaluation, and checksum continuity.

## Track C-1 Streamlit Daily Briefing MVP

The Daily Briefing MVP is a minimal analyst-facing Streamlit workflow over existing SEFI intelligence outputs.

Launch locally:

```bash
streamlit run apps/sefi_daily_briefing.py
```

Primary workflow:
1. **Daily Briefing** — shows briefing date, attention level, briefing quality status, top developments, story evolution highlights, investigation candidates, historical/live deviations, emerging themes, persistence watchlist, confidence labels, and compact lifecycle/archetype labels.
2. **Investigation Queue** — shows deterministic ranked items with investigation type, lifecycle state, narrative archetype, priority, why each item appears, deterministic `why_now` context, analyst value, and review questions.
3. **Story Detail** — shows current state, lifecycle state, narrative archetype, a short continuity explanation, deterministic `why_now` context, story history summary, historical context, similarities, differences, analyst significance, next questions, and expandable evidence drill-down.

### Cross-day story continuity and evolution (C-1G)

C-1G adds a read-only, presentation-only continuity layer over multiple available Daily Briefing artifacts. It uses existing artifact fields only and does not persist derived fields anywhere.

Story identity is deterministic. The adapter creates a stable `story_key` from existing `identifier` or `title` values whenever possible, with lifecycle/archetype/source/classification fields used only as deterministic fallback signals when no meaningful title-like identifier exists. This lets the same story resolve to the same identity across briefing dates without introducing a database table or schema migration.

For each visible story, the adapter builds a compact story history summary from loaded artifacts:

- `first_seen`
- `last_seen`
- `appearance_count`
- `consecutive_appearances`
- `highest_priority_seen`
- internal confidence, lifecycle, archetype, priority, and seen-date histories used for deterministic classification

The UI displays only the compact summary fields. It does not expose raw history payloads or raw JSON.

Evolution direction is deterministic and limited to:

- `rising` — priority, confidence, or lifecycle strength increased versus the prior appearance.
- `stable` — no material priority/confidence/lifecycle movement was detected.
- `falling` — priority or lifecycle strength weakened versus the prior appearance.
- `reappearing` — the story appears after a dated gap in available artifacts.
- `unknown` — insufficient prior history exists for cross-day comparison.

The adapter also adds deterministic `why_now` templates, such as:

- `priority increased versus previous appearance`
- `confidence improved versus previous appearance`
- `first appearance after absence`
- `no material change detected`
- `insufficient prior history for cross-day comparison`

Daily Briefing now includes **Story Evolution Highlights** grouped into Rising Stories, Reappearing Stories, and Falling Stories. The normalized adapter model also includes a capped `evolution_highlights` section with `rising_stories`, `stable_stories`, `falling_stories`, and `reappearing_stories`; each group is capped at 5 items and respects the same duplicate, low-confidence, low-priority, and internal-artifact suppression logic used by the quality gate.

This layer is explicitly read-only and presentation-only. It does not create schema migrations, create tables, write to Supabase, alter pipelines, call external APIs, generate new intelligence, add forecasting, or add prediction/trading language.

### Briefing quality gate

C-1F adds a deterministic presentation-only quality gate so the briefing stays concise, non-duplicative, and analyst-useful as more local intelligence artifacts accumulate. The gate does not create new intelligence; it only selects, suppresses, and labels existing artifact items for display.

Section caps are enforced before rendering:

- `major_developments`: max 5
- `investigation_candidates`: max 7
- `historical_live_deviation_highlights`: max 5
- `emerging_themes`: max 5
- `persistence_watchlist`: max 5
- `evolution_highlights`: max 5 per group

The gate deterministically suppresses duplicate items, low-confidence items when medium/high-confidence alternatives exist, low-priority investigation items when higher-priority candidates exist, items without meaningful title/identifier, evidence-only/raw-ID-only items, and internal governance/pipeline/validation-only artifacts. Duplicate items are collapsed when they share materially similar title/identifier, lifecycle state, narrative archetype, and source section; the retained item is selected by priority, confidence, ranking metric value, evidence/fact support count, then deterministic title sort.

The Daily Briefing page shows a **Briefing quality gate** expander with counts only:

- `total_candidates_seen`
- `total_items_suppressed`
- `duplicates_suppressed`
- `low_confidence_suppressed`
- `low_priority_suppressed`
- `internal_artifacts_suppressed`
- `final_items_shown`

Suppressed item details are not rendered. The summary is quality metadata only; top-level briefing cards continue to omit raw evidence IDs, while Story Detail preserves the evidence drill-down.

Briefing quality statuses are normalized as:

- `empty` — no briefing-worthy items remain; the app states: "No major ecosystem changes detected for the selected date."
- `thin` — some briefing-worthy intelligence exists but support is limited; the app states: "Limited briefing-worthy intelligence detected; review watchlist items before escalating."
- `strong` — at least three medium/high-confidence major or investigation items are available.
- `noisy` — duplicate, low-confidence, or internal artifact suppression is high enough that the loaded artifacts need analyst caution.

Narrative lifecycle labels are deterministic read-only presentation fields inferred from existing artifact signals only:

- `new` — live-only or newly surfaced signals.
- `developing` — historical/live deviations, baseline deviations, or strengthening live signals.
- `stable` — persistent, recurring, or continued structures.
- `weakening` — live signals weaker than historical context or persistent weakening.
- `resolved` — source artifacts that already mark an item as resolved, closed, or normalized.

Narrative archetypes are also deterministic read-only presentation fields inferred from existing artifact signals only:

- `continuation` — stable persistence or recurrence.
- `acceleration` — historically weak structures strengthening in live context.
- `emergence` — live-only or live-only anomaly items.
- `breakdown` — persistent structures weakening live or live weaker than historical context.
- `transition` — baseline or historical/live deviations.

These lifecycle/archetype labels, cross-day evolution fields, `why_now` templates, story history summaries, evolution highlights, and the quality gate are presentation logic only. They do not create schema migrations, write to Supabase, create database tables, alter pipelines, call external APIs, or generate new intelligence.

Data sources read by the MVP are local JSON artifacts only. The adapter inspects these paths in order and loads any that exist:

- `artifacts/obs_query4_ecosystem_briefing.json`
- `artifacts/obs_query4_investigation_queue.json`
- `artifacts/obs_query3_historical_live_comparison.json`
- `artifacts/hist_intel4_ecosystem_intelligence_synthesis.json`
- `outputs/obs_query4_ecosystem_briefing.json`
- `outputs/obs_query4_investigation_queue.json`
- `outputs/obs_query3_historical_live_comparison.json`
- `reports/hist_intel4_ecosystem_intelligence_synthesis.json`

If no artifact is available for the selected date, the app shows a clear empty state, lists inspected paths, and suggests running the existing OPS-LIVE / OBS-QUERY pipeline.

This MVP does **not** create schema migrations, write database rows, alter pipelines, generate new intelligence, expose raw JSON as the primary UI, add portfolio dashboards, make forecasts, or provide market action language.
