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


def test_cache_inputs_exist_with_false_defaults() -> None:
    text = WORKFLOW_PATH.read_text(encoding='utf-8')
    assert 'raw_cache_enabled:' in text
    assert 'description: "Enable raw FMP cache reads"' in text
    assert 'raw_cache_write_enabled:' in text
    assert 'description: "Enable raw FMP cache writes"' in text
    assert text.count('default: "false"') >= 2
    assert 'options: ["false", "true"]' in text


def test_cache_flags_only_enabled_when_input_true() -> None:
    text = WORKFLOW_PATH.read_text(encoding='utf-8')
    assert 'INPUT_RAW_CACHE_ENABLED' in text
    assert 'INPUT_RAW_CACHE_WRITE_ENABLED' in text
    assert '[ "$INPUT_RAW_CACHE_ENABLED" = "true" ] && echo --raw-cache-enabled' in text
    assert '[ "$INPUT_RAW_CACHE_WRITE_ENABLED" = "true" ] && echo --raw-cache-write-enabled' in text
