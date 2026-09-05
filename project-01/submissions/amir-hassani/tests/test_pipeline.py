from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def test_sales_has_expected_columns():
    df = pd.read_csv(
        PROCESSED_DATA_DIR / "sales.csv"
    )

    expected_columns = {
        "sale_id",
        "sale_date",
        "sku",
        "warehouse_id",
        "quantity",
        "unit_price",
        "revenue",
    }

    assert expected_columns.issubset(
        df.columns
    )


def test_sales_ids_are_unique():
    df = pd.read_csv(
        PROCESSED_DATA_DIR / "sales.csv"
    )

    assert df["sale_id"].is_unique


def test_inventory_has_no_negative_stock():
    df = pd.read_csv(
        PROCESSED_DATA_DIR / "inventory.csv"
    )

    assert (
        df["on_hand_quantity"] >= 0
    ).all()


def test_inventory_grain_is_unique():
    df = pd.read_csv(
        PROCESSED_DATA_DIR / "inventory.csv"
    )

    assert not df.duplicated(
        subset=[
            "snapshot_date",
            "sku",
            "warehouse_id",
        ]
    ).any()


def test_business_table_has_expected_columns():
    df = pd.read_csv(
        PROCESSED_DATA_DIR
        / "inventory_business_ready.csv"
    )

    expected_columns = {
        "sku",
        "product_id",
        "warehouse_id",
        "warehouse_name",
        "on_hand_quantity",
        "sales_quantity",
        "sales_revenue",
        "pending_order_quantity",
        "inventory_after_pending_orders",
        "inventory_status",
    }

    assert expected_columns.issubset(
        df.columns
    )


def test_business_table_has_valid_status():
    df = pd.read_csv(
        PROCESSED_DATA_DIR
        / "inventory_business_ready.csv"
    )

    valid_statuses = {
        "sufficient",
        "low",
        "critical",
    }

    assert set(
        df["inventory_status"].unique()
    ).issubset(valid_statuses)