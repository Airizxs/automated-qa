import { chromium } from 'playwright';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, dirname, basename, extname } from 'path';
import { fileURLToPath } from 'url';
import readline from 'readline';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─────────────────────────────────────────────────────────────────────────────
// CONFIGURATION
// ─────────────────────────────────────────────────────────────────────────────
// Ilagay mo dito yung URL na gusto mong i-check.
// Pwede mong i-override sa command line: node broken-images-checker.js https://example.com
const DEFAULT_URL = '';

const VIEWPORTS = [
  { name: 'Mobile', width: 375, height: 812, mobile: true },
  { name: 'Tablet', width: 768, height: 1024, mobile: false },
  { name: 'Desktop', width: 1280, height: 800, mobile: false },
];

const REQUEST_TIMEOUT = 10000;
const PAGE_LOAD_TIMEOUT = 30000;
const SCROLL_DELAY = 600;
const VIEWPORT_SCREENSHOT_HEIGHT = 4000;

const IMAGE_EXTENSIONS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.avif', '.bmp', '.ico', '.tiff',
]);

// ─────────────────────────────────────────────────────────────────────────────
// UTILITY FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

function getUA(mobile) {
  return mobile
    ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0';
}

function normalizeUrl(src, baseUrl) {
  if (!src) return null;
  try {
    return new URL(src, baseUrl).href;
  } catch {
    return null;
  }
}

function getResourceType(href) {
  if (!href) return 'unknown';
  const ext = extname(new URL(href, 'http://example.com/').pathname).toLowerCase();
  if (ext === '.svg') return 'svg';
  if (['.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.bmp', '.ico', '.tiff'].includes(ext)) return 'raster';
  return 'other';
}

function truncate(str, len = 80) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '…' : str;
}

