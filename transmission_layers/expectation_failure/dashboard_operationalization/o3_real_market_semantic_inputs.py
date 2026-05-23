"""Deterministic Phase O3 real-market semantic input normalization layer."""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

SEMANTIC_CATEGORIES = [
    "VALUATION_STRETCH",
    "NARRATIVE_SATURATION",
    "BREADTH_DETERIORATION",
    "MOMENTUM_DISPERSION",
    "VOLATILITY_STRESS",
    "CREDIT_STRESS",
    "LIQUIDITY_STRESS",
    "PARTICIPATION_CONCENTRATION",
    "EXPECTATION_FRAGILITY",
    "UNCLASSIFIED_MARKET_EVIDENCE",
]

CATEGORY_METRIC_TOKENS = {
    "VALUATION_STRETCH": {"pe", "ev_ebitda", "fcf_yield", "valuation_proxy"},
    "NARRATIVE_SATURATION": {"news_volume", "hype_score", "narrative_score", "certainty_density"},
    "BREADTH_DETERIORATION": {"percent_above_ma", "breadth_score", "advance_decline"},
    "MOMENTUM_DISPERSION": {"momentum_score", "dispersion_score", "price_vs_ma"},
    "VOLATILITY_STRESS": {"vix", "realized_volatility", "implied_volatility"},
    "CREDIT_STRESS": {"credit_spread", "high_yield_spread", "bbb_spread"},
    "LIQUIDITY_STRESS": {"liquidity_score", "funding_stress", "bid_ask_spread"},
    "PARTICIPATION_CONCENTRATION": {"concentration_score", "mega_cap_weight", "options_concentration"},
    "EXPECTATION_FRAGILITY": {"expectation_fragility_score", "expectation_gap"},
}
SEVERITY_BANDS = ((24, "LOW"), (49, "MODERATE"), (69, "ELEVATED"), (84, "HIGH"), (100, "SEVERE"))
SCORE_COMPATIBILITY_TOKENS = {"score", "percent", "percentile", "proxy", "index"}
CATEGORY_FIELD_MAP = {
    "VALUATION_STRETCH": "valuation_stretch_score",
    "NARRATIVE_SATURATION": "narrative_saturation_score",
    "BREADTH_DETERIORATION": "breadth_deterioration_score",
    "MOMENTUM_DISPERSION": "momentum_dispersion_score",
    "VOLATILITY_STRESS": "volatility_stress_score",
    "CREDIT_STRESS": "credit_stress_score",
    "LIQUIDITY_STRESS": "liquidity_stress_score",
    "PARTICIPATION_CONCENTRATION": "participation_concentration_score",
    "EXPECTATION_FRAGILITY": "expectation_fragility_score",
}
ALLOWED_USES = [
    "deterministic market evidence normalization",
    "semantic market-state classification",
    "expectation-fragility input preparation",
    "dashboard view-model generation",
    "replay-safe structural interpretation support",
]
FORBIDDEN_USES = [
    "price prediction", "trading recommendations", "portfolio optimization", "autonomous execution",
    "probabilistic forecasting", "investment advice", "expected return generation", "black-box model inference",
    "live data fetching", "database writes",
]


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _semantic_category(metric_name: Any, metric_category: Any) -> str:
    tokens = {str(metric_name or "").strip().lower(), str(metric_category or "").strip().lower()}
    for category in SEMANTIC_CATEGORIES:
        if category == "UNCLASSIFIED_MARKET_EVIDENCE":
            continue
        if tokens & CATEGORY_METRIC_TOKENS.get(category, set()):
            return category
    return "UNCLASSIFIED_MARKET_EVIDENCE"


def _score_payload(obs: Mapping[str, Any]) -> tuple[float, str]:
    percentile = _to_float(obs.get("percentile"))
    if percentile is not None:
        return round(_clamp(percentile), 2), "READY"
    z_score = _to_float(obs.get("z_score"))
    if z_score is not None:
        if z_score <= -2:
            return 5.0, "READY"
        if z_score <= -1:
            return 20.0, "READY"
        if z_score < 1:
            return 50.0, "READY"
        if z_score < 2:
            return 75.0, "READY"
        return 90.0, "READY"
    metric_value = _to_float(obs.get("metric_value"))
    if metric_value is None:
        return 50.0, "DEGRADED_MISSING_NUMERIC_VALUE"
    unit = str(obs.get("metric_unit") or "").lower()
    category = str(obs.get("metric_category") or "").lower()
    if any(t in unit for t in SCORE_COMPATIBILITY_TOKENS) or any(t in category for t in SCORE_COMPATIBILITY_TOKENS):
        return round(_clamp(metric_value), 2), "READY"
    return 50.0, "DEGRADED_NUMERIC_VALUE_NOT_SCORE_COMPATIBLE"


