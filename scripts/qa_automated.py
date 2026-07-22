#!/usr/bin/env python3
"""
qa_automated.py — Automated QA checks for Ticket #1001
Generates a full JSON report matching the QA-CHECKLIST.md categories.

Usage:
  python3 scripts/qa_automated.py check basespawellness.com
  python3 scripts/qa_automated.py full-report basespawellness.com
  python3 scripts/qa_automated.py psi basespawellness.com
"""

import json, subprocess, sys, os, re
from datetime import datetime
from urllib.parse import urlparse, urljoin

PSI_API_KEY = os.environ.get("GOOGLE_PAGESPEED_API_KEY") or "AIzaSyBP-S7D4XIAEO0HjgcuZOk8JDfgbwTQhkc"

# ─── HELPERS ──────────────────────────────────────────────────

def _curl(url: str, timeout: int = 15) -> str:
    try:
        r = subprocess.run(["curl", "-sL", url], capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except:
        return ""

def _curl_head(url: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(["curl", "-sI", url], capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except:
        return ""

def _resolve_url(input_str: str) -> str:
    """Convert domain or partial URL to full URL. Accepts both."""
    if "://" in input_str:
        return input_str
    input_str = input_str.rstrip("/")
    if input_str.startswith("www."):
        return f"https://{input_str}/"
    if "." in input_str and not input_str.startswith("http"):
        return f"https://www.{input_str}/"
    return f"https://{input_str}/"

def _get_html(input_str: str) -> str:
    return _curl(_resolve_url(input_str))

def _run_psi(url: str, strategy: str = "mobile") -> dict:
    import requests
    params = {
        "url": url,
        "key": PSI_API_KEY,
        "strategy": strategy,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    }
    resp = requests.get(
        "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
        params=params, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

# ─── SECTION A: PERFORMANCE SCORES ────────────────────────────

def check_performance(input_str: str) -> dict:
    url = _resolve_url(input_str)
    results = {"psi_mobile": {}, "psi_desktop": {}, "status": "PASS"}
    try:
        mobile = _run_psi(url, "mobile")
        desktop = _run_psi(url, "desktop")
        lr_m = mobile.get("lighthouseResult", {})
        lr_d = desktop.get("lighthouseResult", {})

        cats_m = lr_m.get("categories", {})
        cats_d = lr_d.get("categories", {})

        audits_m = lr_m.get("audits", {})
        audits_d = lr_d.get("audits", {})

        results["psi_mobile"] = {
            "performance": round(cats_m.get("performance", {}).get("score", 0) * 100),
            "accessibility": round(cats_m.get("accessibility", {}).get("score", 0) * 100),
            "best_practices": round(cats_m.get("best-practices", {}).get("score", 0) * 100),
            "seo": round(cats_m.get("seo", {}).get("score", 0) * 100),
            "lcp_ms": audits_m.get("largest-contentful-paint", {}).get("numericValue"),
            "cls": audits_m.get("cumulative-layout-shift", {}).get("numericValue"),
            "fcp_ms": audits_m.get("first-contentful-paint", {}).get("numericValue"),
            "tbt_ms": audits_m.get("total-blocking-time", {}).get("numericValue"),
            "si_ms": audits_m.get("speed-index", {}).get("numericValue"),
            "tti_ms": audits_m.get("interactive", {}).get("numericValue"),
        }
        results["psi_desktop"] = {
            "performance": round(cats_d.get("performance", {}).get("score", 0) * 100),
            "accessibility": round(cats_d.get("accessibility", {}).get("score", 0) * 100),
            "best_practices": round(cats_d.get("best-practices", {}).get("score", 0) * 100),
            "seo": round(cats_d.get("seo", {}).get("score", 0) * 100),
            "lcp_ms": audits_d.get("largest-contentful-paint", {}).get("numericValue"),
            "cls": audits_d.get("cumulative-layout-shift", {}).get("numericValue"),
        }

        # Check pass/fail thresholds
        pm = results["psi_mobile"]
        if pm["performance"] < 65: results["status"] = "FAIL"
        if pm["lcp_ms"] and pm["lcp_ms"] > 2500: results["status"] = "FAIL"
        if pm["cls"] and pm["cls"] > 0.1: results["status"] = "FAIL"
        if pm["fcp_ms"] and pm["fcp_ms"] > 1800: results["status"] = "FAIL"

    except Exception as e:
        results["status"] = "ERROR"
        results["error"] = str(e)

    return results

# ─── SECTION B: WP ROCKET ─────────────────────────────────────

def check_wp_rocket(input_str: str) -> dict:
    html = _get_html(input_str)
    results = {"checks": []}

    # Remove Unused CSS — WP Rocket adds critical CSS link
    has_critical_css = "rocket-critical-css" in html or "data-rocket-critical-css" in html
    results["checks"].append({
        "id": "B1", "name": "remove_unused_css",
        "status": "PASS" if has_critical_css else "FAIL",
        "detail": "Critical CSS detected" if has_critical_css else "No critical CSS — Remove Unused CSS may be off"
    })

    # Delay JS — WP Rocket adds data-rocket-defer
    has_delay = "data-rocket-defer" in html
    results["checks"].append({
        "id": "B2", "name": "delay_js",
        "status": "PASS" if has_delay else "FAIL",
        "detail": "data-rocket-defer found" if has_delay else "No delayed JS detected"
    })

    # LazyLoad
    has_lazy = 'loading="lazy"' in html
    results["checks"].append({
        "id": "B3", "name": "lazyload",
        "status": "PASS" if has_lazy else "FAIL",
        "detail": "loading=lazy found" if has_lazy else "No lazy loading detected"
    })

    # WebP — check if images serve as webp
    imgs = re.findall(r'(https://[^"\']+\.(?:png|jpg|jpeg)[^"\']*)', html, re.IGNORECASE)
    webp_found = False
    for img_url in sorted(set(imgs))[:5]:
        h = _curl_head(img_url)
        if "image/webp" in h.lower():
            webp_found = True
            break
    results["checks"].append({
        "id": "B4", "name": "webp_conversion",
        "status": "PASS" if not imgs else ("PASS" if webp_found else "WARN"),
        "detail": f"WebP detected" if webp_found else f"No WebP detected — {len(imgs)} PNG/JPG found"
    })

    results["overall"] = "PASS" if all(c["status"] == "PASS" for c in results["checks"]) else "FAIL"
    return results

# ─── SECTION C: IMAGE OPTIMIZATION ────────────────────────────

def check_images(input_str: str) -> dict:
    html = _get_html(input_str)
    results = {"checks": [], "all_images": []}

    # Find all images
    imgs = re.findall(r'(https://[^"\']+\.(?:png|jpg|jpeg|webp|gif|svg)[^"\']*)', html, re.IGNORECASE)
    seen = set()

    for img_url in sorted(set(imgs)):
        if img_url in seen: continue
        seen.add(img_url)
        h = _curl_head(img_url)
        size_match = re.search(r'content-length:\s*(\d+)', h, re.IGNORECASE)
        ct_match = re.search(r'content-type:\s*(\S+)', h, re.IGNORECASE)
        size_kb = int(size_match.group(1)) // 1024 if size_match else 0
        content_type = ct_match.group(1) if ct_match else "unknown"
        status_code = "OK"

        entry = {
            "url": img_url,
            "size_kb": size_kb,
            "format": content_type,
            "status": "PASS"
        }

        if img_url.endswith(".png") and size_kb > 10:
            entry["status"] = "FAIL"
            entry["reason"] = f"PNG {size_kb}KB — should be WebP"
        elif img_url.endswith(".png"):
            entry["status"] = "WARN"
            entry["reason"] = "PNG under 10KB, still consider WebP"

        results["all_images"].append(entry)
        if entry["status"] == "FAIL":
            results["checks"].append({
                "id": "C_img", "name": "oversized_png",
                "status": "FAIL", "detail": f"{img_url.split('/')[-1]} — {size_kb}KB"
            })

    # Check specific critical images from the report
    critical_images = [
        "Evolve-X", "Saint-Jane-Beauty-Serum", "Laser-01", "Facials-01",
        "Injectables", "sunlesstan", "BASE-logo-mobile", "BaseSpa-243",
        "BaseSpa-274", "VIP-Beauty-Bank", "Brandi-Robertson"
    ]
    for name in critical_images:
        found = [i for i in results["all_images"] if name in i["url"]]
        if not found or all(f["status"] == "FAIL" for f in found):
            results["checks"].append({
                "id": "C_critical", "name": f"critical_image_{name}",
                "status": "WARN", "detail": f"{name} not found or still oversized"
            })

    total_size = sum(i.get("size_kb", 0) for i in results["all_images"] if i["size_kb"])
    png_count = len([i for i in results["all_images"] if i["url"].endswith(".png") and i["size_kb"] > 10])

    results["summary"] = f"{png_count} oversized PNGs, ~{total_size}KB total images"
    return results

# ─── SECTION D: LAYOUT ────────────────────────────────────────

def check_layout(input_str: str) -> dict:
    html = _get_html(input_str)
    results = {"checks": []}

    # Check for min-height CSS (CLS fix)
    has_min_height = re.search(r'min-height', html, re.IGNORECASE)
    results["checks"].append({
        "id": "D1", "name": "cls_fix_min_height",
        "status": "PASS" if has_min_height else "WARN",
        "detail": "min-height CSS found" if has_min_height else "No min-height — CLS fix may not be applied"
    })

    # Viewport meta
    vp = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', html, re.IGNORECASE)
    results["checks"].append({
        "id": "D_vp", "name": "viewport_meta",
        "status": "PASS" if vp else "FAIL",
        "detail": vp.group(0)[:120] if vp else "No viewport meta"
    })

    # DOM element count (rough)
    elements = len(re.findall(r'<[a-zA-Z][^>]*>', html))
    results["checks"].append({
        "id": "D_dom", "name": "dom_size",
        "status": "PASS" if elements < 1400 else "WARN",
        "detail": f"~{elements} DOM elements"
    })

    # HTML size
    html_size_kb = len(html) // 1024
    results["checks"].append({
        "id": "D_html", "name": "html_size",
        "status": "PASS" if html_size_kb < 150 else "WARN",
        "detail": f"{html_size_kb}KB HTML"
    })

    results["overall"] = "PASS" if all(c["status"] == "PASS" for c in results["checks"]) else "WARN"
    return results

# ─── SECTION E: ACCESSIBILITY ─────────────────────────────────

def check_accessibility(input_str: str) -> dict:
    html = _get_html(input_str)
    results = {"checks": []}

    # Viewport zoom
    vp = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', html, re.IGNORECASE)
    if vp:
        content = vp.group(0)
        blocks_zoom = "user-scalable=0" in content or "user-scalable=no" in content or "maximum-scale=1.0" in content
        results["checks"].append({
            "id": "E2", "name": "viewport_zoom",
            "status": "FAIL" if blocks_zoom else "PASS",
            "detail": "Zoom blocked" if blocks_zoom else "Zoom allowed"
        })

    # <main> landmark
    has_main = bool(re.search(r'<main[^>]*>', html))
    results["checks"].append({
        "id": "E3", "name": "main_landmark",
        "status": "PASS" if has_main else "FAIL",
        "detail": "<main> found" if has_main else "No <main> landmark"
    })

    # Heading order — check for h2->h4 skip
    headings = re.findall(r'<h([1-6])[^>]*>', html)
    results["checks"].append({
        "id": "E4", "name": "heading_order",
        "status": "PASS",
        "detail": f"Headings found: H{', H'.join(sorted(set(headings), key=int)) if headings else 'none'}"
    })
    if headings:
        for i in range(len(headings) - 1):
            if int(headings[i+1]) > int(headings[i]) + 1:
                results["checks"][-1]["status"] = "FAIL"
                results["checks"][-1]["detail"] = f"Skip detected: H{headings[i]} → H{headings[i+1]}"
                break

    # Generic link text
    generic_links = len(re.findall(r'>\s*LEARN\s*MORE\s*<', html, re.IGNORECASE))
    results["checks"].append({
        "id": "E5", "name": "generic_link_text",
        "status": "FAIL" if generic_links > 0 else "PASS",
        "detail": f"{generic_links} 'LEARN MORE' links found" if generic_links else "No generic links"
    })

    results["overall"] = "PASS" if all(c["status"] == "PASS" for c in results["checks"]) else "FAIL"
    return results

# ─── SECTION F: SEO ──────────────────────────────────────────

def check_seo(input_str: str) -> dict:
    html = _get_html(input_str)
    results = {"checks": []}

    # Title
    title = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
    results["checks"].append({
        "id": "F1", "name": "meta_title",
        "status": "PASS" if title else "FAIL",
        "detail": title.group(1)[:100] if title else "No title tag"
    })

    # Meta description
    desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
    results["checks"].append({
        "id": "F2", "name": "meta_description",
        "status": "PASS" if desc else "FAIL",
        "detail": desc.group(1)[:100] if desc else "No meta description"
    })

    # Canonical
    canon = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']', html, re.IGNORECASE)
    results["checks"].append({
        "id": "F3", "name": "canonical",
        "status": "PASS" if canon else "WARN",
        "detail": canon.group(1) if canon else "No canonical URL"
    })

    # Noindex
    noindex = re.search(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex[^"\']*["\']', html, re.IGNORECASE)
    results["checks"].append({
        "id": "F4", "name": "indexability",
        "status": "FAIL" if noindex else "PASS",
        "detail": "Has noindex directive!" if noindex else "Indexable"
    })

    results["overall"] = "PASS" if all(c["status"] == "PASS" for c in results["checks"]) else "FAIL"
    return results

# ─── SECTION G: THIRD-PARTY ──────────────────────────────────

def check_third_party(input_str: str) -> dict:
    html = _get_html(input_str)
    results = {"checks": []}

    # Trustindex cache headers
    trustindex_urls = re.findall(r'(https://cdn\.trustindex\.io[^"\']*)', html)
    if trustindex_urls:
        h = _curl_head(trustindex_urls[0])
        cache_match = re.search(r'cache-control:\s*([^\r\n]+)', h, re.IGNORECASE)
        has_cache = cache_match and "max-age=0" not in cache_match.group(1).lower()
        results["checks"].append({
            "id": "G1", "name": "trustindex_cache",
            "status": "PASS" if has_cache else "FAIL",
            "detail": f"Cache: {cache_match.group(1) if cache_match else 'none'} — TTL: {cache_match.group(1).split('=')[-1] if cache_match and '=' in cache_match.group(1) else '0'}"
        })
    else:
        results["checks"].append({
            "id": "G1", "name": "trustindex_cache",
            "status": "N/A", "detail": "No Trustindex scripts found on page"
        })

    # easypiechart.js
    has_easypie = "easypiechart" in html
    results["checks"].append({
        "id": "G2", "name": "easypiechart_js",
        "status": "FAIL" if has_easypie else "PASS",
        "detail": "easypiechart.js still loading" if has_easypie else "easypiechart.js not found"
    })

    # FontAwesome
    has_fontawesome = "font-awesome" in html.lower() or "fontawesome" in html.lower() or "fa-solid" in html
    results["checks"].append({
        "id": "G3", "name": "fontawesome_loading",
        "status": "PASS",
        "detail": "FontAwesome detected" if has_fontawesome else "No FontAwesome detected"
    })

    # Script count
    scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
    results["checks"].append({
        "id": "G_scripts", "name": "script_count",
        "status": "PASS" if len(scripts) <= 6 else "WARN",
        "detail": f"{len(scripts)} external scripts loaded"
    })

    # Font count
    fonts = re.findall(r'url\(["\']?(https://[^"\')]+\.(?:woff2?|ttf|eot)[^"\')]*)', html, re.IGNORECASE)
    results["checks"].append({
        "id": "G_fonts", "name": "font_count",
        "status": "PASS" if len(set(fonts)) <= 8 else "WARN",
        "detail": f"{len(set(fonts))} font files loaded"
    })

    results["overall"] = "PASS" if all(c["status"] == "PASS" for c in results["checks"]) else "WARN"
    return results

# ─── FULL REPORT ─────────────────────────────────────────────

def full_report(input_str: str) -> dict:
    url = _resolve_url(input_str)
    print(f"Running full QA report for {url}...\n")

    report = {
        "timestamp": datetime.now().isoformat(),
        "input": input_str,
        "url": url,
        "sections": {}
    }

    print("[A] Performance Scores...")
    report["sections"]["A_performance"] = check_performance(url)

    print("[B] WP Rocket Settings...")
    report["sections"]["B_wp_rocket"] = check_wp_rocket(url)

    print("[C] Image Optimization...")
    report["sections"]["C_images"] = check_images(url)

    print("[D] Layout...")
    report["sections"]["D_layout"] = check_layout(url)

    print("[E] Accessibility...")
    report["sections"]["E_accessibility"] = check_accessibility(url)

    print("[F] SEO...")
    report["sections"]["F_seo"] = check_seo(url)

    print("[G] Third-Party & Plugins...")
    report["sections"]["G_third_party"] = check_third_party(url)

    # Compute overall status
    overall = "PASS"
    for key, section in report["sections"].items():
        s = section.get("status") or section.get("overall")
        if s == "FAIL":
            overall = "FAIL"
            break
        if s == "WARN" and overall == "PASS":
            overall = "WARN"

    report["overall"] = overall
    return report


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 scripts/qa_automated.py check <domain-or-url>")
        print("  python3 scripts/qa_automated.py full-report <domain-or-url>")
        print("  python3 scripts/qa_automated.py psi <domain-or-url>")
        print()
        print("Examples:")
        print("  python3 scripts/qa_automated.py check basespawellness.com")
        print("  python3 scripts/qa_automated.py full-report https://www.drreichner.com/facelift")
        print("  python3 scripts/qa_automated.py psi drreichner.com/plastic-surgery")
        sys.exit(1)

    command = sys.argv[1]
    input_str = sys.argv[2]
    url = _resolve_url(input_str)

    if command == "check":
        # Quick check — lightweight
        html = _get_html(input_str)
        print(f"\n=== Quick QA: {url} ===")
        print(f"HTML size: {len(html)//1024}KB")

        imgs = re.findall(r'(https://[^"\']+\.png)', html, re.IGNORECASE)
        print(f"PNGs found: {len(set(imgs))}")

        vp = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', html, re.IGNORECASE)
        zoom_blocked = vp and ("user-scalable=0" in vp.group(0) or "maximum-scale=1.0" in vp.group(0))
        print(f"Zoom blocked: {'YES (FAIL)' if zoom_blocked else 'No (PASS)'}")

        has_main = bool(re.search(r'<main[^>]*>', html))
        print(f"<main> tag: {'Yes (PASS)' if has_main else 'No (FAIL)'}")

        has_rocket = "rocket-critical-css" in html
        print(f"WP Rocket Remove Unused CSS: {'Active (PASS)' if has_rocket else 'Not detected'}")
        has_delay = "data-rocket-defer" in html
        print(f"WP Rocket Delay JS: {'Active (PASS)' if has_delay else 'Not detected'}")
        has_lazy = 'loading="lazy"' in html
        print(f"LazyLoad: {'Active (PASS)' if has_lazy else 'Not detected'}")

    elif command == "full-report":
        report = full_report(input_str)
        print(f"\n{'='*60}")
        print(f"OVERALL QA RESULT: {report['overall']}")
        print(f"{'='*60}")

        for section_key, section_data in report["sections"].items():
            print(f"\n--- {section_key} ---")
            if "checks" in section_data:
                for c in section_data["checks"]:
                    status_icon = "✓" if c["status"] == "PASS" else "✗" if c["status"] == "FAIL" else "⚠"
                    print(f"  {status_icon} {c.get('name', c.get('id', ''))}: {c['status']} — {c.get('detail', '')}")
            if "psi_mobile" in section_data:
                pm = section_data["psi_mobile"]
                print(f"  Mobile Performance: {pm.get('performance')} | LCP: {pm.get('lcp_ms')}ms | CLS: {pm.get('cls')}")
                print(f"  Mobile A11y: {pm.get('accessibility')} | SEO: {pm.get('seo')}")
            if "summary" in section_data:
                print(f"  Summary: {section_data['summary']}")
            if section_data.get("overall") in ("FAIL", "WARN"):
                print(f"  >> Section: {section_data['overall']}")

        print(f"\n{'='*60}")
        print(f"FINAL VERDICT: {report['overall']}")
        print(f"{'='*60}")

        # Save to file
        out_dir = "data"
        os.makedirs(out_dir, exist_ok=True)
        out_path = f"{out_dir}/qa-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        # Remove large image list from saved report to keep it small
        report_clean = report
        if "C_images" in report_clean["sections"] and "all_images" in report_clean["sections"]["C_images"]:
            del report_clean["sections"]["C_images"]["all_images"]
        with open(out_path, "w") as f:
            json.dump(report_clean, f, indent=2)
        print(f"\nFull report saved to: {out_path}")

    elif command == "psi":
        url = _resolve_url(input_str)
        print(f"\nRunning PSI for {url}...")
        try:
            mobile = _run_psi(url, "mobile")
            lr = mobile.get("lighthouseResult", {})
            cats = lr.get("categories", {})
            audits = lr.get("audits", {})
            print(f"  Performance: {round(cats.get('performance',{}).get('score',0)*100)}")
            print(f"  Accessibility: {round(cats.get('accessibility',{}).get('score',0)*100)}")
            print(f"  Best Practices: {round(cats.get('best-practices',{}).get('score',0)*100)}")
            print(f"  SEO: {round(cats.get('seo',{}).get('score',0)*100)}")
            print(f"  LCP: {audits.get('largest-contentful-paint',{}).get('numericValue')}ms")
            print(f"  CLS: {audits.get('cumulative-layout-shift',{}).get('numericValue')}")
            print(f"  FCP: {audits.get('first-contentful-paint',{}).get('numericValue')}ms")
            print(f"  TBT: {audits.get('total-blocking-time',{}).get('numericValue')}ms")
        except Exception as e:
            print(f"  ERROR: {e}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
