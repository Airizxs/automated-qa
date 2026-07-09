# SEO & QA Audit Tool v2.0

Automated website audit — checks SEO, accessibility, images, layout, performance, and more across Desktop, iPad, and Mobile. Uses Playwright (browser-based) for real rendered DOM checks and Chrome DevTools Protocol (CDP) for performance metrics. No API keys needed.

---

## Quick Start

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
# URL > example.com, another-site.com
# URL > exit
```

### Flags

| Flag | Effect |
|---|---|
| `--quick` | Skip CDP checks, image loading, and link verification. ~2-3x faster. |
| `--pdf` | Generate PDF report alongside HTML and JSON. |
| `--email <address>` | Send report via email (requires SMTP_* env vars). |
| `--file <path>` | Read URLs from file (one per line or CSV first column). |

### Output

Each audit generates up to 3 files in `reports/`:

| File | Always | With `--pdf` |
|---|---|---|
| `report-*.html` | Yes | Yes |
| `report-*.json` | Yes | Yes |
| `report-*.pdf` | — | Yes |

### Email Setup

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-email@gmail.com
export SMTP_PASS="your-app-password"
export SMTP_FROM=your-email@gmail.com
```

Then:

```bash
python3 main.py --pdf --email client@email.com example.com
```

### Historical Tracking

Each run saves scores to `reports/history.json`. Subsequent audits show comparison with the previous run:

```
Previous: 92.5% (A) | Now: 94.7% (A) | ↑ +2.2%
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

### CDP Checks (Chrome DevTools Protocol)
| Check | What It Detects |
|---|---|
| Console errors | JS errors during page load |
| Failed requests | HTTP 4xx/5xx, broken network requests |
| Performance score | Simulated Lighthouse-style 0–100 |
| CLS | Cumulative Layout Shift |
| FCP | First Contentful Paint (seconds) |
| TTFB | Time to First Byte (seconds) |

### Additional Visual Checks
| Check | Viewports |
|---|---|
| Sticky menu | Desktop, iPad, Mobile |
| Hero images | Desktop, iPad, Mobile |
| Full-page screenshots | Desktop, iPad, Mobile |

---

## Run Tests

```bash
pytest test_seo.py -v
```

---

## Output

Each audit generates:
- **Terminal report** — PASS/FAIL summary with details
- **HTML report** — saved to `reports/` with full breakdown
- **Dashboard** — interactive HTML summary with scores

---

## Requirements

- **Python** 3.9+
- **Playwright** (Chrome/Chromium browser)
- **Dependencies:** playwright, requests, pytest

---

## Example Output

```
  ════════════════════════════════════════════════════════════
                      SEO & QA AUDIT TOOL
           Paste a URL to audit. Type "exit" to quit.
  ════════════════════════════════════════════════════════════

  URL > https://example.com

  Running SEO audit on: https://example.com
  ..................................................

  ────────────────────────────────────────────────────────────
                     SEO & QA AUDIT RESULTS
  ────────────────────────────────────────────────────────────

  — STATIC CHECKS (HTML) —
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

  — DYNAMIC CHECKS (PLAYWRIGHT) —
  IMAGE LOADING              PASS  |  Total: 23 | Flagged: 0
  HERO (DESKTOP)             PASS  |  Method: heuristic
  HERO (IPAD)                PASS  |  Method: heuristic
  HERO (MOBILE)              PASS  |  Method: heuristic
  BREADCRUMBS                PASS  |  Found: True
  MENU CLICKABILITY          PASS  |  Links: 18
  FONT CONSISTENCY           PASS  |  Fonts: 2
  BUTTON STYLE               PASS  |  Variations: 3
  CONTACT FORMS              PASS  |  Found: 2

  — CDP —
  CONSOLE ERRORS             FAIL  |  Errors: 2 | Warnings: 5
  FAILED REQUESTS            PASS  |  Failed: 0/45
  PERFORMANCE SCORE          PASS  |  Score: 78/100
  CLS                        PASS  |  0.012
  FCP                        PASS  |  1.45s
  TTFB                       PASS  |  0.23s

  Report: file:///path/to/reports/report-example.com-2026-07-10_12-34-56.html
```
