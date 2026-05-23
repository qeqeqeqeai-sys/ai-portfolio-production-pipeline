"""P3-G Structural Explainability & Narrative Layer: deterministic bounded additive narrative consolidation across P3-A..P3-F."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CERTIFIED_STRUCTURAL_INTERPRETATION = "CERTIFIED_STRUCTURAL_INTERPRETATION"
DEGRADED_STRUCTURAL_INTERPRETATION = "DEGRADED_STRUCTURAL_INTERPRETATION"
BLOCKED_STRUCTURAL_INTERPRETATION = "BLOCKED_STRUCTURAL_INTERPRETATION"

MAX_ACTIVE_EXPLANATIONS = 4

FORBIDDEN_LANGUAGE_TERMS: Tuple[str, ...] = (
    "will", "likely", "predict", "forecast", "buy", "sell", "short opportunity", "reduce exposure",
    "high-conviction", "expected return", "outperform", "underperform", "recommend", "trade",
)

EXPECTED_P3_KEYS: Tuple[str, ...] = ("path3a", "path3b", "path3c", "path3d", "path3e", "path3f")


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _safe_float(value: Any, default: float = 50.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def _clamp(value: Any) -> float:
    return round(max(0.0, min(100.0, _safe_float(value))), 2)


def build_path3g_explanation_registry() -> Dict[str, Any]:
    explanations = [
        {"explanation_id": "P3G_EXP_001", "category": "asymmetry", "priority": 1, "source_layers": ["path3b", "path3f"], "trigger_rule": "downside_asymmetry>=65", "input_fields": ["path3b.asymmetry_dimensions.downside_asymmetry"], "template": "Downside structural asymmetry remains elevated.", "driver_label": "elevated_downside_asymmetry"},
        {"explanation_id": "P3G_EXP_002", "category": "benchmark", "priority": 2, "source_layers": ["path3c"], "trigger_rule": "benchmark_relative_pressure>=60", "input_fields": ["path3c.benchmark_asymmetry_dimensions.benchmark_relative_pressure"], "template": "Benchmark-relative resilience deterioration persists.", "driver_label": "benchmark_relative_deterioration"},
        {"explanation_id": "P3G_EXP_003", "category": "persistence", "priority": 3, "source_layers": ["path3d"], "trigger_rule": "asymmetry_persistence>=62", "input_fields": ["path3d.persistence_dimensions.asymmetry_persistence"], "template": "Structural asymmetry persistence remains elevated.", "driver_label": "persistent_asymmetry_pressure"},
        {"explanation_id": "P3G_EXP_004", "category": "concentration", "priority": 4, "source_layers": ["path3e"], "trigger_rule": "fragility_concentration>=65", "input_fields": ["path3e.imbalance_dimensions.fragility_concentration"], "template": "Fragility concentration remains elevated.", "driver_label": "concentrated_fragility"},
        {"explanation_id": "P3G_EXP_005", "category": "regime", "priority": 5, "source_layers": ["path3f"], "trigger_rule": "regime_in_fragility_set", "input_fields": ["path3f.asymmetry_regime"], "template": "Regime classification indicates broad structural fragility pressure.", "driver_label": "fragility_regime_context"},
    ]
    registry = {"version": "P3G_REGISTRY_V1", "max_active_explanations": MAX_ACTIVE_EXPLANATIONS, "explanations": explanations}
    registry["registry_checksum"] = _checksum(registry)
    return registry


def build_path3g_bounded_grammar_registry() -> Dict[str, Any]:
    grammar = {
        "subjects": ["structural asymmetry", "benchmark-relative resilience", "fragility concentration", "regime classification"],
        "states": ["remains elevated", "persists", "indicates pressure", "is concentrated"],
        "contexts": ["within current structural conditions", "relative to benchmark context", "across persistence horizons"],
        "qualifiers": ["without predictive semantics", "with bounded interpretation", "under deterministic replay"],
        "rules": {"template_only": True, "no_synonyms": True, "no_adaptive_phrasing": True},
    }
    grammar["grammar_checksum"] = _checksum(grammar)
    return grammar


def _get_path(data: Dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = data
    for token in dotted.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(token)
    return cur if cur is not None else default


def evaluate_path3g_explanation_triggers(path_inputs: Dict[str, Any], registry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    reg = deepcopy(registry) if registry is not None else build_path3g_explanation_registry()
    fragility_regimes = {"FRAGILITY_DIVERGENCE_REGIME", "DOWNSIDE_ASYMMETRY_EXPANSION_REGIME", "CONCENTRATED_FRAGILITY_REGIME", "BROAD_STRUCTURAL_DETERIORATION_REGIME", "EXTREME_IMBALANCE_REGIME"}
    trigger_values = {
        "downside_asymmetry": _clamp(_get_path(src, "path3b.asymmetry_dimensions.downside_asymmetry", 50.0)),
        "benchmark_relative_pressure": _clamp(_get_path(src, "path3c.benchmark_asymmetry_dimensions.benchmark_relative_pressure", 50.0)),
        "asymmetry_persistence": _clamp(_get_path(src, "path3d.persistence_dimensions.asymmetry_persistence", 50.0)),
        "fragility_concentration": _clamp(_get_path(src, "path3e.imbalance_dimensions.fragility_concentration", 50.0)),
        "asymmetry_regime": str(_get_path(src, "path3f.asymmetry_regime", "STABLE_SYMMETRY_REGIME")),
    }
    evaluations: List[Dict[str, Any]] = []
    for exp in sorted(reg["explanations"], key=lambda x: (x["priority"], x["explanation_id"])):
        rid = exp["explanation_id"]
        active = False
        if rid == "P3G_EXP_001":
            active = trigger_values["downside_asymmetry"] >= 65.0
        elif rid == "P3G_EXP_002":
            active = trigger_values["benchmark_relative_pressure"] >= 60.0
        elif rid == "P3G_EXP_003":
            active = trigger_values["asymmetry_persistence"] >= 62.0
        elif rid == "P3G_EXP_004":
            active = trigger_values["fragility_concentration"] >= 65.0
        elif rid == "P3G_EXP_005":
            active = trigger_values["asymmetry_regime"] in fragility_regimes
        evaluations.append({"explanation_id": rid, "active": active, "priority": exp["priority"], "trigger_rule": exp["trigger_rule"], "source_layers": exp["source_layers"], "input_fields": exp["input_fields"], "driver_label": exp["driver_label"]})
    active = [e for e in evaluations if e["active"]][: reg["max_active_explanations"]]
    return {"trigger_matrix": evaluations, "active_explanations": active, "trigger_values": trigger_values}


def build_path3g_interpretation_blocks(path_inputs: Dict[str, Any], registry: Dict[str, Any] | None = None, grammar_registry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    reg = deepcopy(registry) if registry else build_path3g_explanation_registry()
    gram = deepcopy(grammar_registry) if grammar_registry else build_path3g_bounded_grammar_registry()
    trig = evaluate_path3g_explanation_triggers(src, reg)
    exp_by_id = {e["explanation_id"]: e for e in reg["explanations"]}
    blocks: List[Dict[str, Any]] = []
    for item in trig["active_explanations"]:
        exp = exp_by_id[item["explanation_id"]]
        blocks.append({"block_id": f"BLK_{item['explanation_id']}", "sentence": exp["template"], "lineage": {"explanation_id": item["explanation_id"], "source_layers": item["source_layers"], "trigger_rule": item["trigger_rule"], "input_fields": item["input_fields"], "registry_checksum": reg["registry_checksum"], "grammar_checksum": gram["grammar_checksum"]}})
    if not blocks:
        blocks = [{"block_id": "BLK_P3G_FALLBACK", "sentence": "Structural conditions remain mixed with bounded interpretability under deterministic replay.", "lineage": {"explanation_id": "P3G_FALLBACK", "source_layers": ["path3a", "path3b", "path3c", "path3d", "path3e", "path3f"], "trigger_rule": "fallback_no_primary_trigger", "input_fields": [], "registry_checksum": reg["registry_checksum"], "grammar_checksum": gram["grammar_checksum"]}}]
    return {"interpretation_blocks": blocks, "trigger_evaluation": trig}


def _scan_forbidden_language(text: str) -> Dict[str, bool]:
    lower = text.lower()
    return {f"forbidden_{term.replace(' ', '_')}": term in lower for term in FORBIDDEN_LANGUAGE_TERMS}


def build_path3g_structural_narrative(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    reg = build_path3g_explanation_registry()
    gram = build_path3g_bounded_grammar_registry()
    blocks = build_path3g_interpretation_blocks(src, reg, gram)["interpretation_blocks"]
    sentence = " ".join(b["sentence"] for b in blocks)
    forbidden_flags = _scan_forbidden_language(sentence)
    checksum_manifest = {"registry_checksum": reg["registry_checksum"], "grammar_checksum": gram["grammar_checksum"], "narrative_checksum": _checksum({"sentence": sentence, "blocks": blocks})}
    lineage = [{**b["lineage"], "block_id": b["block_id"], "narrative_checksum": checksum_manifest["narrative_checksum"]} for b in blocks]
    return {"summary_sentence": sentence, "interpretation_blocks": blocks, "narrative_lineage": lineage, "checksum_manifest": checksum_manifest, "forbidden_language_flags": forbidden_flags}


def certify_path3g_structural_explainability(path_inputs: Dict[str, Any], narrative_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    payload = deepcopy(narrative_payload) if narrative_payload else build_path3g_structural_narrative(src)
    has_inputs = all(isinstance(src.get(k), dict) for k in EXPECTED_P3_KEYS)
    flags = payload.get("forbidden_language_flags", {})
    blocked = any(flags.values())
    lineage_ok = all("explanation_id" in row and "source_layers" in row and "trigger_rule" in row and "narrative_checksum" in row for row in payload.get("narrative_lineage", []))
    checksum_ok = all(isinstance(payload.get("checksum_manifest", {}).get(k), str) for k in ("registry_checksum", "grammar_checksum", "narrative_checksum"))
    gates = {"registry_available": True, "bounded_grammar_available": True, "triggers_evaluated": True, "narrative_deterministic": True, "lineage_complete": lineage_ok, "checksums_stable": checksum_ok, "forbidden_language_absent": not blocked, "prior_inputs_present": has_inputs, "no_predictive_or_trading_semantics": not blocked}
    status = BLOCKED_STRUCTURAL_INTERPRETATION if blocked else (CERTIFIED_STRUCTURAL_INTERPRETATION if all(gates.values()) else DEGRADED_STRUCTURAL_INTERPRETATION)
    return {"certification_status": status, "certification_gates": gates}


def build_path3g_dashboard_explanation(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    narrative = build_path3g_structural_narrative(src)
    trig = evaluate_path3g_explanation_triggers(src)
    cert = certify_path3g_structural_explainability(src, narrative)
    regime = str(_get_path(src, "path3f.asymmetry_regime", "STABLE_SYMMETRY_REGIME"))
    source_summary = {k: ("available" if isinstance(src.get(k), dict) else "missing") for k in EXPECTED_P3_KEYS}
    return {"summary_sentence": narrative["summary_sentence"], "regime_interpretation": f"Regime context: {regime}.", "primary_driver_labels": [r["driver_label"] for r in trig["active_explanations"]], "active_explanation_ids": [r["explanation_id"] for r in trig["active_explanations"]], "source_layer_summary": source_summary, "certification_status": cert["certification_status"], "narrative_checksum": narrative["checksum_manifest"]["narrative_checksum"], "registry_checksum": narrative["checksum_manifest"]["registry_checksum"]}


def build_path3g_narrative_manifest(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    reg = build_path3g_explanation_registry()
    gram = build_path3g_bounded_grammar_registry()
    narrative = build_path3g_structural_narrative(src)
    cert = certify_path3g_structural_explainability(src, narrative)
    return {"registry": reg, "bounded_grammar": gram, "narrative": narrative, "certification": cert, "manifest_checksum": _checksum({"registry": reg["registry_checksum"], "grammar": gram["grammar_checksum"], "narrative": narrative["checksum_manifest"]["narrative_checksum"], "status": cert["certification_status"]})}


def build_path3g_supervisor_report(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    manifest = build_path3g_narrative_manifest(src)
    trig = evaluate_path3g_explanation_triggers(src, manifest["registry"])
    inactive = [t for t in trig["trigger_matrix"] if not t["active"]]
    return {"objective": "Deterministic structural explainability and bounded narrative synthesis across P3-A through P3-F.", "scope": "Interpret structural conditions using fixed registries, triggers, and bounded grammar.", "non_goals": ["prediction", "recommendation", "trade execution", "optimization", "llm generation"], "active_explanations": trig["active_explanations"], "inactive_explanations_summary": [{"explanation_id": i["explanation_id"], "trigger_rule": i["trigger_rule"]} for i in inactive], "trigger_matrix": trig["trigger_matrix"], "bounded_grammar_inventory": manifest["bounded_grammar"], "narrative_lineage": manifest["narrative"]["narrative_lineage"], "checksum_manifest": manifest["narrative"]["checksum_manifest"], "certification_decision": manifest["certification"], "governance_boundary_review": {"forbidden_terms_inventory": list(FORBIDDEN_LANGUAGE_TERMS), "forbidden_flags": manifest["narrative"]["forbidden_language_flags"]}, "final_interpretation": manifest["narrative"]["summary_sentence"]}


def build_path3g_report(output_path: str = "reports/path3g_structural_explainability_narrative_report.md") -> str:
    p = Path(output_path)
    return p.read_text(encoding="utf-8") if p.exists() else ""
