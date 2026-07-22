import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const VIEWPORTS = [
  { name: 'Mobile', width: 375, height: 812, mobile: true },
  { name: 'Tablet', width: 768, height: 1024, mobile: false },
  { name: 'Desktop', width: 1280, height: 800, mobile: false },
];

const BUTTON_SELECTORS = [
  'button:not([data-bc-ignore])',
  'a[role="button"]',
  'input[type="submit"]',
  'input[type="button"]',
  '[role="button"]',
  '.et_pb_button',
  'a.et_pb_button',
  '.dsm_button',
  'a.dsm_button',
  '.gform_button',
  'input[type="reset"]',
];

// Selectors for child elements that, if found inside a candidate, mean it is a wrapper.
const CHILD_BUTTON_SELECTORS = [
  'button',
  'a[role="button"]',
  'input[type="submit"]',
  'input[type="button"]',
  '[role="button"]',
  '.et_pb_button',
  'a.et_pb_button',
  '.dsm_button',
  'a.dsm_button',
  '.gform_button',
  'input[type="reset"]',
];

function getUA(mobile) {
  return mobile
    ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
}

async function getButtonInfo(page, isMobile) {
  const sels = isMobile ? BUTTON_SELECTORS : [...BUTTON_SELECTORS];
  return await page.evaluate(({ selectors, childSelectors }) => {
    let idx = 0;
    let groupIdx = 0;
    const allButtons = [];
    const allGroups = [];
    const seen = new Set();

    function getText(el) {
      if (el.tagName === 'INPUT') return el.value?.trim() || '';
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
      let out = '';
      let node;
      while ((node = walker.nextNode())) {
        const txt = node.textContent?.trim();
        if (txt) out += (out ? ' ' : '') + txt;
      }
      return out;
    }

    function collectButtons() {
      for (const sel of selectors) {
        const elements = document.querySelectorAll(sel);
        for (const el of elements) {
          if (seen.has(el)) continue;
          seen.add(el);

          const tag = el.tagName.toLowerCase();
          if (tag === 'div' || tag === 'span') {
            const hasChildButton = childSelectors.some(cs => el.querySelector(cs));
            if (hasChildButton) continue;
          }

          el.setAttribute('data-bc-id', String(idx));
          const rect = el.getBoundingClientRect();
          const text = getText(el);
          const styles = window.getComputedStyle(el);
          allButtons.push({
            tag: tag + (el.getAttribute('type') ? `[type="${el.getAttribute('type')}"]` : ''),
            text,
            visible: rect.width > 0 && rect.height > 0,
            rect: {
              x: Math.round(rect.x), y: Math.round(rect.y),
              width: Math.round(rect.width), height: Math.round(rect.height),
            },
            css: {
              display: styles.display, visibility: styles.visibility,
              opacity: styles.opacity, fontSize: styles.fontSize,
              color: styles.color, bgColor: styles.backgroundColor,
              borderRadius: styles.borderRadius,
              padding: `${styles.paddingTop} ${styles.paddingRight} ${styles.paddingBottom} ${styles.paddingLeft}`,
              fontWeight: styles.fontWeight, textAlign: styles.textAlign,
              border: `${styles.borderWidth} ${styles.borderStyle} ${styles.borderColor}`,
              cursor: styles.cursor,
            },
            classes: el.className || '',
            idx,
          });
          idx++;
        }
      }
    }

    function collectGroups() {
      // Find containers that hold multiple buttons (mobile stacked layouts).
      const groupCandidates = document.querySelectorAll([
        '.et_pb_button_module_wrapper',
        '.dsm_button',
        '[class*="button-module"]',
        '[class*="button_wrapper"]',
        '[class*="button-wrapper"]',
        '[class*="btn-group"]',
        '[class*="btngroup"]',
      ].join(', '));

      const groupSeen = new Set();
      for (const container of groupCandidates) {
        if (container.tagName.toLowerCase() === 'body') continue;
        const btns = Array.from(container.querySelectorAll('[data-bc-id]')).filter(b => {
          const r = b.getBoundingClientRect();
          return r.width > 0 && r.height > 0;
        });
        if (btns.length < 2) continue;
        if (groupSeen.has(container)) continue;
        groupSeen.add(container);

        const rect = container.getBoundingClientRect();
        const styles = window.getComputedStyle(container);
        container.setAttribute('data-bc-group-id', String(groupIdx));
        allGroups.push({
          idx: groupIdx,
          text: getText(container),
          count: btns.length,
          visible: rect.width > 0 && rect.height > 0,
          rect: {
            x: Math.round(rect.x), y: Math.round(rect.y),
            width: Math.round(rect.width), height: Math.round(rect.height),
          },
          css: {
            display: styles.display,
            flexDirection: styles.flexDirection,
          },
        });
        groupIdx++;
      }
    }

    collectButtons();
    collectGroups();
    return { buttons: allButtons, groups: allGroups };
  }, { selectors: sels, childSelectors: CHILD_BUTTON_SELECTORS });
}

