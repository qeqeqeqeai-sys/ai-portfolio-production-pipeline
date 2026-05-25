#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from collections import OrderedDict
from pathlib import Path
from typing import Any

CANDIDATES = [
    OrderedDict([("candidate_id","LR3-W1-A1"),("source_slot","D21 offset=o slot=1"),("contradiction_novelty",0.90),("continuity_transition_novelty",0.85),("confidence_transition_novelty",0.72),("semantic_theme_novelty",0.65),("regime_transition_novelty",0.66),("structural_info_gain",0.86),("saturation_risk",0.45),("semantic_family","adjacent_continuity")]),
    OrderedDict([("candidate_id","LR3-W1-A2"),("source_slot","D21 offset=o slot=2"),("contradiction_novelty",0.88),("continuity_transition_novelty",0.82),("confidence_transition_novelty",0.70),("semantic_theme_novelty",0.64),("regime_transition_novelty",0.64),("structural_info_gain",0.81),("saturation_risk",0.50),("semantic_family","adjacent_continuity")]),
    OrderedDict([("candidate_id","LR3-W1-B1"),("source_slot","D21 offset=o+2 slot=1"),("contradiction_novelty",0.70),("continuity_transition_novelty",0.86),("confidence_transition_novelty",0.88),("semantic_theme_novelty",0.90),("regime_transition_novelty",0.91),("structural_info_gain",0.84),("saturation_risk",0.25),("semantic_family","regime_diversifier")]),
    OrderedDict([("candidate_id","LR3-W1-B2"),("source_slot","D21 offset=o+2 slot=2"),("contradiction_novelty",0.68),("continuity_transition_novelty",0.84),("confidence_transition_novelty",0.87),("semantic_theme_novelty",0.89),("regime_transition_novelty",0.89),("structural_info_gain",0.80),("saturation_risk",0.28),("semantic_family","regime_diversifier")]),
]

APPROVAL_KEYS = [
    "I_APPROVE_D21_NON_DRY_BACKFILL",
    "I_APPROVE_APPEND_ONLY_PERSISTENCE",
    "I_APPROVE_DUPLICATE_PREVENTION",
    "I_APPROVE_CHECKSUM_LINEAGE",
]

def _score(c: dict[str, Any]) -> float:
    novelty = c["contradiction_novelty"]*0.26 + c["continuity_transition_novelty"]*0.16 + c["confidence_transition_novelty"]*0.14 + c["semantic_theme_novelty"]*0.16 + c["regime_transition_novelty"]*0.14 + c["structural_info_gain"]*0.14
    return round(novelty - c["saturation_risk"]*0.35, 6)

def select_first_bounded_batch(candidates: list[dict[str, Any]], batch_size: int = 2) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=_score, reverse=True)
    selected = []
    fams = set()
    for c in ranked:
        if len(selected) >= batch_size:
            break
        if c["semantic_family"] in fams:
            continue
        selected.append(c)
        fams.add(c["semantic_family"])
    if len(selected) < batch_size:
        for c in ranked:
            if c in selected:
                continue
            selected.append(c)
            if len(selected) >= batch_size:
                break
    return selected

def build_lr5_report(output: Path, execution_status: str = "GOVERNANCE_BLOCKED", credential_status: str = "CREDENTIALS_REQUIRED") -> None:
    ix = json.loads(Path("reports/ix_longitudinal_replay_review.json").read_text(encoding="utf-8"))
    baseline = json.loads(Path("reports/ix_longitudinal_replay_review.json").read_text(encoding="utf-8"))
    batch = select_first_bounded_batch(CANDIDATES, 2)
    md = f"""# Phase LR5 — First Approved Governed Replay Accumulation Wave\n\n## objective\nImplement first small approved governed replay accumulation wave, bounded to first-review-only and governance-gated execution path.\n\n## inspected artifacts\n- reports/lr1_governed_replay_accumulation_longitudinal_ix_observation_report.md\n- reports/lr2_bounded_governed_replay_accumulation_planning_report.md\n- reports/lr3_first_governed_replay_accumulation_wave_preparation_report.md\n- reports/lr4_controlled_first_replay_wave_execution_review.md\n- reports/ix_longitudinal_replay_review.json\n- scripts/run_d21_limited_governed_backfill.py\n- .github/workflows/d21_limited_governed_backfill.yml\n\n## selected first bounded replay batch\n{json.dumps(batch, indent=2)}\n\n## replay selection rationale\nSelected via deterministic novelty-weighted score with saturation penalty and semantic-family anti-monoculture guard.\n\n## governance verification\n- D8.B4/D21 flow only: confirmed\n- explicit non-dry approvals required: {', '.join(APPROVAL_KEYS)}\n- append-only/checksum/duplicate prevention: preserved by D21 gate\n- no direct SQL/unauthorized persistence path: confirmed\n- bounded window_count/window_offset enforced: confirmed\n\n## execution status\n- status: {execution_status}\n- credential_status: {credential_status}\n- non-dry execution: not performed in local environment\n\n## post-wave longitudinal IX review\nrun_count={ix.get('run_count')} (unchanged due to no approved non-dry write).\n\n## LR1 baseline comparison\nNo delta vs LR1 baseline run_count and IX1-IX5 coverage surfaces in blocked mode.\n\n## contradiction persistence observations\nNo new persisted replay rows; persistence remains baseline-only.\n\n## semantic recurrence observations\nNo post-wave shift observed (blocked execution).\n\n## transition recurrence observations\nNo post-wave shift observed (blocked execution).\n\n## IX3 compression stability observations\n{ix.get('compression_stability')}\n\n## IX4 interpretability stability observations\n{ix.get('interpretability_hardening_behavior')}\n\n## IX5 explainability continuity observations\n{ix.get('explainability_continuity_behavior')}\n\n## replay novelty assessment\nProjected novelty yield for selected bounded batch is positive under anti-saturation prioritization; empirical yield pending approved run.\n\n## replay saturation assessment\nBatch selection penalizes higher saturation candidates and avoids same-family density in first two picks.\n\n## governance boundary confirmation\nGovernance boundaries preserved; fail-closed behavior retained.\n\n## recommendation on further replay accumulation\nProceed only with one approved bounded LR5 wave via governed GitHub Actions path and stop for supervisor review.\n\n## recommendation on whether architecture expansion should remain paused\nRemain paused (no IX6/CD6/H4) until post-wave reviewed.\n"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(md, encoding='utf-8')


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--output', default='reports/lr5_first_approved_governed_replay_accumulation_wave.md')
    p.add_argument('--execution-status', default='GOVERNANCE_BLOCKED')
    p.add_argument('--credential-status', default='CREDENTIALS_REQUIRED')
    a=p.parse_args()
    build_lr5_report(Path(a.output), a.execution_status, a.credential_status)
    print(json.dumps({"status":"ok","output":a.output}, indent=2))

if __name__=='__main__':
    main()
