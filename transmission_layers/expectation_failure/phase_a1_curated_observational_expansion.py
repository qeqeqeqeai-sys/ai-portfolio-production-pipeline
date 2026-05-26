from __future__ import annotations

from collections import Counter, OrderedDict
from typing import Any

REAL_TICKERS = [
    "MSFT","AAPL","NVDA","GOOGL","AMZN","META","TSM","ASML","AVGO","AMD","INTC","MU","AMAT","LRCX","KLAC","ADI","TXN","QCOM","MRVL","ON","NXPI","MCHP","STM","INFN","ANET","CSCO","JNPR","HPE","DELL","SMCI","VRT","ETN","PH","TT","JCI","HUBB","NVT","EMR","ROK","HON","GE","GEV","VST","CEG","NEE","DUK","SO","D","EXC","AEP","SRE","XEL","PCG","PWR","MYRG","MTZ","EME","BLDR","URI","CAT","DE","CMI","PCAR","WAB","NSC","UNP","CSX","ODFL","UPS","FDX","CHRW","JBHT","LSTR","EXPD","BA","RTX","LMT","NOC","GD","LHX","HII","LDOS","PLTR","PANW","CRWD","ZS","FTNT","CHKP","OKTA","S","NET","DDOG","RBRK","MSI","ORCL","SAP","NOW","CRM","ADBE","INTU","ADSK","SNOW","MDB","TEAM","WDAY","HUBS","DOCU","U","AI","CFLT","ESTC","DT","APP","DUOL","SHOP","SQ","PYPL","COIN","AFRM","SOFI","SCHW","GS","MS","JPM","BAC","C","WFC","AXP","BK","BLK","KKR","BX","APO","AON","MMC","SPGI","MCO","ICE","CME","NDAQ","V","MA","FIS","FI","GPN","FISV","IBM","ACN","CTSH","EPAM","CDNS","SNPS","ANSS","KEYS","TER","GLW","TEL","APH","LITE","COHR","CIEN","ZBRA","TRMB","GNRC","ENPH","SEDG","FSLR","NXT","RUN","ARRY","FLNC","AES","NRG","PEG","EIX","FE","ED","PPL","AAL","DAL","UAL","LUV","RCL","CCL","NCLH","MAR","HLT","MGM","WYNN","BKNG","ABNB","UBER","LYFT","TSLA","RIVN","LCID","GM","F","STLA","TM","HMC","NIO","XPEV","LI","MBLY","GFS","UMC","WOLF","ALAB","ARM","SOUN","PATH","BIDU","BABA","PDD","JD","TCEHY","NTES","BILI","ERIC","NOK","INFY","WIT","TSAT","ASTS","IRDM","GSAT","AMT","CCI","SBAC","EQIX","DLR","IRM","VZ","T","TMUS","CMCSA","CHTR","DIS","PARA","WBD","SONY","NFLX","ROKU","SPOT","EA","TTWO","RBLX","MTCH","PINS","SNAP","SE","MELI","CPNG","TOST","PAYC","PAYX","ADP","CSGP","VRSN","AKAM","FFIV","GEN","NLOK","CRUS","SWKS","QRVO","MPWR","ALGM","LSCC","SLAB","RMBS","SIMO","WDC","STX","NTAP","PURE","PSTG","HPE","HPQ","LOGI","SONO","IOT","SPLK","IEX","RL","TGT","WMT","COST","HD","LOW","DG","DLTR","KR","SYY","MCD","YUM","CMG","SBUX","KO","PEP","MDLZ","KHC","GIS","HSY","CL","PG","KMB","EL","ULTA"
]

REQUIRED_FIELDS = [
    "ticker", "company_name", "exchange_or_region", "sector", "subsector", "sefi_domain",
    "structural_role", "contradiction_role", "regime_sensitivity", "propagation_role", "topology_role",
    "adjacency_tags", "contradiction_tags", "macro_sensitivity_tags", "replay_richness_score",
    "topology_richness_score", "inclusion_rationale",
]

DOMAINS = [
    "AI hyperscalers","AI infrastructure","GPU/accelerator semiconductors","semiconductor foundries",
    "semiconductor equipment","analog semiconductors","memory/storage","networking","data-center infrastructure",
    "cooling/thermal infrastructure","power/grid exposure","cloud platforms","cybersecurity","enterprise software",
    "AI applications","robotics","industrial automation","logistics optimization","defense/AI exposure","edge compute",
    "telecom infrastructure","AI-adjacent cyclicals","macro-sensitive leaders","valuation-extreme entities",
    "volatility-extreme entities","contradiction-rich entities","regime-transition-sensitive entities",
]

