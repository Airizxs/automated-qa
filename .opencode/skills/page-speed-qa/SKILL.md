---
name: page-speed-qa
description: Full website QA automation — run automated PageSpeed checks, image audits, WP Rocket verification, accessibility/SEO scans, third-party analysis, AND full visual/manual checklist validation. Use when verifying ANY website changes before sign-off or deployment. Covers both automated scripts and manual browser checks. Triggers on: "qa", "pagespeed", "page speed", "performance qa", "check website", "full qa", "qa checklist", "manual qa", "visual qa".
allowed-tools:
  - Read
  - Grep
  - Bash
  - WebFetch
  - Write
  - Glob
---

# Full Website QA Skill — No Excuses, Same Checklist Every Time

## Purpose

One unified QA process — automated + manual — packaged as a repeatable skill so the whole team runs the **exact same checks** on every project. Dev submits → QA runs this → if it fails, it goes back. No "hindi ko alam icheck yan." No "iba yung ginamit ko."

## Workflow (3-Step)

### Step 1 — Automated QA (Playwright)
```bash
npm run qa:playwright -- <url>
```
This launches a real browser (Playwright) and runs all checks across 3 viewports (Desktop, Tablet, Mobile). Uses the **actual rendered DOM** — not raw HTML — so results are accurate. Saves HTML report + JSON + screenshots.

### Step 2 — Supplementary Scripts (Optional)
```bash
npm run check -- <url>          # Button visual check (3 viewports)
npm run check:images -- <url>   # Broken image scan (3 viewports)
```

### Step 3 — Manual Browser QA
Open the site in a browser and check every item below. Take screenshots for any FAIL.

### Step 4 — Sign-off
All automated PASS + all manual PASS = **QA PASSED**.  
Any FAIL → send back to dev with screenshot evidence and the exact checklist item.

---

## Step 1: Automated Checks (Playwright — Browser-Based)

### Commands

| Command | What | Time | Method |
|---|---|---|---|
| `npm run qa:playwright -- <url>` | Full QA across 3 viewports | ~30-60 sec | Playwright browser |
| `npm run check -- <url>` | Button check (3 viewports) | ~20 sec | Playwright |
| `npm run check:images -- <url>` | Broken image scan (3 viewports) | ~20 sec | Playwright |
| `python3 scripts/qa_automated.py full-report <domain>` | Old QA (curl-based) | ~2-3 min | Curl + regex |

### What the Playwright Script Checks (Sections A–G)

| Section | What | Method |
|---|---|---|
| A — Performance | Console errors | Playwright browser capture |
| B — WP Rocket | Critical CSS, Delay JS, LazyLoad, WebP | Rendered DOM query |
| C — Images | Broken images, oversized PNGs, missing alt text | Rendered image natural vs display size |
| D — Layout | Viewport meta, zoom, DOM size, HTML size | Rendered page evaluate |
| E — Accessibility | Heading order, `<main>` landmark, generic links | Rendered DOM heading walk |
| F — SEO | Title, meta desc, canonical, noindex, H1 | Rendered DOM query |
| G — Third-Party | Trustindex requests, easypiechart, script/font count | Network request monitoring |
| — | Sticky menu detection | Computed style check |
| — | Screenshots (full page, all viewports) | Playwright screenshot |

### Why Playwright Over curl

| Check | curl (old) | Playwright (new) |
|---|---|---|
| Images | Scans HTML for .png URLs, assumes oversized | Actually renders the page, checks natural vs displayed size |
| WP Rocket | Looks for strings in raw HTML source | Checks the actual rendered DOM after JS executes |
| Layout | Regex on HTML string | Uses browser computed styles |
| A11y | Regex for headings in raw HTML | Walks the actual rendered heading elements |
| Network | Can't capture | Full request/response monitoring |
| Screenshots | None | Full page + element screenshots |

### Passing Criteria (Automated)

| Metric | Target |
|---|---|
| Console errors | 0 errors |
| WP Rocket Critical CSS | Present (rendered) |
| WP Rocket Delay JS | Present |
| Broken images | 0 broken |
| Missing alt text | 0 missing on visible images |
| Viewport meta | Present |
| Pinch-zoom | Allowed (not blocked) |
| DOM elements | < 1400 |
| Heading order | Sequential (no skips) |
| `<main>` landmark | Present |
| Generic "Learn More" links | 0 |
| Title tag | Present |
| H1 heading | Present |
| Indexability | No noindex |
| easypiechart.js | Not loading |

---

## Step 2: Manual Browser Checks 👁️

Open the URL in a browser. Check across **Desktop (1280+)**, **iPad (768)**, and **Mobile (375)**.

