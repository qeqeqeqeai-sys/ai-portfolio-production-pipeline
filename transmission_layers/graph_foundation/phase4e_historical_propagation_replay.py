import os,time,math,re,statistics
from collections import defaultdict
from datetime import datetime,timedelta,date,timezone
from graph_supabase_client import SupabaseRestClient

PIPELINE_NAME="PHASE_4E_HISTORICAL_PROPAGATION_REPLAY"
SNAPSHOT_VERSION="phase4e_v1"
ANCHOR_THEME_NAME=os.getenv("ANCHOR_THEME_NAME","ai").strip().lower()
THEME_NAME=os.getenv("THEME_NAME","").strip().lower()
LOOKBACK_DAYS=int(os.getenv("LOOKBACK_DAYS","30"))
MAX_ROWS=int(os.getenv("MAX_ROWS","50000"))
MAX_TRANSFER_WEIGHT=float(os.getenv("MAX_TRANSFER_WEIGHT","0.85"))
MIN_OBSERVATIONS_FOR_MEMORY=int(os.getenv("MIN_OBSERVATIONS_FOR_MEMORY","2"))

def now_iso(): return datetime.now(timezone.utc).isoformat()
def run_date(): return datetime.utcnow().strftime("%Y-%m-%d")
def today(): return datetime.utcnow().date()
def snap_id(): return f"{SNAPSHOT_VERSION}_{ANCHOR_THEME_NAME}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
def flt(v,d=0.0):
    try:
        x=float(v); return d if math.isnan(x) or math.isinf(x) else x
    except Exception: return d
def c01(v): return max(0.0,min(1.0,flt(v)))
def slug(v): return re.sub(r"_+","_",re.sub(r"[^a-z0-9]+","_",str(v or "").lower())).strip("_") or "unknown"
def parse_date(v):
    try: return datetime.fromisoformat(str(v)[:10]).date()
    except Exception: return None
def days(a,b): return max(0,(b-a).days+1) if a and b else 0

def fetch(client,table):
    start=(today()-timedelta(days=LOOKBACK_DAYS)).isoformat()
    filters={"anchor_theme_name":f"eq.{ANCHOR_THEME_NAME}","run_date_sgt":f"gte.{start}"}
    if THEME_NAME: filters["theme_name"]=f"eq.{THEME_NAME}"
    return client.select(table,filters=filters,order="run_date_sgt.asc",limit=MAX_ROWS)

def prop_key(src,tgt,edge): return "single_hop:"+":".join([slug(ANCHOR_THEME_NAME),slug(src),slug(tgt),slug(edge or "no_edge")])
def mem_key(r): return "memory:"+":".join([slug(ANCHOR_THEME_NAME),slug(r.get("source_node_key")),slug(r.get("target_node_key")),slug(r.get("edge_key") or r.get("propagation_key"))])

def by_date(rows):
    out=defaultdict(list)
    for r in rows:
        d=str(r.get("run_date_sgt") or "")[:10]
        if d: out[d].append(r)
    return out

def idx_by_date(rows,keyname):
    out=defaultdict(dict)
    for r in rows:
        d=str(r.get("run_date_sgt") or "")[:10]
        for k in [r.get("source_node_key"),r.get("target_node_key"),r.get(keyname)]:
            if k and k not in out[d]: out[d][k]=r
    return out

def latest_edges_on(edge_by_date,d):
    keys=[k for k in edge_by_date if k<=d]
    return edge_by_date[max(keys)] if keys else []

def merged_idx_on(idx,d):
    keys=sorted(k for k in idx if k<=d)
    out={}
    for k in keys: out.update(idx[k])
    return out

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