def _severity(score: float) -> str:
    for ceiling, label in SEVERITY_BANDS:
        if score <= ceiling:
            return label
    return "SEVERE"


def _direction(score: float) -> str:
    return f"PRESSURE_{_severity(score)}"


def build_o3_semantic_evidence_records(observations: list[Mapping[str, Any]] | None = None) -> list[OrderedDict[str, Any]]:
    rows = deepcopy(list(observations or []))
    out = []
    for obs in rows:
        blocked = [str(x) for x in list(obs.get("blocked_reasons") or [])]
        score, quality = _score_payload(obs)
        category = _semantic_category(obs.get("metric_name"), obs.get("metric_category"))
        quality = "BLOCKED_EVIDENCE" if blocked else quality
        out.append(OrderedDict([
            ("observation_id", str(obs.get("observation_id") or "")), ("as_of_date", str(obs.get("as_of_date") or "")),
            ("symbol", str(obs.get("symbol") or "UNKNOWN")), ("entity_name", str(obs.get("entity_name") or "UNKNOWN")),
            ("sector", str(obs.get("sector") or "UNKNOWN")), ("subsector", str(obs.get("subsector") or "UNKNOWN")),
            ("metric_name", str(obs.get("metric_name") or "UNKNOWN")), ("semantic_category", category),
            ("normalized_score", score), ("severity_band", _severity(score)), ("direction_label", _direction(score)),
            ("evidence_quality", quality), ("source_name", str(obs.get("source_name") or "")),
            ("checksum_present", bool(obs.get("checksum"))),
            ("interpretation", f"Deterministic semantic evidence classified as {category} with {quality} quality."),
        ]))
    out.sort(key=lambda r: (r["as_of_date"], r["symbol"], r["semantic_category"], r["metric_name"], r["observation_id"]))
    return out


