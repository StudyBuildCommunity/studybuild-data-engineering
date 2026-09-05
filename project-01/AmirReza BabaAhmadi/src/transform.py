"""
Phase 3 (Q3: can files be standardized automatically?) + Phase 4 (Q4: safe
integration) + Phase 5 (Q5/Q6: business-ready view and operational flags).

All reusable transforms live here and are applied the same way to every
raw file, in the fixed order the roadmap specifies:
  1. read raw  2. standardize column names  3. convert types (dates/numbers)
  4. run validation rules  5. drop/flag by rule  6. drop exact duplicates

Written in a method-chaining style throughout (`.pipe()` / `.assign()` /
`.query()`), so each cleaning pipeline reads top-to-bottom as one pass over
the data rather than a series of `df = df.something()` reassignments.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .logging_config import get_logger

log = get_logger()


# ---------------------------------------------------------------------------
# Reusable atomic transforms -- each takes a DataFrame and returns one, so
# every one of them is a drop-in step for `.pipe()`.
# ---------------------------------------------------------------------------
def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """lower_snake_case every column: strip, collapse spaces, drop stray punctuation."""
    return df.rename(columns=lambda c: re.sub(r"[^a-z0-9_]", "", re.sub(r"\s+", "_", c.strip().lower())))


def parse_dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.assign(**{c: pd.to_datetime(df[c], errors="coerce") for c in cols if c in df.columns})


def to_numeric_safe(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.assign(**{c: pd.to_numeric(df[c], errors="coerce") for c in cols if c in df.columns})


def clean_text(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.assign(**{
        c: df[c].astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
        for c in cols if c in df.columns
    })


def normalize_ids(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.assign(**{
        c: (
            df[c].astype(str).str.strip().str.upper()
            .str.replace(" ", "", regex=False)
            .str.replace("_", "-", regex=False)
            .replace({"NAN": np.nan})
        )
        for c in cols if c in df.columns
    })


def drop_exact_duplicates(df: pd.DataFrame, name: str) -> pd.DataFrame:
    deduped = df.drop_duplicates()
    log.info(f"'{name}': dropped {len(df) - len(deduped)} exact duplicate rows")
    return deduped


def enforce_warehouse_fk(df: pd.DataFrame, name: str, valid_ids) -> pd.DataFrame:
    """R2: warehouse_id must exist in the warehouses master table. Rows that
    fail are quarantined (not silently dropped) to data/processed/quarantine_*.csv
    so nothing disappears without a trace."""
    if valid_ids is None or "warehouse_id" not in df.columns:
        return df

    is_known = df["warehouse_id"].isin(valid_ids)
    if (~is_known).any():
        n_bad = int((~is_known).sum())
        q_dir = Path(__file__).resolve().parent.parent / "data" / "processed"
        q_dir.mkdir(parents=True, exist_ok=True)
        df.loc[~is_known].to_csv(q_dir / f"quarantine_{name}_bad_warehouse_id.csv", index=False)
        log.warning(f"'{name}': quarantined {n_bad} rows with warehouse_id not in warehouses master "
                    f"(R2) -> data/processed/quarantine_{name}_bad_warehouse_id.csv")

    return df.loc[is_known]


# ---------------------------------------------------------------------------
# Per-file cleaning pipelines -- one chain each, same six-step shape:
# standardize -> normalize/parse/type-convert -> enforce R2 -> validate ->
# drop exact duplicates -> de-duplicate on the primary key.
# ---------------------------------------------------------------------------
def clean_warehouses(raw: pd.DataFrame) -> pd.DataFrame:
    return (
        raw
        .pipe(standardize_column_names)
        .pipe(normalize_ids, ["warehouse_id"])
        .assign(
            # proper nouns: trim whitespace only, keep original casing for display
            warehouse_name=lambda df_: df_["warehouse_name"].astype(str).str.strip(),
            city=lambda df_: df_["city"].astype(str).str.strip(),
            region=lambda df_: df_["region"].astype(str).str.strip(),
        )
        .pipe(drop_exact_duplicates, "warehouses")
        .dropna(subset=["warehouse_id"])
        .drop_duplicates(subset=["warehouse_id"])
        .reset_index(drop=True)
    )


def clean_sales(raw: pd.DataFrame, valid_warehouse_ids=None) -> pd.DataFrame:
    df = (
        raw
        .pipe(standardize_column_names)
        .rename(columns={"transactionid": "transaction_id", "saledate": "sale_date"})
        .pipe(normalize_ids, ["warehouse_id"])
        .pipe(parse_dates, ["sale_date"])
        .pipe(to_numeric_safe, ["quantity", "revenue"])
        .pipe(enforce_warehouse_fk, "sales", valid_warehouse_ids)
        .assign(sku=lambda df_: (
            df_["sku"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan, "None": np.nan})
        ))
    )

    log.info(
        f"validate sales: missing_sku={df['sku'].isna().sum()}, "
        f"missing_date={df['sale_date'].isna().sum()}, "
        f"missing_qty={df['quantity'].isna().sum()}, "
        f"negative_qty={(df['quantity'] < 0).sum()}"
    )

    # R1/R3/R4/R5: rows failing hard rules are dropped (with reason logged);
    # no explicit "return" flag exists in source data, so any negative
    # quantity is treated as a data-entry error, not a genuine return.
    before = len(df)
    df = (
        df
        .dropna(subset=["sku", "sale_date", "quantity", "warehouse_id"])
        .query("quantity >= 0")
    )
    log.info(f"'sales': {before - len(df)} rows dropped by validation rules (R1/R3/R4/R5)")

    return (
        df
        .pipe(drop_exact_duplicates, "sales")
        .drop_duplicates(subset=["transaction_id"], keep="first")
        .reset_index(drop=True)
    )


def clean_orders(raw: pd.DataFrame, valid_warehouse_ids=None) -> pd.DataFrame:
    valid_status = {"pending", "shipped", "cancelled", "delivered"}

    df = (
        raw
        .pipe(standardize_column_names)
        .pipe(normalize_ids, ["warehouseid"])
        .rename(columns={"warehouseid": "warehouse_id", "orderid": "order_id",
                          "orderdate": "order_date", "orderedqty": "ordered_qty"})
        .pipe(parse_dates, ["order_date"])
        .pipe(to_numeric_safe, ["ordered_qty"])
        .pipe(clean_text, ["status"])
        .pipe(enforce_warehouse_fk, "orders", valid_warehouse_ids)
        .assign(status=lambda df_: (
            df_["status"]
            .replace({"shiped": "shipped"})  # normalize the one typo seen in the source
            .where(lambda s: s.isin(valid_status))
        ))
    )

    before = len(df)
    df = (
        df
        .dropna(subset=["sku", "order_date", "ordered_qty", "warehouse_id", "status"])
        .query("ordered_qty >= 0")
    )
    log.info(f"'orders': {before - len(df)} rows dropped by validation rules (R1/R3/R4/R7)")

    return (
        df
        .pipe(drop_exact_duplicates, "orders")
        .drop_duplicates(subset=["order_id"], keep="first")
        .reset_index(drop=True)
    )


def clean_inventory(raw: pd.DataFrame, valid_warehouse_ids=None) -> pd.DataFrame:
    df = (
        raw
        .pipe(standardize_column_names)
        .rename(columns={"warehouseid": "warehouse_id", "snapshotdate": "snapshot_date",
                          "onhandqty": "on_hand_qty"})
        .pipe(normalize_ids, ["warehouse_id"])
        .pipe(parse_dates, ["snapshot_date"])
        .pipe(to_numeric_safe, ["on_hand_qty"])
        .pipe(enforce_warehouse_fk, "inventory", valid_warehouse_ids)
    )

    before = len(df)
    df = df.dropna(subset=["sku", "snapshot_date", "on_hand_qty", "warehouse_id"])
    n_negative = int((df["on_hand_qty"] < 0).sum())
    df = df.query("on_hand_qty >= 0")  # R6: negative on-hand is impossible -> floored out
    log.info(f"'inventory': {before - len(df)} rows dropped by validation rules "
             f"({n_negative} were negative on_hand_qty)")

    return (
        df
        .pipe(drop_exact_duplicates, "inventory")
        .sort_values("snapshot_date")
        .drop_duplicates(subset=["sku", "warehouse_id", "snapshot_date"], keep="last")
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Phase 4 (Q4): safe merges with row-count accounting
# ---------------------------------------------------------------------------
def safe_left_merge(left: pd.DataFrame, right: pd.DataFrame, on: list[str], name: str):
    before = len(left)
    merged = left.merge(right, on=on, how="left", indicator=True)
    unmatched = merged.query("_merge == 'left_only'")

    log.info(f"MERGE {name}: before={before}, after={len(merged)}, unmatched={len(unmatched)}")
    if len(merged) != before:
        log.warning(f"MERGE {name}: row count changed during merge ({before} -> {len(merged)}); "
                    f"check for duplicate keys on the right side (fan-out)")

    return merged.drop(columns="_merge"), unmatched


# ---------------------------------------------------------------------------
# Phase 5 (Q5): business-ready analytic table
# ---------------------------------------------------------------------------
def build_analytic_view(sales: pd.DataFrame, orders: pd.DataFrame,
                         inventory: pd.DataFrame, warehouses: pd.DataFrame,
                         as_of: pd.Timestamp, window_days: int = 30):
    window_start = as_of - pd.Timedelta(days=window_days)

    # latest on-hand snapshot per (sku, warehouse)
    latest_snap = (
        inventory
        .sort_values("snapshot_date")
        .drop_duplicates(subset=["sku", "warehouse_id"], keep="last")
        .loc[:, ["sku", "warehouse_id", "snapshot_date", "on_hand_qty"]]
        .rename(columns={"snapshot_date": "last_inventory_date"})
    )

    sales_agg = (
        sales
        .query("sale_date >= @window_start")
        .groupby(["sku", "warehouse_id"])
        .agg(recent_sales_qty=("quantity", "sum"), last_sale_date=("sale_date", "max"))
        .reset_index()
    )

    open_orders = orders.loc[
        (orders["order_date"] >= window_start) & (orders["status"] != "cancelled")
    ]
    orders_agg = (
        open_orders
        .groupby(["sku", "warehouse_id"])
        .agg(recent_orders_qty=("ordered_qty", "sum"), last_order_date=("order_date", "max"))
        .reset_index()
    )

    # universe = every sku/warehouse combo seen anywhere
    universe = (
        pd.concat([
            latest_snap.loc[:, ["sku", "warehouse_id"]],
            sales_agg.loc[:, ["sku", "warehouse_id"]],
            orders_agg.loc[:, ["sku", "warehouse_id"]],
        ])
        .drop_duplicates()
        .reset_index(drop=True)
    )

    unmatched_report = {}
    view, unmatched_report["inventory"] = safe_left_merge(
        universe, latest_snap, ["sku", "warehouse_id"], "analytic<-inventory")
    view, unmatched_report["sales"] = safe_left_merge(
        view, sales_agg, ["sku", "warehouse_id"], "analytic<-sales")
    view, unmatched_report["orders"] = safe_left_merge(
        view, orders_agg, ["sku", "warehouse_id"], "analytic<-orders")
    view, unmatched_report["warehouses"] = safe_left_merge(
        view, warehouses, ["warehouse_id"], "analytic<-warehouses")

    view = view.assign(
        on_hand_qty=lambda df_: df_["on_hand_qty"].fillna(0),
        recent_sales_qty=lambda df_: df_["recent_sales_qty"].fillna(0),
        recent_orders_qty=lambda df_: df_["recent_orders_qty"].fillna(0),
    )

    n_orphan_wh = view["warehouse_name"].isna().sum() if "warehouse_name" in view.columns else 0
    log.info(f"analytic view: {len(view)} sku/warehouse rows, "
             f"{int(n_orphan_wh)} with no matching warehouse master record")

    return view, unmatched_report


def add_operational_flags(view: pd.DataFrame) -> pd.DataFrame:
    df = view.assign(
        flag_stockout_risk=lambda df_: (df_["on_hand_qty"] <= 0) & (df_["recent_sales_qty"] > 0),               # F1
        flag_excess_inventory=lambda df_: (
            (df_["recent_sales_qty"] > 0) & (df_["on_hand_qty"] > 4 * df_["recent_sales_qty"])
        ),                                                                                                        # F2
        flag_order_backlog=lambda df_: (
            (df_["recent_orders_qty"] > 0) & (df_["recent_orders_qty"] > df_["on_hand_qty"])
        ),                                                                                                        # F3
        flag_dead_stock=lambda df_: (df_["recent_sales_qty"] == 0) & (df_["on_hand_qty"] > 0),                    # F4
    )

    for col in ("flag_stockout_risk", "flag_excess_inventory", "flag_order_backlog", "flag_dead_stock"):
        n = int(df[col].sum())
        log.info(f"FLAG {col}: {n} sku/warehouse rows ({n / len(df) * 100:.1f}%)")

    return df
