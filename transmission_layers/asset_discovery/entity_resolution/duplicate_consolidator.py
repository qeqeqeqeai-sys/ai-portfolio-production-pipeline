from __future__ import annotations
import hashlib


def duplicate_group_key(row: dict) -> str:
    raw = "|".join([
        str(row.get("normalized_ticker") or ""),
        str(row.get("normalized_exchange") or ""),
        str(row.get("normalized_name") or ""),
        str(row.get("asset_type_guess") or ""),
        str(row.get("theme_name") or ""),
        str(row.get("run_date_sgt") or ""),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def apply_duplicate_sizes(rows: list[dict]) -> list[dict]:
    counts = {}
    for row in rows:
        key = duplicate_group_key(row)
        counts[key] = counts.get(key, 0) + 1
        row["duplicate_group_key"] = key
    for row in rows:
        row["duplicate_group_size"] = counts.get(row["duplicate_group_key"], 1)
    return rows
