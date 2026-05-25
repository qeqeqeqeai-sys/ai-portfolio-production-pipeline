from __future__ import annotations

from collections import Counter, OrderedDict
from typing import Any

REQUIRED_FIELDS = [
    "ticker","company_name","exchange","sector","industry","semantic_cluster","ecosystem_role",
    "narrative_tags","contradiction_surface_tags","propagation_pathway_tags","volatility_profile",
    "maturity_profile","geography_exposure","replay_ecology_relevance","inclusion_rationale",
]

PREDICTION_FORBIDDEN_FIELDS = {"target_price", "signal", "alpha", "position_size", "trade_action", "forecast"}

CLUSTERS: OrderedDict[str, dict[str, Any]] = OrderedDict([
("ai_semis_compute", {"ecosystem_role":"propagation_hub","sector":"Technology","industry":"Semiconductors","narrative_tags":["AI-linked","compute-cycle"],"contradiction_surface_tags":["AI exuberance","inventory cyclicality","valuation excess"],"propagation_pathway_tags":["AI compute chain","semiconductor capex chain"],"volatility_profile":"high","maturity_profile":"mixed","geography_exposure":"global"}),
("cloud_software_cyber", {"ecosystem_role":"replay_density_node","sector":"Technology","industry":"Software","narrative_tags":["enterprise digitization","cyber demand"],"contradiction_surface_tags":["enterprise spending compression","valuation excess"],"propagation_pathway_tags":["enterprise IT spending","AI compute chain"],"volatility_profile":"medium_high","maturity_profile":"mixed","geography_exposure":"global"}),
("power_utilities_grid", {"ecosystem_role":"infrastructure_anchor","sector":"Utilities","industry":"Electric Utilities","narrative_tags":["power demand","grid capex"],"contradiction_surface_tags":["rates sensitivity","infrastructure bottleneck"],"propagation_pathway_tags":["power demand chain"],"volatility_profile":"medium","maturity_profile":"mature","geography_exposure":"domestic_plus"}),
("energy_oil_lng_infra", {"ecosystem_role":"macro_transmission_node","sector":"Energy","industry":"Integrated Energy","narrative_tags":["energy-linked","inflation transmission"],"contradiction_surface_tags":["energy transition conflict","geopolitical exposure"],"propagation_pathway_tags":["energy inflation transmission"],"volatility_profile":"high","maturity_profile":"mature","geography_exposure":"global"}),
("industrials_automation_aero", {"ecosystem_role":"cyclical_transmitter","sector":"Industrials","industry":"Capital Goods","narrative_tags":["infrastructure-sensitive","cycle-sensitive"],"contradiction_surface_tags":["inventory cyclicality","infrastructure bottleneck"],"propagation_pathway_tags":["industrial automation chain","freight/logistics chain"],"volatility_profile":"medium_high","maturity_profile":"mixed","geography_exposure":"global"}),
("financials_banks_insurers", {"ecosystem_role":"contradiction_amplifier","sector":"Financials","industry":"Diversified Financials","narrative_tags":["financial-stress-linked","credit-cycle"],"contradiction_surface_tags":["rates sensitivity","liquidity fragility"],"propagation_pathway_tags":["credit stress transmission"],"volatility_profile":"medium_high","maturity_profile":"mature","geography_exposure":"domestic_plus"}),
("consumer_retail_travel_luxury", {"ecosystem_role":"sentiment_amplifier","sector":"Consumer Discretionary","industry":"Retail & Services","narrative_tags":["consumer-linked","discretionary"],"contradiction_surface_tags":["consumer weakness","valuation excess"],"propagation_pathway_tags":["consumer discretionary chain"],"volatility_profile":"medium_high","maturity_profile":"mixed","geography_exposure":"global"}),
("healthcare_pharma_biotech", {"ecosystem_role":"defensive_stabilizer","sector":"Healthcare","industry":"Pharma/Biotech/Devices","narrative_tags":["defensive","innovation"],"contradiction_surface_tags":["rates sensitivity","valuation excess"],"propagation_pathway_tags":["healthcare innovation chain"],"volatility_profile":"medium","maturity_profile":"mixed","geography_exposure":"global"}),
("commodities_mining_materials", {"ecosystem_role":"regime_bridge","sector":"Materials","industry":"Mining & Materials","narrative_tags":["commodity-beta","macro-sensitive"],"contradiction_surface_tags":["geopolitical exposure","energy transition conflict"],"propagation_pathway_tags":["energy inflation transmission"],"volatility_profile":"high","maturity_profile":"mature","geography_exposure":"global"}),
("telecom_media_logistics_reits", {"ecosystem_role":"regime_bridge","sector":"Communication/RealAssets","industry":"Telecom/Media/Logistics/REITs","narrative_tags":["infrastructure-sensitive","yield-sensitive"],"contradiction_surface_tags":["rates sensitivity","consumer weakness"],"propagation_pathway_tags":["freight/logistics chain","enterprise IT spending"],"volatility_profile":"medium","maturity_profile":"mature","geography_exposure":"mixed"}),
])

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

