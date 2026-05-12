import os, time, math, re, statistics
from collections import defaultdict
from datetime import datetime, timezone, date
from graph_supabase_client import SupabaseRestClient

PIPELINE_NAME="PHASE_4B_PROPAGATION_MEMORY_DECAY"
SNAPSHOT_VERSION="phase4b_v1"

ANCHOR_THEME_NAME=os.getenv("ANCHOR_THEME_NAME","ai").strip().lower()
THEME_NAME=os.getenv("THEME_NAME","").strip().lower()
MAX_PROPAGATION_ROWS=int(os.getenv("MAX_PROPAGATION_ROWS","20000"))
MIN_OBSERVATIONS_FOR_MEMORY=int(os.getenv("MIN_OBSERVATIONS_FOR_MEMORY","2"))
DECAY_THRESHOLD=float(os.getenv("DECAY_THRESHOLD","0.05"))
REINFORCEMENT_THRESHOLD=float(os.getenv("REINFORCEMENT_THRESHOLD","0.05"))

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
def parse_date(v):
    if not v: return None
    if isinstance(v,date): return v
    try: return datetime.fromisoformat(str(v)[:10]).date()
    except Exception: return None
def days_between(a,b):
    if not a or not b: return 0
    return max(0,(b-a).days+1)

def memory_key(row):
    return "memory:"+":".join([
        slug(ANCHOR_THEME_NAME),
        slug(row.get("source_node_key")),
        slug(row.get("target_node_key")),
        slug(row.get("edge_key") or row.get("propagation_key"))
    ])

def fetch_propagation_rows(client):
    filters={"anchor_theme_name":f"eq.{ANCHOR_THEME_NAME}"}
    if THEME_NAME:
        filters["theme_name"]=f"eq.{THEME_NAME}"
    return client.select(
        "structural_theme_graph_single_hop_propagation",
        filters=filters,
        order="run_date_sgt.desc",
        limit=MAX_PROPAGATION_ROWS
    )

def group_by_memory(rows):
    grouped=defaultdict(list)
    for row in rows:
        grouped[memory_key(row)].append(row)
    for k in grouped:
        grouped[k].sort(key=lambda r: str(r.get("run_date_sgt") or ""))
    return grouped

def volatility(vals):
    if len(vals)<2: return 0.0
    try: return c01(statistics.pstdev(vals))
    except Exception: return 0.0

def trend(vals):
    if not vals: return 0.0,None,0.0
    first=vals[0]; last=vals[-1]
    diff=last-first
    pct=diff/abs(first) if abs(first)>1e-9 else None
    slope=diff/(len(vals)-1) if len(vals)>=2 else 0.0
    return diff,pct,slope

def classify(obs, change, vol, latest, days_since):
    if obs < MIN_OBSERVATIONS_FOR_MEMORY:
        return "insufficient_memory","new"
    if days_since > 30:
        return "dormant","dormant"
    if vol >= 0.20:
        return "volatile","volatile"
    if latest <= 0.05 and change < 0:
        return "exhausted","exhausted"
    if change >= REINFORCEMENT_THRESHOLD:
        return "reinforcing","reinforced"
    if change <= -DECAY_THRESHOLD:
        return "decaying","weakening"
    return "persistent","active"

def half_life_proxy(vals):
    if len(vals)<2:
        return None
    peak=max(vals)
    if peak<=0:
        return None
    half=peak*0.5
    for idx,v in enumerate(vals):
        if idx>0 and v<=half:
            return idx
    return None

