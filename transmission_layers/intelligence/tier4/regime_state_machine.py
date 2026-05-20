from __future__ import annotations

from collections import deque
from typing import Dict, List

_ALLOWED = {
    "stable": ["stressed", "transitional"],
    "stressed": ["stable", "fragmented", "overloaded", "suppressed"],
    "fragmented": ["stressed", "overloaded", "recovering"],
    "overloaded": ["stressed", "cascading_failure", "recovering"],
    "cascading_failure": ["recovering"],
    "suppressed": ["stressed", "recovering"],
    "recovering": ["stable", "transitional"],
    "transitional": ["stable", "stressed", "fragmented"],
}

def enumerate_allowed_transitions() -> Dict[str, List[str]]:
    return {k: list(v) for k, v in sorted(_ALLOWED.items())}

def validate_regime_transition(previous_regime: str, current_regime: str) -> Dict[str, object]:
    allowed = current_regime in _ALLOWED.get(previous_regime, [])
    return {"valid": allowed, "previous_regime": previous_regime, "current_regime": current_regime, "diagnostic": "valid_transition" if allowed else "invalid_direct_transition"}

def compute_transition_path(start_regime: str, end_regime: str, max_depth: int = 6) -> Dict[str, object]:
    if start_regime == end_regime: return {"path_found": True, "path": [start_regime]}
    q = deque([(start_regime, [start_regime])])
    while q:
        node, path = q.popleft()
        if len(path) > max_depth: continue
        for nxt in _ALLOWED.get(node, []):
            if nxt in path: continue
            p2 = path + [nxt]
            if nxt == end_regime: return {"path_found": True, "path": p2}
            q.append((nxt, p2))
    return {"path_found": False, "path": [], "diagnostic": "no_bounded_path"}
