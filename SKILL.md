# QA Checker Skill

Full QA automation toolkit — checks images, buttons, performance, SEO, accessibility, console errors, layout, and more across Desktop, Tablet, and Mobile.

## When to Use

Trigger before deploying or after any changes to:
- Website pages, dashboards, or static files
- Images, CSS, or JavaScript
- WP Rocket, Divi, or plugin settings
- Content updates that affect layout

## Quick Start

```bash
# 1. Install (first time only)
npm install && npx playwright install chromium

# 2. Run full QA on any URL
npm run qa:playwright -- https://example.com
```

## All Commands

### Browser-Based (Playwright — Most Accurate)

| Command | What It Checks | Time |
|---|---|---|
| `npm run qa:playwright -- <url>` | Full QA: 25+ checks, 3 viewports, screenshots | ~2 min |
| `npm run check:images -- <url>` | Broken images, oversized PNGs, missing alt | ~30s |
| `npm run check -- <url>` | Button size, visibility, touch targets | ~30s |

### Python (PageSpeed API + HTML Analysis)

| Command | What It Checks |
|---|---|
| `python3 scripts/qa_automated.py full-report <domain>` | Full automated QA matching QA-CHECKLIST.md |
| `python3 scripts/qa_automated.py psi <domain>` | PageSpeed Insights only (mobile + desktop) |
| `python3 scripts/qa_automated.py check <domain>` | Quick HTML checks only (no PSI) |

### Dashboard (Web UI)

```bash
npm run dashboard    # → http://localhost:8766
```

### QA Runner (Dashboard-specific)

```bash
npm run qa:full -- <base-url>      # Full unified QA
npm run qa:values -- <base-url>    # Filter/KPI value changes
npm run qa:sweep -- <base-url>     # Section-by-section sweep
```

## QA Checklist Workflow

1. **Run automated QA** (covers ~80% of items):
   ```bash
   python3 scripts/qa_automated.py full-report basespawellness.com
   npm run qa:playwright -- https://www.basespawellness.com
   ```

2. **Review reports:**
   - `reports/qa-full-*/report.html` — Playwright HTML report with screenshots
   - `data/qa-report-*.json` — Python automated results

3. **Fill out manual checks** (16 items: visual, accessibility, functionality)

4. **Update QA-CHECKLIST.md** with results

## Project Structure

```
qa/                              # Dashboard QA pipeline
  registry/filter-card-registry.js
  helpers/  filters.js  dom-readers.js  screenshots.js  report.js
  specs/    filter-value-change.spec.js  section-sweep.spec.js
  run.js

scripts/
  qa_automated.py                # Main QA automation (PSI + HTML checks)
  performance_qa.py              # Legacy PSI check

qa-full-playwright.js            # Full Playwright browser QA
broken-images-checker.js         # Image checker
button-checker.js                # Button checker
server.js                        # Dashboard web UI
QA-CHECKLIST.md                  # Current QA results
```

## Reports Location

| Tool | Output |
|---|---|
| `npm run qa:playwright` | `reports/qa-full-<timestamp>/report.html` + `report.json` + screenshots |
| `python3 scripts/qa_automated.py` | `data/qa-report-<timestamp>.json` |
| `npm run check:images` | `reports/broken-images-<timestamp>/` |
| `npm run check` | `reports/button-check-<timestamp>/` |

## Adding a New Dashboard Card to QA

1. Add `data-testid` attributes to the card, value, and label in the UI.
2. Register the card in `qa/registry/filter-card-registry.js`.
3. Set `type` to either:
   - `responds` — value must change when filters change
   - `unfiltered-labeled` — value stays the same, label updates

## Expected Workflow

1. Serve the app or static files on a local port
2. Run `npm run qa:full -- http://localhost:PORT`
3. Open generated HTML reports in `reports/qa-<timestamp>/`
