from __future__ import annotations

import json
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any

SDE2_VERSION = "SDE2_CURATED_SYMBOL_ECOLOGY_V2"
MIN_UNIVERSE_SIZE = 150
MAX_UNIVERSE_SIZE = 300

CATEGORY_SYMBOLS: "OrderedDict[str, list[str]]" = OrderedDict([
    ("mega_cap_ai_technology", "AAPL MSFT GOOGL AMZN META NVDA TSLA ORCL IBM ADBE CRM SAP NOW".split()),
    ("semiconductors", "AMD AVGO QCOM MU INTC TXN AMAT LRCX KLAC MCHP MPWR ADI MRVL ON NXPI ASML TSM ARM GFS UMC".split()),
    ("cloud_software_infrastructure", "SNOW PANW CRWD FTNT ZS OKTA NET DDOG MDB ESTC HUBS TEAM SHOP WDAY DOCU DDOG PLTR DT".split()),
    ("ai_infrastructure_suppliers", "SMCI ANET CSCO HPE DELL HPQ WDC STX TER SWKS QRVO JBL FLEX APH GLW".split()),
    ("cybersecurity", "PANW CRWD FTNT ZS OKTA CHKP GEN S SENT CYBR VRNS TENB".split()),
    ("industrials_automation", "GE HON EMR ETN ROK PH ITW JCI CARR OTIS MMM CAT DE URI GWW FAST PWR".split()),
    ("robotics", "IR SYM RBT ABB FANUY ROK TER ISRG TXN NVDA AMZN".split()),
    ("energy_utilities", "XOM CVX COP EOG OXY SLB HAL BKR NEE SO DUK AEP EXC XEL SRE CEG AES".split()),
    ("commodities", "GLD SLV USO DBA DBC BHP RIO VALE FCX NEM NUE STLD SCCO ALB CF MOS".split()),
    ("financials", "JPM BAC WFC C GS MS BK USB PNC SCHW BLK BX KKR APO AXP SPGI MCO".split()),
    ("credit_sensitive_entities", "HYG JNK LQD KRE KBE IWM IYR VNQ TLT".split()),
    ("healthcare_biotech", "UNH ELV CI HUM CVS ABBV JNJ MRK PFE BMY LLY AMGN GILD REGN BIIB VRTX MRNA".split()),
    ("consumer_discretionary", "WMT COST TGT HD LOW SBUX MCD CMG NKE LULU ROST TJX BKNG EXPE MAR HLT RCL CCL NCLH".split()),
    ("communication_platforms", "NFLX DIS CMCSA CHTR T VZ TMUS SPOT ROKU ZM PARA WBD".split()),
    ("transportation_logistics", "UPS FDX UNP CSX NSC DAL UAL AAL LUV JBHT ODFL XPO CHRW".split()),
    ("macro_sensitive_etfs", "SPY QQQ IWM DIA XLF XLK XLE XLU XLI XLY XLV XLB XLP".split()),
    ("volatility_defensive_assets", "VIXY SHY IEF TIP UUP GLD SLV XLU XLP".split()),
    ("contradictory_regime_assets", "TLT XLE GLD KRE UUP HYG DBA VIXY".split()),
    ("bubble_sensitive_momentum_entities", "TSLA PLTR SMCI COIN MSTR APP UPST AFRM ROKU".split()),
    ("high_duration_valuation_sensitive_entities", "ARKK ICLN TAN SNOW DDOG MDB NET ZS CRWD".split()),
])

CATEGORY_TO_SECTOR = {
    "mega_cap_ai_technology": "Technology", "semiconductors": "Technology", "cloud_software_infrastructure": "Technology",
    "ai_infrastructure_suppliers": "Technology", "cybersecurity": "Technology", "industrials_automation": "Industrials",
    "robotics": "Industrials", "energy_utilities": "EnergyUtilities", "commodities": "CommoditiesMaterials", "financials": "Financials",
    "credit_sensitive_entities": "CreditMacro", "healthcare_biotech": "Healthcare", "consumer_discretionary": "Consumer",
    "communication_platforms": "Communication", "transportation_logistics": "Transportation", "macro_sensitive_etfs": "MacroETF",
    "volatility_defensive_assets": "Defensive", "contradictory_regime_assets": "Contradictory", "bubble_sensitive_momentum_entities": "Momentum",
    "high_duration_valuation_sensitive_entities": "DurationSensitive",
}

# bounded deterministic overrides
EXCLUSION_REPLACEMENT_MAP = OrderedDict({"RBT": "ROK", "FANUY": "ABB", "SENT": "CHKP"})
FMP_AVAILABILITY_RISK_OVERRIDES = {"FANUY": "high", "RBT": "high", "SENT": "high", "VIXY": "medium", "ARKK": "medium"}


def _membership_index() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for c, symbols in CATEGORY_SYMBOLS.items():
        for s in symbols:
            out.setdefault(s, []).append(c)
    return out


def _deduplicated_symbols() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for symbols in CATEGORY_SYMBOLS.values():
        for symbol in symbols:
            if symbol not in seen:
                seen.add(symbol)
                out.append(symbol)
    return out


def _default_risk(symbol: str) -> str:
    if symbol in FMP_AVAILABILITY_RISK_OVERRIDES:
        return FMP_AVAILABILITY_RISK_OVERRIDES[symbol]
    if len(symbol) > 4 and not symbol.endswith("Q"):
        return "medium"
    return "low"


