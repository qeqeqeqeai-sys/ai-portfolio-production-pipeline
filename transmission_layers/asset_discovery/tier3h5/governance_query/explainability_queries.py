from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.artifacts import EXPLAINABILITY_PATH
from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import load_json

EXPLANATION_KEYS = ("persistence_explanation", "trend_explanation", "continuity_explanation", "lifecycle_explanation")


def query_governance_explainability(explanation_type: str | None = None) -> dict[str, Any]:
    payload = load_json(EXPLAINABILITY_PATH)
    if explanation_type is None:
        explanations = {key: payload.get(key, {}) for key in EXPLANATION_KEYS}
    else:
        if explanation_type not in EXPLANATION_KEYS:
            explanations = {}
        else:
            explanations = {explanation_type: payload.get(explanation_type, {})}
    return {
        "explainability_source": "persisted_governance_history_only",
        "explanations": explanations,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