def build_replay(d,e,p,t):
    edge_strength=c01(e.get("edge_strength")); edge_conf=c01(e.get("confidence_score"))
    evidence=c01(e.get("evidence_intensity")); persistence=c01(e.get("persistence_score"))
    source_pressure=c01((p or {}).get("pressure_score"))
    pos=c01((p or {}).get("positive_pressure")); neg=c01((p or {}).get("negative_pressure"))
    potential=c01((t or {}).get("transmission_potential_score"))
    readiness=c01((t or {}).get("propagation_readiness_score"))
    susceptibility=c01((t or {}).get("susceptibility_score"))
    bottleneck=c01((t or {}).get("bottleneck_score")); fragility=c01((t or {}).get("fragility_score"))
    saturation=c01((p or {}).get("saturation_score"))
    prop_input=c01(0.35*source_pressure+0.30*potential+0.20*readiness+0.15*susceptibility)
    transfer=min(MAX_TRANSFER_WEIGHT,c01(0.35*edge_strength+0.25*edge_conf+0.20*evidence+0.20*persistence))
    propagated=c01(prop_input*transfer*c01(1-bottleneck*0.35)*c01(1-fragility*0.25)*c01(1-saturation*0.20)*c01(0.5+edge_conf*0.5))
    total=pos+neg
    prop_pos=propagated*(pos/total) if total>1e-9 else propagated*0.5
    prop_neg=propagated*(neg/total) if total>1e-9 else propagated*0.5
    return {
        "run_date_sgt":d,"propagation_key":prop_key(e.get("source_node_key"),e.get("target_node_key"),e.get("edge_key")),
        "anchor_theme_name":e.get("anchor_theme_name") or ANCHOR_THEME_NAME,"theme_name":e.get("theme_name"),
        "source_node_key":e.get("source_node_key"),"target_node_key":e.get("target_node_key"),
        "source_node_type":e.get("source_node_type"),"target_node_type":e.get("target_node_type"),
        "edge_key":e.get("edge_key"),"edge_type":e.get("edge_type"),
        "transmission_key":(t or {}).get("transmission_key"),"pressure_key":(p or {}).get("pressure_key"),
        "source_pressure_score":round(source_pressure,6),"source_transmission_potential_score":round(potential,6),
        "edge_strength":round(edge_strength,6),"edge_confidence_score":round(edge_conf,6),
        "evidence_intensity":round(evidence,6),"persistence_score":round(persistence,6),
        "propagation_input_score":round(prop_input,6),"propagation_transfer_weight":round(transfer,6),
        "propagated_pressure_score":round(propagated,6),"propagated_positive_pressure":round(prop_pos,6),
        "propagated_negative_pressure":round(prop_neg,6),"propagation_direction":direction(prop_pos,prop_neg),
        "propagation_regime":regime(propagated),"propagation_status":status(propagated,bottleneck,fragility,saturation),
        "bottleneck_modifier":round(c01(1-bottleneck*0.35),6),"fragility_modifier":round(c01(1-fragility*0.25),6),
        "saturation_modifier":round(c01(1-saturation*0.20),6),"confidence_modifier":round(c01(0.5+edge_conf*0.5),6),
        "propagation_metadata":{"phase":"4E","historical_replay":True,"single_hop_only":True},
        "updated_at":now_iso()
    }

def generate(edge_hist,pressures,transmissions):
    ebd=by_date(edge_hist); pidx=idx_by_date(pressures,"pressure_key"); tidx=idx_by_date(transmissions,"transmission_key")
    all_dates=sorted(set(list(ebd.keys())+list(pidx.keys())+list(tidx.keys())))
    replay=[]
    for d in all_dates:
        pmap=merged_idx_on(pidx,d); tmap=merged_idx_on(tidx,d)
        for e in latest_edges_on(ebd,d):
            p=pmap.get(e.get("source_node_key")) or pmap.get(e.get("target_node_key")) or pmap.get(e.get("edge_key"))
            t=tmap.get(e.get("source_node_key")) or tmap.get(e.get("target_node_key")) or tmap.get(e.get("edge_key"))
            if p or t: replay.append(build_replay(d,e,p,t))
    return replay

def volatility(vals):
    if len(vals)<2: return 0
    try: return c01(statistics.pstdev(vals))
    except Exception: return 0