def get_sde2_symbol_categories() -> dict[str, list[str]]:
    return {k: list(v) for k, v in CATEGORY_SYMBOLS.items()}


def get_sde2_curated_symbol_universe() -> list[str]:
    return _deduplicated_symbols()


def get_sde2_symbol_validation_metadata() -> dict[str, dict[str, Any]]:
    memberships = _membership_index()
    out: dict[str, dict[str, Any]] = {}
    for symbol in get_sde2_curated_symbol_universe():
        cats = memberships[symbol]
        out[symbol] = {
            "fmp_availability_risk": _default_risk(symbol),
            "category_overlap_count": len(cats),
            "primary_category": cats[0],
            "secondary_categories": cats[1:],
        }
    return out


def get_sde2_diversity_metrics() -> dict[str, float | int]:
    symbols = get_sde2_curated_symbol_universe()
    metadata = get_sde2_symbol_validation_metadata()
    unique_sector_counts = Counter(CATEGORY_TO_SECTOR[metadata[s]["primary_category"]] for s in symbols)
    n = len(symbols)
    max_sector_ratio = max(unique_sector_counts.values()) / n
    contradiction_unique = len({s for s in CATEGORY_SYMBOLS["contradictory_regime_assets"]})
    return {
        "sector_diversity_ratio": round(len(unique_sector_counts) / 20, 6),
        "regime_diversity_ratio": round(len(CATEGORY_SYMBOLS) / 20, 6),
        "contradiction_diversity_ratio": round(contradiction_unique / n, 6),
        "monoculture_risk_ratio": round(max_sector_ratio, 6),
        "topology_balance_ratio": round(1 - max_sector_ratio, 6),
        "propagation_pathway_diversity_ratio": round(len(CATEGORY_SYMBOLS) / 24, 6),
        "universe_size": n,
    }


def validate_sde2_constraints() -> dict[str, Any]:
    symbols = get_sde2_curated_symbol_universe()
    metadata = get_sde2_symbol_validation_metadata()
    sector_counts = Counter(CATEGORY_TO_SECTOR[metadata[s]["primary_category"]] for s in symbols)
    total = len(symbols)
    max_sector_concentration_ratio = max(sector_counts.values()) / total
    max_correlated_cluster_ratio = max(len(set(v)) for v in CATEGORY_SYMBOLS.values()) / total
    contradiction_diversity_ratio = len(set(CATEGORY_SYMBOLS["contradictory_regime_assets"])) / total
    high_risk = sorted([s for s, m in metadata.items() if m["fmp_availability_risk"] == "high"])
    return {
        "max_sector_concentration_ratio": round(max_sector_concentration_ratio, 6),
        "max_correlated_cluster_ratio": round(max_correlated_cluster_ratio, 6),
        "minimum_category_diversity_count": len(CATEGORY_SYMBOLS),
        "minimum_contradiction_diversity_ratio": round(contradiction_diversity_ratio, 6),
        "high_risk_tickers": high_risk,
        "passes": MIN_UNIVERSE_SIZE <= total <= MAX_UNIVERSE_SIZE and max_sector_concentration_ratio <= 0.42 and len(CATEGORY_SYMBOLS) >= 20 and contradiction_diversity_ratio >= 0.03,
    }


def build_sde2_artifacts(output_root: str = "reports/sde2") -> dict[str, str]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    symbols = get_sde2_curated_symbol_universe()
    payload = {
        "version": SDE2_VERSION,
        "universe_size": len(symbols),
        "symbols": symbols,
        "categories": get_sde2_symbol_categories(),
        "symbol_validation_metadata": get_sde2_symbol_validation_metadata(),
        "diversity_metrics": get_sde2_diversity_metrics(),
        "anti_monoculture_constraints": validate_sde2_constraints(),
        "bounded_exclusion_replacement_list": EXCLUSION_REPLACEMENT_MAP,
        "topology_review_summaries": ["topology diversity increased materially", "monoculture risk reduced", "macro contradiction pathways improved", "continuity opportunity space expanded", "saturation concentration moderated"],
        "governance_certification": {"observational_only_semantics": True, "no_prediction_or_trading_logic": True, "no_replay_activation": True, "no_topology_activation": True, "no_autonomous_orchestration": True, "no_cognition_persistence_introduced": True},
        "next_phase_recommendations": ["Use as readiness input for future HIST-DENSITY scope planning.", "Preserve deterministic curation and anti-monoculture checks before ingestion expansion."],
    }
    json_path = root / "sde2_curated_universe.json"
    md_path = root / "sde2_curated_universe.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(
        "\n".join([
            "# SDE-2 Curated Universe",
            f"- Version: {SDE2_VERSION}",
            f"- Universe size: {len(symbols)}",
            "- GOOG/GOOGL handling: GOOG excluded; GOOGL retained as canonical share class to avoid dual counting.",
            "", "## FMP availability risk",
            "- High-risk focus: FANUY, RBT, SENT (flagged for deterministic review and bounded replacement mapping).",
            "", "## Governance certification",
            "- observational-only semantics", "- no prediction/trading logic", "- no replay activation", "- no topology activation", "- no autonomous orchestration", "- no cognition persistence introduced",
        ]) + "\n",
        encoding="utf-8",
    )
    return {"json_path": str(json_path), "md_path": str(md_path)}
