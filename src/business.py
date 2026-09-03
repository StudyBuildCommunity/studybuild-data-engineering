from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def create_business_ready_inventory(
    inventory: pd.DataFrame,
    sales: pd.DataFrame,
    orders: pd.DataFrame,
    products: pd.DataFrame,
    warehouses: pd.DataFrame,
) -> pd.DataFrame:
    """Create a business-ready inventory table."""

    inventory_summary = (
        inventory
        .groupby(
            ["sku", "warehouse_id"],
            as_index=False,
        )
        .agg(
            on_hand_quantity=(
                "on_hand_quantity",
                "sum",
            )
        )
    )

    sales_summary = (
        sales
        .groupby(
            ["sku", "warehouse_id"],
            as_index=False,
        )
        .agg(
            sales_quantity=(
                "quantity",
                "sum",
            ),
            sales_revenue=(
                "revenue",
                "sum",
            ),
        )
    )

    pending_orders = orders[
        orders["status"] == "pending"
    ]

    order_summary = (
        pending_orders
        .groupby(
            ["sku", "warehouse_id"],
            as_index=False,
        )
        .agg(
            pending_order_quantity=(
                "ordered_quantity",
                "sum",
            )
        )
    )

    result = inventory_summary.merge(
        sales_summary,
        on=["sku", "warehouse_id"],
        how="left",
    )

    result = result.merge(
        order_summary,
        on=["sku", "warehouse_id"],
        how="left",
    )

    result = result.merge(
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

    result[
        [
            "sales_quantity",
            "sales_revenue",
            "pending_order_quantity",
        ]
    ] = result[
        [
            "sales_quantity",
            "sales_revenue",
            "pending_order_quantity",
        ]
    ].fillna(0)

    result["inventory_after_pending_orders"] = (
        result["on_hand_quantity"]
        - result["pending_order_quantity"]
    )

    result["inventory_status"] = "sufficient"

    result.loc[
        result["inventory_after_pending_orders"] <= 0,
        "inventory_status",
    ] = "critical"

    result.loc[
        (
            result["inventory_after_pending_orders"] > 0
        )
        & (
            result["inventory_after_pending_orders"]
            < result["pending_order_quantity"]
        ),
        "inventory_status",
    ] = "low"

    return result[
        [
            "sku",
            "product_id",
            "warehouse_id",
            "warehouse_name",
            "city",
            "region",
            "on_hand_quantity",
            "sales_quantity",
            "sales_revenue",
            "pending_order_quantity",
            "inventory_after_pending_orders",
            "inventory_status",
        ]
    ]


def main() -> None:
    print("Loading processed datasets...")

    inventory = pd.read_csv(
        PROCESSED_DATA_DIR / "inventory.csv"
    )

    sales = pd.read_csv(
        PROCESSED_DATA_DIR / "sales.csv"
    )

    orders = pd.read_csv(
        PROCESSED_DATA_DIR / "orders.csv"
    )

    products = pd.read_csv(
        PROCESSED_DATA_DIR / "products.csv"
    )

    warehouses = pd.read_csv(
        PROCESSED_DATA_DIR / "warehouses.csv"
    )

    print("Creating business-ready inventory table...")

    result = create_business_ready_inventory(
        inventory,
        sales,
        orders,
        products,
        warehouses,
    )

    output_path = (
        PROCESSED_DATA_DIR
        / "inventory_business_ready.csv"
    )

    result.to_csv(
        output_path,
        index=False,
    )

    print("\n=== BUSINESS TABLE RESULT ===")
    print(
        f"Rows: {len(result):,}"
    )
    print(
        f"Columns: {len(result.columns)}"
    )
    print(
        f"Output: {output_path}"
    )

    print("\nInventory status:")
    print(
        result["inventory_status"]
        .value_counts()
    )


if __name__ == "__main__":
    main()