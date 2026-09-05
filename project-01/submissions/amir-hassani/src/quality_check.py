from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_csv(
    directory: Path,
    file_name: str,
) -> pd.DataFrame:
    """Load a CSV file."""

    return pd.read_csv(directory / file_name)


def check_row_counts() -> bool:
    """Check expected row counts across the ETL pipeline."""

    raw_sales = load_csv(
        RAW_DATA_DIR,
        "sales.csv",
    )

    raw_orders = load_csv(
        RAW_DATA_DIR,
        "orders.csv",
    )

    raw_inventory = load_csv(
        RAW_DATA_DIR,
        "inventory.csv",
    )

    clean_sales = load_csv(
        PROCESSED_DATA_DIR,
        "sales.csv",
    )

    clean_orders = load_csv(
        PROCESSED_DATA_DIR,
        "orders.csv",
    )

    clean_inventory = load_csv(
        PROCESSED_DATA_DIR,
        "inventory.csv",
    )

    integrated_sales = load_csv(
        PROCESSED_DATA_DIR,
        "integrated_sales.csv",
    )

    integrated_orders = load_csv(
        PROCESSED_DATA_DIR,
        "integrated_orders.csv",
    )

    checks = {
        "orders preserved": (
            len(raw_orders) == len(clean_orders)
            == len(integrated_orders)
        ),
        "inventory preserved": (
            len(raw_inventory) == len(clean_inventory)
        ),
        "sales integration preserved": (
            len(clean_sales) == len(integrated_sales)
        ),
        "sales cleaning reduced rows": (
            len(clean_sales) <= len(raw_sales)
        ),
    }

    print("\n=== ROW COUNT CHECK ===")

    all_passed = True

    for name, passed in checks.items():
        status = "PASS" if passed else "FAIL"

        print(
            f"{status}: {name}"
        )

        if not passed:
            all_passed = False

    return all_passed


def check_sales_revenue() -> bool:
    """Check sales revenue calculation."""

    sales = load_csv(
        PROCESSED_DATA_DIR,
        "sales.csv",
    )

    expected_revenue = (
        sales["quantity"]
        * sales["unit_price"]
    ).round(2)

    mismatches = (
        sales["revenue"] != expected_revenue
    ).sum()

    passed = mismatches == 0

    print("\n=== REVENUE CHECK ===")
    print(
        f"{'PASS' if passed else 'FAIL'}: "
        f"{mismatches} revenue mismatches"
    )

    return passed


def check_integrated_sales() -> bool:
    """Check integrated sales for missing master data."""

    sales = load_csv(
        PROCESSED_DATA_DIR,
        "integrated_sales.csv",
    )

    checks = {
        "missing product_id": (
            sales["product_id"].isna().sum()
        ),
        "missing warehouse_name": (
            sales["warehouse_name"].isna().sum()
        ),
    }

    print("\n=== INTEGRATION CHECK ===")

    passed = True

    for name, count in checks.items():
        check_passed = count == 0

        print(
            f"{'PASS' if check_passed else 'FAIL'}: "
            f"{name}: {count}"
        )

        if not check_passed:
            passed = False

    return passed


def main() -> None:
    print("=== DATA QUALITY CHECK ===")

    results = [
        check_row_counts(),
        check_sales_revenue(),
        check_integrated_sales(),
    ]

    print("\n=== QUALITY RESULT ===")

    if all(results):
        print("PASSED")
        print("All quality checks passed.")
    else:
        print("FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()