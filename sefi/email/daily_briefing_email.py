"""Deterministic Daily Briefing email rendering and optional SMTP delivery.

This module is consumption-only: it reads an existing Daily Briefing JSON view model,
renders HTML/plain text artifacts, and optionally sends them over SMTP when explicitly
enabled by the caller.
"""

from __future__ import annotations

import html as html_lib
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Mapping, Sequence

GOVERNANCE_FOOTER = (
    "Observational ecosystem intelligence report.\n"
    "Read-only analytical output.\n"
    "Not investment advice.\n"
    "No trading recommendation."
)
DEFAULT_SMTP_HOST = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587
DEFAULT_SUBJECT_PREFIX = "SEFI Daily Briefing"


class EmailConfigError(ValueError):
    """Raised when email sending is requested without safe, complete config."""


class EmailDeliveryError(RuntimeError):
    """Raised when SMTP delivery fails after configuration has been validated."""


def load_daily_briefing(path: str | Path) -> dict[str, Any]:
    """Load an existing Daily Briefing JSON artifact from disk."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Daily Briefing JSON root must be an object")
    return payload


def _text(value: Any, default: str = "Not available") -> str:
    if value is None:
        return default
    rendered = str(value).strip()
    return rendered or default


def _escape(value: Any, default: str = "Not available") -> str:
    return html_lib.escape(_text(value, default=default), quote=True)


def _items(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _first_present(item: Mapping[str, Any], keys: Sequence[str], default: str = "Not available") -> str:
    for key in keys:
        if item.get(key) not in (None, "", []):
            return _text(item.get(key), default=default)
    return default


def _item_line(item: Mapping[str, Any]) -> str:
    title = _first_present(item, ("title", "identifier", "story_id"), default="Untitled item")
    summary = _first_present(item, ("summary", "description", "continuity_explanation"), default="No summary supplied")
    metadata = []
    for label, key in (
        ("priority", "priority"),
        ("confidence", "confidence"),
        ("direction", "evolution_direction"),
        ("why now", "why_now"),
    ):
        if item.get(key) not in (None, "", []):
            metadata.append(f"{label}: {_text(item.get(key))}")
    suffix = f" ({'; '.join(metadata)})" if metadata else ""
    return f"{title}: {summary}{suffix}"


def _render_html_items(items: Sequence[Mapping[str, Any]], empty_message: str) -> str:
    if not items:
        return f'<p style="margin:0;color:#64748b;">{_escape(empty_message)}</p>'
    rows = []
    for item in items:
        title = _first_present(item, ("title", "identifier", "story_id"), default="Untitled item")
        summary = _first_present(item, ("summary", "description", "continuity_explanation"), default="No summary supplied")
        badges = []
        for key in ("priority", "confidence", "evolution_direction", "lifecycle_state", "narrative_archetype"):
            if item.get(key) not in (None, "", []):
                badges.append(
                    '<span style="display:inline-block;margin:4px 6px 0 0;padding:2px 6px;'
                    'border-radius:999px;background:#e2e8f0;color:#334155;font-size:12px;">'
                    f'{_escape(key.replace("_", " "))}: {_escape(item.get(key))}</span>'
                )
        why_now = ""
        if item.get("why_now") not in (None, "", []):
            why_now = f'<p style="margin:8px 0 0;color:#475569;"><strong>Why now:</strong> {_escape(item.get("why_now"))}</p>'
        rows.append(
            '<li style="margin:0 0 14px 0;padding:0 0 12px 0;border-bottom:1px solid #e2e8f0;">'
            f'<div style="font-weight:700;color:#0f172a;">{_escape(title)}</div>'
            f'<div style="margin-top:4px;color:#334155;">{_escape(summary)}</div>'
            f'{why_now}'
            f'<div>{"".join(badges)}</div>'
            '</li>'
        )
    return '<ul style="margin:0;padding-left:20px;">' + "".join(rows) + "</ul>"


def _section(title: str, body: str) -> str:
    return (
        '<section style="margin:18px 0;padding:16px;background:#ffffff;border:1px solid #e2e8f0;'
        'border-radius:12px;">'
        f'<h2 style="margin:0 0 12px 0;font-size:18px;color:#0f172a;">{_escape(title)}</h2>'
        f'{body}'
        '</section>'
    )


def _evolution_highlight_items(briefing: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    highlights = briefing.get("evolution_highlights")
    if not isinstance(highlights, Mapping):
        return []
    ordered: list[Mapping[str, Any]] = []
    for key in ("rising_stories", "stable_stories", "falling_stories", "reappearing_stories"):
        ordered.extend(_items(highlights.get(key)))
    return ordered


def _direction_counts(briefing: Mapping[str, Any]) -> dict[str, int]:
    counts = {"rising": 0, "stable": 0, "falling": 0}
    stories = _items(briefing.get("stories"))
    if stories:
        for story in stories:
            direction = str(story.get("evolution_direction") or "").strip().lower()
            if direction in counts:
                counts[direction] += 1
        return counts
    highlights = briefing.get("evolution_highlights")
    if isinstance(highlights, Mapping):
        counts["rising"] = len(_items(highlights.get("rising_stories")))
        counts["stable"] = len(_items(highlights.get("stable_stories")))
        counts["falling"] = len(_items(highlights.get("falling_stories")))
    return counts


def render_daily_briefing_html(briefing: Mapping[str, Any]) -> str:
    """Render a deterministic, escaped, mobile-friendly HTML email body."""

    date = _text(briefing.get("briefing_date"), default="not dated")
    counts = _direction_counts(briefing)
    active_count = len(_items(briefing.get("stories"))) or len(_items(briefing.get("major_developments")))
    summary_rows = "".join(
        f'<td style="padding:10px;border:1px solid #cbd5e1;text-align:center;"><div style="font-size:20px;font-weight:700;color:#0f172a;">{value}</div><div style="font-size:12px;color:#64748b;">{label}</div></td>'
        for label, value in (
            ("Active stories", active_count),
            ("Rising", counts["rising"]),
            ("Stable", counts["stable"]),
            ("Falling", counts["falling"]),
        )
    )
    ecosystem = (
        '<p style="margin:0;color:#334155;">'
        f'Attention level: <strong>{_escape(briefing.get("attention_level"))}</strong><br>'
        f'Quality status: <strong>{_escape(briefing.get("briefing_quality_status"))}</strong><br>'
        f'Confidence labels: {_escape(", ".join(briefing.get("confidence_labels") or []) or "Not available")}'
        '</p>'
    )
    html_body = "".join(
        [
            _section("Ecosystem Summary", ecosystem),
            _section("Active Story Counts", f'<table role="presentation" width="100%" style="border-collapse:collapse;"> <tr>{summary_rows}</tr></table>'),
            _section("Story Evolution Highlights", _render_html_items(_evolution_highlight_items(briefing), "No story evolution highlights supplied.")),
            _section("Top Story Changes", _render_html_items(_items(briefing.get("major_developments")), "No top story changes supplied.")),
            _section("Why Now Summaries", _render_html_items(_items(briefing.get("stories")), "No story-level why-now summaries supplied.")),
            _section("Investigation Queue", _render_html_items(_items(briefing.get("investigation_candidates")), "No investigation queue items supplied.")),
        ]
    )
    footer = "<br>".join(_escape(line) for line in GOVERNANCE_FOOTER.splitlines())
    return (
        '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>SEFI Daily Briefing | {_escape(date)}</title></head>'
        '<body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">'
        '<main style="max-width:720px;margin:0 auto;padding:20px;">'
        '<header style="padding:20px;background:#0f172a;border-radius:14px;color:#ffffff;">'
        '<div style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#cbd5e1;">SEFI Daily Briefing</div>'
        f'<h1 style="margin:8px 0 0 0;font-size:24px;line-height:1.25;">Snapshot {_escape(date)}</h1>'
        '</header>'
        f'{html_body}'
        '<footer style="margin:18px 0 0 0;padding:16px;color:#475569;font-size:13px;line-height:1.5;">'
        f'{footer}'
        '</footer></main></body></html>'
    )


def _text_section(title: str, lines: Sequence[str]) -> str:
    body = "\n".join(lines) if lines else "No items supplied."
    return f"{title}\n{'=' * len(title)}\n{body}"


def _text_lines(items: Sequence[Mapping[str, Any]], empty_message: str) -> list[str]:
    if not items:
        return [empty_message]
    return [f"- {_item_line(item)}" for item in items]


def render_daily_briefing_text(briefing: Mapping[str, Any]) -> str:
    """Render a deterministic plain text email body."""

    date = _text(briefing.get("briefing_date"), default="not dated")
    counts = _direction_counts(briefing)
    active_count = len(_items(briefing.get("stories"))) or len(_items(briefing.get("major_developments")))
    sections = [
        f"SEFI Daily Briefing | {date}",
        _text_section(
            "Ecosystem Summary",
            [
                f"Attention level: {_text(briefing.get('attention_level'))}",
                f"Quality status: {_text(briefing.get('briefing_quality_status'))}",
                f"Confidence labels: {', '.join(briefing.get('confidence_labels') or []) or 'Not available'}",
            ],
        ),
        _text_section("Active Story Counts", [f"Active stories: {active_count}", f"Rising: {counts['rising']}", f"Stable: {counts['stable']}", f"Falling: {counts['falling']}"]),
        _text_section("Story Evolution Highlights", _text_lines(_evolution_highlight_items(briefing), "No story evolution highlights supplied.")),
        _text_section("Top Story Changes", _text_lines(_items(briefing.get("major_developments")), "No top story changes supplied.")),
        _text_section("Why Now Summaries", _text_lines(_items(briefing.get("stories")), "No story-level why-now summaries supplied.")),
        _text_section("Investigation Queue", _text_lines(_items(briefing.get("investigation_candidates")), "No investigation queue items supplied.")),
        GOVERNANCE_FOOTER,
    ]
    return "\n\n".join(sections) + "\n"


def write_email_artifacts(html: str, text: str, output_dir: str | Path) -> dict[str, str]:
    """Write daily_email.html and daily_email.txt artifacts."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    html_path = target / "daily_email.html"
    text_path = target / "daily_email.txt"
    html_path.write_text(html, encoding="utf-8")
    text_path.write_text(text, encoding="utf-8")
    return {"html_path": str(html_path), "text_path": str(text_path)}


