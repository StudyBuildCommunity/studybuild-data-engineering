// Shared numeric source-of-truth for both report builds. Reads straight
// from reports/quality_summary.json (produced by src/main.py) plus a couple
// of intermediate counts pulled from logs/pipeline.log, so the English and
// Persian reports can never drift from each other or from the actual run.
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const summary = JSON.parse(fs.readFileSync(path.join(ROOT, "reports", "quality_summary.json"), "utf-8"));

// Parsed by hand from logs/pipeline.log for the waterfall table (quarantine
// counts and "other validation rule" counts per file). These reconcile
// exactly: raw - quarantined - other_rules - exact_dupes = clean.
const waterfall = {
  sales: { raw: 1877, quarantined_fk: 27, other_rules: 401, exact_dupes: 22, clean: 1427 },
  orders: { raw: 767, quarantined_fk: 14, other_rules: 114, exact_dupes: 6, clean: 633 },
  inventory: { raw: 3470, quarantined_fk: 69, other_rules: 448, exact_dupes: 20, clean: 2933 },
  warehouses: { raw: 8, quarantined_fk: 0, other_rules: 0, exact_dupes: 0, clean: 8 },
};

module.exports = { ROOT, summary, waterfall };
