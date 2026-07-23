# SEO & QA Audit — Test Bank

## Category 1: Static Checks (HTML)

### TC-01: Title Tag
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-01.1 | Title present, optimal length | Page with `<title>` 40-50 chars | PASS — "GOOD" | P0 |
| TC-01.2 | Title too long | Page with `<title>` 65+ chars | FAIL — "TOO LONG" | P0 |
| TC-01.3 | Title warning length | Page with `<title>` 51-60 chars | PASS — "WARNING" | P0 |
| TC-01.4 | Title missing | Page without `<title>` tag | FAIL — "MISSING" | P0 |
| TC-01.5 | Empty title | `<title></title>` | FAIL — "MISSING" | P1 |

### TC-02: Meta Description
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-02.1 | Meta desc present, optimal | `<meta name="description">` 120-150 chars | PASS — "GOOD" | P0 |
| TC-02.2 | Meta desc too long | 170+ chars | FAIL — "TOO LONG" | P0 |
| TC-02.3 | Meta desc warning | 151-160 chars | PASS — "WARNING" | P0 |
| TC-02.4 | Meta desc missing | No description meta tag | FAIL — "MISSING" | P0 |
| TC-02.5 | Meta desc with special chars | Description containing `"` and special chars | PASS — properly read | P1 |

### TC-03: Headings
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-03.1 | Single H1, proper hierarchy | 1 H1 + H2, H3 subheadings | PASS | P0 |
| TC-03.2 | Missing H1 | No H1 tag on page | FAIL — "Missing H1" | P0 |
| TC-03.3 | Multiple H1 tags | 2+ H1 tags | FAIL — "Multiple H1" | P0 |
| TC-03.4 | No headings at all | Page with zero heading tags | FAIL — h1_count=0 | P1 |
| TC-03.5 | Nested heading text | Headings with inline `<span>`, `<strong>` | PASS — text extracted correctly | P1 |
| TC-03.6 | HTML entities in headings | `&amp;`, `&copy;` in heading text | PASS — unescaped correctly | P2 |

### TC-04: Schema Markup
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-04.1 | JSON-LD schema present | Valid `application/ld+json` script | PASS — types detected | P0 |
| TC-04.2 | Multiple schema blocks | 2+ JSON-LD scripts (Organization, WebPage) | PASS — count=2, types listed | P0 |
| TC-04.3 | @graph schema | JSON-LD with `@graph` array | PASS — all types extracted | P1 |
| TC-04.4 | Microdata (itemtype) | `itemtype="http://schema.org/Product"` | PASS — type detected | P1 |
| TC-04.5 | No schema at all | Page with no structured data | FAIL — count=0 | P0 |
| TC-04.6 | Malformed JSON-LD | Invalid JSON in ld+json script | PASS — skipped gracefully | P2 |

### TC-05: Image Alt Text
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-05.1 | All images have alt | Every `<img>` has alt attribute | PASS — missing=0 | P0 |
| TC-05.2 | Some images missing alt | 5/23 images lack alt | FAIL — missing=5 | P0 |
| TC-05.3 | Empty alt (decorative) | `<img alt="">` | PASS — has alt attribute | P1 |
| TC-05.4 | No images on page | Zero `<img>` tags | PASS — total=0, missing=0 | P2 |

### TC-06: Viewport (Responsive)
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-06.1 | Standard viewport meta | `<meta name="viewport" content="width=device-width, initial-scale=1">` | PASS | P0 |
| TC-06.2 | Missing viewport | No viewport meta tag | FAIL | P0 |
| TC-06.3 | Custom viewport | Viewport without `width=device-width` | FAIL | P1 |
| TC-06.4 | Reversed attribute order | `content` before `name` | PASS — still detected | P2 |

### TC-07: Indexability
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-07.1 | Indexable (no robots) | No robots meta tag | PASS — indexable=true | P0 |
| TC-07.2 | Noindex directive | `<meta name="robots" content="noindex">` | FAIL — indexable=false | P0 |
| TC-07.3 | Noindex, nofollow | `content="noindex, nofollow"` | FAIL — indexable=false | P1 |
| TC-07.4 | Index, follow | `content="index, follow"` | PASS | P2 |

