import os,time,math,re
from collections import defaultdict
from datetime import datetime, timezone
from typing import *
from graph_supabase_client import SupabaseRestClient

PIPELINE_NAME="PHASE_3E_TRANSMISSION_POTENTIAL_SURFACE"
ANCHOR_THEME_NAME=os.getenv("ANCHOR_THEME_NAME","ai").strip().lower()
THEME_NAME=os.getenv("THEME_NAME","").strip().lower()
MAX_ROWS=int(os.getenv("MAX_ROWS","20000"))

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def run_date():
    return datetime.utcnow().strftime("%Y-%m-%d")

def snap_id():
    return f"phase3e_v1_{ANCHOR_THEME_NAME}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

def f(v,d=0.0):
    try:
        x=float(v)
        if math.isnan(x) or math.isinf(x):
            return d
        return x
    except:
        return d

def c(v):
    return max(0.0,min(1.0,f(v)))

def slug(v):
    return re.sub(r"_+","_",re.sub(r"[^a-z0-9]+","_",str(v or "").lower())).strip("_") or "unknown"

def fetch(client,table):
    filters={"anchor_theme_name":f"eq.{ANCHOR_THEME_NAME}"}
    if THEME_NAME:
        filters["theme_name"]=f"eq.{THEME_NAME}"
    return client.select(table,filters=filters,order="run_date_sgt.desc",limit=MAX_ROWS)

def regime(score):
    if score>=0.85: return "extreme_potential"
    if score>=0.65: return "high_potential"
    if score>=0.35: return "moderate_potential"
    return "low_potential"

def status(row):
    if row["bottleneck_score"]>=0.70:
        return "bottleneck"
    if row["fragility_score"]>=0.70:
        return "fragile"
    if row["transmission_potential_score"]>=0.65:
        return "active"
    return "watchlist"

def avg(rows,key):
    vals=[f(r.get(key),None) for r in rows]
    vals=[x for x in vals if x is not None]
    return sum(vals)/len(vals) if vals else 0.0

def make_row(scope,values,p_rows,t_rows,d_rows):
    pressure=max(avg(p_rows,"pressure_score"),avg(p_rows,"saturation_score"))
    persistence=avg(p_rows,"persistence_pressure")
    imbalance=avg(p_rows,"imbalance_score")
    drift=max(avg(d_rows,"drift_magnitude"),avg(p_rows,"drift_pressure"))
    reinforcement=avg(p_rows,"reinforcing_pressure")
    decay=avg(p_rows,"decay_pressure")
    emergence=avg(p_rows,"emergence_pressure")
    volatility=avg(p_rows,"volatility_pressure")

    propagation_readiness=c(
        0.35*pressure+
        0.25*persistence+
        0.20*reinforcement+
        0.20*emergence
    )

    susceptibility=c(
        0.35*imbalance+
        0.35*drift+
        0.30*volatility
    )

    pressure_gradient=c(abs(
        avg(p_rows,"positive_pressure")-
        avg(p_rows,"negative_pressure")
    ))

    directional_tension=c(
        0.5*imbalance+
        0.5*pressure_gradient
    )

    bottleneck=c(
        0.45*pressure+
        0.30*imbalance+
        0.25*persistence
    )

    fragility=c(
        0.40*volatility+
        0.35*drift+
        0.25*decay
    )

    persistence_alignment=c(
        0.6*persistence+
        0.4*reinforcement
    )

    drift_alignment=c(
        0.6*drift+
        0.4*emergence
    )

    score=c(
        0.20*propagation_readiness+
        0.18*susceptibility+
        0.18*pressure_gradient+
        0.14*directional_tension+
        0.10*bottleneck+
        0.10*fragility+
        0.10*persistence_alignment
    )

    row={
        "run_date_sgt":run_date(),
        "transmission_key":"transmission:"+":".join([
            slug(scope),
            slug(values.get("theme_name")),
            slug(values.get("source_node_key")),
            slug(values.get("target_node_key")),
            slug(values.get("target_node_type")),
            slug(values.get("edge_type"))
        ]),
        "transmission_scope":scope,
        "anchor_theme_name":ANCHOR_THEME_NAME,
        "theme_name":values.get("theme_name"),
        "source_node_key":values.get("source_node_key"),
        "target_node_key":values.get("target_node_key"),
        "target_node_type":values.get("target_node_type"),
        "edge_type":values.get("edge_type"),

        "transmission_potential_score":round(score,6),
        "propagation_readiness_score":round(propagation_readiness,6),
        "susceptibility_score":round(susceptibility,6),
        "pressure_gradient_score":round(pressure_gradient,6),
        "directional_tension_score":round(directional_tension,6),
        "bottleneck_score":round(bottleneck,6),
        "fragility_score":round(fragility,6),
        "persistence_alignment_score":round(persistence_alignment,6),
        "drift_alignment_score":round(drift_alignment,6),

        "transmission_regime":regime(score),
        "transmission_status":"pending",

        "contributing_pressure_rows":len(p_rows),
        "contributing_transition_rows":len(t_rows),
        "contributing_drift_rows":len(d_rows),

        "pressure_metadata":{
            "phase":"3E",
            "pipeline_name":PIPELINE_NAME,
        },
        "updated_at":now_iso()
    }

    row["transmission_status"]=status(row)
    return row

