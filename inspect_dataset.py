from pathlib import Path

import pandas as pd


DATASET_PATH = Path("data/raw/online_retail_II.xlsx")


def inspect_dataset(file_path: Path) -> None:
    """Load and inspect the raw UCI Online Retail II dataset."""

    print("=" * 60)
    print("DATASET INSPECTION")
    print("=" * 60)

    print(f"\nFile: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    print("\nLoading dataset...")

    df = pd.read_excel(file_path)

    print("\n--- Shape ---")
    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]}")

    print("\n--- Columns ---")
    for column in df.columns:
        print(f"- {column}")

    print("\n--- Data Types ---")
    print(df.dtypes)

    print("\n--- Missing Values ---")
    missing = df.isna().sum()

    for column, count in missing.items():
        percentage = (count / len(df)) * 100
        print(f"{column}: {count:,} ({percentage:.2f}%)")

    print("\n--- Duplicate Rows ---")
    duplicates = df.duplicated().sum()
    print(f"Duplicates: {duplicates:,}")

    print("\n--- First 5 Rows ---")
    print(df.head().to_string())

    print("\n--- Numeric Summary ---")
    print(df.describe().to_string())

    print("\n" + "=" * 60)
    print("INSPECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    inspect_dataset(DATASET_PATH)