### TC-08: Canonical
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-08.1 | Canonical matches URL | Canonical href = page URL | PASS — matches=true | P0 |
| TC-08.2 | Canonical different URL | Canonical points to another URL | FAIL — matches=false | P0 |
| TC-08.3 | No canonical tag | No canonical link element | FAIL — href="" | P1 |
| TC-08.4 | Self-referencing canonical | Canonical = same URL (no trailing slash diff) | PASS — matches=true | P1 |

### TC-09: Internal Links
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-09.1 | All internal links work | 40 internal links, all 200 OK | PASS — broken=0 | P0 |
| TC-09.2 | Broken internal link | At least 1 link returns 404 | FAIL — broken≥1 | P0 |
| TC-09.3 | External links excluded | Links to other domains not counted | PASS — only same-domain checked | P1 |
| TC-09.4 | Anchor/JS links skipped | `#section`, `javascript:void(0)` | PASS — excluded from count | P1 |
| TC-09.5 | Quick mode skips verification | `--quick` flag active | PASS — skipped, no broken check | P2 |

### TC-10: OG Tags
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-10.1 | All 6 OG tags present | og:title, description, image, url, type, site_name | PASS — 6/6 found | P0 |
| TC-10.2 | Partial OG tags | Only 2 tags present | FAIL — 2/6 | P0 |
| TC-10.3 | No OG tags | No og: meta tags | FAIL — 0/6 | P1 |
| TC-10.4 | OG tags with title+desc only | og:title + og:description present | PASS — tags_found≥2 means passed | P1 |

### TC-11: SSL / HTTPS
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-11.1 | HTTPS with valid cert | `https://example.com` | PASS | P0 |
| TC-11.2 | HTTP only (no SSL) | `http://example.com` | FAIL | P0 |
| TC-11.3 | HTTPS with expired cert | Valid HTTPS URL, expired certificate | FAIL — cert_valid=false | P1 |

---

## Category 2: Dynamic Checks (Playwright)

### TC-12: Image Loading
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-12.1 | All images load | Every img has naturalWidth > 0 | PASS — broken=0 | P0 |
| TC-12.2 | Broken image detected | 1+ img has naturalWidth = 0 | FAIL — broken≥1 | P0 |
| TC-12.3 | Lazy-loaded images | Images load after scroll | PASS — scroll triggers load | P1 |
| TC-12.4 | Quick mode skips | `--quick` flag | PASS — skipped | P1 |
| TC-12.5 | SVG images | Inline SVG and `<img src="...svg">` | PASS — handled correctly | P2 |

### TC-13: Hero Image (Desktop / iPad / Mobile)
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-13.1 | Hero via img tag | Large img near top (≥250px wide, ≥160px tall) | PASS — method=img | P0 |
| TC-13.2 | Hero via CSS background | `background-image` on top section | PASS — method=css-bg | P0 |
| TC-13.3 | Hero via section detection | Large block element at top | PASS — method=section | P0 |
| TC-13.4 | No hero found | No large image/section near top | FAIL — "No hero image found" | P0 |
| TC-13.5 | Hero works on iPad | Banner scales correctly on 768x1024 | PASS | P1 |
| TC-13.6 | Hero works on Mobile | Banner displays on 375x667 | PASS | P1 |

### TC-14: Breadcrumbs
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-14.1 | Schema breadcrumbs | `BreadcrumbList` in JSON-LD | PASS — method=structured_data | P0 |
| TC-14.2 | HTML breadcrumbs | `<nav aria-label="breadcrumb">` | PASS — method=html | P0 |
| TC-14.3 | CSS class breadcrumbs | Element with class `breadcrumb` or `breadcrumbs` | PASS — method=html | P1 |
| TC-14.4 | No breadcrumbs | No breadcrumb indicators found | FAIL — exists=false | P1 |

### TC-15: Menu Clickability
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-15.1 | Menu links detected | Nav/header/menu links found | PASS — total_links≥1 | P0 |
| TC-15.2 | Empty menu | No nav links found | PASS — total_links=0 | P1 |
| TC-15.3 | Dropdown menu links | Links in dropdown submenus | PASS — counted in total | P1 |

