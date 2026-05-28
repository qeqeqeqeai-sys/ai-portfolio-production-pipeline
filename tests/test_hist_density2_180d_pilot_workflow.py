from pathlib import Path

WORKFLOW_PATH = Path('.github/workflows/hist_density2_180d_pilot.yml')

def test_manual_trigger_only() -> None:
    text = WORKFLOW_PATH.read_text(encoding='utf-8')
    assert 'workflow_dispatch:' in text
    assert 'push:' not in text and 'pull_request:' not in text and 'schedule:' not in text

def test_safety_defaults() -> None:
    text = WORKFLOW_PATH.read_text(encoding='utf-8').lower()
    assert 'supabase' not in text
    assert 'replay' not in text
    assert 'git push' not in text
