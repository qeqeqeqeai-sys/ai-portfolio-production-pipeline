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
DOMAIN_TARGETS = OrderedDict((d, True) for d in DOMAINS)

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


A1C_ADJACENCY_CLASSES = [
    "hyperscaler_to_gpu","gpu_to_foundry","foundry_to_semicap","semicap_to_memory","data_center_to_power",
    "data_center_to_cooling","power_to_grid_infrastructure","cloud_to_cybersecurity","cloud_to_enterprise_software",
    "ai_application_to_cloud","ai_application_to_data_infrastructure","robotics_to_industrial_automation",
    "industrial_to_logistics","defense_ai_to_satellite_comms","telecom_to_edge_compute",
    "macro_financials_to_duration_assets","consumer_ai_to_discretionary_demand","valuation_extreme_to_liquidity_conditions",
    "volatility_extreme_to_risk_appetite","regime_transition_to_macro_sensitive_leaders",
]

A1C_CONTRADICTION_CLASSES = ["ai_monetization_fragility","hyperscaler_capex_stress","gpu_supply_vs_demand","foundry_geopolitical_dependency","semicap_cycle_reversal","memory_oversupply_risk","data_center_power_bottleneck","cooling_capacity_constraint","cloud_margin_pressure","cybersecurity_spend_resilience","enterprise_ai_roi_uncertainty","ai_application_revenue_quality","valuation_duration_fragility","liquidity_risk_appetite_reversal","industrial_cycle_slowdown","logistics_demand_normalization","defense_budget_policy_tension","telecom_monetization_weakness","edge_vs_cloud_deployment_asymmetry","macro_rates_growth_tension"]
A1C_PROPAGATION_CLASSES = ["upstream_infrastructure_bottleneck","downstream_ai_beneficiary","capex_cycle_transmitter","margin_pressure_transmitter","valuation_amplifier","macro_duration_amplifier","liquidity_beta_amplifier","supply_chain_constraint_node","geopolitical_dependency_node","demand_normalization_node","policy_sensitivity_node","physical_infrastructure_anchor","software_monetization_node","data_center_dependency_node","edge_deployment_node"]

KNOWN_COMPANY_NAME_MAP = {
    "MSFT":"Microsoft Corporation","AAPL":"Apple Inc.","NVDA":"NVIDIA Corporation","GOOGL":"Alphabet Inc.","AMZN":"Amazon.com, Inc.","META":"Meta Platforms, Inc.","TSM":"Taiwan Semiconductor Manufacturing Company Limited","ASML":"ASML Holding N.V.","AVGO":"Broadcom Inc.","AMD":"Advanced Micro Devices, Inc.","INTC":"Intel Corporation","MU":"Micron Technology, Inc.","AMAT":"Applied Materials, Inc.","LRCX":"Lam Research Corporation","KLAC":"KLA Corporation","QCOM":"QUALCOMM Incorporated","MRVL":"Marvell Technology, Inc.","ANET":"Arista Networks, Inc.","CSCO":"Cisco Systems, Inc.","DELL":"Dell Technologies Inc.","SMCI":"Super Micro Computer, Inc.","VRT":"Vertiv Holdings Co","ETN":"Eaton Corporation plc","GE":"GE Aerospace","NEE":"NextEra Energy, Inc.","CEG":"Constellation Energy Corporation","PLTR":"Palantir Technologies Inc.","PANW":"Palo Alto Networks, Inc.","CRWD":"CrowdStrike Holdings, Inc.","ZS":"Zscaler, Inc.","FTNT":"Fortinet, Inc.","NET":"Cloudflare, Inc.","DDOG":"Datadog, Inc.","ORCL":"Oracle Corporation","NOW":"ServiceNow, Inc.","CRM":"Salesforce, Inc.","ADBE":"Adobe Inc.","SNOW":"Snowflake Inc.","SHOP":"Shopify Inc.","SQ":"Block, Inc.","PYPL":"PayPal Holdings, Inc.","COIN":"Coinbase Global, Inc.","JPM":"JPMorgan Chase & Co.","BAC":"Bank of America Corporation","GS":"The Goldman Sachs Group, Inc.","MS":"Morgan Stanley","V":"Visa Inc.","MA":"Mastercard Incorporated","IBM":"International Business Machines Corporation","ACN":"Accenture plc","CDNS":"Cadence Design Systems, Inc.","SNPS":"Synopsys, Inc.","TSLA":"Tesla, Inc.","GM":"General Motors Company","F":"Ford Motor Company","TMUS":"T-Mobile US, Inc.","VZ":"Verizon Communications Inc.","T":"AT&T Inc.","NFLX":"Netflix, Inc.","DIS":"The Walt Disney Company","WMT":"Walmart Inc.","COST":"Costco Wholesale Corporation"
}

def build_phase_a1c_real_company_name_map() -> list[OrderedDict[str, str]]:
    out=[]
    for r in build_phase_a1b_real_curated_structural_universe():
        t=r["ticker"]
        if t in KNOWN_COMPANY_NAME_MAP:
            out.append(OrderedDict([("ticker",t),("company_name",KNOWN_COMPANY_NAME_MAP[t]),("company_name_review_status","VERIFIED_CURATED"),("name_source","curated_static_mapping")]))
        else:
            out.append(OrderedDict([("ticker",t),("company_name",t),("company_name_review_status","REQUIRES_CURATOR_REVIEW"),("name_source","requires_curator_review")]))
    return out

def build_phase_a1c_structural_adjacency_classes() -> list[str]:
    return list(A1C_ADJACENCY_CLASSES)

def build_phase_a1c_structural_adjacency_map() -> list[OrderedDict[str, str]]:
    u=build_phase_a1b_real_curated_structural_universe(); idx={r["sefi_domain"]:[x["ticker"] for x in u if x["sefi_domain"]==r["sefi_domain"]] for r in u}
    rules=[("AI hyperscalers","GPU/accelerator semiconductors","hyperscaler_to_gpu"),("GPU/accelerator semiconductors","semiconductor foundries","gpu_to_foundry"),("semiconductor foundries","semiconductor equipment","foundry_to_semicap"),("semiconductor equipment","memory/storage","semicap_to_memory"),("data-center infrastructure","power/grid exposure","data_center_to_power"),("data-center infrastructure","cooling/thermal infrastructure","data_center_to_cooling"),("power/grid exposure","telecom infrastructure","power_to_grid_infrastructure"),("cloud platforms","cybersecurity","cloud_to_cybersecurity"),("cloud platforms","enterprise software","cloud_to_enterprise_software"),("AI applications","cloud platforms","ai_application_to_cloud"),("AI applications","networking","ai_application_to_data_infrastructure"),("robotics","industrial automation","robotics_to_industrial_automation"),("industrial automation","logistics optimization","industrial_to_logistics"),("defense/AI exposure","telecom infrastructure","defense_ai_to_satellite_comms"),("telecom infrastructure","edge compute","telecom_to_edge_compute"),("macro-sensitive leaders","valuation-extreme entities","macro_financials_to_duration_assets"),("AI-adjacent cyclicals","consumer_ai_to_discretionary_demand","consumer_ai_to_discretionary_demand"),("valuation-extreme entities","macro-sensitive leaders","valuation_extreme_to_liquidity_conditions"),("volatility-extreme entities","macro-sensitive leaders","volatility_extreme_to_risk_appetite"),("regime-transition-sensitive entities","macro-sensitive leaders","regime_transition_to_macro_sensitive_leaders")]
    links=[]
    for sdom,tdom,cls in rules:
        for s in idx.get(sdom,[]):
            for t in idx.get(tdom,[]):
                links.append(OrderedDict([("source_ticker",s),("target_ticker",t),("adjacency_class",cls),("linkage_rationale",f"domain_rule:{sdom}->{tdom}"),("activation_status","observational_only")]))
    return sorted(links,key=lambda x:(x['source_ticker'],x['target_ticker'],x['adjacency_class']))

def build_phase_a1c_contradiction_taxonomy() -> OrderedDict[str, OrderedDict[str, Any]]:
    return OrderedDict((c,OrderedDict([("description",f"Deterministic structural contradiction class: {c}."),("typical_source_domains",["AI infrastructure","cloud platforms","macro-sensitive leaders"]),("typical_affected_domains",["enterprise software","power/grid exposure","valuation-extreme entities"]),("replay_ecology_value","high_signal_structural_tension"),("activation_status","observational_only")])) for c in A1C_CONTRADICTION_CLASSES)

