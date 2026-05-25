from scripts.inspect_d7_h1_h2_post_expansion import _build_payload


def test_missing_credentials_blocked_shape(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    payload = _build_payload()
    assert payload["inspection_status"] == "BLOCKED_MISSING_CREDENTIALS"
    assert payload["reason"] == "supabase_client_not_resolved"
    assert "runtime" in payload


def test_no_forbidden_language_or_sql_in_script():
    text = open("scripts/inspect_d7_h1_h2_post_expansion.py", "r", encoding="utf-8").read().lower()
    assert "insert into" not in text
    assert ".insert(" not in text
    assert ".upsert(" not in text
    assert ".update(" not in text
    assert "predict" not in text
    assert "trade" not in text
    assert "autonomous" not in text
