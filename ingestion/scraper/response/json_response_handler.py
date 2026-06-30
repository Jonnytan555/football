import json
import pandas as pd
from requests import Response
from .response_handler import ResponseHandler


class JsonResponseHandler(ResponseHandler):

    def handle(self, response: Response) -> pd.DataFrame:
        data = json.loads(response.text)
        if self.data_path:
            for path in self.data_path.split('.'):
                data = data[path]
        return pd.json_normalize(data)
