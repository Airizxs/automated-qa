#!/usr/bin/env python3
"""
performance_qa.py — Performance change validation toolkit.

Usage:
  python3 performance_qa.py baseline <url> <out_path>
  python3 performance_qa.py check <domain>
  python3 performance_qa.py compare <baseline_path> <current_path>
"""

import json, subprocess, sys, os, re
from datetime import datetime


PSI_API_KEY = os.environ.get("GOOGLE_PAGESPEED_API_KEY") or "AIzaSyBP-S7D4XIAEO0HjgcuZOk8JDfgbwTQhkc"

def _run_psi(url: str, strategy: str = "mobile") -> dict:
    """Run PageSpeed Insights API directly."""
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


def capture_baseline(url: str, out_path: str) -> dict:
    """Capture full baseline state via PSI API + curl."""
    baseline = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "psi": {},
        "images": [],
        "scripts": [],
        "styles": [],
        "fonts": [],
        "dom_stats": {"elements": 0},
        "page_size_bytes": 0
    }
    
    # PSI
    try:
        result = _run_psi(url, "mobile")
        lr = result.get("lighthouseResult", {})
        baseline["psi"]["mobile"] = {
            "performance": lr.get("categories",{}).get("performance",{}).get("score"),
            "lcp": lr.get("audits",{}).get("largest-contentful-paint",{}).get("numericValue"),
            "cls": lr.get("audits",{}).get("cumulative-layout-shift",{}).get("numericValue"),
            "tbt": lr.get("audits",{}).get("total-blocking-time",{}).get("numericValue"),
        }
    except Exception as e:
        baseline["psi"]["error"] = str(e)
    
    # Resource inventory from HTML
    domain = url.replace("https://", "").rstrip("/")
    html = subprocess.run(
        ["curl", "-s", "-H", "Accept: application/json", url],
        capture_output=True, text=True, timeout=30
    ).stdout
    
    baseline["page_size_bytes"] = len(html)
    
    # Images
    imgs = re.findall(r'(https://[^"\']+\.(?:png|jpg|jpeg|webp|gif|svg)[^"\']*)', html, re.IGNORECASE)
    baseline["images"] = sorted(set(imgs))
    
    # Scripts
    scripts = re.findall(r'src="(https://[^"]+\.js[^"]*)"', html)
    baseline["scripts"].extend(scripts)
    
    # Stylesheets
    styles = re.findall(r'href="(https://[^"]+\.css[^"]*)"', html)
    baseline["styles"].extend(styles)
    
    # Fonts
    fonts = re.findall(r'url\(["\']?(https://[^"\')]+\.(?:woff2?|ttf|eot)[^"\')]*)', html, re.IGNORECASE)
    baseline["fonts"] = sorted(set(fonts))
    
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"Baseline saved to {out_path}")
    return baseline


def check_image_format(domain: str, max_png_kb: int = 10) -> list:
    """Check homepage for PNG files above threshold."""
    from urllib.parse import urlparse
    
    results = []
    html = subprocess.run(
        ["curl", "-s", f"https://www.{domain}/"],
        capture_output=True, text=True, timeout=30
    ).stdout
    
    pngs = re.findall(r'(https://[^"\']+\.png)', html, re.IGNORECASE)
    for url in sorted(set(pngs)):
        resp = subprocess.run(
            ["curl", "-sI", url], capture_output=True, text=True, timeout=15
        )
        # Content-Length check
        size_match = re.search(r'content-length:\s*(\d+)', resp.stdout, re.IGNORECASE)
        size_kb = int(size_match.group(1)) // 1024 if size_match else 0
        if size_kb > max_png_kb:
            results.append({
                "url": url,
                "size_kb": size_kb,
                "status": "FAIL",
                "reason": f"PNG over {max_png_kb}KB threshold"
            })
    return results


def check_css_rule(domain: str, rule_snippet: str) -> bool:
    """Check if a CSS rule is present in the rendered page HTML."""
    html = subprocess.run(
        ["curl", "-s", f"https://www.{domain}/"],
        capture_output=True, text=True, timeout=30
    ).stdout
    return rule_snippet in html


