from __future__ import annotations

from collections import Counter, OrderedDict
from math import log
from typing import Any

REQUIRED_FIELDS = [
    "ticker",
    "company_name",
    "sector",
    "subsector",
    "themes",
    "regime_sensitivity",
    "contradiction_exposures",
    "propagation_vectors",
    "volatility_profile",
    "market_cap_bucket",
    "geography",
    "topology_cluster",
]

PREDICTION_FORBIDDEN_FIELDS = {
    "target_price",
    "signal",
    "alpha",
    "position_size",
    "trade_action",
    "forecast",
}

CLUSTERS: OrderedDict[str, dict[str, Any]] = OrderedDict(
    [
        ("ai_semis_compute", {"sector": "Technology", "subsector": "Semiconductors", "themes": ["AI-linked", "compute-cycle"], "regime_sensitivity": "risk_on", "contradiction_exposures": ["AI exuberance", "inventory cyclicality", "valuation excess"], "propagation_vectors": ["AI compute chain", "semiconductor capex chain"], "volatility_profile": "high", "market_cap_bucket": "mega_to_mid", "geography": "global", "topology_cluster": "compute_infrastructure"}),
        ("cloud_software_cyber", {"sector": "Technology", "subsector": "Software", "themes": ["enterprise digitization", "cyber demand"], "regime_sensitivity": "risk_on", "contradiction_exposures": ["enterprise spending compression", "valuation excess"], "propagation_vectors": ["enterprise IT spending", "AI compute chain"], "volatility_profile": "medium_high", "market_cap_bucket": "large_to_mid", "geography": "global", "topology_cluster": "application_control"}),
        ("power_utilities_grid", {"sector": "Utilities", "subsector": "Electric Utilities", "themes": ["power demand", "grid capex"], "regime_sensitivity": "defensive", "contradiction_exposures": ["rates sensitivity", "infrastructure bottleneck"], "propagation_vectors": ["power demand chain"], "volatility_profile": "medium", "market_cap_bucket": "large_to_mid", "geography": "domestic_plus", "topology_cluster": "power_backbone"}),
        ("energy_oil_lng_infra", {"sector": "Energy", "subsector": "Integrated Energy", "themes": ["energy-linked", "inflation transmission"], "regime_sensitivity": "inflationary", "contradiction_exposures": ["energy transition conflict", "geopolitical exposure"], "propagation_vectors": ["energy inflation transmission"], "volatility_profile": "high", "market_cap_bucket": "large_to_mid", "geography": "global", "topology_cluster": "commodity_transmission"}),
        ("industrials_automation_aero", {"sector": "Industrials", "subsector": "Capital Goods", "themes": ["infrastructure-sensitive", "cycle-sensitive"], "regime_sensitivity": "cyclical", "contradiction_exposures": ["inventory cyclicality", "infrastructure bottleneck"], "propagation_vectors": ["industrial automation chain", "freight/logistics chain"], "volatility_profile": "medium_high", "market_cap_bucket": "large_to_mid", "geography": "global", "topology_cluster": "real_economy_linkers"}),
        ("financials_banks_insurers", {"sector": "Financials", "subsector": "Diversified Financials", "themes": ["financial-stress-linked", "credit-cycle"], "regime_sensitivity": "rates_sensitive", "contradiction_exposures": ["rates sensitivity", "liquidity fragility"], "propagation_vectors": ["credit stress transmission"], "volatility_profile": "medium_high", "market_cap_bucket": "large_to_mid", "geography": "domestic_plus", "topology_cluster": "balance_sheet_network"}),
        ("consumer_retail_travel_luxury", {"sector": "Consumer Discretionary", "subsector": "Retail & Services", "themes": ["consumer-linked", "discretionary"], "regime_sensitivity": "cyclical", "contradiction_exposures": ["consumer weakness", "valuation excess"], "propagation_vectors": ["consumer discretionary chain"], "volatility_profile": "medium_high", "market_cap_bucket": "mega_to_mid", "geography": "global", "topology_cluster": "demand_sentiment"}),
        ("healthcare_pharma_biotech", {"sector": "Healthcare", "subsector": "Pharma/Biotech/Devices", "themes": ["defensive", "innovation"], "regime_sensitivity": "defensive", "contradiction_exposures": ["rates sensitivity", "valuation excess"], "propagation_vectors": ["healthcare innovation chain"], "volatility_profile": "medium", "market_cap_bucket": "large_to_mid", "geography": "global", "topology_cluster": "defensive_innovation"}),
        ("commodities_mining_materials", {"sector": "Materials", "subsector": "Mining & Materials", "themes": ["commodity-beta", "macro-sensitive"], "regime_sensitivity": "inflationary", "contradiction_exposures": ["geopolitical exposure", "energy transition conflict"], "propagation_vectors": ["energy inflation transmission"], "volatility_profile": "high", "market_cap_bucket": "large_to_mid", "geography": "global", "topology_cluster": "input_cost_transmission"}),
        ("telecom_media_logistics_reits", {"sector": "Communication/RealAssets", "subsector": "Telecom/Media/Logistics/REITs", "themes": ["infrastructure-sensitive", "yield-sensitive"], "regime_sensitivity": "mixed", "contradiction_exposures": ["rates sensitivity", "consumer weakness"], "propagation_vectors": ["freight/logistics chain", "enterprise IT spending"], "volatility_profile": "medium", "market_cap_bucket": "large_to_mid", "geography": "mixed", "topology_cluster": "connectivity_distribution"}),
    ]
)
# existing CLUSTER_TICKERS unchanged
CLUSTER_TICKERS = OrderedDict([
("ai_semis_compute", "NVDA AMD AVGO QCOM MU INTC TXN AMAT LRCX KLAC MCHP MPWR ADI MRVL ON NXPI TER SWKS QRVO ASML TSM ARM GFS UMC SMCI ANET CSCO HPE DELL HPQ WDC STX CORZ IONQ RGTI IBM AAPL GOOG META MSFT".split()),
("cloud_software_cyber", "ORCL CRM ADBE NOW INTU SAP SNOW PANW CRWD FTNT ZS OKTA NET DDOG MDB ESTC HUBS TEAM SHOP WDAY DOCU SPLK AKAM CHKP GEN PAYC ADSK UBER ABNB APPF BRZE TWLO CFLT PLTR DT".split()),
("power_utilities_grid", "NEE SO DUK AEP EXC XEL SRE D ETR CEG PCG PEG ED FE EIX PPL AEE WEC AES NI".split()),
("energy_oil_lng_infra", "XOM CVX COP EOG OXY SLB HAL BKR VLO MPC PSX KMI WMB TRGP LNG FANG APA DVN MRO EQT CTRA PXD HES BP SHEL TOT".split()),
("industrials_automation_aero", "GE RTX BA LMT NOC GD HII CAT DE PCAR CMI ETN EMR HON ROK PH ITW JCI CARR OTIS MMM UPS FDX UNP CSX NSC WM RSG URI GWW FAST PWR JBL".split()),
("financials_banks_insurers", "JPM BAC WFC C GS MS BK STT USB PNC TFC MTB FITB RF KEY COF AXP SCHW BLK BX KKR APO AIG ALL TRV PGR CB MET PRU AFL MMC AJG SPGI MCO".split()),
("consumer_retail_travel_luxury", "AMZN WMT COST TGT HD LOW SBUX MCD YUM CMG NKE LULU DECK ROST TJX DG DLTR BBY EBAY ETSY BKNG EXPE MAR HLT RCL CCL NCLH TSLA GM F ULTA DPZ RL".split()),
("healthcare_pharma_biotech", "UNH ELV CI HUM CVS CAH MCK ABBV JNJ MRK PFE BMY LLY AMGN GILD REGN BIIB VRTX ISRG MDT SYK BSX BDX EW TMO DHR IQV A ZTS ILMN ALNY MRNA NBIX INCY".split()),
("commodities_mining_materials", "LIN APD ECL SHW FCX NEM AA CENX NUE STLD X CLF RS SCCO TECK BHP RIO VALE MOS CF ALB".split()),
("telecom_media_logistics_reits", "T VZ TMUS CMCSA CHTR PARA DIS WBD NFLX SPOT LYV ROKU ZM AMT CCI SBAC EQIX DLR PLD O STAG PSA EXR EGP".split()),
])

