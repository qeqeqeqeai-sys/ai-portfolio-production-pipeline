# P2 Demo Readiness Checklist

## Purpose
This checklist hardens live demonstration reliability and reviewer experience for the **Deterministic Institutional Expectation-Failure Intelligence Platform**. It is documentation-only and presentation-oriented.

## Demo Readiness Scope
- Confirm environment and repository readiness for live use.
- Confirm deterministic seeded-data visibility and dashboard traceability.
- Confirm replay and certification evidence can be shown quickly.
- Confirm institutional framing and governance boundaries are stated explicitly.
- Explicit exclusion reminder: no autonomous trading, no target prices, no portfolio optimization, no trade execution, no uncontrolled LLM reasoning, no adaptive control systems, no autonomous trading agents, no predictive market forecasting, and no buy/sell/short recommendations.

## Pre-Demo Environment Checklist
- [ ] Use a known-good demo environment consistent with D4 closeout.
- [ ] Confirm required credentials and runtime variables are already configured.
- [ ] Confirm network access is stable for dashboard data reads.
- [ ] Confirm presenter has local copies of P1A/P1B/P1C assets.
- [ ] Confirm clock/timing plan (5-minute and 10-minute versions) is prepared.

## Repository Cleanliness Checklist
- [ ] `git status --short` is clean before demo start.
- [ ] Demo branch/tag is fixed and known to interviewer/reviewer.
- [ ] No in-demo code edits are planned.
- [ ] No package installation or dependency mutation is required.
- [ ] No configuration drift from D4 demo environment closeout.

## Dashboard Startup Checklist
- [ ] Start dashboard using existing certified run method.
- [ ] Confirm home/landing loads without console errors.
- [ ] Confirm key views from O1–O10 certified scope are reachable.
- [ ] Confirm expected tables/figures render in deterministic order.
- [ ] Confirm presenter can move between views without ad-hoc debugging.

## Seeded Data Visibility Checklist
- [ ] Demonstrate deterministic sample-data seeding provenance (D1).
- [ ] Show expected seeded records are visible in dashboard pathways.
- [ ] State that seeded data supports reproducible reviewer walkthroughs.
- [ ] Clarify seeded-data use is for deterministic demonstration and review consistency.

## Replay / Certification Visibility Checklist
- [ ] Show where D3 supervisor playback evidence is stored.
- [ ] Show where D2 visibility certification and D4 closeout reports are stored.
- [ ] Confirm presenter can navigate certification chain without search overhead.
- [ ] Tie replay views to bounded, explainable system behavior.

## Safety Boundary Checklist
- [ ] State platform identity as deterministic and bounded.
- [ ] State this is intelligence support and structural interpretation, not execution automation.
- [ ] Repeat explicit exclusions:
  - no autonomous trading
  - no target prices
  - no portfolio optimization
  - no trade execution
  - no uncontrolled LLM reasoning
  - no adaptive control systems
  - no autonomous trading agents
  - no predictive market forecasting
  - no buy/sell/short recommendations
- [ ] Avoid overreach terms (e.g., "AI hedge fund", "beat the market").

## Screenshot / Artifact Checklist
- [ ] Capture architecture-first sequence screenshots.
- [ ] Capture one deterministic seeded-data visibility screenshot.
- [ ] Capture one replay/certification evidence screenshot.
- [ ] Capture one dashboard structural walkthrough screenshot set.
- [ ] Ensure screenshots contain no sensitive credentials or terminal secrets.

## Interview Readiness Checklist
- [ ] Prepare 30-second, 2-minute, 5-minute, and 10-minute versions.
- [ ] Prepare response set for governance and risk boundary questions.
- [ ] Prepare response set for "what this does not do" questions.
- [ ] Rehearse architecture-first narrative before UI-first walkthrough.
- [ ] End with measured institutional framing and next-step discussion.

## Final Go / No-Go Criteria
**Go** when all checklist categories above are green and demonstration can proceed without runtime improvisation.

**No-Go** when any of the following are unresolved:
- dashboard cannot start or core views fail,
- seeded-data visibility is inconsistent,
- certification chain cannot be shown clearly,
- safety boundary statement is not prepared,
- repository/demo environment is not clean.
