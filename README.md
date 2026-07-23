# SEO & QA Audit Tool

Automated website audit — 30 checks across SEO, accessibility, images, layout, performance, and more using Playwright + Chrome DevTools Protocol.

---

## Quick Start

```bash
git clone https://github.com/Airizxs/automated-qa.git
cd automated-qa
pip install -r requirements.txt
playwright install chromium
python3 main.py https://example.com
```

---

## Commands

```bash
# Full audit (static + dynamic + CDP + visual)
python3 main.py https://basespawellness.com

# Quick audit (skips CDP, faster)
python3 main.py --quick example.com

# Batch multiple URLs
python3 main.py example.com another.com third.com

# Test bank — run by suite
python3 run_test_bank.py --suite SMOKE https://example.com   # 28 critical tests
python3 run_test_bank.py --suite REG https://example.com     # 58 standard tests
python3 run_test_bank.py --suite FULL https://example.com    # 89 all tests
```

| Flag | Effect |
|---|---|
| `--quick` | Skip CDP checks — 2-3x faster |
| `--pdf` | Generate PDF report |
| `--file <path>` | Read URLs from file |

---

## Example Output

```
$ python3 run_test_bank.py --suite FULL https://basespawellness.com

Running FULL suite: 47 tests on https://basespawellness.com

───────────────────────────────────────────────────────────────────────────────
  FULL SUITE RESULTS
───────────────────────────────────────────────────────────────────────────────
ID         Area      Object               Status   Severity   Title
───────────────────────────────────────────────────────────────────────────────
TC-01.1    Static    Title Tag            PASS     Critical   Title: Optimal
TC-02.1    Static    Meta Description     FAIL     Critical   Meta Desc: Optimal
TC-03.1    Static    Headings             PASS     Critical   Single H1
TC-04.1    Static    Schema Markup        PASS     Critical   JSON-LD present
TC-05.1    Static    Image Alt Text       PASS     Critical   All present
TC-06.1    Static    Viewport             PASS     Critical   Standard
TC-07.1    Static    Robots Meta          PASS     Critical   Indexable
TC-08.1    Static    Canonical Tag        PASS     Critical   Matches URL
TC-11.1    Static    SSL/HTTPS            PASS     Critical   Valid
TC-12.1    Dynamic   Image Loading        PASS     Critical   All load
TC-13.1    Dynamic   Hero Image           PASS     Critical   Found
TC-15.1    Dynamic   Menu Clickability    PASS     Critical   Links found
TC-19.1    CDP       Console Errors       PASS     Critical   No errors
TC-21.1    CDP       Core Web Vitals      PASS     Critical   LCP good
TC-22.1    Visual    Sticky Menu          PASS     Critical   Works
  ...
───────────────────────────────────────────────────────────────────────────────
  PASS: 32 | FAIL: 2 | WARN: 1 | MANUAL: 12 | TOTAL: 47
  Score: 91%

  Previous: 89.5% (B) | Now: 91.0% (A) | ↑ +1.5%
```

---

## Requirements

- **Python** 3.9+
- **Playwright** Chromium browser
