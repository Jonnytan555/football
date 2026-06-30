import os

# football-data.org API
API_KEY = os.getenv("FOOTBALL_API_KEY", "")

# Competitions to scrape
LEAGUES = {
    "Premier League": 2021,
    "Championship": 2016,
    "Champions League": 2001,
}

# Seconds between requests — free tier allows 10/min
RATE_LIMIT_SLEEP = 7

# Seasons to backfill if none specified
BACKFILL_FROM = 2020
