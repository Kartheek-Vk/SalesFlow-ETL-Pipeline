from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from salesflow.logging_config import configure_logging

logger = configure_logging()


@dataclass
class IngestionResult:
    frames: dict[str, pd.DataFrame]
    records_ingested: int
    files_ingested: int
    ingestion_timestamp: str


REQUIRED_FILES = ("customers.csv", "products.csv", "orders.csv")


def ingest_csvs(raw_dir: Path) -> IngestionResult:
    timestamp = datetime.now(timezone.utc).isoformat()
    frames: dict[str, pd.DataFrame] = {}
    total_records = 0

    for filename in REQUIRED_FILES:
        path = raw_dir / filename
        if not path.exists():
            logger.error("ingestion_failed file=%s reason=missing_file", filename)
            raise FileNotFoundError(f"Required raw file is missing: {path}")
        frame = pd.read_csv(path, dtype="string")
        key = path.stem
        frames[key] = frame
        total_records += len(frame)
        logger.info("ingested file=%s records=%d", filename, len(frame))

    logger.info(
        "ingestion_succeeded files=%d records=%d timestamp=%s",
        len(frames),
        total_records,
        timestamp,
    )
    return IngestionResult(frames, total_records, len(frames), timestamp)