def compute_memory(k, hist):
    today=parse_date(run_date()) or date.today()
    dates=[parse_date(r.get("run_date_sgt")) for r in hist]
    dates=[d for d in dates if d]
    first_seen=min(dates) if dates else today
    last_seen=max(dates) if dates else today
    latest=hist[-1]

    pressures=[c01(r.get("propagated_pressure_score")) for r in hist]
    positives=[c01(r.get("propagated_positive_pressure")) for r in hist]
    negatives=[c01(r.get("propagated_negative_pressure")) for r in hist]
    inputs=[c01(r.get("propagation_input_score")) for r in hist]
    transfers=[c01(r.get("propagation_transfer_weight")) for r in hist]

    obs=len(hist)
    active_days=days_between(first_seen,last_seen)
    latest_pressure=pressures[-1] if pressures else 0.0
    avg_pressure=sum(pressures)/len(pressures) if pressures else 0.0
    max_pressure=max(pressures) if pressures else 0.0
    min_pressure=min(pressures) if pressures else 0.0
    change,pct,slope=trend(pressures)
    vol=volatility(pressures)
    days_since=max(0,(today-last_seen).days)

    persistence=c01((obs/max(1,days_between(first_seen,today)))*0.45 + avg_pressure*0.35 + (1-vol)*0.20)
    reinforcement=c01(max(0,change)*2.0 + max(0,slope)*5.0 + latest_pressure*0.30)
    decay=c01(max(0,-change)*2.0 + max(0,-slope)*5.0 + min(1,days_since/60)*0.25)
    exhaustion=c01((1-latest_pressure)*0.40 + decay*0.40 + (1 if latest_pressure<=0.05 else 0)*0.20)
    carry=c01(latest_pressure*0.35 + persistence*0.30 + reinforcement*0.20 + avg(transfers)*0.15)

    regime,status=classify(obs,change,vol,latest_pressure,days_since)

    return {
        "run_date_sgt":run_date(),
        "memory_key":k,
        "propagation_key":latest.get("propagation_key"),
        "anchor_theme_name":latest.get("anchor_theme_name") or ANCHOR_THEME_NAME,
        "theme_name":latest.get("theme_name"),
        "source_node_key":latest.get("source_node_key"),
        "target_node_key":latest.get("target_node_key"),
        "source_node_type":latest.get("source_node_type"),
        "target_node_type":latest.get("target_node_type"),
        "edge_key":latest.get("edge_key"),
        "edge_type":latest.get("edge_type"),
        "first_seen_date_sgt":first_seen.isoformat(),
        "last_seen_date_sgt":last_seen.isoformat(),
        "observation_count":obs,
        "active_days":active_days,
        "latest_propagated_pressure_score":round(latest_pressure,6),
        "avg_propagated_pressure_score":round(avg_pressure,6),
        "max_propagated_pressure_score":round(max_pressure,6),
        "min_propagated_pressure_score":round(min_pressure,6),
        "pressure_change_abs":round(change,6),
        "pressure_change_pct":round(pct,6) if pct is not None else None,
        "propagation_persistence_score":round(persistence,6),
        "propagation_reinforcement_score":round(reinforcement,6),
        "propagation_decay_score":round(decay,6),
        "propagation_exhaustion_score":round(exhaustion,6),
        "carry_forward_score":round(carry,6),
        "half_life_proxy_days":half_life_proxy(pressures),
        "memory_regime":regime,
        "memory_status":status,
        "memory_metadata":{
            "phase":"4B",
            "pipeline_name":PIPELINE_NAME,
            "volatility_score":round(vol,6),
            "days_since_last_seen":days_since,
            "avg_positive_pressure":round(sum(positives)/len(positives),6) if positives else 0,
            "avg_negative_pressure":round(sum(negatives)/len(negatives),6) if negatives else 0,
            "avg_input_score":round(sum(inputs)/len(inputs),6) if inputs else 0,
            "avg_transfer_weight":round(sum(transfers)/len(transfers),6) if transfers else 0,
            "recent_history":[
                {
                    "run_date_sgt":r.get("run_date_sgt"),
                    "propagated_pressure_score":r.get("propagated_pressure_score"),
                    "propagation_regime":r.get("propagation_regime"),
                    "propagation_status":r.get("propagation_status")
                } for r in hist[-20:]
            ]
        },
        "updated_at":now_iso()
    }

def avg(rows,col):
    vals=[flt(r.get(col),None) for r in rows]
    vals=[v for v in vals if v is not None]
    return sum(vals)/len(vals) if vals else 0.0

def validate(rows):
    errors=[]; warnings=[]
    if not rows: warnings.append("No propagation memory rows generated.")
    metrics=[
        "latest_propagated_pressure_score","avg_propagated_pressure_score",
        "max_propagated_pressure_score","min_propagated_pressure_score",
        "propagation_persistence_score","propagation_reinforcement_score",
        "propagation_decay_score","propagation_exhaustion_score","carry_forward_score"
    ]
    regimes={"insufficient_memory","persistent","reinforcing","decaying","exhausted","volatile","dormant"}
    statuses={"new","active","reinforced","weakening","exhausted","dormant","volatile"}
    for r in rows:
        for col in ["memory_key","propagation_key","source_node_key","target_node_key","memory_regime","memory_status"]:
            if not r.get(col): errors.append(f"Missing {col}")
        if r.get("memory_regime") not in regimes: errors.append("Invalid memory_regime")
        if r.get("memory_status") not in statuses: errors.append("Invalid memory_status")
        for m in metrics:
            v=flt(r.get(m),None)
            if v is None or v<0 or v>1: errors.append(f"{m} out of range")
    if errors: return "failed",errors,warnings
    if warnings: return "warning",errors,warnings
    return "passed",errors,warnings