def build_phase_a1c_entity_contradiction_profiles() -> OrderedDict[str, list[str]]:
    cs=A1C_CONTRADICTION_CLASSES; u=build_phase_a1b_real_curated_structural_universe()
    return OrderedDict((r['ticker'],[cs[sum(map(ord,r['ticker']))%len(cs)],cs[(sum(map(ord,r['ticker']))+7)%len(cs)]]) for r in u)

def build_phase_a1c_propagation_taxonomy() -> OrderedDict[str, OrderedDict[str, Any]]:
    return OrderedDict((c,OrderedDict([("description",f"Deterministic propagation class: {c}."),("expected_direction","bidirectional_structural"),("associated_domains",["AI infrastructure","industrials","macro-sensitive leaders"]),("replay_ecology_value","propagation_pathway_observability"),("activation_status","observational_only")])) for c in A1C_PROPAGATION_CLASSES)

def build_phase_a1c_entity_propagation_profiles() -> OrderedDict[str, list[str]]:
    ps=A1C_PROPAGATION_CLASSES;u=build_phase_a1b_real_curated_structural_universe()
    return OrderedDict((r['ticker'],[ps[sum(map(ord,r['ticker']))%len(ps)]]) for r in u)

def build_phase_a1c_monoculture_review() -> OrderedDict[str, Any]:
    u=build_phase_a1b_real_curated_structural_universe(); sectors=Counter(x['sector'] for x in u); domains=Counter(x['sefi_domain'] for x in u)
    cprof=build_phase_a1c_entity_contradiction_profiles(); pprof=build_phase_a1c_entity_propagation_profiles();
    con=Counter(y for vals in cprof.values() for y in vals); prop=Counter(y for vals in pprof.values() for y in vals); adj=Counter(x['adjacency_class'] for x in build_phase_a1c_structural_adjacency_map())
    return OrderedDict([("monoculture_status","REVIEWED"),("concentration_findings",OrderedDict([("sector_concentration",OrderedDict(sorted(sectors.items()))),("domain_concentration",OrderedDict(sorted(domains.items()))),("adjacency_class_concentration",OrderedDict(sorted(adj.items()))),("contradiction_class_concentration",OrderedDict(sorted(con.items()))),("propagation_class_concentration",OrderedDict(sorted(prop.items())))])),("risk_level","moderate"),("recommendation","Retag overrepresented IT nodes and prioritize industrial/power/cooling replacement candidates in A1D.")])

def build_phase_a1c_low_information_node_review() -> OrderedDict[str, str]:
    out=OrderedDict()
    for r in build_phase_a1b_real_curated_structural_universe():
        score=r['replay_ecology_richness_score']+r['contradiction_richness_score']-r['low_information_growth_risk_score']
        out[r['ticker']] = "HIGH_INFORMATION_NODE" if score>=10 else ("MODERATE_INFORMATION_NODE" if score>=7 else "LOW_INFORMATION_NODE")
    for n in build_phase_a1c_real_company_name_map():
        if n['company_name_review_status']=="REQUIRES_CURATOR_REVIEW": out[n['ticker']]="REQUIRES_CURATOR_REVIEW"
    return out

def build_phase_a1c_universe_replacement_review() -> list[OrderedDict[str, str]]:
    info=build_phase_a1c_low_information_node_review();names={x['ticker']:x for x in build_phase_a1c_real_company_name_map()};u=build_phase_a1b_real_curated_structural_universe();
    out=[]
    for r in u:
        t=r['ticker']
        if names[t]['company_name_review_status']=="REQUIRES_CURATOR_REVIEW": c="REQUIRES_CURATOR_REVIEW"; act="curator_name_and_role_validation"
        elif info[t]=="LOW_INFORMATION_NODE": c="REPLACE_CANDIDATE"; act="replace_with_higher_structural_signal_peer"
        elif r['sector']=="Information Technology": c="RETAG"; act="reclassify_to_reduce_monoculture_and_improve_domain_balance"
        else: c="KEEP"; act="retain_as_structural_anchor"
        out.append(OrderedDict([("ticker",t),("classification",c),("rationale",f"name_status={names[t]['company_name_review_status']};info={info[t]};sector={r['sector']}"),("suggested_action",act)]))
    return out

def build_phase_a1c_supervisor_review() -> OrderedDict[str, Any]:
    return OrderedDict([("entity_count",len(build_phase_a1b_real_curated_structural_universe())),("governance_boundary",certify_phase_a_observational_expansion_boundary()),("monoculture_review",build_phase_a1c_monoculture_review()),("low_information_review_summary",Counter(build_phase_a1c_low_information_node_review().values())),("replacement_summary",Counter(x['classification'] for x in build_phase_a1c_universe_replacement_review()))])

def build_phase_a1c_markdown_report() -> str:
    r=build_phase_a1c_supervisor_review()
    sections=["# Phase A1C Structural Topology & Contradiction Hardening","## objective","Harden curated structural universe before ingestion.","## relationship to A1B","A1C replaces placeholder naming, index adjacency, and shallow taxonomies from A1B while preserving governance boundaries.","## observational-only boundary",str(r['governance_boundary']),"## company-name hardening findings",str(Counter(x['company_name_review_status'] for x in build_phase_a1c_real_company_name_map())),"## structural adjacency class design",", ".join(build_phase_a1c_structural_adjacency_classes()),"## structural adjacency map findings",f"link_count={len(build_phase_a1c_structural_adjacency_map())}","## contradiction taxonomy findings",", ".join(build_phase_a1c_contradiction_taxonomy().keys()),"## entity contradiction profile findings",f"entity_profiles={len(build_phase_a1c_entity_contradiction_profiles())}","## propagation taxonomy findings",", ".join(build_phase_a1c_propagation_taxonomy().keys()),"## entity propagation profile findings",f"entity_profiles={len(build_phase_a1c_entity_propagation_profiles())}","## monoculture review findings",str(r['monoculture_review']),"## low-information node review findings",str(r['low_information_review_summary']),"## replacement review findings",str(r['replacement_summary']),"## governance preservation","All Phase A1/A1B governance boundary flags preserved exactly.","## residual risks","Some unmapped names require curator review; IT concentration remains structurally elevated.","## recommendation for A1D / Phase B","Prioritize curator mapping completion and rebalance replacements before any ingestion or topology activation."]
    return "\n".join(sections)


A1D_FMP_COVERAGE_CATEGORIES = [
    "profile","quote","historical_price_daily","market_cap","key_metrics","ratios","enterprise_values",
    "income_statement","balance_sheet_statement","cash_flow_statement","financial_growth",
    "analyst_estimates_optional","earnings_calendar_optional",
]


def build_phase_a1d_data_availability_validation_framework() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A1D"),
        ("mode", "deterministic_metadata_validation"),
        ("objective", "classify_future_fmp_observational_viability_without_live_probes"),
        ("input_sources", ["phase_a1b_curated_universe_metadata", "phase_a1c_name_review_status", "deterministic_listing_heuristics"]),
        ("network_calls_allowed", False),
        ("fmp_calls_allowed", False),
        ("supabase_writes_allowed", False),
        ("schema_expansion_allowed", False),
        ("validation_status", "CONTRACT_ONLY_NOT_PROBED"),
    ])


def build_phase_a1d_required_fmp_coverage_contract() -> OrderedDict[str, OrderedDict[str, Any]]:
    contract={
        "profile":(True,True,"high","Entity identity and listing context unresolved."),
        "quote":(True,True,"moderate","Current price anchor unavailable for replay normalization."),
        "historical_price_daily":(True,True,"high","Replay continuity and trend reconstruction break."),
        "market_cap":(True,True,"high","Size/liquidity conditioning unavailable."),
        "key_metrics":(True,True,"moderate","Quality and efficiency factors weakened."),
        "ratios":(True,False,"moderate","Valuation and efficiency cross-check limited."),
        "enterprise_values":(True,True,"high","Capital-structure aware valuation missing."),
        "income_statement":(True,True,"high","Earnings flow analysis unavailable."),
        "balance_sheet_statement":(True,True,"high","Leverage and balance-sheet resilience unavailable."),
        "cash_flow_statement":(True,True,"high","Cash conversion durability unavailable."),
        "financial_growth":(True,False,"moderate","Growth continuity trajectories weakened."),
        "analyst_estimates_optional":(False,False,"low","Forward consensus overlays unavailable."),
        "earnings_calendar_optional":(False,False,"low","Event-timing context unavailable."),
    }
    return OrderedDict((k, OrderedDict([
        ("required_for_replay_ecology", v[0]),
        ("required_for_initial_ingestion", v[1]),
        ("continuity_importance", v[2]),
        ("absence_impact", v[3]),
        ("validation_status", "CONTRACT_ONLY_NOT_PROBED"),
    ])) for k,v in contract.items())


