from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REJECTED_DIR = DATA_DIR / "rejected"
REPORTS_DIR = DATA_DIR / "reports"
LOG_DIR = PROJECT_ROOT / "logs"
DB_PATH = DATA_DIR / "salesflow.db"


def ensure_directories() -> None:
    for directory in (RAW_DIR, PROCESSED_DIR, REJECTED_DIR, REPORTS_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)