### TC-16: Font Consistency
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-16.1 | Single font family | All headings/body use same font | PASS — unique=1 | P0 |
| TC-16.2 | Multiple font families | 3+ different font families | PASS — informational only | P1 |
| TC-16.3 | Custom web fonts | Google Fonts, Adobe Fonts loaded | PASS — detected correctly | P1 |

### TC-17: Button Consistency
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-17.1 | Uniform button styles | All buttons share same padding, font | PASS — unique_styles=low | P0 |
| TC-17.2 | Varied button styles | Different padding/font-size across buttons | PASS — informational only | P1 |
| TC-17.3 | No buttons on page | Zero button/link elements | PASS — unique_styles=0 | P2 |

### TC-18: Contact Forms
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-18.1 | Standard form present | `<form>` with input/textarea | PASS — found=form | P0 |
| TC-18.2 | Popup/modal form | Form inside `.popup`, `.modal` | PASS — found=popup | P0 |
| TC-18.3 | Third-party widget | HubSpot, Gravity Forms, CF7 | PASS — found=widget | P1 |
| TC-18.4 | No forms found | Page has no contact form | FAIL — count=0 | P1 |
| TC-18.5 | Shadow DOM form | Form inside shadow root | PASS — found=shadow-dom | P2 |

---

## Category 3: CDP Checks (Chrome DevTools Protocol)

### TC-19: Console Errors
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-19.1 | No console errors | Clean page load, no JS errors | PASS — errors=0 | P0 |
| TC-19.2 | Console errors present | Page throws JS errors | FAIL — errors≥1 | P0 |
| TC-19.3 | Tracker warnings excluded | google-analytics, gtm, fb pixel warnings | PASS — filtered out | P1 |
| TC-19.4 | Quick mode skips CDP | `--quick` flag | PASS — skipped | P1 |

### TC-20: Failed Network Requests
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-20.1 | All requests succeed | Zero failed network requests | PASS — failed=0 | P0 |
| TC-20.2 | Failed requests present | 404/500 errors on resources | FAIL — failed≥1 | P0 |
| TC-20.3 | Tracker failures excluded | Analytics/tracker failures filtered | PASS — not counted | P1 |

### TC-21: Core Web Vitals
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-21.1 | LCP good (≤2.5s) | Largest Contentful Paint under 2.5s | PASS | P0 |
| TC-21.2 | LCP poor (>4.0s) | LCP over 4 seconds | FAIL — -25 score | P0 |
| TC-21.3 | CLS good (≤0.1) | Cumulative Layout Shift under 0.1 | PASS | P0 |
| TC-21.4 | CLS poor (>0.25) | CLS over 0.25 | FAIL — -25 score | P0 |
| TC-21.5 | TTFB good (≤0.8s) | Time to First Byte under 0.8s | PASS | P0 |
| TC-21.6 | Performance score ≥70 | Overall perf score 70+ | PASS | P1 |
| TC-21.7 | Performance score <70 | Overall perf score below 70 | FAIL | P1 |

---

## Category 4: Visual / Layout Checks

### TC-22: Sticky Menu (Desktop / iPad / Mobile)
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-22.1 | Menu sticks on scroll | Header stays at top after scroll (fixed/sticky) | PASS — has_sticky=true | P0 |
| TC-22.2 | Menu does NOT stick | Header scrolls away | FAIL — "no sticky detected" | P0 |
| TC-22.3 | No header found | No header/nav element on page | FAIL — "No header/nav found" | P0 |
| TC-22.4 | Sticky on Desktop (1280x800) | Menu fixed on desktop size | PASS | P0 |
| TC-22.5 | Sticky on iPad (768x1024) | Menu fixed on tablet size | PASS | P0 |
| TC-22.6 | Sticky on Mobile (375x667) | Menu fixed on mobile size | PASS | P0 |
| TC-22.7 | Burger menu sticky (mobile) | Hamburger menu stays fixed | PASS | P1 |
| TC-22.8 | Evidence screenshot captured | Screenshot saved after scroll | Screenshot file exists | P1 |