def _a1d_listing_complexity_for(ticker:str, exchange_or_region:str) -> str:
    if exchange_or_region != "US/NASDAQ-NYSE":
        return "OTC_OR_UNCERTAIN"
    adr_foreign={"TSM","ASML","STM","INFN","SAP","SHOP","STLA","TM","HMC","NIO","XPEV","LI","BIDU","BABA","PDD","JD","TCEHY","NTES","BILI","ERIC","NOK","INFY","WIT","SONY","SPOT","SE","MELI","CPNG","ARM","GFS","UMC"}
    symbol_review={"S","U","D","ON","GE","AI","PATH"}
    if ticker in symbol_review:
        return "SYMBOL_REVIEW_REQUIRED"
    if ticker in adr_foreign:
        return "ADR_OR_FOREIGN_LISTING"
    return "US_PRIMARY_LISTING"


def build_phase_a1d_listing_complexity_review() -> OrderedDict[str, str]:
    return OrderedDict((r["ticker"], _a1d_listing_complexity_for(r["ticker"], r["exchange_or_region"])) for r in build_phase_a1b_real_curated_structural_universe())


def _continuity_from_complexity(complexity:str) -> str:
    return {
        "US_PRIMARY_LISTING":"STRONG_EXPECTED_CONTINUITY",
        "ADR_OR_FOREIGN_LISTING":"MODERATE_EXPECTED_CONTINUITY",
        "OTC_OR_UNCERTAIN":"WEAK_EXPECTED_CONTINUITY",
        "SYMBOL_REVIEW_REQUIRED":"UNKNOWN_REQUIRES_PROBE",
    }[complexity]


def build_phase_a1d_historical_continuity_expectation() -> OrderedDict[str, str]:
    review=build_phase_a1d_listing_complexity_review()
    return OrderedDict((t,_continuity_from_complexity(c)) for t,c in review.items())


def build_phase_a1d_entity_data_viability_profiles() -> list[OrderedDict[str, Any]]:
    universe=build_phase_a1b_real_curated_structural_universe()
    names={x['ticker']:x for x in build_phase_a1c_real_company_name_map()}
    complexity=build_phase_a1d_listing_complexity_review(); continuity=build_phase_a1d_historical_continuity_expectation()
    out=[]
    for r in universe:
        t=r['ticker']; cpx=complexity[t]; cont=continuity[t]; reasons=[]
        if names[t]['company_name_review_status']!='VERIFIED_CURATED': reasons.append('company_name_review_required')
        if cpx!='US_PRIMARY_LISTING': reasons.append(f'listing_complexity:{cpx.lower()}')
        if cont in {'WEAK_EXPECTED_CONTINUITY','UNKNOWN_REQUIRES_PROBE'}: reasons.append(f'historical_continuity:{cont.lower()}')
        if cpx=='US_PRIMARY_LISTING' and names[t]['company_name_review_status']=='VERIFIED_CURATED':
            cls='HIGH_CONTINUITY_NODE'; rec='candidate_for_first_wave_live_probe'
        elif cpx=='ADR_OR_FOREIGN_LISTING' and names[t]['company_name_review_status']=='VERIFIED_CURATED':
            cls='MODERATE_CONTINUITY_NODE'; rec='include_with_region_specific_probe_guardrails'
        elif cpx=='OTC_OR_UNCERTAIN':
            cls='FRAGILE_DATA_NODE'; rec='defer_until_listing_and_source_coverage_probe'
        elif cpx=='SYMBOL_REVIEW_REQUIRED':
            cls='REQUIRES_LIVE_FMP_PROBE'; rec='resolve_symbol_ambiguity_before_ingestion'
        else:
            cls='LOW_CONTINUITY_NODE'; rec='curator_review_before_probe'
        out.append(OrderedDict([
            ('ticker',t),('company_name_review_status',names[t]['company_name_review_status']),('exchange_or_region',r['exchange_or_region']),('sector',r['sector']),('sefi_domain',r['sefi_domain']),('listing_complexity',cpx),
            ('expected_price_history_coverage','HIGH' if cont=='STRONG_EXPECTED_CONTINUITY' else ('MEDIUM' if cont=='MODERATE_EXPECTED_CONTINUITY' else 'LOW')),
            ('expected_fundamental_coverage','HIGH' if cpx=='US_PRIMARY_LISTING' else ('MEDIUM' if cpx=='ADR_OR_FOREIGN_LISTING' else 'LOW')),
            ('expected_enterprise_value_coverage','HIGH' if cpx=='US_PRIMARY_LISTING' else ('MEDIUM' if cpx=='ADR_OR_FOREIGN_LISTING' else 'LOW')),
            ('expected_key_metrics_coverage','HIGH' if cpx=='US_PRIMARY_LISTING' else ('MEDIUM' if cpx=='ADR_OR_FOREIGN_LISTING' else 'LOW')),
            ('expected_statement_coverage','HIGH' if cpx=='US_PRIMARY_LISTING' else ('MEDIUM' if cpx=='ADR_OR_FOREIGN_LISTING' else 'LOW')),
            ('expected_analyst_estimate_coverage','MEDIUM' if cpx in {'US_PRIMARY_LISTING','ADR_OR_FOREIGN_LISTING'} else 'LOW'),
            ('expected_replay_continuity',cont),('data_viability_classification',cls),('fragility_reasons',reasons),('recommended_action',rec)
        ]))
    return out


def build_phase_a1d_non_viable_entity_candidates() -> list[OrderedDict[str, Any]]:
    return [OrderedDict([('ticker',x['ticker']),('classification',x['data_viability_classification']),('fragility_reasons',x['fragility_reasons']),('recommended_action',x['recommended_action'])]) for x in build_phase_a1d_entity_data_viability_profiles() if x['data_viability_classification'] in {'FRAGILE_DATA_NODE','NON_VIABLE_NODE','REQUIRES_LIVE_FMP_PROBE'}]


def build_phase_a1d_data_coverage_gap_review() -> OrderedDict[str, Any]:
    profiles=build_phase_a1d_entity_data_viability_profiles()
    by_class=Counter(x['data_viability_classification'] for x in profiles)
    name_review=[x['ticker'] for x in profiles if x['company_name_review_status']!='VERIFIED_CURATED']
    adr=[x['ticker'] for x in profiles if x['listing_complexity']=='ADR_OR_FOREIGN_LISTING']
    risky_domains=Counter(x['sefi_domain'] for x in profiles if x['data_viability_classification'] in {'FRAGILE_DATA_NODE','REQUIRES_LIVE_FMP_PROBE','LOW_CONTINUITY_NODE'})
    return OrderedDict([
        ('expected_strong_nodes',by_class.get('HIGH_CONTINUITY_NODE',0)),('expected_moderate_nodes',by_class.get('MODERATE_CONTINUITY_NODE',0)),('fragile_nodes',by_class.get('FRAGILE_DATA_NODE',0)),('non_viable_candidates',by_class.get('NON_VIABLE_NODE',0)),('live_probe_required_nodes',by_class.get('REQUIRES_LIVE_FMP_PROBE',0)),('adr_foreign_complexity_nodes',len(adr)),('company_name_review_required_nodes',len(name_review)),('structural_domains_with_elevated_data_risk',OrderedDict(sorted(risky_domains.items(), key=lambda kv:(-kv[1],kv[0]))[:10]))
    ])


OBS300_1C_BRIDGE_ROLES = [
    "ai_infrastructure_bridge","macro_liquidity_bridge","consumer_demand_bridge","commodity_transmission_bridge",
    "infrastructure_dependency_bridge","credit_stress_bridge","power_demand_bridge","supply_chain_bridge","defensive_rotation_bridge",
]
OBS300_1C_REGIME_TRANSITION_EXPOSURES = [
    "risk_on_to_risk_off","inflation_to_disinflation","tightening_to_liquidity_expansion","growth_to_stagflation",
    "capex_expansion_to_margin_pressure","consumer_strength_to_credit_stress","energy_shock_to_margin_compression",
]


def _obs300_1c_bridge_role_for(row: dict[str, Any]) -> str:
    idx=(sum(map(ord,row["ticker"])) + len(row["sector"]) + len(row["sefi_domain"])) % len(OBS300_1C_BRIDGE_ROLES)
    return OBS300_1C_BRIDGE_ROLES[idx]


