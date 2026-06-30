import logging
import os
from datetime import date, timedelta

import pandas as pd
import requests
import sqlalchemy as sa

from shared.db import engine
from modelling.python.features import build_features, current_team_stats, h2h_stats, load_matches
from modelling.python.predictor import FootballPredictor, MODEL_PATH

COMPETITIONS = {2021, 2016, 2001}


def fetch_upcoming(days_ahead: int = 7) -> list[dict]:
    resp = requests.get(
        "https://api.football-data.org/v4/matches",
        headers={"X-Auth-Token": os.getenv("FOOTBALL_API_KEY", "")},
        params={
            "dateFrom": date.today().isoformat(),
            "dateTo": (date.today() + timedelta(days=days_ahead)).isoformat(),
            "status": "SCHEDULED",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return [m for m in resp.json().get("matches", []) if m.get("competition", {}).get("id") in COMPETITIONS]


def _save_predictions(rows: list[dict]) -> None:
    if not rows:
        return
    pd.DataFrame(rows).to_sql(
        "football_predictions", con=engine, schema="public", if_exists="append", index=False,
        dtype={c: sa.Float() for c in ["prob_home_win", "prob_draw", "prob_away_win"]},
    )
    logging.info("Saved %d predictions", len(rows))


def run(days_ahead: int = 7, retrain: bool = False) -> None:
    fixtures = fetch_upcoming(days_ahead)
    if not fixtures:
        logging.info("No upcoming fixtures found")
        return
    logging.info("Found %d fixtures", len(fixtures))

    if retrain or not MODEL_PATH.exists():
        predictor = FootballPredictor()
        stats = predictor.train(build_features())
        predictor.save()
        logging.info("Trained — accuracy %.1f%%", stats["accuracy"] * 100)
    else:
        predictor = FootballPredictor.load()

    matches = load_matches()
    team_stats = current_team_stats(matches)
    results = []

    for fixture in fixtures:
        home_id = fixture["homeTeam"]["id"]
        away_id = fixture["awayTeam"]["id"]
        home_name = fixture["homeTeam"]["name"]
        away_name = fixture["awayTeam"]["name"]

        if home_id not in team_stats or away_id not in team_stats:
            logging.warning("No history for %s vs %s — skipping", home_name, away_name)
            continue

        home_s = {f"home_{k}": v for k, v in team_stats[home_id].items()}
        away_s = {f"away_{k}": v for k, v in team_stats[away_id].items()}
        h2h = h2h_stats(home_id, away_id, matches)
        probs = predictor.predict_match(home_s, away_s, h2h["h2h_home_win_rate"], h2h["h2h_meetings"])

        results.append({
            "match_id": fixture["id"],
            "utc_date": fixture["utcDate"],
            "competition": fixture["competition"]["name"],
            "home_team": home_name,
            "away_team": away_name,
            "prob_home_win": probs["Home Win"],
            "prob_draw": probs["Draw"],
            "prob_away_win": probs["Away Win"],
            "predicted_outcome": max(probs, key=probs.get),
            "predicted_on": date.today().isoformat(),
        })
        logging.info("%-25s vs %-25s  HW %.0f%%  D %.0f%%  AW %.0f%%",
                     home_name, away_name, probs["Home Win"] * 100, probs["Draw"] * 100, probs["Away Win"] * 100)

    _save_predictions(results)
