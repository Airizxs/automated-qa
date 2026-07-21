#!/usr/bin/env python3
"""
Run a subset of the QA test bank against a URL.

Usage:
    .venv/bin/python run_test_bank.py --suite CONTENT https://example.com
    .venv/bin/python run_test_bank.py --suite SMOKE https://example.com
    .venv/bin/python run_test_bank.py --suite FULL https://example.com
    .venv/bin/python run_test_bank.py --suite HELPDESK

Suites:
    SMOKE     - Critical checks for quick validation
    CONTENT   - Content-focused checks (SEO, images, layout)
    FULL      - All automated checks
    REG       - Regression checks (links, forms, breadcrumbs, etc.)
    HELPDESK  - Helpdesk API checks (uses FreeScout keys)
"""
import argparse
import csv
import os
import asyncio
import sys
from datetime import datetime
from seo_audit import SEOAuditor

# ─── SUITES ───
# Map suite name to list of test IDs
SUITES = {
    "SMOKE": [
        "QA-SEO-001", "QA-SEO-004", "QA-SEO-007", "QA-SEO-013",
        "QA-SEO-015", "QA-SEO-017", "QA-SEO-026",
        "QA-VIS-001", "QA-VIS-002", "QA-VIS-003",
        "QA-DYN-012",
    ],
    "CONTENT": [
        "QA-SEO-001", "QA-SEO-002", "QA-SEO-004", "QA-SEO-005",
        "QA-SEO-007", "QA-SEO-009", "QA-SEO-010", "QA-SEO-011",
        "QA-SEO-013", "QA-SEO-014", "QA-SEO-024", "QA-SEO-025",
        "QA-DYN-004", "QA-DYN-005", "QA-DYN-006",
        "QA-DYN-007", "QA-DYN-008", "QA-DYN-013",
        "QA-VIS-007", "QA-VIS-008", "QA-VIS-009", "QA-VIS-010",
    ],
    "REG": [
        "QA-SEO-021", "QA-SEO-022", "QA-SEO-023",
        "QA-SEO-019", "QA-SEO-020",
        "QA-DYN-009", "QA-DYN-010", "QA-DYN-011",
        "QA-DYN-015", "QA-DYN-016", "QA-DYN-017", "QA-DYN-018",
        "QA-DYN-014", "QA-VIS-011",
    ],
    "FULL": [],  # populated later: all IDs in the bank
    "HELPDESK": [],  # handled separately
}


def load_test_bank(path="TEST_BANK.csv"):
    """Load test bank from CSV into a list of dicts."""
    tests = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tests.append(row)
    return tests


