import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from shared.logger import setup_log

_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "football_data", "logs")
setup_log(app="ingestion", filename=os.path.join(_LOG_PATH, "ingestion.log"), use_stream=True)
