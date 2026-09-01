# SalesFlow ETL

An interview-ready Python data engineering portfolio project that turns messy e-commerce CSVs into validated Spark facts, SQLite analytics, and a FastAPI read layer.

## Run & Operate

- `python scripts/generate_data.py` — generate the reproducible raw dataset
- `python run_pipeline.py` — run ingestion, validation, Spark transformation, quality reporting, and SQLite loading
- `python -m uvicorn api.main:app --reload` — run the analytics API locally
- `pnpm --filter @workspace/api-server run dev` — generate, run the pipeline, and serve the API through the preview
- `pnpm run typecheck` — full typecheck across all packages
- `pytest -q` — run the automated test suite

## Stack

- Python 3.11, Pandas, PySpark, SQLite, FastAPI, Pydantic, pytest

## Where things live

- `salesflow/ingestion/reader.py` — extract CSV files and log counts
- `salesflow/validation/rules.py` — validation rules and reject-file handling
- `salesflow/transformation/spark_transform.py` — PySpark joins and revenue calculations
- `salesflow/database/sqlite_loader.py` — warehouse schema and load
- `salesflow/analytics/queries.py` — source-of-truth SQL analytics
- `api/main.py` — FastAPI routes and Pydantic response models
- `run_pipeline.py` — end-to-end entry point

## Architecture decisions

- Raw data is intentionally dirty so the quality layer is visible during a portfolio walkthrough.
- Rejected records are written separately with rule-level reasons; they are never silently dropped.
- SQLite is the local warehouse; the same star-schema boundary can be moved to a managed SQL engine.
- Spark owns the main join and derived-metric work, even though the included dataset is intentionally small.

## Product

Run one command to create sample data and populate a local analytics database, then query revenue, products, categories, states, months, and the quality report through documented API endpoints.

## User preferences

The implementation should remain understandable to a 3rd-year B.Tech student presenting it in an internship interview.

## Gotchas

- Run `python scripts/generate_data.py` before the first pipeline run in a clean checkout.
- The FastAPI service intentionally reports database-not-ready until `run_pipeline.py` has completed.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
