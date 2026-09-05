"""Phase 6 (Q7/Q8): load cleaned tables into SQLite and verify what landed."""
import sqlite3
from pathlib import Path
import pandas as pd

from .logging_config import get_logger

log = get_logger()

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "inventory.db"


def load_to_sqlite(tables: dict, db_path: Path = DB_PATH) -> dict:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    checks = {}
    try:
        for table_name, df in tables.items():
            n_before = len(df)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            n_loaded = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            ok = n_before == n_loaded
            checks[table_name] = {"rows_in_dataframe": n_before, "rows_in_sqlite": n_loaded, "match": ok}
            level = log.info if ok else log.warning
            level(f"LOAD {table_name}: dataframe_rows={n_before}, sqlite_rows={n_loaded}, match={ok}")

        # referential check: fact tables should reference only known warehouses
        if "dim_warehouses" in tables and "fact_sales" in tables:
            known = set(tables["dim_warehouses"]["warehouse_id"])
            orphan = tables["fact_sales"].loc[~tables["fact_sales"]["warehouse_id"].isin(known)]
            checks["fact_sales_orphan_warehouse_ids"] = int(len(orphan))
            log.info(f"LOAD quality check: fact_sales rows with warehouse_id missing from dim_warehouses = {len(orphan)}")

        total_check = conn.execute(
            "SELECT (SELECT COUNT(*) FROM fact_sales) + (SELECT COUNT(*) FROM fact_orders) "
            "+ (SELECT COUNT(*) FROM fact_inventory)"
        ).fetchone()[0]
        checks["total_fact_rows"] = total_check
        log.info(f"LOAD quality check: SELECT COUNT(*) across fact tables = {total_check}")
    finally:
        conn.close()
    log.info(f"Database written to {db_path}")
    return checks