UNIVERSE = []
for cluster, tickers in CLUSTER_TICKERS.items():
    spec = CLUSTERS[cluster]
    for t in tickers:
        UNIVERSE.append({"ticker": t, "company_name": f"{t} Corporation", **spec})

FMP_COVERAGE_FIXTURE = {r["ticker"] for r in UNIVERSE}

def load_curated_300_stock_universe() -> list[dict[str, Any]]: return [dict(r) for r in UNIVERSE]
def validate_curated_300_stock_count(records): return len(records) == 300
def validate_unique_tickers(records): return len({r["ticker"] for r in records}) == len(records)
def validate_required_fields(records): return all(all(f in r and r[f] not in (None, "", []) for f in REQUIRED_FIELDS) for r in records)
def validate_sector_diversity(records, min_sectors: int = 8): return len({r["sector"] for r in records}) >= min_sectors
def validate_semantic_cluster_diversity(records, min_clusters: int = 10): return len({r["topology_cluster"] for r in records}) >= min_clusters
def validate_anti_monoculture_distribution(records, max_cluster_share: float = 0.20): return max(Counter(r["topology_cluster"] for r in records).values()) / len(records) <= max_cluster_share
def validate_no_prediction_fields(records): return all(not any(k in PREDICTION_FORBIDDEN_FIELDS for k in r) for r in records)
def validate_fmp_symbol_coverage(records, fixture_symbols: set[str] | None = None): return all(r["ticker"] in (fixture_symbols or FMP_COVERAGE_FIXTURE) for r in records)

