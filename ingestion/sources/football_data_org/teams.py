import logging

from retry import retry
from ingestion import appsettings as settings
from shared.db import engine
from ingestion.scraper.scraper import Scraper
from ingestion.scraper.request.get_request import HttpGetRequestHandler
from ingestion.scraper.response.json_response_handler import JsonResponseHandler
from ingestion.scraper.persistence.db_insert_handler import DbInsertHandler

class TeamsScraper:

    @retry(tries=5, delay=2, backoff=2)
    def scrape(self):
        for league_name, competition_id in settings.LEAGUES.items():
            logging.info("Scraping teams: %s", league_name)
            try:
                Scraper(
                    request_handler=HttpGetRequestHandler(
                        url=f"https://api.football-data.org/v4/competitions/{competition_id}/teams",
                        headers={"X-Auth-Token": settings.API_KEY},
                    ),
                    response_handler=JsonResponseHandler(data_path="teams"),
                    persist_handler=DbInsertHandler(engine=engine, schema="public", table_name="football_teams", key_cols=["id"]),
                ).scrape(dropNa=False)
            except Exception:
                logging.exception("Failed teams: %s", league_name)