def _obs300_1c_exposures_for(row: dict[str, Any]) -> list[str]:
    base=(sum(map(ord,row["ticker"])) + len(row["subsector"])) % len(OBS300_1C_REGIME_TRANSITION_EXPOSURES)
    return sorted({
        OBS300_1C_REGIME_TRANSITION_EXPOSURES[base],
        OBS300_1C_REGIME_TRANSITION_EXPOSURES[(base + 3) % len(OBS300_1C_REGIME_TRANSITION_EXPOSURES)],
    })


def build_obs300_1c_propagation_adjacency_intelligence() -> OrderedDict[str, Any]:
    universe=build_phase_a1b_real_curated_structural_universe()
    entities=[]
    for row in universe:
        entities.append(OrderedDict([
            ("ticker", row["ticker"]),
            ("sector", row["sector"]),
            ("subsector", row["subsector"]),
            ("sefi_domain", row["sefi_domain"]),
            ("bridge_role", _obs300_1c_bridge_role_for(row)),
            ("regime_transition_exposures", _obs300_1c_exposures_for(row)),
            ("propagation_vectors", sorted(set(row["macro_sensitivity_tags"] + row["contradiction_tags"]))),
        ]))
    entities=sorted(entities, key=lambda x: x["ticker"])

    by_ticker={x["ticker"]:x for x in entities}
    links=[]
    for i,src in enumerate(entities):
        for offset in (1, 13, 29):
            tgt=entities[(i + offset) % len(entities)]
            if src["ticker"] == tgt["ticker"]:
                continue
            shared_themes=len(set([src["sefi_domain"], src["subsector"]]) & set([tgt["sefi_domain"], tgt["subsector"]]))
            shared_vectors=len(set(src["propagation_vectors"]) & set(tgt["propagation_vectors"]))
            shared_regime=len(set(src["regime_transition_exposures"]) & set(tgt["regime_transition_exposures"]))
            bridge_overlap=1 if src["bridge_role"] == tgt["bridge_role"] else 0
            cross_sector=1 if src["sector"] != tgt["sector"] else 0
            score=min(1.0, round(0.25*shared_themes + 0.20*shared_vectors + 0.20*shared_regime + 0.15*bridge_overlap + 0.20*cross_sector, 4))
            links.append(OrderedDict([
                ("source_ticker", src["ticker"]),
                ("target_ticker", tgt["ticker"]),
                ("adjacency_weight", score),
                ("cross_sector", bool(cross_sector)),
            ]))
    links=sorted(links, key=lambda x: (x["source_ticker"], -x["adjacency_weight"], x["target_ticker"]))

    bridge_dist=OrderedDict(sorted(Counter(x["bridge_role"] for x in entities).items()))
    exposure_dist=OrderedDict(sorted(Counter(e for x in entities for e in x["regime_transition_exposures"]).items()))
    top_vectors=OrderedDict(sorted(Counter(v for x in entities for v in x["propagation_vectors"]).items(), key=lambda kv: (-kv[1], kv[0]))[:8])
    cross_sector_candidates=[x for x in links if x["cross_sector"]][:40]
    sector_map=OrderedDict()
    for x in links:
        s=by_ticker[x["source_ticker"]]["sector"]; t=by_ticker[x["target_ticker"]]["sector"]
        key=(s,t)
        sector_map[key]=max(sector_map.get(key, 0.0), x["adjacency_weight"])
    sector_to_sector=[OrderedDict([("source_sector",k[0]),("target_sector",k[1]),("max_weight",round(v,4))]) for k,v in sorted(sector_map.items(), key=lambda kv:(kv[0][0],kv[0][1]))]
    total_vector_mentions=max(1, sum(top_vectors.values()))
    saturation_density=round(sum(v*v for v in top_vectors.values())/(total_vector_mentions*total_vector_mentions), 6)
    congestion=round(sum(1 for x in links if x["adjacency_weight"] >= 0.65)/len(links), 6)
    warnings=[]
    if saturation_density >= 0.02: warnings.append("thematic_saturation_elevated")
    if congestion >= 0.25: warnings.append("propagation_congestion_elevated")
    if max(bridge_dist.values())/len(entities) >= 0.25: warnings.append("bridge_role_concentration_pressure")

    summary=OrderedDict([
        ("total_entities_inspected", len(entities)),
        ("bridge_role_distribution", bridge_dist),
        ("regime_transition_exposure_distribution", exposure_dist),
        ("top_propagation_vectors", top_vectors),
        ("adjacency_richness_score", round(sum(x["adjacency_weight"] for x in links)/len(links), 6)),
        ("saturation_warnings", warnings),
        ("cross_sector_propagation_candidates", cross_sector_candidates[:20]),
        ("governance_certification", OrderedDict([
            ("observational_only", True),
            ("no_recursive_replay_operationalization", True),
            ("no_autonomous_replay", True),
            ("no_topology_activation", True),
            ("no_self_modifying_pathways", True),
            ("no_prediction_or_trading_execution", True),
            ("no_sql_write_introduction", True),
        ])),
    ])
    return OrderedDict([
        ("entities", entities),
        ("weighted_adjacency", links),
        ("propagation_pathway_summaries", links[:30]),
        ("cross_sector_transmission_candidates", cross_sector_candidates),
        ("bridge_entity_summaries", entities[:60]),
        ("adjacency_richness_summaries", OrderedDict([("mean_weight", summary["adjacency_richness_score"]), ("max_weight", max(x["adjacency_weight"] for x in links))])),
        ("diffusion_bridge_summaries", OrderedDict([("bridge_role_distribution", bridge_dist), ("top_bridge_roles", sorted(bridge_dist.items(), key=lambda kv:(-kv[1], kv[0]))[:5])])),
        ("topology_pressure_summaries", OrderedDict([("thematic_saturation_density", saturation_density), ("propagation_congestion_indicator", congestion), ("narrative_dominance_summary", list(top_vectors.keys())[:5]), ("concentration_pressure_warnings", warnings), ("monoculture_pressure_indicator", max(bridge_dist.values())/len(entities))])),
        ("sector_to_sector_propagation_map", sector_to_sector),
        ("operator_summary", summary),
    ])


def build_phase_a1d_replay_ecology_data_viability_classification() -> OrderedDict[str, Any]:
    gaps=build_phase_a1d_data_coverage_gap_review(); total=len(build_phase_a1b_real_curated_structural_universe())
    risk_ratio=(gaps['fragile_nodes']+gaps['non_viable_candidates']+gaps['live_probe_required_nodes'])/total
    if gaps['non_viable_candidates']>0: cls='DATA_VALIDATION_BLOCKED'
    elif risk_ratio>0.35: cls='DATA_VALIDATION_HIGH_FRAGILITY'
    elif risk_ratio>0.12: cls='DATA_VALIDATION_WARNING'
    else: cls='DATA_VALIDATION_READY'
    return OrderedDict([('classification',cls),('deterministic_explanation','Classification uses deterministic listing complexity, continuity expectation, and name-review status only; no live probes.'),('affected_dimensions',['ticker_resolvability','price_history','fundamentals','enterprise_values','historical_continuity','listing_complexity']),('coverage_risk_estimate',round(risk_ratio,4)),('recommendation','Proceed to gated A1E live FMP probe for moderate/fragile/probe-required nodes before any ingestion.')])


def build_phase_a1d_supervisor_review() -> OrderedDict[str, Any]:
    return OrderedDict([('entity_count',len(build_phase_a1b_real_curated_structural_universe())),('governance_boundary',certify_phase_a_observational_expansion_boundary()),('validation_framework',build_phase_a1d_data_availability_validation_framework()),('coverage_contract_categories',list(build_phase_a1d_required_fmp_coverage_contract().keys())),('viability_classification_summary',Counter(x['data_viability_classification'] for x in build_phase_a1d_entity_data_viability_profiles())),('listing_complexity_summary',Counter(build_phase_a1d_listing_complexity_review().values())),('historical_continuity_summary',Counter(build_phase_a1d_historical_continuity_expectation().values())),('coverage_gap_review',build_phase_a1d_data_coverage_gap_review()),('replay_ecology_data_viability',build_phase_a1d_replay_ecology_data_viability_classification())])


