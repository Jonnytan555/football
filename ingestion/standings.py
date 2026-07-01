"""
python -m ingestion.standings
python -m ingestion.standings 2023 2024
"""
import sys
import ingestion._setup  # noqa: F401
from ingestion.sources.football_data_org.standings import StandingsScraper

if __name__ == "__main__":
    seasons = [int(s) for s in sys.argv[1:]] or None
    StandingsScraper().scrape(seasons)
