from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

DIRTY_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed" / "dirty"
)

REQUIRED_COLUMNS = {
    "sales": [
        "sale_id",
        "sale_date",
        "sku",
        "warehouse_id",
        "quantity",
        "unit_price",
        "revenue",
    ],
    "orders": [
        "order_id",
        "order_date",
        "sku",
        "warehouse_id",
        "ordered_quantity",
        "status",
    ],
    "inventory": [
        "snapshot_date",
        "sku",
        "warehouse_id",
        "on_hand_quantity",
    ],
    "warehouses": [
        "warehouse_id",
        "warehouse_name",
        "city",
        "region",
    ],
}


def load_csv(
    file_name: str,
    data_dir: Path,
) -> pd.DataFrame:
    """Load a CSV file from the specified data directory."""

    file_path = data_dir / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    return pd.read_csv(file_path)


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    table_name: str,
) -> list[str]:
    """Check that all required columns exist."""

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        return [
            f"{table_name}: missing columns: "
            f"{missing_columns}"
        ]

    return []


def validate_no_nulls(
    df: pd.DataFrame,
    columns: list[str],
    table_name: str,
) -> list[str]:
    """Check critical columns for NULL values."""

    errors = []

    for column in columns:
        null_count = df[column].isna().sum()

        if null_count > 0:
            errors.append(
                f"{table_name}.{column}: "
                f"{null_count} null values"
            )

    return errors


def validate_unique_key(
    df: pd.DataFrame,
    column: str,
    table_name: str,
) -> list[str]:
    """Check that a column contains unique values."""

    duplicate_count = df[column].duplicated().sum()

    if duplicate_count > 0:
        return [
            f"{table_name}.{column}: "
            f"{duplicate_count} duplicate values"
        ]

    return []


def validate_inventory_grain(
    df: pd.DataFrame,
) -> list[str]:
    """Check inventory grain uniqueness."""

    key_columns = [
        "snapshot_date",
        "sku",
        "warehouse_id",
    ]

    duplicate_count = df.duplicated(
        subset=key_columns
    ).sum()

    if duplicate_count > 0:
        return [
            "inventory: "
            f"{duplicate_count} duplicate grain records"
        ]

    return []


def validate_non_negative(
    df: pd.DataFrame,
    column: str,
    table_name: str,
) -> list[str]:
    """Check that a numeric column is not negative."""

    invalid_count = (df[column] < 0).sum()

    if invalid_count > 0:
        return [
            f"{table_name}.{column}: "
            f"{invalid_count} negative values"
        ]

    return []

def validate_numeric(
    df: pd.DataFrame,
    column: str,
    table_name: str,
) -> list[str]:
    """Check that a column contains only numeric values."""

    numeric_values = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    invalid_count = numeric_values.isna().sum()

    if invalid_count > 0:
        return [
            f"{table_name}.{column}: "
            f"{invalid_count} non-numeric values"
        ]

    return []

def validate_warehouse_ids(
    df: pd.DataFrame,
    warehouse_ids: set[str],
    table_name: str,
) -> list[str]:
    """Check that warehouse IDs exist in the warehouse master."""

    invalid_count = (
        ~df["warehouse_id"].isin(warehouse_ids)
    ).sum()

    if invalid_count > 0:
        return [
            f"{table_name}.warehouse_id: "
            f"{invalid_count} unknown warehouse IDs"
        ]

    return []


def validate_sales_revenue(
    df: pd.DataFrame,
) -> list[str]:
    """Check that revenue equals quantity multiplied by unit price."""

    quantity = pd.to_numeric(
        df["quantity"],
        errors="coerce",
    )

    unit_price = pd.to_numeric(
        df["unit_price"],
        errors="coerce",
    )

    valid_rows = (
        quantity.notna()
        & unit_price.notna()
        & df["revenue"].notna()
    )

    expected_revenue = (
        quantity[valid_rows]
        * unit_price[valid_rows]
    ).round(2)

    mismatch_count = (
        df.loc[valid_rows, "revenue"]
        != expected_revenue
    ).sum()

    if mismatch_count > 0:
        return [
            "sales.revenue: "
            f"{mismatch_count} calculation mismatches"
        ]

    return []


