# SEO & QA Audit Tool v2.0

Automated website audit — checks SEO, accessibility, images, layout, performance, WP Rocket, and more across Desktop, iPad, and Mobile. Uses Playwright (browser-based) for real rendered DOM checks and Chrome DevTools Protocol (CDP) for performance metrics.

---

## Quick Start (Python — Main Tool)

```bash
# 1. Clone
git clone https://github.com/Airizxs/automated-qa.git
cd automated-qa

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers (one-time)
playwright install chromium

# 4. Run on any site
python3 main.py https://example.com
```

### Quick Start (Node.js — Extended QA)

```bash
# 1. Install dependencies
npm install && npx playwright install chromium

# 2. Run full Playwright QA
npm run qa:playwright -- https://example.com
```

---

## Usage

```bash
# Single URL (full audit)
python3 main.py https://www.basespawellness.com

# Single URL (quick — skips CDP, image loading, link verification)
python3 main.py --quick example.com

# Batch — multiple URLs (browser reused across URLs for speed)
python3 main.py --quick example.com another-site.com third-site.com

# Batch — read URLs from file (one per line, or CSV first column)
python3 main.py --file urls.txt

# Interactive mode — paste URLs one by one
python3 main.py
```

### Flags

| Flag | Effect |
|---|---|
| `--quick` | Skip CDP checks, image loading, and link verification. ~2-3x faster. |
| `--pdf` | Generate PDF report alongside HTML and JSON. |
| `--email <address>` | Send report via email (requires SMTP_* env vars). |
| `--file <path>` | Read URLs from file (one per line or CSV first column). |

---

## All Commands

### Python (main.py + scripts)

| Command | What It Checks |
|---|---|
| `python3 main.py <url>` | Full SEO + QA audit (static, dynamic, CDP) |
| `python3 main.py --quick <url>` | Fast audit — skips CDP |
| `python3 main.py --pdf <url>` | Full audit + PDF report |
| `python3 scripts/qa_automated.py full-report <domain>` | PageSpeed API + HTML curl checks |
| `python3 scripts/qa_automated.py psi <domain>` | PageSpeed Insights only |

### Node.js (Playwright — Browser-Based)

| Command | What It Checks |
|---|---|
| `npm run qa:playwright -- <url>` | Full QA — 25+ checks across 3 viewports |
| `npm run check -- <url>` | Button size, visibility, touch targets |
| `npm run check:images -- <url>` | Broken images, oversized PNGs, missing alt |
| `npm run qa:full -- <url>` | Filter value changes + section sweep |
| `npm run qa:values -- <url>` | Filter/KPI card value change tests |
| `npm run qa:sweep -- <url>` | Section-by-section visual sweep |

### Dashboard (Web UI)

```bash
npm run dashboard
# Open http://localhost:8766
```

---

## What It Checks

### Static Checks (HTML)
| Check | What It Detects |
|---|---|
| Title tag | Present, character count, SEO status |
| Meta description | Present, character count, SEO status |
| Headings | H1 count, total count, hierarchy |
| Schema markup | JSON-LD count, schema types |
| Image alt text | Missing alt attributes |
| Viewport meta | Present, content |
| Indexability | No noindex, robots meta |
| Canonical tag | Present, matches URL |
| Internal links | Total count, broken links |
| Open Graph tags | og:title, og:description, og:image, og:url, og:type, og:site_name |
| SSL/HTTPS | Redirect from HTTP to HTTPS |

### Dynamic Checks (Playwright Browser)
| Check | What It Detects |
|---|---|
| Image loading | Broken images across all viewports |
| Hero banner | Loaded correctly on Desktop, iPad, Mobile |
| Breadcrumbs | Present (schema or element detection) |
| Menu clickability | Navigation link count |
| Font consistency | Unique font family count |
| Button style | CSS style variations |
| Contact forms | Form count (Gravity Forms, CF7, etc.) |
| Sticky menu | Desktop, iPad, Mobile |

### CDP Checks (Chrome DevTools Protocol)
| Check | What It Detects |
|---|---|
| Console errors | JS errors during page load |
| Failed requests | HTTP 4xx/5xx, broken network requests |
| Performance score | Simulated Lighthouse-style 0-100 |
| CLS | Cumulative Layout Shift |
| FCP | First Contentful Paint (seconds) |
| TTFB | Time to First Byte (seconds) |

### Extended QA Checks (Playwright — npm run qa:playwright)
| Section | Checks |
|---|---|
| **Console** | JS errors during page load |
| **WP Rocket** | Critical CSS, Delay JS, LazyLoad, WebP |
| **Images** | Broken images, oversized PNGs, missing alt |
| **Layout** | Viewport meta, pinch-zoom, DOM size, HTML size |
| **Accessibility** | Heading order, <main> landmark, generic links |
| **SEO** | Title, meta description, canonical, noindex, H1 |
| **Third-Party** | Trustindex, easypiechart, script/font count |
| **Screenshots** | Full-page capture on Desktop, iPad, Mobile |

---

## Example Output

### Python (main.py)

