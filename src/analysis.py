from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed"
)

FIGURES_DIR = PROJECT_ROOT / "figures"


def load_business_data() -> pd.DataFrame:
    """Load the business-ready inventory dataset."""

    file_path = (
        PROCESSED_DATA_DIR
        / "inventory_business_ready.csv"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Business dataset not found: {file_path}"
        )

    return pd.read_csv(file_path)


def create_inventory_by_warehouse(
    df: pd.DataFrame,
) -> None:
    """Create total inventory by warehouse."""

    summary = (
        df.groupby("warehouse_name")[
            "on_hand_quantity"
        ]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(10, 6))

    summary.plot(
        kind="bar",
    )

    plt.title("Total Inventory by Warehouse")
    plt.xlabel("Warehouse")
    plt.ylabel("On-Hand Quantity")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR / "inventory_by_warehouse.png",
        dpi=150,
    )

    plt.close()


def create_revenue_by_warehouse(
    df: pd.DataFrame,
) -> None:
    """Create total sales revenue by warehouse."""

    summary = (
        df.groupby("warehouse_name")[
            "sales_revenue"
        ]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(10, 6))

    summary.plot(
        kind="bar",
    )

    plt.title("Sales Revenue by Warehouse")
    plt.xlabel("Warehouse")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR / "revenue_by_warehouse.png",
        dpi=150,
    )

    plt.close()


def create_inventory_status(
    df: pd.DataFrame,
) -> None:
    """Create inventory status distribution."""

    summary = (
        df["inventory_status"]
        .value_counts()
    )

    plt.figure(figsize=(8, 6))

    summary.plot(
        kind="bar",
    )

    plt.title("Inventory Status Distribution")
    plt.xlabel("Inventory Status")
    plt.ylabel("SKU-Warehouse Count")
    plt.xticks(rotation=0)
    plt.tight_layout()

    plt.savefig(
        FIGURES_DIR / "inventory_status.png",
        dpi=150,
    )

    plt.close()


def print_business_insights(
    df: pd.DataFrame,
) -> None:
    """Print basic business insights."""

    warehouse_inventory = (
        df.groupby("warehouse_name")[
            "on_hand_quantity"
        ]
        .sum()
        .sort_values(ascending=False)
    )

    warehouse_revenue = (
        df.groupby("warehouse_name")[
            "sales_revenue"
        ]
        .sum()
        .sort_values(ascending=False)
    )

    status_counts = (
        df["inventory_status"]
        .value_counts()
    )

    print("\n=== BUSINESS INSIGHTS ===")

    print(
        "\nHighest inventory warehouse:"
    )
    print(
        warehouse_inventory.index[0],
        f"({warehouse_inventory.iloc[0]:,.0f} units)",
    )

    print(
        "\nHighest revenue warehouse:"
    )
    print(
        warehouse_revenue.index[0],
        f"({warehouse_revenue.iloc[0]:,.2f})",
    )

    print(
        "\nInventory status counts:"
    )
    print(status_counts)


def main() -> None:
    print("Loading business-ready data...")

    df = load_business_data()

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Creating figures...")

    create_inventory_by_warehouse(df)
    create_revenue_by_warehouse(df)
    create_inventory_status(df)

    print_business_insights(df)

    print("\n=== ANALYSIS COMPLETE ===")
    print(
        f"Figures saved to: {FIGURES_DIR}"
    )


if __name__ == "__main__":
    main()