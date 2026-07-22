---
name: website-qa
description: Full website QA automation using Playwright. Runs browser-based checks across Desktop/Tablet/Mobile — images, SEO, accessibility, WP Rocket, console errors, buttons, sticky menu, third-party scripts. Triggers on: "qa", "check website", "full qa", "qa checklist", "run qa", "website audit".
allowed-tools:
  - Read
  - Bash
  - Write
  - Glob
---

# Website QA Skill

## How to Run

```bash
npm run qa:playwright -- <url>
```

Example:
```bash
npm run qa:playwright -- https://basespawellness.com
npm run qa:playwright -- drreichner.com/plastic-surgery
```

This launches a real Playwright browser and runs all checks across **Desktop (1280px), Tablet (768px), Mobile (375px)**. Generates an HTML report + JSON + full-page screenshots in `reports/qa-full-*/`.

## What It Checks

| # | Check | What It Detects |
|---|---|---|
| 1 | Console errors | JS errors during page load |
| 2 | WP Rocket Critical CSS | Remove Unused CSS active |
| 3 | WP Rocket Delay JS | Delay JavaScript active |
| 4 | WP Rocket LazyLoad | Lazy loading on images |
| 5 | WebP detection | Images served as WebP |
| 6 | Broken images | Images that fail to load (0 natural size) |
| 7 | Oversized PNGs | PNGs rendered smaller than natural size |
| 8 | Alt text | Missing alt on visible images |
| 9 | Viewport meta | Present and correct |
| 10 | Pinch-zoom | Not blocked (accessibility) |
| 11 | Heading order | H1→H2→H3 sequential, no skips |
| 12 | `<main>` landmark | Present |
| 13 | Generic links | No "Learn More" without description |
| 14 | Title tag | Present |
| 15 | Meta description | Present |
| 16 | Canonical URL | Present |
| 17 | Indexability | No `noindex` directive |
| 18 | H1 heading | Present |
| 19 | Sticky menu | Detected at top of page |
| 20 | Trustindex | Loading from CDN |
| 21 | easypiechart.js | Not loading (performance) |
| 22 | Script count | Under threshold |
| 23 | Font count | Under threshold |
| 24 | DOM size | Under 1400 elements |
| 25 | HTML size | Under 150KB |

## What Still Needs Manual Checking

These cannot be automated — check manually in browser:

- [ ] Font consistency across all sections
- [ ] Button consistency (size, color, hover)
- [ ] Whitespace and spacing (walang siksik)
- [ ] Overlapping elements
- [ ] Contact forms (submit and validate)
- [ ] Internal links (no 404s)
- [ ] Hero images (looks good on all viewports)
- [ ] Featured image (set, sized, shows on feeds)
- [ ] Navigation / breadcrumbs
- [ ] Menu clickability (burger menu, dropdowns)
- [ ] Cookie consent banner

## How to Share With Team

Each team member runs once:

```bash
cp -r .opencode/skills/website-qa ~/.agents/skills/website-qa
```

Then restart opencode. When they type "run QA on example.com", opencode loads this skill automatically.

## Files

```
qa-full-playwright.js      ← Main QA script (Playwright, browser-based)
reports/qa-full-*/         ← Generated reports (HTML + JSON + screenshots)
package.json               ← npm run qa:playwright command
```

## Why Playwright Over curl

The old script used `curl` + regex to scan raw HTML. It was inaccurate because:
- It couldn't see the rendered page
- JavaScript-rendered content was invisible
- It flagged PNGs that were actually small/decorative
- It couldn't check actual image dimensions

Playwright launches a real browser, executes JS, and checks the **actual rendered state** — accurate results every time.
