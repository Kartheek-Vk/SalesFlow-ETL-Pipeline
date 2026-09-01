import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


def _query(db_path: Path, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sqlite3.connect(db_path) as connection:
        frame = pd.read_sql_query(sql, connection, params=params)
    return frame.to_dict(orient="records")


def summary(db_path: Path) -> dict[str, float | int]:
    with sqlite3.connect(db_path) as connection:
        row = pd.read_sql_query(
            """
            SELECT
                COALESCE(SUM(net_revenue), 0) AS total_revenue,
                COUNT(DISTINCT order_id) AS total_orders,
                COALESCE(AVG(net_revenue), 0) AS average_order_value,
                COALESCE(SUM(discount_amount), 0) AS total_discount,
                SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
                COUNT(DISTINCT customer_id) AS unique_customers
            FROM sales_fact
            """,
            connection,
        ).iloc[0]
    return {key: round(float(value), 2) if key not in {"total_orders", "cancelled_orders", "unique_customers"} else int(value) for key, value in row.to_dict().items()}


def top_products(db_path: Path, limit: int = 10) -> list[dict[str, Any]]:
    return _query(db_path, "SELECT * FROM product_sales_summary ORDER BY net_revenue DESC LIMIT ?", (limit,))


def revenue_by_category(db_path: Path) -> list[dict[str, Any]]:
    return _query(db_path, "SELECT category, ROUND(SUM(net_revenue), 2) AS revenue FROM sales_fact GROUP BY category ORDER BY revenue DESC")


def revenue_by_state(db_path: Path) -> list[dict[str, Any]]:
    return _query(db_path, "SELECT state, ROUND(SUM(net_revenue), 2) AS revenue FROM sales_fact GROUP BY state ORDER BY revenue DESC")


def monthly_revenue(db_path: Path) -> list[dict[str, Any]]:
    return _query(db_path, "SELECT order_month AS month, ROUND(SUM(net_revenue), 2) AS revenue FROM sales_fact GROUP BY order_month ORDER BY month")


def daily_sales(db_path: Path) -> list[dict[str, Any]]:
    return _query(db_path, "SELECT * FROM daily_sales_summary ORDER BY order_date")


def repeat_customers(db_path: Path) -> list[dict[str, Any]]:
    return _query(db_path, "SELECT customer_id, customer_name, COUNT(DISTINCT order_id) AS orders, ROUND(SUM(net_revenue), 2) AS revenue FROM sales_fact GROUP BY customer_id, customer_name HAVING orders > 1 ORDER BY orders DESC")


def cancelled_orders(db_path: Path) -> list[dict[str, Any]]:
    return _query(db_path, "SELECT order_id, order_date, customer_name, product_name, gross_revenue FROM sales_fact WHERE order_status = 'cancelled' ORDER BY order_date DESC")


def discount_impact(db_path: Path) -> dict[str, float]:
    return _query(db_path, "SELECT ROUND(SUM(discount_amount), 2) AS discount_amount, ROUND(SUM(gross_revenue), 2) AS gross_revenue, ROUND(SUM(net_revenue), 2) AS net_revenue FROM sales_fact")[0]


def purchase_frequency(db_path: Path) -> list[dict[str, Any]]:
    return _query(db_path, "SELECT orders, COUNT(*) AS customers FROM (SELECT customer_id, COUNT(DISTINCT order_id) AS orders FROM sales_fact GROUP BY customer_id) GROUP BY orders ORDER BY orders")