from __future__ import annotations

import json
import smtplib
import sys

import pytest

from sefi.email.daily_briefing_email import (
    GOVERNANCE_FOOTER,
    EmailConfigError,
    EmailDeliveryError,
    build_subject,
    load_daily_briefing,
    render_daily_briefing_html,
    render_daily_briefing_text,
    send_email_smtp,
    write_email_artifacts,
)
from scripts import run_daily_briefing_email


def _briefing() -> dict:
    return {
        "briefing_date": "2026-05-30",
        "attention_level": "high",
        "briefing_quality_status": "strong",
        "confidence_labels": ["high", "medium"],
        "major_developments": [
            {
                "title": "Top <Story>",
                "summary": "Revenue & supply pressure changed",
                "priority": "high",
                "confidence": "high",
                "evolution_direction": "rising",
                "why_now": "priority increased versus previous appearance",
            }
        ],
        "stories": [
            {
                "title": "Story Alpha",
                "summary": "Structural change remains visible",
                "priority": "medium",
                "confidence": "medium",
                "evolution_direction": "stable",
                "why_now": "no material change detected",
            }
        ],
        "investigation_candidates": [
            {
                "title": "Investigate beta",
                "summary": "Live-only anomaly requires review",
                "priority": "high",
                "confidence": "medium",
            }
        ],
        "evolution_highlights": {
            "rising_stories": [
                {
                    "title": "Rising Story",
                    "summary": "Momentum increased",
                    "evolution_direction": "rising",
                    "why_now": "confidence improved versus previous appearance",
                }
            ],
            "stable_stories": [],
            "falling_stories": [],
        },
    }


def test_html_renderer_escapes_and_includes_governance_footer():
    html = render_daily_briefing_html(_briefing())

    assert "Top &lt;Story&gt;" in html
    assert "Top <Story>" not in html
    assert "Revenue &amp; supply pressure changed" in html
    assert "Not investment advice." in html
    assert "No trading recommendation." in html


def test_text_renderer_includes_major_sections_and_governance_footer():
    text = render_daily_briefing_text(_briefing())

    for section in (
        "Ecosystem Summary",
        "Active Story Counts",
        "Story Evolution Highlights",
        "Top Story Changes",
        "Why Now Summaries",
        "Investigation Queue",
    ):
        assert section in text
    assert GOVERNANCE_FOOTER in text


def test_write_artifacts_and_load_daily_briefing(tmp_path):
    source = tmp_path / "daily_briefing.json"
    source.write_text(json.dumps(_briefing()), encoding="utf-8")

    briefing = load_daily_briefing(source)
    paths = write_email_artifacts("<html></html>", "text", tmp_path / "email")

    assert briefing["briefing_date"] == "2026-05-30"
    assert (tmp_path / "email" / "daily_email.html").read_text(encoding="utf-8") == "<html></html>"
    assert (tmp_path / "email" / "daily_email.txt").read_text(encoding="utf-8") == "text"
    assert paths["html_path"].endswith("daily_email.html")
    assert paths["text_path"].endswith("daily_email.txt")


def test_missing_secrets_handled_safely():
    with pytest.raises(EmailConfigError) as excinfo:
        send_email_smtp("html", "text", "subject", {"enabled": "true", "smtp_user": "user@example.com"})

    message = str(excinfo.value)
    assert "required email configuration is missing" in message
    assert "password" not in message.lower()
    assert "secret" not in message.lower()


def test_subject_includes_date_when_available():
    assert build_subject(_briefing()) == "SEFI Daily Briefing | 2026-05-30"
    assert build_subject({"briefing_date": ""}, prefix="Custom") == "Custom"


def test_smtp_exceptions_do_not_leak_credentials(monkeypatch):
    class FailingSMTP:
        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self, context):
            return None

        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"app-password-123")

        def send_message(self, message):
            return None

    monkeypatch.setattr(smtplib, "SMTP", FailingSMTP)
    with pytest.raises(EmailDeliveryError) as excinfo:
        send_email_smtp(
            "html",
            "text",
            "subject",
            {
                "enabled": "true",
                "smtp_host": "smtp.gmail.com",
                "smtp_port": "587",
                "smtp_user": "sender@example.com",
                "smtp_app_password": "app-password-123",
                "from_addr": "sender@example.com",
                "to_addr": "recipient@example.com",
            },
        )

    message = str(excinfo.value)
    assert "SMTPAuthenticationError" in message
    assert "app-password-123" not in message
    assert "sender@example.com" not in message


def test_cli_without_send_does_not_attempt_send(tmp_path, monkeypatch, capsys):
    input_json = tmp_path / "daily_briefing.json"
    input_json.write_text(json.dumps(_briefing()), encoding="utf-8")

    def fail_send(*args, **kwargs):  # pragma: no cover - should never execute
        raise AssertionError("send should not be attempted")

    monkeypatch.setattr(run_daily_briefing_email, "send_email_smtp", fail_send)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_daily_briefing_email.py",
            "--input-json",
            str(input_json),
            "--output-dir",
            str(tmp_path / "email"),
        ],
    )

    assert run_daily_briefing_email.main() == 0
    assert (tmp_path / "email" / "daily_email.html").exists()
    assert (tmp_path / "email" / "daily_email.txt").exists()
    assert '"send_requested": false' in capsys.readouterr().out


def test_cli_with_missing_secrets_fails_safely(tmp_path, monkeypatch, capsys):
    input_json = tmp_path / "daily_briefing.json"
    input_json.write_text(json.dumps(_briefing()), encoding="utf-8")
    monkeypatch.delenv("SEFI_EMAIL_ENABLED", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_daily_briefing_email.py",
            "--input-json",
            str(input_json),
            "--output-dir",
            str(tmp_path / "email"),
            "--send",
        ],
    )

    assert run_daily_briefing_email.main() == 2
    err = capsys.readouterr().err
    assert "SEFI_EMAIL_ENABLED is not true" in err
    assert "password" not in err.lower()


def test_cli_smtp_delivery_failure_warns_and_keeps_success(tmp_path, monkeypatch, capsys):
    input_json = tmp_path / "daily_briefing.json"
    input_json.write_text(json.dumps(_briefing()), encoding="utf-8")

    def fail_delivery(*args, **kwargs):
        raise EmailDeliveryError("SMTP email delivery failed: SMTPServerDisconnected")

    monkeypatch.setattr(run_daily_briefing_email, "send_email_smtp", fail_delivery)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_daily_briefing_email.py",
            "--input-json",
            str(input_json),
            "--output-dir",
            str(tmp_path / "email"),
            "--send",
        ],
    )

    assert run_daily_briefing_email.main() == 0
    assert (tmp_path / "email" / "daily_email.html").exists()
    assert (tmp_path / "email" / "daily_email.txt").exists()
    captured = capsys.readouterr()
    assert "WARNING: SMTP email delivery failed: SMTPServerDisconnected" in captured.err
    assert '"email_warning"' in captured.out
