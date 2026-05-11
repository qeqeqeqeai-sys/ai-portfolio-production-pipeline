from historical_backfill_utils import fetch_table

TABLE = "historical_ai_transmission_scores"

rows = fetch_table(TABLE)

assert rows, "Validation failed: no rows written"

allowed_regimes = {
    "OVERHEATED",
    "BULLISH",
    "NEUTRAL",
    "BEARISH",
    "COLLAPSING"
}

invalid_regimes = []
negative_scores = []

for row in rows:

    regime = row.get("transmission_regime")

    if regime not in allowed_regimes:
        invalid_regimes.append(regime)

    score = row.get("transmission_score")

    if score is not None:
        if score < 0 or score > 100:
            negative_scores.append(score)

assert len(invalid_regimes) == 0, "Invalid regimes detected"
assert len(negative_scores) == 0, "Out-of-range scores detected"

print("VALIDATION PASSED")