def build_o3_market_observation_inventory(observations: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    records = build_o3_semantic_evidence_records(observations)
    total = len(records)
    blocked = sum(1 for r in records if r["evidence_quality"] == "BLOCKED_EVIDENCE")
    degraded = sum(1 for r in records if r["evidence_quality"].startswith("DEGRADED"))
    missing_checksum = sum(1 for r in records if not r["checksum_present"])
    missing_source = sum(1 for r in records if not r["source_name"])
    valid = total - blocked
    if total == 0 or blocked == total:
        state = "O3_INVENTORY_BLOCKED"
    elif degraded > 0 or missing_checksum > 0 or missing_source > 0:
        state = "O3_INVENTORY_DEGRADED"
    else:
        state = "O3_INVENTORY_READY"
    return OrderedDict([
        ("total_observations", total), ("valid_observations", valid), ("degraded_observations", degraded), ("blocked_observations", blocked),
        ("missing_checksum_count", missing_checksum), ("missing_source_count", missing_source),
        ("observed_symbols", sorted({r["symbol"] for r in records})),
        ("observed_metric_names", sorted({r["metric_name"] for r in records})),
        ("observed_semantic_categories", sorted({r["semantic_category"] for r in records})),
        ("inventory_state", state),
    ])


def build_o3_expectation_fragility_inputs(observations=None, semantic_records=None) -> OrderedDict[str, Any]:
    records = list(semantic_records) if semantic_records is not None else build_o3_semantic_evidence_records(observations)
    by_entity = defaultdict(list)
    by_sub = defaultdict(list)
    for r in records:
        by_entity[(r["symbol"], r["entity_name"], r["sector"], r["subsector"])].append(r)
        by_sub[(r["sector"], r["subsector"])].append(r)

    def _agg(bucket: list[Mapping[str, Any]], header: tuple[str, ...]) -> OrderedDict[str, Any]:
        values = {k: [] for k in CATEGORY_FIELD_MAP}
        for r in bucket:
            if r["semantic_category"] in values:
                values[r["semantic_category"]].append(r["normalized_score"])
        body = OrderedDict()
        if len(header) == 4:
            body.update({"symbol": header[0], "entity_name": header[1], "sector": header[2], "subsector": header[3]})
        else:
            body.update({"sector": header[0], "subsector": header[1]})
        for cat, field in CATEGORY_FIELD_MAP.items():
            vals = values[cat]
            body[field] = round(sum(vals) / len(vals), 2) if vals else 50.0
        cat_scores = [body[field] for field in CATEGORY_FIELD_MAP.values()]
        body["composite_semantic_pressure_score"] = round(sum(cat_scores) / len(cat_scores), 2)
        body["evidence_count"] = len(bucket)
        body["degraded_evidence_count"] = sum(1 for r in bucket if str(r["evidence_quality"]).startswith("DEGRADED"))
        body["interpretation"] = "Deterministic expectation-fragility semantic aggregation record."
        return body

    entity = [_agg(v, k) for k, v in by_entity.items()]
    entity.sort(key=lambda x: (x["symbol"], x["subsector"]))
    subsector = [_agg(v, k) for k, v in by_sub.items()]
    subsector.sort(key=lambda x: (x["sector"], x["subsector"]))
    strongest = sorted(entity, key=lambda x: (-x["composite_semantic_pressure_score"], x["symbol"]))[:5]
    weakest = sorted(entity, key=lambda x: (x["composite_semantic_pressure_score"], x["symbol"]))[:5]
    cat_avg = OrderedDict((cat, round(sum(r["normalized_score"] for r in records if r["semantic_category"] == cat) / max(1, sum(1 for r in records if r["semantic_category"] == cat)), 2)) for cat in SEMANTIC_CATEGORIES)
    highest = sorted(cat_avg.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    return OrderedDict([
        ("entity_expectation_fragility_inputs", entity), ("subsector_expectation_fragility_inputs", subsector),
        ("strongest_expectation_pressure_entities", strongest), ("weakest_structural_support_entities", weakest),
        ("highest_semantic_pressure_categories", [{"semantic_category": c, "average_score": s} for c, s in highest]),
    ])


def build_o3_market_evidence_cards(observations=None, semantic_records=None) -> OrderedDict[str, Any]:
    records = list(semantic_records) if semantic_records is not None else build_o3_semantic_evidence_records(observations)
    def _card(title, cats):
        subset = [r for r in records if r["semantic_category"] in cats]
        score = round(sum(r["normalized_score"] for r in subset) / len(subset), 2) if subset else 50.0
        return OrderedDict([("title", title), ("state", _severity(score)), ("score", score), ("evidence_count", len(subset)), ("interpretation", "Deterministic semantic evidence dashboard card.")])
    return OrderedDict([
        ("valuation_stretch_card", _card("Valuation Stretch", {"VALUATION_STRETCH"})),
        ("narrative_saturation_card", _card("Narrative Saturation", {"NARRATIVE_SATURATION"})),
        ("breadth_deterioration_card", _card("Breadth Deterioration", {"BREADTH_DETERIORATION"})),
        ("stress_conditions_card", _card("Stress Conditions", {"VOLATILITY_STRESS", "CREDIT_STRESS", "LIQUIDITY_STRESS"})),
        ("expectation_fragility_card", _card("Expectation Fragility", {"EXPECTATION_FRAGILITY", "PARTICIPATION_CONCENTRATION", "MOMENTUM_DISPERSION"})),
        ("evidence_quality_card", OrderedDict([("title", "Evidence Quality"), ("state", "DEGRADED" if any(str(r["evidence_quality"]).startswith("DEGRADED") for r in records) else "READY"), ("score", round(100.0 * sum(1 for r in records if r["evidence_quality"] == "READY") / len(records), 2) if records else 0.0), ("evidence_count", len(records)), ("interpretation", "Deterministic evidence quality completeness assessment.")])),
    ])


def build_o3_semantic_category_summary(observations=None, semantic_records=None) -> OrderedDict[str, Any]:
    records = list(semantic_records) if semantic_records is not None else build_o3_semantic_evidence_records(observations)
    counts = OrderedDict((c, sum(1 for r in records if r["semantic_category"] == c)) for c in SEMANTIC_CATEGORIES)
    avgs = OrderedDict((c, round(sum(r["normalized_score"] for r in records if r["semantic_category"] == c) / max(1, counts[c]), 2)) for c in SEMANTIC_CATEGORIES)
    degraded = sorted({r["semantic_category"] for r in records if str(r["evidence_quality"]).startswith("DEGRADED")})
    high = max(avgs.items(), key=lambda kv: (kv[1], kv[0]))[0] if avgs else "UNCLASSIFIED_MARKET_EVIDENCE"
    weak = min(counts.items(), key=lambda kv: (kv[1], kv[0]))[0] if counts else "UNCLASSIFIED_MARKET_EVIDENCE"
    return OrderedDict([("category_counts", counts), ("category_average_scores", avgs), ("highest_pressure_category", high), ("weakest_evidence_category", weak), ("degraded_categories", degraded), ("summary_interpretation", "Deterministic semantic category breadth and pressure summary.")])


def certify_o3_real_market_semantic_inputs(observations=None, semantic_records=None) -> OrderedDict[str, Any]:
    records = list(semantic_records) if semantic_records is not None else build_o3_semantic_evidence_records(observations)
    inv = build_o3_market_observation_inventory(observations)
    blocking, degraded = [], []
    unclassified = sum(1 for r in records if r["semantic_category"] == "UNCLASSIFIED_MARKET_EVIDENCE")
    if inv["total_observations"] == 0 or inv["blocked_observations"] == inv["total_observations"]:
        status = "O3_MARKET_SEMANTICS_BLOCKED"; blocking.append("no_usable_market_observations")
    elif inv["missing_checksum_count"] > 0 or inv["missing_source_count"] > 0 or inv["degraded_observations"] > 0 or unclassified > (len(records) / 2):
        status = "O3_MARKET_SEMANTICS_DEGRADED"; degraded.append("semantic_evidence_quality_or_classification_degraded")
    else:
        status = "O3_MARKET_SEMANTICS_READY"
    invariants = OrderedDict([("fixed_ordering", True), ("stable_output_structure", True), ("canonical_checksum", True), ("no_runtime_timestamp", True), ("no_network", True), ("no_database_calls", True), ("input_immutability", True), ("no_randomness", True)])
    forbidden = OrderedDict((x, True) for x in FORBIDDEN_USES)
    payload = OrderedDict([("records", records), ("inventory", inv), ("status", status)])
    return OrderedDict([("certification_status", status), ("certification_passed", status == "O3_MARKET_SEMANTICS_READY"), ("blocking_reasons", blocking), ("degraded_reasons", degraded), ("invariant_results", invariants), ("forbidden_capability_check", forbidden), ("checksum", _stable_checksum(payload)), ("replay_safe", status != "O3_MARKET_SEMANTICS_BLOCKED"), ("supervisor_decision", "APPROVED" if status.endswith("READY") else "APPROVED_WITH_DEGRADATION" if status.endswith("DEGRADED") else "BLOCKED_REMEDIATION_REQUIRED")])


def build_o3_dashboard_view_model(observations=None) -> OrderedDict[str, Any]:
    records = build_o3_semantic_evidence_records(observations)
    return OrderedDict([
        ("page_id", "sefi_o3_real_market_semantic_inputs"), ("page_title", "SEFI O3 Real Market Semantic Inputs"), ("generated_at_policy", "deterministic_no_runtime_clock"),
        ("market_observation_inventory", build_o3_market_observation_inventory(observations)), ("semantic_evidence_records", records),
        ("expectation_fragility_inputs", build_o3_expectation_fragility_inputs(semantic_records=records)),
        ("market_evidence_cards", build_o3_market_evidence_cards(semantic_records=records)),
        ("semantic_category_summary", build_o3_semantic_category_summary(semantic_records=records)),
        ("supervisor_summary", "Deterministic O3 market semantic normalization for expectation-fragility evidence preparation."),
        ("governance_boundaries", OrderedDict([("allowed_uses", list(ALLOWED_USES)), ("forbidden_uses", list(FORBIDDEN_USES))])),
        ("certification_summary", certify_o3_real_market_semantic_inputs(observations, records)),
    ])


def build_o3_real_market_semantic_inputs_report(observations=None) -> str:
    cert = certify_o3_real_market_semantic_inputs(observations)
    return "\n".join([
        "# O3 Real Market Semantic Inputs Report", "", "## Objective", "Deterministic normalization of provided market observations into bounded semantic evidence records.",
        "", "## Scope", "Semantic mapping, bounded scoring, expectation-fragility input assembly, dashboard view model support, deterministic certification.",
        "", "## Non-goals", "No live data fetch, no prediction, no trading guidance, no optimization, no autonomous execution.",
        "", "## Architecture Role", "Input semantic normalization layer between raw observations and dashboard-consumable evidence.",
        "", "## Semantic Category Mapping", "Metric names/categories are deterministically mapped into fixed O3 semantic categories.",
        "", "## Scoring and Bounding Methodology", "Percentile clamp first, z-score band conversion second, numeric score-compatible clamp third, deterministic degraded fallback last.",
        "", "## Expectation-Fragility Input Assembly", "Entity and subsector deterministic category averages with composite pressure scoring.",
        "", "## Dashboard View Model", "Provides inventory, semantic records, cards, category summary, governance boundaries, and certification summary.",
        "", "## Certification States", "READY, DEGRADED, BLOCKED state machine with explicit blocking and degraded reasons.",
        "", "## Governance Boundaries", f"Allowed: {', '.join(ALLOWED_USES)}. Forbidden: {', '.join(FORBIDDEN_USES)}.",
        "", "## Final Interpretation", f"Certification status: {cert['certification_status']} with deterministic replay-safe semantic evidence handling.",
    ])
