#!/usr/bin/env python3
"""
Validate the SEO/QA audit tool against known HTML fixtures.

This script creates a set of test pages with specific issues, runs the audit tool
against each one, and checks whether the tool correctly detects the expected
conditions.

Usage:
    .venv/bin/python validate_tool.py
"""
import asyncio
import os
import tempfile
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from seo_audit import SEOAuditor


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "tests", "fixtures")


# Define expected outcomes for each fixture.
# Keys are field names, values are the expected boolean or count.
# Use "skip" for checks that are not deterministic on file:// URLs.
EXPECTED = {
    "good.html": {
        "title_passed": True,
        "meta_passed": True,
        "headings_passed": True,
        "schema_passed": True,
        "image_alt_passed": True,
        "responsive_passed": True,
        "indexable_passed": True,
        "canonical_passed": True,
        "og_tags_passed": True,
        "sticky_dt_passed": True,
        "hero_dt_passed": True,
        "forms_passed": True,
    },
    "missing-title.html": {
        "title_passed": False,
        "meta_passed": False,
        "headings_passed": True,
        "schema_passed": False,
        "responsive_passed": True,
        "indexable_passed": True,
    },
    "long-title.html": {
        "title_passed": False,
        "headings_passed": True,
        "responsive_passed": True,
    },
    "missing-meta.html": {
        "meta_passed": False,
        "responsive_passed": True,
        "headings_passed": True,
    },
    "long-meta.html": {
        "meta_passed": False,
        "responsive_passed": True,
    },
    "missing-h1.html": {
        "headings_passed": False,
        "responsive_passed": True,
    },
    "multiple-h1.html": {
        "headings_passed": False,
        "responsive_passed": True,
    },
    "no-schema.html": {
        "schema_passed": False,
        "responsive_passed": True,
    },
    "missing-alt.html": {
        "image_alt_passed": False,
        "responsive_passed": True,
    },
    "no-viewport.html": {
        "responsive_passed": False,
        "headings_passed": True,
    },
    "noindex.html": {
        "indexable_passed": False,
        "responsive_passed": True,
    },
    "missing-canonical.html": {
        "canonical_passed": False,
        "responsive_passed": True,
    },
    "no-og.html": {
        "og_tags_passed": False,
        "responsive_passed": True,
    },
    "sticky.html": {
        "sticky_dt_passed": True,
        "responsive_passed": True,
    },
    "non-sticky.html": {
        "sticky_dt_passed": False,
        "responsive_passed": True,
    },
}


def get_result_value(result, key):
    """Extract a value from the audit result by dotted key."""
    mapping = {
        "title_passed": result.title.passed,
        "meta_passed": result.meta_desc.passed,
        "headings_passed": result.headings.passed,
        "schema_passed": result.schema.passed,
        "image_alt_passed": result.image_alt.passed,
        "responsive_passed": result.responsive.passed,
        "indexable_passed": result.indexable.passed,
        "canonical_passed": result.canonical.passed,
        "internal_links_passed": result.internal_links.passed,
        "og_tags_passed": result.og_tags.passed,
        "ssl_passed": result.ssl.passed,
        "sticky_dt_passed": result.sticky_dt.passed,
        "sticky_ip_passed": result.sticky_ip.passed,
        "sticky_mo_passed": result.sticky_mo.passed,
        "hero_dt_passed": result.hero_dt.passed,
        "hero_ip_passed": result.hero_ip.passed,
        "hero_mo_passed": result.hero_mo.passed,
        "breadcrumbs_passed": result.breadcrumbs.passed,
        "forms_passed": result.forms.passed,
        "image_load_passed": result.image_load.passed,
        "cdp_console_passed": result.cdp_console.passed,
        "cdp_network_passed": result.cdp_network.passed,
        "cdp_vitals_passed": result.cdp_vitals.passed,
    }
    return mapping.get(key)


async def run_fixture(browser, fixture_name):
    """Run the audit on a single fixture file and return the result."""
    path = os.path.join(FIXTURES_DIR, fixture_name)
    url = f"file://{os.path.abspath(path)}"
    auditor = SEOAuditor(url, report_dir=tempfile.mkdtemp(), quick=True)
    return await auditor.run_all(browser=browser)


def check_fixture(fixture_name, result):
    """Check if a result matches expected outcomes."""
    expected = EXPECTED.get(fixture_name, {})
    failures = []
    for key, expected_val in expected.items():
        actual = get_result_value(result, key)
        if actual is None:
            continue
        if actual != expected_val:
            failures.append(f"{key}: expected {expected_val}, got {actual}")
    return failures


async def main():
    print("=" * 70)
    print("TOOL VALIDATION HARNESS")
    print("=" * 70)
    print(f"Fixtures: {len(EXPECTED)}")
    print()

    total = 0
    passed = 0
    failed = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        try:
            for fixture_name in sorted(EXPECTED.keys()):
                total += 1
                result = await run_fixture(browser, fixture_name)
                errors = check_fixture(fixture_name, result)

                if errors:
                    failed += 1
                    status = "FAIL"
                    detail = " | ".join(errors)
                else:
                    passed += 1
                    status = "PASS"
                    detail = "All expected checks matched"

                print(f"{fixture_name:<25} {status:<5} {detail}")
        finally:
            await browser.close()

    print()
    print("=" * 70)
    print(f"RESULT: {passed} passed, {failed} failed, {total} total")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    raise SystemExit(exit_code)
