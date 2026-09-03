from pathlib import Path

import pandas as pd
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed"
)

DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "inventory.db"


TABLES = {
    "products": "products.csv",
    "warehouses": "warehouses.csv",
    "sales": "sales.csv",
    "orders": "orders.csv",
    "inventory": "inventory.csv",
    "integrated_sales": "integrated_sales.csv",
    "integrated_orders": "integrated_orders.csv",
    "inventory_summary": "inventory_summary.csv",
}


def load_table(
    connection: sqlite3.Connection,
    table_name: str,
    file_name: str,
) -> int:
    """Load one processed CSV into SQLite."""

    file_path = PROCESSED_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    df.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False,
    )

    return len(df)


def load_database() -> None:
    """Load all processed datasets into SQLite."""

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        print("Loading processed datasets...")

        for table_name, file_name in TABLES.items():
            row_count = load_table(
                connection,
                table_name,
                file_name,
            )

            print(
                f"{table_name}: "
                f"{row_count:,} rows"
            )

        connection.commit()

    finally:
        connection.close()

    print("\n=== LOAD RESULT ===")
    print(f"Database: {DATABASE_PATH}")


if __name__ == "__main__":
    load_database()