import json
import pandas as pd
from requests import Response
from .response_handler import ResponseHandler


class FootballResponseHandler(ResponseHandler):

    def handle(self, response: Response) -> pd.DataFrame:
        data = json.loads(response.text)
        if self.data_path:
            for path in self.data_path.split('.'):
                data = data[path]

        df = pd.json_normalize(data)
        mapped = pd.DataFrame()
        mapped['match_id'] = df.get('id')
        mapped['utc_date'] = df.get('utcDate')
        mapped['status'] = df.get('status')
        mapped['competition_id'] = df.get('competition.id')
        mapped['competition_name'] = df.get('competition.name')
        mapped['home_team_id'] = df.get('homeTeam.id')
        mapped['home_team'] = df.get('homeTeam.name')
        mapped['away_team_id'] = df.get('awayTeam.id')
        mapped['away_team'] = df.get('awayTeam.name')
        mapped['winner'] = df.get('score.winner')
        mapped['home_goals'] = df.get('score.fullTime.home')
        mapped['away_goals'] = df.get('score.fullTime.away')
        mapped['last_updated'] = df.get('lastUpdated')
        return mapped
