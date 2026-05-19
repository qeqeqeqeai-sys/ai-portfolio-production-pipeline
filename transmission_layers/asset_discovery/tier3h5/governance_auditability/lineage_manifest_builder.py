from __future__ import annotations

from typing import Any


def _keys_for(context: dict[str, Any], prefix: str) -> list[str]:
    return sorted([k for k in context["inputs"] if prefix in k])


def build_lineage_manifest(context: dict[str, Any]) -> dict[str, Any]:
    categories = {
        "orchestration": _keys_for(context, "orchestration"),
        "monitoring": _keys_for(context, "monitoring"),
        "drift": _keys_for(context, "drift"),
        "trend_analytics": _keys_for(context, "trend") + _keys_for(context, "history"),
        "reporting": _keys_for(context, "report"),
        "release_auditability": _keys_for(context, "release") + _keys_for(context, "readiness"),
    }
    lineage_categories = {
        key: {
            "artifact_count": len(paths),
            "artifacts": paths,
        }
        for key, paths in sorted(categories.items())
    }
    total = sum(v["artifact_count"] for v in lineage_categories.values())
    return {
        "lineage_manifest_status": "generated",
        "lineage_records_generated": total,
        "lineage_categories": lineage_categories,
    }
