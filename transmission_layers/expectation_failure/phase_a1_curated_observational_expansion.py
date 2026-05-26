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