### TC-23: Featured Image
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-23.1 | og:image present and loads | Valid og:image URL, image loads | PASS | P0 |
| TC-23.2 | og:image missing | No og:image meta tag | FAIL — "No og:image found" | P0 |
| TC-23.3 | og:image broken URL | og:image points to 404 | FAIL — image_exists=false | P1 |
| TC-23.4 | Twitter image fallback | `twitter:image` present, no og:image | PASS — uses twitter:image | P1 |

### TC-24: Whitespace
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-24.1 | Proper spacing | No elements too close to each other | PASS — issues=0 | P1 |
| TC-24.2 | Overlapping elements | Two text elements touching/overlapping | FAIL — issues≥1 | P1 |
| TC-24.3 | Zero-margin stacking | h1 directly touching p below | FAIL — spacing issue detected | P2 |

---

## Category 5: Output & Reporting

### TC-25: HTML Report
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-25.1 | Report generated | Audit completes successfully | HTML file created in reports/ | P0 |
| TC-25.2 | Score calculation | 15/19 checks pass | Score ~78.9%, Grade B | P0 |
| TC-25.3 | All sections present | Static, Dynamic, CDP, Evidence | 4 sections in report | P0 |
| TC-25.4 | Evidence screenshots | Sticky + Image loading screenshots | Screenshots embedded as base64 | P1 |
| TC-25.5 | file:// URL displayed | Terminal output after audit | `file:///path/to/report.html` printed | P1 |
| TC-25.6 | Compact layout | Report uses min-width grid | No horizontal scroll at 1280px | P2 |

### TC-26: JSON Report
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-26.1 | JSON generated | Audit completes | JSON file alongside HTML | P0 |
| TC-26.2 | Valid JSON structure | All fields populated | JSON parseable, no null required fields | P0 |
| TC-26.3 | Quick mode flag in JSON | `--quick` used | `"quick_mode": true` in JSON | P2 |

### TC-27: PDF Report
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-27.1 | PDF generated | `--pdf` flag used | PDF file created in reports/ | P1 |
| TC-27.2 | PDF not generated without flag | No `--pdf` flag | No PDF file created | P1 |
| TC-27.3 | PDF has correct content | Open PDF | Contains score, checks, screenshots | P2 |

### TC-28: Batch Mode
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-28.1 | Multiple URLs | 3 URLs as args | 3 reports generated | P1 |
| TC-28.2 | URLs from file | `--file urls.txt` | All URLs in file audited | P1 |
| TC-28.3 | Comma-separated input | `url1.com, url2.com` | Both audited | P1 |
| TC-28.4 | Batch summary printed | After batch completes | Summary table with scores | P1 |
| TC-28.5 | Browser reused in batch | Multiple URLs | Single browser instance used | P2 |

### TC-29: Flags
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-29.1 | --quick flag | `--quick example.com` | CDP + image load + links skipped | P1 |
| TC-29.2 | --pdf flag | `--pdf example.com` | PDF generated alongside HTML | P1 |
| TC-29.3 | --email flag | `--email test@test.com` with SMTP env | Email sent | P2 |
| TC-29.4 | --email missing SMTP | `--email` without SMTP_* env vars | Prints "Email skipped" | P2 |

### TC-30: History Tracking
| ID | Test Case | Input / Scenario | Expected Result | Priority |
|---|---|---|---|---|
| TC-30.1 | First audit | Domain never audited before | "First audit for domain.com" | P1 |
| TC-30.2 | Second audit | Same domain audited again | Shows previous score + delta with arrow | P1 |
| TC-30.3 | Score improvement | Score went up | Shows ↑ and +X% | P2 |
| TC-30.4 | Score decline | Score went down | Shows ↓ and -X% | P2 |

---

## Summary

| Category | Test Count | P0 | P1 | P2 |
|---|---|---|---|---|
| Static Checks | 29 | 16 | 10 | 3 |
| Dynamic Checks | 20 | 9 | 9 | 2 |
| CDP Checks | 11 | 5 | 6 | 0 |
| Visual Checks | 12 | 7 | 4 | 1 |
| Output / Reporting | 17 | 3 | 10 | 4 |
| **Total** | **89** | **40** | **39** | **10** |

**Priority Key:** P0 = Critical (must pass before release) | P1 = Important | P2 = Nice to have
