from __future__ import annotations

def build_executive_summary(health: dict, release: dict) -> dict:
    return {
        "operational_health_status": health["operational_classification"],
        "executive_readiness_status": release["release_readiness_classification"],
        "release_readiness_status": release["release_readiness_classification"],
    }
