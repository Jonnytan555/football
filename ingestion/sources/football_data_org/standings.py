import logging
import time
from datetime import date
from typing import Optional

from retry import retry
from ingestion import appsettings as settings
from shared.db import engine
from ingestion.scraper.scraper import Scraper
from ingestion.scraper.request.get_request import HttpGetRequestHandler
from ingestion.scraper.response.standings_response_handler import StandingsResponseHandler
from ingestion.scraper.persistence.db_insert_handler import DbInsertHandler

class StandingsScraper:

    def scrape(self, seasons: Optional[list[int]] = None):
        seasons = seasons or list(range(settings.BACKFILL_FROM, date.today().year + 1))
        for league_name, competition_id in settings.LEAGUES.items():
            for season in seasons:
                logging.info("Scraping standings: %s season %s", league_name, season)
                try:
                    self._scrape_season(competition_id, season)
                    time.sleep(settings.RATE_LIMIT_SLEEP)
                except Exception:
                    logging.exception("Failed standings: %s season %s", league_name, season)

    @retry(tries=5, delay=2, backoff=2)
    def _scrape_season(self, competition_id: int, season: int):
        Scraper(
            request_handler=HttpGetRequestHandler(
                url=f"https://api.football-data.org/v4/competitions/{competition_id}/standings",
                headers={"X-Auth-Token": settings.API_KEY},
                params={"season": season},
            ),
            response_handler=StandingsResponseHandler(),
            persist_handler=DbInsertHandler(
                engine=engine, schema="public", table_name="football_standings",
                key_cols=["competition_id", "season", "team_id"],
            ),
        ).scrape(dropNa=False)