def build_subject(briefing: Mapping[str, Any], prefix: str | None = None) -> str:
    """Build a deterministic email subject with snapshot date when available."""

    subject_prefix = _text(prefix or os.environ.get("SEFI_EMAIL_SUBJECT_PREFIX"), default=DEFAULT_SUBJECT_PREFIX)
    date = _text(briefing.get("briefing_date"), default="")
    return f"{subject_prefix} | {date}" if date and date != "not dated" else subject_prefix


def config_from_env() -> dict[str, Any]:
    return {
        "enabled": os.environ.get("SEFI_EMAIL_ENABLED", ""),
        "smtp_host": os.environ.get("SEFI_EMAIL_SMTP_HOST", DEFAULT_SMTP_HOST),
        "smtp_port": os.environ.get("SEFI_EMAIL_SMTP_PORT", str(DEFAULT_SMTP_PORT)),
        "smtp_user": os.environ.get("SEFI_EMAIL_SMTP_USER", ""),
        "smtp_app_password": os.environ.get("SEFI_EMAIL_SMTP_APP_PASSWORD", ""),
        "from_addr": os.environ.get("SEFI_EMAIL_FROM", ""),
        "to_addr": os.environ.get("SEFI_EMAIL_TO", ""),
    }


def _require_send_config(config: Mapping[str, Any]) -> dict[str, Any]:
    if str(config.get("enabled", "")).strip().lower() != "true":
        raise EmailConfigError("Email sending requested but SEFI_EMAIL_ENABLED is not true.")
    required = ("smtp_user", "smtp_app_password", "from_addr", "to_addr")
    missing = [key for key in required if not str(config.get(key) or "").strip()]
    if missing:
        raise EmailConfigError("Email sending requested but required email configuration is missing: SMTP credentials, sender, or recipient.")
    try:
        port = int(config.get("smtp_port") or DEFAULT_SMTP_PORT)
    except (TypeError, ValueError) as exc:
        raise EmailConfigError("Email SMTP port must be an integer.") from exc
    return {
        "smtp_host": str(config.get("smtp_host") or DEFAULT_SMTP_HOST),
        "smtp_port": port,
        "smtp_user": str(config["smtp_user"]),
        "smtp_app_password": str(config["smtp_app_password"]),
        "from_addr": str(config["from_addr"]),
        "to_addr": str(config["to_addr"]),
    }


def send_email_smtp(html: str, text: str, subject: str, config: Mapping[str, Any]) -> None:
    """Send a multipart email with STARTTLS SMTP using a prevalidated config."""

    safe_config = _require_send_config(config)
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = safe_config["from_addr"]
    message["To"] = safe_config["to_addr"]
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(safe_config["smtp_host"], safe_config["smtp_port"], timeout=30) as smtp:
            smtp.starttls(context=context)
            smtp.login(safe_config["smtp_user"], safe_config["smtp_app_password"])
            smtp.send_message(message)
    except Exception as exc:  # noqa: BLE001 - sanitize all provider/library errors before surfacing.
        raise EmailDeliveryError(f"SMTP email delivery failed: {exc.__class__.__name__}") from None
