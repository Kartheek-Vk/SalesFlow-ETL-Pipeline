from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from salesflow.config import DB_PATH, RAW_DIR
from scripts.generate_data import generate_dataset
from salesflow.pipeline import run_pipeline


@pytest.fixture(scope="session")
def pipeline_result() -> dict[str, object]:
    generate_dataset(seed=42)
    return run_pipeline()


@pytest.fixture(scope="session")
def database_path(pipeline_result: dict[str, object]) -> Path:
    return DB_PATH