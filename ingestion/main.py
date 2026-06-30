"""
Ingestion entry point. Run from the football/ root directory.

    python -m ingestion.main today
    python -m ingestion.main backfill
    python -m ingestion.main backfill 2022 2023 2024
    python -m ingestion.main standings
    python -m ingestion.main standings 2023 2024
    python -m ingestion.main teams
"""
import logging
import os
import sys
import traceback

from shared.logger import setup_log

APP_NAME = "ingestion"
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "football_data", "logs")
setup_log(app=APP_NAME, filename=os.path.join(LOG_PATH, f"{APP_NAME}.log"), use_stream=True)

from ingestion.sources.football_data_org.matches import MatchesScraper
from ingestion.sources.football_data_org.standings import StandingsScraper
from ingestion.sources.football_data_org.teams import TeamsScraper

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "today"
    seasons = [int(s) for s in sys.argv[2:]] or None
    try:
        if mode == "today":
            MatchesScraper().scrape_today()
        elif mode == "backfill":
            MatchesScraper().scrape_seasons(seasons)
        elif mode == "standings":
            StandingsScraper().scrape(seasons)
        elif mode == "teams":
            TeamsScraper().scrape()
        else:
            print(f"Unknown mode '{mode}'. Use: today | backfill | standings | teams")
            sys.exit(1)
    except Exception:
        logging.error(traceback.format_exc())
