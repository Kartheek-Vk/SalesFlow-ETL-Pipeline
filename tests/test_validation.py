import pandas as pd

from salesflow.validation.rules import validate_customers, validate_orders, validate_products


def test_customer_validation_rejects_impossible_age():
    result = validate_customers(pd.DataFrame([{
        "customer_id": "C1", "customer_name": "A", "age": "8", "gender": "F",
        "city": "X", "state": "Y", "signup_date": "2024-01-01",
    }]))
    assert len(result.valid) == 0
    assert "impossible_age" in result.rejected.iloc[0]["rejection_reasons"]


def test_product_validation_rejects_negative_price():
    result = validate_products(pd.DataFrame([{
        "product_id": "P1", "product_name": "A", "category": "Home", "unit_price": "-4",
    }]))
    assert len(result.rejected) == 1
    assert "invalid_price" in result.rejected.iloc[0]["rejection_reasons"]


def test_order_validation_detects_foreign_keys():
    result = validate_orders(pd.DataFrame([{
        "order_id": "O1", "customer_id": "C404", "product_id": "P404",
        "order_date": "2024-01-01", "quantity": "1", "discount": "0.1",
        "payment_method": "Card", "order_status": "delivered",
    }]), {"C1"}, {"P1"})
    assert {"invalid_customer_reference", "invalid_product_reference"} <= set(result.rejected.iloc[0]["rejection_reasons"].split("; "))


def test_duplicate_ids_are_rejected():
    frame = pd.DataFrame([
        {"product_id": "P1", "product_name": "A", "category": "Home", "unit_price": "4"},
        {"product_id": "P1", "product_name": "B", "category": "Home", "unit_price": "5"},
    ])
    result = validate_products(frame)
    assert len(result.rejected) == 2
    assert all("duplicate_product_id" in reason for reason in result.rejected["rejection_reasons"])


def test_invalid_discount_is_rejected():
    frame = pd.DataFrame([{
        "order_id": "O1", "customer_id": "C1", "product_id": "P1",
        "order_date": "2024-01-01", "quantity": "1", "discount": "2",
        "payment_method": "Card", "order_status": "delivered",
    }])
    result = validate_orders(frame, {"C1"}, {"P1"})
    assert "invalid_discount" in result.rejected.iloc[0]["rejection_reasons"]


def test_invalid_date_is_rejected():
    frame = pd.DataFrame([{
        "customer_id": "C1", "customer_name": "A", "age": "25", "gender": "F",
        "city": "X", "state": "Y", "signup_date": "not-a-date",
    }])
    result = validate_customers(frame)
    assert "invalid_signup_date" in result.rejected.iloc[0]["rejection_reasons"]