def evaluate_website_test(t, result):
    """Map a test case to an audit result. Returns 'PASS', 'FAIL', or 'MANUAL'."""
    tid = t["ID"]

    # Title
    if tid == "QA-SEO-001":
        return "PASS" if result.title.passed else "FAIL"
    if tid == "QA-SEO-002":
        return "FAIL" if result.title.status == "TOO LONG" else "PASS"
    if tid == "QA-SEO-003":
        return "FAIL" if result.title.status == "MISSING" else "PASS"

    # Meta
    if tid == "QA-SEO-004":
        return "PASS" if result.meta_desc.passed else "FAIL"
    if tid == "QA-SEO-005":
        return "FAIL" if result.meta_desc.status == "TOO LONG" else "PASS"
    if tid == "QA-SEO-006":
        return "FAIL" if result.meta_desc.status == "MISSING" else "PASS"

    # Headings
    if tid == "QA-SEO-007":
        return "PASS" if result.headings.passed else "FAIL"
    if tid == "QA-SEO-008":
        return "FAIL" if result.headings.h1_count > 1 else "PASS"
    if tid == "QA-SEO-009":
        return "FAIL" if result.headings.h1_count == 0 else "PASS"

    # Schema
    if tid == "QA-SEO-010":
        return "PASS" if result.schema.passed else "FAIL"
    if tid == "QA-SEO-011":
        return "FAIL" if not result.schema.passed else "PASS"

    # Image Alt
    if tid == "QA-SEO-013":
        return "PASS" if result.image_alt.passed else "FAIL"
    if tid == "QA-SEO-014":
        return "FAIL" if not result.image_alt.passed else "PASS"

    # Viewport
    if tid == "QA-SEO-015":
        return "PASS" if result.responsive.passed else "FAIL"
    if tid == "QA-SEO-016":
        return "FAIL" if not result.responsive.passed else "PASS"

    # Indexability
    if tid == "QA-SEO-017":
        return "PASS" if result.indexable.passed else "FAIL"
    if tid == "QA-SEO-018":
        return "FAIL" if not result.indexable.passed else "PASS"

    # Canonical
    if tid == "QA-SEO-019":
        return "PASS" if result.canonical.passed else "FAIL"
    if tid == "QA-SEO-020":
        return "FAIL" if not result.canonical.passed else "PASS"

    # Internal Links
    if tid == "QA-SEO-021":
        return "PASS" if result.internal_links.passed else "FAIL"
    if tid == "QA-SEO-022":
        return "FAIL" if not result.internal_links.passed else "PASS"
    if tid == "QA-SEO-023":
        return "MANUAL"  # depends on --quick flag

    # OG Tags
    if tid == "QA-SEO-024":
        return "PASS" if result.og_tags.passed else "FAIL"
    if tid == "QA-SEO-025":
        return "FAIL" if not result.og_tags.passed else "PASS"

    # SSL
    if tid == "QA-SEO-026":
        return "PASS" if result.ssl.passed else "FAIL"
    if tid == "QA-SEO-027":
        return "FAIL" if not result.ssl.passed else "PASS"

    # Image Loading
    if tid == "QA-DYN-001":
        return "PASS" if result.image_load.passed else "FAIL"
    if tid == "QA-DYN-002":
        return "FAIL" if not result.image_load.passed else "PASS"
    if tid == "QA-DYN-003":
        return "MANUAL"  # depends on --quick flag

    # Hero
    if tid == "QA-DYN-004":
        return "PASS" if result.hero_dt.passed else "FAIL"
    if tid == "QA-DYN-005":
        return "PASS" if result.hero_dt.passed else "FAIL"
    if tid == "QA-DYN-006":
        return "FAIL" if not result.hero_dt.passed else "PASS"
    if tid == "QA-DYN-007":
        return "PASS" if result.hero_ip.passed else "FAIL"
    if tid == "QA-DYN-008":
        return "PASS" if result.hero_mo.passed else "FAIL"

    # Breadcrumbs
    if tid == "QA-DYN-009":
        return "PASS" if result.breadcrumbs.passed else "FAIL"
    if tid == "QA-DYN-010":
        return "PASS" if result.breadcrumbs.passed else "FAIL"
    if tid == "QA-DYN-011":
        return "FAIL" if not result.breadcrumbs.passed else "PASS"

    # Menu Clickability
    if tid == "QA-DYN-012":
        return "PASS" if result.menu_click.total_links > 0 else "FAIL"

    # Fonts
    if tid == "QA-DYN-013":
        return "PASS"  # informational

    # Buttons
    if tid == "QA-DYN-014":
        return "PASS"  # informational

    # Forms
    if tid == "QA-DYN-015":
        return "PASS" if result.forms.passed else "FAIL"
    if tid == "QA-DYN-016":
        return "PASS" if result.forms.passed else "FAIL"
    if tid == "QA-DYN-017":
        return "PASS" if result.forms.passed else "FAIL"
    if tid == "QA-DYN-018":
        return "FAIL" if not result.forms.passed else "PASS"

    # CDP Console
    if tid == "QA-CDP-001":
        return "PASS" if result.cdp_console.passed else "FAIL"
    if tid == "QA-CDP-002":
        return "FAIL" if not result.cdp_console.passed else "PASS"
    if tid == "QA-CDP-003":
        return "PASS"  # trackers are filtered in code
    if tid == "QA-CDP-004":
        return "MANUAL"  # depends on --quick flag

    # CDP Network
    if tid == "QA-CDP-005":
        return "PASS" if result.cdp_network.passed else "FAIL"
    if tid == "QA-CDP-006":
        return "FAIL" if not result.cdp_network.passed else "PASS"

    # Web Vitals
    if tid == "QA-CDP-007":
        return "PASS" if result.cdp_vitals.passed else "FAIL"
    if tid == "QA-CDP-008":
        return "FAIL" if not result.cdp_vitals.passed else "PASS"
    if tid in ("QA-CDP-009", "QA-CDP-010", "QA-CDP-011", "QA-CDP-012"):
        return "PASS" if result.cdp_vitals.passed else "FAIL"

    # Sticky
    if tid == "QA-VIS-001":
        return "PASS" if result.sticky_dt.passed else "FAIL"
    if tid == "QA-VIS-002":
        return "PASS" if result.sticky_ip.passed else "FAIL"
    if tid == "QA-VIS-003":
        return "PASS" if result.sticky_mo.passed else "FAIL"
    if tid == "QA-VIS-004":
        return "FAIL" if result.sticky_dt.passed else "PASS"
    if tid == "QA-VIS-005":
        return "FAIL" if result.sticky_dt.passed else "PASS"  # no header means fail
    if tid == "QA-VIS-006":
        return "PASS" if result.sticky_dt.screenshot else "FAIL"

    # Featured Image
    if tid == "QA-VIS-007":
        return "PASS" if result.featured_image.passed else "FAIL"
    if tid == "QA-VIS-008":
        return "FAIL" if not result.featured_image.passed else "PASS"
    if tid == "QA-VIS-009":
        return "FAIL" if not result.featured_image.passed else "PASS"

    # Whitespace
    if tid == "QA-VIS-010":
        return "PASS" if result.whitespace.passed else "FAIL"
    if tid == "QA-VIS-011":
        return "FAIL" if not result.whitespace.passed else "PASS"
    if tid == "QA-VIS-012":
        return "PASS" if result.whitespace.passed else "FAIL"

    return "MANUAL"


