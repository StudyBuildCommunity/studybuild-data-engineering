from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def transform_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize sales data."""

    result = df.copy()

    result["sale_date"] = pd.to_datetime(
        result["sale_date"],
        errors="coerce",
    )

    result["quantity"] = pd.to_numeric(
        result["quantity"],
        errors="coerce",
    )

    result["unit_price"] = pd.to_numeric(
        result["unit_price"],
        errors="coerce",
    )

    result["revenue"] = (
        result["quantity"] * result["unit_price"]
    ).round(2)

    result = result.dropna(
        subset=[
            "sale_id",
            "sale_date",
            "sku",
            "warehouse_id",
            "quantity",
            "unit_price",
        ]
    )

    result = result[result["quantity"] >= 0]
    result = result[result["unit_price"] >= 0]

    result = result.drop_duplicates(
        subset=["sale_id"]
    )

    return result


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize orders data."""

    result = df.copy()

    result["order_date"] = pd.to_datetime(
        result["order_date"],
        errors="coerce",
    )

    result["ordered_quantity"] = pd.to_numeric(
        result["ordered_quantity"],
        errors="coerce",
    )

    result = result.dropna(
        subset=[
            "order_id",
            "order_date",
            "sku",
            "warehouse_id",
            "ordered_quantity",
        ]
    )

    result = result[result["ordered_quantity"] > 0]

    result = result.drop_duplicates(
        subset=["order_id"]
    )

    return result


def transform_inventory(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize inventory data."""

    result = df.copy()

    result["snapshot_date"] = pd.to_datetime(
        result["snapshot_date"],
        errors="coerce",
    )

    result["on_hand_quantity"] = pd.to_numeric(
        result["on_hand_quantity"],
        errors="coerce",
    )

    result = result.dropna(
        subset=[
            "snapshot_date",
            "sku",
            "warehouse_id",
            "on_hand_quantity",
        ]
    )

    result = result[result["on_hand_quantity"] >= 0]

    result = result.drop_duplicates(
        subset=[
            "snapshot_date",
            "sku",
            "warehouse_id",
        ]
    )

    return result


def transform_warehouses(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Clean warehouse master data."""

    result = df.copy()

    result = result.dropna(
        subset=[
            "warehouse_id",
            "warehouse_name",
        ]
    )

    result = result.drop_duplicates(
        subset=["warehouse_id"]
    )

    return result


def transform_products(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Clean product master data."""

    result = df.copy()

    result = result.dropna(
        subset=["product_id", "sku"]
    )

    result = result.drop_duplicates(
        subset=["sku"]
    )

    return result


def transform_all(
    datasets: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Transform all extracted datasets."""

    return {
        "sales": transform_sales(datasets["sales"]),
        "orders": transform_orders(datasets["orders"]),
        "inventory": transform_inventory(datasets["inventory"]),
        "warehouses": transform_warehouses(
            datasets["warehouses"]
        ),
        "products": transform_products(
            datasets["products"]
        ),
    }


if __name__ == "__main__":
    from extract import extract_all

    datasets = extract_all()
    transformed = transform_all(datasets)

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=== TRANSFORM RESULT ===")

    for name, df in transformed.items():
        output_path = (
            PROCESSED_DATA_DIR / f"{name}.csv"
        )

        df.to_csv(
            output_path,
            index=False,
        )

        print(
            f"{name}: "
            f"{len(df):,} rows"
        )