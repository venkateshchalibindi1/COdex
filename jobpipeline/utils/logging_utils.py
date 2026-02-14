from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_fields"):
            payload.update(getattr(record, "extra_fields"))
        return json.dumps(payload)


def setup_logging(log_dir: str = "data/logs") -> None:
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    logfile = path / "jobpipeline.log"
    handler = logging.FileHandler(logfile, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]
