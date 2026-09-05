"""Phase 0/1: pull the four raw CSVs off disk exactly as they arrived."""
from pathlib import Path
import pandas as pd

from .logging_config import get_logger

log = get_logger()

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def read_csv(filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename
    df = pd.read_csv(path)
    log.info(f"EXTRACT {filename}: read {len(df)} rows, {len(df.columns)} columns from {path}")
    return df


def read_all() -> dict:
    return {
        "sales": read_csv("sales.csv"),
        "orders": read_csv("orders.csv"),
        "inventory": read_csv("inventory.csv"),
        "warehouses": read_csv("warehouses.csv"),
    }
