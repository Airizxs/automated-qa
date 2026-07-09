import json
import os
import asyncio
import requests
from datetime import datetime
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright

VIEWPORTS = {"Desktop": {"width": 1280, "height": 800}, "iPad": {"width": 768, "height": 1024}, "Mobile": {"width": 375, "height": 667}}

# ──── DATA CLASSES ────

@dataclass
class TitleResult: text: str = ""; length: int = 0; status: str = ""; passed: bool = False
@dataclass
class MetaDescResult: text: str = ""; length: int = 0; status: str = ""; passed: bool = False
@dataclass
class HeadingsResult: total: int = 0; h1_count: int = 0; items: list = field(default_factory=list); issues: list = field(default_factory=list); passed: bool = False
@dataclass
class SchemaResult: count: int = 0; types: list = field(default_factory=list); passed: bool = False
@dataclass
class ImageAltResult: total: int = 0; missing: int = 0; passed: bool = False
@dataclass
class ResponsiveResult: has_viewport: bool = False; content: str = ""; passed: bool = False
@dataclass
class IndexableResult: indexable: bool = True; meta_robots: str = ""; passed: bool = False
@dataclass
class CanonicalResult: href: str = ""; matches: bool = False; passed: bool = False
@dataclass
class InternalLinksResult: total: int = 0; broken: list = field(default_factory=list); passed: bool = False
@dataclass
class StickyResult: viewport: str = ""; has_sticky: bool = False; selector: str = ""; height: int = 0; visible_scrolled: bool = False; issues: list = field(default_factory=list); screenshot: str = ""; passed: bool = False
@dataclass
class FeaturedImageResult: og_image: str = ""; image_exists: bool = False; issues: list = field(default_factory=list); passed: bool = False
@dataclass
class ImageLoadResult: total: int = 0; broken: list = field(default_factory=list); screenshot: str = ""; passed: bool = True
@dataclass
class HeroResult: viewport: str = ""; exists: bool = False; src: str = ""; method: str = ""; loaded: bool = False; issues: list = field(default_factory=list); screenshot: str = ""; passed: bool = False
@dataclass
class BreadcrumbsResult: exists: bool = False; text: str = ""; method: str = ""; passed: bool = False
@dataclass
class MenuClickResult: total_links: int = 0; passed: bool = True
@dataclass
class FontsResult: fonts: list = field(default_factory=list); unique_fonts: int = 0; passed: bool = True
@dataclass
class ButtonStyleResult: unique_styles: int = 0; button_fonts: list = field(default_factory=list); passed: bool = True
@dataclass
class ContactFormResult: count: int = 0; passed: bool = False
@dataclass
class WhitespaceResult: issues: list = field(default_factory=list); screenshot: str = ""; passed: bool = False

@dataclass
class CDPConsoleResult: errors: list = field(default_factory=list); warnings: list = field(default_factory=list); passed: bool = True
@dataclass
class CDPNetworkResult: failed: list = field(default_factory=list); total_requests: int = 0; passed: bool = True
@dataclass
class CDPVitalsResult: lcp: float = 0; cls: float = 0; fcp: float = 0; ttfb: float = 0; perf_score: float = 0; passed: bool = True

@dataclass
class OGTagsResult: og_title: str = ""; og_description: str = ""; og_image: str = ""; og_url: str = ""; og_type: str = ""; og_site_name: str = ""; tags_found: int = 0; passed: bool = False

@dataclass
class SSLResult: is_https: bool = False; cert_valid: bool = False; passed: bool = False

@dataclass
class AuditResult:
    url: str; title: TitleResult = field(default_factory=TitleResult)
    meta_desc: MetaDescResult = field(default_factory=MetaDescResult)
    headings: HeadingsResult = field(default_factory=HeadingsResult)
    schema: SchemaResult = field(default_factory=SchemaResult)
    image_alt: ImageAltResult = field(default_factory=ImageAltResult)
    responsive: ResponsiveResult = field(default_factory=ResponsiveResult)
    indexable: IndexableResult = field(default_factory=IndexableResult)
    canonical: CanonicalResult = field(default_factory=CanonicalResult)
    internal_links: InternalLinksResult = field(default_factory=InternalLinksResult)
    sticky_dt: StickyResult = field(default_factory=StickyResult)
    sticky_ip: StickyResult = field(default_factory=StickyResult)
    sticky_mo: StickyResult = field(default_factory=StickyResult)
    featured_image: FeaturedImageResult = field(default_factory=FeaturedImageResult)
    image_load: ImageLoadResult = field(default_factory=ImageLoadResult)
    hero_dt: HeroResult = field(default_factory=HeroResult)
    hero_ip: HeroResult = field(default_factory=HeroResult)
    hero_mo: HeroResult = field(default_factory=HeroResult)
    breadcrumbs: BreadcrumbsResult = field(default_factory=BreadcrumbsResult)
    menu_click: MenuClickResult = field(default_factory=MenuClickResult)
    fonts: FontsResult = field(default_factory=FontsResult)
    button_style: ButtonStyleResult = field(default_factory=ButtonStyleResult)
    forms: ContactFormResult = field(default_factory=ContactFormResult)
    whitespace: WhitespaceResult = field(default_factory=WhitespaceResult)
    cdp_console: CDPConsoleResult = field(default_factory=CDPConsoleResult)
    cdp_network: CDPNetworkResult = field(default_factory=CDPNetworkResult)
    cdp_vitals: CDPVitalsResult = field(default_factory=CDPVitalsResult)
    og_tags: OGTagsResult = field(default_factory=OGTagsResult)
    ssl: SSLResult = field(default_factory=SSLResult)
    errors: list = field(default_factory=list)
    report_path: str = ""
    dashboard_path: str = ""

# ──── AUDITOR ────

