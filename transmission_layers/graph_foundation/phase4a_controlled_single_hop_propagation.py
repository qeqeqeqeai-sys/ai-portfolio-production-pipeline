import os, time, math, re
from collections import defaultdict
from datetime import datetime, timezone
from graph_supabase_client import SupabaseRestClient

PIPELINE_NAME="PHASE_4A_CONTROLLED_SINGLE_HOP_PROPAGATION"
SNAPSHOT_VERSION="phase4a_v1"
ANCHOR_THEME_NAME=os.getenv("ANCHOR_THEME_NAME","ai").strip().lower()
THEME_NAME=os.getenv("THEME_NAME","").strip().lower()
MAX_ROWS=int(os.getenv("MAX_ROWS","20000"))
MIN_EDGE_STRENGTH=float(os.getenv("MIN_EDGE_STRENGTH","0.0"))
MIN_TRANSMISSION_POTENTIAL=float(os.getenv("MIN_TRANSMISSION_POTENTIAL","0.0"))
MAX_TRANSFER_WEIGHT=float(os.getenv("MAX_TRANSFER_WEIGHT","0.85"))

def now_iso(): return datetime.now(timezone.utc).isoformat()
def run_date(): return datetime.utcnow().strftime("%Y-%m-%d")
def snap_id(): return f"{SNAPSHOT_VERSION}_{ANCHOR_THEME_NAME}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
def flt(v,d=0.0):
    try:
        x=float(v)
        return d if math.isnan(x) or math.isinf(x) else x
    except Exception:
        return d
def c01(v): return max(0.0,min(1.0,flt(v)))
def slug(v):
    return re.sub(r"_+","_",re.sub(r"[^a-z0-9]+","_",str(v or "").lower())).strip("_") or "unknown"

def fetch(client,table,order="run_date_sgt.desc"):
    filters={"anchor_theme_name":f"eq.{ANCHOR_THEME_NAME}"}
    if THEME_NAME: filters["theme_name"]=f"eq.{THEME_NAME}"
    return client.select(table,filters=filters,order=order,limit=MAX_ROWS)

def pkey(source,target,edge):
    return "single_hop:"+":".join([slug(ANCHOR_THEME_NAME),slug(source),slug(target),slug(edge or "no_edge")])

def index_by_possible_keys(rows,key_name):
    idx={}
    for r in rows:
        for k in [r.get("target_node_key"), r.get("source_node_key"), r.get(key_name)]:
            if k and k not in idx: idx[k]=r
    return idx

def direction(pos,neg):
    total=pos+neg
    if total<=1e-9: return "neutral"
    if abs(pos-neg)/total<0.15: return "mixed"
    return "positive" if pos>neg else "negative"

def regime(score):
    if score>=0.70: return "extreme_propagation"
    if score>=0.45: return "high_propagation"
    if score>=0.20: return "moderate_propagation"
    return "low_propagation"

def status(score,bottleneck,fragility,saturation):
    if saturation>=0.80: return "saturated"
    if fragility>=0.70: return "fragile"
    if bottleneck>=0.70: return "constrained"
    if score>=0.45: return "active"
    if score>=0.20: return "watchlist"
    return "inactive"

