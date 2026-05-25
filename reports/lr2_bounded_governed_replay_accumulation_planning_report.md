# Phase LR2 — Bounded Governed Replay Accumulation Planning

## 1) Scope, objective, and hard-constraint confirmation
Objective: prepare the **first bounded governed replay accumulation wave** for longitudinal IX observation, using existing CD2/CD3/CD4/CD5 guidance where available.

Confirmed constraints held in this planning phase:
- No autonomous replay execution.
- No autonomous approval.
- No direct SQL.
- No writes outside approved D8.B4/D21 governed replay flows.
- No predictive/trading outputs.
- Deterministic reproducibility preserved.
- Append-only semantics preserved.
- Checksum lineage posture preserved.
- Additive architecture preserved.
- No IX6/CD6/H4/foundational architecture expansion.

This LR2 phase is planning-only and read-only.

## 2) CD2/CD3/CD4/CD5 candidate availability assessment

### 2.1 Artifacts inspected
- `reports/lr1_governed_replay_accumulation_longitudinal_ix_observation_report.md`
- `reports/ix_longitudinal_replay_review.json`
- `reports/d8_b2r_replay_candidate_source_repair_audit_report.md`
- `reports/deep_d7_h1_h2_semantic_inspection_report.md`
- `reports/d7_h1_h2_post_expansion_inspection_report.md`
- `scripts/run_d21_limited_governed_backfill.py`

### 2.2 Availability conclusion by CD layer
1. **CD2 (novelty prioritization intent): AVAILABLE (policy-level), PARTIAL (explicit ranked candidate list absent).**
   - LR1 and deep semantic inspection both identify diversity/novelty as priority axes.
2. **CD3 (governed novelty-guided expansion intent): AVAILABLE (process-level).**
   - Existing bounded offset/window governance pattern is present in prior reports.
3. **CD4 (drift/saturation intelligence): AVAILABLE (signal-level), PARTIAL (live metrics may be credential-gated).**
   - LR1 has novelty drought/saturation signal; deep inspection flags richness-improving-but-sublinear dynamic.
4. **CD5 (operator adjudication assist): AVAILABLE (control-level).**
   - D21 approval token gating is explicitly codified in script-level flow.

### 2.3 Candidate-window readiness conclusion
Usable candidate-window planning context **exists** (from prior bounded window IDs and offset progression), but a fresh environment-specific ranked candidate table is not embedded in repository artifacts. Therefore LR2 proceeds with **bounded first-wave recommendations** tied to known deterministic window slicing and explicit operator checkpointing.

## 3) LR1 baseline carry-forward (for gating)
- run_count=0 in current repository-local IX review input path.
- IX1–IX5 coverage all 0 in that local review context.
- novelty ratio=0.0 in that local review context.
- minimum target: 5 total governed replay runs.
- practical target: 6–8 governed replay runs.

Implication: first wave should prioritize **diversity-per-run** over raw count scaling.

## 4) First-wave bounded replay accumulation plan (recommended)

## Batch A (start first): contradiction/continuity diversity probe
- **Batch size:** 2 governed runs.
- **Candidate source/artifact reference:** deterministic offset-slice progression after previously selected windows (`W16–W18` context) via governed D21 window selection flow.
- **Novelty rationale:** target windows expected to maximize contradiction recurrence under adjacent-but-non-identical continuity states.
- **Expected structural value:** fastest path to first non-zero signal for continuity-transition and contradiction persistence/mutation traces in IX longitudinal review.
- **Saturation risk:** medium if adjacent windows are too semantically similar; mitigate by rejecting near-duplicate theme signatures during operator review.
- **Governance requirements:** D8.B4/D21 bounded flow only, deterministic candidate derivation, append-only writes, lineage/checksum verification post-run.
- **Approval required before non-dry execution:** **Yes** (mandatory operator approval).

## Batch B (execute only after Batch A readback review): confidence/semantic/regime diversity probe
- **Batch size:** 2 governed runs.
- **Candidate source/artifact reference:** same deterministic candidate source family, but select windows with maximal semantic-theme and regime-transition delta vs Batch A.
- **Novelty rationale:** diversify away from pattern-family density by intentionally selecting different theme/regime contexts.
- **Expected structural value:** increases confidence-transition visibility and semantic-theme novelty ratio while reducing monoculture risk.
- **Saturation risk:** low-to-medium if explicit anti-monoculture selection rules are applied; high if selection defaults to nearest-offset-only similarity.
- **Governance requirements:** same D8.B4/D21 approval-gated bounded execution; deterministic parameter freeze; checksum lineage and duplicate prevention verification.
- **Approval required before non-dry execution:** **Yes** (mandatory operator approval).

## 5) First-batch replay diversity rationale
To avoid replay monoculture, semantic saturation, repeated pattern-family density, and replay-density-without-richness:
1. Use **1–2 small batches** first (2 + 2), not all 6–8 runs.
2. Enforce per-batch novelty objective separation:
   - Batch A: contradiction + continuity-transition novelty.
   - Batch B: confidence-transition + semantic-theme + regime-transition novelty.
3. Apply operator-side exclusion checks before approval:
   - exclude near-duplicate theme families,
   - exclude same regime cluster dominance,
   - exclude windows with marginal structural information gain below threshold.
4. After Batch A, run read-only IX longitudinal review before Batch B execution decision.

## 6) Candidate evaluation template (for operator use)
For each proposed window candidate, score:
- contradiction novelty (0–3)
- continuity-transition novelty (0–3)
- confidence-transition novelty (0–3)
- semantic-theme novelty (0–3)
- regime-transition novelty (0–3)
- marginal structural information gain (0–3)
- saturation risk penalty (0 to -3)

Select bounded windows with highest net diversity score under governance constraints.

## 7) Operator approval checklist (stop here before any non-dry run)
1. Confirm run mode is governed D8.B4/D21 flow only.
2. Confirm deterministic window parameters (count/offset/candidate IDs) are frozen and recorded.
3. Confirm no direct SQL path is introduced.
4. Confirm no autonomous approval; explicit operator token/action required.
5. Confirm append-only semantics and duplicate prevention are active.
6. Confirm checksum lineage capture is active for all planned runs.
7. Confirm no predictive/trading outputs are requested or emitted.
8. Execute dry-run diagnostics first; review source readiness and candidate derivation status.
9. Approve Batch A only (2 runs) for non-dry execution.
10. After Batch A completion, perform read-only LR review and approve/adjust Batch B.

## 8) Governance boundary confirmation
Planning activity in LR2 remained within governance boundaries:
- read-only planning and artifact inspection only,
- no replay execution,
- no approvals issued,
- no direct SQL,
- no new architecture/intelligence/governance foundational layer added.

## 9) Architecture pause recommendation
Recommendation: **keep architecture expansion paused** until at least 5 total governed runs are accumulated and IX1–IX5 longitudinal coverage shows non-zero continuity/contradiction/confidence/regime/thematic signals with acceptable saturation risk.
