"""SEFI email rendering and delivery helpers."""

from .daily_briefing_email import (
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    DEFAULT_SUBJECT_PREFIX,
    GOVERNANCE_FOOTER,
    EmailConfigError,
    EmailDeliveryError,
    build_subject,
    config_from_env,
    load_daily_briefing,
    render_daily_briefing_html,
    render_daily_briefing_text,
    send_email_smtp,
    write_email_artifacts,
)

__all__ = [
    "DEFAULT_SMTP_HOST",
    "DEFAULT_SMTP_PORT",
    "DEFAULT_SUBJECT_PREFIX",
    "GOVERNANCE_FOOTER",
    "EmailConfigError",
    "EmailDeliveryError",
    "build_subject",
    "config_from_env",
    "load_daily_briefing",
    "render_daily_briefing_html",
    "render_daily_briefing_text",
    "send_email_smtp",
    "write_email_artifacts",
]
