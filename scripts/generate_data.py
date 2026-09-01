"""Generate a small, reproducible e-commerce dataset with intentional defects."""

from datetime import date, timedelta
import csv
import random
import sys
from pathlib import Path

# Allow both `python scripts/generate_data.py` and
# `python -m scripts.generate_data` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from salesflow.config import RAW_DIR, ensure_directories


def generate_dataset(seed: int = 42) -> dict[str, int]:
    random.seed(seed)
    ensure_directories()
    states = ["Karnataka", "Maharashtra", "Telangana", "Tamil Nadu", "Delhi", "Gujarat"]
    cities = ["Bengaluru", "Mumbai", "Hyderabad", "Chennai", "New Delhi", "Ahmedabad"]
    categories = {
        "Electronics": ["Wireless Headphones", "Mechanical Keyboard", "Smart Watch"],
        "Home": ["Desk Lamp", "Coffee Maker", "Air Purifier"],
        "Fitness": ["Yoga Mat", "Resistance Bands", "Running Shoes"],
    }
    customers = []
    for index in range(1, 31):
        customers.append({
            "customer_id": f"C{index:04d}",
            "customer_name": f"Customer {index:02d}",
            "age": random.randint(19, 58),
            "gender": random.choice(["F", "M", "Non-binary"]),
            "city": cities[index % len(cities)],
            "state": states[index % len(states)],
            "signup_date": (date(2023, 1, 1) + timedelta(days=index * 9)).isoformat(),
        })
    products = []
    product_index = 1
    for category, names in categories.items():
        for name in names:
            products.append({
                "product_id": f"P{product_index:04d}",
                "product_name": name,
                "category": category,
                "unit_price": round(random.uniform(18, 260), 2),
            })
            product_index += 1

    orders = []
    for index in range(1, 121):
        orders.append({
            "order_id": f"O{index:05d}",
            "customer_id": random.choice(customers)["customer_id"],
            "product_id": random.choice(products)["product_id"],
            "order_date": (date(2024, 1, 1) + timedelta(days=random.randint(0, 364))).isoformat(),
            "quantity": random.randint(1, 4),
            "discount": random.choice([0, 0.05, 0.10, 0.15, 0.20]),
            "payment_method": random.choice(["UPI", "Card", "Net Banking", "Cash on Delivery"]),
            "order_status": random.choices(
                ["delivered", "pending", "cancelled", "returned"],
                weights=[75, 10, 8, 7],
            )[0],
        })

    # Defects are intentionally mixed into otherwise believable data so the
    # quality layer has something concrete to detect during an interview.
    customers.extend([
        {**customers[0], "customer_name": "Duplicate Customer"},
        {**customers[1], "customer_id": "C9999", "age": 8},
        {**customers[2], "customer_id": "C9998", "signup_date": "not-a-date"},
        {**customers[3], "customer_id": "C9997", "customer_name": None},
    ])
    products.extend([
        {**products[0], "product_id": "P0001", "product_name": "Duplicate Product"},
        {**products[1], "product_id": "P9999", "unit_price": -20},
        {**products[2], "product_id": "P9998", "product_name": None},
    ])
    orders.extend([
        {**orders[0], "order_id": "O00001"},
        {**orders[1], "order_id": "O99999", "quantity": -2},
        {**orders[2], "order_id": "O99998", "discount": 1.5},
        {**orders[3], "order_id": "O99997", "order_date": "2024-99-99"},
        {**orders[4], "order_id": "O99996", "customer_id": "C4040"},
        {**orders[5], "order_id": "O99995", "product_id": "P4040"},
        {**orders[6], "order_id": "O99994", "payment_method": None},
    ])

    datasets = {"customers": customers, "products": products, "orders": orders}
    for name, rows in datasets.items():
        with (RAW_DIR / f"{name}.csv").open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    return {name: len(rows) for name, rows in datasets.items()}


if __name__ == "__main__":
    print(generate_dataset())