def filter_rows(rows,field,value):
    return [r for r in rows if str(r.get(field) or "")==str(value or "")]

def generate(p_rows,t_rows,d_rows):
    out=[]

    out.append(make_row(
        "anchor_theme",
        {"theme_name":THEME_NAME or None},
        p_rows,t_rows,d_rows
    ))

    specs=[
        ("theme","theme_name"),
        ("target_node_type","target_node_type"),
        ("edge_type","edge_type"),
        ("source_node","source_node_key"),
        ("target_node","target_node_key")
    ]

    for scope,field in specs:
        values=sorted(set(str(r.get(field) or "") for r in p_rows if r.get(field)))
        for value in values:
            pv=filter_rows(p_rows,field,value)
            tv=filter_rows(t_rows,field,value) if t_rows and field in t_rows[0] else []
            dv=filter_rows(d_rows,field,value) if d_rows and field in d_rows[0] else []

            out.append(make_row(
                scope,
                {
                    "theme_name":value if field=="theme_name" else None,
                    "source_node_key":value if field=="source_node_key" else None,
                    "target_node_key":value if field=="target_node_key" else None,
                    "target_node_type":value if field=="target_node_type" else None,
                    "edge_type":value if field=="edge_type" else None,
                },
                pv,tv,dv
            ))

    return out

def validate(rows):
    errors=[]
    warnings=[]

    if not rows:
        warnings.append("No transmission rows generated")

    metrics=[
        "transmission_potential_score",
        "propagation_readiness_score",
        "susceptibility_score",
        "pressure_gradient_score",
        "directional_tension_score",
        "bottleneck_score",
        "fragility_score",
        "persistence_alignment_score",
        "drift_alignment_score"
    ]

    for r in rows:
        for m in metrics:
            v=f(r.get(m),None)
            if v is None or v<0 or v>1:
                errors.append(f"{m} invalid")

    if errors:
        return "failed",errors,warnings
    if warnings:
        return "warning",errors,warnings
    return "passed",errors,warnings

def top(rows,key,n=10):
    s=sorted(rows,key=lambda r:f(r.get(key)),reverse=True)
    return [{
        "transmission_key":r.get("transmission_key"),
        "transmission_scope":r.get("transmission_scope"),
        "theme_name":r.get("theme_name"),
        "source_node_key":r.get("source_node_key"),
        "target_node_key":r.get("target_node_key"),
        key:r.get(key),
        "transmission_regime":r.get("transmission_regime"),
        "transmission_status":r.get("transmission_status"),
    } for r in s[:n]]

