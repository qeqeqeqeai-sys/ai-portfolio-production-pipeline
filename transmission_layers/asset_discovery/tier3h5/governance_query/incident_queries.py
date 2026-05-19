from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import INCIDENT_HISTORY_PATH

from .base import apply_filters, bounded_window, history_rows, paginate


def query_governance_incidents(*, page: int = 1, page_size: int = 100, window: int | None = None, **filters: Any) -> dict[str, Any]:
    rows = bounded_window(apply_filters(history_rows(INCIDENT_HISTORY_PATH), **filters), window)
    return paginate(rows, page=page, page_size=page_size)


def query_replay_instability_history(**kwargs: Any) -> dict[str, Any]:
    return query_governance_incidents(governance_domain="replay_governance_incident", **kwargs)


def query_lineage_instability_history(**kwargs: Any) -> dict[str, Any]:
    return query_governance_incidents(governance_domain="lineage_integrity_incident", **kwargs)


def query_provenance_degradation_history(**kwargs: Any) -> dict[str, Any]:
    return query_governance_incidents(governance_domain="provenance_governance_incident", **kwargs)


def query_normalization_drift_history(**kwargs: Any) -> dict[str, Any]:
    return query_governance_incidents(governance_domain="normalization_governance_incident", **kwargs)


def query_cross_registry_instability_history(**kwargs: Any) -> dict[str, Any]:
    return query_governance_incidents(governance_domain="cross_registry_governance_incident", **kwargs)
