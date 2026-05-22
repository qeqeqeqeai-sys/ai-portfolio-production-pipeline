from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Dict, Mapping, Sequence, Tuple

from transmission_layers.alpha.layer_a import ALPHA_CLASSIFICATIONS

REGIME_OUTCOMES: Tuple[str, ...] = (
    "works",
    "fails",
    "decays",
    "inverts",
    "insufficient_data",
    "invalid_input",
)


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _outcome(classification: str, factor_decay: float, ic: float, rank_ic: float) -> str:
    if classification in {"invalid_input", "insufficient_data"}:
        return classification
    if ic < -0.05 and rank_ic < -0.05:
        return "inverts"
    if factor_decay > 0.15:
        return "decays"
    if classification in {"strong_positive_efficacy", "moderate_positive_efficacy", "weak_positive_efficacy"}:
        return "works"
    if classification in {"neutral_efficacy", "weak_negative_efficacy", "moderate_negative_efficacy", "strong_negative_efficacy"}:
        return "fails"
    return "invalid_input"


def run_alpha_layer_b_regime_conditional_signal_efficacy(*, alpha_layer_a_outputs: Sequence[Mapping[str, Any]], regime_classifications: Mapping[str, str]) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "invariants": {
            "deterministic_output": True,
            "replay_compatible": True,
            "immutable_input_safe": True,
            "no_runtime_mutation": True,
            "no_adaptive_control": True,
            "no_black_box_ml": True,
            "no_trading_execution": True,
        }
    }
    if not isinstance(alpha_layer_a_outputs, Sequence) or not isinstance(regime_classifications, Mapping):
        payload = {**base, "classification": "invalid_input", "regime_results": []}
        payload["replay_metadata"] = {"schema_version": "alpha_layer_b_v1", "fingerprint_sha256": _fingerprint(payload)}
        return payload

    results = []
    for item in sorted(alpha_layer_a_outputs, key=lambda x: (str(x.get("signal_name", "")), str(x.get("window", "")), str(x.get("regime_tag", "")))):
        regime_tag = str(item.get("regime_tag", "all_regimes"))
        regime_label = regime_classifications.get(regime_tag, "unclassified_regime")
        cls = str(item.get("classification", "invalid_input"))
        if cls not in ALPHA_CLASSIFICATIONS:
            cls = "invalid_input"
        metrics = item.get("metrics", {}) if isinstance(item.get("metrics"), Mapping) else {}
        ic = float(metrics.get("information_coefficient", 0.0))
        rank_ic = float(metrics.get("rank_information_coefficient", 0.0))
        decay = float(metrics.get("factor_decay", 0.0))
        outcome = _outcome(cls, decay, ic, rank_ic)
        results.append(
            {
                "signal_name": str(item.get("signal_name", "")),
                "window": str(item.get("window", "")),
                "regime_tag": regime_tag,
                "regime_classification": regime_label,
                "alpha_layer_a_classification": cls,
                "regime_outcome": outcome,
                "explanation": (
                    "Regime efficacy evaluation signal={signal} window={window} regime={regime}({label}) "
                    "base={base} IC={ic:.6f} RankIC={rank_ic:.6f} Decay={decay:.6f} outcome={outcome}."
                ).format(
                    signal=str(item.get("signal_name", "")),
                    window=str(item.get("window", "")),
                    regime=regime_tag,
                    label=regime_label,
                    base=cls,
                    ic=ic,
                    rank_ic=rank_ic,
                    decay=decay,
                    outcome=outcome,
                ),
            }
        )

    payload = {**base, "classification": "valid", "regime_results": results}
    payload["replay_metadata"] = {"schema_version": "alpha_layer_b_v1", "fingerprint_sha256": _fingerprint(payload)}
    return payload