### Content & Metadata
| # | Item | Desktop | iPad | Mobile |
|---|---|---|---|---|
| 1 | **Title & Meta** — Optimized, aligned with target keywords | ☐ | — | — |
| 2 | **Headings** — Proper H1→H2→H3 hierarchy, no skips | ☐ | ☐ | ☐ |
| 3 | **Schema Markup** — Present (Organization, LocalBusiness, etc.) | ☐ | — | — |
| 4 | **Canonical** — Points to correct URL (no stray params) | ☐ | — | — |
| 5 | **Indexability** — No `noindex` directives | ☐ | — | — |
| 6 | **Featured Image** — Correctly set, properly sized, shows on feeds | ☐ | — | — |

### Navigation
| # | Item | Desktop | iPad | Mobile |
|---|---|---|---|---|
| 7 | **Sticky Menu** — Stays fixed at top, functions smoothly | ☐ | ☐ | ☐ |
| 8 | **Menu Clickability** — Links, burger menus, dropdowns 100% responsive | ☐ | ☐ | ☐ |
| 9 | **Navigation / Breadcrumbs** — Shows clear path where URL came from | ☐ | ☐ | ☐ |

### Images & Media
| # | Item | Desktop | iPad | Mobile |
|---|---|---|---|---|
| 10 | **Image Loading** — All images load completely (walang broken) | ☐ | ☐ | ☐ |
| 11 | **Hero Image** — Banner displays beautifully, no awkward cropping | ☐ | ☐ | ☐ |
| 12 | **Image Alt Text** — Reviewed and validated, all content images have alt | ☐ | ☐ | ☐ |
| 13 | **Image Loading Attribute** — Lazy loading applied where appropriate | ☐ | ☐ | ☐ |

### Buttons & Interactions
| # | Item | Desktop | iPad | Mobile |
|---|---|---|---|---|
| 14 | **Buttons & Spacing** — Clickable, large enough for touch (≥ 38px), proper margins/padding | ☐ | ☐ | ☐ |
| 15 | **Button Consistency** — Same style/size/color/hover across the page | ☐ | ☐ | ☐ |
| 16 | **Contact Forms** — Gravity Forms / CF7 submit and validate correctly | ☐ | ☐ | ☐ |
| 17 | **Internal Links** — All destination URLs correct and working (no 404s) | ☐ | ☐ | ☐ |

### Layout & Visual
| # | Item | Desktop | iPad | Mobile |
|---|---|---|---|---|
| 18 | **Responsive** — Viewport meta tag with proper settings | ☐ | ☐ | ☐ |
| 19 | **Overlapping Items** — No text, graphics, or elements bleeding into each other | ☐ | ☐ | ☐ |
| 20 | **Font Consistency** — Same font family/size/weight throughout | ☐ | ☐ | ☐ |
| 21 | **Whitespace** — Proper spacing, padding, margins, no cramping | ☐ | ☐ | ☐ |
| 22 | **Scroll to Top** — Button works | ☐ | ☐ | ☐ |
| 23 | **Cookie Consent** — Banner appears and functions | ☐ | ☐ | ☐ |

---

## Step 3: Final Verdict

```
╔══════════════════════════════════════════════╗
║  AUTOMATED: ___ PASS  ___ FAIL  ___ WARN    ║
║  MANUAL:    ___ PASS  ___ FAIL              ║
║                                              ║
║  OVERALL:   ___ PASS  ___ FAIL              ║
║                                              ║
║  FAIL items attached as screenshots:         ║
║  1.                                          ║
║  2.                                          ║
╚══════════════════════════════════════════════╝
```

**Rule:** If QA finds a FAIL that the dev's own run should have caught → the dev runs their own QA before submitting next time. The script is the same. No excuses.

---

## How to Add This Skill to opencode

### Option A: Auto-detected location (recommended)
Copy the entire skill folder into your `~/.agents/skills/`:
```bash
cp -r /path/to/tickets/1001/.opencode/skills/page-speed-qa ~/.agents/skills/page-speed-qa
```

### Option B: Project-level (stays in your repo)
Already set up at `.opencode/skills/page-speed-qa/SKILL.md`.  
opencode auto-scans `.opencode/skills/` for any `**/SKILL.md`.

### Option C: Custom path
Add to your `opencode.json`:
```json
{
  "skills": {
    "paths": [".opencode/skills"]
  }
}
```

---

## Files Referenced

```
qa-full-playwright.js         # NEW: Playwright-based full QA (recommended)
button-checker.js             # Playwright button visual checker
broken-images-checker.js      # Playwright broken image scanner
scripts/
├── qa_automated.py           # Old curl-based QA script (inaccurate)
├── performance_qa.py         # Original simpler QA script
QA-CHECKLIST.md               # Full printable checklist
```

---

## Philosophy

> "Give them the same script, the same checklist, the same passing criteria. If it still fails after they submit, they're not doing their job. Remove all excuses, then scale. You'll still do baby manual audits, but at least they're running the exact same checklist you are."

— Chester
