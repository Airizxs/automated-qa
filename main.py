#!/usr/bin/env python3
import sys
import os
import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from seo_audit import SEOAuditor


def print_results(result):
    def _line(name, passed, detail=""):
        return f"  {name:<28} {'PASS' if passed else 'FAIL'}" + (f"  |  {detail}" if detail else "")

    print()
    print(f"  {'─'*60}")
    print(f"  {'SEO & QA AUDIT RESULTS':^60}")
    print(f"  {'─'*60}")
    print()
    print(f"  {'— STATIC CHECKS (HTML) —':^56}")
    print(_line("TITLE", result.title.passed, f"Chars: {result.title.length} | {result.title.status}"))
    print(_line("META DESCRIPTION", result.meta_desc.passed, f"Chars: {result.meta_desc.length} | {result.meta_desc.status}"))
    print(_line("HEADINGS", result.headings.passed, f"H1: {result.headings.h1_count} | Total: {result.headings.total}"))
    print(_line("SCHEMA MARKUP", result.schema.passed, f"Found: {result.schema.count}"))
    print(_line("IMAGE ALT TEXT", result.image_alt.passed, f"Missing: {result.image_alt.missing}/{result.image_alt.total}"))
    print(_line("RESPONSIVE (VIEWPORT)", result.responsive.passed))
    print(_line("INDEXABILITY", result.indexable.passed))
    print(_line("CANONICAL TAG", result.canonical.passed))
    print(_line("INTERNAL LINKS", result.internal_links.passed, f"Total: {result.internal_links.total} | Broken: {len(result.internal_links.broken)}"))
    print(_line("OG TAGS", result.og_tags.passed, f"Found: {result.og_tags.tags_found}/6"))
    print(_line("SSL/HTTPS", result.ssl.passed))
    print()
    print(f"  {'— DYNAMIC CHECKS (PLAYWRIGHT) —':^60}")
    print(_line("IMAGE LOADING", True, f"Total: {result.image_load.total} | Flagged: {len(result.image_load.broken)}"))
    print(_line("HERO (DESKTOP)", result.hero_dt.passed, f"Method: {result.hero_dt.method}"))
    print(_line("HERO (IPAD)", result.hero_ip.passed, f"Method: {result.hero_ip.method}"))
    print(_line("HERO (MOBILE)", result.hero_mo.passed, f"Method: {result.hero_mo.method}"))
    print(_line("BREADCRUMBS", True, f"Found: {result.breadcrumbs.exists}"))
    print(_line("MENU CLICKABILITY", True, f"Links: {result.menu_click.total_links}"))
    print(_line("FONT CONSISTENCY", result.fonts.passed, f"Fonts: {result.fonts.unique_fonts}"))
    print(_line("BUTTON STYLE", True, f"Variations: {result.button_style.unique_styles}"))
    print(_line("CONTACT FORMS", result.forms.passed, f"Found: {result.forms.count}"))
    print()
    print(f"  {'— CDP (CHROME DEVTOOLS PROTOCOL) —':^60}")
    print(_line("CONSOLE ERRORS", result.cdp_console.passed, f"Errors: {len(result.cdp_console.errors)} | Warnings: {len(result.cdp_console.warnings)}"))
    print(_line("FAILED REQUESTS", result.cdp_network.passed, f"Failed: {len(result.cdp_network.failed)}/{result.cdp_network.total_requests}"))
    print(_line("PERFORMANCE SCORE", result.cdp_vitals.passed, f"Score: {result.cdp_vitals.perf_score:.0f}/100"))
    print(_line("CLS (Cumulative Layout Shift)", result.cdp_vitals.passed, f"{result.cdp_vitals.cls:.3f}"))
    print(_line("FCP (First Contentful Paint)", result.cdp_vitals.passed, f"{result.cdp_vitals.fcp:.2f}s"))
    print(_line("TTFB (Time to First Byte)", result.cdp_vitals.passed, f"{result.cdp_vitals.ttfb:.2f}s"))
    print()
    abs_path = os.path.abspath(result.report_path)
    print(f"  Report: file://{abs_path}")
    print()


