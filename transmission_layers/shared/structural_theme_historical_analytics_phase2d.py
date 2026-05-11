import os
import math
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

THEME_NAME = os.getenv("THEME_NAME", "ai")
LOOKBACK_DAYS = int(os.getenv("PHASE2D_LOOKBACK_DAYS", "90"))

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal",
}


def require_env():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY")


def sgt_today():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).date()


def supabase_get(table, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.get(url, headers=HEADERS, params=params or {}, timeout=60)
    if r.status_code >= 300:
        raise RuntimeError(f"GET failed for {table}: {r.status_code} {r.text}")
    return r.json()


def supabase_upsert(table, rows, conflict_cols):
    if not rows:
        print(f"[SKIP] No rows for {table}")
        return

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {"on_conflict": ",".join(conflict_cols)}

    for i in range(0, len(rows), 500):
        batch = rows[i:i + 500]
        r = requests.post(url, headers=HEADERS, params=params, json=batch, timeout=90)
        if r.status_code >= 300:
            raise RuntimeError(f"UPSERT failed for {table}: {r.status_code} {r.text}")

    print(f"[OK] Upserted {len(rows)} rows into {table}")


def safe_num(x, default=0.0):
    try:
        if x is None or pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def classify_momentum_regime(momentum_30d, acceleration_7d):
    momentum_30d = safe_num(momentum_30d)
    acceleration_7d = safe_num(acceleration_7d)

    if momentum_30d > 10 and acceleration_7d > 0:
        return "Strong Expansion"
    if momentum_30d > 3:
        return "Moderate Expansion"
    if abs(momentum_30d) <= 3:
        return "Stable"
    if momentum_30d < -10 and acceleration_7d < 0:
        return "Stress Reversal"
    if momentum_30d < -3:
        return "Deceleration"
    return "Mixed"


def classify_evidence_regime(spike_score):
    spike_score = safe_num(spike_score)
    if spike_score >= 2.0:
        return "Evidence Explosion"
    if spike_score >= 1.0:
        return "Rising Evidence"
    if spike_score <= -1.0:
        return "Fading Evidence"
    return "Normal"


def compute_consecutive_active_days(df, group_cols, date_col, active_col):
    df = df.sort_values(group_cols + [date_col]).copy()
    results = []

    for keys, g in df.groupby(group_cols, dropna=False):
        count = 0
        for _, row in g.iterrows():
            if safe_num(row[active_col]) > 0:
                count += 1
            else:
                count = 0

            record = row.to_dict()
            record["persistence_days"] = count
            results.append(record)

    return pd.DataFrame(results)


def compute_half_life(values):
    values = [safe_num(v) for v in values if v is not None]
    if len(values) < 3:
        return None

    peak = max(values)
    if peak <= 0:
        return None

    threshold = peak * 0.5
    peak_index = values.index(peak)

    for i in range(peak_index, len(values)):
        if values[i] <= threshold:
            return i - peak_index

    return None


def fetch_scores(run_date_from):
    params = {
        "theme_name": f"eq.{THEME_NAME}",
        "run_date_sgt": f"gte.{run_date_from}",
        "select": "*",
        "order": "run_date_sgt.asc",
    }
    return pd.DataFrame(supabase_get("structural_theme_scores", params))


def fetch_component_scores(run_date_from):
    params = {
        "theme_name": f"eq.{THEME_NAME}",
        "run_date_sgt": f"gte.{run_date_from}",
        "select": "*",
        "order": "run_date_sgt.asc",
    }
    return pd.DataFrame(supabase_get("structural_theme_component_scores", params))


def fetch_evidence_attribution(run_date_from):
    params = {
        "theme_name": f"eq.{THEME_NAME}",
        "run_date_sgt": f"gte.{run_date_from}",
        "select": "*",
        "order": "run_date_sgt.asc",
    }
    return pd.DataFrame(supabase_get("structural_theme_evidence_attribution", params))


def fetch_explanations(run_date_from):
    params = {
        "theme_name": f"eq.{THEME_NAME}",
        "run_date_sgt": f"gte.{run_date_from}",
        "select": "*",
        "order": "run_date_sgt.asc",
    }
    return pd.DataFrame(supabase_get("structural_theme_explanations", params))


def get_entity_col(df):
    for c in ["entity", "ticker", "symbol", "target_entity", "asset"]:
        if c in df.columns:
            return c
    return None


def get_score_col(df):
    for c in ["theme_score", "score", "composite_score", "transmission_score", "final_score"]:
        if c in df.columns:
            return c
    return None


def build_momentum_history(scores):
    if scores.empty:
        return []

    df = scores.copy()
    entity_col = get_entity_col(df)
    score_col = get_score_col(df)

    if not entity_col or not score_col:
        print("[WARN] Cannot build momentum history: missing entity or score column")
        return []

    df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"]).dt.date
    df[score_col] = pd.to_numeric(df[score_col], errors="coerce").fillna(0)

    rows = []

    for entity, g in df.groupby(entity_col):
        g = g.sort_values("run_date_sgt").copy()
        g["score_7d_ago"] = g[score_col].shift(7)
        g["score_30d_ago"] = g[score_col].shift(30)

        g["momentum_7d"] = g[score_col] - g["score_7d_ago"]
        g["momentum_30d"] = g[score_col] - g["score_30d_ago"]

        g["prev_momentum_7d"] = g["momentum_7d"].shift(1)
        g["prev_momentum_30d"] = g["momentum_30d"].shift(1)

        g["acceleration_7d"] = g["momentum_7d"] - g["prev_momentum_7d"]
        g["acceleration_30d"] = g["momentum_30d"] - g["prev_momentum_30d"]

        g["active"] = (g[score_col] > 0).astype(int)
        g = compute_consecutive_active_days(g, [entity_col], "run_date_sgt", "active")

        for _, r in g.iterrows():
            m7 = safe_num(r.get("momentum_7d"))
            m30 = safe_num(r.get("momentum_30d"))
            a7 = safe_num(r.get("acceleration_7d"))
            persistence_days = int(safe_num(r.get("persistence_days")))

            persistence_score = min(persistence_days / 30, 1)

            structural_momentum_score = (
                0.40 * max(min(m30 / 20, 1), -1)
                + 0.30 * max(min(m7 / 10, 1), -1)
                + 0.20 * max(min(a7 / 10, 1), -1)
                + 0.10 * persistence_score
            ) * 100

            rows.append({
                "run_date_sgt": str(r["run_date_sgt"]),
                "theme_name": THEME_NAME,
                "entity": str(entity),
                "theme_score": safe_num(r[score_col]),
                "momentum_7d": m7,
                "momentum_30d": m30,
                "acceleration_7d": a7,
                "acceleration_30d": safe_num(r.get("acceleration_30d")),
                "momentum_persistence_days": persistence_days,
                "structural_momentum_score": structural_momentum_score,
                "momentum_regime": classify_momentum_regime(m30, a7),
            })

    return rows


def build_attribution_trends(component_scores):
    if component_scores.empty:
        return []

    df = component_scores.copy()
    entity_col = get_entity_col(df)

    component_col = "component_name" if "component_name" in df.columns else None
    score_col = None

    for c in ["component_score", "contribution_score", "score", "weighted_score"]:
        if c in df.columns:
            score_col = c
            break

    if not entity_col or not component_col or not score_col:
        print("[WARN] Cannot build attribution trend history: missing required columns")
        return []

    df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"]).dt.date
    df[score_col] = pd.to_numeric(df[score_col], errors="coerce").fillna(0)

    rows = []

    for (entity, component), g in df.groupby([entity_col, component_col]):
        g = g.sort_values("run_date_sgt").copy()
        g["rolling_avg_7d"] = g[score_col].rolling(7, min_periods=1).mean()
        g["rolling_avg_30d"] = g[score_col].rolling(30, min_periods=1).mean()
        g["attribution_change_7d"] = g[score_col] - g[score_col].shift(7)
        g["attribution_change_30d"] = g[score_col] - g[score_col].shift(30)

        for _, r in g.iterrows():
            rows.append({
                "run_date_sgt": str(r["run_date_sgt"]),
                "theme_name": THEME_NAME,
                "entity": str(entity),
                "component_name": str(component),
                "attribution_score": safe_num(r[score_col]),
                "rolling_avg_7d": safe_num(r["rolling_avg_7d"]),
                "rolling_avg_30d": safe_num(r["rolling_avg_30d"]),
                "attribution_change_7d": safe_num(r["attribution_change_7d"]),
                "attribution_change_30d": safe_num(r["attribution_change_30d"]),
                "attribution_rank": None,
            })

    out = pd.DataFrame(rows)

    if not out.empty:
        out["attribution_rank"] = (
            out.groupby(["run_date_sgt", "theme_name", "entity"])["attribution_score"]
            .rank(method="dense", ascending=False)
            .astype(int)
        )
        rows = out.to_dict("records")

    return rows


def build_evidence_intensity(evidence):
    if evidence.empty:
        return []

    df = evidence.copy()
    entity_col = get_entity_col(df)

    if not entity_col:
        print("[WARN] Cannot build evidence intensity: missing entity column")
        return []

    pathway_col = "pathway_name" if "pathway_name" in df.columns else None

    strength_col = None
    for c in ["evidence_strength", "confidence_score", "attribution_score", "score"]:
        if c in df.columns:
            strength_col = c
            break

    df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"]).dt.date

    if strength_col:
        df[strength_col] = pd.to_numeric(df[strength_col], errors="coerce").fillna(0)
    else:
        df["evidence_strength_fallback"] = 1.0
        strength_col = "evidence_strength_fallback"

    if pathway_col is None:
        df["pathway_name"] = "generic"
        pathway_col = "pathway_name"

    grouped = (
        df.groupby(["run_date_sgt", "theme_name", entity_col, pathway_col])
        .agg(
            evidence_count=(strength_col, "count"),
            high_confidence_evidence_count=(strength_col, lambda x: int((x >= 0.7).sum())),
            avg_evidence_strength=(strength_col, "mean"),
        )
        .reset_index()
    )

    rows = []

    for (entity, pathway), g in grouped.groupby([entity_col, pathway_col]):
        g = g.sort_values("run_date_sgt").copy()
        g["rolling_evidence_7d"] = g["evidence_count"].rolling(7, min_periods=1).mean()
        g["rolling_evidence_30d"] = g["evidence_count"].rolling(30, min_periods=1).mean()
        g["evidence_spike_score"] = (
            (g["evidence_count"] - g["rolling_evidence_30d"])
            / g["rolling_evidence_30d"].replace(0, 1)
        )

        for _, r in g.iterrows():
            spike = safe_num(r["evidence_spike_score"])
            rows.append({
                "run_date_sgt": str(r["run_date_sgt"]),
                "theme_name": THEME_NAME,
                "entity": str(entity),
                "pathway_name": str(pathway),
                "evidence_count": int(r["evidence_count"]),
                "high_confidence_evidence_count": int(r["high_confidence_evidence_count"]),
                "avg_evidence_strength": safe_num(r["avg_evidence_strength"]),
                "rolling_evidence_7d": safe_num(r["rolling_evidence_7d"]),
                "rolling_evidence_30d": safe_num(r["rolling_evidence_30d"]),
                "evidence_spike_score": spike,
                "evidence_regime": classify_evidence_regime(spike),
            })

    return rows


def build_regime_history(momentum_rows):
    if not momentum_rows:
        return []

    df = pd.DataFrame(momentum_rows)
    df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"]).dt.date
    rows = []

    for entity, g in df.groupby("entity"):
        g = g.sort_values("run_date_sgt").copy()
        g["previous_regime"] = g["momentum_regime"].shift(1)
        g["regime_changed"] = g["previous_regime"] != g["momentum_regime"]

        duration = 0
        last_regime = None

        for _, r in g.iterrows():
            current_regime = r["momentum_regime"]

            if current_regime == last_regime:
                duration += 1
            else:
                duration = 1

            previous_regime = r["previous_regime"]
            regime_changed = bool(r["regime_changed"]) if previous_regime == previous_regime else False

            if not previous_regime or previous_regime != previous_regime:
                transition_type = "Initial"
            elif regime_changed:
                transition_type = f"{previous_regime} -> {current_regime}"
            else:
                transition_type = "No Change"

            rows.append({
                "run_date_sgt": str(r["run_date_sgt"]),
                "theme_name": THEME_NAME,
                "entity": str(entity),
                "previous_regime": None if previous_regime != previous_regime else str(previous_regime),
                "current_regime": str(current_regime),
                "regime_changed": regime_changed,
                "regime_duration_days": duration,
                "transition_type": transition_type,
            })

            last_regime = current_regime

    return rows


def build_driver_persistence(component_scores):
    if component_scores.empty:
        return []

    df = component_scores.copy()
    entity_col = get_entity_col(df)
    driver_col = "component_name" if "component_name" in df.columns else None

    score_col = None
    for c in ["contribution_score", "component_score", "weighted_score", "score"]:
        if c in df.columns:
            score_col = c
            break

    if not entity_col or not driver_col or not score_col:
        print("[WARN] Cannot build driver persistence: missing columns")
        return []

    df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"]).dt.date
    df[score_col] = pd.to_numeric(df[score_col], errors="coerce").fillna(0)
    df["driver_direction"] = df[score_col].apply(lambda x: "positive" if x >= 0 else "negative")
    df["active"] = (df[score_col].abs() > 0).astype(int)

    df = compute_consecutive_active_days(
        df,
        [entity_col, driver_col, "driver_direction"],
        "run_date_sgt",
        "active"
    )

    rows = []

    for (entity, driver, direction), g in df.groupby([entity_col, driver_col, "driver_direction"]):
        g = g.sort_values("run_date_sgt").copy()
        g["rolling_avg_7d"] = g[score_col].rolling(7, min_periods=1).mean()
        g["rolling_avg_30d"] = g[score_col].rolling(30, min_periods=1).mean()

        values = list(g[score_col].abs())
        half_life = compute_half_life(values)

        for _, r in g.iterrows():
            persistence_days = int(safe_num(r["persistence_days"]))
            persistence_score = min(persistence_days / 30, 1) * 100

            rows.append({
                "run_date_sgt": str(r["run_date_sgt"]),
                "theme_name": THEME_NAME,
                "entity": str(entity),
                "driver_name": str(driver),
                "driver_direction": str(direction),
                "contribution_score": safe_num(r[score_col]),
                "rolling_avg_7d": safe_num(r["rolling_avg_7d"]),
                "rolling_avg_30d": safe_num(r["rolling_avg_30d"]),
                "persistence_days": persistence_days,
                "persistence_half_life": half_life,
                "persistence_score": persistence_score,
            })

    return rows


def main():
    require_env()

    today = sgt_today()
    run_date_from = today - timedelta(days=LOOKBACK_DAYS)

    print(f"[START] Phase 2D historical analytics for theme={THEME_NAME}")
    print(f"[INFO] Lookback from {run_date_from} to {today}")

    scores = fetch_scores(run_date_from)
    components = fetch_component_scores(run_date_from)
    evidence = fetch_evidence_attribution(run_date_from)

    print(f"[INFO] scores rows: {len(scores)}")
    print(f"[INFO] component rows: {len(components)}")
    print(f"[INFO] evidence rows: {len(evidence)}")

    momentum_rows = build_momentum_history(scores)
    attribution_rows = build_attribution_trends(components)
    evidence_rows = build_evidence_intensity(evidence)
    regime_rows = build_regime_history(momentum_rows)
    driver_rows = build_driver_persistence(components)

    supabase_upsert(
        "structural_theme_momentum_history",
        momentum_rows,
        ["run_date_sgt", "theme_name", "entity"]
    )

    supabase_upsert(
        "structural_theme_attribution_trend_history",
        attribution_rows,
        ["run_date_sgt", "theme_name", "entity", "component_name"]
    )

    supabase_upsert(
        "structural_theme_evidence_intensity_history",
        evidence_rows,
        ["run_date_sgt", "theme_name", "entity", "pathway_name"]
    )

    supabase_upsert(
        "structural_theme_regime_history",
        regime_rows,
        ["run_date_sgt", "theme_name", "entity"]
    )

    supabase_upsert(
        "structural_theme_driver_persistence_history",
        driver_rows,
        ["run_date_sgt", "theme_name", "entity", "driver_name", "driver_direction"]
    )

    print("[DONE] Phase 2D historical analytics completed")


if __name__ == "__main__":
    main()
