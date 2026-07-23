import { chromium } from 'playwright';
import { FILTER_CARDS, CHANNEL_OPTIONS, DATE_OPTIONS } from '../registry/filter-card-registry.js';
import { selectChannel, selectDateRange, resetFilters } from '../helpers/filters.js';
import { getAllCardSnapshots } from '../helpers/dom-readers.js';
import { captureFullPage } from '../helpers/screenshots.js';
import { ensureOutputDir, writeJSON, escapeHtml, statusBadge } from '../helpers/report.js';
import { resolve } from 'path';
import { writeFileSync } from 'fs';

const VIEWPORT = { width: 1280, height: 800 };

export async function runFilterValueTests(baseUrl, outputDir) {
  ensureOutputDir(outputDir);
  const fullUrl = `${baseUrl.replace(/\/$/, '')}/dashboard-demo.html`;

  console.log(`\n[Filter Value Tests] ${fullUrl}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();

  const results = [];
  let allPassed = true;

  try {
    await page.goto(fullUrl, { waitUntil: 'networkidle', timeout: 30000 });

    // Establish baseline
    await resetFilters(page);
    const baseline = await getAllCardSnapshots(page, FILTER_CARDS);

    // Test each channel option
    for (const channel of CHANNEL_OPTIONS.slice(1)) {
      await selectChannel(page, channel);
      const afterChannel = await getAllCardSnapshots(page, FILTER_CARDS);
      results.push(...compareSnapshots('channel', channel, baseline, afterChannel));
    }

    await resetFilters(page);

    // Test each date option
    for (const date of DATE_OPTIONS.slice(1)) {
      await selectDateRange(page, date);
      const afterDate = await getAllCardSnapshots(page, FILTER_CARDS);
      results.push(...compareSnapshots('date', date, baseline, afterDate));
    }

    await resetFilters(page);

    // Final evidence screenshot
    await captureFullPage(page, outputDir, 'filter-value-baseline.png');
  } catch (err) {
    console.error('Filter value test error:', err.message);
    allPassed = false;
  } finally {
    await browser.close();
  }

  allPassed = results.every((r) => r.passed) && allPassed;

  const summary = {
    total: results.length,
    passed: results.filter((r) => r.passed).length,
    failed: results.filter((r) => !r.passed).length,
    allPassed,
  };

  const reportData = { baseUrl, summary, results };
  writeJSON(outputDir, 'filter-value-report.json', reportData);
  const htmlPath = generateHTML(outputDir, reportData);

  console.log(`  ${summary.passed}/${summary.total} assertions passed`);
  console.log(`  Report: ${htmlPath}`);

  return { summary, htmlPath, allPassed };
}

function compareSnapshots(filterType, filterValue, baseline, current) {
  const comparisons = [];
  for (let i = 0; i < baseline.length; i++) {
    const base = baseline[i];
    const curr = current[i];
    const isUnfiltered = base.type === 'unfiltered-labeled';

    const valueMatches = base.value === curr.value;
    const labelChanged = base.label !== curr.label;

    let passed;
    let message;
    if (isUnfiltered) {
      passed = valueMatches && labelChanged;
      message = passed
        ? 'Value unchanged, label updated'
        : valueMatches
        ? 'Value unchanged but label did not update'
        : 'Unfiltered-labeled value changed unexpectedly';
    } else {
      passed = !valueMatches && labelChanged;
      message = passed
        ? 'Value changed, label updated'
        : valueMatches
        ? 'Value did not change after filter'
        : 'Label did not update';
    }

    comparisons.push({
      cardId: base.id,
      cardName: base.name,
      type: base.type,
      filterType,
      filterValue,
      baselineValue: base.value,
      currentValue: curr.value,
      baselineLabel: base.label,
      currentLabel: curr.label,
      passed,
      message,
    });
  }
  return comparisons;
}

function generateHTML(outputDir, data) {
  const rows = data.results
    .map(
      (r) => `<tr class="${r.passed ? '' : 'fail-row'}">
        <td>${escapeHtml(r.cardName)}</td>
        <td><code>${escapeHtml(r.type)}</code></td>
        <td>${escapeHtml(r.filterType)} = ${escapeHtml(r.filterValue)}</td>
        <td>${escapeHtml(r.baselineValue)} → ${escapeHtml(r.currentValue)}</td>
        <td>${escapeHtml(r.baselineLabel)} → ${escapeHtml(r.currentLabel)}</td>
        <td>${statusBadge(r.passed)}</td>
        <td>${escapeHtml(r.message)}</td>
      </tr>`
    )
    .join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Filter Value Change QA Report</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}
.container{max-width:1200px;margin:0 auto}
h1{font-size:24px;margin-bottom:5px}
.url{color:#94a3b8;font-size:14px;word-break:break-all;margin-bottom:20px}
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:15px;margin-bottom:25px}
.stat-card{background:#1e293b;border-radius:8px;padding:15px;text-align:center;border:1px solid #334155}
.stat-card .num{font-size:28px;font-weight:700}
.stat-card .label{font-size:12px;color:#94a3b8;margin-top:4px}
table{width:100%;border-collapse:collapse;background:#1e293b;border-radius:8px;overflow:hidden;font-size:13px}
th{background:#334155;color:#94a3b8;padding:10px 8px;text-align:left;font-weight:600}
td{padding:8px;border-bottom:1px solid #1e293b;vertical-align:top}
tr:hover{background:rgba(255,255,255,0.03)}
.fail-row{background:rgba(239,68,68,0.08)}
code{background:#0f172a;padding:1px 5px;border-radius:3px;font-size:12px}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600}
.badge-good{background:#166534;color:#86efac}
.badge-bad{background:#7f1d1d;color:#fca5a5}
</style>
</head>
<body>
<div class="container">
<h1>Filter Value Change QA</h1>
<div class="url">${escapeHtml(data.baseUrl)}</div>
<div class="summary">
  <div class="stat-card"><div class="num" style="color:#38bdf8">${data.summary.total}</div><div class="label">Total Assertions</div></div>
  <div class="stat-card"><div class="num" style="color:#86efac">${data.summary.passed}</div><div class="label">Passed</div></div>
  <div class="stat-card"><div class="num" style="color:#fca5a5">${data.summary.failed}</div><div class="label">Failed</div></div>
</div>
<table>
<thead><tr>
<th>Card</th><th>Type</th><th>Filter Change</th><th>Value Change</th><th>Label Change</th><th>Result</th><th>Message</th>
</tr></thead>
<tbody>${rows}</tbody>
</table>
</div>
</body>
</html>`;

  const path = resolve(outputDir, 'filter-value-report.html');
  writeFileSync(path, html);
  return path;
}

// Allow direct execution only when this file is the entry point.
if (process.argv[1] && process.argv[1].includes('filter-value-change.spec.js')) {
  const baseUrl = process.argv[2];
  if (baseUrl) {
    const outputDir = new URL('.', import.meta.url).pathname + `../../reports/qa-filter-values-${Date.now()}`;
    runFilterValueTests(baseUrl, outputDir).then((res) => {
      process.exit(res.allPassed ? 0 : 1);
    });
  }
}