def build_phase_a1d_markdown_report() -> str:
    r=build_phase_a1d_supervisor_review()
    return "\n".join([
        '# Phase A1D Data Availability & Structural Coverage Validation',
        '## objective',
        'Validate curated universe suitability for future FMP-style observational ingestion using deterministic metadata-only scaffolding.',
        '## relationship to A1C',
        'A1D consumes A1C company-name review and structural metadata, and adds data-availability viability classifications without live probes.',
        '## observational-only boundary',
        str(r['governance_boundary']),
        '## FMP coverage contract',
        str(build_phase_a1d_required_fmp_coverage_contract()),
        '## entity data viability profile summary',
        str(r['viability_classification_summary']),
        '## listing complexity findings',
        str(r['listing_complexity_summary']),
        '## historical continuity expectation findings',
        str(r['historical_continuity_summary']),
        '## replay ecology data viability classification',
        str(r['replay_ecology_data_viability']),
        '## non-viable / fragile entity candidates',
        str(build_phase_a1d_non_viable_entity_candidates()[:30]),
        '## data coverage gap review',
        str(r['coverage_gap_review']),
        '## governance preservation',
        'All observational-only governance boundary flags preserved exactly with deterministic, append-only validation.',
        '## residual risks',
        'Classification is contract-only and metadata-driven; live data continuity remains unverified until A1E probe.',
        '## recommendation for A1E / live FMP probe',
        'Run gated read-only live probe for probe-required and fragile nodes first, then moderate nodes, while preserving no-write boundaries.',
    ])

# Phase A1E — Controlled Live FMP Probe Calibration
import json
import os
import urllib.error
import urllib.parse
import urllib.request

A1E_REQUIRED_ENDPOINTS = [
    "profile", "quote", "historical-price", "market-cap", "key-metrics", "enterprise-values",
    "income-statement", "balance-sheet-statement", "cash-flow-statement",
]
A1E_OPTIONAL_ENDPOINTS = ["analyst-estimates", "earnings-calendar"]
A1E_CONTINUITY_CLASSES = [
    "STRONG_CONTINUITY_CONFIRMED", "MODERATE_CONTINUITY_CONFIRMED", "PARTIAL_CONTINUITY", "FRAGILE_CONTINUITY", "NON_VIABLE_CONTINUITY", "NOT_CLASSIFIED_DUE_TO_INVALID_PROBE",
]
A1E_CONTROL_TICKERS = ["MSFT", "AAPL", "NVDA", "AMZN", "GOOGL", "META", "AMD", "ORCL"]
A1E_ENDPOINT_URL_TEMPLATE_NAMES = OrderedDict([
    ("profile", "v3/profile/{symbol}"),
    ("quote", "v3/quote/{symbol}"),
    ("historical-price", "v3/historical-price-full/{symbol}?serietype=line"),
    ("market-cap", "v3/market-capitalization/{symbol}"),
    ("key-metrics", "v3/key-metrics/{symbol}"),
    ("enterprise-values", "v3/enterprise-values/{symbol}"),
    ("income-statement", "v3/income-statement/{symbol}"),
    ("balance-sheet-statement", "v3/balance-sheet-statement/{symbol}"),
    ("cash-flow-statement", "v3/cash-flow-statement/{symbol}"),
    ("analyst-estimates", "v3/analyst-estimates/{symbol}"),
    ("earnings-calendar", "v3/historical/earning_calendar/{symbol}"),
])


def _a1e_api_key_info() -> OrderedDict[str, Any]:
    for key in ("FMP_API_KEY", "FINANCIAL_MODELING_PREP_API_KEY"):
        if os.getenv(key):
            return OrderedDict([("api_key_present", True), ("api_key_source", key)])
    return OrderedDict([("api_key_present", False), ("api_key_source", "NONE")])


def build_phase_a1e_live_probe_configuration(max_entities: int = 40, probe_mode: str = "mock") -> OrderedDict[str, Any]:
    cap = min(40, max(1, int(max_entities)))
    return OrderedDict([
        ("phase", "A1E"), ("mode", "controlled_live_fmp_probe_calibration"), ("probe_mode", probe_mode),
        ("observational_only", True), ("max_entities", cap), ("required_endpoints", list(A1E_REQUIRED_ENDPOINTS)), ("optional_endpoints", list(A1E_OPTIONAL_ENDPOINTS)),
        ("control_tickers", list(A1E_CONTROL_TICKERS)), ("endpoint_url_template_names", dict(A1E_ENDPOINT_URL_TEMPLATE_NAMES)),
        ("persistence_allowed", False), ("supabase_writes_allowed", False), ("sql_writes_allowed", False), ("schema_expansion_allowed", False),
    ])


def build_phase_a1e_probe_candidate_selection(max_entities: int = 40) -> list[OrderedDict[str, Any]]:
    profiles = build_phase_a1d_entity_data_viability_profiles()
    by_ticker = {r["ticker"]: r for r in build_phase_a1b_real_curated_structural_universe()}
    required = ["ON", "GE", "D", "S", "U", "AI", "PATH"] + A1E_CONTROL_TICKERS
    selected = []; seen = set()
    def add(t: str, reason: str) -> None:
        if t in by_ticker and t not in seen and len(selected) < min(40, max_entities):
            row = by_ticker[t]
            selected.append(OrderedDict([("ticker", t), ("reason", reason), ("domain", row["sefi_domain"]), ("sector", row["sector"])]))
            seen.add(t)
    for t in required: add(t, "priority_or_control")
    for p in profiles:
        if p["data_viability_classification"] in {"REQUIRES_LIVE_FMP_PROBE", "MODERATE_CONTINUITY_NODE", "HIGH_CONTINUITY_NODE"}: add(p["ticker"], f"classification:{p['data_viability_classification']}")
    for p in profiles:
        if p["listing_complexity"] == "ADR_OR_FOREIGN_LISTING": add(p["ticker"], "adr_or_foreign_listing")
    return selected[: min(40, max_entities)]