def top(rows,col,n=10):
    return [
        {
            "memory_key":r.get("memory_key"),
            "source_node_key":r.get("source_node_key"),
            "target_node_key":r.get("target_node_key"),
            "edge_key":r.get("edge_key"),
            "carry_forward_score":r.get("carry_forward_score"),
            "memory_regime":r.get("memory_regime"),
            "memory_status":r.get("memory_status"),
            col:r.get(col)
        }
        for r in sorted(rows,key=lambda x:flt(x.get(col)),reverse=True)[:n]
    ]

def make_snapshot(client,rows,prop_read,val,errs,warns):
    sid=snap_id()
    def count(reg): return sum(1 for r in rows if r.get("memory_regime")==reg)
    client.insert("structural_theme_graph_propagation_memory_snapshots",[{
        "snapshot_id":sid,
        "run_date_sgt":run_date(),
        "snapshot_version":SNAPSHOT_VERSION,
        "anchor_theme_name":ANCHOR_THEME_NAME,
        "theme_name":THEME_NAME or None,
        "propagation_rows_read":prop_read,
        "memory_rows_generated":len(rows),
        "insufficient_memory_count":count("insufficient_memory"),
        "persistent_count":count("persistent"),
        "reinforcing_count":count("reinforcing"),
        "decaying_count":count("decaying"),
        "exhausted_count":count("exhausted"),
        "volatile_count":count("volatile"),
        "dormant_count":count("dormant"),
        "avg_carry_forward_score":round(avg(rows,"carry_forward_score"),6),
        "avg_decay_score":round(avg(rows,"propagation_decay_score"),6),
        "avg_reinforcement_score":round(avg(rows,"propagation_reinforcement_score"),6),
        "avg_persistence_score":round(avg(rows,"propagation_persistence_score"),6),
        "strongest_memory_paths":top(rows,"carry_forward_score"),
        "fastest_decaying_paths":top(rows,"propagation_decay_score"),
        "strongest_reinforcing_paths":top(rows,"propagation_reinforcement_score"),
        "validation_status":val,
        "validation_errors":errs,
        "validation_warnings":warns,
        "snapshot_metadata":{"phase":"4B","pipeline_name":PIPELINE_NAME}
    }])
    return sid

def telemetry(client,status,sid,prop_read,rows_n,val,errs,warns,rt,msg=None):
    client.insert("structural_theme_graph_propagation_memory_telemetry",[{
        "pipeline_name":PIPELINE_NAME,
        "snapshot_id":sid,
        "status":status,
        "propagation_rows_read":prop_read,
        "memory_rows_upserted":rows_n,
        "validation_status":val,
        "validation_error_count":len(errs),
        "validation_warning_count":len(warns),
        "runtime_seconds":round(rt,3),
        "github_run_id":os.getenv("GITHUB_RUN_ID"),
        "github_workflow":os.getenv("GITHUB_WORKFLOW"),
        "github_repository":os.getenv("GITHUB_REPOSITORY"),
        "github_branch":os.getenv("GITHUB_REF_NAME"),
        "error_message":msg,
        "telemetry_metadata":{"phase":"4B"}
    }])

def main():
    start=time.time()
    client=SupabaseRestClient()
    sid=None
    prop_rows=[]
    memory_rows=[]
    try:
        prop_rows=fetch_propagation_rows(client)
        grouped=group_by_memory(prop_rows)
        memory_rows=[compute_memory(k,h) for k,h in grouped.items()]
        val,errs,warns=validate(memory_rows)
        if val=="failed":
            raise RuntimeError("Phase 4B validation failed: "+" | ".join(errs[:10]))
        if memory_rows:
            client.upsert(
                "structural_theme_graph_propagation_memory",
                memory_rows,
                on_conflict="run_date_sgt,memory_key"
            )
        sid=make_snapshot(client,memory_rows,len(prop_rows),val,errs,warns)
        regime_counts=defaultdict(int); status_counts=defaultdict(int)
        for r in memory_rows:
            regime_counts[r.get("memory_regime")]+=1
            status_counts[r.get("memory_status")]+=1
        telemetry(client,"success" if val=="passed" else "warning",sid,len(prop_rows),len(memory_rows),val,errs,warns,time.time()-start)
        print("Phase 4B Propagation Memory & Decay completed.")
        print(f"Propagation rows read: {len(prop_rows)}")
        print(f"Memory rows upserted: {len(memory_rows)}")
        print(f"Snapshot: {sid}")
        print(f"Validation: {val}")
        print(f"Memory regime counts: {dict(regime_counts)}")
        print(f"Memory status counts: {dict(status_counts)}")
    except Exception as exc:
        telemetry(client,"failed",sid,len(prop_rows),0,"failed",[str(exc)],[],time.time()-start,str(exc))
        raise

if __name__=="__main__":
    main()
