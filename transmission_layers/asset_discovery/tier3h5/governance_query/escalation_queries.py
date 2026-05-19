from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import ESCALATION_HISTORY_PATH

from .base import apply_filters, bounded_window, history_rows, paginate


def query_escalation_history(*, page: int = 1, page_size: int = 100, window: int | None = None, **filters: Any) -> dict[str, Any]:
    rows = bounded_window(apply_filters(history_rows(ESCALATION_HISTORY_PATH), **filters), window)
    return paginate(rows, page=page, page_size=page_size)