def compute_memory(k,hist):
    hist=sorted(hist,key=lambda r:str(r.get("run_date_sgt") or ""))
    dates=[parse_date(r.get("run_date_sgt")) for r in hist if parse_date(r.get("run_date_sgt"))]
    first=min(dates); last=max(dates); latest=hist[-1]
    vals=[c01(r.get("propagated_pressure_score")) for r in hist]
    change=vals[-1]-vals[0]; slope=change/(len(vals)-1) if len(vals)>1 else 0
    vol=volatility(vals)
    persistence=c01((len(hist)/max(1,days(first,today())))*0.45 + (sum(vals)/len(vals))*0.35 + (1-vol)*0.20)
    reinforcement=c01(max(0,change)*2+max(0,slope)*5+vals[-1]*0.3)
    decay=c01(max(0,-change)*2+max(0,-slope)*5)
    exhaustion=c01((1-vals[-1])*0.4+decay*0.4+(1 if vals[-1]<=0.05 else 0)*0.2)
    transfers=[c01(r.get("propagation_transfer_weight")) for r in hist]
    carry=c01(vals[-1]*0.35+persistence*0.30+reinforcement*0.20+(sum(transfers)/len(transfers) if transfers else 0)*0.15)
    if len(hist)<MIN_OBSERVATIONS_FOR_MEMORY: regime,status="insufficient_memory","new"
    elif vol>=0.20: regime,status="volatile","volatile"
    elif vals[-1]<=0.05 and change<0: regime,status="exhausted","exhausted"
    elif change>=0.05: regime,status="reinforcing","reinforced"
    elif change<=-0.05: regime,status="decaying","weakening"
    else: regime,status="persistent","active"
    return {
        "run_date_sgt":run_date(),"memory_key":k,"propagation_key":latest.get("propagation_key"),
        "anchor_theme_name":latest.get("anchor_theme_name") or ANCHOR_THEME_NAME,"theme_name":latest.get("theme_name"),
        "source_node_key":latest.get("source_node_key"),"target_node_key":latest.get("target_node_key"),
        "source_node_type":latest.get("source_node_type"),"target_node_type":latest.get("target_node_type"),
        "edge_key":latest.get("edge_key"),"edge_type":latest.get("edge_type"),
        "first_seen_date_sgt":first.isoformat(),"last_seen_date_sgt":last.isoformat(),
        "observation_count":len(hist),"active_days":days(first,last),
        "latest_propagated_pressure_score":round(vals[-1],6),"avg_propagated_pressure_score":round(sum(vals)/len(vals),6),
        "max_propagated_pressure_score":round(max(vals),6),"min_propagated_pressure_score":round(min(vals),6),
        "pressure_change_abs":round(change,6),"pressure_change_pct":round(change/abs(vals[0]),6) if abs(vals[0])>1e-9 else None,
        "propagation_persistence_score":round(persistence,6),"propagation_reinforcement_score":round(reinforcement,6),
        "propagation_decay_score":round(decay,6),"propagation_exhaustion_score":round(exhaustion,6),
        "carry_forward_score":round(carry,6),"half_life_proxy_days":None,"memory_regime":regime,"memory_status":status,
        "memory_metadata":{"phase":"4E","historical_replay_backfill":True,"observations":len(hist)},"updated_at":now_iso()
    }

def build_memory(replay):
    g=defaultdict(list)
    for r in replay: g[mem_key(r)].append(r)
    return [compute_memory(k,h) for k,h in g.items()]

def validate(replay,memory):
    errors=[]; warnings=[]
    if not replay: warnings.append("No replay rows generated.")
    if not memory: warnings.append("No memory rows rebuilt.")
    for r in replay:
        for col in ["run_date_sgt","propagation_key","source_node_key","target_node_key"]:
            if not r.get(col): errors.append(f"Missing replay {col}")
    for r in memory:
        for col in ["memory_key","propagation_key","source_node_key","target_node_key","memory_regime"]:
            if not r.get(col): errors.append(f"Missing memory {col}")
    if errors: return "failed",errors,warnings
    if warnings: return "warning",errors,warnings
    return "passed",errors,warnings

def avg(rows,col):
    vals=[flt(r.get(col),None) for r in rows]; vals=[v for v in vals if v is not None]
    return round(sum(vals)/len(vals),6) if vals else None
def top(rows,col,n=10):
    return [{k:r.get(k) for k in ["propagation_key","memory_key","source_node_key","target_node_key","edge_key",col,"memory_regime","memory_status"]} for r in sorted(rows,key=lambda x:flt(x.get(col)),reverse=True)[:n]]

def write_run(client,status,start_date,end_date,replay,memory,val,errs,warns,rt,msg=None,edges=0,pressures=0,trans=0):
    client.insert("structural_theme_graph_propagation_replay_runs",[{
        "pipeline_name":PIPELINE_NAME,"anchor_theme_name":ANCHOR_THEME_NAME,"theme_name":THEME_NAME or None,
        "replay_start_date_sgt":start_date,"replay_end_date_sgt":end_date,"replay_days":LOOKBACK_DAYS,"status":status,
        "edge_history_rows_read":edges,"pressure_rows_read":pressures,"transmission_rows_read":trans,
        "replay_rows_generated":len(replay),"replay_rows_upserted":len(replay),"memory_rows_rebuilt":len(memory),
        "validation_status":val,"validation_error_count":len(errs),"validation_warning_count":len(warns),
        "runtime_seconds":round(rt,3),"github_run_id":os.getenv("GITHUB_RUN_ID"),"github_workflow":os.getenv("GITHUB_WORKFLOW"),
        "github_repository":os.getenv("GITHUB_REPOSITORY"),"github_branch":os.getenv("GITHUB_REF_NAME"),
        "error_message":msg,"replay_metadata":{"phase":"4E","lookback_days":LOOKBACK_DAYS}
    }])