def run_helpdesk_suite():
    """Placeholder for helpdesk tests. Reads FreeScout API keys from env."""
    read_only = os.environ.get("FREESCOUT_READ_ONLY")
    read_write = os.environ.get("FREESCOUT_READ_WRITE")
    if not read_only or not read_write:
        print("Set FREESCOUT_READ_ONLY and FREESCOUT_READ_WRITE env vars to run HELPDESK suite.")
        print("Example:")
        print("  export FREESCOUT_READ_ONLY=fsk_...")
        print("  export FREESCOUT_READ_WRITE=fsk_...")
        return []
    print("HELPDESK suite not yet automated in this script.")
    return []


async def run_website_suite(suite_name, url, quick=False):
    """Run a website QA suite against a URL and return results."""
    tests = load_test_bank()
    all_ids = {t["ID"] for t in tests}
    SUITES["FULL"] = list(all_ids)

    suite_ids = set(SUITES.get(suite_name, []))
    suite_tests = [t for t in tests if t["ID"] in suite_ids]

    if not suite_tests:
        print(f"No tests found for suite: {suite_name}")
        return []

    print(f"\nRunning {suite_name} suite: {len(suite_tests)} tests on {url}")
    print("=" * 70)

    auditor = SEOAuditor(url, quick=quick)
    result = await auditor.run_all()

    results = []
    for t in suite_tests:
        status = evaluate_website_test(t, result)
        results.append({
            "ID": t["ID"],
            "Area": t["Area"],
            "Object": t["Object"],
            "Title": t["Title"],
            "Expected": t["Expected"],
            "Severity": t["Severity"],
            "Status": status,
        })
    return results


def print_results(results, suite_name):
    """Print a formatted test result table."""
    if not results:
        return

    passed = sum(1 for r in results if r["Status"] == "PASS")
    failed = sum(1 for r in results if r["Status"] == "FAIL")
    manual = sum(1 for r in results if r["Status"] == "MANUAL")

    print(f"\n{'─' * 90}")
    print(f"{suite_name} SUITE RESULTS")
    print(f"{'─' * 90}")
    print(f"{'ID':<12} {'Area':<8} {'Object':<18} {'Status':<8} {'Severity':<10} {'Title'}")
    print(f"{'─' * 90}")
    for r in results:
        status_color = "\033[92m" if r["Status"] == "PASS" else "\033[91m" if r["Status"] == "FAIL" else "\033[93m"
        reset = "\033[0m"
        print(f"{r['ID']:<12} {r['Area']:<8} {r['Object']:<18} {status_color}{r['Status']:<8}{reset} {r['Severity']:<10} {r['Title'][:35]}")
    print(f"{'─' * 90}")
    print(f"PASS: {passed} | FAIL: {failed} | MANUAL: {manual}")

    # Save to CSV
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join("reports", f"testbank-{suite_name}-{ts}.csv")
    os.makedirs("reports", exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Area", "Object", "Title", "Expected", "Severity", "Status"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved: {path}")


async def main():
    parser = argparse.ArgumentParser(description="Run QA test bank suites")
    parser.add_argument("--suite", choices=list(SUITES.keys()), default="SMOKE", help="Test suite to run")
    parser.add_argument("--quick", action="store_true", help="Skip CDP, image loading, link verification")
    parser.add_argument("url", nargs="?", help="URL to audit (not needed for HELPDESK suite)")
    args = parser.parse_args()

    if args.suite == "HELPDESK":
        run_helpdesk_suite()
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    results = await run_website_suite(args.suite, args.url, quick=args.quick)
    print_results(results, args.suite)


if __name__ == "__main__":
    asyncio.run(main())
