from __future__ import annotations

from copy import deepcopy
from typing import Any

from .federation_common import clamp_score
from .federation_determinism import stable_checksum


SCORE_SUFFIX = "_score"


def validate_score_contracts(payload: dict[str, Any]) -> dict[str, Any]:
    frozen = deepcopy(payload)
    score_keys = sorted(k for k, v in frozen.items() if k.endswith(SCORE_SUFFIX) and isinstance(v, (int, float)))
    bounded = [k for k in score_keys if 0.0 <= float(frozen[k]) <= 1.0]
    score_contract_score = clamp_score(len(bounded) / len(score_keys)) if score_keys else 1.0
    return {
        "score_keys": score_keys,
        "bounded_score_keys": bounded,
        "federation_score_contract_score": score_contract_score,
        "federation_checksum_contract_score": 1.0 if any("checksum" in k for k in frozen) else 0.0,
        "federation_score_contracts_checksum": stable_checksum({"score_keys": score_keys, "bounded": bounded, "score": score_contract_score}, prefix="tier5h_score_contracts"),
    }
