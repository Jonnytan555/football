import logging
import time
from datetime import date
from typing import Optional

from retry import retry
from ingestion import appsettings as settings
from shared.db import engine
from ingestion.scraper.scraper import Scraper
from ingestion.scraper.request.get_request import HttpGetRequestHandler
from ingestion.scraper.response.football_response_handler import FootballResponseHandler
from ingestion.scraper.persistence.db_insert_handler import DbInsertHandler

class MatchesScraper:

    @retry(tries=5, delay=2, backoff=2)
    def scrape_today(self, date_from: Optional[date] = None, date_to: Optional[date] = None):
        date_from = date_from or date.today()
        date_to = date_to or date.today()
        Scraper(
            request_handler=HttpGetRequestHandler(
                url='https://api.football-data.org/v4/matches',
                headers={'X-Auth-Token': settings.API_KEY},
                params={'dateFrom': date_from.isoformat(), 'dateTo': date_to.isoformat()},
            ),
            response_handler=FootballResponseHandler(data_path='matches'),
            persist_handler=DbInsertHandler(engine=engine, schema="public", table_name="football_matches", key_cols=["match_id"]),
        ).scrape(dropNa=False)

    def scrape_seasons(self, seasons: Optional[list[int]] = None):
        seasons = seasons or list(range(settings.BACKFILL_FROM, date.today().year + 1))
        for league_name, competition_id in settings.LEAGUES.items():
            for season in seasons:
                logging.info("Scraping %s season %s", league_name, season)
                try:
                    self._scrape_season(competition_id, season)
                    time.sleep(settings.RATE_LIMIT_SLEEP)
                except Exception:
                    logging.exception("Failed: %s season %s", league_name, season)

    @retry(tries=5, delay=2, backoff=2)
    def _scrape_season(self, competition_id: int, season: int):
        Scraper(
            request_handler=HttpGetRequestHandler(
                url=f'https://api.football-data.org/v4/competitions/{competition_id}/matches',
                headers={'X-Auth-Token': settings.API_KEY},
                params={'season': season},
            ),
            response_handler=FootballResponseHandler(data_path='matches'),
            persist_handler=DbInsertHandler(engine=engine, schema="public", table_name="football_matches", key_cols=["match_id"]),
        ).scrape(dropNa=False)
