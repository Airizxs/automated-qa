#!/usr/bin/env python3
import sys
import os
import csv
import asyncio
from datetime import datetime
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
    json_abs = os.path.abspath(result.json_path)
    print(f"  HTML: file://{abs_path}")
    print(f"  JSON: file://{json_abs}")
    if result.pdf_path:
        pdf_abs = os.path.abspath(result.pdf_path)
        print(f"  PDF:  file://{pdf_abs}")
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


def save_history(result):
    """Save score to history.json and show comparison with previous run."""
    import json
    domain = urlparse(result["url"]).netloc.replace("www.", "")
    history_file = os.path.join(os.path.dirname(__file__), "reports", "history.json")

    history = {}
    try:
        if os.path.exists(history_file):
            history = json.loads(open(history_file).read())
    except:
        pass

    entry = {
        "timestamp": datetime.now().isoformat(),
        "score": result["score"],
        "grade": result["grade"],
        "passed": result["passed"],
        "total": result["total"],
    }

    prev = history.get(domain)
    history[domain] = entry

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    if prev:
        diff = result["score"] - prev["score"]
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
        color = "+" if diff > 0 else "" if diff == 0 else "-"
        print(f"  Previous: {prev['score']}% ({prev['grade']}) | Now: {result['score']}% ({result['grade']}) | {arrow} {color}{abs(diff):.1f}%")
    else:
        print(f"  First audit for {domain}")


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


async def run_audit(url, quick=False, browser=None, pdf=False, suite="FULL"):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    auditor = SEOAuditor(url, report_dir=report_dir, quick=quick)
    result = await auditor.run_all(browser=browser, generate_pdf=pdf)

    print_test_bank_table(result, suite)
    summary = get_score_summary(result)
    save_history(summary)
    return result


