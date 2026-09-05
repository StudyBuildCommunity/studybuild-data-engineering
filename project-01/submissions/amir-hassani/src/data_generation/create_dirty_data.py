from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DIRTY_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed" / "dirty"
)


def load_raw_data(file_name: str) -> pd.DataFrame:
    """Load a raw CSV dataset."""

    file_path = RAW_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Raw file not found: {file_path}"
        )

    return pd.read_csv(file_path)


def create_dirty_sales(
    sales: pd.DataFrame,
) -> pd.DataFrame:
    """Create controlled data-quality issues in sales."""

    dirty = sales.copy()

    # 1. Duplicate primary key
    duplicate_row = dirty.iloc[[0]].copy()

    dirty = pd.concat(
        [dirty, duplicate_row],
        ignore_index=True,
    )

    # 2. Unknown warehouse ID
    dirty.loc[1, "warehouse_id"] = "WH999"

    # 3. Missing critical SKU
    dirty.loc[2, "sku"] = None

    # 4. Non-numeric quantity
    dirty["quantity"] = dirty["quantity"].astype("object")
    dirty.loc[3, "quantity"] = "INVALID"

    return dirty


def create_dirty_inventory(
    inventory: pd.DataFrame,
) -> pd.DataFrame:
    """Create controlled data-quality issues in inventory."""

    dirty = inventory.copy()

    # 1. Negative inventory
    dirty.loc[0, "on_hand_quantity"] = -100

    # 2. Unknown warehouse ID
    dirty.loc[1, "warehouse_id"] = "WH999"

    # 3. Duplicate inventory grain
    duplicate_row = dirty.iloc[[2]].copy()

    dirty = pd.concat(
        [dirty, duplicate_row],
        ignore_index=True,
    )

    return dirty


def create_dirty_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Create controlled data-quality issues in orders."""

    dirty = orders.copy()

    # 1. Missing critical warehouse ID
    dirty.loc[0, "warehouse_id"] = None

    # 2. Non-numeric ordered quantity
    dirty["ordered_quantity"] = (
        dirty["ordered_quantity"].astype("object")
    )
    dirty.loc[1, "ordered_quantity"] = "INVALID"

    return dirty


def create_dirty_data() -> None:
    """Generate intentionally corrupted datasets."""

    DIRTY_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading raw datasets...")

    sales = load_raw_data("sales.csv")
    orders = load_raw_data("orders.csv")
    inventory = load_raw_data("inventory.csv")
    warehouses = load_raw_data("warehouses.csv")

    print("Creating dirty sales...")
    dirty_sales = create_dirty_sales(sales)

    print("Creating dirty orders...")
    dirty_orders = create_dirty_orders(orders)

    print("Creating dirty inventory...")
    dirty_inventory = create_dirty_inventory(inventory)

    dirty_sales.to_csv(
        DIRTY_DATA_DIR / "sales.csv",
        index=False,
    )

    dirty_orders.to_csv(
        DIRTY_DATA_DIR / "orders.csv",
        index=False,
    )

    dirty_inventory.to_csv(
        DIRTY_DATA_DIR / "inventory.csv",
        index=False,
    )

    warehouses.to_csv(
        DIRTY_DATA_DIR / "warehouses.csv",
        index=False,
    )

    print("\nDirty data generation complete.")

    print(f"Sales rows: {len(dirty_sales):,}")
    print(f"Orders rows: {len(dirty_orders):,}")
    print(f"Inventory rows: {len(dirty_inventory):,}")
    print(f"Warehouse rows: {len(warehouses):,}")


if __name__ == "__main__":
    create_dirty_data()
