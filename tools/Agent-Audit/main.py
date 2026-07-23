#!/usr/bin/env python3
"""SEO + QA Audit using agent-browser CLI (Vercel Labs)"""
import sys, os, json, subprocess, html as hmod, time, re

AB = "agent-browser"
VIEWPORTS = {"Desktop": (1280, 800), "iPad": (768, 1024), "Mobile": (375, 667)}
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

def run(cmd, timeout=30):
    """Run agent-browser command and return stdout."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        return f"ERROR: {e}"

def run_batch(cmds, timeout=60):
    """Run multiple agent-browser commands in batch mode."""
    json_cmds = json.dumps([c.split() for c in cmds])
    return subprocess.run(
        [AB, "batch", "--json"],
        input=json_cmds, capture_output=True, text=True, timeout=timeout
    ).stdout.strip()

def eval_js(js):
    """Run JavaScript and return parsed result."""
    wrapper = f"(function(){{ return JSON.stringify((function(){{{js}}})()); }})()"
    result = run([AB, "eval", wrapper])
    if not result:
        return None
    try:
        parsed = json.loads(result)
        if isinstance(parsed, str):
            try:
                return json.loads(parsed)
            except:
                return parsed
        return parsed
    except:
        return result

def screenshot(path, full=False):
    cmd = [AB, "screenshot", path]
    if full: cmd.append("--full")
    run(cmd)

def audit(url):
    results = {"url": url}
    if not url.startswith("http"):
        url = "https://" + url
    
    print(f"\n  Opening {url}...")
    
    # Open the page
    run([AB, "open", url], timeout=30)
    time.sleep(3)
    
    # ── STATIC CHECKS (via JS eval) ──
    print("  Running static checks...")
    
    # Title
    title_data = eval_js("""
        const t = document.querySelector('title');
        const text = t ? t.innerText.trim() : '';
        return { text, length: text.length };
    """)
    if title_data:
        results["title"] = title_data["text"]
        results["title_len"] = title_data["length"]
    
    # Meta description
    meta_data = eval_js("""
        const m = document.querySelector('meta[name="description"]');
        const text = m ? m.getAttribute('content') || '' : '';
        return { text, length: text.length };
    """)
    if meta_data:
        results["meta_desc"] = meta_data["text"]
        results["meta_len"] = meta_data["length"]
    
    # Headings
    headings_data = eval_js("""
        const hs = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        const items = [];
        for (const h of hs) items.push({ tag: h.tagName.toLowerCase(), text: h.innerText.trim().slice(0, 100) });
        return { total: items.length, h1: items.filter(i => i.tag === 'h1').length, items };
    """)
    if headings_data:
        results["headings"] = headings_data
    
    # Schema
    schema_data = eval_js("""
        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
        const types = [];
        for (const s of scripts) {
            try {
                const d = JSON.parse(s.textContent);
                if (d['@type']) types.push(d['@type']);
                if (d['@graph']) d['@graph'].forEach(g => { if (g['@type']) types.push(g['@type']); });
            } catch(e) {}
        }
        return types;
    """)
    results["schema"] = schema_data or []
    
    # Image alt
    alt_data = eval_js("""
        const imgs = document.querySelectorAll('img');
        let missing = 0;
        for (const img of imgs) { if (!img.getAttribute('alt')) missing++; }
        return { total: imgs.length, missing };
    """)
    if alt_data:
        results["image_alt"] = alt_data
    
    # Viewport
    vp_data = eval_js("""
        const m = document.querySelector('meta[name="viewport"]');
        return m ? m.getAttribute('content') : null;
    """)
    results["viewport"] = vp_data
    
    # Canonical
    canon_data = eval_js("""
        const c = document.querySelector('link[rel="canonical"]');
        return c ? c.getAttribute('href') : null;
    """)
    results["canonical"] = canon_data
    
    # Internal links count
    links_data = eval_js("""
        const domain = window.location.hostname;
        const links = document.querySelectorAll('a[href]');
        let count = 0;
        for (const a of links) {
            const href = a.getAttribute('href');
            if (href && !href.startsWith('#') && !href.startsWith('javascript:') && !href.startsWith('mailto:')) {
                try { if (new URL(href, window.location.href).hostname === domain) count++; } catch(e) {}
            }
        }
        return count;
    """)
    results["internal_links"] = links_data
    
    # Contact forms
    form_data = eval_js("""
        const forms = document.querySelectorAll('form');
        let count = 0;
        for (const f of forms) {
            if (f.querySelector('input, textarea, select')) count++;
        }
        if (count === 0) {
            const popup = document.querySelector('[class*="popup"] input, [class*="modal"] input, [class*="widget"] input');
            if (popup) count = 1;
        }
        return count;
    """)
    results["contact_forms"] = form_data
    
    # Fonts
    font_data = eval_js("""
        const els = document.querySelectorAll('body, h1, h2, h3, p, a, div');
        const fonts = new Set();
        for (const el of els) { try { fonts.add(getComputedStyle(el).fontFamily); } catch(e) {} }
        return Array.from(fonts).slice(0, 10);
    """)
    results["fonts"] = font_data or []
    
    # ── DYNAMIC CHECKS ──
    print("  Running dynamic checks...")
    
    # Sticky menu
    sticky_results = {}
    for vp_name in ["Desktop", "iPad", "Mobile"]:
        w, h = VIEWPORTS[vp_name]
        run([AB, "set", "viewport", str(w), str(h)])
        time.sleep(0.5)
        
        # Scroll first
        eval_js("window.scrollBy(0, 800)")
        time.sleep(2)
        
        # Then check
        sticky_data = eval_js("""
            var stuck = document.querySelector('.stuck, .sticky, .is-sticky, .et_pb_sticky--stuck, .et_pb_sticky_module');
            var header = document.querySelector('header');
            if (stuck) {
                var cs = getComputedStyle(stuck);
                var rect = stuck.getBoundingClientRect();
                if (cs.position === 'fixed' && rect.height > 20) return true;
            }
            if (header) {
                var cs = getComputedStyle(header);
                if (cs.position === 'fixed' || cs.position === 'sticky') return true;
            }
            return false;
        """)
        sticky_results[vp_name] = sticky_data
    
    results["sticky"] = sticky_results
    
    # Hero image
    hero_data = eval_js("""
        const imgs = document.querySelectorAll('img');
        let best = null, bestArea = 0;
        for (const img of imgs) {
            if (!img.complete || img.naturalWidth === 0) continue;
            const r = img.getBoundingClientRect();
            if (r.top < window.innerHeight * 0.6 && r.width > 80) {
                const area = r.width * r.height;
                if (area > bestArea) { bestArea = area; best = { src: img.src.slice(0, 80), w: img.naturalWidth, h: img.naturalHeight }; }
            }
        }
        return best;
    """)
    results["hero"] = hero_data
    
    # Image loading
    img_load = eval_js("""
        const imgs = document.querySelectorAll('img');
        const broken = [];
        for (const img of imgs) {
            if (img.naturalWidth === 0) broken.push(img.src || '(no src)');
        }
        return { total: imgs.length, broken };
    """)
    results["image_loading"] = img_load
    
    # ── SCREENSHOTS ──
    print("  Taking screenshots...")
    run([AB, "set", "viewport", "1280", "800"])
    time.sleep(0.3)
    screenshot(os.path.join(REPORT_DIR, "sticky_desktop.png"))
    
    # Scroll and take sticky screenshot
    eval_js("window.scrollBy(0, 800)")
    time.sleep(1)
    screenshot(os.path.join(REPORT_DIR, "sticky_desktop_scrolled.png"))
    eval_js("window.scrollTo(0, 0)")
    
    # iPad
    run([AB, "set", "viewport", "768", "1024"])
    time.sleep(0.5)
    screenshot(os.path.join(REPORT_DIR, "hero_ipad.png"))
    
    # Mobile
    run([AB, "set", "viewport", "375", "667"])
    time.sleep(0.5)
    screenshot(os.path.join(REPORT_DIR, "hero_mobile.png"))
    
    # Close browser
    run([AB, "close"])
    
    return results


def print_report(r):
    def line(name, val, detail=""):
        d = f"  |  {detail}" if detail else ""
        return f"  {name:<28} {val}{d}"
    
    print()
    print(f"  {'─'*60}")
    print(f"  {'SEO & QA AUDIT (agent-browser)':^60}")
    print(f"  {'─'*60}")
    print()
    print(f"  {'— STATIC CHECKS —':^40}")
    print(line("TITLE", f"Chars: {r.get('title_len', 0)}"))
    print(line("META DESCRIPTION", f"Chars: {r.get('meta_len', 0)}"))
    print(line("HEADINGS", f"H1: {r.get('headings', {}).get('h1', 0)} | Total: {r.get('headings', {}).get('total', 0)}"))
    print(line("SCHEMA", f"Types: {len(r.get('schema', []))}"))
    print(line("IMAGE ALT", f"Missing: {r.get('image_alt', {}).get('missing', 0)}/{r.get('image_alt', {}).get('total', 0)}"))
    print(line("VIEWPORT", "Found" if r.get('viewport') else "Missing"))
    print(line("CANONICAL", r.get('canonical') or "Missing"))
    print(line("INTERNAL LINKS", f"Total: {r.get('internal_links', 0)}"))
    print(line("CONTACT FORMS", f"Found: {r.get('contact_forms', 0)}"))
    print(line("FONTS", f"Unique: {len(r.get('fonts', []))}"))
    print()
    print(f"  {'— DYNAMIC CHECKS —':^40}")
    for vp in ["Desktop", "iPad", "Mobile"]:
        sticky = r.get("sticky", {}).get(vp, False)
        visible = "Yes" if sticky else "No"
        print(line(f"STICKY ({vp.upper()})", "PASS" if sticky else "FAIL", f"Visible: {'Yes' if sticky else 'No'}"))
    img = r.get("image_loading", {})
    print(line("IMAGE LOADING", f"Total: {img.get('total', 0)} | Flagged: {len(img.get('broken', []))}"))
    print(line("HERO IMAGE", "Found" if r.get("hero") else "Not found"))
    print()


def generate_html(r):
    def badge(passed):
        c = "#22c55e" if passed else "#ef4444"
        t = "PASS" if passed else "FAIL"
        return f'<span style="background:{c};color:white;padding:2px 8px;border-radius:10px;font-size:10px">{t}</span>'
    
    def row(label, value):
        return f'<tr><td style="color:#64748b;width:200px">{label}</td><td>{value}</td></tr>'
    
    sticky = r.get("sticky", {})
    img = r.get("image_loading", {})
    headings = r.get("headings", {})
    alt = r.get("image_alt", {})
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent-Browser Audit — {r.get('url', '')}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f8fafc;color:#1e293b;padding:24px}}
.container{{max-width:900px;margin:0 auto}}
h1{{font-size:20px;margin-bottom:4px}}
.url{{color:#64748b;font-size:12px;margin-bottom:20px;word-break:break-all}}
.disclaimer{{background:#fffbeb;border:2px solid #f59e0b;border-radius:8px;padding:14px 18px;margin-bottom:24px;font-size:12px;color:#78350f;line-height:1.6}}
.section{{margin-bottom:24px}}
.section h2{{font-size:14px;color:#334155;margin-bottom:12px;border-bottom:2px solid #e2e8f0;padding-bottom:6px}}
table{{width:100%;border-collapse:collapse;font-size:12px;background:white;border-radius:8px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,0.05)}}
td{{padding:8px 14px;border-bottom:1px solid #f1f5f9}}
img{{max-width:100%;border-radius:6px;margin-top:8px;border:1px solid #e2e8f0}}
</style>
</head>
<body><div class="container">
<h1>SEO + QA Audit (agent-browser)</h1>
<div class="url">{r.get('url', '')}</div>
<div class="disclaimer"><strong>Disclaimer:</strong> Automated audit using agent-browser (headless). Some checks may be affected by headless detection. Manual verification recommended.</div>

<div class="section"><h2>Static Checks</h2><table>
{row("Title", f"{r.get('title', '—')} ({r.get('title_len', 0)} chars)")}
{row("Meta Description", f"{r.get('meta_desc', '—')} ({r.get('meta_len', 0)} chars)")}
{row("Headings", f"H1: {headings.get('h1', 0)} | Total: {headings.get('total', 0)}")}
{row("Schema Markup", f"{len(r.get('schema', []))} types found")}
{row("Image Alt Text", f"Missing: {alt.get('missing', 0)}/{alt.get('total', 0)}")}
{row("Viewport Meta", r.get('viewport', 'Not found'))}
{row("Canonical", r.get('canonical', 'Not found'))}
{row("Internal Links", str(r.get('internal_links', 0)))}
{row("Contact Forms", str(r.get('contact_forms', 0)))}
{row("Fonts", ', '.join(r.get('fonts', [])[:5]))}
</table></div>

<div class="section"><h2>Dynamic Checks</h2><table>
{row("Sticky (Desktop)", badge(sticky.get('Desktop', False)))}
{row("Sticky (iPad)", badge(sticky.get('iPad', False)))}
{row("Sticky (Mobile)", badge(sticky.get('Mobile', False)))}
{row("Image Loading", f"Total: {img.get('total', 0)} | Flagged: {len(img.get('broken', []))}")}
{row("Hero Image", f"{r.get('hero', {}).get('src', 'Not found') if r.get('hero') else 'Not found'}")}
</table></div>

<div class="section"><h2>Evidence (Screenshots)</h2>
<p style="font-size:12px;color:#64748b;margin-bottom:8px">Sticky Menu — Desktop (before/after scroll):</p>
<img src="sticky_desktop.png" loading="lazy">
<img src="sticky_desktop_scrolled.png" loading="lazy" style="margin-bottom:16px">
<p style="font-size:12px;color:#64748b;margin-bottom:8px">Hero — iPad / Mobile:</p>
<img src="hero_ipad.png" loading="lazy" style="width:49%;display:inline-block">
<img src="hero_mobile.png" loading="lazy" style="width:49%;display:inline-block">
</div>

</div></body></html>"""
    path = os.path.join(REPORT_DIR, "report.html")
    with open(path, "w") as f:
        f.write(html)
    return os.path.abspath(path)


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Paste URL: ").strip()
        if not url:
            print("No URL provided.")
            return
    
    print(f"\n  Agent-Browser Audit")
    print(f"  {'='*50}")
    
    try:
        results = audit(url)
        print_report(results)
        report_path = generate_html(results)
        print(f"  Report: {report_path}")
        print()
    except Exception as e:
        print(f"  ✗ Error: {e}")


if __name__ == "__main__":
    main()