def build_row(edge, pressure, transmission):
    edge_strength=c01(edge.get("edge_strength"))
    edge_conf=c01(edge.get("confidence_score"))
    evidence=c01(edge.get("evidence_intensity"))
    persistence=c01(edge.get("persistence_score"))

    source_pressure=c01((pressure or {}).get("pressure_score"))
    pos_pressure=c01((pressure or {}).get("positive_pressure"))
    neg_pressure=c01((pressure or {}).get("negative_pressure"))

    transmission_potential=c01((transmission or {}).get("transmission_potential_score"))
    readiness=c01((transmission or {}).get("propagation_readiness_score"))
    susceptibility=c01((transmission or {}).get("susceptibility_score"))
    bottleneck=c01((transmission or {}).get("bottleneck_score"))
    fragility=c01((transmission or {}).get("fragility_score"))
    saturation=c01((pressure or {}).get("saturation_score"))

    prop_input=c01(0.35*source_pressure+0.30*transmission_potential+0.20*readiness+0.15*susceptibility)
    transfer=min(MAX_TRANSFER_WEIGHT,c01(0.35*edge_strength+0.25*edge_conf+0.20*evidence+0.20*persistence))

    bottleneck_mod=c01(1-bottleneck*0.35)
    fragility_mod=c01(1-fragility*0.25)
    saturation_mod=c01(1-saturation*0.20)
    confidence_mod=c01(0.5+edge_conf*0.5)

    propagated=c01(prop_input*transfer*bottleneck_mod*fragility_mod*saturation_mod*confidence_mod)

    total=pos_pressure+neg_pressure
    if total>1e-9:
        prop_pos=propagated*(pos_pressure/total)
        prop_neg=propagated*(neg_pressure/total)
    else:
        prop_pos=propagated*0.5
        prop_neg=propagated*0.5

    return {
        "run_date_sgt":run_date(),
        "propagation_key":pkey(edge.get("source_node_key"),edge.get("target_node_key"),edge.get("edge_key")),
        "anchor_theme_name":edge.get("anchor_theme_name") or ANCHOR_THEME_NAME,
        "theme_name":edge.get("theme_name"),
        "source_node_key":edge.get("source_node_key"),
        "target_node_key":edge.get("target_node_key"),
        "source_node_type":edge.get("source_node_type"),
        "target_node_type":edge.get("target_node_type"),
        "edge_key":edge.get("edge_key"),
        "edge_type":edge.get("edge_type"),
        "transmission_key":(transmission or {}).get("transmission_key"),
        "pressure_key":(pressure or {}).get("pressure_key"),
        "source_pressure_score":round(source_pressure,6),
        "source_transmission_potential_score":round(transmission_potential,6),
        "edge_strength":round(edge_strength,6),
        "edge_confidence_score":round(edge_conf,6),
        "evidence_intensity":round(evidence,6),
        "persistence_score":round(persistence,6),
        "propagation_input_score":round(prop_input,6),
        "propagation_transfer_weight":round(transfer,6),
        "propagated_pressure_score":round(propagated,6),
        "propagated_positive_pressure":round(prop_pos,6),
        "propagated_negative_pressure":round(prop_neg,6),
        "propagation_direction":direction(prop_pos,prop_neg),
        "propagation_regime":regime(propagated),
        "propagation_status":status(propagated,bottleneck,fragility,saturation),
        "bottleneck_modifier":round(bottleneck_mod,6),
        "fragility_modifier":round(fragility_mod,6),
        "saturation_modifier":round(saturation_mod,6),
        "confidence_modifier":round(confidence_mod,6),
        "propagation_metadata":{"phase":"4A","single_hop_only":True,"recursive_propagation":False,"multi_hop_propagation":False},
        "updated_at":now_iso()
    }

def generate(edges, pressures, transmissions):
    pidx=index_by_possible_keys(pressures,"pressure_key")
    tidx=index_by_possible_keys(transmissions,"transmission_key")
    out=[]
    for e in edges:
        if c01(e.get("edge_strength"))<MIN_EDGE_STRENGTH: continue
        source=e.get("source_node_key")
        target=e.get("target_node_key")
        pressure=pidx.get(source) or pidx.get(target) or pidx.get(e.get("edge_key"))
        transmission=tidx.get(source) or tidx.get(target) or tidx.get(e.get("edge_key"))
        if not pressure and not transmission: continue
        if transmission and c01(transmission.get("transmission_potential_score"))<MIN_TRANSMISSION_POTENTIAL: continue
        out.append(build_row(e,pressure,transmission))
    return out

def validate(rows):
    errors=[]; warnings=[]
    if not rows: warnings.append("No single-hop propagation rows generated.")
    metrics=["source_pressure_score","source_transmission_potential_score","edge_strength","edge_confidence_score","evidence_intensity","persistence_score","propagation_input_score","propagation_transfer_weight","propagated_pressure_score","propagated_positive_pressure","propagated_negative_pressure","bottleneck_modifier","fragility_modifier","saturation_modifier","confidence_modifier"]
    for r in rows:
        for col in ["propagation_key","source_node_key","target_node_key"]:
            if not r.get(col): errors.append(f"Missing {col}")
        for m in metrics:
            v=flt(r.get(m),None)
            if v is None or v<0 or v>1: errors.append(f"{m} out of range")
    if errors: return "failed",errors,warnings
    if warnings: return "warning",errors,warnings
    return "passed",errors,warnings

def avg(rows,col):
    vals=[flt(r.get(col),None) for r in rows]
    vals=[v for v in vals if v is not None]
    return round(sum(vals)/len(vals),6) if vals else None

def top(rows,col,n=10):
    return [{k:r.get(k) for k in ["propagation_key","source_node_key","target_node_key","edge_key","edge_type","propagated_pressure_score","propagation_transfer_weight","propagation_regime","propagation_status"]} for r in sorted(rows,key=lambda x:flt(x.get(col)),reverse=True)[:n]]

