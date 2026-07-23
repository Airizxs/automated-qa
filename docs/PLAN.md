# Ticket #1001 — basespawellness.com | Full PageSpeed Audit & Analysis

**Date:** 2026-06-09
**Type:** Performance Audit (Analysis Phase — No Fixes)
**Status:** Plan — Awaiting Approval

---

## 1. Executive Summary

Full PageSpeed Insights (PSI v5) Lighthouse audit completed on `https://www.basespawellness.com/` for both **mobile** and **desktop** strategies. Raw JSON payloads (845KB mobile / 907KB desktop) saved to `data/`. This plan outlines the analysis methodology for extracting every diagnostic, opportunity, and insight from the data, mapping issues to the website's codebase, and producing a prioritized remediation roadmap.

---

## 2. Current Scores (Lighthouse v11)

### Mobile
| Category | Score | Status |
|---|---|---|
| **Performance** | **46/100** | Poor |
| Accessibility | 83/100 | Good |
| Best Practices | 100/100 | Excellent |
| SEO | 92/100 | Good |

### Desktop
| Category | Score | Status |
|---|---|---|
| **Performance** | **81/100** | Moderate |
| Accessibility | 87/100 | Good |
| Best Practices | 92/100 | Good |
| SEO | 92/100 | Good |

### Core Web Vitals — Mobile
| Metric | Value | Status |
|---|---|---|
| **LCP** | **10.2s** | FAIL (threshold: 2.5s) |
| FCP | 4.5s | FAIL |
| TBT | 20ms | PASS |
| **CLS** | **0.295** | FAIL (threshold: 0.1) |
| Speed Index | 6.3s | FAIL |
| TTI | 10.4s | FAIL |
| TTFB | 80ms | PASS |

### Core Web Vitals — Desktop
| Metric | Value | Status |
|---|---|---|
| LCP | 1.9s | PASS |
| FCP | 0.8s | PASS |
| TBT | 20ms | PASS |
| CLS | 0.0 | PASS |
| Speed Index | 7.0s | FAIL |
| TTI | 2.0s | PASS |
| TTFB | 30ms | PASS |

---

## 3. Site Stack (Detected)

| Layer | Technology |
|---|---|
| **CMS** | WordPress |
| **Theme** | Divi 4.27.6 + NKP Child Theme |
| **Hosting** | WP Engine |
| **CDN** | Cloudflare |
| **Caching** | WP Rocket 3.21.1 |
| **Page Builder** | Divi Builder (shortcode-based) |

### Active Plugins (PageSpeed-relevant)
| Plugin | Version | Impact |
|---|---|---|
| WP Rocket | 3.21.1 | Caching, minification, lazy load |
| Divi Machine | 6.5.3 | Ajax filter, carousel, masonry |
| Divi Mega Pro | 1.9.4 | Mega menus |
| Divi Mad Menu | 2.2.2 | Menu enhancements |
| DS Divi Extras | — | Extra modules, preloaders |
| Supreme Modules Pro | 4.9.97.42 | Card carousel, swiper |
| Gravity Forms | 2.10.3 | Forms |
| WP Tools GF Divi Module | 9.1.1 | GF integration |
| Cookie Law Info | 3.5.1 | Cookie consent |
| Contact Form 7 | — | Forms |
| WPCF7 Redirect | — | CF7 redirects |
| Trustindex | — | Reviews widget |
| WPFront Scroll Top | 3.0.1 | Scroll-to-top button |
| Akismet | — | Spam protection |

---

## 4. Analysis Scope — 10 Workstreams

Each workstream has its own section in the final report with: current state, specific findings from the PSI data, severity rating, and prioritized recommendations.

### A. CORE WEB VITALS DEEP DIVE
- LCP breakdown (TTFB, load delay, load duration, render delay)
- CLS culprits (shift sources, element-level tracing)
- FCP bottlenecks
- TBT main-thread breakdown (script eval, style/layout, rendering)
- Compare mobile vs desktop discrepancy

### B. IMAGE OPTIMIZATION
- **~1,235 KiB estimated savings** from image-delivery-insight
- Unoptimized images (PNG → WebP/AVIF)
- Oversized images (displaying at fractions of natural size)
- Missing responsive srcset/sizes
- Lazy-load implementation audit
- Logo, background images, service thumbnails (980x980 displayed at 195x195)
- Priority: LCP image delivery path

### C. JAVASCRIPT — CODE LEAKS & EXECUTION
- **38 KiB wasted** (62%) in Divi's `scripts.min.js` (4.27.6)
- Forced reflows in `scripts.min.js` and `jquery.min.js` (105ms total)
- 6 script requests / 129 KiB total
- Third-party JS: Trustindex loader (22 KiB, 25ms main thread)
- JS execution time: 334ms total (Divi 234ms, jQuery 107ms, Trustindex 102ms)
- Legacy JS polyfills audit

