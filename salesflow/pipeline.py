import json
import time
from dataclasses import asdict

from salesflow.config import DB_PATH, PROCESSED_DIR, RAW_DIR, REPORTS_DIR, REJECTED_DIR, ensure_directories
from salesflow.database.sqlite_loader import database_counts, load_to_sqlite
from salesflow.ingestion.reader import ingest_csvs
from salesflow.logging_config import configure_logging
from salesflow.quality.report import build_quality_report
from salesflow.transformation.spark_transform import transform_with_spark
from salesflow.validation.rules import validate_customers, validate_orders, validate_products, write_rejections

logger = configure_logging()


def run_pipeline() -> dict[str, object]:
    ensure_directories()
    start = time.perf_counter()
    logger.info("pipeline_started")
    ingestion = ingest_csvs(RAW_DIR)

    customer_result = validate_customers(ingestion.frames["customers"])
    product_result = validate_products(ingestion.frames["products"])
    order_result = validate_orders(
        ingestion.frames["orders"],
        set(customer_result.valid["customer_id"]),
        set(product_result.valid["product_id"]),
    )
    validation_results = {
        "customers": customer_result,
        "products": product_result,
        "orders": order_result,
    }
    rejected_records = write_rejections(validation_results, REJECTED_DIR)
    valid_frames = {
        name: result.valid for name, result in validation_results.items()
    }
    for name, frame in valid_frames.items():
        frame.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)

    transformed = transform_with_spark(valid_frames)
    report = build_quality_report(
        valid_frames,
        transformed.sales_fact,
        customer_result.checks + product_result.checks + order_result.checks,
        rejected_records,
        ingestion.records_ingested,
        REPORTS_DIR / "quality_report.json",
    )
    loaded_records = load_to_sqlite(
        DB_PATH, transformed.customers, transformed.products, transformed.sales_fact
    )
    elapsed = round(time.perf_counter() - start, 2)
    result = {
        "records_ingested": ingestion.records_ingested,
        "records_cleaned": sum(len(frame) for frame in valid_frames.values()),
        "records_rejected": rejected_records,
        "records_loaded": loaded_records,
        "quality_score": report["quality_score"],
        "execution_time_seconds": elapsed,
        "database_counts": database_counts(DB_PATH),
    }
    logger.info("pipeline_completed result=%s", json.dumps(result))
    return result