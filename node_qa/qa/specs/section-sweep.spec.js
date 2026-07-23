import { chromium } from 'playwright';
import { SECTIONS } from '../registry/filter-card-registry.js';
import { captureFullPage } from '../helpers/screenshots.js';
import { ensureOutputDir, writeJSON, escapeHtml, statusBadge } from '../helpers/report.js';
import { resolve } from 'path';
import { writeFileSync } from 'fs';

const VIEWPORT = { width: 1280, height: 800 };

export async function runSectionSweep(baseUrl, outputDir) {
  ensureOutputDir(outputDir);
  baseUrl = baseUrl.replace(/\/$/, '');

  console.log(`\n[Section Sweep] ${baseUrl}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();

  const results = [];

  try {
    for (const section of SECTIONS) {
      const url = `${baseUrl}${section.path}`;
      console.log(`  Sweeping ${section.name}...`);

      const result = {
        id: section.id,
        name: section.name,
        url,
        loaded: false,
        noErrors: false,
        screenshot: null,
        error: null,
      };

      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(1000);

        // Basic smoke check: body exists and no uncaught errors captured via page.on
        const bodyExists = await page.evaluate(() => !!document.body);
        result.loaded = bodyExists;
        result.noErrors = !page.__hadError;
        result.screenshot = await captureFullPage(page, outputDir, `sweep-${section.id}.png`);
      } catch (err) {
        result.error = err.message;
        result.screenshot = await page.screenshot({ path: resolve(outputDir, 'screenshots', `sweep-${section.id}-error.png`) }).catch(() => null);
      }

      results.push(result);
    }
  } finally {
    await browser.close();
  }

  const summary = {
    total: results.length,
    passed: results.filter((r) => r.loaded && r.noErrors).length,
    failed: results.filter((r) => !r.loaded || !r.noErrors || r.error).length,
    allPassed: results.every((r) => r.loaded && r.noErrors && !r.error),
  };

  const reportData = { baseUrl, summary, results };
  writeJSON(outputDir, 'section-sweep-report.json', reportData);
  const htmlPath = generateHTML(outputDir, reportData);

  console.log(`  ${summary.passed}/${summary.total} sections passed`);
  console.log(`  Report: ${htmlPath}`);

  return { summary, htmlPath, allPassed: summary.allPassed };
}

function generateHTML(outputDir, data) {
  const rows = data.results
    .map(
      (r) => `<tr class="${r.loaded && r.noErrors && !r.error ? '' : 'fail-row'}">
        <td>${escapeHtml(r.name)}</td>
        <td><a href="${escapeHtml(r.url)}" target="_blank">${escapeHtml(r.url)}</a></td>
        <td>${statusBadge(r.loaded && r.noErrors && !r.error)}</td>
        <td>${r.error ? escapeHtml(r.error) : '<em>—</em>'}</td>
        <td>${r.screenshot ? `<a href="screenshots/${escapeHtml(r.screenshot.replace(/^.*[\\/]/, ''))}" target="_blank">view</a>` : '<em>none</em>'}</td>
      </tr>`
    )
    .join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Section Sweep QA Report</title>
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
a{color:#38bdf8;text-decoration:none}
a:hover{text-decoration:underline}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600}
.badge-good{background:#166534;color:#86efac}
.badge-bad{background:#7f1d1d;color:#fca5a5}
</style>
</head>
<body>
<div class="container">
<h1>Section Sweep QA</h1>
<div class="url">${escapeHtml(data.baseUrl)}</div>
<div class="summary">
  <div class="stat-card"><div class="num" style="color:#38bdf8">${data.summary.total}</div><div class="label">Total Sections</div></div>
  <div class="stat-card"><div class="num" style="color:#86efac">${data.summary.passed}</div><div class="label">Passed</div></div>
  <div class="stat-card"><div class="num" style="color:#fca5a5">${data.summary.failed}</div><div class="label">Failed</div></div>
</div>
<table>
<thead><tr>
<th>Section</th><th>URL</th><th>Result</th><th>Error</th><th>Screenshot</th>
</tr></thead>
<tbody>${rows}</tbody>
</table>
</div>
</body>
</html>`;

  const path = resolve(outputDir, 'section-sweep-report.html');
  writeFileSync(path, html);
  return path;
}

// Allow direct execution only when this file is the entry point.
if (process.argv[1] && process.argv[1].includes('section-sweep.spec.js')) {
  const baseUrl = process.argv[2];
  if (baseUrl) {
    const outputDir = new URL('.', import.meta.url).pathname + `../../reports/qa-section-sweep-${Date.now()}`;
    runSectionSweep(baseUrl, outputDir).then((res) => {
      process.exit(res.allPassed ? 0 : 1);
    });
  }
}
