import pandas as pd

from salesflow.transformation.spark_transform import transform_with_spark


def _frames():
    return {
        "customers": pd.DataFrame([{
            "customer_id": "C1", "customer_name": "A", "age": 25, "gender": "F",
            "city": "X", "state": "Y", "signup_date": "2024-01-01",
        }]),
        "products": pd.DataFrame([{
            "product_id": "P1", "product_name": "Widget", "category": "Home", "unit_price": 100.0,
        }]),
        "orders": pd.DataFrame([{
            "order_id": "O1", "customer_id": "C1", "product_id": "P1", "order_date": "2024-01-01",
            "quantity": 2, "discount": 0.1, "payment_method": "Card", "order_status": "delivered",
        }]),
    }


def test_spark_join_produces_one_fact_row():
    result = transform_with_spark(_frames())
    assert result.transformed_records == 1
    assert result.sales_fact.iloc[0]["product_name"] == "Widget"


def test_revenue_calculation_uses_quantity_and_price():
    fact = transform_with_spark(_frames()).sales_fact.iloc[0]
    assert fact["gross_revenue"] == 200
    assert fact["discount_amount"] == 20
    assert fact["net_revenue"] == 180


def test_cancelled_order_has_zero_net_revenue():
    frames = _frames()
    frames["orders"].loc[0, "order_status"] = "cancelled"
    fact = transform_with_spark(frames).sales_fact.iloc[0]
    assert fact["gross_revenue"] == 200
    assert fact["net_revenue"] == 0