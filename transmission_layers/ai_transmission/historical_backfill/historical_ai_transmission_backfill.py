import time
import pandas as pd
from datetime import datetime, timedelta

from historical_backfill_utils import (
    fetch_table,
    upsert_rows,
    calculate_return,
    regime_from_score
)

from historical_backfill_checkpointing import (
    save_checkpoint
)

from historical_backfill_telemetry import (
    write_telemetry
)

PROCESS_NAME = "HISTORICAL_AI_TRANSMISSION_BACKFILL"
TARGET_TABLE = "historical_ai_transmission_scores"

LOOKBACK_DAYS = 90
CHUNK_SIZE = 7


print("Loading transmission map...")

transmission_map = fetch_table("ai_transmission_map")
prices = fetch_table("ai_stock_prices")
stock_scores = fetch_table("ai_stock_scores")
observations = fetch_table("ai_transmission_observations")

prices_df = pd.DataFrame(prices)
stock_scores_df = pd.DataFrame(stock_scores)
obs_df = pd.DataFrame(observations)

prices_df["date"] = pd.to_datetime(prices_df["date"])
obs_df["run_date_sgt"] = pd.to_datetime(obs_df["run_date_sgt"])
stock_scores_df["run_date_sgt"] = pd.to_datetime(stock_scores_df["run_date_sgt"])

end_date = datetime.today()
start_date = end_date - timedelta(days=LOOKBACK_DAYS)

all_dates = pd.date_range(start_date, end_date)

rows_written_total = 0
chunk_id = 0

start_runtime = time.time()

for i in range(0, len(all_dates), CHUNK_SIZE):

    chunk_dates = all_dates[i:i + CHUNK_SIZE]
    chunk_id += 1

    output_rows = []

    print(f"Processing chunk {chunk_id}...")

    for current_date in chunk_dates:

        current_date_str = current_date.strftime("%Y-%m-%d")

        for mapping in transmission_map:

            ticker = mapping.get("affected_ticker")

            if not ticker:
                continue

            momentum_30d = calculate_return(
                prices_df,
                ticker,
                current_date,
                30
            )

            score_subset = stock_scores_df[
                (
                    stock_scores_df["ticker"] == ticker
                )
                &
                (
                    stock_scores_df["run_date_sgt"] <= current_date
                )
            ].sort_values("run_date_sgt")

            factor_score = 50

            if not score_subset.empty:
                factor_score = float(
                    score_subset.iloc[-1].get(
                        "overall_ai_risk_score",
                        50
                    ) or 50
                )

            obs_subset = obs_df[
                (
                    obs_df["map_id"] == mapping["id"]
                )
                &
                (
                    obs_df["run_date_sgt"] <= current_date
                )
            ].sort_values("run_date_sgt")

            observation_score = 0

            if not obs_subset.empty:
                latest_obs = obs_subset.iloc[-1]

                days_since = (
                    current_date - latest_obs["run_date_sgt"]
                ).days

                decay = pow(2.71828, -days_since / 14)

                observation_score = float(
                    latest_obs.get(
                        "impact_magnitude_score",
                        0
                    ) or 0
                ) * decay

            persistence_score = min(
                max(momentum_30d, 0),
                100
            )

            transmission_score = (
                0.35 * float(mapping.get("base_strength_score") or 50)
                + 0.20 * momentum_30d
                + 0.15 * factor_score
                + 0.15 * observation_score
                + 0.15 * persistence_score
            )

            transmission_score = max(
                min(transmission_score, 100),
                0
            )

            regime = regime_from_score(transmission_score)

            row = {
                "run_date_sgt": current_date_str,
                "map_id": mapping["id"],
                "ai_subsector": mapping["ai_subsector"],
                "affected_sector": mapping["affected_sector"],
                "affected_subsector": mapping["affected_subsector"],
                "affected_ticker": ticker,
                "affected_company": mapping["affected_company"],
                "reconstructed_momentum_score": round(momentum_30d, 4),
                "reconstructed_factor_score": round(factor_score, 4),
                "reconstructed_observation_score": round(observation_score, 4),
                "persistence_score": round(persistence_score, 4),
                "transmission_score": round(transmission_score, 4),
                "transmission_regime": regime,
                "confidence_score": round(transmission_score * 0.85, 4)
            }

            output_rows.append(row)

    written = upsert_rows(
        TARGET_TABLE,
        output_rows,
        on_conflict="run_date_sgt,map_id,affected_ticker"
    )

    rows_written_total += written

    save_checkpoint(
        PROCESS_NAME,
        chunk_dates[-1].strftime("%Y-%m-%d"),
        written,
        chunk_id,
        runtime_seconds=round(time.time() - start_runtime, 2)
    )

    print(f"Chunk {chunk_id} complete. Rows written: {written}")

runtime_seconds = round(time.time() - start_runtime, 2)

write_telemetry({
    "process_name": PROCESS_NAME,
    "lookback_days": LOOKBACK_DAYS,
    "dates_processed": len(all_dates),
    "rows_written": rows_written_total,
    "chunk_count": chunk_id,
    "runtime_seconds": runtime_seconds,
    "warnings": 0,
    "failures": 0,
    "coverage_ratio": 1.0,
    "status": "SUCCESS",
    "message": "Historical AI transmission reconstruction completed"
})

print("DONE")
