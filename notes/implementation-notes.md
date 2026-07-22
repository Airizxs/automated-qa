# Ticket #1001 — Implementation Plan (Ready for Ticket 1002)

**Domain:** basespawellness.com
**Date:** 2026-06-09
**Previous ticket:** #8921 (content updates)
**Next ticket:** #1002 (performance fixes)
**Status:** Analysis complete — ready for implementation sprint

---

## Implementation Order

The fix plan is organized into 3 implementation passes. Each pass builds on the previous.

---

## Pass 1: WP Rocket Configuration (30 min — No Code Changes)

| # | Task | Time | Verification |
|---|---|---|---|
| 1.1 | Enable **Remove Unused CSS** in WP Rocket → File Optimization | 2 min | Check CSS payload reduced in DevTools |
| 1.2 | Enable **Delay JavaScript Execution** in WP Rocket → File Optimization | 2 min | Verify site functions normally post-load |
| 1.3 | Enable **LazyLoad** for images (verify already on) | 1 min | Check images load on scroll |
| 1.4 | Enable **WebP conversion** via Imagify integration in WP Rocket | 5 min | Verify WebP served after cache clear |
| 1.5 | Set **Google Fonts optimization** in WP Rocket | 2 min | Check font requests combined |
| 1.6 | Add **Preload Fonts** (Marcellus, Amiko) in WP Rocket | 3 min | Verify `<link rel="preload">` in HTML |
| 1.7 | Add **Preconnect** hints for `fonts.gstatic.com`, `cdn.trustindex.io` | 3 min | Check preconnect in request waterfall |
| 1.8 | Disable Divi **easypiechart.js** dynamic asset (Divi → Performance) | 2 min | Check console for timeout error gone |
| 1.9 | Purge WP Rocket cache + Cloudflare cache | 2 min | — |
| 1.10 | **Re-run PageSpeed** to measure improvement | 8 min | Target: Performance 46 → ~65 |

**Expected result after Pass 1:** Performance 46 → 60–70

---

## Pass 2: Image & CLS Fixes (2-3 hours — Code/Content Changes)

| # | Task | Files | Time |
|---|---|---|---|
| 2.1 | **Batch convert all PNGs to WebP** — use Imagify batch optimization (WP Rocket) | All images in Media Library | 20 min |
| 2.2 | **Regenerate thumbnails** for service icons at correct display sizes (195×195 instead of 1250×1250) | Service icon images | 30 min |
| 2.3 | **Replace oversized originals** — Evolve-X.png, Saint-Jane-Beauty-Serum.png with properly sized WebP | These 2 images in their Divi modules | 15 min |
| 2.4 | **Fix VIP Beauty Bank carousel CLS** — add `min-height` CSS to carousel container | Divi Machine carousel module CSS | 15 min |
| 2.5 | **Compress and resize** BaseSpa-243.jpg and BaseSpa-274.jpg | Homepage About section images | 10 min |
| 2.6 | **Replace BASE-logo-mobile.png** with properly sized WebP | Logo image in theme header | 10 min |
| 2.7 | **Optimize Brandi Robertson section (desktop)** — resize + aspect ratio fix | Staff images | 15 min |
| 2.8 | Purge caches + re-run PageSpeed | — | 10 min |

**Expected result after Pass 2:** Performance 65 → 75–85, CLS 0.295 → <0.05

---

## Pass 3: Accessibility, SEO & Polish (1 hour)

| # | Task | Location | Time |
|---|---|---|---|
| 3.1 | **Fix viewport meta** — remove `user-scalable=0, maximum-scale=1.0` | Divi Theme Customizer or child theme `header.php` | 5 min |
| 3.2 | **Add `<main>` landmark** — wrap content area | Divi theme wrapper (`footer.php` or `singular.php`) | 5 min |
| 3.3 | **Fix heading order** — adjust H2→H4 to H2→H3 or H2→H2 | Homepage Divi text modules | 10 min |
| 3.4 | **Replace generic "LEARN MORE" links** — add descriptive text or `aria-label` | Divi button modules (7 instances) | 15 min |
| 3.5 | **Fix color contrast** — 15+ issues identified | Various Divi text/background combinations | 20 min |
| 3.6 | **Configure Trustindex cache** via Cloudflare page rule | Cloudflare dashboard | 5 min |
| 3.7 | Update outdated plugins (if safe) | MainWP | 10 min |

**Expected result after Pass 3:** Accessibility 83 → 90+, SEO 92 → 95+

---

## Files to Modify (Read-Only During This Audit)

### Will need edits (no changes made during audit):
1. `wp-content/themes/NKP-Child-Theme-1/header.php` — viewport meta
2. `wp-content/themes/NKP-Child-Theme-1/footer.php` — main landmark wrapper
3. WordPress Media Library — image replacements
4. Divi page content (252327) — heading levels, link text, images
5. Divi Machine carousel module — CLS fix CSS
6. WP Rocket dashboard — configuration toggles
7. Cloudflare dashboard — caching rule
8. Divi Theme Options → Performance settings

### Will NOT modify:
- Divi core theme files (`/themes/Divi/`) — updates would overwrite changes
- Plugin PHP files — except through admin configuration

---

## Rollback Plan

Each fix in Passes 1-3 is individually revertible:
- **Pass 1:** Toggle WP Rocket settings back
- **Pass 2:** Restore original images from Media Library, remove added CSS
- **Pass 3:** Revert theme edits from child theme backups

---

## Estimated Total Effort

| Pass | Time | Personnel |
|---|---|---|
| Pass 1: WP Rocket config | 30 min | 1 dev |
| Pass 2: Images + CLS | 2–3 hr | 1 dev |
| Pass 3: A11y + SEO | 1 hr | 1 dev |
| **Total** | **3.5–4.5 hr** | **1 dev** |

---

## Verification Gate (for Ticket 1002)

After all passes complete:
1. Run **mobile PageSpeed** audit — target: Performance ≥ 75, Accessibility ≥ 90
2. Run **desktop PageSpeed** audit — target: Performance ≥ 90
3. Manual QA: browse all optimized pages, verify no visual regressions
4. Check Trustindex reviews widget still loads correctly
5. Check Gravity Forms still functional
6. Check all carousels/sliders work correctly
7. Generate comparison report (before/after scores)

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| WP Rocket Remove Unused CSS breaks page layout | Medium | Test on staging first; keep backup |
| LazyLoad breaks carousel images | Low | Set WP Rocket to exclude carousel container from lazy load |
| WebP conversion quality loss | Low | Use 80-85 quality setting |
| Divi update wipes custom settings | Low | All changes in child theme or WP Rocket, not core Divi |

---

## Open Questions (for handover)

1. Is there a staging/sandbox environment for basespawellness.com?
2. Are FontAwesome icons actively used anywhere, or can we disable?
3. Is the Trustindex widget needed on every page or just homepage?
4. Who has Cloudflare API token with Cache Purge permission?
5. Any upcoming Divi 5 migration plans? (Would change all optimization strategies)
