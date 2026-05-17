from __future__ import annotations
import re


def normalize_ticker(raw_ticker: str | None) -> tuple[str | None, bool]:
    if not raw_ticker:
        return None, False
    cleaned = re.sub(r"[\s\[\](){}$]", "", str(raw_ticker).upper())
    cleaned = re.sub(r"[^A-Z0-9.-]", "", cleaned)
    if not cleaned:
        return None, False
    suspicious = len(cleaned) > 8 or not re.match(r"^[A-Z0-9][A-Z0-9.-]*$", cleaned)
    return cleaned, suspicious
