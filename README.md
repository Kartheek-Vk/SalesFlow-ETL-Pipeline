# SalesFlow ETL

SalesFlow ETL is a small but complete sales data engineering portfolio project. It takes intentionally messy e-commerce CSV files, validates and cleans them, uses PySpark for the main dimensional joins and revenue calculations, loads a local SQLite warehouse, and exposes real analytics through FastAPI.

It is designed to be easy to explain in a data science or data engineering internship interview without hiding the important parts behind a framework.

## Business problem

An online retailer receives customer, product, and order exports from different operational systems. Before analysts can trust revenue reports, the pipeline needs to:

1. Ingest the raw files and record what arrived.
2. Detect bad data such as duplicates, missing values, invalid dates, negative quantities, and orphan references.
3. Preserve rejected rows with the exact reason they were rejected.
4. Join orders to customer and product dimensions.
5. Calculate gross revenue, discount amount, and net revenue.
6. Store an analytics-friendly model and answer common business questions.

## Architecture

```text
data/raw/*.csv
      |
      v
CSV ingestion + logging
      |
      v
Pandas validation and cleaning --------> data/rejected/*.csv
      |
      v
PySpark typed joins and calculations
      |
      +-------------------------------> data/processed/*.csv
      |
      v
SQLite warehouse
      |
      +-------------------------------> data/reports/quality_report.json
      |
      v
SQL analytics queries
      |
      +--------------------> FastAPI read-only endpoints
      |
      +--------------------> Streamlit demonstration dashboard
```

## Technology stack

- Python 3.11
- Pandas for file ingestion and row-level validation
- Apache Spark / PySpark for typed transformations and joins
- SQLite for a portable local warehouse
- SQL for analytics and summary tables
- FastAPI + Pydantic for the API
- Python logging for pipeline monitoring
- pytest for automated tests

## Project structure

```text
.
├── api/main.py                         # FastAPI app and response models
├── data/
│   ├── raw/                            # generated input CSVs
│   ├── processed/                      # validated inputs
│   ├── rejected/                       # bad rows with rejection_reasons
│   └── reports/quality_report.json
├── salesflow/
│   ├── ingestion/reader.py
│   ├── validation/rules.py
│   ├── transformation/spark_transform.py
│   ├── quality/report.py
│   ├── database/sqlite_loader.py
│   └── analytics/queries.py
├── scripts/generate_data.py             # reproducible sample data
├── tests/                               # validation, Spark, DB, and API tests
├── run_pipeline.py
├── requirements.txt
└── logs/pipeline.log
```

## Dataset

The generator creates:

- `customers.csv`: customer identity, demographics, location, signup date
- `products.csv`: product name, category, and unit price
- `orders.csv`: customer/product references, dates, quantity, discount, payment, and status

It also adds representative defects: duplicate IDs, impossible ages, invalid prices and dates, negative quantities, invalid discounts, and invalid customer/product references. This makes the quality report demonstrable rather than decorative.

## Data-quality strategy

Every validation function returns two data frames:

- **Valid rows** continue through the pipeline.
- **Rejected rows** are written to `data/rejected/<dataset>.csv` with a `rejection_reasons` column.

Checks include null required fields, duplicate IDs, numeric ranges, dates, foreign keys, order status, and orphan fact rows. The report in `data/reports/quality_report.json` records totals, valid and rejected counts, failed check names, per-check counts, a timestamp, and an overall score.

Bad data is never silently deleted. In a production pipeline, these reject files would normally be sent to a quarantine location for remediation and replay.
https://venkatakartheek.streamlit.app/#sales-flow-etl

## Data model

The SQLite database contains:

- `customers`: customer dimension, primary key `customer_id`
- `products`: product dimension, primary key `product_id`
- `orders`: cleaned transaction-level order records
- `sales_fact`: enriched fact table with customer/product attributes and revenue measures
- `daily_sales_summary`: daily aggregate for fast reads
- `product_sales_summary`: product aggregate for fast reads

The central fact-table measures are:

```text
gross_revenue   = quantity * unit_price
discount_amount = gross_revenue * discount
net_revenue     = gross_revenue - discount_amount
```

Cancelled orders retain their gross value for operational context but contribute `0` to net revenue.

## Spark usage

`transform_with_spark` creates explicit Spark schemas, converts date strings with Spark functions, joins orders to both dimensions, and derives the three revenue measures. The result is collected back to Pandas only because this local portfolio dataset is small enough to load into SQLite. With millions of rows, Spark would write partitioned Parquet or load directly into a distributed warehouse instead.

## Run locally

The Python dependencies are listed in `requirements.txt`. In this environment they are also managed by `pyproject.toml` and `uv.lock`.

