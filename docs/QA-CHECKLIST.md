# Ticket #1001 — QA Report

**Website:** basespawellness.com
**QA Tester:** Jean Airiz
**Date:** July 22, 2026
**Overall Result:** FAIL — 42% pass rate

---

## Quick Summary

```
 Performance   ██████░░░░░░░░░░░░░░░░░░  46/100  FAIL
 Accessibility ████████████████░░░░░░░░  83/100  FAIL
 Best Practices███████████████████████ 100/100  PASS
 SEO           ██████████████████░░░░░░  92/100  FAIL

 Mobile LCP: 10.2s (target ≤2.5s)    CLS: 0.295 (target ≤0.1)
```

---

## What's Working ✓

| Item | Detail |
|---|---|
| WebP conversion active | Images served as WebP |
| Delay JavaScript execution | WP Rocket Delay JS is ON |
| Meta title | "Medical Spa in Chesterton, IN \| BASE Spa & Wellness" |
| Meta description | Present, 150 chars |
| Canonical URL | Correctly points to basespawellness.com |
| Indexability | No noindex — page is indexable |
| min-height CSS for CLS | Carousel container has min-height |
| 0 broken images | All 26 images load (all viewports) |
| TBT 20ms | Total Blocking Time is good |
| Desktop Best Practices 100 | Mobile score is clean |

---

## What's Broken ✗

### HIGH PRIORITY

| # | Issue | Impact | Fix |
|---|---|---|---|
| 1 | **Mobile Performance 46/100** | LCP 10.2s, CLS 0.295 | Apply Pass 1-3 fixes |
| 2 | **WP Rocket Remove Unused CSS OFF** | 97KB wasted CSS | Enable in WP Rocket settings |
| 3 | **LazyLoad OFF** | All images load upfront | Enable WP Rocket LazyLoad |
| 4 | **easypiechart.js still loading** | Console errors on all devices | Disable in Divi → Performance |
| 5 | **Trustindex cache TTL = 0** | 22KB re-downloaded every visit | Add Cloudflare page rule |

### ACCESSIBILITY

| # | Issue | Fix |
|---|---|---|
| 6 | **Pinch-zoom blocked** (`user-scalable=0`) | Remove from viewport meta |
| 7 | **No `<main>` landmark** | Wrap content in `<main>` |
| 8 | **Heading skip: H1 → H4** | Fix heading hierarchy in Divi modules |
| 9 | **4 "LEARN MORE" generic links** | Add descriptive text or aria-label |

### SEO

| # | Issue | Fix |
|---|---|---|
| 10 | **SEO 92/100** (target ≥95) | Fix heading structure, link text |
| 11 | **Heading structure not sequential** | Same as #8 above |

---

## Needs Attention ⚠

| # | Issue | Detail |
|---|---|---|
| W1 | 404 errors on tablet/mobile | 4 resource 404s on Tablet & Mobile, 1 on Desktop |
| W2 | 30 font files loaded | FontAwesome + Google Fonts still bloating the page |
| W3 | 47-97 external scripts | Too many JS files — consider combining |
| W4 | HTML size 1169-1256KB | Page is heavy — needs CSS/JS cleanup |
| W5 | DOM elements ~1320-1700 | Above 1400 threshold on Tablet/Mobile |
| W6 | Sticky menu not detected | No fixed header found during automated check |
| W7 | 11 image filenames not found | Checklist images may be renamed — needs manual verification |

---

## Manual Checks Pending 👁 (16 items)

### Visual (Layout — Section D)
- D4: Mobile view — no overlapping elements
- D5: Tablet view — looks correct
- D6: Desktop view — looks correct
- D7: Proper spacing and whitespace
- D8: Font consistency across sections
- D9: Button consistency (size, color, hover)

### Visual (Accessibility — Section E)
- E6: Color contrast WCAG AA
- E7: Links have discernible names
- E8: aria-label added where needed

### Functionality (Section H)
- H2: Desktop nav menu works
- H3: Mobile burger menu works
- H7: Menu items clickable
- H8: VIP Beauty Bank carousel works
- H9: Gravity Forms submit & validate
- H10: Contact Form 7 submit & validate
- H12: Cookie consent banner
- H13: Scroll to top button
- H14: All internal links — no 404s
- H15-H17: Hero image on desktop/iPad/mobile
- H18: Featured image
- H19: Breadcrumbs
- H21-H22: Touch targets, no overlapping

---

## Image Audit — Needs Manual Re-check

The 11 images listed in the original QA checklist were not found by name in the page source. The site may have renamed or replaced them. WebP format *is* detected and active. Manual inspection needed:

```
C1  Evolve-X.png → WebP       C7  BASE-logo-mobile.png → WebP
C2  Saint-Jane-Beauty-Serum    C8  BaseSpa-243.jpg → resize
C3  Laser-01-980x980.png      C9  BaseSpa-274.jpg → resize
C4  Facials-01-980x980.png    C10 Service icons → 195x195
C5  Injectables-980x980.png   C11 VIP-Beauty-Bank.webp
C6  sunlesstan-01-980x980.png C12 Brandi Robertson images
```

---

## Automation Results

```
Python QA (curl + PSI):   B:FAIL  C:WARN  D:WARN  E:FAIL  F:PASS  G:WARN
Playwright QA (browser):  32 PASS / 21 FAIL / 19 WARN / 3 N/A
Overall: FAIL
```

PageSpeed API was unreachable during this run — performance scores are from prior audit data (June 9, 2026). Re-run PSI when API is available.

---

## Next Steps (Ticket 1002)

1. Enable WP Rocket Remove Unused CSS (5 min)
2. Enable WP Rocket LazyLoad (5 min)
3. Disable easypiechart.js in Divi Performance (5 min)
4. Add Cloudflare cache rule for Trustindex (10 min)
5. Convert remaining images to WebP (2-3 hr)
6. Fix accessibility: viewport zoom, `<main>`, headings, link text (1 hr)
7. Complete 16 manual checks
8. Re-run PSI API to confirm score improvements

---

## How to Run QA

```bash
# Full automated QA (Python + Playwright)
python3 scripts/qa_automated.py full-report basespawellness.com
npm run qa:playwright -- https://www.basespawellness.com

# Individual checks
python3 scripts/qa_automated.py psi basespawellness.com      # PageSpeed only
npm run check:images -- https://www.basespawellness.com      # Broken images
npm run check -- https://www.basespawellness.com             # Button checks
npm run dashboard                                             # Open web UI at :8766

# Manual checks needed
open reports/qa-full-1784677324185/report.html               # Playwright HTML report
```

| Icon | Meaning |
|---|---|
| ✓ | PASS — no action needed |
| ✗ | FAIL — needs fix |
| ⚠ | WARN — investigate |
| 👁 | Manual check required |

---

**QA Tester:** Jean Airiz
**Date:** July 22, 2026
