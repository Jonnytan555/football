import logging
from datetime import date

import pandas as pd
import sqlalchemy as sa

from shared.db import engine


def load_predictions() -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(sa.text("SELECT * FROM football_predictions"), conn, parse_dates=["utc_date"])


def load_results() -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(sa.text("SELECT match_id, winner, home_goals, away_goals FROM football_matches WHERE status = 'FINISHED'"), conn)


def _label(winner: str) -> str:
    return {"HOME_TEAM": "Home Win", "DRAW": "Draw", "AWAY_TEAM": "Away Win"}.get(winner, "Unknown")


def evaluate() -> pd.DataFrame:
    merged = load_predictions().merge(load_results(), on="match_id", how="inner")
    if merged.empty:
        logging.info("No settled predictions yet")
        return pd.DataFrame()

    merged["actual_outcome"] = merged["winner"].map(_label)
    merged["correct"] = merged["predicted_outcome"] == merged["actual_outcome"]
    overall_acc = merged["correct"].mean()
    logging.info("Overall accuracy: %.1f%%  (%d matches)", overall_acc * 100, len(merged))

    breakdown = (
        merged.groupby("actual_outcome")["correct"]
        .agg(correct="sum", total="count")
        .assign(accuracy=lambda d: d["correct"] / d["total"])
    )
    logging.info("\nPer-outcome:\n%s", breakdown.to_string())

    merged["confidence"] = merged[["prob_home_win", "prob_draw", "prob_away_win"]].max(axis=1)
    merged["confidence_bucket"] = pd.cut(
        merged["confidence"], bins=[0, 0.4, 0.5, 0.6, 0.7, 1.0],
        labels=["<40%", "40-50%", "50-60%", "60-70%", ">70%"]
    )
    calibration = (
        merged.groupby("confidence_bucket", observed=True)["correct"]
        .agg(correct="sum", total="count")
        .assign(accuracy=lambda d: d["correct"] / d["total"])
    )
    logging.info("\nCalibration:\n%s", calibration.to_string())

    summary = []
    for outcome, row in breakdown.iterrows():
        summary.append({
            "evaluated_on": date.today().isoformat(),
            "outcome": outcome,
            "correct": int(row["correct"]),
            "total": int(row["total"]),
            "accuracy": round(float(row["accuracy"]), 4),
            "overall_accuracy": round(float(overall_acc), 4),
        })
    pd.DataFrame(summary).to_sql("football_prediction_accuracy", con=engine, schema="public", if_exists="append", index=False)
    logging.info("Saved accuracy summary")
    return merged
