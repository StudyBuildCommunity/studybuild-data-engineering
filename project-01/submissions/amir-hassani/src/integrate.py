from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def integrate_sales(
    sales: pd.DataFrame,
    products: pd.DataFrame,
    warehouses: pd.DataFrame,
) -> pd.DataFrame:
    """Integrate sales with product and warehouse master data."""

    result = sales.merge(
        products,
        on="sku",
        how="left",
        validate="many_to_one",
    )

    result = result.merge(
        warehouses[
            [
                "warehouse_id",
                "warehouse_name",
                "city",
                "region",
            ]
        ],
        on="warehouse_id",
        how="left",
        validate="many_to_one",
    )

    return result


def integrate_orders(
    orders: pd.DataFrame,
    products: pd.DataFrame,
    warehouses: pd.DataFrame,
) -> pd.DataFrame:
    """Integrate orders with product and warehouse master data."""

    result = orders.merge(
        products,
        on="sku",
        how="left",
        validate="many_to_one",
    )

    result = result.merge(
        warehouses,
        on="warehouse_id",
        how="left",
        validate="many_to_one",
    )

    return result


def create_inventory_summary(
    inventory: pd.DataFrame,
) -> pd.DataFrame:
    """Create a warehouse-level inventory summary."""

    summary = (
        inventory
        .groupby(
            "warehouse_id",
            as_index=False,
        )
        .agg(
            total_on_hand_quantity=(
                "on_hand_quantity",
                "sum",
            ),
            sku_count=(
                "sku",
                "nunique",
            ),
        )
    )

    return summary


if __name__ == "__main__":
    print("Loading transformed datasets...")

    sales = pd.read_csv(
        PROCESSED_DATA_DIR / "sales.csv"
    )
    orders = pd.read_csv(
        PROCESSED_DATA_DIR / "orders.csv"
    )
    inventory = pd.read_csv(
        PROCESSED_DATA_DIR / "inventory.csv"
    )
    products = pd.read_csv(
        PROCESSED_DATA_DIR / "products.csv"
    )
    warehouses = pd.read_csv(
        PROCESSED_DATA_DIR / "warehouses.csv"
    )

    print("Integrating sales...")
    integrated_sales = integrate_sales(
        sales,
        products,
        warehouses,
    )

    print("Integrating orders...")
    integrated_orders = integrate_orders(
        orders,
        products,
        warehouses,
    )

    print("Creating inventory summary...")
    inventory_summary = create_inventory_summary(
        inventory
    )

    integrated_sales.to_csv(
        PROCESSED_DATA_DIR / "integrated_sales.csv",
        index=False,
    )

    integrated_orders.to_csv(
        PROCESSED_DATA_DIR / "integrated_orders.csv",
        index=False,
    )

    inventory_summary.to_csv(
        PROCESSED_DATA_DIR / "inventory_summary.csv",
        index=False,
    )

    print("\n=== INTEGRATION RESULT ===")
    print(
        f"Integrated sales: "
        f"{len(integrated_sales):,} rows"
    )
    print(
        f"Integrated orders: "
        f"{len(integrated_orders):,} rows"
    )
    print(
        f"Inventory summary: "
        f"{len(inventory_summary):,} rows"
    )