```
  URL > https://example.com

  Running SEO audit on: https://example.com
  ..................................................

  -- STATIC CHECKS (HTML) --
  TITLE                      PASS  |  Chars: 52 | Optimal
  META DESCRIPTION           PASS  |  Chars: 148 | Optimal
  HEADINGS                   PASS  |  H1: 1 | Total: 8
  SCHEMA MARKUP              PASS  |  Found: 3
  IMAGE ALT TEXT             FAIL  |  Missing: 5/23
  RESPONSIVE (VIEWPORT)      PASS
  INDEXABILITY               PASS
  CANONICAL TAG              PASS
  INTERNAL LINKS             PASS  |  Total: 42 | Broken: 0
  OG TAGS                    PASS  |  Found: 6/6
  SSL/HTTPS                  PASS

  -- DYNAMIC CHECKS (PLAYWRIGHT) --
  IMAGE LOADING              PASS  |  Total: 23 | Flagged: 0
  HERO (DESKTOP)             PASS  |  Method: heuristic
  HERO (IPAD)                PASS  |  Method: heuristic
  HERO (MOBILE)              PASS  |  Method: heuristic
  BREADCRUMBS                PASS  |  Found: True
  MENU CLICKABILITY          PASS  |  Links: 18
  FONT CONSISTENCY           PASS  |  Fonts: 2
  BUTTON STYLE               PASS  |  Variations: 3
  CONTACT FORMS              PASS  |  Found: 2

  -- CDP --
  CONSOLE ERRORS             FAIL  |  Errors: 2 | Warnings: 5
  FAILED REQUESTS            PASS  |  Failed: 0/45
  PERFORMANCE SCORE          PASS  |  Score: 78/100
  CLS                        PASS  |  0.012
  FCP                        PASS  |  1.45s
  TTFB                       PASS  |  0.23s

  Report: reports/report-example.com-2026-07-10_12-34-56.html
```

### Node.js Playwright QA (npm run qa:playwright)

```
=== Desktop (1280x800) ===
  Console errors: 1
  Images: 26 total, 0 broken, 0 missing alt
  WP Rocket Critical CSS: false
  WP Rocket Delay JS: true
  SEO Title: Medical Spa in Chesterton, IN | BASE Spa & Wellness
  SEO H1: Medical Spa, Day Spa, & Wellness
  Sticky Menu: Not detected
  Scripts: 49, Fonts: 10

=== Tablet (768x1024) ===
  Console errors: 4
  Images: 26 total, 0 broken, 0 missing alt
  ...

=== Mobile (375x812) ===
  Console errors: 4
  ...

============================================================
QA FULL REPORT
============================================================
URL: https://www.basespawellness.com
Viewports: Desktop, Tablet, Mobile

Results: 32 PASS / 21 FAIL / 19 WARN / 3 N/A
Overall: FAIL

Report: reports/qa-full-1784677324185/report.html
JSON: reports/qa-full-1784677324185/report.json
============================================================
```

---

## Run Tests

```bash
# Python tests
pytest test_seo.py -v
cd SCRIPT/Automated-QA && pytest test_seo.py -v

# Node.js tests
npm run check:images -- https://www.basespawellness.com
npm run check -- https://www.basespawellness.com
```

---

## Requirements

- **Python** 3.9+
- **Node.js** 20+
- **Playwright** (Chrome/Chromium browser)
- **Dependencies:** playwright, requests, pytest + npm packages

---

## Project Structure

```
main.py                         # Main Python QA tool (CLI + batch)
seo_audit.py                    # SEO audit module
test_seo.py                     # Python test suite
requirements.txt                # Python dependencies
qa-full-playwright.js           # Full Playwright QA (recommended)
broken-images-checker.js        # Image checker
button-checker.js               # Button checker
server.js                       # Dashboard web UI
qa/                             # Dashboard QA pipeline
  registry/  helpers/  specs/   # Filter/card testing
scripts/
  qa_automated.py               # PageSpeed API + HTML checks
  performance_qa.py             # Legacy PSI check
SCRIPT/
  Automated-QA/                 # Python SEO auditor (Playwright + CDP)
  Agent-Audit/                  # Agent-browser SEO audit
.opencode/skills/
  website-qa/SKILL.md           # OpenCode skill — website QA
  page-speed-qa/SKILL.md        # OpenCode skill — full QA + checklist
QA-CHECKLIST.md                 # Ticket #1001 QA results
PLAN.md                         # Performance audit plan
reports/                        # Generated reports (HTML, JSON, screenshots)
```

---

## Example Output

```
$ npm run qa:playwright -- https://www.basespawellness.com

=== Desktop (1280x800) ===
  Console errors: 1
  Images: 26 total, 0 broken, 0 missing alt
  WP Rocket Critical CSS: false
  WP Rocket Delay JS: true
  SEO Title: Medical Spa in Chesterton, IN | BASE Spa & Wellness
  SEO H1: Medical Spa, Day Spa, & Wellness
  Sticky Menu: Not detected
  Scripts: 49, Fonts: 10

=== Tablet (768x1024) ===
  Console errors: 4
  Images: 26 total, 0 broken, 0 missing alt
  WP Rocket Critical CSS: false
  WP Rocket Delay JS: true
  ...

=== Mobile (375x812) ===
  Console errors: 4
  Images: 26 total, 0 broken, 0 missing alt
  WP Rocket Critical CSS: false
  WP Rocket Delay JS: true
  ...

============================================================
QA FULL REPORT
============================================================
URL: https://www.basespawellness.com
Viewports: Desktop, Tablet, Mobile

Results: 32 PASS / 21 FAIL / 19 WARN / 3 N/A

Overall: FAIL

Report: reports/qa-full-1784677324185/report.html
JSON: reports/qa-full-1784677324185/report.json
============================================================
```

---

## Passing Criteria (Automated)

| Check | Target |
|---|---|
| Console errors | 0 errors |
| WP Rocket Critical CSS | Present |
| Broken images | 0 broken |
| Missing alt text | 0 missing |
| Pinch-zoom | Allowed |
| DOM elements | < 1400 |
| Heading order | Sequential (H1 > H2 > H3) |
| <main> element | Present |
| Title + H1 + Meta desc | Present |
| Indexability | No noindex |
