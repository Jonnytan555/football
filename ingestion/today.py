"""python -m ingestion.today"""
import ingestion._setup  # noqa: F401 — configures logging + env
from ingestion.sources.football_data_org.matches import MatchesScraper

if __name__ == "__main__":
    MatchesScraper().scrape_today()
