from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def extract_csv(
    file_name: str,
    data_dir: Path = RAW_DATA_DIR,
) -> pd.DataFrame:
    """Extract a CSV file into a pandas DataFrame."""

    file_path = data_dir / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {file_path}"
        )

    return pd.read_csv(file_path)


def extract_all(
    data_dir: Path = RAW_DATA_DIR,
) -> dict[str, pd.DataFrame]:
    """Extract all raw project datasets."""

    return {
        "sales": extract_csv("sales.csv", data_dir),
        "orders": extract_csv("orders.csv", data_dir),
        "inventory": extract_csv("inventory.csv", data_dir),
        "warehouses": extract_csv("warehouses.csv", data_dir),
        "products": extract_csv("products.csv", data_dir),
    }


if __name__ == "__main__":
    datasets = extract_all()

    print("=== EXTRACT RESULT ===")

    for name, df in datasets.items():
        print(f"{name}: {len(df):,} rows")