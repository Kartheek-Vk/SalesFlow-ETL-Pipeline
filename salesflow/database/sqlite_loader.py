import sqlite3
from pathlib import Path

import pandas as pd

from salesflow.logging_config import configure_logging

logger = configure_logging()


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
DROP TABLE IF EXISTS daily_sales_summary;
DROP TABLE IF EXISTS product_sales_summary;
DROP TABLE IF EXISTS sales_fact;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    signup_date TEXT NOT NULL
);
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL CHECK (unit_price > 0)
);
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    order_date TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    discount REAL NOT NULL CHECK (discount BETWEEN 0 AND 1),
    payment_method TEXT NOT NULL,
    order_status TEXT NOT NULL
);
CREATE TABLE sales_fact (
    order_id TEXT PRIMARY KEY REFERENCES orders(order_id),
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    customer_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    discount REAL NOT NULL,
    discount_amount REAL NOT NULL,
    gross_revenue REAL NOT NULL,
    net_revenue REAL NOT NULL,
    payment_method TEXT NOT NULL,
    order_status TEXT NOT NULL,
    order_month TEXT NOT NULL
);
CREATE TABLE daily_sales_summary (
    order_date TEXT PRIMARY KEY,
    orders INTEGER NOT NULL,
    gross_revenue REAL NOT NULL,
    net_revenue REAL NOT NULL,
    discount_amount REAL NOT NULL
);
CREATE TABLE product_sales_summary (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    orders INTEGER NOT NULL,
    units_sold INTEGER NOT NULL,
    net_revenue REAL NOT NULL
);
"""


def load_to_sqlite(
    db_path: Path,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    sales_fact: pd.DataFrame,
) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    orders = sales_fact[
        ["order_id", "customer_id", "product_id", "order_date", "quantity", "discount", "payment_method", "order_status"]
    ].copy()
    daily = (
        sales_fact.groupby("order_date", as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            gross_revenue=("gross_revenue", "sum"),
            net_revenue=("net_revenue", "sum"),
            discount_amount=("discount_amount", "sum"),
        )
        .round(2)
    )
    product_summary = (
        sales_fact.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            units_sold=("quantity", "sum"),
            net_revenue=("net_revenue", "sum"),
        )
        .round(2)
    )
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
        customers.to_sql("customers", connection, if_exists="append", index=False)
        products.to_sql("products", connection, if_exists="append", index=False)
        orders.to_sql("orders", connection, if_exists="append", index=False)
        sales_fact.to_sql("sales_fact", connection, if_exists="append", index=False)
        daily.to_sql("daily_sales_summary", connection, if_exists="append", index=False)
        product_summary.to_sql("product_sales_summary", connection, if_exists="append", index=False)
    logger.info(
        "database_loaded path=%s customers=%d products=%d facts=%d",
        db_path,
        len(customers),
        len(products),
        len(sales_fact),
    )
    return len(sales_fact)


def database_counts(db_path: Path) -> dict[str, int]:
    with sqlite3.connect(db_path) as connection:
        return {
            table: int(pd.read_sql_query(f"SELECT COUNT(*) AS count FROM {table}", connection)["count"].iloc[0])
            for table in ("customers", "products", "orders", "sales_fact")
        }