def snapshot(client,start_date,end_date,replay,memory,val,errs,warns):
    sid=snap_id()
    def count(reg): return sum(1 for r in memory if r.get("memory_regime")==reg)
    client.insert("structural_theme_graph_propagation_replay_snapshots",[{
        "snapshot_id":sid,"run_date_sgt":run_date(),"snapshot_version":SNAPSHOT_VERSION,"anchor_theme_name":ANCHOR_THEME_NAME,
        "theme_name":THEME_NAME or None,"replay_start_date_sgt":start_date,"replay_end_date_sgt":end_date,"replay_days":LOOKBACK_DAYS,
        "replay_rows_generated":len(replay),"replay_rows_upserted":len(replay),"memory_rows_rebuilt":len(memory),
        "insufficient_memory_count":count("insufficient_memory"),"persistent_count":count("persistent"),"reinforcing_count":count("reinforcing"),
        "decaying_count":count("decaying"),"exhausted_count":count("exhausted"),"volatile_count":count("volatile"),"dormant_count":count("dormant"),
        "avg_replayed_pressure_score":avg(replay,"propagated_pressure_score"),"avg_carry_forward_score":avg(memory,"carry_forward_score"),
        "avg_decay_score":avg(memory,"propagation_decay_score"),"avg_reinforcement_score":avg(memory,"propagation_reinforcement_score"),
        "strongest_replayed_paths":top(replay,"propagated_pressure_score"),"strongest_backfilled_memory_paths":top(memory,"carry_forward_score"),
        "fastest_decaying_backfilled_paths":top(memory,"propagation_decay_score"),
        "validation_status":val,"validation_errors":errs,"validation_warnings":warns,"snapshot_metadata":{"phase":"4E","historical_replay":True}
    }])
    return sid

def main():
    start=time.time(); client=SupabaseRestClient()
    start_date=(today()-timedelta(days=LOOKBACK_DAYS)).isoformat(); end_date=today().isoformat()
    replay=[]; memory=[]
    try:
        edges=fetch(client,"structural_theme_graph_edge_history")
        pressures=fetch(client,"structural_theme_graph_pressure_accumulation")
        transmissions=fetch(client,"structural_theme_graph_transmission_potential")
        replay=generate(edges,pressures,transmissions)
        memory=build_memory(replay)
        val,errs,warns=validate(replay,memory)
        if val=="failed": raise RuntimeError("Phase 4E validation failed: "+" | ".join(errs[:10]))
        if replay: client.upsert("structural_theme_graph_single_hop_propagation",replay,on_conflict="run_date_sgt,propagation_key")
        if memory: client.upsert("structural_theme_graph_propagation_memory",memory,on_conflict="run_date_sgt,memory_key")
        sid=snapshot(client,start_date,end_date,replay,memory,val,errs,warns)
        write_run(client,"success" if val=="passed" else "warning",start_date,end_date,replay,memory,val,errs,warns,time.time()-start,edges=len(edges),pressures=len(pressures),trans=len(transmissions))
        regimes=defaultdict(int)
        for r in memory: regimes[r.get("memory_regime")]+=1
        print("Phase 4E Historical Propagation Replay & Memory Backfill completed.")
        print(f"Edge history rows read: {len(edges)}")
        print(f"Pressure rows read: {len(pressures)}")
        print(f"Transmission rows read: {len(transmissions)}")
        print(f"Replay rows upserted: {len(replay)}")
        print(f"Memory rows rebuilt: {len(memory)}")
        print(f"Snapshot: {sid}")
        print(f"Validation: {val}")
        print(f"Memory regime counts: {dict(regimes)}")
    except Exception as exc:
        write_run(client,"failed",start_date,end_date,replay,memory,"failed",[str(exc)],[],time.time()-start,msg=str(exc))
        raise

if __name__=="__main__":
    main()