def get_score_summary(result):
    """Extract score summary from audit result for batch reports."""
    r = result
    checks = [
        ("Title", r.title.passed), ("Meta Desc", r.meta_desc.passed), ("Headings", r.headings.passed),
        ("Schema", r.schema.passed), ("Image Alt", r.image_alt.passed), ("Responsive", r.responsive.passed),
        ("Indexability", r.indexable.passed), ("Canonical", r.canonical.passed), ("Internal Links", r.internal_links.passed),
        ("OG Tags", r.og_tags.passed), ("SSL", r.ssl.passed),
        ("Hero Desktop", r.hero_dt.passed), ("Hero iPad", r.hero_ip.passed), ("Hero Mobile", r.hero_mo.passed),
        ("Fonts", r.fonts.passed), ("Contact Forms", r.forms.passed),
        ("CDP Console", r.cdp_console.passed), ("CDP Network", r.cdp_network.passed), ("Web Vitals", r.cdp_vitals.passed),
    ]
    passed = sum(1 for _, p in checks if p)
    total = len(checks)
    score = round(passed / total * 100, 1)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    return {"url": r.url, "score": score, "grade": grade, "passed": passed, "total": total, "report_path": r.report_path}


def print_batch_summary(results):
    """Print a clean batch audit summary table."""
    scores = [r["score"] for r in results]
    avg = round(sum(scores) / len(scores), 1)
    best = max(results, key=lambda r: r["score"])
    worst = min(results, key=lambda r: r["score"])

    print()
    print(f"  {'─'*80}")
    print(f"  {'BATCH AUDIT SUMMARY':^80}")
    print(f"  {len(results)} URLs completed | Average: {avg}%")
    print(f"  {'─'*80}")
    print(f"  {'#':<4} {'URL':<48} {'Score':<8} {'Grade':<7} {'Passed':<9} {'Report'}")
    print(f"  {'─'*80}")

    for i, r in enumerate(results, 1):
        domain = urlparse(r["url"]).netloc.replace("www.", "") + urlparse(r["url"]).path
        if len(domain) > 46:
            domain = domain[:43] + "..."
        filename = os.path.basename(r["report_path"])
        print(f"  {i:<4} {domain:<48} {r['score']:>5.1f}%  {r['grade']:<7} {r['passed']}/{r['total']:<7} {filename}")

    print(f"  {'─'*80}")
    print(f"  Best: {best['score']}% ({best['grade']}) | Worst: {worst['score']}% ({worst['grade']})")
    print(f"  {'─'*80}")
    print()


def read_urls_from_file(filepath):
    """Read URLs from a text file (one per line) or CSV (first column)."""
    urls = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "," in line:
                    line = line.split(",")[0].strip()
                if line:
                    urls.append(line)
    return urls


async def run_audit(url, quick=False, browser=None):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    auditor = SEOAuditor(url, report_dir=report_dir, quick=quick)
    result = await auditor.run_all(browser=browser)
    print_results(result)
    return result


async def run_batch(urls, quick=False):
    """Run audit on multiple URLs and print batch summary."""
    results_data = []
    total = len(urls)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        try:
            for i, url in enumerate(urls, 1):
                url = url.strip()
                if not url:
                    continue
                print(f"\n  [{i}/{total}]", end="")
                try:
                    result = await run_audit(url, quick=quick, browser=browser)
                    if result:
                        results_data.append(get_score_summary(result))
                except Exception as e:
                    print(f"  \u2717 Error: {e}")
        finally:
            await browser.close()

    if results_data:
        print_batch_summary(results_data)


async def main():
    args = sys.argv[1:]
    quick = "--quick" in args
    args = [a for a in args if a != "--quick"]

    urls = []

    # --file flag: read URLs from file
    if "--file" in args:
        idx = args.index("--file")
        if idx + 1 < len(args):
            urls = read_urls_from_file(args[idx + 1])
            if not urls:
                print(f"  No URLs found in file")
                return
        else:
            print("  Usage: python3 main.py --file <path>")
            return
    elif len(args) >= 1:
        urls = args

    if len(urls) == 1:
        await run_audit(urls[0], quick=quick)
    elif len(urls) > 1:
        print(f"\n  Batch audit: {len(urls)} URLs" + (" (--quick mode)" if quick else ""))
        await run_batch(urls, quick=quick)
    else:
        # Interactive mode
        print()
        print(f"  {'═'*60}")
        print(f"  {'SEO & QA AUDIT TOOL v2.0':^60}")
        print(f"  {'Paste a URL to audit. Type "exit" to quit.':^60}")
        print(f"  {'For batch: paste comma-separated URLs or use --file':^60}")
        print(f"  {'═'*60}")
        print()

        while True:
            try:
                url_input = input("  URL > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Bye!")
                break

            if not url_input:
                continue
            if url_input.lower() in ("exit", "quit", "q"):
                print("  Bye!")
                break

            if "," in url_input:
                url_list = [u.strip() for u in url_input.split(",") if u.strip()]
                await run_batch(url_list, quick=quick)
            else:
                await run_audit(url_input, quick=quick)


if __name__ == "__main__":
    asyncio.run(main())
