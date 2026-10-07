#!/usr/bin/env bash
set -euo pipefail

REPORT="${1:-apps/dashboard/playwright-report/results.json}"
OUTPUT="${2:-/tmp/playwright-results.txt}"

if [ ! -f "$REPORT" ]; then
  echo "No Playwright JSON report found at $REPORT" > "$OUTPUT"
  exit 0
fi

node - "$REPORT" "$OUTPUT" <<'EOF'
const fs = require("fs");
const [,, reportPath, outputPath] = process.argv;

const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));

const lines = [];
let passed = 0, failed = 0, skipped = 0;

function visitSuite(suite) {
  for (const spec of suite.specs ?? []) {
    for (const test of spec.tests ?? []) {
      const lastResult= test.results?.at(-1);
      const rawStatus = lastResult?.status ?? test.outcome ?? "unknown";
      const status = rawStatus === "passed" ? "pass"
                   : rawStatus === "skipped"  ? "skip"
                   : "FAIL";
      if (status === "pass") passed++;
      else if (status === "skip") skipped++;
      else failed++;
      const icon = status === "pass" ? "✓" : status === "skip" ? "–" : "✗";
      const title = spec.title;
      let detail = "";
      if (status === "FAIL") {
        const raw = lastResult?.errors?.[0]?.message ?? "";
        const err = raw.replace(/\x1b\[[0-9;]*m/g, "");
        detail = " — " + err.split("\n")[0].slice(0, 120);
      }
      lines.push(`${icon} ${title}${detail}`);
    }
  }
  for (const child of suite.suites ?? []) visitSuite(child);
}
for (const suite of report.suites ?? []) visitSuite(suite);

const summary = `${passed} passed, ${failed} failed, ${skipped} skipped`;
const out = [summary, "", ...lines].join("\n");
fs.writeFileSync(outputPath, out, "utf8");
EOF