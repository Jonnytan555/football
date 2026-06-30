import logging
import httpx
from .request_handler import RequestHandler


class HttpGetRequestHandler(RequestHandler):

    def handle(self):
        try:
            logging.info("[GET] %s params=%s", self.url, self.params)
            response = httpx.request(
                method="GET",
                url=self.url,
                headers=self.headers,
                params=self.params,
                auth=self.auth,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response
        except Exception as e:
            logging.error("GET failed %s: %s", self.url, repr(e))
            raise