def check_console_errors(domain: str) -> list:
    """Check for known problematic scripts still loading."""
    results = []
    html = subprocess.run(
        ["curl", "-s", f"https://www.{domain}/"],
        capture_output=True, text=True, timeout=30
    ).stdout
    
    checks = [
        ("easypiechart.js", "Script loads but may cause timeout errors on desktop"),
    ]
    for script, warning in checks:
        if script in html:
            results.append({"check": script, "status": "WARN", "detail": warning})
    return results


def check_viewport_zoom(domain: str) -> dict:
    """Check if viewport meta allows zoom."""
    html = subprocess.run(
        ["curl", "-s", f"https://www.{domain}/"],
        capture_output=True, text=True, timeout=30
    ).stdout
    meta = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', html, re.IGNORECASE)
    if meta:
        content = meta.group(0)
        if "user-scalable=0" in content or "user-scalable=no" in content or "maximum-scale=1.0" in content:
            return {"status": "FAIL", "detail": "Viewport disables zoom", "meta": content[:200]}
    return {"status": "PASS", "detail": "Viewport allows zoom"}


def check_main_landmark(domain: str) -> dict:
    """Check if <main> element exists."""
    html = subprocess.run(
        ["curl", "-s", f"https://www.{domain}/"],
        capture_output=True, text=True, timeout=30
    ).stdout
    if re.search(r'<main[^>]*>', html):
        return {"status": "PASS", "detail": "<main> landmark found"}
    return {"status": "FAIL", "detail": "No <main> landmark"}


def run_full_qa(domain: str) -> dict:
    """Run all performance QA checks."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "domain": domain,
        "checks": []
    }
    
    # Image format
    png_issues = check_image_format(domain)
    results["checks"].append({
        "name": "image_format",
        "status": "FAIL" if any(i["status"]=="FAIL" for i in png_issues) else "PASS",
        "items": png_issues,
        "summary": f"{len(png_issues)} oversized PNGs found"
    })
    
    # Console errors
    errors = check_console_errors(domain)
    results["checks"].append({
        "name": "console_errors",
        "status": "PASS" if not errors else "WARN",
        "items": errors
    })
    
    # Viewport
    vp = check_viewport_zoom(domain)
    results["checks"].append({
        "name": "viewport_zoom",
        "status": vp["status"],
        "detail": vp["detail"]
    })
    
    # Main landmark
    ml = check_main_landmark(domain)
    results["checks"].append({
        "name": "main_landmark",
        "status": ml["status"],
        "detail": ml["detail"]
    })
    
    return results


def compare_baselines(baseline_path: str, current_path: str) -> dict:
    """Compare two baseline snapshots."""
    with open(baseline_path) as f:
        before = json.load(f)
    with open(current_path) as f:
        after = json.load(f)
    
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "deltas": {}
    }
    
    # PSI comparison
    if "psi" in before and "psi" in after:
        b = before["psi"].get("mobile", {})
        a = after["psi"].get("mobile", {})
        for metric in ["performance", "lcp", "cls", "tbt"]:
            bv = b.get(metric)
            av = a.get(metric)
            if bv is not None and av is not None:
                delta = av - bv
                direction = "improved" if (metric == "performance" and delta > 0) or (metric != "performance" and delta < 0) else "regressed" if (metric == "performance" and delta < 0) or (metric != "performance" and delta > 0) else "unchanged"
                comparison["deltas"][metric] = {
                    "before": bv,
                    "after": av,
                    "delta": delta,
                    "direction": direction
                }
    
    # Image count comparison
    b_imgs = len(before.get("images", []))
    a_imgs = len(after.get("images", []))
    comparison["deltas"]["image_count"] = {"before": b_imgs, "after": a_imgs, "delta": a_imgs - b_imgs}
    
    return comparison


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  performance_qa.py baseline <url> <out_path>")
        print("  performance_qa.py check <domain>")
        print("  performance_qa.py compare <baseline_path> <current_path>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "baseline":
        capture_baseline(sys.argv[2], sys.argv[3])
    elif command == "check":
        results = run_full_qa(sys.argv[2])
        print(json.dumps(results, indent=2))
        # Exit with error if any FAIL
        if any(c["status"] == "FAIL" for c in results["checks"]):
            sys.exit(1)
    elif command == "compare":
        results = compare_baselines(sys.argv[2], sys.argv[3])
        print(json.dumps(results, indent=2))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