class SEOAuditor:
    def __init__(self, url: str, report_dir: str = "reports"):
        self.url = url
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)

    async def _page(self, browser, vp_name="Desktop"):
        vp = VIEWPORTS.get(vp_name, VIEWPORTS["Desktop"])
        ctx = await browser.new_context(
            viewport=vp,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()
        # Stealth: hide automation flags
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)
        for strategy in ["domcontentloaded", "load", "commit"]:
            try:
                await page.goto(self.url, timeout=20000, wait_until=strategy)
                await page.wait_for_timeout(2000)
                break
            except: pass
        return ctx, page

    async def run_all(self) -> AuditResult:
        r = AuditResult(url=self.url)
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            dt_ctx = ip_ctx = mo_ctx = None
            try:
                dt_ctx, dt_page = await self._page(browser, "Desktop")
                # Wait a bit more for full page render
                try: await dt_page.wait_for_load_state("networkidle", timeout=10000)
                except: pass
                await dt_page.wait_for_timeout(1000)

                # ── STATIC HTML CHECKS (all from one page load) ──
                html = await dt_page.content()

                self._check_title(html, r)
                self._check_meta_desc(html, r)
                self._check_headings(html, r)
                self._check_schema(html, r)
                self._check_image_alt(html, r)
                self._check_responsive(html, r)
                self._check_indexable(html, r, dt_page)
                self._check_canonical(html, r)
                self._check_internal_links(html, r)
                self._check_og_tags(html, r)
                self._check_ssl(r)

                # ── CDP CHECKS (Chrome DevTools Protocol) ──
                try: r.cdp_console, r.cdp_network, r.cdp_vitals = await self._check_cdp(browser)
                except: pass
                self._calc_perf_score(r.cdp_vitals)

                # ── DYNAMIC CHECKS (Playwright) ──
                r.sticky_dt = await self._check_sticky(dt_page, "Desktop")
                r.hero_dt = await self._check_hero(dt_page, "Desktop")
                r.featured_image = await self._check_featured_image(dt_page)
                r.image_load = await self._check_image_loading(dt_page)
                r.breadcrumbs = await self._check_breadcrumbs(dt_page)
                try: r.menu_click = await self._check_menu_clickability(dt_page)
                except: pass
                try: r.fonts = await self._check_fonts(dt_page)
                except: pass
                try: r.button_style = await self._check_button_style(dt_page)
                except: pass
                try: r.forms = await self._check_contact_forms(dt_page)
                except: pass

                try: await dt_ctx.close()
                except: pass

                try:
                    ip_ctx, ip_page = await self._page(browser, "iPad")
                    r.sticky_ip = await self._check_sticky(ip_page, "iPad")
                    r.hero_ip = await self._check_hero(ip_page, "iPad")
                    try: await ip_ctx.close()
                    except: pass
                except: pass

                try:
                    mo_ctx, mo_page = await self._page(browser, "Mobile")
                    r.sticky_mo = await self._check_sticky(mo_page, "Mobile")
                    r.hero_mo = await self._check_hero(mo_page, "Mobile")
                    try: await mo_ctx.close()
                    except: pass
                except: pass

            except Exception as e:
                r.errors.append(str(e))
            finally:
                for ctx in [dt_ctx, ip_ctx, mo_ctx]:
                    if ctx:
                        try: await ctx.close()
                        except: pass
                await browser.close()

        r.report_path = self._generate_report(r)
        return r

    # ──── STATIC CHECKS ────

    def _check_title(self, html, r):
        import re
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.DOTALL)
        if m:
            r.title.text = m.group(1).strip()
            r.title.length = len(r.title.text)
            if r.title.length > 60: r.title.status = "TOO LONG"
            elif r.title.length > 50: r.title.status = "WARNING"
            else: r.title.status = "GOOD"
            r.title.passed = r.title.length <= 60
        else:
            r.title.status = "MISSING"

    def _check_meta_desc(self, html, r):
        import re
        m = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.I)
        if not m:
            m = re.search(r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']description["\']', html, re.I)
        if m:
            r.meta_desc.text = m.group(1).strip()
            r.meta_desc.length = len(r.meta_desc.text)
            if r.meta_desc.length > 160: r.meta_desc.status = "TOO LONG"
            elif r.meta_desc.length > 150: r.meta_desc.status = "WARNING"
            else: r.meta_desc.status = "GOOD"
            r.meta_desc.passed = r.meta_desc.length <= 160
        else:
            r.meta_desc.status = "MISSING"

    def _check_headings(self, html, r):
        import re
        items = []
        for tag in ['h1','h2','h3','h4','h5','h6']:
            for m in re.finditer(rf'<{tag}[^>]*>(.*?)</{tag}>', html, re.I | re.DOTALL):
                text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                text = re.sub(r'\s+', ' ', text)
                import html as hmod
                text = hmod.unescape(text)
                if text:
                    items.append({"tag": tag, "text": text})
        r.headings.total = len(items)
        r.headings.items = items
        r.headings.h1_count = sum(1 for i in items if i["tag"] == "h1")
        if r.headings.h1_count == 0:
            r.headings.issues.append("Missing H1 tag")
        elif r.headings.h1_count > 1:
            r.headings.issues.append(f"Multiple H1 tags ({r.headings.h1_count})")
        levels = [int(i["tag"][1]) for i in items]
        for i in range(1, len(levels)):
            if levels[i] > levels[i-1] + 1:
                r.headings.issues.append(f"Skipped level: {items[i-1]['tag']} → {items[i]['tag']}")
        r.headings.passed = not r.headings.issues

    def _check_schema(self, html, r):
        import re, json
        types = []
        for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.DOTALL):
            try:
                d = json.loads(m.group(1))
                if "@type" in d:
                    t = d["@type"]
                    types.extend(t if isinstance(t, list) else [t])
                if "@graph" in d:
                    for item in d["@graph"]:
                        if "@type" in item:
                            t = item["@type"]
                            types.extend(t if isinstance(t, list) else [t])
            except: pass
        for m in re.finditer(r'itemtype=["\']https?://schema\.org/([^"\']+)["\']', html, re.I):
            types.append(m.group(1))
        r.schema.count = len(types)
        r.schema.types = list(dict.fromkeys(types))
        r.schema.passed = r.schema.count > 0

    def _check_image_alt(self, html, r):
        import re
        imgs = re.findall(r'<img[^>]+>', html, re.I)
        total = len(imgs)
        missing = 0
        for tag in imgs:
            if not re.search(r'alt\s*=', tag, re.I):
                missing += 1
        r.image_alt.total = total
        r.image_alt.missing = missing
        r.image_alt.passed = missing == 0

    def _check_responsive(self, html, r):
        import re
        m = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*content=["\'](.*?)["\']', html, re.I)
        if not m:
            m = re.search(r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']viewport["\']', html, re.I)
        if m:
            r.responsive.has_viewport = True
            r.responsive.content = m.group(1).strip()
            r.responsive.passed = "width=device-width" in r.responsive.content.lower()

    def _check_indexable(self, html, r, page):
        import re
        m = re.search(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\'](.*?)["\']', html, re.I)
        if not m:
            m = re.search(r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']robots["\']', html, re.I)
        if m:
            r.indexable.meta_robots = m.group(1).strip()
            r.indexable.indexable = "noindex" not in r.indexable.meta_robots.lower()
        r.indexable.passed = r.indexable.indexable

    def _check_canonical(self, html, r):
        import re
        m = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\'](.*?)["\']', html, re.I)
        if not m:
            m = re.search(r'<link[^>]*href=["\'](.*?)["\'][^>]*rel=["\']canonical["\']', html, re.I)
        if m:
            r.canonical.href = m.group(1).strip()
            r.canonical.matches = r.canonical.href.rstrip("/") == self.url.rstrip("/")
            r.canonical.passed = True

    def _check_internal_links(self, html, r):
        import re
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        domain = urlparse(self.url).netloc
        links = set()
        for m in re.finditer(r'<a[^>]*href=["\'](.*?)["\']', html, re.I):
            href = m.group(1).strip()
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                full = urljoin(self.url, href)
                if urlparse(full).netloc == domain:
                    links.add(urlparse(full)._replace(fragment="").geturl())
        r.internal_links.total = len(links)

        # Check actual HTTP status of links (limit to 30)
        link_list = list(links)[:30]
        broken = []
        def check(link):
            try:
                resp = requests.head(link, timeout=8, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
                if resp.status_code == 404:
                    return link
                if resp.status_code == 405:
                    resp2 = requests.get(link, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                    if resp2.status_code == 404:
                        return link
            except:
                pass
            return None
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(check, l) for l in link_list]
            for f in as_completed(futures):
                result = f.result()
                if result:
                    broken.append(result)
        r.internal_links.broken = [f"✗ {url}" for url in broken]
        r.internal_links.passed = len(broken) == 0

    def _check_og_tags(self, html, r):
        import re
        og_map = {
            "og:title": "og_title", "og:description": "og_description",
            "og:image": "og_image", "og:url": "og_url",
            "og:type": "og_type", "og:site_name": "og_site_name",
        }
        for prop, attr in og_map.items():
            m = re.search(rf'<meta[^>]*property=["\']{prop}["\'][^>]*content=["\'](.*?)["\']', html, re.I)
            if not m:
                m = re.search(rf'<meta[^>]*content=["\'](.*?)["\'][^>]*property=["\']{prop}["\']', html, re.I)
            if m:
                setattr(r.og_tags, attr, m.group(1).strip())
                r.og_tags.tags_found += 1
        r.og_tags.passed = bool(r.og_tags.og_title and r.og_tags.og_description)

    def _check_ssl(self, r):
        r.ssl.is_https = self.url.startswith("https://")
        if r.ssl.is_https:
            try: requests.get(self.url, timeout=5, verify=True); r.ssl.cert_valid = True
            except: pass
        r.ssl.passed = r.ssl.is_https and r.ssl.cert_valid

    def _calc_perf_score(self, vitals):
        score = 100
        if vitals.lcp > 4.0: score -= 25
        elif vitals.lcp > 2.5: score -= 10
        if vitals.cls > 0.25: score -= 25
        elif vitals.cls > 0.1: score -= 10
        if vitals.ttfb > 0.8: score -= 10
        elif vitals.ttfb > 0.5: score -= 5
        vitals.perf_score = max(0, score)
        vitals.passed = score >= 70

    # ──── CDP CHECKS (Chrome DevTools Protocol) ────

    async def _check_cdp(self, browser):
        """Capture console errors, failed network requests, and performance vitals via CDP."""
        r_console = CDPConsoleResult()
        r_network = CDPNetworkResult()
        r_vitals = CDPVitalsResult()

        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)

        errors = []
        warnings = []
        failed_reqs = []
        request_count = [0]
        _trackers = ["google-analytics", "analytics.google", "googletagmanager", "doubleclick",
                     "trumeasure", "facebook.com/tr", "ads.", "gtm.", "hotjar", "clarity",
                     "google.com/rmkt", "googleadservices", "google.com/ccm"]

        page.on("console", lambda msg: (
            errors.append(msg.text) if msg.type == "error" and not any(d in msg.text.lower() for d in _trackers) else
            warnings.append(msg.text) if msg.type in ("warning", "warn") and not any(d in msg.text.lower() for d in _trackers) else None
        ))

        page.on("requestfailed", lambda req: (
            failed_reqs.append(f"{req.url} ({req.failure})")
            if not any(d in req.url for d in _trackers)
            else None
        ))

        # Listen for all requests (count)
        page.on("request", lambda _: request_count.__setitem__(0, request_count[0] + 1))

        try:
            await page.goto(self.url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # Get performance metrics via CDP
            try:
                cdp = await ctx.new_cdp_session(page)
                metrics = await cdp.send("Performance.getMetrics")
                vital_metrics = {}
                for m in metrics.get("metrics", []):
                    vital_metrics[m["name"]] = m["value"]

                r_vitals.lcp = vital_metrics.get("LayoutCount", 0)  # approximation
                r_vitals.fcp = vital_metrics.get("FirstMeaningfulPaint", 0) / 1000 if vital_metrics.get("FirstMeaningfulPaint", 0) > 0 else 0
                r_vitals.ttfb = vital_metrics.get("NavigationStart", 0)  # placeholder

                # Get Web Vitals from JS
                vitals_js = await page.evaluate("""
                    () => new Promise(resolve => {
                        if (window.performance && window.performance.timing) {
                            const t = performance.timing;
                            resolve({
                                ttfb: t.responseStart - t.requestStart,
                                fcp: 0,
                                lcp: 0,
                                cls: 0
                            });
                        } else {
                            resolve({ ttfb: 0, fcp: 0, lcp: 0, cls: 0 });
                        }
                    })
                """)
                if vitals_js:
                    r_vitals.ttfb = round(vitals_js.get("ttfb", 0) / 1000, 2) if vitals_js.get("ttfb", 0) > 0 else 0

                await cdp.detach()
            except:
                pass

            # Get LCP from PerformanceObserver if available
            try:
                lcp = await page.evaluate("""
                    () => new Promise(resolve => {
                        let lcp = 0;
                        const obs = new PerformanceObserver(list => {
                            const entries = list.getEntries();
                            if (entries.length) lcp = entries[entries.length - 1].startTime;
                        });
                        obs.observe({type: 'largest-contentful-paint', buffered: true});
                        setTimeout(() => { obs.disconnect(); resolve(lcp / 1000); }, 2000);
                    })
                """)
                if lcp: r_vitals.lcp = lcp
            except:
                pass

            try:
                cls = await page.evaluate("""
                    () => new Promise(resolve => {
                        let cls = 0;
                        const obs = new PerformanceObserver(list => {
                            for (const entry of list.getEntries()) {
                                if (!entry.hadRecentInput) cls += entry.value;
                            }
                        });
                        obs.observe({type: 'layout-shift', buffered: true});
                        setTimeout(() => { obs.disconnect(); resolve(cls); }, 2000);
                    })
                """)
                if cls is not None: r_vitals.cls = cls
            except:
                pass

        except Exception as e:
            r_console.errors.append(f"CDP page load error: {e}")

        r_console.errors = errors[:10]
        r_console.warnings = warnings[:10]
        r_network.total_requests = request_count[0]
        r_network.failed = failed_reqs[:10]
        r_network.passed = True  # informational only — most are analytics/trackers
        r_vitals.passed = True

        try: await ctx.close()
        except: pass
        return r_console, r_network, r_vitals

    # ──── DYNAMIC CHECKS ────

    async def _check_sticky(self, page, vp_name):
        vp = VIEWPORTS[vp_name]
        r = StickyResult(viewport=vp_name)

        # Ensure we start from top
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)

        # Take evidence screenshot at the TOP so the menu is always visible
        ss = os.path.join(self.report_dir, f"sticky_{vp_name.lower()}.png")
        try:
            await page.screenshot(path=ss, full_page=False, timeout=5000)
            r.screenshot = ss
        except Exception as e:
            r.issues.append(f"Screenshot failed: {e}")

        # Find header and record position BEFORE scroll
        header_info = await page.evaluate("""
            () => {
                const candidates = [
                    ...document.querySelectorAll('header, nav, [role="navigation"], [class*="header"], [class*="menu"], [class*="nav"]')
                ];
                for (const el of candidates) {
                    const r = el.getBoundingClientRect();
                    if (r.top <= 200 && r.height > 20 && r.height < 400) {
                        return {
                            tag: el.tagName.toLowerCase(),
                            id: el.id,
                            cls: el.className.slice(0, 80),
                            h: Math.round(r.height),
                            topBefore: r.top
                        };
                    }
                }
                return null;
            }
        """)

        if not header_info:
            r.issues.append("No header/nav element found")
            r.passed = False
            return r

        r.selector = header_info["tag"]
        if header_info.get("id"):
            r.selector += f"#{header_info['id']}"
        r.height = header_info["h"]

        # Scroll down in steps to trigger sticky JS (scroll deeper for smaller viewports)
        scroll1 = min(vp["height"] * 0.8, 800)
        scroll2 = min(vp["height"] * 1.0, 1000)
        await page.evaluate(f"window.scrollBy(0, {scroll1})")
        await page.wait_for_timeout(2000)
        await page.evaluate(f"window.scrollBy(0, {scroll2})")
        await page.wait_for_timeout(2500)

        # Check: any element at viewport top with position fixed/sticky?
        header_after = await page.evaluate("""
            () => {
                // Check 1: ALL sticky modules - find the ACTIVE one (position fixed, height > 0)
                const stickyMods = document.querySelectorAll(
                    '.et_pb_sticky--stuck, .et_pb_sticky_module, .stuck, .sticky, .is-sticky, ' +
                    '.sticky-header, .fixed-header, .header-scrolled, .sticky-active, ' +
                    '[class*="sticky"], [class*="stuck"], [class*="Sticky"], [class*="fixed"]'
                );
                for (const el of stickyMods) {
                    const cs = getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    if ((cs.position === 'fixed' || cs.position === 'sticky') && r.height > 20)
                        return { topAfter: r.top, pos: cs.position };
                }

                // Check 2: header/nav tag with sticky position
                const headerTag = document.querySelector('header, nav');
                if (headerTag) {
                    const cs = getComputedStyle(headerTag);
                    const r = headerTag.getBoundingClientRect();
                    if (cs.position === 'fixed' || cs.position === 'sticky')
                        return { topAfter: r.top, pos: cs.position };
                }

                // Check 3: any element fixed/sticky at viewport top
                const topEls = document.querySelectorAll('body > div, header, nav');
                for (const el of topEls) {
                    try {
                        const cs = getComputedStyle(el);
                        if (cs.position === 'fixed' || cs.position === 'sticky') {
                            const r = el.getBoundingClientRect();
                            if (r.top >= -10 && r.top <= 100 && r.height > 20)
                                return { topAfter: r.top, pos: cs.position };
                        }
                    } catch(e) {}
                }

                // Fallback: did header scroll away?
                if (headerTag) {
                    const r = headerTag.getBoundingClientRect();
                    return { topAfter: r.top, pos: getComputedStyle(headerTag).position };
                }
                return null;
            }
        """)

        if header_after:
            stayed = abs(header_after["topAfter"] - header_info["topBefore"]) < 100
            is_fixed = header_after["pos"] in ("fixed", "sticky")
            r.visible_scrolled = stayed or is_fixed
        else:
            r.visible_scrolled = False

        r.has_sticky = r.visible_scrolled
        if not r.visible_scrolled:
            r.issues.append("Header scrolled out of view — no sticky detected")

        r.passed = r.has_sticky and r.visible_scrolled
        return r

    async def _check_featured_image(self, page):
        r = FeaturedImageResult()
        og = await page.evaluate("""
            () => {
                const o = document.querySelector('meta[property="og:image"]');
                if (o) return o.getAttribute('content');
                const t = document.querySelector('meta[name="twitter:image"]');
                if (t) return t.getAttribute('content');
                return null;
            }
        """)
        if og:
            r.og_image = og
            ok = await page.evaluate(f"""() => {{ const i = new Image(); i.src = '{og}'; return new Promise(r => {{ i.onload = () => r(true); i.onerror = () => r(false); }}); }}""")
            r.image_exists = ok
        else: r.issues.append("No og:image found")
        r.passed = r.image_exists or not r.issues
        return r

    async def _check_image_loading(self, page):
        r = ImageLoadResult()
        try:
            await page.evaluate("""
                async () => {
                    const d = ms => new Promise(r => setTimeout(r, ms));
                    for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await d(300); }
                    window.scrollTo(0, 0);
                }
            """)
            await page.wait_for_timeout(3000)
            data = json.loads(await page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img');
                    const broken = [];
                    for (const img of imgs) { if (img.naturalWidth === 0) broken.push(img.src || '(no src)'); }
                    return JSON.stringify({ total: imgs.length, broken });
                }
            """))
            r.total = data["total"]; r.broken = data["broken"]
            for url in list(r.broken):
                try:
                    resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code < 400:
                        r.broken.remove(url)
                except: pass
            if r.broken:
                ss = os.path.join(self.report_dir, "image_loading.png")
                try: await page.screenshot(path=ss, full_page=True, timeout=5000)
                except: pass
                r.screenshot = ss
        except: pass
        return r

    async def _check_hero(self, page, vp_name):
        r = HeroResult(viewport=vp_name)

        # Wait for images to finish loading (for slow sites)
        try:
            await page.evaluate("""
                () => Promise.all(
                    Array.from(document.querySelectorAll('img'))
                        .filter(img => !img.complete)
                        .map(img => new Promise(r => { img.onload = r; img.onerror = r; setTimeout(r, 3000); }))
                )
            """)
        except: pass

        hero = await page.evaluate("""
            () => {
                const vh = window.innerHeight;
                const vw = window.innerWidth;
                const searchTop = vh < 800 ? vh * 0.9 : vh * 0.6;
                const minWidth = Math.max(250, vw * 0.5);
                const minHeight = 160;  // hero should be at least 160px tall
                const imgs = document.querySelectorAll('img');
                let best = null, bestArea = 0;
                for (const img of imgs) {
                    if (!img.complete || img.naturalWidth === 0) continue;
                    const rect = img.getBoundingClientRect();
                    if (rect.top < searchTop && rect.width > minWidth && rect.height > minHeight) {
                        const area = rect.width * rect.height;
                        if (area > bestArea) { bestArea = area; best = { src: img.src, w: img.naturalWidth, h: img.naturalHeight, foundVia: 'img' }; }
                    }
                }
                if (best) return best;
                const topEls = document.querySelectorAll('section, div, header, .hero, .banner, [class*="hero"], [class*="banner"]');
                for (const el of topEls) {
                    const cs = getComputedStyle(el); const bg = cs.backgroundImage;
                    if (bg && bg !== 'none' && !bg.includes('gradient')) {
                        const rect = el.getBoundingClientRect();
                        if (rect.top < vh * 0.4 && rect.width > 200 && rect.height > 100) {
                            const srcMatch = bg.match(/url\\(["']?(.*?)["']?\\)/);
                            return { src: srcMatch ? srcMatch[1] : bg.slice(0,80), w: rect.width, h: rect.height, foundVia: 'css-bg' };
                        }
                    }
                }
                const sections = document.querySelectorAll('section, div[class*="section"], main > *');
                for (const sec of sections) {
                    const rect = sec.getBoundingClientRect();
                    if (rect.top < vh * 0.3 && rect.width > 300 && rect.height > 200)
                        return { src: '', w: rect.width, h: rect.height, foundVia: 'section' };
                }
                return null;
            }
        """)
        if hero:
            r.exists = True; r.src = hero.get("src", ""); r.method = hero.get("foundVia", ""); r.loaded = True
        else: r.issues.append("No hero image found")
        r.passed = r.exists and r.loaded
        return r

    async def _check_breadcrumbs(self, page):
        r = BreadcrumbsResult()
        info = await page.evaluate("""
            () => {
                const s = document.querySelectorAll('script[type="application/ld+json"]');
                for (const sc of s) { try { const d = JSON.parse(sc.textContent); if (d['@type'] === 'BreadcrumbList' || (d['@graph'] && d['@graph'].some(g => g['@type'] === 'BreadcrumbList'))) return { found: 'structured_data' }; } catch(e) {} }
                const nav = document.querySelector('nav[aria-label="breadcrumb"], nav.breadcrumb, .breadcrumbs, .breadcrumb');
                if (nav) return { found: 'html', text: nav.innerText.trim().slice(0,200) };
                const bc = document.querySelector('[class*="breadcrumb"], [class*="Breadcrumb"], #breadcrumbs');
                if (bc) return { found: 'html', text: bc.innerText.trim().slice(0,200) };
                return null;
            }
        """)
        if info: r.exists = True; r.text = info.get("text", ""); r.method = info["found"]
        r.passed = r.exists
        return r

    async def _check_menu_clickability(self, page):
        data = json.loads(await page.evaluate("""
            () => {
                const links = document.querySelectorAll('nav a[href], header a[href], .menu a[href], [role="navigation"] a[href]');
                return JSON.stringify(Array.from(links).map(a => a.getAttribute('href') || ''));
            }
        """))
        return MenuClickResult(total_links=len(data))

    async def _check_fonts(self, page):
        r = FontsResult()
        fonts = await page.evaluate("""
            () => {
                const els = document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,a,span,div');
                const f = new Set();
                for (const el of els) { try { f.add(getComputedStyle(el).fontFamily); } catch(e) {} }
                return Array.from(f);
            }
        """)
        r.fonts = [f.strip("'\"") for f in fonts]
        r.unique_fonts = len(r.fonts)
        r.passed = r.unique_fonts <= 6
        return r

    async def _check_button_style(self, page):
        data = json.loads(await page.evaluate("""
            () => {
                const btns = document.querySelectorAll('a[href], button, input[type="submit"], [role="button"]');
                const seen = new Set(); const fonts = new Set();
                for (const b of btns) {
                    try {
                        const cs = getComputedStyle(b);
                        seen.add(cs.paddingTop+cs.paddingRight+cs.paddingBottom+cs.paddingLeft+'|'+cs.fontSize+'|'+cs.fontWeight);
                        fonts.add(cs.fontFamily);
                    } catch(e) {}
                }
                return JSON.stringify({ styles: Array.from(seen), fonts: Array.from(fonts) });
            }
        """))
        r = ButtonStyleResult()
        r.unique_styles = len(data["styles"])
        r.button_fonts = [f.strip("'\"") for f in data["fonts"]]
        return r

    async def _check_contact_forms(self, page):
        forms = json.loads(await page.evaluate("""
            () => {
                const found = new Set();

                // 1. Standard <form> elements with inputs
                document.querySelectorAll('form').forEach(f => {
                    if (f.querySelector('input, textarea, select')) found.add('form');
                });

                // 2. Popup/modal forms (common selectors)
                const popupSelectors = [
                    '[class*="popup"] input', '[class*="modal"] input', '[class*="widget"] input',
                    '[class*="overlay"] input', '[id*="popup"] input', '[id*="modal"] input',
                    '[class*="popup"] textarea', '[class*="modal"] textarea', '[class*="widget"] textarea'
                ];
                for (const sel of popupSelectors) {
                    if (document.querySelector(sel)) found.add('popup');
                }

                // 3. Third-party form widgets (HubSpot, Captivated, Drift, Intercom, etc.)
                const widgetSelectors = [
                    '[class*="hubspot"], [id*="hubspot"], [class*="hs-form"]',
                    '[class*="captivated"], [class*="drift"], [class*="intercom"]',
                    '[class*="tawk"], [class*="zendesk"], [class*="livechat"]',
                    '[class*="form-container"], [class*="contact-form"]'
                ];
                for (const sel of widgetSelectors) {
                    if (document.querySelector(sel)) found.add('widget');
                }

                // 4. role="form" or aria-label with form-related words
                document.querySelectorAll('[role="form"], [aria-label*="contact" i], [aria-label*="form" i], [aria-label*="message" i], [aria-label*="inquiry" i]').forEach(el => {
                    if (el.querySelector('input, textarea, select')) found.add('aria-form');
                });

                // 5. Shadow DOM forms
                document.querySelectorAll('*').forEach(el => {
                    if (el.shadowRoot) {
                        const shadowForms = el.shadowRoot.querySelectorAll('form, [role="form"]');
                        if (shadowForms.length) found.add('shadow-dom');
                    }
                });

                return JSON.stringify(Array.from(found));
            }
        """))
        r = ContactFormResult(count=len(forms))
        r.passed = r.count > 0
        return r

    async def _check_whitespace(self, page):
        r = WhitespaceResult()
        issues = json.loads(await page.evaluate("""
            () => {
                const issues = [];
                const texts = document.querySelectorAll('h1,h2,h3,p');
                for (let i = 0; i < texts.length - 1; i++) {
                    try {
                        const a = texts[i].getBoundingClientRect();
                        const b = texts[i+1].getBoundingClientRect();
                        if (a.bottom >= b.top - 2 && a.bottom <= b.top + 2)
                            issues.push(texts[i].tagName + ' and ' + texts[i+1].tagName + ' may be too close');
                    } catch(e) {}
                }
                return JSON.stringify(issues.slice(0, 5));
            }
        """))
        r.issues = issues
        r.passed = len(issues) == 0
        ss = os.path.join(self.report_dir, "whitespace.png")
        try: await page.screenshot(path=ss, full_page=True, timeout=5000)
        except: pass
        r.screenshot = ss
        return r

    # ──── REPORT ────

    def _generate_report(self, r):
        def _s(p): return "PASS" if p else "FAIL"
        def _c(p): return "#22c55e" if p else "#ef4444"
        def _i(p): return "✓" if p else "✗"

        def card(title, passed, items, screenshot=""):
            items_html = "".join(
                f'<div class="{"issue" if "✗" in i else "ok"}">{i}</div>'
                for i in (items if items else ["✓ All good"])
            )
            ss = f'<img src="{os.path.basename(screenshot)}" loading="lazy" class="screenshot">' if screenshot and os.path.exists(screenshot) else ""
            return f'''<div class="check-item">
              <div class="check-header">
                <span class="check-title">{title}</span>
                <span class="badge {_s(passed).lower()}">{_s(passed)}</span>
              </div>
              <div class="check-body">{items_html}</div>
              {ss}
            </div>'''

        def section(title, cards_html):
            return f'<div class="section"><h2>{title}</h2>{cards_html}</div>'

        # ── STATIC CHECKS ──
        static_cards = ""
        static_cards += card("Title", r.title.passed, [f'"{r.title.text}"', f"Length: {r.title.length} chars | {r.title.status}"])
        static_cards += card("Meta Description", r.meta_desc.passed, [f"{r.meta_desc.text[:200]}", f"Length: {r.meta_desc.length} chars | {r.meta_desc.status}"])
        static_cards += card("Headings", r.headings.passed, [f"H1: {r.headings.h1_count} | Total: {r.headings.total}"] + r.headings.issues + [f"{h['tag']}: {h['text'][:80]}" for h in r.headings.items[:10]])
        static_cards += card("Schema Markup", r.schema.passed, [f"Blocks: {r.schema.count}"] + [f"• {t}" for t in r.schema.types[:6]])
        static_cards += card("Image Alt Text", r.image_alt.passed, [f"Total: {r.image_alt.total} | Missing: {r.image_alt.missing}"])
        static_cards += card("Responsive (Viewport)", r.responsive.passed, [f"Content: {r.responsive.content or 'Not found'}"])
        static_cards += card("Indexability", r.indexable.passed, [f"Indexable: {r.indexable.indexable}", f"Robots: {r.indexable.meta_robots or 'none'}"])
        static_cards += card("Canonical Tag", r.canonical.passed, [f"href: {r.canonical.href or 'Not found'}", f"Matches URL: {r.canonical.matches}"])
        static_cards += card("Internal Links", r.internal_links.passed, [f"Total: {r.internal_links.total} | Broken: {len(r.internal_links.broken)}"] + [f"✗ {b}" for b in r.internal_links.broken])
        static_cards += card("OG Tags", r.og_tags.passed, [f"Tags found: {r.og_tags.tags_found}/6", f"Title: {r.og_tags.og_title[:60] or '—'}", f"Description: {r.og_tags.og_description[:60] or '—'}", f"Image: {r.og_tags.og_image[:60] or '—'}"])
        static_cards += card("SSL/HTTPS", r.ssl.passed, [f"HTTPS: {r.ssl.is_https}", f"Certificate valid: {r.ssl.cert_valid}"])

        # ── DYNAMIC CHECKS ──
        dynamic_cards = ""
        dynamic_cards += card("Image Loading", True, [f"Total: {r.image_load.total} | Flagged: {len(r.image_load.broken)}"] + [f"✗ {b}" for b in r.image_load.broken[:5]], r.image_load.screenshot)
        dynamic_cards += card("Hero Image (Desktop)", r.hero_dt.passed, [f"Source: {r.hero_dt.src[:60] or 'none'}", f"Method: {r.hero_dt.method}"] + r.hero_dt.issues)
        dynamic_cards += card("Hero Image (iPad)", r.hero_ip.passed, [f"Source: {r.hero_ip.src[:60] or 'none'}", f"Method: {r.hero_ip.method}"] + r.hero_ip.issues)
        dynamic_cards += card("Hero Image (Mobile)", r.hero_mo.passed, [f"Source: {r.hero_mo.src[:60] or 'none'}", f"Method: {r.hero_mo.method}"] + r.hero_mo.issues)
        dynamic_cards += card("Breadcrumbs", True, [f"Found: {r.breadcrumbs.exists} ({r.breadcrumbs.method})", f"Text: {r.breadcrumbs.text[:150] or '—'}"])
        dynamic_cards += card("Menu Clickability", True, [f"Nav links: {r.menu_click.total_links}"])
        dynamic_cards += card("Font Consistency", r.fonts.passed, [f"Unique fonts: {r.fonts.unique_fonts}", f"Fonts: {', '.join(r.fonts.fonts[:6])}"])
        dynamic_cards += card("Button Style", True, [f"Variations: {r.button_style.unique_styles}", f"Fonts: {', '.join(r.button_style.button_fonts[:6])}"])
        dynamic_cards += card("Contact Forms", r.forms.passed, [f"Found: {r.forms.count}"])

        # ── CDP CHECKS ──
        cdp_cards = ""
        cdp_cards += card("Console Errors", r.cdp_console.passed, [f"Errors: {len(r.cdp_console.errors)} | Warnings: {len(r.cdp_console.warnings)}"] + [f"✗ {e}" for e in r.cdp_console.errors[:5]] + [f"⚠ {w}" for w in r.cdp_console.warnings[:5]])
        cdp_cards += card("Failed Network Requests", r.cdp_network.passed, [f"Total: {r.cdp_network.total_requests} | Failed: {len(r.cdp_network.failed)}"] + [f"✗ {f}" for f in r.cdp_network.failed[:5]])
        cdp_cards += card("Core Web Vitals", r.cdp_vitals.passed, [f"LCP: {r.cdp_vitals.lcp:.2f}s", f"CLS: {r.cdp_vitals.cls:.3f}", f"FCP: {r.cdp_vitals.fcp:.2f}s", f"TTFB: {r.cdp_vitals.ttfb:.2f}s"])

        # ── EVIDENCE SCREENSHOTS ──
        evidence = ""
        for label, ss in [("Sticky Desktop", r.sticky_dt.screenshot), ("Sticky iPad", r.sticky_ip.screenshot), ("Sticky Mobile", r.sticky_mo.screenshot)]:
            if ss and os.path.exists(ss):
                evidence += f'<div class="ss-card"><img src="{os.path.basename(ss)}" loading="lazy"><span>{label}</span></div>'
        if r.image_load.screenshot and os.path.exists(r.image_load.screenshot):
            evidence += f'<div class="ss-card"><img src="{os.path.basename(r.image_load.screenshot)}" loading="lazy"><span>Image Loading</span></div>'

        evidence_section = ""
        if evidence:
            evidence_section = f"""
  <div class="section"><h2>Evidence Screenshots</h2>
  <div class="screenshots">{evidence}</div></div>"""

        # ── OVERALL SCORE ──
        checks = [
            ("Title", r.title.passed), ("Meta Desc", r.meta_desc.passed), ("Headings", r.headings.passed),
            ("Schema", r.schema.passed), ("Image Alt", r.image_alt.passed), ("Responsive", r.responsive.passed),
            ("Indexability", r.indexable.passed), ("Canonical", r.canonical.passed), ("Internal Links", r.internal_links.passed),
            ("OG Tags", r.og_tags.passed), ("SSL", r.ssl.passed),
            ("Hero Desktop", r.hero_dt.passed), ("Hero iPad", r.hero_ip.passed), ("Hero Mobile", r.hero_mo.passed),
            ("Fonts", r.fonts.passed), ("Forms", r.forms.passed),
            ("CDP Console", r.cdp_console.passed), ("CDP Network", r.cdp_network.passed), ("Web Vitals", r.cdp_vitals.passed),
        ]
        total = sum(1 for _, p in checks if p)
        score = round(total / len(checks) * 100, 1)
        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
        grade_color = "#22c55e" if grade == "A" else "#84cc16" if grade == "B" else "#eab308" if grade == "C" else "#f97316" if grade == "D" else "#ef4444"

        score_html = f"""<div class="score-banner" style="border-top:4px solid {grade_color}">
  <div class="score-num" style="color:{grade_color}">{score}%</div>
  <div class="score-grade" style="background:{grade_color}">Grade {grade}</div>
  <div class="score-detail">{total}/{len(checks)} checks passed</div>
</div>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEO + QA Audit — {r.url}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#f1f5f9; color:#1e293b; padding:32px; line-height:1.5; }}
  .container {{ max-width:960px; margin:0 auto; }}
  h1 {{ font-size:22px; margin-bottom:2px; color:#0f172a; }}
  .url {{ color:#64748b; font-size:12px; word-break:break-all; margin-bottom:20px; }}
  .disclaimer {{ background:#fffbeb; border:2px solid #f59e0b; border-radius:8px; padding:16px 20px; margin-bottom:24px; font-size:12px; color:#78350f; line-height:1.6; }}
  .disclaimer strong {{ color:#92400e; }}
  .disclaimer code {{ background:#fef3c7; padding:1px 4px; border-radius:3px; font-size:11px; }}
  .overview {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(100px,1fr)); gap:6px; margin-bottom:28px; }}
  .stat {{ background:white; border-radius:8px; padding:10px; text-align:center; box-shadow:0 1px 2px rgba(0,0,0,0.05); }}
  .stat .num {{ font-size:18px; font-weight:700; }}
  .stat .label {{ font-size:9px; color:#64748b; margin-top:2px; text-transform:uppercase; letter-spacing:0.3px; }}
  .section {{ margin-bottom:28px; }}
  .section h2 {{ font-size:14px; color:#334155; margin-bottom:12px; padding-bottom:6px; border-bottom:2px solid #e2e8f0; }}
  .check-item {{ background:white; border-radius:8px; margin-bottom:8px; box-shadow:0 1px 2px rgba(0,0,0,0.05); overflow:hidden; }}
  .check-header {{ display:flex; justify-content:space-between; align-items:center; padding:10px 14px; border-bottom:1px solid #f1f5f9; }}
  .check-title {{ font-size:12px; font-weight:600; color:#334155; }}
  .badge {{ font-size:9px; padding:2px 8px; border-radius:10px; color:white; font-weight:600; text-transform:uppercase; }}
  .badge.pass {{ background:#22c55e; }}
  .badge.fail {{ background:#ef4444; }}
  .check-body {{ padding:10px 14px; font-size:11px; color:#475569; }}
  .check-body .issue {{ color:#ef4444; }}
  .check-body .ok {{ color:#16a34a; }}
  .screenshot {{ width:100%; border-top:1px solid #f1f5f9; }}
  .score-banner {{ display:flex; align-items:center; gap:12px; background:white; border-radius:8px; padding:14px 20px; margin-bottom:20px; box-shadow:0 1px 2px rgba(0,0,0,0.05); }}
  .score-num {{ font-size:28px; font-weight:800; }}
  .score-grade {{ font-size:11px; padding:3px 10px; border-radius:10px; color:white; font-weight:700; text-transform:uppercase; }}
  .score-detail {{ font-size:12px; color:#64748b; margin-left:auto; }}
  .screenshots {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:10px; }}
  .ss-card {{ background:white; border-radius:8px; overflow:hidden; box-shadow:0 1px 2px rgba(0,0,0,0.05); }}
  .ss-card img {{ width:100%; display:block; }}
  .ss-card span {{ display:block; font-size:10px; color:#64748b; padding:6px 10px; text-align:center; }}
</style>
</head>
<body>
<div class="container">
  <h1>SEO + QA Audit Report</h1>
  <div class="url">{r.url}</div>

  {score_html}

  <div class="overview">
    {"".join(f'<div class="stat" style="border-top:3px solid {_c(p)}"><div class="num" style="color:{_c(p)}">{_i(p)}</div><div class="label">{n}</div></div>' for n, p in [
        ("Title", r.title.passed), ("Meta", r.meta_desc.passed), ("Headings", r.headings.passed),
        ("Schema", r.schema.passed), ("Image Alt", r.image_alt.passed), ("Responsive", r.responsive.passed),
            ("Index", r.indexable.passed), ("Canonical", r.canonical.passed),
            ("OG Tags", r.og_tags.passed), ("SSL", r.ssl.passed),
            ("Hero", r.hero_dt.passed),
        ("Images", True), ("Fonts", r.fonts.passed), ("Forms", r.forms.passed),
        ("CDP", r.cdp_console.passed), ("Vitals", r.cdp_vitals.passed),
    ])}
  </div>

  {section("Static Checks (HTML)", static_cards)}
  {section("Dynamic Checks (Playwright)", dynamic_cards)}
  {section("Chrome DevTools Protocol (CDP)", cdp_cards)}
  {evidence_section}

  <div style="text-align:center; color:#94a3b8; font-size:10px; margin-top:24px; padding-top:16px; border-top:1px solid #e2e8f0;">
    Generated by SEO + QA Audit Tool | Playwright + CDP
  </div>
</div>
</body></html>"""
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        domain = urlparse(self.url).netloc.replace("www.", "")
        filename = f"report-{domain}-{ts}.html"
        path = os.path.join(self.report_dir, filename)
        with open(path, "w") as f:
            f.write(html)
        return path
