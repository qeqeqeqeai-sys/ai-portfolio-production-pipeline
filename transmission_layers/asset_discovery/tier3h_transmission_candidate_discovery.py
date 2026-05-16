from __future__ import annotations
import json, os, re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import requests

ALLOWED_ACTIONS={"watch","review","candidate_add","reject"}
ALLOWED_IDENTIFIER_TYPES={"TICKER","ETF","NODE","THEME","REGIME","UNKNOWN"}
ALLOWED_ENTITY_LINK_METHODS={"curated_static_map","direct_ticker","node_alias","unresolved"}
TABLE_NAME="tier3h_transmission_candidates"
LOG_DIR=Path("logs"); SUMMARY_PATH=LOG_DIR/"tier3h_candidate_discovery_summary.json"; VALIDATION_PATH=LOG_DIR/"tier3h_candidate_discovery_validation.json"; MANIFEST_PATH=LOG_DIR/"tier3h_candidate_discovery_manifest.json"
LOCAL_SOURCE_FILES=[Path("logs/transmission_candidate_inputs.json")]
SUPABASE_SOURCES=[{"name":"phase4a_single_hop_propagation","table":"structural_theme_graph_single_hop_propagation","order":"run_date_sgt.desc","limit":500}]
CURATED_MAP={"ai":["TICKER::NVDA","TICKER::AVGO","TICKER::TSM","TICKER::ASML","TICKER::AMD","TICKER::MSFT","TICKER::GOOGL","TICKER::AMZN","TICKER::META","ETF::SMH"],"semiconductor":["TICKER::NVDA","TICKER::AMD","TICKER::AVGO","TICKER::TSM","TICKER::ASML","TICKER::AMAT","TICKER::LRCX","TICKER::KLAC","ETF::SMH"],"data_center":["TICKER::MSFT","TICKER::AMZN","TICKER::GOOGL","TICKER::META","TICKER::ORCL","TICKER::SMCI","TICKER::DELL","TICKER::VRT","THEME::AI_POWER_DEMAND"],"power":["TICKER::CEG","TICKER::VST","TICKER::NEE","TICKER::ETN","TICKER::PWR","ETF::GRID"]}
KEYWORDS={"ai":{"ai","artificial_intelligence"},"semiconductor":{"semiconductor","gpu","chip","accelerator"},"data_center":{"data_center","cloud","infrastructure"},"power":{"power","electricity","grid","energy"}}

def utc_now()->datetime:return datetime.now(timezone.utc)
def run_date_sgt(today_utc:datetime|None=None)->str:return ((today_utc or utc_now())+timedelta(hours=8)).date().isoformat()
def _safe_float(v:Any,d:float=0.0)->float:
    try:return float(v)
    except (TypeError,ValueError):return d
def _safe_int(v:Any,d:int=0)->int:
    try:return int(float(v))
    except (TypeError,ValueError):return d

def _normalize_token(v:str)->str:return re.sub(r"[^A-Z0-9]+","_",v.upper()).strip("_")

def _supabase_get_rows(table:str,order:str,limit:int)->list[dict[str,Any]]:
    url=(os.getenv("SUPABASE_URL") or "").rstrip("/"); key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:return []
    try:
        r=requests.get(f"{url}/rest/v1/{table}",headers={"apikey":key,"Authorization":f"Bearer {key}"},params={"select":"*","order":order,"limit":str(limit)},timeout=60)
        p=r.json() if r.status_code<400 else []
        return [x for x in p if isinstance(x,dict)] if isinstance(p,list) else []
    except Exception:return []

def load_upstream_rows():
    rows=[]; used=[]; counts={}; cols={}
    for src in SUPABASE_SOURCES:
        loaded=_supabase_get_rows(src["table"],src["order"],src["limit"]); lab=f"supabase:{src['table']}"; counts[lab]=len(loaded); cols[lab]=sorted({k for r in loaded for k in r.keys()})
        if loaded: rows.extend(loaded); used.append(lab)
    return rows,used,counts,cols,not bool(rows)

