from pathlib import Path

import pandas as pd


DATASET_PATH = Path("data/raw/online_retail_II.xlsx")


def inspect_sheet(file_path: Path, sheet_name: str) -> None:
    """Inspect one sheet from the raw UCI Online Retail II dataset."""

    print("\n" + "=" * 70)
    print(f"SHEET: {sheet_name}")
    print("=" * 70)

    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
    )

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

    print("\n--- Negative Quantity ---")
    negative_quantity = (df["Quantity"] < 0).sum()
    print(f"Negative quantity rows: {negative_quantity:,}")

    print("\n--- Negative Price ---")
    negative_price = (df["Price"] < 0).sum()
    print(f"Negative price rows: {negative_price:,}")

    print("\n--- Unique Values ---")
    print(f"Unique invoices: {df['Invoice'].nunique():,}")
    print(f"Unique SKUs: {df['StockCode'].nunique():,}")
    print(f"Unique customers: {df['Customer ID'].nunique():,}")
    print(f"Unique countries: {df['Country'].nunique():,}")

    print("\n--- Invoice Prefixes ---")
    invoice_text = df["Invoice"].astype(str)

    prefixes = invoice_text.str[0].value_counts()

    print(prefixes)

    print("\n--- Quantity Statistics ---")
    print(df["Quantity"].describe())

    print("\n--- Price Statistics ---")
    print(df["Price"].describe())

    print("\n--- Top 10 SKUs ---")
    print(df["StockCode"].value_counts().head(10))

    print("\n--- Top 10 Countries ---")
    print(df["Country"].value_counts().head(10))


def inspect_dataset(file_path: Path) -> None:
    """Inspect all sheets in the Excel dataset."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    print("=" * 70)
    print("UCI ONLINE RETAIL II - DATASET PROFILING")
    print("=" * 70)

    excel_file = pd.ExcelFile(file_path)

    print("\nAvailable sheets:")
    for sheet in excel_file.sheet_names:
        print(f"- {sheet}")

    for sheet in excel_file.sheet_names:
        inspect_sheet(file_path, sheet)

    print("\n" + "=" * 70)
    print("PROFILING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    inspect_dataset(DATASET_PATH)