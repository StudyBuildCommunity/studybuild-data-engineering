const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, Header, Footer, PageNumber,
  VerticalAlign,
} = require("docx");
const { ROOT, summary, waterfall } = require("./report_data");

const NAVY = "1F4E5A";
const BLUE = "2E6E8E";
const LIGHT = "EAF1F4";
const ORANGE = "B5551A";
const GREY = "5A6B72";
const FONT = "Calibri";

const fig = (name) => fs.readFileSync(path.join(ROOT, "figures", name));

// ---------------------------------------------------------------------------
// small helpers
// ---------------------------------------------------------------------------
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 380, after: 180 },
    border: { bottom: { color: BLUE, space: 4, style: BorderStyle.SINGLE, size: 6 } },
    children: [new TextRun({ text, bold: true, color: NAVY, size: 30, font: FONT })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, bold: true, color: BLUE, size: 24, font: FONT })],
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    children: [new TextRun({ text, size: 21, font: FONT, ...opts })],
  });
}
function bullet(text) {
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, size: 21, font: FONT })],
  });
}
function caption(text) {
  return new Paragraph({
    spacing: { before: 60, after: 260 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, size: 18, italics: true, color: GREY, font: FONT })],
  });
}
function image(name, widthPx = 520) {
  const buf = fig(name);
  const ratio = 675 / 1200;
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: widthPx, height: Math.round(widthPx * ratio) } })],
  });
}

function cellText(text, { bold = false, color = "111111", align = AlignmentType.LEFT } = {}) {
  return new Paragraph({ alignment: align, children: [new TextRun({ text: String(text), bold, color, size: 19, font: FONT })] });
}
function headerCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: NAVY, color: "auto" },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [cellText(text, { bold: true, color: "FFFFFF" })],
  });
}
function bodyCell(text, width, { shaded = false, align = AlignmentType.LEFT, bold = false, color = "111111" } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shaded ? { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 70, bottom: 70, left: 100, right: 100 },
    children: [cellText(text, { align, bold, color })],
  });
}
function dataTable(widths, headers, rows) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => headerCell(h, widths[i])) }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((c, ci) => bodyCell(c, widths[ci], { shaded: ri % 2 === 1, align: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })),
      })),
    ],
  });
}

const pct = (n, d) => `${((n / d) * 100).toFixed(1)}%`;
const S = summary; // shorthand

// ---------------------------------------------------------------------------
// content
// ---------------------------------------------------------------------------
const children = [];