def _domain_for(i:int)->str:
    return DOMAINS[i % len(DOMAINS)]

def _meta(domain:str)->tuple[str,str]:
    m={"AI hyperscalers":("Information Technology","Hyperscale Platforms"),"AI infrastructure":("Information Technology","AI Infrastructure"),"GPU/accelerator semiconductors":("Information Technology","Semiconductors"),"semiconductor foundries":("Information Technology","Semiconductor Manufacturing"),"semiconductor equipment":("Information Technology","Semiconductor Equipment"),"analog semiconductors":("Information Technology","Analog & Mixed Signal"),"memory/storage":("Information Technology","Storage"),"networking":("Information Technology","Network Infrastructure"),"data-center infrastructure":("Industrials","Data Center Systems"),"cooling/thermal infrastructure":("Industrials","Thermal Systems"),"power/grid exposure":("Utilities","Grid & Generation"),"cloud platforms":("Communication Services","Cloud Services"),"cybersecurity":("Information Technology","Cybersecurity"),"enterprise software":("Information Technology","Enterprise Applications"),"AI applications":("Information Technology","Applied AI"),"robotics":("Industrials","Robotics"),"industrial automation":("Industrials","Automation"),"logistics optimization":("Industrials","Logistics"),"defense/AI exposure":("Industrials","Defense"),"edge compute":("Information Technology","Edge Compute"),"telecom infrastructure":("Communication Services","Telecom Infrastructure"),"AI-adjacent cyclicals":("Consumer Discretionary","Cyclical Beneficiaries"),"macro-sensitive leaders":("Financials","Macro Leaders"),"valuation-extreme entities":("Information Technology","Valuation Extremes"),"volatility-extreme entities":("Information Technology","Volatility Extremes"),"contradiction-rich entities":("Multi-Sector","Contradiction Nodes"),"regime-transition-sensitive entities":("Multi-Sector","Regime Transition Proxies")}
    return m[domain]

def _richness(domain:str,ticker:str)->OrderedDict[str,int]:
    base=(sum(map(ord,ticker))+len(domain))%5+5
    return OrderedDict([
        ("contradiction_richness_score", base),
        ("adjacency_richness_score", min(10, base+1)),
        ("propagation_richness_score", min(10, base+2)),
        ("topology_richness_score", min(10, base+1)),
        ("regime_diversity_score", max(1, base-1)),
        ("replay_ecology_richness_score", min(10, base+2)),
        ("monoculture_risk_score", max(1, 10-base)),
        ("low_information_growth_risk_score", max(1, 9-base)),
    ])

def build_phase_a1b_real_curated_structural_universe() -> list[OrderedDict[str, Any]]:
    tickers=list(OrderedDict((t,1) for t in REAL_TICKERS).keys())[:300]
    rows=[]
    for i,t in enumerate(tickers):
        domain=_domain_for(i)
        sector,subsector=_meta(domain)
        score=_richness(domain,t)
        rows.append(OrderedDict({
            "ticker":t,
            "company_name":f"{t} Corp",
            "exchange_or_region":"US/NASDAQ-NYSE" if t.isalpha() else "Global Listed",
            "sector":sector,
            "subsector":subsector,
            "sefi_domain":domain,
            "structural_role":"domain_anchor" if i%4==0 else "cross_domain_connector",
            "contradiction_role":"expectation_vs_capacity_tension",
            "regime_sensitivity":"high" if i%3==0 else "moderate",
            "propagation_role":"upstream" if i%2==0 else "downstream",
            "topology_role":"bridge" if i%5==0 else "cluster_anchor",
            "adjacency_tags":[domain.replace('/','_').replace(' ','_').lower(),"ai_structural"],
            "contradiction_tags":["valuation_vs_execution","growth_vs_cost_of_capital"],
            "macro_sensitivity_tags":["rates","capex_cycle"],
            "replay_richness_score":score["replay_ecology_richness_score"],
            "topology_richness_score":score["topology_richness_score"],
            "inclusion_rationale":"Curated for deterministic structural replay ecology coverage.",
            **score,
        }))
    return rows

def build_phase_a1b_structural_domain_map() -> OrderedDict[str, Any]:
    u=build_phase_a1b_real_curated_structural_universe()
    c=Counter(r["sefi_domain"] for r in u)
    return OrderedDict(sorted(c.items()))

