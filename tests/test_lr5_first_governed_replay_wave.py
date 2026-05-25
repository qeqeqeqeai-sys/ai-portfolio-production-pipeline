from pathlib import Path

from scripts.run_lr5_first_governed_replay_wave_review import (
    CANDIDATES,
    build_lr5_report,
    select_first_bounded_batch,
)


def test_lr5_report_builder_exists(tmp_path):
    out = tmp_path / "lr5.md"
    build_lr5_report(out)
    text = out.read_text(encoding="utf-8")
    assert "Phase LR5" in text
    assert "governance boundary confirmation" in text.lower()


def test_bounded_replay_batch_selection_is_deterministic():
    a = [x["candidate_id"] for x in select_first_bounded_batch(CANDIDATES, 2)]
    b = [x["candidate_id"] for x in select_first_bounded_batch(CANDIDATES, 2)]
    assert a == b


def test_selection_avoids_saturation_and_monoculture_when_possible():
    selected = select_first_bounded_batch(CANDIDATES, 2)
    fams = {x["semantic_family"] for x in selected}
    assert len(fams) == 2
    assert max(x["saturation_risk"] for x in selected) <= 0.45


def test_no_direct_sql_path_introduced():
    script_text = Path("scripts/run_lr5_first_governed_replay_wave_review.py").read_text(encoding="utf-8").lower()
    assert "select(" not in script_text
    assert "insert(" not in script_text
    assert "update(" not in script_text
    assert "delete(" not in script_text


def test_assumptions_represented_append_only_checksum_duplicate_prevention():
    text = Path("reports/lr5_first_approved_governed_replay_accumulation_wave.md").read_text(encoding="utf-8")
    assert "append-only" in text
    assert "checksum" in text
    assert "duplicate" in text


def test_workflow_defaults_fail_closed_and_stops_after_first_wave():
    wf = Path(".github/workflows/lr5_first_governed_replay_wave.yml").read_text(encoding="utf-8")
    assert 'default: "true"' in wf
    assert "Fail-closed: DRY_RUN must be false" in wf
    assert "run_d21_limited_governed_backfill.py" in wf
    assert "Stop after first bounded wave" in wf