def snapshot(client,rows,val,errs,warns):
    sid=snap_id()

    def count(field,valx):
        return sum(1 for r in rows if r.get(field)==valx)

    client.insert("structural_theme_graph_transmission_snapshots",[{
        "snapshot_id":sid,
        "run_date_sgt":run_date(),
        "anchor_theme_name":ANCHOR_THEME_NAME,
        "theme_name":THEME_NAME or None,

        "transmission_rows_generated":len(rows),
        "low_potential_count":count("transmission_regime","low_potential"),
        "moderate_potential_count":count("transmission_regime","moderate_potential"),
        "high_potential_count":count("transmission_regime","high_potential"),
        "extreme_potential_count":count("transmission_regime","extreme_potential"),

        "active_count":count("transmission_status","active"),
        "watchlist_count":count("transmission_status","watchlist"),
        "bottleneck_count":count("transmission_status","bottleneck"),
        "fragile_count":count("transmission_status","fragile"),

        "avg_transmission_potential_score":round(avg(rows,"transmission_potential_score"),6),
        "avg_pressure_gradient_score":round(avg(rows,"pressure_gradient_score"),6),
        "avg_fragility_score":round(avg(rows,"fragility_score"),6),

        "strongest_transmission_surfaces":top(rows,"transmission_potential_score"),
        "largest_pressure_gradients":top(rows,"pressure_gradient_score"),
        "largest_fragility_surfaces":top(rows,"fragility_score"),

        "validation_status":val,
        "validation_errors":errs,
        "validation_warnings":warns,
        "snapshot_metadata":{
            "phase":"3E",
            "pipeline_name":PIPELINE_NAME
        }
    }])

    return sid

def telemetry(client,status,sid,p,t,d,u,val,errs,warns,rt,meta,msg=None):
    client.insert("structural_theme_graph_transmission_telemetry",[{
        "snapshot_id":sid,
        "status":status,
        "pressure_rows_read":p,
        "transition_rows_read":t,
        "drift_rows_read":d,
        "transmission_rows_upserted":u,
        "validation_status":val,
        "validation_error_count":len(errs),
        "validation_warning_count":len(warns),
        "runtime_seconds":round(rt,3),
        "error_message":msg,
        "telemetry_metadata":meta
    }])

def main():
    start=time.time()
    client=SupabaseRestClient()

    sid=None
    try:
        pressure_rows=fetch(client,"structural_theme_graph_pressure_accumulation")
        transition_rows=fetch(client,"structural_theme_graph_regime_transitions")
        drift_rows=fetch(client,"structural_theme_graph_structural_drift")

        rows=generate(pressure_rows,transition_rows,drift_rows)

        val,errs,warns=validate(rows)

        if val=="failed":
            raise RuntimeError("Validation failed")

        client.upsert(
            "structural_theme_graph_transmission_potential",
            rows,
            on_conflict="run_date_sgt,transmission_key"
        )

        sid=snapshot(client,rows,val,errs,warns)

        regime_counts=defaultdict(int)
        status_counts=defaultdict(int)

        for r in rows:
            regime_counts[r.get("transmission_regime")]+=1
            status_counts[r.get("transmission_status")]+=1

        telemetry(
            client,
            "success" if val=="passed" else "warning",
            sid,
            len(pressure_rows),
            len(transition_rows),
            len(drift_rows),
            len(rows),
            val,
            errs,
            warns,
            time.time()-start,
            {
                "phase":"3E",
                "regime_counts":dict(regime_counts),
                "status_counts":dict(status_counts)
            }
        )

        print("Phase 3E Transmission Potential Surface completed.")
        print(f"Pressure rows read: {len(pressure_rows)}")
        print(f"Transition rows read: {len(transition_rows)}")
        print(f"Drift rows read: {len(drift_rows)}")
        print(f"Transmission rows upserted: {len(rows)}")
        print(f"Snapshot: {sid}")
        print(f"Validation: {val}")
        print(f"Transmission regime counts: {dict(regime_counts)}")
        print(f"Transmission status counts: {dict(status_counts)}")

    except Exception as exc:
        telemetry(
            client,"failed",sid,0,0,0,0,"failed",[str(exc)],[],
            time.time()-start,
            {"phase":"3E"},
            str(exc)
        )
        raise

if __name__=="__main__":
    main()