function slug(str) {
  return String(str).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// ─────────────────────────────────────────────────────────────────────────────
// DOM COLLECTION FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

async function collectImagesFromDOM(page, baseUrl) {
  return await page.evaluate(({ baseUrl }) => {
    const results = [];
    const seen = new Set();
    let idx = 0;

    function mark(el, data) {
      const id = `bic-${idx}`;
      el.setAttribute('data-bic-id', id);
      results.push({ ...data, id, idx });
      idx++;
    }

    // 1. Standard <img> elements
    document.querySelectorAll('img').forEach((img) => {
      const rect = img.getBoundingClientRect();
      const styles = window.getComputedStyle(img);
      const src = img.currentSrc || img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || img.getAttribute('data-original');

      mark(img, {
        type: 'img',
        tag: 'img',
        src,
        resolvedSrc: src,
        alt: img.alt || '',
        width: img.width,
        height: img.height,
        naturalWidth: img.naturalWidth || 0,
        naturalHeight: img.naturalHeight || 0,
        visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none' && styles.visibility !== 'hidden',
        rect: {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        },
        classes: img.className || '',
        id_attr: img.id || '',
        loading: img.getAttribute('loading') || '',
        decoding: img.getAttribute('decoding') || '',
        srcset: img.getAttribute('srcset') || img.getAttribute('data-srcset') || '',
        dataSrc: img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || img.getAttribute('data-original') || '',
      });
    });

    // 2. <picture> / <source> elements
    document.querySelectorAll('picture source').forEach((src) => {
      const sourceSrc = src.srcset || src.src || '';
      const firstCandidate = sourceSrc.split(',')[0]?.trim().split(' ')[0];
      if (!firstCandidate || seen.has(firstCandidate)) return;
      seen.add(firstCandidate);

      mark(src, {
        type: 'source',
        tag: 'picture>source',
        src: firstCandidate,
        resolvedSrc: firstCandidate,
        alt: '',
        width: 0,
        height: 0,
        naturalWidth: 0,
        naturalHeight: 0,
        visible: false,
        rect: { x: 0, y: 0, width: 0, height: 0 },
        classes: src.className || '',
        id_attr: src.id || '',
        loading: '',
        decoding: '',
        srcset: sourceSrc,
        dataSrc: '',
      });
    });

    // 3. CSS background-images
    const all = document.querySelectorAll('*');
    for (const el of all) {
      const styles = window.getComputedStyle(el);
      const bg = styles.backgroundImage;
      if (!bg || bg === 'none') continue;

      const matches = bg.matchAll(/url\(["']?([^"')]+)["']?\)/g);
      for (const m of matches) {
        const url = m[1];
        if (seen.has(url)) continue;
        seen.add(url);
        const rect = el.getBoundingClientRect();
        mark(el, {
          type: 'css-background',
          tag: el.tagName.toLowerCase(),
          src: url,
          resolvedSrc: url,
          alt: '',
          width: 0,
          height: 0,
          naturalWidth: 0,
          naturalHeight: 0,
          visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none' && styles.visibility !== 'hidden',
          rect: {
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
          },
          classes: el.className || '',
          id_attr: el.id || '',
          loading: '',
          decoding: '',
          srcset: '',
          dataSrc: '',
        });
      }
    }

    // 4. Inline SVGs (just for reporting completeness)
    document.querySelectorAll('svg').forEach((svg) => {
      const rect = svg.getBoundingClientRect();
      mark(svg, {
        type: 'inline-svg',
        tag: 'svg',
        src: '(inline SVG)',
        resolvedSrc: '',
        alt: svg.getAttribute('aria-label') || svg.getAttribute('title') || '',
        width: rect.width,
        height: rect.height,
        naturalWidth: 0,
        naturalHeight: 0,
        visible: rect.width > 0 && rect.height > 0,
        rect: {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        },
        classes: svg.className || '',
        id_attr: svg.id || '',
        loading: '',
        decoding: '',
        srcset: '',
        dataSrc: '',
      });
    });

    return results;
  }, { baseUrl });
}

// ─────────────────────────────────────────────────────────────────────────────
// NETWORK / HTTP STATUS CHECK FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

async function createNetworkMonitor(page) {
  const statuses = new Map();

  page.on('response', (response) => {
    const url = response.url();
    const req = response.request();
    if (req.resourceType() === 'image' || getResourceType(url) !== 'other') {
      statuses.set(url, {
        status: response.status(),
        statusText: response.statusText(),
        contentType: response.headers()['content-type'] || '',
        size: response.headers()['content-length'] || 'unknown',
      });
    }
  });

  page.on('requestfailed', (request) => {
    const url = request.url();
    if (request.resourceType() === 'image' || getResourceType(url) !== 'other') {
      statuses.set(url, {
        status: 0,
        statusText: request.failure()?.errorText || 'failed',
        contentType: '',
        size: 0,
      });
    }
  });

  return {
    getStatus: (url) => statuses.get(url),
    async probeUrl(url) {
      if (statuses.has(url)) return statuses.get(url);
      try {
        const response = await page.request.get(url, { timeout: REQUEST_TIMEOUT });
        const info = {
          status: response.status(),
          statusText: response.statusText(),
          contentType: response.headers()['content-type'] || '',
          size: response.headers()['content-length'] || 'unknown',
        };
        statuses.set(url, info);
        return info;
      } catch (err) {
        const info = { status: 0, statusText: err.message || 'probe-failed', contentType: '', size: 0 };
        statuses.set(url, info);
        return info;
      }
    },
  };
}

async function resolveLazyLoadedImages(page, images, baseUrl) {
  // Try to force lazy images to load by scrolling and removing loading="lazy"
  await page.evaluate(() => {
    document.querySelectorAll('img[loading="lazy"]').forEach((img) => {
      img.setAttribute('data-bic-was-lazy', 'true');
      img.removeAttribute('loading');
    });
    document.querySelectorAll('img[data-src], img[data-lazy-src], img[data-original]').forEach((img) => {
      const src = img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || img.getAttribute('data-original');
      if (src && !img.src) img.src = src;
    });
  });

  // Wait a bit for lazy images to start loading
  await page.waitForTimeout(1500);

  // Re-collect to get currentSrc / naturalWidth after lazy load
  const refreshed = await collectImagesFromDOM(page, baseUrl);
  const map = new Map();
  for (const img of refreshed) {
    if (img.type === 'img') {
      map.set(img.id || `${img.tag}-${img.idx}`, img);
    }
  }

  return images.map((img) => {
    if (img.type !== 'img') return img;
    const updated = map.get(img.id);
    return updated
      ? { ...img, resolvedSrc: updated.resolvedSrc || updated.src, naturalWidth: updated.naturalWidth, naturalHeight: updated.naturalHeight }
      : img;
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// CLASSIFICATION / ANALYSIS FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

function classifyImage(img, status, baseUrl) {
  const issues = [];
  const warnings = [];

  // Missing source
  if (!img.src && !img.resolvedSrc && !img.dataSrc) {
    issues.push('missing-src');
  }

  // Network-level broken
  if (status) {
    if (status.status === 0) issues.push('network-failure');
    else if (status.status >= 400) issues.push(`http-${status.status}`);
    else if (status.status >= 300) warnings.push(`redirect-${status.status}`);
  }

  // Zero natural size for raster <img>
  if (img.type === 'img' && getResourceType(img.resolvedSrc || img.src) === 'raster') {
    if (img.naturalWidth === 0 || img.naturalHeight === 0) {
      issues.push('zero-natural-size');
    }
  }

  // SVG-specific: very small or network fail
  if (getResourceType(img.resolvedSrc || img.src) === 'svg') {
    if (status && status.status >= 400) issues.push('svg-broken');
  }

  // Lazy load with data-src still present and src empty/missing
  if (img.dataSrc && (!img.src || img.src === windowLocationOrigin(baseUrl))) {
    warnings.push('lazy-not-loaded');
  }

  // Alt text missing on visible content images
  if (img.type === 'img' && img.visible && !img.alt && !isDecorative(img)) {
    warnings.push('missing-alt');
  }

  // Oversized download compared to rendered size (basic heuristic)
  if (img.type === 'img' && img.naturalWidth > 0 && img.rect.width > 0) {
    const ratio = img.naturalWidth / img.rect.width;
    if (ratio > 3) warnings.push('oversized-asset');
  }

  const isBroken = issues.length > 0;
  const severity = isBroken ? 'broken' : warnings.length > 0 ? 'warning' : 'ok';

  return { issues, warnings, severity, isBroken };
}

function windowLocationOrigin(baseUrl) {
  try {
    return new URL(baseUrl).origin;
  } catch {
    return '';
  }
}

function isDecorative(img) {
  const cls = (img.classes || '').toLowerCase();
  return cls.includes('decorative') || cls.includes('icon') || cls.includes('logo') || cls.includes('avatar');
}

function summarize(results) {
  let total = 0;
  let broken = 0;
  let warnings = 0;
  let ok = 0;
  const issueTypes = {};
  const byViewport = {};

  for (const [vp, data] of Object.entries(results)) {
    const vpTotal = data.images.length;
    const vpBroken = data.images.filter((i) => i.severity === 'broken').length;
    const vpWarn = data.images.filter((i) => i.severity === 'warning').length;
    const vpOk = data.images.filter((i) => i.severity === 'ok').length;
    total += vpTotal;
    broken += vpBroken;
    warnings += vpWarn;
    ok += vpOk;
    byViewport[vp] = { total: vpTotal, broken: vpBroken, warnings: vpWarn, ok: vpOk };

    for (const img of data.images) {
      for (const issue of img.issues) {
        issueTypes[issue] = (issueTypes[issue] || 0) + 1;
      }
    }
  }

  return { total, broken, warnings, ok, issueTypes, byViewport };
}

// ─────────────────────────────────────────────────────────────────────────────
// SCREENSHOT / EVIDENCE FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

async function highlightBrokenOnPage(page, brokenImages) {
  await page.evaluate((broken) => {
    broken.forEach(({ id, issues }) => {
      const el = document.querySelector(`[data-bic-id="${id}"]`);
      if (!el) return;
      el.style.outline = '4px dashed #ef4444 !important';
      el.style.outlineOffset = '2px !important';
      el.style.background = 'rgba(239,68,68,0.15) !important';
      el.style.position = 'relative';

      const badge = document.createElement('div');
      badge.textContent = 'BROKEN: ' + issues.join(', ');
      badge.style.cssText =
        'position:absolute;top:0;left:0;background:#ef4444;color:#fff;font:11px sans-serif;padding:2px 6px;z-index:99999;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
      el.appendChild(badge);
    });
  }, brokenImages);
}

async function captureViewportScreenshot(page, viewportName, outputDir) {
  try {
    const path = resolve(outputDir, `screenshots/viewport-${slug(viewportName)}.png`);
    await page.screenshot({ path, fullPage: true });
    return path;
  } catch (err) {
    console.log(`      Screenshot error (${viewportName}): ${err.message}`);
    return null;
  }
}

async function captureImageScreenshots(page, images, viewportName, outputDir) {
  const captured = [];
  for (const img of images.filter((i) => i.visible)) {
    try {
      if (img.rect.width < 5 || img.rect.height < 5) continue;
      const el = page.locator(`[data-bic-id="${img.id}"]`).first();
      if (!(await el.isVisible({ timeout: 500 }).catch(() => false))) continue;

      const fileName = `img-${slug(viewportName)}-${img.idx}.png`;
      const path = resolve(outputDir, 'screenshots', fileName);
      await el.screenshot({ path });
      captured.push({ idx: img.idx, path: `screenshots/${fileName}` });
    } catch {
      // ignore per-element screenshot failures
    }
  }
  return captured;
}

// ─────────────────────────────────────────────────────────────────────────────
// REPORT GENERATION FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function severityBadge(severity, issues, warnings) {
  if (severity === 'broken') {
    return `<span class="badge badge-bad">Broken</span> <small>${escapeHtml(issues.join(', '))}</small>`;
  }
  if (severity === 'warning') {
    return `<span class="badge badge-warn">Warning</span> <small>${escapeHtml(warnings.join(', '))}</small>`;
  }
  return `<span class="badge badge-good">OK</span>`;
}

function generateHTMLReport(results, url, outputDir) {
  const reportPath = resolve(outputDir, 'report.html');
  const summary = summarize(results);

  let tableRows = '';
  let brokenGallery = '';
  let allGallery = '';

  for (const [viewportName, data] of Object.entries(results)) {
    for (const img of data.images) {
      const srcDisplay = truncate(img.resolvedSrc || img.src || img.dataSrc || '(none)', 90);
      const typeLabel = img.type === 'img' ? 'IMG' : img.type === 'source' ? 'SOURCE' : img.type === 'css-background' ? 'CSS BG' : 'INLINE SVG';
      const status = img.status ? `${img.status.status} ${img.status.statusText}` : '—';
      const size = img.status?.size ? img.status.size : `${img.naturalWidth}x${img.naturalHeight}`;

      tableRows += `<tr class="${img.severity}-row" data-viewport="${escapeHtml(viewportName)}" data-severity="${img.severity}">
        <td>${escapeHtml(viewportName)}</td>
        <td><code>${typeLabel}</code></td>
        <td><a href="${escapeHtml(img.resolvedSrc || img.src || '#')}" target="_blank">${escapeHtml(srcDisplay)}</a></td>
        <td>${escapeHtml(img.alt || '')}</td>
        <td>${escapeHtml(status)}</td>
        <td>${escapeHtml(String(size))}</td>
        <td>${img.rect.width}x${img.rect.height}</td>
        <td>${severityBadge(img.severity, img.issues, img.warnings)}</td>
      </tr>`;

      const screenshotPath = data.screenshots.find((s) => s.idx === img.idx)?.path;
      const card = `<div class="img-card ${img.severity}-card">
        <div class="img-label">${escapeHtml(viewportName)} — ${typeLabel}</div>
        ${screenshotPath ? `<img src="${screenshotPath}" loading="lazy" alt="">` : `<div class="no-thumb">no screenshot</div>`}
        <div class="img-meta">
          <div>${severityBadge(img.severity, img.issues, img.warnings)}</div>
          <div>${escapeHtml(srcDisplay)}</div>
          <div>${img.rect.width}x${img.rect.height} | ${escapeHtml(status)}</div>
        </div>
      </div>`;

      allGallery += card;
      if (img.severity === 'broken') brokenGallery += card;
    }
  }

  const viewportScreenshots = Object.entries(results)
    .map(([vp, data]) => {
      if (!data.viewportScreenshot) return '';
      return `<div class="img-card">
        <div class="img-label">${escapeHtml(vp)} — Full page with broken highlights</div>
        <a href="${data.viewportScreenshot}" target="_blank"><img src="${data.viewportScreenshot}" loading="lazy" alt=""></a>
      </div>`;
    })
    .join('');

  const issueTypeHtml = Object.entries(summary.issueTypes)
    .sort((a, b) => b[1] - a[1])
    .map(([issue, count]) => `<div class="stat-card"><div class="num" style="color:#fca5a5">${count}</div><div class="label">${escapeHtml(issue)}</div></div>`)
    .join('');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Broken Images Checker Report</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}
.container{max-width:1400px;margin:0 auto}
h1{font-size:24px;margin-bottom:5px}
.url{color:#94a3b8;font-size:14px;word-break:break-all;margin-bottom:20px}
h2{font-size:18px;margin:25px 0 10px;color:#38bdf8}
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:15px;margin-bottom:25px}
.stat-card{background:#1e293b;border-radius:8px;padding:15px;text-align:center;border:1px solid #334155}
.stat-card .num{font-size:28px;font-weight:700}
.stat-card .label{font-size:12px;color:#94a3b8;margin-top:4px;text-transform:capitalize}
.tabs{display:flex;gap:2px;margin-bottom:15px;flex-wrap:wrap}
.tabs button{padding:8px 18px;border:1px solid #334155;background:#1e293b;color:#94a3b8;border-radius:6px 6px 0 0;cursor:pointer;font-size:14px}
.tabs button.active{background:#38bdf8;color:#0f172a;border-color:#38bdf8;font-weight:600}
.tab-content{display:none}
.tab-content.active{display:block}
.img-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-bottom:30px}
.img-card{background:#1e293b;border-radius:8px;padding:10px;border:1px solid #334155;overflow:hidden}
.img-card img{width:100%;border-radius:4px;display:block;background:#0f172a;min-height:80px}
.no-thumb{min-height:80px;background:#0f172a;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#64748b;font-size:12px}
.img-label{font-size:12px;color:#94a3b8;margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.img-meta{font-size:11px;color:#64748b;margin-top:6px;line-height:1.5}
.broken-card{border-color:#ef4444}
.warn-card{border-color:#eab308}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;background:#1e293b;border-radius:8px;overflow:hidden;font-size:13px}
th{background:#334155;color:#94a3b8;padding:10px 8px;text-align:left;font-weight:600;position:sticky;top:0}
td{padding:8px;border-bottom:1px solid #1e293b;vertical-align:top}
tr:hover{background:rgba(255,255,255,0.03)}
.broken-row{background:rgba(239,68,68,0.08)}
.warn-row{background:rgba(234,179,8,0.08)}
code{background:#0f172a;padding:1px 5px;border-radius:3px;font-size:12px}
a{color:#38bdf8;text-decoration:none}
a:hover{text-decoration:underline}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600}
.badge-good{background:#166534;color:#86efac}
.badge-warn{background:#854d0e;color:#fde047}
.badge-bad{background:#7f1d1d;color:#fca5a5}
.filters{margin:15px 0;display:flex;gap:8px;flex-wrap:wrap}
.filters button{padding:6px 14px;border:1px solid #334155;background:#1e293b;color:#e2e8f0;border-radius:6px;cursor:pointer;font-size:13px}
.filters button.active{background:#38bdf8;color:#0f172a;border-color:#38bdf8;font-weight:600}
.viewports{margin-bottom:25px}
.legend{font-size:12px;color:#94a3b8;margin-top:10px}
</style>
</head>
<body>
<div class="container">
<h1>Broken Images Checker</h1>
<div class="url">${escapeHtml(url)}</div>

<div class="summary">
  <div class="stat-card"><div class="num" style="color:#38bdf8">${summary.total}</div><div class="label">Total Images</div></div>
  <div class="stat-card"><div class="num" style="color:#86efac">${summary.ok}</div><div class="label">OK</div></div>
  <div class="stat-card"><div class="num" style="color:#fde047">${summary.warnings}</div><div class="label">Warnings</div></div>
  <div class="stat-card"><div class="num" style="color:#fca5a5">${summary.broken}</div><div class="label">Broken</div></div>
</div>

${issueTypeHtml ? `<h2>Issue Breakdown</h2><div class="summary">${issueTypeHtml}</div>` : ''}

<div class="tabs">
  <button class="active" onclick="switchTab('broken',this)">Broken (${summary.broken})</button>
  <button onclick="switchTab('all',this)">All Images (${summary.total})</button>
  <button onclick="switchTab('viewports',this)">Viewport Evidence</button>
  <button onclick="switchTab('table',this)">Data Table</button>
</div>

<div id="tab-broken" class="tab-content active">
  <h2>Broken Images</h2>
  <div class="img-grid">
    ${brokenGallery || '<p style="color:#94a3b8">No broken images detected.</p>'}
  </div>
</div>

<div id="tab-all" class="tab-content">
  <h2>All Images</h2>
  <div class="img-grid">
    ${allGallery || '<p style="color:#94a3b8">No images found.</p>'}
  </div>
</div>

<div id="tab-viewports" class="tab-content">
  <h2>Full-Page Screenshots with Broken Highlights</h2>
  <div class="img-grid">
    ${viewportScreenshots || '<p style="color:#94a3b8">No viewport screenshots available.</p>'}
  </div>
</div>

<div id="tab-table" class="tab-content">
  <h2>All Images Data</h2>
  <div class="filters">
    <button class="active" onclick="filter('all',this)">All</button>
    <button onclick="filter('broken',this)">Broken</button>
    <button onclick="filter('warning',this)">Warnings</button>
    <button onclick="filter('ok',this)">OK</button>
  </div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Viewport</th><th>Type</th><th>Source</th><th>Alt</th><th>HTTP</th><th>Size</th><th>Rendered</th><th>Status</th>
      </tr></thead>
      <tbody>${tableRows}</tbody>
    </table>
  </div>
</div>

<div class="legend">
  <strong>Legend:</strong>
  <span class="badge badge-good">OK</span> no issues detected &nbsp;
  <span class="badge badge-warn">Warning</span> potential issue &nbsp;
  <span class="badge badge-bad">Broken</span> failed to load
</div>

</div>

<script>
const rows = document.querySelectorAll('tbody tr');
function filter(f, btn){
  document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  rows.forEach(r => {
    if (f === 'all') r.style.display = '';
    else r.style.display = r.dataset.severity === f ? '' : 'none';
  });
}
function switchTab(t, btn){
  document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-' + t).classList.add('active');
}
</script>
</body>
</html>`;

  writeFileSync(reportPath, html);
  return reportPath;
}

function generateJSONReport(results, url, outputDir) {
  const jsonPath = resolve(outputDir, 'report.json');
  const summary = summarize(results);
  const payload = { url, generatedAt: new Date().toISOString(), summary, viewports: results };
  writeFileSync(jsonPath, JSON.stringify(payload, null, 2));
  return jsonPath;
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN ORCHESTRATION
// ─────────────────────────────────────────────────────────────────────────────

async function processViewport(browser, url, vp, outputDir) {
  console.log(`  ${vp.name} (${vp.width}x${vp.height})...`);

  const context = await browser.newContext({
    userAgent: getUA(vp.mobile),
    viewport: { width: vp.width, height: vp.height },
    isMobile: vp.mobile,
    hasTouch: vp.mobile,
    locale: 'en-US',
    deviceScaleFactor: vp.mobile ? 2 : 1,
  });

  const page = await context.newPage();
  const monitor = await createNetworkMonitor(page);

  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: PAGE_LOAD_TIMEOUT });
  } catch (err) {
    console.log(`    Page load warning: ${err.message}`);
  }

  // Wait for initial images / fonts / lazy scripts
  await page.waitForTimeout(2000);

  // Scroll to trigger lazy loading
  await autoScroll(page);

  // Collect and resolve lazy images
  let images = await collectImagesFromDOM(page, url);
  images = await resolveLazyLoadedImages(page, images, url);

  // Resolve absolute URLs
  images = images.map((img) => ({
    ...img,
    resolvedSrc: normalizeUrl(img.resolvedSrc || img.src, url) || img.resolvedSrc || img.src,
  }));

  // Probe statuses for external / non-intercepted URLs
  for (const img of images) {
    if (img.type === 'inline-svg') {
      img.status = { status: 200, statusText: 'inline', contentType: 'image/svg+xml', size: 0 };
      continue;
    }
    if (!img.resolvedSrc) {
      img.status = { status: 0, statusText: 'no-source', contentType: '', size: 0 };
      continue;
    }

    let status = monitor.getStatus(img.resolvedSrc);
    if (!status) {
      status = await monitor.probeUrl(img.resolvedSrc);
    }
    img.status = status;
  }

  // Classify each image
  images = images.map((img) => {
    const classification = classifyImage(img, img.status, url);
    return { ...img, ...classification };
  });

  const brokenImages = images.filter((i) => i.severity === 'broken');

  // Highlight broken images in DOM
  if (brokenImages.length > 0) {
    await highlightBrokenOnPage(page, brokenImages);
  }

  // Screenshots
  const viewportScreenshot = await captureViewportScreenshot(page, vp.name, outputDir);
  const screenshots = await captureImageScreenshots(page, images, vp.name, outputDir);

  const visible = images.filter((i) => i.visible).length;
  console.log(`    -> ${images.length} images (${visible} visible), ${brokenImages.length} broken, ${images.filter((i) => i.severity === 'warning').length} warnings`);

  await context.close();

  return {
    images,
    screenshots,
    viewportScreenshot,
    counts: {
      total: images.length,
      visible,
      broken: brokenImages.length,
      warnings: images.filter((i) => i.severity === 'warning').length,
      ok: images.filter((i) => i.severity === 'ok').length,
    },
  };
}

async function autoScroll(page) {
  try {
    const scrollHeight = await page.evaluate(() => document.body.scrollHeight);
    if (!scrollHeight) return;
    const steps = Math.max(3, Math.min(8, Math.ceil(scrollHeight / 1000)));
    for (let i = 1; i <= steps; i++) {
      await page.evaluate((y) => window.scrollTo(0, y), Math.round((scrollHeight / steps) * i));
      await page.waitForTimeout(SCROLL_DELAY);
    }
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(400);
  } catch (err) {
    console.log(`    Scroll warning: ${err.message}`);
  }
}

function askUrl() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question('Enter URL to check: ', (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

async function main() {
  let url = process.argv[2] || DEFAULT_URL;
  if (!url) {
    url = await askUrl();
  }
  if (!url) {
    console.log(`\nUsage: node broken-images-checker.js <url>\n`);
    console.log(`Example: node broken-images-checker.js https://example.com\n`);
    console.log(`Or set DEFAULT_URL at the top of this file.\n`);
    process.exit(1);
  }

  const outputDir = resolve(__dirname, 'reports', `broken-images-${Date.now()}`);
  mkdirSync(outputDir, { recursive: true });
  mkdirSync(resolve(outputDir, 'screenshots'), { recursive: true });

  console.log(`\nChecking images on: ${url}`);
  console.log(`Output: ${outputDir}\n`);

  const browser = await chromium.launch({ headless: true });
  const allResults = {};

  for (const vp of VIEWPORTS) {
    try {
      allResults[vp.name] = await processViewport(browser, url, vp, outputDir);
    } catch (err) {
      console.log(`    Error: ${err.message}`);
      allResults[vp.name] = { images: [], screenshots: [], viewportScreenshot: null, counts: { total: 0, visible: 0, broken: 0, warnings: 0, ok: 0 }, error: err.message };
    }
  }

  const htmlPath = generateHTMLReport(allResults, url, outputDir);
  const jsonPath = generateJSONReport(allResults, url, outputDir);
  const summary = summarize(allResults);

  console.log(`\nDone!`);
  console.log(`HTML Report: ${htmlPath}`);
  console.log(`JSON Report: ${jsonPath}`);
  console.log(`Summary: ${summary.total} images, ${summary.broken} broken, ${summary.warnings} warnings, ${summary.ok} OK\n`);

  await browser.close().catch(() => {});
}

main().catch((err) => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