function generateReport(allResults, url, outputDir) {
  const reportPath = resolve(outputDir, 'report.html');
  mkdirSync(resolve(outputDir, 'screenshots'), { recursive: true });

  let rows = '';
  let vsGallery = '';
  let groupGallery = '';

  for (const [viewportName, data] of Object.entries(allResults)) {
    const buttons = data.buttons || [];
    const groups = data.groups || [];

    buttons.forEach((btn) => {
      const isSmall = btn.rect.width < 38 || btn.rect.height < 38;
      const isHidden = !btn.visible || btn.css.display === 'none' || btn.css.visibility === 'hidden' || parseFloat(btn.css.opacity) === 0;
      const status = isHidden ? 'Hidden' : isSmall ? 'Small' : 'OK';

      let warn = '';
      if (btn.rect.width < 38) warn += ` w=${btn.rect.width}px`;
      if (btn.rect.height < 38) warn += ` h=${btn.rect.height}px`;

      rows += `<tr class="${isHidden ? 'hidden-row' : isSmall ? 'warn-row' : ''}">
        <td>${viewportName}</td>
        <td><code>${btn.tag}</code></td>
        <td>${btn.text || '<em>(empty)</em>'}</td>
        <td>${btn.rect.width}x${btn.rect.height}</td>
        <td><span class="badge badge-${isHidden ? 'bad' : isSmall ? 'warn' : 'good'}">${status}</span>${warn}</td>
        <td style="font-size:${btn.css.fontSize};color:${btn.css.color}">Aa</td>
        <td style="background:${btn.css.bgColor};border-radius:${btn.css.borderRadius};padding:2px 8px;color:transparent">..</td>
      </tr>`;

      if (btn.visible && !isHidden) {
        const ss = `screenshots/btn-${viewportName.toLowerCase()}-${btn.idx}.png`;
        vsGallery += `<div class="btn-card">
          <div class="btn-label">${viewportName} — ${btn.text || '(no text)'}</div>
          <img src="${ss}" alt="${btn.text}" loading="lazy">
          <div class="btn-meta">${btn.rect.width}x${btn.rect.height} | ${btn.css.fontSize} | ${btn.tag}</div>
        </div>`;
      }
    });

    groups.forEach((grp) => {
      if (!grp.visible) return;
      const ss = `screenshots/group-${viewportName.toLowerCase()}-${grp.idx}.png`;
      groupGallery += `<div class="btn-card">
        <div class="btn-label">${viewportName} Group — ${grp.count} buttons ${grp.css.flexDirection ? `(${grp.css.flexDirection})` : ''}</div>
        <img src="${ss}" alt="${grp.text}" loading="lazy">
        <div class="btn-meta">${grp.rect.width}x${grp.rect.height} | ${grp.text.substring(0, 40) || 'button group'}</div>
      </div>`;
    });
  }

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Button Checker Report</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}
.container{max-width:1200px;margin:0 auto}
h1{font-size:24px;margin-bottom:5px}
.url{color:#94a3b8;font-size:14px;word-break:break-all;margin-bottom:20px}
h2{font-size:18px;margin:20px 0 10px;color:#38bdf8}
.btn-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:30px}
.btn-card{background:#1e293b;border-radius:8px;padding:10px;border:1px solid #334155;overflow:hidden}
.btn-card img{width:100%;border-radius:4px;display:block}
.btn-label{font-size:12px;color:#94a3b8;margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.btn-meta{font-size:11px;color:#64748b;margin-top:4px}
table{width:100%;border-collapse:collapse;background:#1e293b;border-radius:8px;overflow:hidden;font-size:13px}
th{background:#334155;color:#94a3b8;padding:10px 8px;text-align:left;font-weight:600;position:sticky;top:0}
td{padding:8px;border-bottom:1px solid #1e293b}
tr:hover{background:rgba(255,255,255,0.03)}
.warn-row{background:rgba(234,179,8,0.08)}
.hidden-row{background:rgba(239,68,68,0.08)}
code{background:#0f172a;padding:1px 5px;border-radius:3px;font-size:12px}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600}
.badge-good{background:#166534;color:#86efac}
.badge-warn{background:#854d0e;color:#fde047}
.badge-bad{background:#7f1d1d;color:#fca5a5}
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:25px}
.stat-card{background:#1e293b;border-radius:8px;padding:15px;text-align:center;border:1px solid #334155}
.stat-card .num{font-size:28px;font-weight:700}
.stat-card .label{font-size:12px;color:#94a3b8;margin-top:4px}
.filters{margin:15px 0;display:flex;gap:8px;flex-wrap:wrap}
.filters button{padding:6px 14px;border:1px solid #334155;background:#1e293b;color:#e2e8f0;border-radius:6px;cursor:pointer;font-size:13px}
.filters button.active{background:#38bdf8;color:#0f172a;border-color:#38bdf8;font-weight:600}
.table-wrap{overflow-x:auto}
.tabs{display:flex;gap:2px;margin-bottom:15px}
.tabs button{padding:8px 18px;border:1px solid #334155;background:#1e293b;color:#94a3b8;border-radius:6px 6px 0 0;cursor:pointer;font-size:14px}
.tabs button.active{background:#38bdf8;color:#0f172a;border-color:#38bdf8;font-weight:600}
.tab-content{display:none}
.tab-content.active{display:block}
</style>
</head>
<body>
<div class="container">
<h1>Button Checker</h1>
<div class="url">${url}</div>

<div class="summary" id="summary"></div>

<div class="tabs">
<button class="active" onclick="switchTab('gallery',this)">Buttons</button>
<button onclick="switchTab('groups',this)">Button Groups</button>
<button onclick="switchTab('table',this)">Data Table</button>
</div>

<div id="tab-gallery" class="tab-content active">
<h2>Individual Button Screenshots</h2>
<div class="btn-grid">
${vsGallery || '<p style="color:#94a3b8">No visible buttons found</p>'}
</div>
</div>

<div id="tab-groups" class="tab-content">
<h2>Button Group Layouts (mobile stacked / side-by-side)</h2>
<div class="btn-grid">
${groupGallery || '<p style="color:#94a3b8">No button groups found</p>'}
</div>
</div>

<div id="tab-table" class="tab-content">
<h2>All Buttons</h2>
<div class="filters">
<button onclick="filter('all',this)">All</button>
<button class="active" onclick="filter('good',this)">OK Only</button>
<button onclick="filter('issue',this)">Issues</button>
</div>
<div class="table-wrap">
<table>
<thead><tr>
<th>Viewport</th><th>Tag</th><th>Text</th><th>Size</th><th>Status</th><th>Font</th><th>Bg</th>
</tr></thead>
<tbody>${rows}</tbody>
</table>
</div>
</div>

</div>

<script>
const rows=document.querySelectorAll('tbody tr');
function filter(f,btn){
document.querySelectorAll('.filters button').forEach(b=>b.classList.remove('active'));
btn.classList.add('active');
rows.forEach(r=>{
if(f==='all'){r.style.display=''}
else{const issue=r.classList.contains('warn-row')||r.classList.contains('hidden-row');
r.style.display=f==='issue'?(issue?'':'none'):(issue?'none':'')}
})}
function switchTab(t,btn){
document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('active'));
document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
btn.classList.add('active');
document.getElementById('tab-'+t).classList.add('active');
}
const t=rows.length,i=document.querySelectorAll('.warn-row,.hidden-row').length;
document.getElementById('summary').innerHTML=\`
<div class="stat-card"><div class="num" style="color:#38bdf8">\${t}</div><div class="label">Total Buttons</div></div>
<div class="stat-card"><div class="num" style="color:#86efac">\${t-i}</div><div class="label">OK</div></div>
<div class="stat-card"><div class="num" style="color:#fde047">\${i}</div><div class="label">Issues</div></div>\`;
</script>
</body>
</html>`;

  writeFileSync(reportPath, html);
  return reportPath;
}

async function main() {
  const url = process.argv[2];
  if (!url) {
    console.log(`\nUsage: node button-checker.js <url>\n`);
    process.exit(1);
  }

  const outputDir = resolve(__dirname, 'reports', `button-check-${Date.now()}`);
  mkdirSync(outputDir, { recursive: true });
  mkdirSync(resolve(outputDir, 'screenshots'), { recursive: true });
  mkdirSync(resolve(outputDir, 'videos'), { recursive: true });

  console.log(`\nChecking buttons on: ${url}`);
  console.log(`Output: ${outputDir}\n`);

  const browser = await chromium.launch({ headless: true });
  const allResults = {};

  for (const vp of VIEWPORTS) {
    console.log(`  ${vp.name} (${vp.width}x${vp.height})...`);
    let page;
    try {
      const context = await browser.newContext({
        userAgent: getUA(vp.mobile),
        viewport: { width: vp.width, height: vp.height },
        isMobile: vp.mobile,
        hasTouch: vp.mobile,
        locale: 'en-US',
        deviceScaleFactor: vp.mobile ? 2 : 1,
        recordVideo: { dir: resolve(outputDir, 'videos'), size: { width: 1280, height: 720 } },
      });
      page = await context.newPage();

      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
      await page.waitForTimeout(2000);
      await page.mouse.click(10, 10).catch(() => {});
      await page.waitForTimeout(500);

      // Try to open mobile hamburger menu (Divi / common WP themes)
      if (vp.mobile) {
        const menuToggles = [
          '.mobile_menu_bar',
          '.et_mobile_menu_button',
          '.menu-toggle',
          '.navbar-toggler',
          '.hamburger',
          '[aria-label="Menu"]',
          '[aria-label="Toggle menu"]',
          '.mobile-nav-toggle',
        ];
        for (const sel of menuToggles) {
          try {
            const toggle = page.locator(sel).first();
            if (await toggle.isVisible({ timeout: 500 })) {
              await toggle.click();
              await page.waitForTimeout(1200);
              break;
            }
          } catch {}
        }
      }

      const scrollH = await page.evaluate(() => document.body.scrollHeight).catch(() => 0);
      if (scrollH > 0) {
        for (let s = 1; s <= 3; s++) {
          await page.evaluate((y) => window.scrollTo(0, y), (scrollH / 3) * s).catch(() => {});
          await page.waitForTimeout(400);
        }
      }
      await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
      await page.waitForTimeout(500);

      const { buttons, groups } = await getButtonInfo(page, vp.mobile);
      allResults[vp.name] = { buttons, groups };

      const visible = buttons.filter(b => b.visible).length;
      console.log(`    -> ${buttons.length} buttons (${visible} visible), ${groups.length} groups`);

      for (const btn of buttons.filter(b => b.visible)) {
        try {
          if (btn.rect.width < 5 || btn.rect.height < 5) continue;
          const el = page.locator(`[data-bc-id="${btn.idx}"]`);
          await el.screenshot({
            path: resolve(outputDir, `screenshots/btn-${vp.name.toLowerCase()}-${btn.idx}.png`),
          });
        } catch {}
      }

      for (const grp of groups.filter(g => g.visible)) {
        try {
          if (grp.rect.width < 10 || grp.rect.height < 10) continue;
          const el = page.locator(`[data-bc-group-id="${grp.idx}"]`);
          await el.screenshot({
            path: resolve(outputDir, `screenshots/group-${vp.name.toLowerCase()}-${grp.idx}.png`),
          });
        } catch {}
      }

      await context.close();
    } catch (e) {
      console.log(`    Error: ${e.message}`);
      allResults[vp.name] = [];
    }
  }

  const reportPath = generateReport(allResults, url, outputDir);

    let total = 0, issues = 0;
  for (const data of Object.values(allResults)) {
    const btns = data.buttons || [];
    for (const b of btns) {
      total++;
      const small = b.rect.width < 38 || b.rect.height < 38;
      const hidden = !b.visible || b.css.display === 'none' || b.css.visibility === 'hidden' || parseFloat(b.css.opacity) === 0;
      if (hidden || small) issues++;
    }
  }

  console.log(`\nDone! Report: ${reportPath}`);
  console.log(`${total} buttons across ${VIEWPORTS.length} viewports${issues ? `, ${issues} flagged` : ''}\n`);

  await browser.close().catch(() => {});
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