def validate_all(
    data_dir: Path = RAW_DATA_DIR,
) -> bool:
    """Run all validation rules."""

    print("Loading raw datasets...")

    sales = load_csv("sales.csv", data_dir)
    orders = load_csv("orders.csv", data_dir)
    inventory = load_csv("inventory.csv", data_dir)
    warehouses = load_csv("warehouses.csv", data_dir)

    errors = []

    print("Running schema validation...")

    errors += validate_required_columns(
        sales,
        REQUIRED_COLUMNS["sales"],
        "sales",
    )

    errors += validate_required_columns(
        orders,
        REQUIRED_COLUMNS["orders"],
        "orders",
    )

    errors += validate_required_columns(
        inventory,
        REQUIRED_COLUMNS["inventory"],
        "inventory",
    )

    errors += validate_required_columns(
        warehouses,
        REQUIRED_COLUMNS["warehouses"],
        "warehouses",
    )

    print("Running NULL validation...")

    errors += validate_no_nulls(
        sales,
        [
            "sale_id",
            "sale_date",
            "sku",
            "warehouse_id",
            "quantity",
            "unit_price",
        ],
        "sales",
    )

    errors += validate_no_nulls(
        orders,
        [
            "order_id",
            "order_date",
            "sku",
            "warehouse_id",
            "ordered_quantity",
        ],
        "orders",
    )

    errors += validate_no_nulls(
        inventory,
        [
            "snapshot_date",
            "sku",
            "warehouse_id",
            "on_hand_quantity",
        ],
        "inventory",
    )

    errors += validate_no_nulls(
        warehouses,
        [
            "warehouse_id",
            "warehouse_name",
        ],
        "warehouses",
    )

    print("Running uniqueness validation...")

    errors += validate_unique_key(
        sales,
        "sale_id",
        "sales",
    )

    errors += validate_unique_key(
        orders,
        "order_id",
        "orders",
    )

    errors += validate_unique_key(
        warehouses,
        "warehouse_id",
        "warehouses",
    )

    errors += validate_inventory_grain(
        inventory
    )

    print("Running numeric validation...")

    errors += validate_numeric(
        sales,
        "quantity",
        "sales",
    )

    errors += validate_numeric(
        sales,
        "unit_price",
        "sales",
    )

    errors += validate_numeric(
        orders,
        "ordered_quantity",
        "orders",
    )

    errors += validate_numeric(
        inventory,
        "on_hand_quantity",
        "inventory",
    )

    errors += validate_non_negative(
        inventory,
        "on_hand_quantity",
        "inventory",
    )

    print("Running warehouse validation...")

    warehouse_ids = set(
        warehouses["warehouse_id"]
    )

    errors += validate_warehouse_ids(
        sales,
        warehouse_ids,
        "sales",
    )

    errors += validate_warehouse_ids(
        orders,
        warehouse_ids,
        "orders",
    )

    errors += validate_warehouse_ids(
        inventory,
        warehouse_ids,
        "inventory",
    )

    print("Running revenue validation...")

    errors += validate_sales_revenue(
        sales
    )

    print("\n=== VALIDATION RESULT ===")

    if errors:
        print("FAILED")

        for error in errors:
            print(f"- {error}")

        return False

    print("PASSED")
    print("All validation checks passed.")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate ETL source datasets."
    )

    parser.add_argument(
        "--dirty",
        action="store_true",
        help="Validate intentionally corrupted datasets.",
    )

    args = parser.parse_args()

    data_dir = (
        DIRTY_DATA_DIR
        if args.dirty
        else RAW_DATA_DIR
    )

    success = validate_all(data_dir)

    if not success:
        raise SystemExit(1)