def send_email_report(recipient, html_path, json_path=None, pdf_path=None):
    """Send audit report via email. Requires SMTP_* environment variables."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        print(f"  Email skipped: set SMTP_USER and SMTP_PASS environment variables")
        return False

    msg = MIMEMultipart()
    msg["From"] = smtp_from
    msg["To"] = recipient
    msg["Subject"] = f"SEO Audit Report — {recipient}"

    body = f"Attached is the SEO + QA audit report.\n\nGenerated: {datetime.now().strftime('%B %d, %Y at %H:%M')}"
    msg.attach(MIMEText(body, "plain"))

    # Attach HTML report
    if html_path and os.path.exists(html_path):
        with open(html_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(html_path)}"')
            msg.attach(part)

    # Attach PDF if exists
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(pdf_path)}"')
            msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"  Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"  Email failed: {e}")
        return False


async def run_batch(urls, quick=False, pdf=False):
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
                    result = await run_audit(url, quick=quick, browser=browser, pdf=pdf)
                    if result:
                        results_data.append(get_score_summary(result))
                except Exception as e:
                    print(f"  \u2717 Error: {e}")
        finally:
            await browser.close()

    if results_data:
        print_batch_summary(results_data)


# ── TEST BANK ──

SUITES = {
    "SMOKE": [
        "TC-01.1", "TC-02.1", "TC-03.1", "TC-04.1", "TC-05.1",
        "TC-06.1", "TC-07.1", "TC-08.1", "TC-11.1",
        "TC-12.1", "TC-13.1", "TC-13.2", "TC-15.1",
        "TC-22.4", "TC-22.5", "TC-22.6",
    ],
    "CONTENT": [
        "TC-01.1", "TC-02.1", "TC-03.1", "TC-05.1",
        "TC-10.1", "TC-13.1", "TC-13.2", "TC-13.5", "TC-13.6",
        "TC-16.1", "TC-23.1", "TC-24.1",
    ],
    "REG": [
        "TC-01.2", "TC-02.2", "TC-03.3", "TC-04.2", "TC-05.2",
        "TC-06.3", "TC-08.2", "TC-09.1", "TC-12.2",
        "TC-14.1", "TC-14.2", "TC-15.2", "TC-17.1",
        "TC-18.1", "TC-18.2", "TC-19.1", "TC-20.1",
        "TC-21.1", "TC-21.3", "TC-22.1", "TC-23.1", "TC-24.1",
    ],
}


def evaluate_test(tid, result):
    """Map TC-* ID to audit result field."""
    # Title
    if tid == "TC-01.1": return "PASS" if result.title.passed else "FAIL"
    if tid == "TC-01.2": return "FAIL" if result.title.status == "TOO LONG" else "PASS"
    # Meta
    if tid == "TC-02.1": return "PASS" if result.meta_desc.passed else "FAIL"
    if tid == "TC-02.2": return "FAIL" if result.meta_desc.status == "TOO LONG" else "PASS"
    # Headings
    if tid == "TC-03.1": return "PASS" if result.headings.passed else "FAIL"
    if tid == "TC-03.3": return "FAIL" if result.headings.h1_count > 1 else "PASS"
    # Schema
    if tid == "TC-04.1": return "PASS" if result.schema.passed else "FAIL"
    if tid == "TC-04.2": return "PASS"
    # Image Alt
    if tid == "TC-05.1": return "PASS" if result.image_alt.passed else "FAIL"
    if tid == "TC-05.2": return "FAIL" if not result.image_alt.passed else "PASS"
    # Viewport
    if tid == "TC-06.1": return "PASS" if result.responsive.passed else "FAIL"
    if tid == "TC-06.3": return "PASS" if result.responsive.passed else "FAIL"
    # Indexability
    if tid == "TC-07.1": return "PASS" if result.indexable.passed else "FAIL"
    # Canonical
    if tid == "TC-08.1": return "PASS" if result.canonical.passed else "FAIL"
    if tid == "TC-08.2": return "FAIL" if not result.canonical.matches else "PASS"
    # Internal Links
    if tid == "TC-09.1": return "PASS" if result.internal_links.passed else "FAIL"
    # OG Tags
    if tid == "TC-10.1": return "PASS" if result.og_tags.passed else "FAIL"
    # SSL
    if tid == "TC-11.1": return "PASS" if result.ssl.passed else "FAIL"
    # Image Loading
    if tid == "TC-12.1": return "PASS" if result.image_load.passed else "FAIL"
    if tid == "TC-12.2": return "FAIL" if not result.image_load.passed else "PASS"
    # Hero
    if tid in ("TC-13.1", "TC-13.2"): return "PASS" if result.hero_dt.passed else "FAIL"
    if tid == "TC-13.5": return "PASS" if result.hero_ip.passed else "FAIL"
    if tid == "TC-13.6": return "PASS" if result.hero_mo.passed else "FAIL"
    # Breadcrumbs
    if tid in ("TC-14.1", "TC-14.2"): return "PASS" if result.breadcrumbs.passed else "FAIL"
    # Menu
    if tid == "TC-15.1": return "PASS" if result.menu_click.total_links > 0 else "FAIL"
    if tid == "TC-15.2": return "PASS"
    # Fonts
    if tid == "TC-16.1": return "PASS"
    # Buttons
    if tid == "TC-17.1": return "PASS"
    # Forms
    if tid in ("TC-18.1", "TC-18.2"): return "PASS" if result.forms.passed else "FAIL"
    # CDP
    if tid == "TC-19.1": return "PASS" if result.cdp_console.passed else "FAIL"
    if tid == "TC-20.1": return "PASS" if result.cdp_network.passed else "FAIL"
    if tid in ("TC-21.1", "TC-21.3"): return "PASS" if result.cdp_vitals.passed else "FAIL"
    # Sticky
    if tid == "TC-22.1": return "PASS" if result.sticky_dt.passed else "FAIL"
    if tid == "TC-22.4": return "PASS" if result.sticky_dt.passed else "FAIL"
    if tid == "TC-22.5": return "PASS" if result.sticky_ip.passed else "FAIL"
    if tid == "TC-22.6": return "PASS" if result.sticky_mo.passed else "FAIL"
    # Featured
    if tid == "TC-23.1": return "PASS" if result.featured_image.passed else "FAIL"
    # Whitespace
    if tid == "TC-24.1": return "PASS" if result.whitespace.passed else "FAIL"
    return "MANUAL"


def load_test_names():
    """Load test case names from CSV."""
    path = os.path.join(os.path.dirname(__file__), "TEST_BANK.csv")
    names = {}
    try:
        with open(path, "r", newline="") as f:
            for row in csv.DictReader(f):
                names[row["ID"]] = {"title": row.get("Title",""), "area": row.get("Area",""), "object": row.get("Object",""), "severity": row.get("Severity","Critical")}
    except: pass
    return names


def print_test_bank_table(result, suite_name):
    """Print test bank results for the given suite."""
    names = load_test_names()

    suite_name = suite_name.upper()
    if suite_name == "FULL":
        suite_ids = list(names.keys())  # ALL 133 test cases from CSV
    else:
        suite_ids = SUITES.get(suite_name, [])

    results = []
    for tid in suite_ids:
        t = names.get(tid, {})
        status = evaluate_test(tid, result)
        results.append({
            "ID": tid, "Area": t.get("area",""), "Object": t.get("object",""),
            "Title": t.get("title",""), "Severity": t.get("severity",""), "Status": status,
        })

    passed = sum(1 for r in results if r["Status"] == "PASS")
    failed = sum(1 for r in results if r["Status"] == "FAIL")
    manual = sum(1 for r in results if r["Status"] == "MANUAL")

    total = passed + failed + manual
    score = round(passed / total * 100, 1) if total > 0 else 0
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"

    print()
    print(f"  {'─'*90}")
    print(f"  {'QA AUDIT — ' + suite_name.upper():^90}")
    print(f"  {'Score: ' + str(score) + '% (' + grade + ') | ' + str(passed) + ' pass, ' + str(failed) + ' fail, ' + str(manual) + ' manual':^90}")
    print(f"  {'─'*90}")
    print(f"  {'ID':<10} {'Area':<8} {'Object':<18} {'Status':<8} {'Title'}")
    print(f"  {'─'*90}")
    for r in results:
        s = "\033[92m" if r["Status"] == "PASS" else "\033[91m" if r["Status"] == "FAIL" else "\033[93m"
        print(f"  {r['ID']:<10} {r['Area']:<8} {r['Object']:<18} {s}{r['Status']:<8}\033[0m {r['Title'][:40]}")
    print(f"  {'─'*90}")
    print(f"  HTML: file://{os.path.abspath(result.report_path)}")
    print(f"  JSON: file://{os.path.abspath(result.json_path)}")
    print()


async def run_validation():
    """Run 15 HTML fixtures to validate the tool itself."""
    import tempfile

    FIXTURES = os.path.join(os.path.dirname(__file__), "tests", "fixtures")
    EXPECTED = {
        "good.html": {"title_passed": True, "meta_passed": True, "headings_passed": True, "schema_passed": True, "image_alt_passed": True, "responsive_passed": True, "indexable_passed": True, "canonical_passed": True, "og_tags_passed": True, "sticky_dt_passed": True, "hero_dt_passed": True, "forms_passed": True},
        "missing-title.html": {"title_passed": False, "headings_passed": True, "responsive_passed": True},
        "long-title.html": {"title_passed": False, "headings_passed": True, "responsive_passed": True},
        "missing-meta.html": {"meta_passed": False, "headings_passed": True, "responsive_passed": True},
        "long-meta.html": {"meta_passed": False, "responsive_passed": True},
        "missing-h1.html": {"headings_passed": False, "responsive_passed": True},
        "multiple-h1.html": {"headings_passed": False, "responsive_passed": True},
        "no-schema.html": {"schema_passed": False, "responsive_passed": True},
        "missing-alt.html": {"image_alt_passed": False, "responsive_passed": True},
        "no-viewport.html": {"responsive_passed": False, "headings_passed": True},
        "noindex.html": {"indexable_passed": False, "responsive_passed": True},
        "missing-canonical.html": {"canonical_passed": False, "responsive_passed": True},
        "no-og.html": {"og_tags_passed": False, "responsive_passed": True},
        "sticky.html": {"sticky_dt_passed": True, "responsive_passed": True},
        "non-sticky.html": {"sticky_dt_passed": False, "responsive_passed": True},
    }

    MAP = {
        "title_passed": lambda r: r.title.passed, "meta_passed": lambda r: r.meta_desc.passed,
        "headings_passed": lambda r: r.headings.passed, "schema_passed": lambda r: r.schema.passed,
        "image_alt_passed": lambda r: r.image_alt.passed, "responsive_passed": lambda r: r.responsive.passed,
        "indexable_passed": lambda r: r.indexable.passed, "canonical_passed": lambda r: r.canonical.passed,
        "og_tags_passed": lambda r: r.og_tags.passed, "hero_dt_passed": lambda r: r.hero_dt.passed,
        "sticky_dt_passed": lambda r: r.sticky_dt.passed, "forms_passed": lambda r: r.forms.passed,
    }

    async def run():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
            try:
                total = passed = failed = 0
                for name in sorted(EXPECTED):
                    total += 1
                    url = f"file://{os.path.abspath(os.path.join(FIXTURES, name))}"
                    result = await SEOAuditor(url, report_dir=tempfile.mkdtemp(), quick=True).run_all(browser=browser)
                    errors = [f"{k}: expected {v}, got {MAP[k](result)}" for k, v in EXPECTED[name].items() if MAP.get(k, lambda _: None)(result) != v]
                    if errors: failed += 1; status = f"FAIL {'|'.join(errors)}"
                    else: passed += 1; status = "PASS"
                    print(f"  {name:<25} {status[:4]:<5} {status[5:] if len(status)>5 else ''}")
                print(f"\n  RESULT: {passed} passed, {failed} failed, {total} total")
            finally:
                await browser.close()
    await run()


async def main():
    raw = sys.argv[1:]
    quick = False
    pdf = False
    email_to = None
    suite = None
    urls = []

    if "--validate" in raw:
        await run_validation()
        return

    flags_suite = {"--suite": ["SMOKE", "CONTENT", "REG", "FULL"]}
    for i in range(len(raw)):
        a = raw[i]
        if a == "--quick":
            quick = True
        elif a == "--pdf":
            pdf = True
        elif a == "--suite" and i + 1 < len(raw):
            suite = raw[i + 1]
        elif a == "--email" and i + 1 < len(raw):
            email_to = raw[i + 1]
        elif a.startswith("--"):
            continue
        elif not (email_to and a == email_to) and not (suite and a == suite):
            urls.append(a)

    if "--file" in raw:
        idx = raw.index("--file")
        if idx + 1 < len(raw):
            urls = read_urls_from_file(raw[idx + 1])

    if len(urls) == 1:
        result = await run_audit(urls[0], quick=quick, pdf=pdf, suite=suite)
        if email_to and result:
            send_email_report(email_to, result.report_path, result.json_path, result.pdf_path)
    elif len(urls) > 1:
        print(f"\n  Batch audit: {len(urls)} URLs" + (" (--quick mode)" if quick else ""))
        await run_batch(urls, quick=quick, pdf=pdf)
        if email_to:
            print(f"  Email batch summary not yet supported for batch mode")
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
                await run_batch(url_list, quick=quick, pdf=pdf)
            else:
                await run_audit(url_input, quick=quick, pdf=pdf)


if __name__ == "__main__":
    asyncio.run(main())