def link_structural_entities(row:dict[str,Any])->list[dict[str,Any]]:
    text=" ".join(str(row.get(k) or "").lower() for k in ["theme_name","anchor_theme_name","source_node_key","target_node_key","source_node_type","target_node_type","propagation_metadata"])
    out=[]
    for bucket,kws in KEYWORDS.items():
        if any(k in text for k in kws):
            for sym in CURATED_MAP[bucket]:
                out.append({"candidate_symbol":sym,"identifier_type":sym.split("::",1)[0],"entity_link_method":"curated_static_map","entity_link_confidence":0.45,"linked_from_theme":str(row.get("theme_name") or row.get("anchor_theme_name") or ""),"linked_from_node":str(row.get("source_node_key") or row.get("target_node_key") or ""),"resolution_reason":f"Linked via {bucket} curated static map."})
    uniq={x["candidate_symbol"]:x for x in out}
    return list(uniq.values())

def discover_candidates(rows:list[dict[str,Any]],sgt_date:str)->list[dict[str,Any]]:
    expanded=[]
    for row in rows:
        links=link_structural_entities(row)
        if links:
            for link in links: expanded.append({**row,**link,"candidate_source":"tier3h_structural_entity_linking"})
        else:
            expanded.append({**row,"candidate_symbol":f"THEME::{_normalize_token(str(row.get('theme_name') or row.get('anchor_theme_name') or 'UNKNOWN'))}","identifier_type":"THEME","entity_link_method":"unresolved","entity_link_confidence":0.0,"linked_from_theme":str(row.get("theme_name") or row.get("anchor_theme_name") or ""),"linked_from_node":str(row.get("source_node_key") or row.get("target_node_key") or ""),"resolution_reason":"Unresolved structural link fallback.","candidate_source":str(row.get("candidate_source") or "upstream_transmission")})
    grouped={}
    for r in expanded:
        key=(sgt_date,r["candidate_symbol"],str(r.get("linked_from_theme") or "unknown_theme"),str(r.get("candidate_source")))
        g=grouped.setdefault(key,{"run_date_sgt":sgt_date,"candidate_symbol":r["candidate_symbol"],"candidate_name":r["candidate_symbol"].split("::",1)[-1],"asset_class":"equity","discovery_theme":key[2],"candidate_source":key[3],"positive_transmission_score":0.0,"negative_transmission_score":0.0,"evidence_count":0,"memory_score":0.0,"cross_theme_strength":0.0,"multi_hop_strength":0.0,"snapshot_id":str(r.get("snapshot_id") or "tier3h-upstream"),"missing_symbol":not r["candidate_symbol"].startswith(("TICKER::","ETF::")),"identifier_type":r.get("identifier_type","UNKNOWN"),"resolution_reason":r.get("resolution_reason",""),"linked_from_theme":r.get("linked_from_theme",""),"linked_from_node":r.get("linked_from_node",""),"entity_link_confidence":_safe_float(r.get("entity_link_confidence")),"entity_link_method":r.get("entity_link_method","unresolved")})
        g["positive_transmission_score"]+=_safe_float(r.get("propagated_positive_pressure") or r.get("positive_transmission_score") or 0)
        g["negative_transmission_score"]+=_safe_float(r.get("propagated_negative_pressure") or r.get("negative_transmission_score") or 0)
        g["memory_score"]+=_safe_float(r.get("edge_strength") or r.get("memory_score") or 0)
        g["cross_theme_strength"]+=_safe_float(r.get("edge_strength") or 0)
        g["multi_hop_strength"]+=_safe_float(r.get("propagated_pressure_score") or 0)
        g["evidence_count"]+=max(1,_safe_int(r.get("evidence_count") or 1,1))
    out=[]
    penalties={"TICKER":0.0,"ETF":0.02,"NODE":0.08,"THEME":0.12,"REGIME":0.25,"UNKNOWN":0.3}
    for g in grouped.values():
        net=g["positive_transmission_score"]-g["negative_transmission_score"]
        conf=max(0.0,(0.55*min((abs(net)+g["cross_theme_strength"]+g["multi_hop_strength"])/10,1.0))+(0.30*min((g["memory_score"]+g["evidence_count"])/12,1.0))+(0.15*min(g["entity_link_confidence"],0.5))-penalties.get(g["identifier_type"],0.3))
        g["confidence_score"]=round(conf,4); g["net_transmission_score"]=round(net,4)
        if g["identifier_type"] in {"REGIME","UNKNOWN"}: action="watch" if conf>=0.3 else "reject"
        elif g["identifier_type"] in {"TICKER","ETF"} and conf>=0.7 and g["evidence_count"]>=3 and abs(net)>=1.8: action="candidate_add"
        elif conf>=0.5: action="review"
        elif conf>=0.28: action="watch"
        else: action="reject"
        g["recommended_action"]=action; g["status"]="advisory_only"; g["discovery_reason"]=f"identifier_type={g['identifier_type']}; method={g['entity_link_method']}; evidence={g['evidence_count']}"
        for k in ["positive_transmission_score","negative_transmission_score","memory_score","cross_theme_strength","multi_hop_strength"]: g[k]=round(g[k],4)
        out.append(g)
    return sorted(out,key=lambda x:(-x["confidence_score"],-abs(x["net_transmission_score"]),x["candidate_symbol"]))

