from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SOURCE_FILE = RAW_DATA_DIR / "online_retail_II.xlsx"

RANDOM_SEED = 42

WAREHOUSES = [
    {
        "warehouse_id": "WH001",
        "warehouse_name": "Central Warehouse",
        "city": "London",
        "region": "South East",
    },
    {
        "warehouse_id": "WH002",
        "warehouse_name": "North Warehouse",
        "city": "Manchester",
        "region": "North West",
    },
    {
        "warehouse_id": "WH003",
        "warehouse_name": "Midlands Warehouse",
        "city": "Birmingham",
        "region": "West Midlands",
    },
    {
        "warehouse_id": "WH004",
        "warehouse_name": "Scotland Warehouse",
        "city": "Glasgow",
        "region": "Scotland",
    },
    {
        "warehouse_id": "WH005",
        "warehouse_name": "Wales Warehouse",
        "city": "Cardiff",
        "region": "Wales",
    },
]


def load_source_data() -> pd.DataFrame:
    """Load the public UCI Online Retail II dataset."""

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {SOURCE_FILE}"
        )

    excel = pd.ExcelFile(SOURCE_FILE)

    frames = []

    for sheet_name in excel.sheet_names:
        frame = pd.read_excel(
            SOURCE_FILE,
            sheet_name=sheet_name,
        )
        frames.append(frame)

    return pd.concat(
        frames,
        ignore_index=True,
    )


def prepare_sales_data(
    source_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Create the sales raw source from UCI transaction data."""

    df = source_df.copy()

    df = df.rename(
        columns={
            "Invoice": "invoice",
            "StockCode": "sku",
            "InvoiceDate": "sale_date",
            "Quantity": "quantity",
            "Price": "unit_price",
        }
    )

    # Keep rows with a usable SKU and transaction date.
    df = df[
        df["sku"].notna()
        & df["sale_date"].notna()
    ].copy()

    # Select a reproducible subset.
    sample_size = min(100_000, len(df))

    df = df.sample(
        n=sample_size,
        random_state=RANDOM_SEED,
    ).reset_index(drop=True)

    # Simulate warehouse assignment.
    warehouse_ids = [
        warehouse["warehouse_id"]
        for warehouse in WAREHOUSES
    ]

    df["warehouse_id"] = rng.choice(
        warehouse_ids,
        size=len(df),
    )

    df["sale_id"] = [
        f"SALE{i:07d}"
        for i in range(1, len(df) + 1)
    ]

    df["revenue"] = (
        df["quantity"] * df["unit_price"]
    ).round(2)

    return df[
        [
            "sale_id",
            "sale_date",
            "sku",
            "warehouse_id",
            "quantity",
            "unit_price",
            "revenue",
        ]
    ]


def create_warehouses() -> pd.DataFrame:
    """Create the simulated warehouse master data."""

    return pd.DataFrame(WAREHOUSES)


def create_orders(
    sales_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Create simulated customer orders from sales activity."""

    order_count = min(30_000, len(sales_df))

    source = sales_df.sample(
        n=order_count,
        random_state=RANDOM_SEED + 1,
    ).copy()

    orders = pd.DataFrame(
        {
            "order_id": [
                f"ORD{i:07d}"
                for i in range(1, len(source) + 1)
            ],
            "order_date": source["sale_date"].values,
            "sku": source["sku"].values,
            "warehouse_id": source["warehouse_id"].values,
            "ordered_quantity": (
                source["quantity"]
                .abs()
                .clip(lower=1)
                .values
            ),
            "status": rng.choice(
                [
                    "pending",
                    "completed",
                    "cancelled",
                ],
                size=len(source),
                p=[0.15, 0.75, 0.10],
            ),
        }
    )

    return orders


def create_inventory(
    sales_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Create simulated warehouse inventory snapshots."""

    skus = sales_df["sku"].dropna().unique()

    records = []

    snapshot_dates = pd.date_range(
        start=sales_df["sale_date"].min().normalize(),
        end=sales_df["sale_date"].max().normalize(),
        periods=4,
    )

    warehouse_ids = [
        warehouse["warehouse_id"]
        for warehouse in WAREHOUSES
    ]

    for snapshot_date in snapshot_dates:
        selected_skus = rng.choice(
            skus,
            size=min(500, len(skus)),
            replace=False,
        )

        for sku in selected_skus:
            for warehouse_id in warehouse_ids:
                quantity = int(
                    rng.integers(
                        low=0,
                        high=1000,
                    )
                )

                records.append(
                    {
                        "snapshot_date": snapshot_date,
                        "sku": sku,
                        "warehouse_id": warehouse_id,
                        "on_hand_quantity": quantity,
                    }
                )

    return pd.DataFrame(records)


def generate_raw_data() -> None:
    """Generate all raw project data sources."""

    print("Loading UCI source dataset...")

    source_df = load_source_data()

    print(
        f"Source rows: {len(source_df):,}"
    )

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    print("Generating sales.csv...")

    sales_df = prepare_sales_data(
        source_df,
        rng,
    )

    print("Generating warehouses.csv...")

    warehouses_df = create_warehouses()

    print("Generating orders.csv...")

    orders_df = create_orders(
        sales_df,
        rng,
    )

    print("Generating inventory.csv...")

    inventory_df = create_inventory(
        sales_df,
        rng,
    )

    sales_df.to_csv(
        RAW_DATA_DIR / "sales.csv",
        index=False,
    )

    orders_df.to_csv(
        RAW_DATA_DIR / "orders.csv",
        index=False,
    )

    inventory_df.to_csv(
        RAW_DATA_DIR / "inventory.csv",
        index=False,
    )

    warehouses_df.to_csv(
        RAW_DATA_DIR / "warehouses.csv",
        index=False,
    )

    print("\nGeneration complete.")
    print(
        f"Sales rows: {len(sales_df):,}"
    )
    print(
        f"Orders rows: {len(orders_df):,}"
    )
    print(
        f"Inventory rows: {len(inventory_df):,}"
    )
    print(
        f"Warehouse rows: {len(warehouses_df):,}"
    )


if __name__ == "__main__":
    generate_raw_data()