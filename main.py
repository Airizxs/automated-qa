#!/usr/bin/env python3
import sys
import os
import asyncio
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
    print(f"  Report: {result.report_path}")
    print(f"  Dashboard: {result.dashboard_path}")
    print()


async def run_audit(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"\n  Running SEO audit on: {url}")
    print(f"  {'.'*50}\n")

    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    auditor = SEOAuditor(url, report_dir=report_dir)
    result = await auditor.run_all()
    print_results(result)


async def main():
    # Single URL mode: python3 main.py https://example.com
    if len(sys.argv) >= 2:
        await run_audit(sys.argv[1])
        return

    # Loop mode: paste URLs one by one
    print()
    print(f"  {'═'*60}")
    print(f"  {'SEO & QA AUDIT TOOL':^60}")
    print(f"  {'Paste a URL to audit. Type "exit" to quit.':^60}")
    print(f"  {'═'*60}")
    print()

    while True:
        try:
            url = input("  URL > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye!")
            break

        if not url or url.lower() in ("exit", "quit", "q"):
            print("  Bye!")
            break

        await run_audit(url)


if __name__ == "__main__":
    asyncio.run(main())
