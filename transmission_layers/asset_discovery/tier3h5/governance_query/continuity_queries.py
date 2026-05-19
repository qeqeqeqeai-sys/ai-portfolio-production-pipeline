from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.artifacts import CONTINUITY_HISTORY_PATH, HISTORY_SUMMARY_PATH
from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import load_json

from .base import apply_filters, bounded_window, history_rows, paginate


def query_governance_continuity(*, page: int = 1, page_size: int = 100, window: int | None = None, **filters: Any) -> dict[str, Any]:
    rows = history_rows(CONTINUITY_HISTORY_PATH)
    if not rows:
        summary = load_json(HISTORY_SUMMARY_PATH)
        rows = [summary] if summary else []
    rows = bounded_window(apply_filters(rows, **filters), window)
    return paginate(rows, page=page, page_size=page_size)