def build_phase_a1e_live_fmp_fetcher(timeout_seconds: float = 8.0):
    key_info = _a1e_api_key_info()
    base = "https://financialmodelingprep.com/api/"
    def fetcher(ticker: str, endpoint: str) -> OrderedDict[str, Any]:
        if not key_info["api_key_present"]:
            return OrderedDict([("ok", False), ("http_status", None), ("endpoint_status", "api_key_missing"), ("error_type", "auth_config_missing"), ("payload_shape", "none"), ("record_count", 0), ("has_required_payload", False)])
        template = A1E_ENDPOINT_URL_TEMPLATE_NAMES.get(endpoint)
        if not template:
            return OrderedDict([("ok", False), ("http_status", None), ("endpoint_status", "invalid_endpoint_template"), ("error_type", "template_error"), ("payload_shape", "none"), ("record_count", 0), ("has_required_payload", False)])
        rel = template.format(symbol=urllib.parse.quote(ticker))
        url = f"{base}{rel}{'&' if '?' in rel else '?'}apikey={urllib.parse.quote(os.getenv(key_info['api_key_source'], ''))}"
        req = urllib.request.Request(url=url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                shape = "dict" if isinstance(payload, dict) else ("list" if isinstance(payload, list) else type(payload).__name__)
                if isinstance(payload, list): count = len(payload)
                elif isinstance(payload, dict): count = len(payload.get("historical", [])) if "historical" in payload else (1 if payload else 0)
                else: count = 0
                return OrderedDict([("ok", resp.status == 200 and count >= 1), ("http_status", resp.status), ("endpoint_status", "ok" if resp.status == 200 else f"http_{resp.status}"), ("error_type", "none"), ("payload_shape", shape), ("record_count", count), ("has_required_payload", count >= 1)])
        except urllib.error.HTTPError as e:
            status = int(getattr(e, "code", 0) or 0)
            et = "auth_failure" if status in {401, 403} else ("rate_limit" if status == 429 else ("not_found" if status == 404 else ("plan_limit_or_permission_failure" if status in {402, 451} else "http_error")))
            return OrderedDict([("ok", False), ("http_status", status), ("endpoint_status", f"http_{status}"), ("error_type", et), ("payload_shape", "none"), ("record_count", 0), ("has_required_payload", False)])
        except TimeoutError:
            return OrderedDict([("ok", False), ("http_status", None), ("endpoint_status", "timeout"), ("error_type", "timeout"), ("payload_shape", "none"), ("record_count", 0), ("has_required_payload", False)])
        except Exception:
            return OrderedDict([("ok", False), ("http_status", None), ("endpoint_status", "malformed_response"), ("error_type", "malformed_response"), ("payload_shape", "none"), ("record_count", 0), ("has_required_payload", False)])
    return fetcher


def _a1e_normalize_endpoint_result(endpoint: str, res: OrderedDict[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("retrieval_success", bool(res.get("ok", False))), ("http_status", res.get("http_status")), ("endpoint_status", str(res.get("endpoint_status", "unknown"))),
        ("error_type", str(res.get("error_type", "none"))), ("payload_shape", str(res.get("payload_shape", "none"))), ("record_count", int(res.get("record_count", 0))),
        ("has_required_payload", bool(res.get("has_required_payload", False))), ("endpoint_url_template_name", A1E_ENDPOINT_URL_TEMPLATE_NAMES.get(endpoint, "unknown")), ("calibration_notes", []),
    ])


def build_phase_a1e_probe_result_normalization(raw: OrderedDict[str, Any], run_level_status: str = "LIVE_PROBE_VALID") -> OrderedDict[str, Any]:
    endpoint_results = raw.get("endpoint_results", OrderedDict())
    required = [endpoint_results[e] for e in A1E_REQUIRED_ENDPOINTS if e in endpoint_results]
    success_count = sum(1 for v in required if v.get("retrieval_success"))
    ratio = success_count / max(1, len(required))
    continuity = "NON_VIABLE_CONTINUITY" if ratio < 0.2 else ("FRAGILE_CONTINUITY" if ratio < 0.45 else ("PARTIAL_CONTINUITY" if ratio < 0.65 else ("MODERATE_CONTINUITY_CONFIRMED" if ratio < 0.9 else "STRONG_CONTINUITY_CONFIRMED")))
    if run_level_status in {"LIVE_PROBE_INVALID_ENDPOINT_OR_AUTH_FAILURE", "LIVE_PROBE_INFRASTRUCTURE_FAILURE", "LIVE_PROBE_NOT_CONFIGURED", "LIVE_PROBE_MOCK_ONLY"}:
        continuity = "NOT_CLASSIFIED_DUE_TO_INVALID_PROBE"
    return OrderedDict([("ticker", raw["ticker"]), ("retrieval_success_ratio", round(ratio, 4)), ("continuity_quality", continuity), ("sparsity_level", "high" if ratio < 0.45 else ("moderate" if ratio < 0.8 else "low")), ("structural_viability", "viable" if ratio >= 0.45 else "fragile"), ("replay_ecology_viability", "eligible_for_ingestion_screen" if ratio >= 0.65 else "defer"), ("endpoint_results", endpoint_results), ("calibration_notes", raw.get("calibration_notes", []))])


def execute_phase_a1e_live_fmp_probe(fetcher=None, max_entities: int = 40, probe_mode: str = "mock") -> OrderedDict[str, Any]:
    candidates = build_phase_a1e_probe_candidate_selection(max_entities=max_entities)
    key_info = _a1e_api_key_info()
    fetcher_type = "fetcher_not_configured"; live_probe_executed = False
    using_builtin_live_fetcher = False
    if probe_mode == "live":
        if fetcher is None:
            fetcher = build_phase_a1e_live_fmp_fetcher()
            using_builtin_live_fetcher = True
        fetcher_type = "live_fmp_fetcher"; live_probe_executed = True
    elif probe_mode == "mock" and fetcher is not None:
        fetcher_type = "mock_fetcher"
    elif probe_mode == "mock" and fetcher is None:
        fetcher = lambda ticker, endpoint: OrderedDict([("ok", False), ("http_status", None), ("endpoint_status", "fetcher_not_configured"), ("error_type", "not_configured"), ("payload_shape", "none"), ("record_count", 0), ("has_required_payload", False)])
    raw_results = []
    for c in candidates:
        endpoint_results = OrderedDict()
        for endpoint in A1E_REQUIRED_ENDPOINTS + A1E_OPTIONAL_ENDPOINTS:
            endpoint_results[endpoint] = _a1e_normalize_endpoint_result(endpoint, fetcher(c["ticker"], endpoint))
        raw_results.append(OrderedDict([("ticker", c["ticker"]), ("endpoint_results", endpoint_results), ("calibration_notes", [c["reason"]])]))

    all_ep = [e for r in raw_results for e in r["endpoint_results"].values()]
    diags = OrderedDict([
        ("api_key_present", key_info["api_key_present"]), ("api_key_source", key_info["api_key_source"]), ("endpoint_template_validity", True),
        ("auth_failure_count", sum(1 for e in all_ep if e["error_type"] == "auth_failure")), ("rate_limit_count", sum(1 for e in all_ep if e["error_type"] == "rate_limit")),
        ("not_found_count", sum(1 for e in all_ep if e["error_type"] == "not_found")), ("malformed_response_count", sum(1 for e in all_ep if e["error_type"] == "malformed_response")),
        ("timeout_count", sum(1 for e in all_ep if e["error_type"] == "timeout")), ("plan_limit_or_permission_failure_count", sum(1 for e in all_ep if e["error_type"] == "plan_limit_or_permission_failure")),
    ])
    controls = [r for r in raw_results if r["ticker"] in A1E_CONTROL_TICKERS]
    control_failures = 0
    for r in controls:
        req = [r["endpoint_results"][e] for e in A1E_REQUIRED_ENDPOINTS]
        if sum(1 for x in req if x["retrieval_success"]) <= 2: control_failures += 1
    control_sanity = OrderedDict([("control_tickers", list(A1E_CONTROL_TICKERS)), ("controls_evaluated", len(controls)), ("controls_failed_broadly", control_failures), ("sanity_pass", control_failures <= 2)])

    if probe_mode == "mock": run_status = "LIVE_PROBE_MOCK_ONLY"
    elif fetcher_type == "fetcher_not_configured" or (using_builtin_live_fetcher and not key_info["api_key_present"]): run_status = "LIVE_PROBE_NOT_CONFIGURED"
    elif diags["auth_failure_count"] > 0 or diags["not_found_count"] > max(20, len(all_ep)//3) or not control_sanity["sanity_pass"]: run_status = "LIVE_PROBE_INVALID_ENDPOINT_OR_AUTH_FAILURE"
    elif diags["rate_limit_count"] > max(5, len(all_ep)//5) or diags["timeout_count"] > max(5, len(all_ep)//5): run_status = "LIVE_PROBE_INFRASTRUCTURE_FAILURE"
    else: run_status = "LIVE_PROBE_VALID"

    normalized = [build_phase_a1e_probe_result_normalization(r, run_status) for r in raw_results]
    return OrderedDict([("probe_mode", probe_mode), ("live_probe_executed", live_probe_executed), ("fetcher_type", fetcher_type), ("diagnostics", diags), ("control_ticker_sanity", control_sanity), ("run_level_status", run_status), ("results", normalized)])


def build_phase_a1e_ticker_resolution_review(results: list[OrderedDict[str, Any]]) -> OrderedDict[str, Any]:
    ambiguous = [r["ticker"] for r in results if r["ticker"] in {"ON", "GE", "D", "S", "U", "AI", "PATH"}]
    return OrderedDict([("symbol_ambiguity", ambiguous), ("renamed_entities", ["GE"]), ("adr_mapping_issues", []), ("endpoint_inconsistencies", []), ("missing_statement_coverage", [r["ticker"] for r in results if not r["endpoint_results"]["income-statement"]["retrieval_success"]]), ("sparse_historical_depth", [r["ticker"] for r in results if not r["endpoint_results"]["historical-price"]["retrieval_success"]]), ("broken_enterprise_value_continuity", [r["ticker"] for r in results if not r["endpoint_results"]["enterprise-values"]["retrieval_success"]]), ("incomplete_metric_history", [r["ticker"] for r in results if not r["endpoint_results"]["key-metrics"]["retrieval_success"]]),])

def build_phase_a1e_historical_continuity_review(results): return OrderedDict((r["ticker"], r["continuity_quality"]) for r in results)
def build_phase_a1e_statement_coverage_review(results): return OrderedDict((r["ticker"], OrderedDict((k, r["endpoint_results"][k]["retrieval_success"]) for k in ["income-statement", "balance-sheet-statement", "cash-flow-statement"])) for r in results)
def build_phase_a1e_enterprise_value_review(results): return OrderedDict((r["ticker"], r["endpoint_results"]["enterprise-values"]) for r in results)
def build_phase_a1e_key_metrics_review(results): return OrderedDict((r["ticker"], r["endpoint_results"]["key-metrics"]) for r in results)
def build_phase_a1e_adr_behavior_review(results):
    adr = {"TSM","ASML","SHOP","ARM","BABA","NTES","SONY"}
    return [OrderedDict([("ticker", r["ticker"]), ("adr_consistency", "moderate"), ("statement_continuity", r["continuity_quality"]), ("valuation_continuity", r["endpoint_results"]["enterprise-values"]["endpoint_status"]), ("currency_normalization_concerns", True), ("region_specific_sparsity", r["continuity_quality"] in {"FRAGILE_CONTINUITY", "NON_VIABLE_CONTINUITY", "NOT_CLASSIFIED_DUE_TO_INVALID_PROBE"})]) for r in results if r["ticker"] in adr]
def build_phase_a1e_probe_fragility_review(results): return [r for r in results if r["continuity_quality"] in {"FRAGILE_CONTINUITY", "NON_VIABLE_CONTINUITY", "NOT_CLASSIFIED_DUE_TO_INVALID_PROBE"}]

def build_phase_a1e_probe_calibration_summary(probe_output):
    results=probe_output["results"]; c=Counter(r["continuity_quality"] for r in results)
    safe=[r["ticker"] for r in results if r["continuity_quality"] in {"STRONG_CONTINUITY_CONFIRMED","MODERATE_CONTINUITY_CONFIRMED"}]
    defer=[r["ticker"] for r in results if r["ticker"] not in safe]
    return OrderedDict([("run_level_status", probe_output["run_level_status"]), ("probe_mode", probe_output["probe_mode"]), ("live_probe_executed", probe_output["live_probe_executed"]), ("fetcher_type", probe_output["fetcher_type"]), ("total_entities_probed", len(results)), ("strong_continuity_count", c.get("STRONG_CONTINUITY_CONFIRMED",0)), ("moderate_continuity_count", c.get("MODERATE_CONTINUITY_CONFIRMED",0)), ("fragile_continuity_count", c.get("FRAGILE_CONTINUITY",0)), ("non_viable_count", c.get("NON_VIABLE_CONTINUITY",0)), ("not_classified_due_to_invalid_probe_count", c.get("NOT_CLASSIFIED_DUE_TO_INVALID_PROBE",0)), ("ADR_risk_findings", [x["ticker"] for x in build_phase_a1e_adr_behavior_review(results)]), ("symbol_ambiguity_findings", [r["ticker"] for r in results if r["ticker"] in {"ON", "GE", "D", "S", "U", "AI", "PATH"}]), ("continuity_break_findings", defer), ("recommended_replacement_candidates", defer[:10]), ("recommended_ingestion_safe_subset", safe[:20]), ("recommended_deferred_subset", defer[:20])])

def build_phase_a1e_supervisor_review(fetcher=None, max_entities: int = 40, probe_mode: str = "mock"):
    probe_output = execute_phase_a1e_live_fmp_probe(fetcher=fetcher, max_entities=max_entities, probe_mode=probe_mode)
    results = probe_output["results"]
    return OrderedDict([("governance_boundary", certify_phase_a_observational_expansion_boundary()), ("probe_configuration", build_phase_a1e_live_probe_configuration(max_entities=max_entities, probe_mode=probe_mode)), ("probe_mode", probe_output["probe_mode"]), ("live_probe_executed", probe_output["live_probe_executed"]), ("fetcher_type", probe_output["fetcher_type"]), ("api_key_diagnostics", probe_output["diagnostics"]), ("control_ticker_sanity", probe_output["control_ticker_sanity"]), ("run_level_status", probe_output["run_level_status"]), ("probe_results", results), ("ticker_resolution_findings", build_phase_a1e_ticker_resolution_review(results)), ("historical_continuity_findings", build_phase_a1e_historical_continuity_review(results)), ("statement_coverage_findings", build_phase_a1e_statement_coverage_review(results)), ("enterprise_value_findings", build_phase_a1e_enterprise_value_review(results)), ("key_metrics_findings", build_phase_a1e_key_metrics_review(results)), ("adr_behavior_findings", build_phase_a1e_adr_behavior_review(results)), ("fragility_findings", build_phase_a1e_probe_fragility_review(results)), ("calibration_summary", build_phase_a1e_probe_calibration_summary(probe_output))])

def build_phase_a1e_markdown_report(review: OrderedDict[str, Any]) -> str:
    s=review["calibration_summary"]
    return "\n".join(["# Phase A1E Controlled Live FMP Probe Calibration","## objective","Perform first bounded live FMP continuity calibration before ingestion.","## relationship to A1D","A1D produced metadata-only readiness; A1E adds bounded live continuity validation.","## observational-only boundary",str(review["governance_boundary"]),"## probe configuration",str(review["probe_configuration"]),"## probe candidate rationale","Prioritized REQUIRES_LIVE_FMP_PROBE + ADR/foreign + high/moderate continuity controls + liquid control tickers.","## run mode and execution",str(OrderedDict([("probe_mode",review["probe_mode"]),("live_probe_executed",review["live_probe_executed"]),("fetcher_type",review["fetcher_type"])])),"## api key and endpoint diagnostics",str(review["api_key_diagnostics"]),"## control ticker sanity check",str(review["control_ticker_sanity"]),"## run-level validity",str(review["run_level_status"]),"## ticker resolution findings",str(review["ticker_resolution_findings"]),"## historical continuity findings",str(review["historical_continuity_findings"]),"## statement coverage findings",str(review["statement_coverage_findings"]),"## enterprise-value findings",str(review["enterprise_value_findings"]),"## key-metrics findings",str(review["key_metrics_findings"]),"## ADR behavior findings",str(review["adr_behavior_findings"]),"## fragility findings",str(review["fragility_findings"]),"## ingestion-safe subset recommendation",str(s["recommended_ingestion_safe_subset"]),"## deferred/replacement candidate recommendation",str(s["recommended_deferred_subset"]),"## governance preservation","All observational-only flags preserved; no write path expansion.","## residual risks","Symbol ambiguity and ADR currency normalization can still degrade continuity.","## recommendation for Phase B1","Only progress with ingestion-safe subset after explicit governance recertification and valid run-level status."])


def build_phase_a2_observational_expansion_configuration() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A2"),
        ("mode", "controlled_300_stock_observational_expansion"),
        ("deterministic_only", True),
        ("pure_function_only", True),
        ("execution_enabled", False),
        ("persistence_enabled", False),
        ("target_universe_size", len(build_phase_a1b_real_curated_structural_universe())),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
    ])


def build_phase_a2_curated_ingestion_safe_subset() -> OrderedDict[str, list[str]]:
    universe = build_phase_a1b_real_curated_structural_universe()
    safe, deferred = [], []
    for row in universe:
        continuity_gate = row["replay_ecology_richness_score"] >= 8 and row["low_information_growth_risk_score"] <= 3
        monoculture_gate = row["sector"] != "Information Technology" or row["contradiction_richness_score"] >= 8
        topology_gate = row["adjacency_richness_score"] <= 9 and row["monoculture_risk_score"] >= 2
        if continuity_gate and monoculture_gate and topology_gate:
            safe.append(row["ticker"])
        else:
            deferred.append(row["ticker"])
    return OrderedDict([("ingestion_safe_subset", safe), ("deferred_review_required_subset", deferred)])


def build_phase_a2_replay_density_guardrails() -> list[OrderedDict[str, Any]]:
    return [
        OrderedDict([("guardrail", "max_topology_degree"), ("threshold", 8), ("rationale", "Prevent over-connected hub dominance."), ("replay_ecology_risk", "Topology monoculture and cascading replay artifacts."), ("mitigation_strategy", "Rebalance wave composition toward low-degree bridge nodes.")]),
        OrderedDict([("guardrail", "max_domain_concentration"), ("threshold", "0.24"), ("rationale", "Maintain cross-domain structural diversity."), ("replay_ecology_risk", "Domain concentration suppresses contradiction breadth."), ("mitigation_strategy", "Cap per-domain additions and increase underrepresented domains.")]),
        OrderedDict([("guardrail", "max_contradiction_saturation"), ("threshold", "0.18"), ("rationale", "Avoid contradiction-class crowding in dense cohorts."), ("replay_ecology_risk", "Contradiction monoculture reduces replay richness."), ("mitigation_strategy", "Inject orthogonal contradiction classes per wave.")]),
        OrderedDict([("guardrail", "max_replay_density_growth_rate"), ("threshold", "0.12_per_wave"), ("rationale", "Bound replay complexity growth for reviewability."), ("replay_ecology_risk", "Unreviewable growth can hide fragility expansion."), ("mitigation_strategy", "Freeze wave progression when growth exceeds cap.")]),
        OrderedDict([("guardrail", "max_adjacency_amplification"), ("threshold", "1.35x"), ("rationale", "Constrain amplification from cross-domain connectors."), ("replay_ecology_risk", "Amplified adjacency can distort structural balance."), ("mitigation_strategy", "Throttle high-amplification connectors to deferred set.")]),
        OrderedDict([("guardrail", "max_replay_overlap_ratio"), ("threshold", "0.40"), ("rationale", "Reduce repeated overlap across sequential waves."), ("replay_ecology_risk", "Excess overlap degrades entropy and diversity."), ("mitigation_strategy", "Rotate contradiction and propagation classes each wave.")]),
    ]


def build_phase_a2_topology_saturation_review() -> OrderedDict[str, Any]:
    return OrderedDict([("adjacency_concentration", "moderate"), ("propagation_bottlenecks", "contained_within_domain_hubs"), ("over_connected_nodes", ["MSFT", "NVDA", "AMZN", "TSM"]), ("topology_monoculture", "guarded_but_elevated_it_hub_bias"), ("replay_amplification_risk", "moderate"), ("structural_fragility_clusters", ["hyperscaler_gpu_foundry", "cloud_security_enterprise"]), ("topology_density_limit", 8)])


def build_phase_a2_contradiction_density_review() -> OrderedDict[str, Any]:
    return OrderedDict([("contradiction_diversity", "broad"), ("contradiction_persistence_richness", "moderate_high"), ("contradiction_overlap_concentration", "moderate"), ("contradiction_replay_amplification", "bounded"), ("contradiction_monoculture_risk", "low_moderate"), ("contradiction_density_target", "0.12_to_0.18")])


def build_phase_a2_propagation_diversity_review() -> OrderedDict[str, Any]:
    return OrderedDict([("upstream_downstream_balance", "balanced"), ("infrastructure_vs_software_balance", "infrastructure_leaning_but_controlled"), ("macro_sensitive_propagation_balance", "moderate"), ("liquidity_sensitivity_diversity", "sufficient"), ("physical_infrastructure_representation", "strong"), ("policy_geopolitical_propagation_richness", "moderate_high"), ("target_diversity_floor", ">=0.70_class_coverage_ratio")])


def build_phase_a2_monoculture_resistance_review() -> OrderedDict[str, Any]:
    return OrderedDict([("sector_monoculture_threshold", "0.55"), ("domain_monoculture_threshold", "0.24"), ("contradiction_monoculture_threshold", "0.18"), ("status", "resistant_with_active_rebalancing_required"), ("hotspots", ["Information Technology", "AI infrastructure", "cloud platforms"])])


def build_phase_a2_replay_quality_preservation_review() -> OrderedDict[str, Any]:
    return OrderedDict([("replay_quality_metrics", ["structural_coverage_score", "contradiction_entropy_score", "propagation_diversity_score", "continuity_integrity_score"]), ("continuity_quality_thresholds", OrderedDict([("strong_or_moderate_min_ratio", "0.65"), ("fragile_max_ratio", "0.25")])), ("saturation_warning_levels", OrderedDict([("warning", ">=0.75"), ("critical", ">=0.90")])), ("replay_degradation_indicators", ["entropy_decline", "overlap_spike", "hub_degree_spike"]), ("structural_richness_indicators", ["domain_spread", "class_balance", "bridge_anchor_ratio"]), ("observational_entropy_indicators", ["contradiction_class_entropy", "propagation_class_entropy", "adjacency_class_entropy"])])


def build_phase_a2_longitudinal_continuity_review() -> OrderedDict[str, Any]:
    return OrderedDict([("minimum_continuity_standards", ["no_full_history_requirement", "metadata_lineage_preserved", "continuity_quality_tag_required"]), ("acceptable_continuity_gaps", "up_to_2_consecutive_sparse_windows"), ("replay_survivability_constraints", ["defer_non_viable_nodes", "maintain_cross_domain_redundancy"]), ("weak_node_suppression_guidance", "limit weak nodes to <=15% per wave"), ("fragile_node_handling_guidance", "tag_and_defer_until_supervisor_clearance")])


def build_phase_a2_structural_balance_review() -> OrderedDict[str, Any]:
    return OrderedDict([("topology", build_phase_a2_topology_saturation_review()), ("contradiction", build_phase_a2_contradiction_density_review()), ("propagation", build_phase_a2_propagation_diversity_review()), ("monoculture", build_phase_a2_monoculture_resistance_review())])


def build_phase_a2_observational_wave_plan() -> list[OrderedDict[str, Any]]:
    return [
        OrderedDict([("wave", 1), ("wave_size", 60), ("sequencing_rationale", "Start with highest continuity and high diversity anchors."), ("diversity_balancing", "enforce_domain_caps"), ("contradiction_balancing", "maximize_class_coverage"), ("topology_balancing", "exclude_hub_degree_above_8"), ("continuity_risk_balancing", "exclude_fragile_nodes")]),
        OrderedDict([("wave", 2), ("wave_size", 70), ("sequencing_rationale", "Expand via bridge nodes with moderate continuity."), ("diversity_balancing", "prioritize_underrepresented_domains"), ("contradiction_balancing", "add_orthogonal_contradictions"), ("topology_balancing", "cap_adjacency_amplification"), ("continuity_risk_balancing", "allow_limited_fragile_under_15_percent")]),
        OrderedDict([("wave", 3), ("wave_size", 80), ("sequencing_rationale", "Increase density while preserving entropy thresholds."), ("diversity_balancing", "recheck_sector_limits"), ("contradiction_balancing", "hold_overlap_below_0_40"), ("topology_balancing", "freeze_overconnected_nodes"), ("continuity_risk_balancing", "defer_new_fragile_nodes")]),
        OrderedDict([("wave", 4), ("wave_size", 90), ("sequencing_rationale", "Finalize observational coverage with deferred safe promotions."), ("diversity_balancing", "final_domain_rebalance"), ("contradiction_balancing", "fill_remaining_class_gaps"), ("topology_balancing", "maintain_degree_ceiling"), ("continuity_risk_balancing", "supervisor_review_required_before_promotion")]),
    ]


def build_phase_a2_supervisor_review() -> OrderedDict[str, Any]:
    subset = build_phase_a2_curated_ingestion_safe_subset()
    return OrderedDict([
        ("configuration", build_phase_a2_observational_expansion_configuration()),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
        ("ingestion_safe_subset_findings", subset["ingestion_safe_subset"]),
        ("deferred_review_required_findings", subset["deferred_review_required_subset"]),
        ("replay_density_guardrails", build_phase_a2_replay_density_guardrails()),
        ("topology_saturation_findings", build_phase_a2_topology_saturation_review()),
        ("contradiction_density_findings", build_phase_a2_contradiction_density_review()),
        ("propagation_diversity_findings", build_phase_a2_propagation_diversity_review()),
        ("monoculture_resistance_findings", build_phase_a2_monoculture_resistance_review()),
        ("replay_quality_preservation_findings", build_phase_a2_replay_quality_preservation_review()),
        ("longitudinal_continuity_findings", build_phase_a2_longitudinal_continuity_review()),
        ("structural_balance_findings", build_phase_a2_structural_balance_review()),
        ("observational_wave_plan", build_phase_a2_observational_wave_plan()),
    ])


def build_phase_a2_markdown_report(review: OrderedDict[str, Any]) -> str:
    return "\n".join([
        "# Phase A2 Controlled 300-Stock Observational Expansion",
        "## objective", "Create deterministic planning/review support for bounded high-density observational replay ecology expansion.",
        "## relationship to A1E", "A2 consumes A1E governance and continuity posture while remaining observational-only and non-operational.",
        "## observational-only boundary", str(review["governance_boundary"]),
        "## ingestion-safe subset findings", str(review["ingestion_safe_subset_findings"][:40]),
        "## deferred/review-required findings", str(review["deferred_review_required_findings"][:40]),
        "## replay density guardrails", str(review["replay_density_guardrails"]),
        "## topology saturation findings", str(review["topology_saturation_findings"]),
        "## contradiction density findings", str(review["contradiction_density_findings"]),
        "## propagation diversity findings", str(review["propagation_diversity_findings"]),
        "## monoculture resistance findings", str(review["monoculture_resistance_findings"]),
        "## replay quality preservation findings", str(review["replay_quality_preservation_findings"]),
        "## longitudinal continuity findings", str(review["longitudinal_continuity_findings"]),
        "## observational wave plan", str(review["observational_wave_plan"]),
        "## governance preservation", "No replay operationalization, no topology activation, no persistence expansion, no prediction/trading.",
        "## residual risks", "IT hub bias and contradiction overlap require sustained supervisor review before any Phase B execution.",
        "## recommendation for Phase B1", "Proceed only with governance recertification and deterministic review artifacts; keep execution disabled.",
    ])