### D. CSS — UNUSED STYLES & RENDER BLOCKING
- **97 KiB wasted** (90%) from inline CSS + emoji styles
- WP Rocket Remove Unused CSS capabilities audit
- Font-awesome inclusion audit (Divi bundles all variants)
- Render-blocking stylesheet analysis

### E. FONTS
- **13 font requests** / 456 KiB
- Font-display strategy: swap/optional audit
- Google Fonts optimization
- Trustindex external fonts (Poppins 57 KiB)

### F. SERVER & NETWORK
- TTFB: 80ms mobile, 30ms desktop (acceptable)
- Redirect: `basespawellness.com` → `www.basespawellness.com` (301)
- Cache lifetimes: Trustindex `loader.js` has 0 cache TTL (22 KiB wasted)
- HTTP/2 multiplexing analysis
- 2,856 KiB total payload mobile (2,101 KiB images = 74%)
- 3,190 KiB total payload desktop (2,439 KiB images = 76%)

### G. DOM & HTML STRUCTURE
- 1,555 DOM elements (above threshold of 1,400)
- Deep nesting: Divi builder patterns
- Empty heading/landmark issues
- Semantic HTML audit
- Viewport: `maximum-scale=1.0, user-scalable=0` (accessibility fail)

### H. THIRD-PARTY IMPACT
- **Trustindex** (reviews widget): 94 KiB, 6 requests, 25ms main thread
- Google Fonts: bundled through WP Rocket
- Cookie banner (Cookie Law Info)
- External preload/preconnect candidates

### I. ACCESSIBILITY (Mobile: 83)
- Color contrast failures (score: 0)
- Heading order not sequential (score: 0)
- Links without discernible name (score: 0)
- Missing landmark main (score: 0)
- `user-scalable=no` on viewport meta (score: 0)
- Touch target size audit

### J. SEO & BEST PRACTICES
- Missing meta description?
- Structured data validation
- HTTP status codes & crawlablility
- Timed out audits from PSI data

---

## 5. Data Sources Collected

| Source | Format | Location |
|---|---|---|
| PSI Mobile Full JSON | JSON (845KB) | `data/pagespeed_mobile_raw.json` |
| PSI Desktop Full JSON | JSON (907KB) | `data/pagespeed_desktop_raw.json` |
| Website HTML Source | Text | Captured via curl |
| HTTP Headers | Text | Response headers captured |
| Plugin/Theme Inventory | Text | HTML source analysis |
| Network Request Log | JSON (embedded in PSI) | Extracted from PSI |
| Resource Summary | JSON | Extracted from PSI |
| Main Thread Tasks | JSON | Extracted from PSI |
| Script Treemap Data | JSON | Extracted from PSI |

### Not yet collected (Phase 2 candidates)
- Multiple page crawl (inner pages: services, about, contact)
- BigQuery historical data (`ga4-stream-445712.pagespeed_all`)
- CrUX field data via Chrome UX Report API
- WebPageTest run (waterfall view)
- Google Search Console data
- Manual code coverage analysis in DevTools

---

## 6. Deliverables

| # | Deliverable | Description |
|---|---|---|
| 1 | Full Analysis Report | `reports/1001-full-analysis.md` — complete findings across all 10 workstreams |
| 2 | Executive Summary | `reports/1001-executive-summary.md` — 1-page overview for stakeholders |
| 3 | Prioritized Fix List | `reports/1001-recommendations.md` — severity-ranked remediation items |
| 4 | Code Issue Map | `reports/1001-code-map.md` — specific files/themes/plugins causing each issue |
| 5 | Raw Data Archive | `data/` — all PSI JSON payloads preserved for reference |
| 6 | Implementation Plan | `notes/implementation-notes.md` — ordered fix strategy (ready for Ticket 1002) |

---

## 7. Proposed Timeline

| Phase | Tasks | Est. Effort |
|---|---|---|
| **Phase 1** (COMPLETE) | PSI API calls, raw data collection, site stack detection | 1 hr |
| **Phase 2** (THIS PLAN) | Analysis, report generation, recommendations | 2–3 hrs |
| **Phase 3** (SEPARATE TICKET) | Fix implementation, re-testing, verification | TBD |

---

## 8. Key Risk Areas Identified

1. **Divi theme overhead** — `scripts.min.js` 62% unused, forced reflow issues
2. **Plugin bloat** — 14+ plugins on a single page load
3. **Image pipeline** — PNG sources from 2022, no WebP conversion pipeline active
4. **Layout shifts** — Hero section + inner rows shifting 0.294 CLS
5. **Font cascade** — 13 font requests across 2 origins
6. **Trustindex** — 94 KiB third-party payload, 0 cache TTL

---

## 9. Next Steps / Approval Gate

Review this plan. Once approved:
1. I will produce the full `reports/1001-full-analysis.md` with detailed issue breakdown
2. Generate the prioritized recommendation list
3. Map each issue to specific code/plugin files
4. Create the implementation roadmap for Ticket 1002

---

**Assigned to:** Chester
**Target for Phase 2 delivery:** Upon approval
