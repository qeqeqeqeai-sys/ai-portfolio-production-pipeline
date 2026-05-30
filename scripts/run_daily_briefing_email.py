#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sefi.email.daily_briefing_email import (  # noqa: E402
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Render and optionally send SEFI Daily Briefing email artifacts.")
    parser.add_argument("--input-json", required=True, help="Existing Daily Briefing JSON artifact path.")
    parser.add_argument("--output-dir", required=True, help="Directory for daily_email.html and daily_email.txt.")
    parser.add_argument("--send", action="store_true", help="Send email via Gmail SMTP when SEFI_EMAIL_ENABLED=true and secrets are present.")
    args = parser.parse_args()

    briefing = load_daily_briefing(args.input_json)
    html = render_daily_briefing_html(briefing)
    text = render_daily_briefing_text(briefing)
    paths = write_email_artifacts(html, text, args.output_dir)
    subject = build_subject(briefing)

    result = {"status": "ok", "send_requested": bool(args.send), "subject": subject, **paths}
    if not args.send:
        print(json.dumps(result, sort_keys=True))
        return 0

    try:
        send_email_smtp(html, text, subject, config_from_env())
    except EmailConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except EmailDeliveryError as exc:
        result["email_warning"] = str(exc)
        print(f"WARNING: {exc}", file=sys.stderr)
        print(json.dumps(result, sort_keys=True))
        return 0

    result["email_sent"] = True
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
