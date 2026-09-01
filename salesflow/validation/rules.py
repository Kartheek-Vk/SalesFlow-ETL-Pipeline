from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from salesflow.logging_config import configure_logging

logger = configure_logging()


@dataclass
class ValidationResult:
    valid: pd.DataFrame
    rejected: pd.DataFrame
    checks: list[dict[str, object]]


def _check(
    name: str,
    total: int,
    failures: int,
    details: str,
) -> dict[str, object]:
    return {
        "check": name,
        "total_records": total,
        "failed_records": failures,
        "status": "passed" if failures == 0 else "failed",
        "details": details,
    }


def _finalize(
    frame: pd.DataFrame,
    invalid_masks: Iterable[tuple[str, pd.Series]],
    checks: list[dict[str, object]],
) -> ValidationResult:
    frame = frame.reset_index(drop=True).copy()
    reasons: dict[object, list[str]] = {index: [] for index in frame.index}
    for reason, mask in invalid_masks:
        count = int(mask.fillna(False).sum())
        checks.append(_check(reason, len(frame), count, f"{count} row(s) failed"))
        for index in frame.index[mask.fillna(False)]:
            reasons[index].append(reason)

    rejected_mask = pd.Series(
        [bool(reasons[index]) for index in frame.index], index=frame.index
    )
    rejected = frame.loc[rejected_mask].copy()
    if not rejected.empty:
        rejected["rejection_reasons"] = [
            "; ".join(reasons[index]) for index in rejected.index
        ]
    valid = frame.loc[~rejected_mask].copy()
    logger.info(
        "validation_complete total=%d valid=%d rejected=%d",
        len(frame),
        len(valid),
        len(rejected),
    )
    return ValidationResult(valid.reset_index(drop=True), rejected.reset_index(drop=True), checks)


def validate_customers(frame: pd.DataFrame) -> ValidationResult:
    data = frame.reset_index(drop=True).copy()
    data["age_num"] = pd.to_numeric(data["age"], errors="coerce")
    data["signup_date_parsed"] = pd.to_datetime(data["signup_date"], errors="coerce")
    duplicate_id = data["customer_id"].duplicated(keep=False) | data["customer_id"].isna()
    masks = [
        ("null_customer_fields", data[["customer_id", "customer_name", "city", "state"]].isna().any(axis=1)),
        ("duplicate_customer_id", duplicate_id),
        ("impossible_age", data["age_num"].isna() | ~data["age_num"].between(13, 100)),
        ("invalid_signup_date", data["signup_date_parsed"].isna()),
    ]
    result = _finalize(data, masks, [])
    result.valid = result.valid.assign(
        age=result.valid["age_num"].astype(int),
        signup_date=result.valid["signup_date_parsed"].dt.strftime("%Y-%m-%d"),
    ).drop(columns=["age_num", "signup_date_parsed"])
    return result


def validate_products(frame: pd.DataFrame) -> ValidationResult:
    data = frame.reset_index(drop=True).copy()
    data["unit_price_num"] = pd.to_numeric(data["unit_price"], errors="coerce")
    duplicate_id = data["product_id"].duplicated(keep=False) | data["product_id"].isna()
    masks = [
        ("null_product_fields", data[["product_id", "product_name", "category"]].isna().any(axis=1)),
        ("duplicate_product_id", duplicate_id),
        ("invalid_price", data["unit_price_num"].isna() | (data["unit_price_num"] <= 0)),
    ]
    result = _finalize(data, masks, [])
    result.valid = result.valid.assign(
        unit_price=result.valid["unit_price_num"].astype(float).round(2)
    ).drop(columns=["unit_price_num"])
    return result


def validate_orders(
    frame: pd.DataFrame, customer_ids: set[str], product_ids: set[str]
) -> ValidationResult:
    data = frame.reset_index(drop=True).copy()
    data["quantity_num"] = pd.to_numeric(data["quantity"], errors="coerce")
    data["discount_num"] = pd.to_numeric(data["discount"], errors="coerce")
    data["order_date_parsed"] = pd.to_datetime(data["order_date"], errors="coerce")
    masks = [
        ("null_order_fields", data[["order_id", "customer_id", "product_id", "payment_method", "order_status"]].isna().any(axis=1)),
        ("duplicate_order_id", data["order_id"].duplicated(keep=False) | data["order_id"].isna()),
        ("invalid_quantity", data["quantity_num"].isna() | (data["quantity_num"] <= 0)),
        ("invalid_discount", data["discount_num"].isna() | ~data["discount_num"].between(0, 1)),
        ("invalid_order_date", data["order_date_parsed"].isna()),
        ("invalid_customer_reference", ~data["customer_id"].isin(customer_ids)),
        ("invalid_product_reference", ~data["product_id"].isin(product_ids)),
        ("invalid_order_status", ~data["order_status"].isin({"delivered", "pending", "cancelled", "returned"})),
    ]
    result = _finalize(data, masks, [])
    result.valid = result.valid.assign(
        quantity=result.valid["quantity_num"].astype(int),
        discount=result.valid["discount_num"].astype(float).round(4),
        order_date=result.valid["order_date_parsed"].dt.strftime("%Y-%m-%d"),
    ).drop(columns=["quantity_num", "discount_num", "order_date_parsed"])
    return result


def write_rejections(results: dict[str, ValidationResult], rejected_dir: Path) -> int:
    rejected_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, result in results.items():
        path = rejected_dir / f"{name}.csv"
        rejected = result.rejected.drop(
            columns=[
                column
                for column in result.rejected.columns
                if column.endswith("_num") or column.endswith("_parsed")
            ],
            errors="ignore",
        )
        rejected.to_csv(path, index=False)
        total += len(rejected)
        logger.info("rejected_records_written file=%s records=%d", path, len(result.rejected))
    return total