def upsert_supabase(rows:list[dict[str,Any]])->str:
    if not rows:return "skipped: no candidate rows"
    return "skipped: missing supabase env"

def main()->int:
    LOG_DIR.mkdir(parents=True,exist_ok=True); sgt_date=run_date_sgt(); upstream_rows,used,counts,cols,soft=load_upstream_rows(); candidates=discover_candidates(upstream_rows,sgt_date) if upstream_rows else []
    summary={"module":"tier3h_transmission_candidate_discovery","run_timestamp_utc":utc_now().isoformat(),"run_date_sgt":sgt_date,"upstream_sources_used":used,"upstream_row_count":len(upstream_rows),"upstream_row_counts_by_source":counts,"source_columns_seen":cols,"candidate_count":len(candidates),"entity_linking_enabled":True,"entity_link_method_counts":dict(Counter(c.get("entity_link_method","unresolved") for c in candidates)),"linked_candidate_count":sum(1 for c in candidates if c.get("entity_link_method")!="unresolved"),"linked_ticker_count":sum(1 for c in candidates if c.get("identifier_type")=="TICKER"),"linked_etf_count":sum(1 for c in candidates if c.get("identifier_type")=="ETF"),"linked_from_theme_counts":dict(Counter(c.get("linked_from_theme") for c in candidates if c.get("linked_from_theme"))),"linked_from_node_counts":dict(Counter(c.get("linked_from_node") for c in candidates if c.get("linked_from_node"))),"unresolved_entity_count":sum(1 for c in candidates if c.get("entity_link_method")=="unresolved"),"top_linked_candidates_preview":candidates[:10],"advisory_only":True,"soft_failure":soft}
    validation={"all_linked_candidates_advisory_only":all(c["status"]=="advisory_only" for c in candidates),"no_main_universe_writes_attempted":True,"entity_link_method_allowed":all(c.get("entity_link_method") in ALLOWED_ENTITY_LINK_METHODS for c in candidates),"identifier_type_allowed":all(c.get("identifier_type") in ALLOWED_IDENTIFIER_TYPES for c in candidates),"candidate_add_not_regime_unknown":all(not (c["recommended_action"]=="candidate_add" and c["identifier_type"] in {"REGIME","UNKNOWN"}) for c in candidates),"upsert_payload_columns":sorted({k for c in candidates for k in c}) if candidates else [],"linked_candidates_have_theme_or_node":all((c.get("entity_link_method")=="unresolved") or bool(c.get("linked_from_theme") or c.get("linked_from_node")) for c in candidates)}
    SUMMARY_PATH.write_text(json.dumps(summary,indent=2),encoding="utf-8"); VALIDATION_PATH.write_text(json.dumps(validation,indent=2),encoding="utf-8"); MANIFEST_PATH.write_text(json.dumps({"summary":str(SUMMARY_PATH),"validation":str(VALIDATION_PATH),"candidates_preview":candidates[:25]},indent=2),encoding="utf-8")
    return 0

if __name__=="__main__": raise SystemExit(main())