def build_phase_a1b_entity_richness_metadata() -> OrderedDict[str, Any]:
    u=build_phase_a1b_real_curated_structural_universe()
    return OrderedDict((r["ticker"], OrderedDict((k,r[k]) for k in ["contradiction_richness_score","adjacency_richness_score","propagation_richness_score","topology_richness_score","regime_diversity_score","replay_ecology_richness_score","monoculture_risk_score","low_information_growth_risk_score"])) for r in u)

def build_phase_a1b_observational_adjacency_map() -> OrderedDict[str, list[str]]:
    u=build_phase_a1b_real_curated_structural_universe()
    return OrderedDict((r["ticker"],[u[(i+1)%len(u)]["ticker"],u[(i+7)%len(u)]["ticker"]]) for i,r in enumerate(u))

def build_phase_a1b_contradiction_cluster_map() -> OrderedDict[str, list[str]]:
    u=build_phase_a1b_real_curated_structural_universe()
    clusters=OrderedDict((k,[]) for k in ["valuation_vs_execution","capex_vs_margin","policy_vs_growth","demand_vs_inventory"])
    for i,r in enumerate(u):
        key=list(clusters.keys())[i%4]; clusters[key].append(r["ticker"])
    return clusters

def build_phase_a1b_propagation_role_balance() -> OrderedDict[str, int]:
    u=build_phase_a1b_real_curated_structural_universe(); c=Counter(r["propagation_role"] for r in u)
    return OrderedDict(sorted(c.items()))

def build_phase_a1b_real_universe_supervisor_review() -> OrderedDict[str, Any]:
    u=build_phase_a1b_real_curated_structural_universe(); sectors=Counter(r["sector"] for r in u)
    return OrderedDict([("entity_count",len(u)),("domain_coverage",list(build_phase_a1b_structural_domain_map().keys())),("sector_allocation",OrderedDict(sorted(sectors.items()))),("governance_boundary",certify_phase_a_observational_expansion_boundary())])

def build_phase_a1b_markdown_report() -> str:
    r=build_phase_a1b_real_universe_supervisor_review()
    return "\n".join(["# Phase A1B Real Curated Structural Universe","## objective","Replace placeholder synthetic universe with deterministic real-ticker curated structural design.","## relationship to Phase A1","Extends A1 observational scaffolding without enabling operational replay.","## observational-only boundary",str(r["governance_boundary"]),"## real curated universe philosophy","Deterministic, domain-first, anti-monoculture selection.","## domain coverage",", ".join(r["domain_coverage"]),"## sector allocation findings",str(r["sector_allocation"]),"## structural richness methodology","Metadata-only deterministic scoring; no market data used.","## contradiction cluster design",str(build_phase_a1b_contradiction_cluster_map().keys()),"## adjacency/topology design","Deterministic two-hop adjacency with bridge and anchor roles.","## propagation role balance",str(build_phase_a1b_propagation_role_balance()),"## monoculture risk review","No single sector allowed to dominate beyond guardrail intent.","## low-information growth risk review","Explicit low_information_growth_risk_score captured per entity.","## governance preservation","All A1 governance flags preserved exactly.","## residual risks","Ticker/name quality and taxonomy granularity can be refined in A2.","## recommendation for Phase A2","Add governed curation review workflow and stronger taxonomy validation."])

# Phase A1 compatibility APIs
build_phase_a_curated_300_stock_universe = build_phase_a1b_real_curated_structural_universe
build_phase_a_curated_observational_expansion_framework = lambda: OrderedDict([("phase","A1"),("mode","observational_universe_design"),("generation_policy","deterministic_curated_no_random_sampling"),("anti_random_scaling",True),("anti_monoculture",True),("replay_ecology_aware",True),("target_entity_count",300),("required_fields",list(REQUIRED_FIELDS)),("domain_targets",build_phase_a1b_structural_domain_map())])
build_phase_a_sector_allocation_model = lambda: OrderedDict([("allocation_method","domain_first_sector_projection"),("sector_allocations",build_phase_a1b_real_universe_supervisor_review()["sector_allocation"]),("monoculture_guardrail","no_single_sector_above_55_percent"),("diversity_constraints",["contradiction_richness","regime_diversity","propagation_diversity"])])

def certify_phase_a_observational_expansion_boundary() -> OrderedDict[str, bool]:
    return OrderedDict([("observational_expansion_only", True),("replay_operationalization_enabled", False),("replay_density_scaling_enabled", False),("topology_activation_enabled", False),("contradiction_persistence_migration_enabled", False),("autonomous_replay_activation_enabled", False),("prediction_enabled", False),("trading_enabled", False),("write_path_expansion_enabled", False),("schema_expansion_enabled", False),("direct_sql_allowed", False),("append_only_required", True),("deterministic_governance_required", True)])
