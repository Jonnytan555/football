import os
from pathlib import Path

# Saved model location
MODEL_PATH = Path(os.getenv("MODEL_PATH", Path(__file__).parent.parent / "football_data" / "model.pkl"))

# Rolling form window (number of games)
FORM_WINDOW = 5

# Competition IDs to include in upcoming fixture predictions
PREDICTION_COMPETITIONS = {2021, 2016, 2001}

# How many days ahead to fetch upcoming fixtures
FIXTURE_LOOKAHEAD_DAYS = 7