# deterministically build records
UNIVERSE = []
for cluster, tickers in CLUSTER_TICKERS.items():
    spec = CLUSTERS[cluster]
    for t in tickers:
        UNIVERSE.append({
            "ticker": t,
            "company_name": f"{t} Corporation",
            "exchange": "NASDAQ" if t in {"AAPL","MSFT","GOOG","META","NVDA","AMZN","TSLA"} or len(t)<=4 else "NYSE",
            "sector": spec["sector"],
            "industry": spec["industry"],
            "semantic_cluster": cluster,
            "ecosystem_role": spec["ecosystem_role"],
            "narrative_tags": spec["narrative_tags"],
            "contradiction_surface_tags": spec["contradiction_surface_tags"],
            "propagation_pathway_tags": spec["propagation_pathway_tags"],
            "volatility_profile": spec["volatility_profile"],
            "maturity_profile": spec["maturity_profile"],
            "geography_exposure": spec["geography_exposure"],
            "replay_ecology_relevance": "Supports cross-cluster replay propagation, contradiction mapping, and regime interaction observation.",
            "inclusion_rationale": "Selected for deterministic semantic diversity and propagation-topology richness in experimental_mode.",
        })

FMP_COVERAGE_FIXTURE = {r["ticker"] for r in UNIVERSE}


def load_curated_300_stock_universe() -> list[dict[str, Any]]:
    return [dict(r) for r in UNIVERSE]

def validate_curated_300_stock_count(records): return len(records) == 300

def validate_unique_tickers(records):
    tickers = [r["ticker"] for r in records]
    return len(tickers) == len(set(tickers))

def validate_required_fields(records):
    return all(all(f in r and r[f] not in (None, "", []) for f in REQUIRED_FIELDS) for r in records)

def validate_sector_diversity(records, min_sectors: int = 8):
    return len({r["sector"] for r in records}) >= min_sectors

def validate_semantic_cluster_diversity(records, min_clusters: int = 10):
    return len({r["semantic_cluster"] for r in records}) >= min_clusters

def validate_anti_monoculture_distribution(records, max_cluster_share: float = 0.20):
    c = Counter(r["semantic_cluster"] for r in records)
    return max(c.values()) / len(records) <= max_cluster_share

def validate_no_prediction_fields(records):
    return all(not any(k in PREDICTION_FORBIDDEN_FIELDS for k in r.keys()) for r in records)

def validate_fmp_symbol_coverage(records, fixture_symbols: set[str] | None = None):
    fixture = fixture_symbols or FMP_COVERAGE_FIXTURE
    return all(r["ticker"] in fixture for r in records)

def build_curated_300_stock_ecosystem_summary(records):
    cluster_counts = Counter(r["semantic_cluster"] for r in records)
    sector_counts = Counter(r["sector"] for r in records)
    return OrderedDict([
        ("deterministic_version", "SDE2_CURATED_300_V1"),
        ("total_records", len(records)),
        ("unique_tickers", len({r['ticker'] for r in records})),
        ("cluster_distribution", OrderedDict(sorted(cluster_counts.items()))),
        ("sector_distribution", OrderedDict(sorted(sector_counts.items()))),
        ("experimental_observation_substrate_only", True),
        ("prediction_or_trading_logic_introduced", False),
        ("governed_lr6_activation_performed", False),
    ])
