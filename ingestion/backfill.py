"""
python -m ingestion.backfill
python -m ingestion.backfill 2022 2023 2024
"""
import sys
import ingestion._setup  # noqa: F401
from ingestion.sources.football_data_org.matches import MatchesScraper

if __name__ == "__main__":
    seasons = [int(s) for s in sys.argv[1:]] or None
    MatchesScraper().scrape_seasons(seasons)
