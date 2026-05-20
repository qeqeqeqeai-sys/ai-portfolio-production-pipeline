from __future__ import annotations
from typing import Any

def explain_cascade(summary: dict[str, Any]) -> str:
    return (
        "cascade status template: "
        f"cascade_id={summary.get('cascade_id', 'tier4m_cascade')}; "
        f"structural_criticality_score={round(float(summary.get('structural_criticality_score', 0.0)), 6)}; "
        f"systemic_cascade_score={round(float(summary.get('systemic_cascade_score', 0.0)), 6)}; "
        f"cascade_escalation_score={round(float(summary.get('cascade_escalation_score', 0.0)), 6)}; "
        f"dominant_cascade_factor={summary.get('dominant_cascade_factor', 'structural_criticality')}; "
        f"cascade_classification={summary.get('cascade_classification', 'contained')}; "
        f"cascade_checksum={summary.get('cascade_checksum', '')}."
    )