def compute_diversification_controls(records, sector_cap=0.22, theme_cap=0.26):
    n = len(records)
    sector = Counter(r["sector"] for r in records)
    themes = Counter(t for r in records for t in r["themes"])
    norm = lambda c: OrderedDict(sorted((k, round(v / n, 6)) for k, v in c.items()))
    sector_share, theme_share = norm(sector), norm(themes)
    return OrderedDict([
        ("sector_cap", sector_cap),
        ("theme_cap", theme_cap),
        ("sector_cap_breaches", [k for k, v in sector_share.items() if v > sector_cap]),
        ("theme_cap_breaches", [k for k, v in theme_share.items() if v > theme_cap]),
        ("anti_monoculture_score", round(1 - max(sector_share.values()), 6)),
        ("redundancy_similarity_score", round(sum(v * v for v in sector_share.values()), 6)),
        ("topology_richness_score", round(len({r['topology_cluster'] for r in records}) / 10, 6)),
        ("propagation_diversity_score", round(len({p for r in records for p in r['propagation_vectors']}) / 12, 6)),
        ("ecosystem_entropy_score", round(-sum(v * log(v) for v in sector_share.values()), 6)),
    ])

def build_topology_diversity_scaffolding(records):
    bridge_pairs = sorted({tuple(sorted((r["sector"], s))) for r in records for s in ["Technology", "Energy", "Financials"] if s != r["sector"]})
    return OrderedDict([
        ("cross_sector_bridges", bridge_pairs[:20]),
        ("thematic_linkages", OrderedDict(sorted((t, sum(t in r["themes"] for r in records)) for t in {x for r in records for x in r["themes"]}))),
        ("propagation_pathway_candidates", sorted({p for r in records for p in r["propagation_vectors"]})),
        ("adjacency_diversity_summary", OrderedDict([("unique_sectors", len({r['sector'] for r in records})), ("unique_topology_clusters", len({r['topology_cluster'] for r in records}))])),
    ])

def build_curated_300_stock_ecosystem_summary(records):
    controls = compute_diversification_controls(records)
    return OrderedDict([
        ("deterministic_version", "OBS300_1A_1B_V1"),
        ("total_records", len(records)),
        ("diversification_controls", controls),
        ("topology_richness_summary", f"clusters={len({r['topology_cluster'] for r in records})}"),
        ("monoculture_warnings", controls["sector_cap_breaches"] + controls["theme_cap_breaches"]),
        ("propagation_diversity_summary", controls["propagation_diversity_score"]),
        ("entropy_preservation_summary", controls["ecosystem_entropy_score"]),
        ("diversification_assessment", "stable" if not controls["sector_cap_breaches"] else "review"),
        ("structural_diversity_summary", "broad" if controls["topology_richness_score"] >= 1 else "narrow"),
        ("observational_only", True),
        ("no_recursive_replay_operationalization", True),
        ("no_autonomous_replay", True),
        ("no_topology_activation", True),
        ("no_self_modifying_pathways", True),
        ("no_prediction_or_trading_execution", True),
    ])
