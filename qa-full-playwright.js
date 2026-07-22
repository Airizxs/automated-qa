import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const VIEWPORTS = [
  { name: 'Desktop', width: 1280, height: 800 },
  { name: 'Tablet', width: 768, height: 1024 },
  { name: 'Mobile', width: 375, height: 812 },
];

function getUA(mobile) {
  return mobile
    ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
}

async function runAllChecks(url) {
  const outputDir = resolve(__dirname, 'reports', `qa-full-${Date.now()}`);
  mkdirSync(outputDir, { recursive: true });
  mkdirSync(resolve(outputDir, 'screenshots'), { recursive: true });

  const results = {
    url,
    timestamp: new Date().toISOString(),
    automated: {},
    environment: {},
  };

  const browser = await chromium.launch({ headless: true });

  for (const vp of VIEWPORTS) {
    const isMobile = vp.name === 'Mobile';
    console.log(`\n=== ${vp.name} (${vp.width}x${vp.height}) ===`);

    const context = await browser.newContext({
      userAgent: getUA(isMobile),
      viewport: { width: vp.width, height: vp.height },
      isMobile,
      hasTouch: isMobile,
      deviceScaleFactor: isMobile ? 2 : 1,
    });

    const page = await context.newPage();
    const checks = {};

    // ─── Network monitoring ───────────────────────────────
    const networkLog = [];
    const consoleErrors = [];
    const imageStats = [];

    page.on('response', (res) => {
      const ct = res.headers()['content-type'] || '';
      networkLog.push({
        url: res.url(),
        status: res.status(),
        statusText: res.statusText(),
        contentType: ct,
        size: res.headers()['content-length'] || 'unknown',
      });
    });

    page.on('requestfailed', (req) => {
      networkLog.push({
        url: req.url(),
        status: 0,
        statusText: req.failure()?.errorText || 'failed',
        contentType: '',
        size: 0,
      });
    });

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push({ type: msg.type(), text: msg.text() });
      }
    });

    // ─── Navigate ─────────────────────────────────────────
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    } catch (e) {
      console.log(`  Navigation warning: ${e.message}`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
    }
    await page.waitForTimeout(2000);

    // Scroll to trigger lazy loading
    await autoScroll(page);

    await page.waitForTimeout(1000);

    // Take fullpage screenshot
    const screenshotPath = resolve(outputDir, 'screenshots', `${vp.name.toLowerCase()}-fullpage.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});

    // ─── A. PERFORMANCE ───────────────────────────────────
    // PSI is done via external API, but we can check console errors
    checks.console_errors = {
      status: consoleErrors.length === 0 ? 'PASS' : 'FAIL',
      detail: consoleErrors.length > 0
        ? consoleErrors.map(e => e.text).join('; ').substring(0, 200)
        : 'No console errors',
      count: consoleErrors.length,
    };

    // ─── B. WP ROCKET ─────────────────────────────────────
    const wpRocketCheck = await page.evaluate(() => {
      const html = document.documentElement.innerHTML;
      return {
        critical_css: html.includes('rocket-critical-css') || html.includes('data-rocket-critical-css'),
        delay_js: html.includes('data-rocket-defer'),
        lazyload: html.includes('loading="lazy"'),
        webp_check: Array.from(document.querySelectorAll('img'))
          .some(img => img.currentSrc?.includes('.webp') || img.src?.includes('.webp')),
      };
    });
    checks.wp_rocket_critical_css = {
      status: wpRocketCheck.critical_css ? 'PASS' : 'FAIL',
      detail: wpRocketCheck.critical_css
        ? 'Remove Unused CSS active (critical CSS found)'
        : 'No critical CSS detected — WP Rocket Remove Unused CSS may be off',
    };
    checks.wp_rocket_delay_js = {
      status: wpRocketCheck.delay_js ? 'PASS' : 'FAIL',
      detail: wpRocketCheck.delay_js
        ? 'Delay JS execution active'
        : 'No delayed JS detected',
    };
    checks.wp_rocket_lazyload = {
      status: wpRocketCheck.lazyload ? 'PASS' : 'WARN',
      detail: wpRocketCheck.lazyload
        ? 'Lazy loading active on images'
        : 'No loading="lazy" attributes found',
    };
    checks.wp_rocket_webp = {
      status: wpRocketCheck.webp_check ? 'PASS' : 'WARN',
      detail: wpRocketCheck.webp_check
        ? 'WebP images detected'
        : 'No WebP images found in rendered DOM',
    };

    // ─── C. IMAGES (rendered) ─────────────────────────────
    const renderedImages = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('img')).map(img => {
        const rect = img.getBoundingClientRect();
        return {
          src: img.src || '',
          currentSrc: img.currentSrc || img.src || '',
          alt: img.alt || '',
          naturalWidth: img.naturalWidth || 0,
          naturalHeight: img.naturalHeight || 0,
          renderedWidth: Math.round(rect.width),
          renderedHeight: Math.round(rect.height),
          visible: rect.width > 0 && rect.height > 0,
          loading: img.getAttribute('loading') || '',
          isPNG: (img.src || '').includes('.png') || (img.currentSrc || '').includes('.png'),
        };
      });
    });

    const brokenCount = renderedImages.filter(
      img => img.visible && (img.naturalWidth === 0 || img.naturalHeight === 0)
    ).length;

    const oversizedPNGs = renderedImages.filter(
      img => img.isPNG && img.naturalWidth > 0 && img.renderedWidth > 0
        && (img.naturalWidth / img.renderedWidth > 2)
    ).length;

    const missingAlt = renderedImages.filter(
      img => img.visible && !img.alt && img.renderedWidth > 50
    ).length;

    checks.images_broken = {
      status: brokenCount === 0 ? 'PASS' : 'FAIL',
      detail: `${brokenCount} broken images out of ${renderedImages.length} total`,
      count: brokenCount,
    };
    checks.images_oversized_png = {
      status: oversizedPNGs === 0 ? 'PASS' : 'WARN',
      detail: `${oversizedPNGs} PNGs rendered significantly smaller than natural size`,
    };
    checks.images_alt_text = {
      status: missingAlt === 0 ? 'PASS' : 'FAIL',
      detail: `${missingAlt} visible images missing alt text`,
    };

    // ─── D. LAYOUT ────────────────────────────────────────
    const layoutCheck = await page.evaluate(() => {
      const vpMeta = document.querySelector('meta[name="viewport"]');
      const vpContent = vpMeta?.getAttribute('content') || '';
      return {
        viewport_content: vpContent,
        has_main: !!document.querySelector('main'),
        dom_elements: document.querySelectorAll('*').length,
        html_size: document.documentElement.innerHTML.length,
        blocks_zoom: vpContent.includes('user-scalable=0') || vpContent.includes('user-scalable=no') || vpContent.includes('maximum-scale=1.0'),
      };
    });

    checks.layout_viewport = {
      status: layoutCheck.viewport_content ? 'PASS' : 'FAIL',
      detail: layoutCheck.viewport_content
        ? `Viewport meta: ${layoutCheck.viewport_content.substring(0, 120)}`
        : 'No viewport meta tag found',
    };
    checks.layout_zoom = {
      status: layoutCheck.blocks_zoom ? 'FAIL' : 'PASS',
      detail: layoutCheck.blocks_zoom
        ? 'Pinch-zoom is BLOCKED (user-scalable=0 or maximum-scale=1.0)'
        : 'Pinch-zoom allowed',
    };
    checks.layout_dom_size = {
      status: layoutCheck.dom_elements < 1400 ? 'PASS' : 'WARN',
      detail: `~${layoutCheck.dom_elements} DOM elements`,
    };
    checks.layout_html_size = {
      status: (layoutCheck.html_size / 1024) < 150 ? 'PASS' : 'WARN',
      detail: `${Math.round(layoutCheck.html_size / 1024)}KB HTML`,
    };

    // ─── E. ACCESSIBILITY ─────────────────────────────────
    const a11yCheck = await page.evaluate(() => {
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
      const headingLevels = headings.map(h => parseInt(h.tagName[1]));
      let orderOk = true;
      for (let i = 0; i < headingLevels.length - 1; i++) {
        if (headingLevels[i + 1] > headingLevels[i] + 1) {
          orderOk = false;
          break;
        }
      }
      const genericLinks = Array.from(document.querySelectorAll('a'))
        .filter(a => a.textContent.trim().toUpperCase() === 'LEARN MORE')
        .length;
      return {
        heading_order_ok: orderOk,
        heading_count: headingLevels.length,
        heading_levels: headingLevels,
        generic_links: genericLinks,
        main_landmark: !!document.querySelector('main'),
      };
    });

    checks.a11y_heading_order = {
      status: a11yCheck.heading_order_ok ? 'PASS' : 'FAIL',
      detail: a11yCheck.heading_order_ok
        ? `Headings OK (${a11yCheck.heading_count} total): H${[...new Set(a11yCheck.heading_levels)].join(', H')}`
        : `Heading skip detected: ${a11yCheck.heading_levels.join(' → ')}`,
    };
    checks.a11y_main_landmark = {
      status: a11yCheck.main_landmark ? 'PASS' : 'FAIL',
      detail: a11yCheck.main_landmark ? '<main> landmark present' : 'No <main> landmark found',
    };
    checks.a11y_generic_links = {
      status: a11yCheck.generic_links === 0 ? 'PASS' : 'FAIL',
      detail: `${a11yCheck.generic_links} "Learn More" links found (use descriptive link text)`,
    };

    // ─── F. SEO ───────────────────────────────────────────
    const seoCheck = await page.evaluate(() => {
      const title = document.title || '';
      const desc = document.querySelector('meta[name="description"]')?.getAttribute('content') || '';
      const canonical = document.querySelector('link[rel="canonical"]')?.getAttribute('href') || '';
      const noindex = document.querySelector('meta[name="robots"][content*="noindex"]');
      const h1 = document.querySelector('h1')?.textContent?.trim() || '';
      return {
        title: title.substring(0, 100),
        title_length: title.length,
        description: desc.substring(0, 150),
        canonical,
        noindex: !!noindex,
        h1,
      };
    });

    checks.seo_title = {
      status: seoCheck.title ? 'PASS' : 'FAIL',
      detail: seoCheck.title
        ? `Title (${seoCheck.title_length} chars): ${seoCheck.title}`
        : 'No title tag found',
    };
    checks.seo_meta_description = {
      status: seoCheck.description ? 'PASS' : 'FAIL',
      detail: seoCheck.description
        ? `Meta description found (${seoCheck.description.length} chars)`
        : 'No meta description found',
    };
    checks.seo_canonical = {
      status: seoCheck.canonical ? 'PASS' : 'WARN',
      detail: seoCheck.canonical || 'No canonical URL',
    };
    checks.seo_noindex = {
      status: seoCheck.noindex ? 'FAIL' : 'PASS',
      detail: seoCheck.noindex ? 'Page has noindex directive!' : 'Page is indexable',
    };
    checks.seo_h1 = {
      status: seoCheck.h1 ? 'PASS' : 'FAIL',
      detail: seoCheck.h1 ? `H1: ${seoCheck.h1}` : 'No H1 heading found',
    };

    // ─── G. THIRD-PARTY (from network log) ────────────────
    const thirdPartyUrls = networkLog
      .filter(n => n.status > 0)
      .map(n => n.url);

    const trustindex = thirdPartyUrls.filter(u => u.includes('trustindex'));
    const hasEasypie = thirdPartyUrls.some(u => u.includes('easypiechart'));
    const hasFontAwesome = thirdPartyUrls.some(u =>
      u.includes('font-awesome') || u.includes('fontawesome') || u.includes('fa-')
    );
    const scripts = networkLog.filter(n => n.contentType.includes('javascript'));
    const fonts = networkLog.filter(n => n.contentType.includes('font'));

    checks.third_party_trustindex = {
      status: trustindex.length > 0 ? 'PASS' : 'N/A',
      detail: trustindex.length > 0
        ? `Trustindex loaded (${trustindex.length} requests)`
        : 'No Trustindex detected',
    };
    checks.third_party_easypiechart = {
      status: hasEasypie ? 'FAIL' : 'PASS',
      detail: hasEasypie ? 'easypiechart.js still loading' : 'No easypiechart.js detected',
    };
    checks.third_party_scripts = {
      status: scripts.length <= 10 ? 'PASS' : 'WARN',
      detail: `${scripts.length} external JS files loaded`,
    };
    checks.third_party_fonts = {
      status: fonts.length <= 8 ? 'PASS' : 'WARN',
      detail: `${fonts.length} font files loaded`,
    };

    // ─── ENVIRONMENT INFO ─────────────────────────────────
    const envInfo = await page.evaluate(() => {
      return {
        userAgent: navigator.userAgent,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        devicePixelRatio: window.devicePixelRatio,
      };
    });

    results.environment[vp.name] = envInfo;
    results.automated[vp.name] = checks;

    // ─── STICKY MENU CHECK (rendered) ─────────────────────
    const stickyCheck = await page.evaluate(() => {
      const all = document.querySelectorAll('*');
      for (const el of all) {
        const style = window.getComputedStyle(el);
        if (style.position === 'fixed' || style.position === 'sticky') {
          const rect = el.getBoundingClientRect();
          if (rect.top === 0 && rect.width > 200 && rect.height > 30) {
            return {
              found: true,
              tag: el.tagName,
              position: style.position,
              height: rect.height,
              visible: style.display !== 'none' && style.visibility !== 'visible' && parseFloat(style.opacity) > 0,
            };
          }
        }
      }
      return { found: false };
    });
    checks.sticky_menu = {
      status: stickyCheck.found ? 'PASS' : 'WARN',
      detail: stickyCheck.found
        ? `Sticky menu detected: ${stickyCheck.tag} (${stickyCheck.position}, ${stickyCheck.height}px)`
        : 'No sticky/fixed header detected at top of page',
    };

    console.log(`  Console errors: ${checks.console_errors.count}`);
    console.log(`  Images: ${renderedImages.length} total, ${brokenCount} broken, ${missingAlt} missing alt`);
    console.log(`  WP Rocket Critical CSS: ${wpRocketCheck.critical_css}`);
    console.log(`  WP Rocket Delay JS: ${wpRocketCheck.delay_js}`);
    console.log(`  SEO Title: ${seoCheck.title || '(none)'}`);
    console.log(`  SEO H1: ${seoCheck.h1 || '(none)'}`);
    console.log(`  Sticky Menu: ${stickyCheck.found ? 'YES' : 'Not detected'}`);
    console.log(`  Scripts: ${scripts.length}, Fonts: ${fonts.length}`);

    await context.close();
  }

  await browser.close();

  // ─── COMPUTE OVERALL ────────────────────────────────────
  const allStatuses = [];
  for (const [vpName, checks] of Object.entries(results.automated)) {
    for (const [checkName, check] of Object.entries(checks)) {
      allStatuses.push({ viewport: vpName, check: checkName, ...check });
    }
  }

  const failCount = allStatuses.filter(s => s.status === 'FAIL').length;
  const warnCount = allStatuses.filter(s => s.status === 'WARN').length;
  const passCount = allStatuses.filter(s => s.status === 'PASS').length;
  const naCount = allStatuses.filter(s => s.status === 'N/A').length;

  results.summary = {
    total: allStatuses.length,
    pass: passCount,
    fail: failCount,
    warn: warnCount,
    na: naCount,
    overall: failCount > 0 ? 'FAIL' : warnCount > 0 ? 'WARN' : 'PASS',
  };

  // ─── GENERATE HTML REPORT ───────────────────────────────
  const reportHtml = generateReport(results, outputDir);
  const jsonPath = resolve(outputDir, 'report.json');
  writeFileSync(jsonPath, JSON.stringify(results, null, 2));

  console.log(`\n${'='.repeat(60)}`);
  console.log(`QA FULL REPORT`);
  console.log(`${'='.repeat(60)}`);
  console.log(`URL: ${url}`);
  console.log(`Viewports: ${VIEWPORTS.map(v => v.name).join(', ')}`);
  console.log(`\nResults: ${results.summary.pass} PASS / ${results.summary.fail} FAIL / ${results.summary.warn} WARN / ${results.summary.na} N/A`);
  console.log(`\nOverall: ${results.summary.overall}`);
  console.log(`\nReport: ${reportHtml}`);
  console.log(`JSON: ${jsonPath}`);
  console.log(`${'='.repeat(60)}\n`);

  return results;
}

// ─── HELPERS ──────────────────────────────────────────────

async function autoScroll(page) {
  try {
    const scrollHeight = await page.evaluate(() => document.body.scrollHeight);
    if (!scrollHeight) return;
    const steps = Math.max(3, Math.min(8, Math.ceil(scrollHeight / 1000)));
    for (let i = 1; i <= steps; i++) {
      await page.evaluate((y) => window.scrollTo(0, y), Math.round((scrollHeight / steps) * i));
      await page.waitForTimeout(400);
    }
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);
  } catch (e) {}
}

function escapeHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function generateReport(results, outputDir) {
  const reportPath = resolve(outputDir, 'report.html');

  let tableRows = '';
  const failChecks = [];

  for (const [vpName, checks] of Object.entries(results.automated)) {
    for (const [checkName, check] of Object.entries(checks)) {
      const rowClass = check.status === 'FAIL' ? 'fail-row' : check.status === 'WARN' ? 'warn-row' : '';
      tableRows += `<tr class="${rowClass}">
        <td>${escapeHtml(vpName)}</td>
        <td>${escapeHtml(checkName)}</td>
        <td><span class="badge badge-${check.status.toLowerCase()}">${check.status}</span></td>
        <td>${escapeHtml(check.detail || '')}</td>
      </tr>`;
      if (check.status === 'FAIL') {
        failChecks.push({ viewport: vpName, check: checkName, detail: check.detail });
      }
    }
  }

  const screenshotEntries = VIEWPORTS.map(vp => {
    const path = `screenshots/${vp.name.toLowerCase()}-fullpage.png`;
    return `<div class="ss-card">
      <div class="ss-label">${vp.name} (${vp.width}x${vp.height})</div>
      <a href="${path}" target="_blank"><img src="${path}" loading="lazy"></a>
    </div>`;
  }).join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QA Full Report — ${escapeHtml(results.url)}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:24px}
.container{max-width:1200px;margin:0 auto}
h1{font-size:22px;margin-bottom:4px}
.url{color:#94a3b8;font-size:13px;word-break:break-all;margin-bottom:20px}
h2{font-size:16px;margin:20px 0 10px;color:#38bdf8}
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:20px}
.stat-card{background:#1e293b;border-radius:8px;padding:14px;text-align:center;border:1px solid #334155}
.stat-card .num{font-size:26px;font-weight:700}
.stat-card .label{font-size:11px;color:#94a3b8;margin-top:4px}
.overall{text-align:center;padding:16px;border-radius:8px;margin-bottom:20px;font-size:20px;font-weight:700}
.overall.PASS{background:#166534;color:#86efac}
.overall.FAIL{background:#7f1d1d;color:#fca5a5}
.overall.WARN{background:#854d0e;color:#fde047}
.screenshots{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin-bottom:25px}
.ss-card{background:#1e293b;border-radius:8px;padding:8px;border:1px solid #334155}
.ss-card img{width:100%;border-radius:4px;display:block}
.ss-label{font-size:11px;color:#94a3b8;margin-bottom:4px}
table{width:100%;border-collapse:collapse;background:#1e293b;border-radius:8px;overflow:hidden;font-size:12px}
th{background:#334155;color:#94a3b8;padding:8px;text-align:left;font-weight:600}
td{padding:6px 8px;border-bottom:1px solid #1e293b;vertical-align:top}
tr:hover{background:rgba(255,255,255,0.03)}
.fail-row{background:rgba(239,68,68,0.08)}
.warn-row{background:rgba(234,179,8,0.08)}
.badge{display:inline-block;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600}
.badge-pass{background:#166534;color:#86efac}
.badge-fail{background:#7f1d1d;color:#fca5a5}
.badge-warn{background:#854d0e;color:#fde047}
.badge-n/a{background:#334155;color:#94a3b8}
code{background:#0f172a;padding:1px 4px;border-radius:3px;font-size:11px}
.fail-list{list-style:none;padding:0}
.fail-list li{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:6px;padding:8px 12px;margin-bottom:6px;font-size:12px}
.fail-list li strong{color:#fca5a5}
.table-wrap{overflow-x:auto}
.tabs{display:flex;gap:2px;margin-bottom:12px;flex-wrap:wrap}
.tabs button{padding:6px 14px;border:1px solid #334155;background:#1e293b;color:#94a3b8;border-radius:5px 5px 0 0;cursor:pointer;font-size:12px}
.tabs button.active{background:#38bdf8;color:#0f172a;border-color:#38bdf8;font-weight:600}
.tab-content{display:none}
.tab-content.active{display:block}
</style>
</head>
<body>
<div class="container">
<h1>QA Full Report — Playwright</h1>
<div class="url">${escapeHtml(results.url)} | ${results.timestamp} | 3 viewports</div>

<div class="overall ${results.summary.overall}">${results.summary.overall}</div>

<div class="summary">
  <div class="stat-card"><div class="num" style="color:#38bdf8">${results.summary.total}</div><div class="label">Total Checks</div></div>
  <div class="stat-card"><div class="num" style="color:#86efac">${results.summary.pass}</div><div class="label">PASS</div></div>
  <div class="stat-card"><div class="num" style="color:#fca5a5">${results.summary.fail}</div><div class="label">FAIL</div></div>
  <div class="stat-card"><div class="num" style="color:#fde047">${results.summary.warn}</div><div class="label">WARN</div></div>
</div>

${failChecks.length > 0 ? `<h2>FAIL Items (${failChecks.length})</h2>
<ul class="fail-list">${failChecks.map(f => `<li><strong>[${f.viewport}]</strong> ${f.check}: ${escapeHtml(f.detail)}</li>`).join('')}</ul>` : ''}

<h2>Screenshots (Full Page)</h2>
<div class="screenshots">${screenshotEntries}</div>

<div class="tabs">
  <button class="active" onclick="switchTab('all',this)">All Checks</button>
  <button onclick="switchTab('fail',this)">FAIL Only</button>
  <button onclick="switchTab('warn',this)">WARN Only</button>
</div>

<div id="tab-all" class="tab-content active">
<div class="table-wrap">
<table>
<thead><tr><th>Viewport</th><th>Check</th><th>Status</th><th>Detail</th></tr></thead>
<tbody>${tableRows}</tbody>
</table>
</div>
</div>

<div id="tab-fail" class="tab-content">
<div class="table-wrap">
<table>
<thead><tr><th>Viewport</th><th>Check</th><th>Status</th><th>Detail</th></tr></thead>
<tbody>${tableRows.replace(/<tr class="(?!.*fail-row)[^"]*">/g, '<tr style="display:none">')}</tbody>
</table>
</div>
</div>

<div id="tab-warn" class="tab-content">
<div class="table-wrap">
<table>
<thead><tr><th>Viewport</th><th>Check</th><th>Status</th><th>Detail</th></tr></thead>
<tbody>${tableRows.replace(/<tr class="(?!.*warn-row)[^"]*">/g, '<tr style="display:none">')}</tbody>
</table>
</div>
</div>

</div>

<script>
function switchTab(t,btn){
document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));
btn.classList.add('active');
document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
document.getElementById('tab-'+t).classList.add('active');
}
</script>
</body>
</html>`;

  writeFileSync(reportPath, html);
  return reportPath;
}

// ─── CLI ──────────────────────────────────────────────────

async function main() {
  const url = process.argv[2];
  if (!url) {
    console.log(`\nUsage: node qa-full-playwright.js <url>`);
    console.log(`\nExamples:`);
    console.log(`  node qa-full-playwright.js https://basespawellness.com`);
    console.log(`  node qa-full-playwright.js drreichner.com/plastic-surgery`);
    console.log(`\nNote: You can pass just a domain, it will auto-add https://\n`);
    process.exit(1);
  }

  const fullUrl = url.match(/^https?:\/\//) ? url : `https://${url}`;
  await runAllChecks(fullUrl);
}

main().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});