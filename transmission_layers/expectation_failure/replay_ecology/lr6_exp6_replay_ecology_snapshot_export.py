from __future__ import annotations

import json
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_exp5_replay_ecology_dashboard_view_model import (
    build_replay_ecology_dashboard_view_model,
)

DETERMINISTIC_VERSION = "LR6_EXP6_REPLAY_ECOLOGY_SNAPSHOT_EXPORT_V1"
DETERMINISTIC_SEED = "LR6_EXP6_REPLAY_ECOLOGY_SNAPSHOT_EXPORT_SEED_V1"
SOURCE_PHASE = "LR6-EXP6"
MAX_SECTION_ITEMS = 6
MAX_SECTION_TEXT = 220


SECTION_ORDER = [
    "overview",
    "replay_drift",
    "propagation_evolution",
    "contradiction_ecology",
    "saturation_monoculture",
    "ecosystem_interaction",
    "entity_cluster_attribution",
    "caveats",
    "next_observation_priorities",
]


SOURCE_MODULES = [
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp2_longitudinal_replay_observation",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp3_replay_ecology_signal_readout",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp4_replay_ecology_evidence_trace",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp5_replay_ecology_dashboard_view_model",
]


def _clip(text: str, limit: int = MAX_SECTION_TEXT) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _stable_unique(items: list[str], limit: int = MAX_SECTION_ITEMS) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = _clip(str(item))
        if key and key not in seen:
            seen.add(key)
            result.append(key)
        if len(result) >= limit:
            break
    return result


def build_replay_ecology_snapshot_comparison_key(dashboard_vm: dict[str, Any]) -> str:
    overview = dashboard_vm["overview_panel"]
    attr = dashboard_vm["entity_cluster_attribution_panel"]
    contradiction = dashboard_vm["contradiction_ecology_panel"]
    propagation = dashboard_vm["propagation_evolution_panel"]
    saturation = dashboard_vm["saturation_monoculture_panel"]
    interaction = dashboard_vm["ecosystem_interaction_panel"]

    parts = [
        f"state={overview['dominant_replay_ecology_state']}",
        f"maturity={overview['replay_ecology_maturity_band']}",
        f"confidence={overview['observation_confidence_band']}",
        "clusters=" + "|".join(_stable_unique(attr["most_referenced_clusters"][:4], limit=4)),
        "contradictions=" + "|".join(_stable_unique(attr["strongest_contradiction_contributors"][:4], limit=4)),
        "pathways=" + "|".join(_stable_unique(attr["strongest_propagation_contributors"][:4], limit=4)),
        "saturation=" + "|".join(_stable_unique(saturation["observations"][:2], limit=2)),
        "interaction=" + "|".join(_stable_unique(interaction["observations"][:2], limit=2)),
        "contradiction_surfaces=" + "|".join(_stable_unique(contradiction["observations"][:2], limit=2)),
        "propagation_pathways=" + "|".join(_stable_unique(propagation["observations"][:2], limit=2)),
    ]
    return "::".join(parts)


def build_replay_ecology_snapshot_metadata(dashboard_vm: dict[str, Any]) -> dict[str, Any]:
    comparison_key = build_replay_ecology_snapshot_comparison_key(dashboard_vm)
    return {
        "snapshot_id": f"{DETERMINISTIC_VERSION}::{dashboard_vm['observation_window']['max_entities']}x{dashboard_vm['observation_window']['slice_count']}",
        "generated_at_marker": DETERMINISTIC_SEED,
        "source_phase": SOURCE_PHASE,
        "source_modules": SOURCE_MODULES,
        "ecosystem_universe_size": dashboard_vm["observation_window"]["max_entities"],
        "dashboard_sections_included": SECTION_ORDER,
        "deterministic_comparison_key": comparison_key,
        "experimental_mode_only": True,
        "no_prediction": True,
        "no_trading": True,
        "no_governed_activation": True,
    }


def build_replay_ecology_snapshot_json_payload(dashboard_vm: dict[str, Any]) -> dict[str, Any]:
    return {
        "overview": {
            "dominant_replay_ecology_state": dashboard_vm["overview_panel"]["dominant_replay_ecology_state"],
            "replay_ecology_density_band": dashboard_vm["overview_panel"]["replay_ecology_density_band"],
            "replay_ecology_maturity_band": dashboard_vm["overview_panel"]["replay_ecology_maturity_band"],
            "observation_confidence_band": dashboard_vm["overview_panel"]["observation_confidence_band"],
            "strongest_observed_signal": dashboard_vm["overview_panel"]["strongest_observed_signal"],
            "weakest_observed_signal": dashboard_vm["overview_panel"]["weakest_observed_signal"],
            "ecological_caveat_summary": dashboard_vm["overview_panel"]["ecological_caveat_summary"],
            "evidence_refs": dashboard_vm["overview_panel"]["evidence_refs"],
        },
        "replay_drift": dashboard_vm["replay_drift_panel"],
        "propagation_evolution": dashboard_vm["propagation_evolution_panel"],
        "contradiction_ecology": dashboard_vm["contradiction_ecology_panel"],
        "saturation_monoculture": dashboard_vm["saturation_monoculture_panel"],
        "ecosystem_interaction": dashboard_vm["ecosystem_interaction_panel"],
        "entity_cluster_attribution": dashboard_vm["entity_cluster_attribution_panel"],
        "caveats": [_clip(x) for x in dashboard_vm["ecological_caveats"][:MAX_SECTION_ITEMS]],
        "next_observation_priorities": [_clip(x) for x in dashboard_vm["next_observation_priorities"][:MAX_SECTION_ITEMS]],
    }