// Title page ------------------------------------------------------------
children.push(
  new Paragraph({ spacing: { before: 1400 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "FMCG Inventory Data", bold: true, color: NAVY, size: 56, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
    children: [new TextRun({ text: "Integration Pipeline", bold: true, color: NAVY, size: 56, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 260, after: 40 },
    children: [new TextRun({ text: "Project Report", bold: false, color: BLUE, size: 32, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 40 },
    children: [new TextRun({ text: "Python · Pandas · SQLite — a 10-day self-study build", color: GREY, size: 22, italics: true, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 900 },
    children: [new TextRun({ text: "Prepared for: AmirReza BabaAhmadi", color: GREY, size: 20, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60 },
    children: [new TextRun({ text: "Data as of: 1 September 2026", color: GREY, size: 20, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
    children: [new TextRun({ text: "Report date: 5 September 2026", color: GREY, size: 20, font: FONT })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// Contents ----------------------------------------------------------------------
const TOC_ENTRIES = [
  "1. Executive Summary", "2. Business Problem & Objectives", "3. Data Sources",
  "4. Pipeline Architecture", "5. Data Quality Findings (Q1)",
  "6. Business Rule Validation (Q2)", "7. Standardization & Transformation (Q3)",
  "8. Data Integration (Q4)", "9. Business-Ready Analytical View (Q5)",
  "10. Operational Flags (Q6)", "11. Loading & Reproducibility (Q7)",
  "12. Logging & Audit Trail (Q8)", "13. Limitations", "14. Conclusion & Recommendations",
];
children.push(
  h1("Contents"),
  ...TOC_ENTRIES.map((t) => new Paragraph({
    spacing: { after: 130 },
    children: [new TextRun({ text: t, size: 21, font: FONT, color: "222222" })],
  })),
  new Paragraph({ children: [new PageBreak()] }),
);

// 1. Executive summary -------------------------------------------------------
children.push(
  h1("1. Executive Summary"),
  p("This project builds a complete, reproducible ETL pipeline for a regional FMCG (fast-moving consumer goods) distributor's sales, order, and inventory data. Four raw CSV extracts — sales, orders, inventory snapshots, and a warehouse master file — were profiled, validated against eight explicit business rules, cleaned and standardized, safely integrated into one business-ready analytic table, screened for four operational risk conditions, and loaded into a SQLite database. Every step is logged for audit."),
  p(`The pipeline processed ${S.raw_row_counts.sales.toLocaleString()} raw sales rows, ${S.raw_row_counts.orders.toLocaleString()} raw order rows, and ${S.raw_row_counts.inventory.toLocaleString()} raw inventory-snapshot rows across ${S.raw_row_counts.warehouses} warehouses. After validation and cleaning, ${S.clean_row_counts.sales.toLocaleString()} sales rows, ${S.clean_row_counts.orders.toLocaleString()} order rows, and ${S.clean_row_counts.inventory.toLocaleString()} inventory rows were loaded, producing a business-ready view of ${S.analytic_rows} SKU/warehouse combinations. Every SQLite table's row count was verified against its source DataFrame, and zero fact-table rows reference a warehouse that doesn't exist in the warehouse master.`),
  p("Key findings: 36.9% of SKU/warehouse combinations show excess inventory relative to recent sales velocity, 13.1% show no sales movement at all in the trailing 30 days (dead stock), and 6.4% have open order quantities that exceed what's currently on hand. These are flagged for business review, not acted on automatically — see Section 8."),
);

// 2. Business problem --------------------------------------------------------
children.push(
  h1("2. Business Problem & Objectives"),
  p("A distributor tracks sales, purchase orders, and warehouse inventory in three separate systems that export flat files on different schedules with no shared data-entry standard. Before anyone can answer basic operating questions — which SKUs are close to stocking out, which warehouses are overstocked, whether open orders are large enough to cover recent demand — the four extracts have to be profiled, cleaned to a common standard, safely joined, and checked for internal consistency."),
  p("This project answers eight concrete questions with evidence rather than assumptions:"),
  bullet("Q1 — Can the raw data be trusted, and where exactly is it dirty?"),
  bullet("Q2 — Which records violate the business's own data rules?"),
  bullet("Q3 — Can the four files be standardized automatically, without manual spreadsheet edits?"),
  bullet("Q4 — Can the sources be merged without silently losing or duplicating records?"),
  bullet("Q5 — What does a single, business-ready view of inventory look like?"),
  bullet("Q6 — Which SKU/warehouse combinations need operational attention right now?"),
  bullet("Q7 — Is the load into SQLite reproducible and internally consistent?"),
  bullet("Q8 — Is there a full audit trail of what happened and when?"),
);

// 3. Data sources -------------------------------------------------------------
children.push(
  h1("3. Data Sources"),
  p("No production export was available for this project, so a synthetic-but-realistic extract was generated (script: scripts_generate_raw_data.py, seeded with numpy for full reproducibility). The generator follows a combined approach: plausible transaction/order/inventory table structures paired with a simulated 8-warehouse distribution network, deliberately seeded with the same categories of problems a real-world export would carry, so the pipeline has something genuine to clean rather than a tidy toy dataset."),
  p("Problems injected on purpose:"),
  bullet("Inconsistent column headers across files (\" SKU\", \"Warehouse_ID\", \"OrderedQty\", \"SnapshotDate\", …)"),
  bullet("Mixed date formats (ISO, US, \"15-Jan-2026\") and outright blank dates"),
  bullet("Blank SKUs and blank quantities"),
  bullet("Unflagged negative quantities — the source systems carry no \"this is a documented return\" indicator"),
  bullet("Warehouse IDs with inconsistent casing/formatting (\"wh-01\", \"WH_05\")"),
  bullet("Warehouse IDs that don't exist anywhere (WH-99) or that appear in transactions but not in the warehouse master (WH-09) — a dangling foreign key"),
  bullet("Exact duplicate rows and duplicate primary keys (re-sent transactions/orders)"),
  bullet("Order-status text with typos and inconsistent casing (\"Shiped\", \"PENDING\", \"cancelled\")"),
);

// 4. Architecture --------------------------------------------------------------
children.push(
  h1("4. Pipeline Architecture"),
  p("The pipeline is organized into five modules under src/, run in a fixed order by src/main.py:"),
  bullet("extract.py — reads the four raw CSVs exactly as they arrive"),
  bullet("profile.py — full data-quality profile of every raw file (Q1)"),
  bullet("transform.py — standardization, validation rules, safe merges, the business-ready view, and the operational flags (Q2–Q6)"),
  bullet("load.py — writes five tables to SQLite and verifies the load (Q7)"),
  bullet("main.py — orchestrates all of the above and writes logs, figures, and the quality summary (Q8)"),
  p("Every file goes through the exact same fixed sequence: read raw → standardize column names → convert types (dates, numbers) → enforce the warehouse foreign key → apply the remaining validation rules → drop exact duplicates → de-duplicate on the primary key. Re-using one set of transform functions across all four files (rather than writing bespoke cleaning code per file) is what makes the pipeline maintainable and its behavior predictable."),
);

// 5. Data quality (Q1) -----------------------------------------------------
children.push(
  h1("5. Data Quality Findings (Q1)"),
  p("Every raw file was profiled before any cleaning took place: row/column counts, exact column names as received, missing-value percentages, exact duplicate rows, duplicate primary keys, unparseable dates, negative values in quantity columns, blank SKUs, and warehouse IDs absent from the warehouse master. Full detail is logged to logs/pipeline.log; the headline numbers:"),
  dataTable(
    [2500, 1500, 1600, 1700, 1600, 1700],
    ["File", "Rows", "Exact\nduplicates", "Blank/\nmissing SKU", "Unparseable\ndates", "Negative\nquantities"],
    [
      ["sales.csv", S.raw_profiles.sales.n_rows, S.raw_profiles.sales.n_exact_dupes, S.raw_profiles.sales.n_blank_sku, S.raw_profiles.sales.bad_dates["SaleDate "], S.raw_profiles.sales.negatives[" Quantity"]],
      ["orders.csv", S.raw_profiles.orders.n_rows, S.raw_profiles.orders.n_exact_dupes, S.raw_profiles.orders.n_blank_sku, S.raw_profiles.orders.bad_dates["Order Date"], S.raw_profiles.orders.negatives["OrderedQty"]],
      ["inventory.csv", S.raw_profiles.inventory.n_rows, S.raw_profiles.inventory.n_exact_dupes, S.raw_profiles.inventory.n_blank_sku, S.raw_profiles.inventory.bad_dates["SnapshotDate"], S.raw_profiles.inventory.negatives["OnHandQty"]],
      ["warehouses.csv", S.raw_profiles.warehouses.n_rows, S.raw_profiles.warehouses.n_exact_dupes, "—", "—", "—"],
    ],
  ),
  caption("Table 1. Raw data-quality profile, before any cleaning."),
  p("Warehouse-ID orphans (values that don't resolve to any row in warehouses.csv) were also counted per file: 27 in sales, 14 in orders, and 69 in inventory. These are addressed under Rule R2 in the next section rather than dropped ad hoc."),
  p("Column headers as received also confirm the standardization problem directly: sales.csv arrived with headers \" SKU\", \"SaleDate \" and \"Warehouse_ID\" side by side — three different spacing/casing conventions in one six-column file. This is exactly what Section 7 (Q3) standardizes automatically."),
);

// 6. Validation (Q2) -----------------------------------------------------------
children.push(
  h1("6. Business Rule Validation (Q2)"),
  p("Eight rules were defined before any cleaning code was written, so that every drop/flag decision downstream traces back to an explicit, documented rule rather than an ad hoc judgment call made while looking at the data:"),
  dataTable(
    [900, 5300, 3700],
    ["Rule", "Statement", "Enforcement"],
    [
      ["R1", "SKU must not be blank", "Rows dropped; count logged"],
      ["R2", "warehouse_id must exist in the warehouse master table", "Rows quarantined to data/processed/quarantine_*.csv — not silently dropped"],
      ["R3", "Date columns must be parseable", "Unparseable values coerced to null via pd.to_datetime(errors='coerce'); rows with a required null date dropped"],
      ["R4", "Quantity-type columns must be numeric", "Non-numeric values coerced to null via pd.to_numeric(errors='coerce')"],
      ["R5", "Negative quantity is only valid if flagged as a documented return", "No return flag exists in the source data, so any negative quantity/ordered_qty is treated as an error and dropped"],
      ["R6", "on_hand_qty cannot be negative", "Rows floored out; count logged"],
      ["R7", "Primary keys should not repeat", "transaction_id / order_id de-duplicated, keep-first"],
      ["R8", "Required columns must not be entirely null", "Verified during profiling (Section 5)"],
    ],
  ),
  caption("Table 2. Business rules validated by src/transform.py."),
  p("R2 deserves a specific callout: rather than silently dropping rows with an unrecognized warehouse ID, the pipeline routes them to a quarantine file per source (data/processed/quarantine_sales_bad_warehouse_id.csv, etc.) with every original column intact, so a data steward can review and, where appropriate, correct and re-ingest them. Nothing disappears without a trace."),
);

// 7. Transform (Q3) -------------------------------------------------------------
children.push(
  h1("7. Standardization & Transformation (Q3)"),
  p("Six reusable functions live once in src/transform.py and are applied identically to every file, so a fix or improvement only needs to be made in one place:"),
  bullet("standardize_column_names — lower-case, strip whitespace, collapse internal spaces to underscores, strip stray punctuation"),
  bullet("normalize_ids — upper-case, trim, unify separators to a dash (so \"wh-01\", \" WH-01 \" and \"WH_05\" all resolve to a single canonical form)"),
  bullet("parse_dates — pd.to_datetime(..., errors='coerce'), applied consistently regardless of the source format mix"),
  bullet("to_numeric_safe — pd.to_numeric(..., errors='coerce') for every quantity-like column"),
  bullet("clean_text — trims and lower-cases free-text fields (order status), with a small typo map (\"shiped\" → \"shipped\") applied before validating against the canonical status set"),
  bullet("drop_exact_duplicates — removes bit-for-bit duplicate rows, with the count logged per file"),
  p("Applying the same six functions everywhere, in the same order, is what turns three inconsistently-formatted CSVs into tables that can be safely joined — the alternative (bespoke per-file cleaning scripts) doesn't scale and is hard to audit."),
);

// 8. Integration (Q4) -----------------------------------------------------------
children.push(
  h1("8. Data Integration (Q4)"),
  p("Grain was fixed before any merge was written: one row per (sku, warehouse_id) for the business-ready view, one row per transaction/order for the fact tables. Every merge uses how='left' with indicator=True; row counts before and after each merge are logged, and unmatched rows are captured separately rather than dropped silently."),
  dataTable(
    [2600, 1500, 1500, 1600, 2400],
    ["Merge", "Rows before", "Rows after", "Unmatched", "Interpretation"],
    [
      ["Analytic ← Inventory", 360, 360, S.unmatched_counts.inventory, "Every SKU/warehouse combination has a current stock snapshot"],
      ["Analytic ← Sales", 360, 360, S.unmatched_counts.sales, "No sales activity in the trailing 30 days — benign, not an error"],
      ["Analytic ← Orders", 360, 360, S.unmatched_counts.orders, "No open orders in the trailing 30 days — benign, not an error"],
      ["Analytic ← Warehouses", 360, 360, S.unmatched_counts.warehouses, "Zero orphans, because R2 quarantined bad warehouse IDs before this stage"],
    ],
  ),
  caption("Table 3. Merge accounting for the business-ready analytic view."),
  p("The row count staying at 360 before and after every merge confirms there was no fan-out (no accidental one-to-many join inflating the row count) — a check the pipeline makes automatically and would raise a warning for if it failed."),
);

// 9. Business ready view (Q5) ------------------------------------------------
children.push(
  h1("9. Business-Ready Analytical View (Q5)"),
  p(`The analytic_sku_warehouse table has one row per (sku, warehouse_id) — ${S.analytic_rows} rows in the current run — with the following columns:`),
  bullet("on_hand_qty — most recent inventory snapshot for that SKU/warehouse"),
  bullet("recent_sales_qty, last_sale_date — trailing 30-day sales volume and most recent sale"),
  bullet("recent_orders_qty, last_order_date — trailing 30-day open-order volume (cancelled orders excluded) and most recent order"),
  bullet("warehouse_name, city, region — joined from the warehouse master"),
  bullet("four operational flag columns — see Section 10"),
  p("This is the table a category manager or operations analyst would actually query day to day, rather than joining the three raw fact tables by hand each time."),
);

// 10. Flags (Q6) -----------------------------------------------------------------
children.push(
  h1("10. Operational Flags (Q6)"),
  p("Four simple, non-optimized flags were computed directly on the business-ready view, deliberately favoring transparency over sophistication for this first pass:"),
  dataTable(
    [1700, 4600, 1500, 1900],
    ["Flag", "Definition", "Rows", "% of 360"],
    [
      ["Stockout risk (F1)", "On-hand quantity ≤ 0 while there was recent sales demand", S.flag_counts.flag_stockout_risk, pct(S.flag_counts.flag_stockout_risk, S.analytic_rows)],
      ["Excess inventory (F2)", "On-hand quantity is more than 4× the recent sales quantity", S.flag_counts.flag_excess_inventory, pct(S.flag_counts.flag_excess_inventory, S.analytic_rows)],
      ["Order backlog (F3)", "Open order quantity exceeds the quantity currently on hand", S.flag_counts.flag_order_backlog, pct(S.flag_counts.flag_order_backlog, S.analytic_rows)],
      ["Dead stock (F4)", "Stock is on hand but there were zero sales in the last 30 days", S.flag_counts.flag_dead_stock, pct(S.flag_counts.flag_dead_stock, S.analytic_rows)],
    ],
  ),
  caption("Table 4. Operational flags computed in src/transform.add_operational_flags()."),
  image("fig2_flags_by_type.png", 480),
  caption("Figure 1. SKU/warehouse rows by operational flag."),
  p("Excess inventory is the largest single flag at 36.9% of SKU/warehouse combinations — a reasonable first-pass signal given a 4× threshold, but one that should be reviewed against real service-level targets before it drives action (see Limitations, Section 13). Only one combination shows outright stockout risk, and 13.1% show no sales movement at all in the trailing 30 days."),
  image("fig1_inventory_by_warehouse.png", 480),
  caption("Figure 2. Total on-hand inventory by warehouse."),
  image("fig3_top_skus_on_hand.png", 480),
  caption("Figure 3. Top 10 SKUs by total on-hand quantity."),
);

// 11. Load (Q7) ---------------------------------------------------------------
children.push(
  h1("11. Loading & Reproducibility (Q7)"),
  p("Five tables were written to database/inventory.db with if_exists='replace': dim_warehouses, fact_sales, fact_orders, fact_inventory, and analytic_sku_warehouse. After loading, the pipeline runs its own quality checks rather than assuming the write succeeded:"),
  dataTable(
    [3300, 2100, 2100, 1700],
    ["Table", "Rows in DataFrame", "Rows in SQLite", "Match"],
    Object.entries(S.load_checks).filter(([k]) => typeof S.load_checks[k] === "object" && "rows_in_dataframe" in S.load_checks[k]).map(([k, v]) => [k, v.rows_in_dataframe, v.rows_in_sqlite, v.match ? "Yes" : "No"]),
  ),
  caption("Table 5. Post-load row-count verification (DataFrame vs. SELECT COUNT(*))."),
  p(`A second check confirms referential integrity end to end: ${S.load_checks.fact_sales_orphan_warehouse_ids} rows in fact_sales reference a warehouse_id absent from dim_warehouses (out of ${S.load_checks.total_fact_rows.toLocaleString()} total rows across the three fact tables).`),
  p("The pipeline uses only relative (pathlib) paths, runs end to end with a single command (python -m src.main), and is idempotent — running it twice in a row from a clean data/processed/ and database/ produces identical row counts and identical flag counts, since the source generator is seeded and every transform is deterministic."),
);

// 12. Logging (Q8) --------------------------------------------------------------
children.push(
  h1("12. Logging & Audit Trail (Q8)"),
  p("logs/pipeline.log is overwritten (not appended) on every run and records, with a timestamp on every line: pipeline start and end; rows read per raw file; every profiling statistic from Section 5; every validation rule violation and quarantine action from Section 6; row counts dropped by cleaning and by exact-duplicate removal; merge before/after/unmatched counts from Section 8; every operational flag count from Section 10; and the post-load verification results from Section 11. Any unhandled exception would be captured with its full traceback rather than failing silently."),
  p("This makes the log file itself a complete, chronological answer to \"what did the pipeline actually do on this run\" — useful both for debugging and for demonstrating to a reviewer that no step was skipped."),
);

// 13. Limitations -----------------------------------------------------------------
children.push(
  h1("13. Limitations"),
  bullet("The underlying data is synthetic, not a live production export; absolute magnitudes (units, revenue) are illustrative, not real sales figures."),
  bullet("No source system carries a \"this negative quantity is a documented return\" indicator, so Rule R5 treats every negative quantity as a data-entry error. A real source system would carry a return/refund flag that should be honored instead of a blanket drop."),
  bullet("The excess-inventory (4×) and order-backlog (>on-hand) thresholds in Section 10 are reasonable starting points for a first pass, not thresholds tuned against real service-level agreements — they should be reviewed with the business before being used to trigger purchasing or allocation decisions."),
  bullet("The trailing window is fixed at 30 days of recent activity over 70 days of history; both are configurable constants in src/main.py, not hard business requirements."),
  bullet("Quarantined rows (R2) are written to disk for review but are not automatically corrected or re-ingested — that step is intentionally a human decision."),
);

// 14. Conclusion --------------------------------------------------------------------
children.push(
  h1("14. Conclusion & Recommendations"),
  p("The pipeline meets all eight objectives set out in Section 2: raw data quality is fully profiled and documented, business rules are explicit and enforced with an audit trail, the four sources are standardized and merged without silent data loss, a single business-ready view answers real operating questions, four operational risk conditions are flagged transparently, the SQLite load is verified rather than assumed, and every run is fully logged and reproducible."),
  p("Recommended next steps: validate the excess-inventory and order-backlog thresholds against the business's actual service-level targets; add a documented return/refund indicator to the sales extract so genuine returns are no longer indistinguishable from data-entry errors; and review the quarantined rows in data/processed/ with whoever owns the warehouse master data, since a recurring dangling warehouse ID usually points to a synchronization gap between source systems rather than a one-off typo."),
);

// ---------------------------------------------------------------------------
const doc = new Document({
  creator: "AmirReza BabaAhmadi",
  title: "FMCG Inventory Data Integration Pipeline — Project Report",
  description: "English project report for the FMCG Inventory ETL pipeline (Python, Pandas, SQLite).",
  styles: {
    default: {
      document: { run: { font: FONT, size: 21 } },
    },
  },
  features: { updateFields: true },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1300, right: 1300 } },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        border: { bottom: { color: "CCCCCC", space: 4, style: BorderStyle.SINGLE, size: 4 } },
        children: [new TextRun({ text: "FMCG Inventory Data Integration Pipeline", size: 16, color: GREY, font: FONT })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Page ", size: 16, color: GREY, font: FONT }),
          new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY, font: FONT }),
          new TextRun({ text: " of ", size: 16, color: GREY, font: FONT }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: GREY, font: FONT }),
        ],
      })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "reports", "FMCG_ETL_Project_Report_EN.docx");
  fs.writeFileSync(out, buf);
  console.log("Wrote", out);
});
