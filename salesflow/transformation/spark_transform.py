from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from salesflow.logging_config import configure_logging

logger = configure_logging()


@dataclass
class TransformationResult:
    customers: pd.DataFrame
    products: pd.DataFrame
    sales_fact: pd.DataFrame
    transformed_records: int


def _spark_schema(fields: list[tuple[str, object]]) -> StructType:
    return StructType([StructField(name, dtype, True) for name, dtype in fields])


def transform_with_spark(valid_frames: dict[str, pd.DataFrame]) -> TransformationResult:
    logger.info("transformation_started engine=pyspark")
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("SalesFlowETL")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .getOrCreate()
    )
    try:
        customer_schema = _spark_schema([
            ("customer_id", StringType()), ("customer_name", StringType()),
            ("age", IntegerType()), ("gender", StringType()), ("city", StringType()),
            ("state", StringType()), ("signup_date", StringType()),
        ])
        product_schema = _spark_schema([
            ("product_id", StringType()), ("product_name", StringType()),
            ("category", StringType()), ("unit_price", DoubleType()),
        ])
        order_schema = _spark_schema([
            ("order_id", StringType()), ("customer_id", StringType()),
            ("product_id", StringType()), ("order_date", StringType()),
            ("quantity", IntegerType()), ("discount", DoubleType()),
            ("payment_method", StringType()), ("order_status", StringType()),
        ])
        customers = spark.createDataFrame(valid_frames["customers"], schema=customer_schema)
        products = spark.createDataFrame(valid_frames["products"], schema=product_schema)
        orders = spark.createDataFrame(valid_frames["orders"], schema=order_schema)

        customers = customers.withColumn(
            "signup_date", F.to_date("signup_date", "yyyy-MM-dd")
        )
        orders = orders.withColumn("order_date", F.to_date("order_date", "yyyy-MM-dd"))
        joined: DataFrame = (
            orders.join(customers, "customer_id", "inner")
            .join(products, "product_id", "inner")
            .withColumn("gross_revenue", F.col("quantity") * F.col("unit_price"))
            .withColumn("discount_amount", F.col("gross_revenue") * F.col("discount"))
            .withColumn(
                "net_revenue",
                F.when(F.col("order_status") == "cancelled", F.lit(0.0))
                .otherwise(F.col("gross_revenue") - F.col("discount_amount")),
            )
            .withColumn("order_month", F.date_format("order_date", "yyyy-MM"))
        )
        fact_columns = [
            "order_id", "order_date", "customer_id", "customer_name", "age", "gender",
            "city", "state", "product_id", "product_name", "category", "unit_price",
            "quantity", "discount", "discount_amount", "gross_revenue", "net_revenue",
            "payment_method", "order_status", "order_month",
        ]
        fact = joined.select(*fact_columns).toPandas()
        customer_output = customers.toPandas()
        product_output = products.toPandas()
        for frame in (fact, customer_output, product_output):
            for column in frame.columns:
                if str(frame[column].dtype).startswith("datetime"):
                    frame[column] = frame[column].dt.strftime("%Y-%m-%d")
        fact["order_date"] = fact["order_date"].astype(str)
        fact["discount_amount"] = fact["discount_amount"].round(2)
        fact["gross_revenue"] = fact["gross_revenue"].round(2)
        fact["net_revenue"] = fact["net_revenue"].round(2)
        logger.info("transformation_complete records=%d joins=customers,products", len(fact))
        return TransformationResult(customer_output, product_output, fact, len(fact))
    finally:
        spark.stop()