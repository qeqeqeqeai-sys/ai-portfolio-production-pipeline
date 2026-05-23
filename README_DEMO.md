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
   - `SUPABASE_ANON_KEY` or `SUPABASE_KEY`
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

Expected post-seed diagnostics:
- `credentials_present=true`
- `client_resolved=true`
- `tables_exist=true`
- `required_columns_present=true`
- `missing_columns=[]`
- Dashboard tables return non-empty rows.
- `health_interpretation` no longer reports `tables_exist_but_empty_or_filters_exclude_rows`.

## GitHub Actions Controlled D1 Sample-Data Seeding
Workflow name:
- `Controlled D1 Dashboard Sample-Data Seeding`

Required repository secrets:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

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