def make_snapshot(client, rows, edges_n, p_n, t_n, val, errs, warns):
    sid=snap_id()
    def count(field,value): return sum(1 for r in rows if r.get(field)==value)
    client.insert("structural_theme_graph_single_hop_snapshots",[{
        "snapshot_id":sid,"run_date_sgt":run_date(),"snapshot_version":SNAPSHOT_VERSION,
        "anchor_theme_name":ANCHOR_THEME_NAME,"theme_name":THEME_NAME or None,
        "source_edges_read":edges_n,"pressure_rows_read":p_n,"transmission_rows_read":t_n,
        "propagation_rows_generated":len(rows),
        "low_propagation_count":count("propagation_regime","low_propagation"),
        "moderate_propagation_count":count("propagation_regime","moderate_propagation"),
        "high_propagation_count":count("propagation_regime","high_propagation"),
        "extreme_propagation_count":count("propagation_regime","extreme_propagation"),
        "active_count":count("propagation_status","active"),
        "watchlist_count":count("propagation_status","watchlist"),
        "constrained_count":count("propagation_status","constrained"),
        "fragile_count":count("propagation_status","fragile"),
        "saturated_count":count("propagation_status","saturated"),
        "avg_propagated_pressure_score":avg(rows,"propagated_pressure_score"),
        "avg_transfer_weight":avg(rows,"propagation_transfer_weight"),
        "avg_input_score":avg(rows,"propagation_input_score"),
        "strongest_single_hop_paths":top(rows,"propagated_pressure_score"),
        "constrained_paths":top([r for r in rows if r.get("propagation_status")=="constrained"],"propagated_pressure_score"),
        "fragile_paths":top([r for r in rows if r.get("propagation_status")=="fragile"],"propagated_pressure_score"),
        "validation_status":val,"validation_errors":errs,"validation_warnings":warns,
        "snapshot_metadata":{"phase":"4A","single_hop_only":True}
    }])
    return sid

def telemetry(client,status,sid,edges_n,p_n,t_n,rows_n,val,errs,warns,rt,msg=None):
    client.insert("structural_theme_graph_single_hop_telemetry",[{
        "pipeline_name":PIPELINE_NAME,"snapshot_id":sid,"status":status,
        "source_edges_read":edges_n,"pressure_rows_read":p_n,"transmission_rows_read":t_n,
        "propagation_rows_upserted":rows_n,"validation_status":val,
        "validation_error_count":len(errs),"validation_warning_count":len(warns),
        "runtime_seconds":round(rt,3),"github_run_id":os.getenv("GITHUB_RUN_ID"),
        "github_workflow":os.getenv("GITHUB_WORKFLOW"),"github_repository":os.getenv("GITHUB_REPOSITORY"),
        "github_branch":os.getenv("GITHUB_REF_NAME"),"error_message":msg,
        "telemetry_metadata":{"phase":"4A","single_hop_only":True}
    }])

def main():
    start=time.time(); client=SupabaseRestClient(); sid=None
    edges=[]; pressures=[]; transmissions=[]; rows=[]
    try:
        edges=fetch(client,"structural_theme_graph_edges","updated_at.desc")
        pressures=fetch(client,"structural_theme_graph_pressure_accumulation")
        transmissions=fetch(client,"structural_theme_graph_transmission_potential")
        rows=generate(edges,pressures,transmissions)
        val,errs,warns=validate(rows)
        if val=="failed": raise RuntimeError("Phase 4A validation failed: "+" | ".join(errs[:10]))
        if rows:
            client.upsert("structural_theme_graph_single_hop_propagation",rows,on_conflict="run_date_sgt,propagation_key")
        sid=make_snapshot(client,rows,len(edges),len(pressures),len(transmissions),val,errs,warns)
        regimes=defaultdict(int); statuses=defaultdict(int)
        for r in rows:
            regimes[r.get("propagation_regime")]+=1
            statuses[r.get("propagation_status")]+=1
        telemetry(client,"success" if val=="passed" else "warning",sid,len(edges),len(pressures),len(transmissions),len(rows),val,errs,warns,time.time()-start)
        print("Phase 4A Controlled Single-Hop Propagation completed.")
        print(f"Source edges read: {len(edges)}")
        print(f"Pressure rows read: {len(pressures)}")
        print(f"Transmission rows read: {len(transmissions)}")
        print(f"Propagation rows upserted: {len(rows)}")
        print(f"Snapshot: {sid}")
        print(f"Validation: {val}")
        print(f"Propagation regime counts: {dict(regimes)}")
        print(f"Propagation status counts: {dict(statuses)}")
    except Exception as exc:
        telemetry(client,"failed",sid,len(edges),len(pressures),len(transmissions),0,"failed",[str(exc)],[],time.time()-start,str(exc))
        raise

if __name__=="__main__":
    main()
