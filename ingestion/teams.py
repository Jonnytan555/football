"""python -m ingestion.teams"""
import ingestion._setup  # noqa: F401
from ingestion.sources.football_data_org.teams import TeamsScraper

if __name__ == "__main__":
    TeamsScraper().scrape()
