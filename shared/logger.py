import logging
import logging.handlers
import os
import sys
from pathlib import Path


def setup_log(
    app: str,
    filename: str | None = None,
    minimum_level: int = logging.INFO,
    backup_count: int = 10,
    rolling_max_bytes: int = 10 * 1024 * 1024,
    use_stream: bool = False,
) -> None:
    log_format = "%(asctime)s [%(levelname)-8s] [%(filename)s:%(lineno)d] %(message)s"
    formatter = logging.Formatter(log_format)

    root = logging.getLogger()
    root.setLevel(minimum_level)

    for h in list(root.handlers):
        root.removeHandler(h)

    if use_stream:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        root.addHandler(sh)

    if filename:
        log_dir = Path(filename).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            filename=str(filename),
            backupCount=backup_count,
            maxBytes=rolling_max_bytes,
        )
        fh.setFormatter(formatter)
        root.addHandler(fh)
