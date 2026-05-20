from __future__ import annotations

from typing import Any


def explain_resistance_diagnostics(summary: dict[str, Any]) -> str:
    return (
        "resistance diagnostics template: "
        f"capacity_id={str(summary.get('capacity_id', 'tier4_stabilization_capacity'))}; "
        f"stabilization_capacity_score={round(float(summary.get('stabilization_capacity_score', 0.0)), 6)}; "
        f"pressure_resistance_score={round(float(summary.get('pressure_resistance_score', 0.0)), 6)}; "
        f"absorption_margin={round(float(summary.get('absorption_margin', 0.0)), 6)}; "
        f"exhaustion_detected={bool(summary.get('exhaustion_detected', False))}; "
        f"saturation_detected={bool(summary.get('saturation_detected', False))}; "
        f"recovery_fatigue_detected={bool(summary.get('recovery_fatigue_detected', False))}; "
        f"dominant_capacity_factor={str(summary.get('dominant_capacity_factor', 'none'))}; "
        f"capacity_consistency_valid={bool(summary.get('capacity_consistency_valid', True))}; "
        f"resistance_replay_window_size={int(summary.get('resistance_replay_window_size', 0))}; "
        f"resistance_checksum={str(summary.get('resistance_checksum', ''))}."
    )
