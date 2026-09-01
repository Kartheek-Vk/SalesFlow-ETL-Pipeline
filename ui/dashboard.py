"""Simple presentation layer for the SalesFlow ETL outputs."""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from salesflow.analytics import queries
from salesflow.config import DB_PATH, REPORTS_DIR, REJECTED_DIR


@st.cache_data
def load_dashboard_data(db_path: str, report_path: str, rejected_dir: str) -> dict[str, object]:
    """Load all dashboard data from the pipeline's persisted outputs."""
    database = Path(db_path)
    report_file = Path(report_path)
    if not database.exists():
        return {"ready": False, "reason": "Run python run_pipeline.py before starting the dashboard."}
    if not report_file.exists():
        return {"ready": False, "reason": "The quality report is missing. Run the pipeline again."}

    import json

    quality = json.loads(report_file.read_text(encoding="utf-8"))
    rejected_frames = []
    for csv_path in sorted(Path(rejected_dir).glob("*.csv")):
        frame = pd.read_csv(csv_path)
        frame.insert(0, "dataset", csv_path.stem)
        rejected_frames.append(frame)
    rejected = pd.concat(rejected_frames, ignore_index=True) if rejected_frames else pd.DataFrame()
    return {
        "ready": True,
        "summary": queries.summary(database),
        "category": pd.DataFrame(queries.revenue_by_category(database)),
        "state": pd.DataFrame(queries.revenue_by_state(database)),
        "monthly": pd.DataFrame(queries.monthly_revenue(database)),
        "products": pd.DataFrame(queries.top_products(database)),
        "quality": quality,
        "rejected": rejected,
    }


def _currency(value: float) -> str:
    return f"₹{value:,.2f}"


def render_dashboard(data: dict[str, object]) -> None:
    summary = data["summary"]
    quality = data["quality"]

    st.title("SalesFlow ETL")
    st.subheader("Sales Data Engineering & Analytics Dashboard")
    st.write(
        "Demonstration dashboard for an end-to-end Python and PySpark data engineering pipeline."
    )
    st.caption("Reading processed facts and quality outputs from the SalesFlow SQLite warehouse.")

    st.header("Key performance indicators")
    kpis = [
        ("Total Revenue", _currency(summary["total_revenue"])),
        ("Total Orders", f"{summary['total_orders']:,}"),
        ("Average Order Value", _currency(summary["average_order_value"])),
        ("Total Discount", _currency(summary["total_discount"])),
        ("Cancelled Orders", f"{summary['cancelled_orders']:,}"),
        ("Unique Customers", f"{summary['unique_customers']:,}"),
    ]
    columns = st.columns(3)
    for index, (label, value) in enumerate(kpis):
        columns[index % 3].metric(label, value)

    st.header("Sales analytics")
    category_col, state_col = st.columns(2)
    with category_col:
        st.subheader("Revenue by category")
        category = data["category"].set_index("category")
        st.bar_chart(category, y="revenue")
    with state_col:
        st.subheader("Revenue by state")
        state = data["state"].set_index("state")
        st.bar_chart(state, y="revenue")

    month_col, product_col = st.columns(2)
    with month_col:
        st.subheader("Monthly revenue")
        monthly = data["monthly"].set_index("month")
        st.line_chart(monthly, y="revenue")
    with product_col:
        st.subheader("Top 10 products")
        products = data["products"].set_index("product_name")[["net_revenue"]]
        st.bar_chart(products)

    st.header("Data quality")
    quality_columns = st.columns(4)
    quality_columns[0].metric("Input records", f"{quality['total_records']:,}")
    quality_columns[1].metric("Valid records", f"{quality['valid_records']:,}")
    quality_columns[2].metric("Rejected records", f"{quality['rejected_records']:,}")
    quality_columns[3].metric("Quality score", f"{quality['quality_score']:.1f}%")
    st.caption(f"Validated at {quality['validation_timestamp']}")
    with st.expander("Rejected records and reasons"):
        rejected = data["rejected"]
        if rejected.empty:
            st.success("No rejected records.")
        else:
            st.dataframe(rejected, width="stretch", hide_index=True)

    st.header("Pipeline information")
    st.info(
        "Data source: generated e-commerce CSV files → Pandas validation → "
        "PySpark joins and calculations → SQLite warehouse → SQL analytics"
    )
    info = pd.DataFrame(
        [
            ["Data source", "data/raw/*.csv"],
            ["ETL stages", "Ingestion, validation, cleaning, PySpark, quality, load"],
            ["Database", str(DB_PATH.relative_to(Path.cwd())) if DB_PATH.is_relative_to(Path.cwd()) else str(DB_PATH)],
            ["Spark processing", "Completed in local PySpark mode"],
            ["Last pipeline execution", quality["validation_timestamp"]],
        ],
        columns=["Stage", "Details"],
    )
    st.table(info)


def main() -> None:
    st.set_page_config(page_title="SalesFlow ETL", page_icon="📊", layout="wide")
    data = load_dashboard_data(str(DB_PATH), str(REPORTS_DIR / "quality_report.json"), str(REJECTED_DIR))
    if not data["ready"]:
        st.title("SalesFlow ETL")
        st.warning(data["reason"])
        st.code("python scripts/generate_data.py\npython run_pipeline.py")
        st.stop()
    render_dashboard(data)


if __name__ == "__main__":
    main()