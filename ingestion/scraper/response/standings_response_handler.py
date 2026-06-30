import json
import pandas as pd
from requests import Response
from .response_handler import ResponseHandler


class StandingsResponseHandler(ResponseHandler):

    def handle(self, response: Response) -> pd.DataFrame:
        data = json.loads(response.text)

        competition_id = data.get("competition", {}).get("id")
        competition_name = data.get("competition", {}).get("name")
        season_start = data.get("season", {}).get("startDate", "")[:4]

        total = next((s for s in data.get("standings", []) if s.get("type") == "TOTAL"), None)
        if not total:
            return pd.DataFrame()

        df = pd.json_normalize(total["table"])
        mapped = pd.DataFrame()
        mapped["competition_id"] = competition_id
        mapped["competition_name"] = competition_name
        mapped["season"] = season_start
        mapped["position"] = df.get("position")
        mapped["team_id"] = df.get("team.id")
        mapped["team_name"] = df.get("team.name")
        mapped["played"] = df.get("playedGames")
        mapped["won"] = df.get("won")
        mapped["draw"] = df.get("draw")
        mapped["lost"] = df.get("lost")
        mapped["points"] = df.get("points")
        mapped["goals_for"] = df.get("goalsFor")
        mapped["goals_against"] = df.get("goalsAgainst")
        mapped["goal_difference"] = df.get("goalDifference")
        mapped["form"] = df.get("form")
        return mapped