```bash
# Install dependencies in a clean Python environment
pip install -r requirements.txt

# Generate reproducible raw files
python scripts/generate_data.py

# Run the complete ETL pipeline
python run_pipeline.py
```

Example output:

```text
ETL PIPELINE COMPLETED
{
  "records_ingested": 173,
  "records_cleaned": 156,
  "records_rejected": 35,
  "records_loaded": 101,
  "quality_score": 79.8,
  "execution_time_seconds": 8.4
}
```

The exact runtime varies by machine. The loaded fact count is lower than the cleaned row count because the count includes all validated datasets while the fact table contains orders only.

## API

After the pipeline has run:

```bash
python -m uvicorn api.main:app --reload
```

Interactive documentation is available at `http://localhost:8000/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service and database readiness |
| GET | `/analytics/summary` | Revenue, orders, AOV, discounts, cancellations |
| GET | `/analytics/top-products?limit=10` | Top products by net revenue |
| GET | `/analytics/revenue-by-category` | Category revenue |
| GET | `/analytics/revenue-by-state` | State revenue |
| GET | `/analytics/monthly-revenue` | Monthly revenue trend |
| GET | `/quality/report` | Full data-quality report |

The preview service also exposes the same endpoints under `/api`, for example `/api/health` and `/api/analytics/summary`.

## Dashboard

Streamlit provides a lightweight visualization layer over the processed SQLite data and the generated quality report. It displays:

- KPI values for revenue, orders, average order value, discounts, cancellations, and customers
- Revenue analytics by category, state, and month
- Top-product analytics
- Rejected records and validation reasons
- Pipeline source, stages, database, Spark status, and last execution time

Start the dashboard after generating the data and running the ETL pipeline:

```bash
streamlit run ui/dashboard.py
```

The dashboard is a presentation layer; the underlying ETL, validation, PySpark processing, and SQL analytics form the core of the project. It does not bypass the pipeline or hardcode analytics values.

Example response:

```json
{
  "total_revenue": 42167.84,
  "total_orders": 119,
  "average_order_value": 354.35,
  "total_discount": 5031.62,
  "cancelled_orders": 8,
  "unique_customers": 29
}
```

## Tests

```bash
pytest -q
```

The suite covers validation rules, duplicate and foreign-key detection, invalid dates and discounts, Spark joins, revenue calculations, cancelled-order behavior, database loading, and API endpoints.

## Monitoring and failure handling

Structured human-readable events are written to `logs/pipeline.log`. The pipeline logs start/end, ingestion counts, validation results, rejection counts, Spark transformation completion, database loading, and errors. Missing input files fail loudly rather than producing a partial report. A scheduled production job could alert on a non-zero exit code or a quality score below a chosen threshold.

## Azure Cloud Mapping

This is a local implementation. It is **not running on Azure**. A proposed production architecture would map the components like this:

| Local component | Proposed Azure service | Responsibility |
|---|---|---|
| `scripts/generate_data.py` / incoming CSVs | Azure Data Lake Storage Gen2 | Durable raw, quarantine, and curated zones |
| Pipeline orchestration | Azure Data Factory | Schedule ingestion, pass parameters, retry activities, and alert |
| PySpark transformation | Azure Databricks | Scale joins and transformations across large partitions |
| SQLite warehouse | Azure SQL Database or Synapse Analytics | Governed serving layer for BI and API queries |
| `logs/pipeline.log` and quality report | Azure Monitor + Log Analytics | Centralized monitoring, dashboards, and alert rules |

The same raw/validated/rejected boundaries make this migration understandable: storage and compute change, while the data contracts and business logic remain recognizable.

## Interview notes

- **ETL**: extract source data, transform it into trusted business-ready data, and load it into a serving store.
- **Why PySpark?**: Spark distributes joins and aggregations when the data outgrows a single machine.
- **Why SQL?**: SQL is expressive and reviewable for business metrics and works well as a serving contract.
- **Why SQLite locally?**: It is zero-setup, transactional, portable, and mirrors the relational model without requiring cloud infrastructure.
- **What is a fact table?**: A table of measurable business events at a defined grain. Here, one valid order is one fact row.
- **How does this scale?**: Keep raw files immutable, partition by date, use Spark for distributed work, write Parquet, and serve aggregates from a warehouse.
- **How are failures handled?**: Invalid rows are quarantined with reasons; missing files and fatal infrastructure errors stop the run and are logged.
- **What would ADF do?**: Orchestrate schedules, dependencies, retries, and movement between storage and compute.
- **What would Databricks do?**: Run the Spark transformation on a managed cluster with autoscaling and job observability.
