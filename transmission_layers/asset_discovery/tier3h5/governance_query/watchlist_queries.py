from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import WATCHLIST_HISTORY_PATH

from .base import apply_filters, bounded_window, history_rows, paginate


def query_governance_watchlists(*, page: int = 1, page_size: int = 100, window: int | None = None, watchlist_name: str | None = None, **filters: Any) -> dict[str, Any]:
    rows = apply_filters(history_rows(WATCHLIST_HISTORY_PATH), **filters)
    if watchlist_name is not None:
        rows = [row for row in rows if str(row.get("watchlist_name")) == str(watchlist_name)]
    return paginate(bounded_window(rows, window), page=page, page_size=page_size)
