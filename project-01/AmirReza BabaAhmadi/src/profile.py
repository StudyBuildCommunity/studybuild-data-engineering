"""
Phase 1 (Q1: Can we trust the raw data?): full profile of every raw file.

profile_dataframe() reports, per file: row/column counts, column names and
dtypes, % missing per column, exact duplicate rows, duplicate key values,
unparseable dates, and negative values in quantity-like columns. Everything
is logged and also returned as a dict so it can feed straight into the
written report and the README quality summary (single source of truth).
"""
import pandas as pd

from .logging_config import get_logger

log = get_logger()


def _std(colname: str) -> str:
    """Same normalization as transform.standardize_column_names, so callers
    can name columns by their *clean* name (e.g. 'sku') even though the raw
    file may spell it ' SKU' or 'Sku' -- exactly the messiness we're profiling."""
    import re
    s = colname.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s


def _loose(colname: str) -> str:
    """Looser than _std: also drops underscores, so 'warehouse_id' and
    'WarehouseID' resolve to the same key regardless of separator style."""
    return _std(colname).replace("_", "")


def _resolve(df: pd.DataFrame, target: str):
    std_map = {_std(c): c for c in df.columns}
    hit = std_map.get(_std(target))
    if hit:
        return hit
    loose_map = {_loose(c): c for c in df.columns}
    return loose_map.get(_loose(target))


def profile_dataframe(df: pd.DataFrame, name: str, key_cols=None, date_cols=None, qty_cols=None,
                       sku_col=None, wh_col=None, valid_warehouse_ids=None) -> dict:
    key_cols = [_resolve(df, c) or c for c in (key_cols or [])]
    date_cols = [_resolve(df, c) or c for c in (date_cols or [])]
    qty_cols = [_resolve(df, c) or c for c in (qty_cols or [])]
    sku_col = _resolve(df, sku_col) if sku_col else None
    wh_col = _resolve(df, wh_col) if wh_col else None

    log.info(f"=== PROFILE {name} ===")
    log.info(f"rows={len(df)}, columns={len(df.columns)}")
    log.info(f"columns: {list(df.columns)}")
    log.info("dtypes:\n" + df.dtypes.to_string())

    null_pct = df.isna().mean().mul(100).round(2)
    log.info("null % per column:\n" + null_pct.to_string())

    n_exact_dupes = int(df.duplicated().sum())
    log.info(f"exact duplicate rows = {n_exact_dupes}")

    dup_keys = {}
    for kc in key_cols:
        if kc in df.columns:
            n = int(df.duplicated(subset=[kc]).sum())
            dup_keys[kc] = n
            log.info(f"duplicate values in key column '{kc}' = {n}")

    bad_dates = {}
    for dc in date_cols:
        if dc in df.columns:
            parsed = pd.to_datetime(df[dc], errors="coerce")
            n_bad = int(parsed.isna().sum())
            bad_dates[dc] = n_bad
            log.info(f"unparseable dates in '{dc}' = {n_bad}")

    negatives = {}
    for qc in qty_cols:
        if qc in df.columns:
            numeric = pd.to_numeric(df[qc], errors="coerce")
            n_neg = int((numeric < 0).sum())
            negatives[qc] = n_neg
            log.info(f"negative values in '{qc}' = {n_neg}")

    n_blank_sku = None
    if sku_col and sku_col in df.columns:
        n_blank_sku = int(
            df[sku_col].isna().pipe(lambda isna: isna | (df[sku_col].astype(str).str.strip() == "")).sum()
        )
        log.info(f"blank/missing SKU in '{sku_col}' = {n_blank_sku}")

    n_orphan_wh = None
    if wh_col and wh_col in df.columns and valid_warehouse_ids is not None:
        normalized_ids = (
            df[wh_col].astype(str).str.strip().str.upper()
            .str.replace(" ", "", regex=False)
            .str.replace("_", "-", regex=False)
        )
        n_orphan_wh = int((~normalized_ids.isin(valid_warehouse_ids) & normalized_ids.notna() & (normalized_ids != "NAN")).sum())
        log.info(f"warehouse_id values in '{wh_col}' not present in warehouses master = {n_orphan_wh}")

    result = {
        "name": name,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": list(df.columns),
        "null_pct": null_pct.to_dict(),
        "n_exact_dupes": n_exact_dupes,
        "dup_keys": dup_keys,
        "bad_dates": bad_dates,
        "negatives": negatives,
        "n_blank_sku": n_blank_sku,
        "n_orphan_warehouse": n_orphan_wh,
    }
    return result
