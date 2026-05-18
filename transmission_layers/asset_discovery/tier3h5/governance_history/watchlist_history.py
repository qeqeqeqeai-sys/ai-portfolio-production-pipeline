from __future__ import annotations

from typing import Any

from .hashing import stable_hash


def normalize_watchlists(summary: dict[str, Any]) -> list[dict[str, Any]]:
    watchlists = summary.get("watchlists", {}) if isinstance(summary.get("watchlists"), dict) else {}
    rows = []
    for name in sorted(watchlists):
        items = watchlists.get(name, []) if isinstance(watchlists.get(name), list) else []
        item_hashes = [item.get("watchlist_item_hash") or stable_hash(item) for item in items if isinstance(item, dict)]
        row = {
            "watchlist_history_id": f"tier3h5-watchlist-history-{stable_hash({'name': name, 'items': item_hashes})[:16]}",
            "watchlist_name": name,
            "watchlist_count": len(item_hashes),
            "watchlist_item_hashes": sorted(item_hashes),
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
        }
        row["watchlist_evolution_hash"] = stable_hash(row)
        rows.append(row)
    return rows