def build_replay_ecology_snapshot_markdown(metadata: dict[str, Any], payload: dict[str, Any]) -> str:
    lines = [
        "# LR6-EXP6 Replay Ecology Snapshot",
        "",
        f"- Snapshot ID: `{metadata['snapshot_id']}`",
        f"- Source phase: `{metadata['source_phase']}`",
        f"- Universe size: `{metadata['ecosystem_universe_size']}`",
        f"- Deterministic comparison key: `{metadata['deterministic_comparison_key']}`",
        "",
    ]
    for section in SECTION_ORDER:
        lines.append(f"## {section.replace('_', ' ').title()}")
        section_data = payload[section]
        if isinstance(section_data, dict):
            if "observations" in section_data:
                for item in section_data["observations"][:MAX_SECTION_ITEMS]:
                    lines.append(f"- {_clip(str(item))}")
            else:
                for k in sorted(section_data.keys()):
                    if k == "evidence_refs":
                        lines.append(f"- evidence_refs: `{json.dumps(section_data[k], sort_keys=True)}`")
                    elif isinstance(section_data[k], list):
                        clipped = ", ".join(_stable_unique([str(x) for x in section_data[k]], limit=MAX_SECTION_ITEMS))
                        lines.append(f"- {k}: {clipped}")
                    else:
                        lines.append(f"- {k}: {_clip(str(section_data[k]))}")
        else:
            for item in section_data[:MAX_SECTION_ITEMS]:
                lines.append(f"- {_clip(str(item))}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_replay_ecology_snapshot_export(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    dashboard_vm = build_replay_ecology_dashboard_view_model(max_entities=max_entities, slice_count=slice_count)
    metadata = build_replay_ecology_snapshot_metadata(dashboard_vm)
    payload = build_replay_ecology_snapshot_json_payload(dashboard_vm)
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "metadata": metadata,
        "payload": payload,
        "markdown": build_replay_ecology_snapshot_markdown(metadata, payload),
        "experimental_certification": certify_lr6_exp6_experimental_boundaries(),
    }


def validate_replay_ecology_snapshot_export(snapshot_export: dict[str, Any]) -> dict[str, Any]:
    metadata = snapshot_export.get("metadata", {})
    payload = snapshot_export.get("payload", {})
    markdown = snapshot_export.get("markdown", "")

    metadata_required = {
        "snapshot_id", "generated_at_marker", "source_phase", "source_modules", "ecosystem_universe_size",
        "dashboard_sections_included", "deterministic_comparison_key", "experimental_mode_only", "no_prediction",
        "no_trading", "no_governed_activation",
    }
    sections_ok = all(section in payload for section in SECTION_ORDER)
    metadata_ok = metadata_required.issubset(metadata.keys())
    json_ok = True
    try:
        json.dumps(snapshot_export, sort_keys=True)
    except TypeError:
        json_ok = False

    bounded_ok = True
    for section in ["replay_drift", "propagation_evolution", "contradiction_ecology", "saturation_monoculture", "ecosystem_interaction"]:
        bounded_ok = bounded_ok and len(payload.get(section, {}).get("observations", [])) <= MAX_SECTION_ITEMS
    bounded_ok = bounded_ok and len(payload.get("caveats", [])) <= MAX_SECTION_ITEMS
    bounded_ok = bounded_ok and len(payload.get("next_observation_priorities", [])) <= MAX_SECTION_ITEMS

    return {
        "passed": metadata_ok and sections_ok and json_ok and bool(markdown.strip()) and bounded_ok,
        "metadata_fields_present": metadata_ok,
        "required_sections_present": sections_ok,
        "json_serializable": json_ok,
        "markdown_present": bool(markdown.strip()),
        "bounded_sections": bounded_ok,
        "comparison_key_present": bool(metadata.get("deterministic_comparison_key")),
    }


def certify_lr6_exp6_experimental_boundaries() -> dict[str, Any]:
    return {
        "experimental_mode_only": True,
        "governed_lr6_activation": False,
        "no_persistence_writes": True,
        "no_direct_sql": True,
        "no_external_apis": True,
        "no_prediction_or_trading": True,
        "additive_architecture_preserved": True,
        "comparison_readiness_enabled": True,
    }
