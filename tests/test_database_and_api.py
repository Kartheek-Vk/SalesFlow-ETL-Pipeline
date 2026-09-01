import sqlite3

from fastapi.testclient import TestClient

from api.main import app
from salesflow.analytics.queries import summary
from salesflow.config import REJECTED_DIR, REPORTS_DIR
from ui.dashboard import load_dashboard_data


def test_database_contains_expected_tables(database_path):
    with sqlite3.connect(database_path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"customers", "products", "orders", "sales_fact", "daily_sales_summary", "product_sales_summary"} <= tables


def test_database_fact_rows_are_loaded(database_path, pipeline_result):
    with sqlite3.connect(database_path) as connection:
        facts = connection.execute("SELECT COUNT(*) FROM sales_fact").fetchone()[0]
    assert facts == pipeline_result["records_loaded"]
    assert facts > 100


def test_summary_is_real_database_data(database_path):
    result = summary(database_path)
    assert result["total_orders"] > 0
    assert result["total_revenue"] > 0


def test_api_health_endpoint():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_analytics_endpoint(pipeline_result):
    response = TestClient(app).get("/analytics/summary")
    assert response.status_code == 200
    assert response.json()["total_orders"] == pipeline_result["database_counts"]["sales_fact"]


def test_api_prefixed_health_endpoint():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_top_products_endpoint(pipeline_result):
    response = TestClient(app).get("/analytics/top-products?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_quality_report_endpoint():
    response = TestClient(app).get("/quality/report")
    assert response.status_code == 200
    assert response.json()["rejected_records"] > 0


def test_dashboard_loader_reads_real_outputs(database_path, pipeline_result):
    data = load_dashboard_data(str(database_path), str(REPORTS_DIR / "quality_report.json"), str(REJECTED_DIR))
    assert data["ready"] is True
    assert data["summary"]["total_revenue"] == summary(database_path)["total_revenue"]
    assert data["quality"]["rejected_records"] == pipeline_result["records_rejected"]


def test_dashboard_loader_includes_rejection_reasons(database_path):
    data = load_dashboard_data(str(database_path), str(REPORTS_DIR / "quality_report.json"), str(REJECTED_DIR))
    rejected = data["rejected"]
    assert not rejected.empty
    assert {"dataset", "rejection_reasons"} <= set(rejected.columns)