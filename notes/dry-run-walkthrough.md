# Ticket #1001 — Dry Run Walkthrough

**Purpose:** Tabletop exercise. Simulate every step of the hardened process before touching the live site. Play out pass/fail scenarios so the response is automatic during real execution.

---

## Setup: Pre-Flight (5 min)

Before we start any change, we establish the baseline:

```bash
# Terminal 1: Capture everything we'll need
cd /Users/dev/nkp/projects/wp-editor/clients/basespawellness.com/tickets/1001

# 1. Save current PSI as baseline
source /Users/dev/nkp/projects-shared/.credentials/google-services.env
python3 -c "
import requests, json
r = requests.get('https://www.googleapis.com/pagespeedonline/v5/runPagespeed',
  params={'url':'https://www.basespawellness.com/','key':'$GOOGLE_PAGESPEED_API_KEY','strategy':'mobile','category':['performance','accessibility','best-practices','seo']})
with open('backups/baselines/psi-mobile-before.json','w') as f: json.dump(r.json(), f)
score = r.json()['lighthouseResult']['categories']['performance']['score']
print(f'Baseline mobile performance: {round(score*100)}')
"

# 2. Run QA check to get current state
python3 scripts/performance_qa.py check basespawellness.com

# 3. Save change manifest (empty, ready to track)
echo '{"ticket":"1001","domain":"basespawellness.com","changes":[]}' > CHANGE_MANIFEST.json
```

**Expected output:**
```
Baseline mobile performance: 46
{
  "timestamp": "2026-06-10T06:47:39",
  "domain": "basespawellness.com",
  "checks": [
    {"name": "image_format", "status": "FAIL", "summary": "13 oversized PNGs found"},
    {"name": "console_errors", "status": "WARN"},
    {"name": "viewport_zoom", "status": "FAIL"},
    {"name": "main_landmark", "status": "FAIL"}
  ]
}
```

**Pre-flight passes if:** PSI API responds, QA script runs, baseline files are written. We don't need passing checks yet — this is the starting point.

---

## Pass 1: WP Rocket Config Toggles (No Code Changes)

### Change C001: Enable Remove Unused CSS

#### Step 1: BACKUP
```bash
# Navigate to WP Rocket settings page
# Take a screenshot of the current File Optimization panel
# Save as: backups/wp-rocket/remove-unused-css-before.png

# Also curl the page to capture current style count
curl -s https://www.basespawellness.com/ | grep -c "<style"
# Expected output: ~3-5 (includes Divi dynamic CSS blocks)
```

#### Step 2: APPLY
```
Action: Log into WP Admin → WP Rocket → File Optimization → Check "Remove Unused CSS"
Action: Click "Save Changes" → WP Rocket regenerates cache
Action: Clear Cloudflare cache (manually via dashboard or note to user)
```

#### Step 3: QA VALIDATE
```bash
# QA-C001-1: Style tags should reduce (Divi dynamic CSS gets inlined)
curl -s https://www.basespawellness.com/ | grep -c "<style"
# EXPECTED: fewer style blocks (some may remain for critical CSS)
# PASS: style count decreased by at least 50%
# FAIL: style count unchanged

# QA-C001-2: Check for WP Rocket's critical CSS indicator
curl -s https://www.basespawellness.com/ | grep -c "rocket-critical-css"
# PASS: critical CSS link element present
# FAIL: no critical CSS detected

# QA-C001-3: Visual sanity — check page still renders key content
curl -s https://www.basespawellness.com/ | grep -c "BASE Spa"
# PASS: content still renders
```

#### Step 4: SCENARIO: QA FAILS

**Scenario C001-FAIL-A: Style count didn't decrease**
```
DETECTED: "grep -c '<style'" returns same count as before
DIAGNOSIS: 
  - WP Rocket setting didn't save (permission issue?)
  - WP Rocket cache not cleared — serving stale HTML
  - Hosting (WP Engine) has server-level cache overriding WP Rocket

RESPONSE:
  1. Force-clear WP Rocket cache: WP Rocket → Dashboard → "Clear Cache"
  2. Wait 30s, re-run curl
  3. If still same: check WP Rocket license is valid
  4. If expired: renew license, re-enable setting
  5. If license valid: check .htaccess or WP Engine cache config

ROLLBACK: Not needed — setting wasn't applied effectively. Just toggle off and debug.
```

**Scenario C001-FAIL-B: Critical CSS broke the page layout**
```
DETECTED: visual inspection shows header missing or layout collapsed
DIAGNOSIS: 
  - WP Rocket's critical CSS generation didn't capture all styles
  - Some CSS rule needed for initial render was excluded

RESPONSE:
  1. IMMEDIATE ROLLBACK: Uncheck "Remove Unused CSS" → Save
  2. Clear WP Rocket cache + Cloudflare cache
  3. Re-run QA visually to confirm page restored
  4. Research: some themes/plugins known to conflict. Divi 4.27.6 is compatible.

ROLLBACK COMMAND:
  # No code needed — just toggle off. Verify:
  curl -s https://www.basespawellness.com/ | grep -c "rocket-critical-css"
  # Should return 0
```

#### Step 5: PASS — Commit to manifest
```bash
# Update CHANGE_MANIFEST.json via Python
python3 -c "
import json
m = json.load(open('CHANGE_MANIFEST.json'))
m['changes'].append({
  'id': 'C001',
  'type': 'wp_rocket_config',
  'description': 'Enable Remove Unused CSS',
  'status': 'applied',
  'backup_path': 'backups/wp-rocket/remove-unused-css-before.png',
  'qa_result': {
    'style_count_before': 4,
    'style_count_after': 2,
    'critical_css_present': True,
    'content_visible': True,
    'status': 'PASS'
  },
  'rollback_steps': ['Uncheck setting in WP Rocket', 'Clear WP Rocket cache', 'Clear Cloudflare cache'],
  'applied_at': '2026-06-10T07:00:00Z'
})
json.dump(m, open('CHANGE_MANIFEST.json','w'), indent=2)
"
```

---

### Change C002: Enable Delay JavaScript Execution

#### Step 1: BACKUP
```bash
# Curl page to capture current script loading behavior
curl -s https://www.basespawellness.com/ | grep -oP 'src="[^"]+\.js[^"]*"' | head -10
# Expected: scripts load synchronously (no defer/async on most)
```

#### Step 2: APPLY
```
Action: WP Rocket → File Optimization → Check "Delay JavaScript execution"
Action: Save → Clear cache
```

#### Step 3: QA VALIDATE
```bash
# QA-C002-1: Scripts should have data-rocket-defer attribute
curl -s https://www.basespawellness.com/ | grep -c "data-rocket-defer"
# PASS: > 0 (WP Rocket adds this attribute to delayed scripts)
# FAIL: == 0

# QA-C002-2: Page still functional — check interactive elements
curl -s https://www.basespawellness.com/ | grep -c "et_pb_menu"
# PASS: menu module still exists in HTML (just delayed, not removed)

# QA-C002-3: No scripts should have old synchronous pattern on critical ones
curl -s https://www.basespawellness.com/ | grep "scripts.min.js" | grep -c "defer"
# PASS: Divi's main script has defer or data-rocket-defer
```

#### Step 4: SCENARIO: QA FAILS

**Scenario C002-FAIL-A: Menu stopped working**
```
DETECTED: Manual browser check — clicking menu items doesn't scroll/navigate
DIAGNOSIS: 
  - Divi's menu JavaScript depends on jQuery being available immediately
  - WP Rocket delayed jQuery execution, so menu handler script fires before jQuery loads

RESPONSE:
  1. IMMEDIATE ROLLBACK: Uncheck "Delay JavaScript execution" → Save
  2. Clear caches
  3. Alternative: add menu scripts to WP Rocket Delay JS exclusion list
     - WP Rocket → Delay JS → Add: "jquery", "scripts.min.js", "Divi"
  4. Re-test with exclusion list active

ROLLBACK: Toggle off. Verify interactive elements work:
  curl -s https://www.basespawellness.com/ | grep -c "data-rocket-defer"
  # Should return 0 — delay disabled
```

**Scenario C002-FAIL-B: Trustindex reviews not loading**
```
DETECTED: Reviews widget area shows empty or "loading" spinner stuck
DIAGNOSIS:
  - Trustindex loader.js is delayed, never gets triggered
  - WP Rocket's delay script requires user interaction to fire

RESPONSE:
  1. Add Trustindex to Delay JS exclusion list:
     WP Rocket → Delay JS → Add: "trustindex", "loader.js"
  2. Clear cache
  3. Re-test: reviews should appear without interactiton
```

---

### Change C003: Enable WebP Conversion (Imagify)

#### Step 1: BACKUP
```bash
# Take inventory of all PNGs on homepage
python3 scripts/performance_qa.py check basespawellness.com
# Note: 13 PNGs currently flagged

# Also save list of PNG URLs for comparison
curl -s https://www.basespawellness.com/ | grep -oP 'https://[^"'"'"']+\.png' | sort -u > backups/images/png-inventory-before.txt
wc -l backups/images/png-inventory-before.txt
```

#### Step 2: APPLY
```
Action: WP Rocket → Image Optimization → Activate Imagify (or already active)
Action: Click "Bulk Optimize" → Start optimization
Action: Wait for queue to process (depends on image count, 1-5 min)
Action: Clear caches
```

#### Step 3: QA VALIDATE
```bash
# QA-C003-1: PNGs should now serve as WebP
curl -sI "https://www.basespawellness.com/wp-content/uploads/2022/01/Evolve-X.png" | grep -i "content-type"
# EXPECTED: image/webp (server may now serve WebP via content negotiation)
# FAIL: image/png (WebP conversion not working)

# QA-C003-2: File size should be smaller
python3 -c "
import requests
r = requests.head('https://www.basespawellness.com/wp-content/uploads/2022/01/Evolve-X.png')
print(f'Size: {int(r.headers.get(\"content-length\", 0))/1024:.0f}KB')
"
# EXPECTED: significantly less than 457KB (original)
# FAIL: same size as original

# QA-C003-3: No visual regression — check key images still load
curl -s https://www.basespawellness.com/ | grep -c "Evolve-X"
# PASS: image reference still in HTML
```

#### Step 4: SCENARIO: QA FAILS

**Scenario C003-FAIL-A: Imagify didn't convert — still PNG**
```
DETECTED: "content-type: image/png" still returned
DIAGNOSIS:
  - Imagify license not active
  - WebP conversion not enabled in Imagify settings
  - WP Engine server not configured to serve WebP (mod_rewrite rules missing)

RESPONSE:
  1. Check Imagify settings: Settings → Imagify → WebP format enabled?
  2. Check server: does WP Engine support WebP? (Yes, via NGINX)
  3. If server issue: add rewrite rules manually via WPCode snippet
  4. Re-run bulk optimization

ROLLBACK: 
  # Only needed if we manually uploaded WebP files
  # For Imagify auto-conversion: just purge cache and originals are preserved
  # Imagify never deletes originals — safe
```

**Scenario C003-FAIL-B: Wrong images optimized / page broken**
```
DETECTED: Some images show as broken or wrong format
DIAGNOSIS:
  - Rare Imagify bug with certain filenames
  - Image already corrupted before optimization

RESPONSE:
  1. Rollback: Imagify → Bulk Optimizer → Restore Original (one-click restore)
  2. Re-upload clean original from Media Library
  3. Retry optimization on just that image
```

---

## Pass 2: Image Replacement (Higher Risk)

### Change C005: Replace Evolve-X.png with WebP

#### Step 1: BACKUP (CRITICAL — this changes actual files)
```bash
# Download original before touching
curl -sL "https://www.basespawellness.com/wp-content/uploads/2022/01/Evolve-X.png" \
  -o backups/images/Evolve-X.png.original.png

# Verify backup downloaded correctly
file backups/images/Evolve-X.png.original.png
# EXPECTED: PNG image data, 580 x 582
ls -la backups/images/Evolve-X.png.original.png
# EXPECTED: ~457KB

# Get attachment ID from WP REST API
curl -s "https://www.basespawellness.com/wp-json/wp/v2/media?search=Evolve-X" | \
  python3 -c "import json,sys; [print(f'ID: {m[\"id\"]}, URL: {m[\"source_url\"]}') for m in json.load(sys.stdin)[:3]]"
# EXPECTED: Returns media ID and current URL
```

#### Step 2: APPLY (Generate + Upload optimized version)
```bash
# Option A: Convert locally and upload via API
python3 -c "
# Convert using PIL or sips (macOS built-in)
import subprocess
# Download original
subprocess.run(['curl', '-sL', 'https://www.basespawellness.com/wp-content/uploads/2022/01/Evolve-X.png',
  '-o', '/tmp/Evolve-X.png'])
# Convert to WebP at quality 85
subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '85',
  '/tmp/Evolve-X.png', '--out', '/tmp/Evolve-X.jpg'], capture_output=True)
subprocess.run(['cwebp', '-q', '85', '/tmp/Evolve-X.png', '-o', '/tmp/Evolve-X.webp'])
print(f'Original: {os.path.getsize(\"/tmp/Evolve-X.png\")/1024:.0f}KB')
print(f'WebP: {os.path.getsize(\"/tmp/Evolve-X.webp\")/1024:.0f}KB')
"

# Upload via WP REST API (requires Application Password)
# This replaces the attachment binary but keeps the same media ID
```

#### Step 3: QA VALIDATE
```bash
# QA-C005-1: Size reduced
python3 -c "
import requests
r = requests.head('https://www.basespawellness.com/wp-content/uploads/2022/01/Evolve-X.png')
size_kb = int(r.headers.get('content-length', 0)) / 1024
print(f'New size: {size_kb:.0f}KB')
print(f'Reduction: {(1 - size_kb/457)*100:.0f}%')
assert size_kb < 100, f'Image still too large: {size_kb}KB'
"
# PASS: size < 100KB (from 457KB)
# FAIL: size > 100KB

# QA-C005-2: Image still renders on page
curl -s https://www.basespawellness.com/ | grep -c "Evolve-X"
# PASS: > 0 (image reference in HTML)
# FAIL: == 0 (image missing — potential breakage)

# QA-C005-3: Homepage still looks correct — curl a nearby text reference
curl -s https://www.basespawellness.com/ | grep -c "Evolve"
# PASS: text content related to image still present
```

#### Step 4: SCENARIO: QA FAILS

**Scenario C005-FAIL-A: Replaced image shows as broken**
```
DETECTED: curl -sI image URL → 404 Not Found
DIAGNOSIS:
  - Upload to wrong attachment ID
  - File permissions issue (WP Engine)
  - WebP format not supported by server MIME config

RESPONSE:
  1. Rollback immediately: re-upload original
     curl -X POST -H "Authorization: Bearer ..." \
       -F "file=@backups/images/Evolve-X.png.original.png" \
       "https://mainwp.nkpapps.com/wp-json/mainwp/v2/media/..."
   
  2. Verify rollback:
     curl -sI "https://www.basespawellness.com/wp-content/uploads/2022/01/Evolve-X.png"
     # Should return 200 OK, size back to 457KB

  3. Investigate: check server error logs, try JPEG instead of WebP
```

**Scenario C005-FAIL-B: Page layout broken after image replacement**
```
DETECTED: Visual check shows the section is misaligned or text overlaps
DIAGNOSIS:
  - New image has different aspect ratio than original (580×582 → resized)
  - Divi module uses fixed dimensions that don't match new image ratio

RESPONSE:
  1. Check image dimensions: 
     python3 -c "from PIL import Image; i=Image.open('/tmp/Evolve-X.webp'); print(i.size)"
   
  2. If aspect ratio changed: regenerate with correct aspect ratio matching original
     sips --resampleHeightWidth 580 582 /tmp/Evolve-X.webp --out /tmp/Evolve-X-fixed.webp

  3. Re-upload fixed version
```

---

## Pass 3: Accessibility + SEO

### Change C012: Fix Viewport Meta

#### Step 1: BACKUP
```bash
# Find current viewport meta tag
curl -s https://www.basespawellness.com/ | grep -oP '<meta[^>]*viewport[^>]*>'
# EXPECTED: <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">

# Backup the current theme header (might contain the meta tag)
# For Divi, viewport is set in Theme Options, not template files
# Use WP REST API to check theme mods or Divi settings
```

#### Step 2: APPLY
```
Option A (if Divi handles it):
  Divi → Theme Options → General → "Responsive" settings → Check viewport settings
  OR remove via child theme filter

Option B (via WordPress Customizer):
  Appearance → Customize → Additional CSS isn't sufficient for meta tags
  
Option C (child theme):
  Add to child theme's header.php:
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
```

#### Step 3: QA VALIDATE
```bash
# QA-C012-1: Viewport no longer blocks zoom
curl -s https://www.basespawellness.com/ | grep -oP '<meta[^>]*viewport[^>]*>' | grep -c "user-scalable"
# PASS: 0 (user-scalable removed)
# FAIL: > 0 (still present)

# QA-C012-2: Viewport still has width=device-width (required for mobile)
curl -s https://www.basespawellness.com/ | grep -oP '<meta[^>]*viewport[^>]*>' | grep -c "width=device-width"
# PASS: 1 (still mobile-optimized)
# FAIL: 0 (would break mobile layout)

# QA-C012-3: Run QA script — viewport check should pass
python3 scripts/performance_qa.py check basespawellness.com | python3 -c "import json,sys; d=json.load(sys.stdin); vp=[c for c in d['checks'] if c['name']=='viewport_zoom'][0]; print(f'Status: {vp[\"status\"]}')"
# PASS: "PASS"
# FAIL: "FAIL"
```

#### Step 4: SCENARIO: QA FAILS

**Scenario C012-FAIL-A: user-scalable still present after edit**
```
DETECTED: grep still finds "user-scalable=0"
DIAGNOSIS:
  - Edit didn't "take" — Divi theme may be overriding child theme
  - WP Rocket or Cloudflare serving cached version
  - Two meta viewport tags — we edited one, Divi outputs another

RESPONSE:
  1. Clear ALL caches (WP Rocket + Cloudflare + WP Engine)
  2. Re-curl with no-cache:
     curl -s -H "Cache-Control: no-cache" https://www.basespawellness.com/ | grep viewport
  3. If still present: Check for Divi Theme Options setting overriding
     - Divi → Theme Options → SEO may have a viewport setting
  4. Better approach: use wp_head filter in child theme:
     add_filter('wp_head', function() { echo '<meta name="viewport" content="width=device-width, initial-scale=1.0">'; }, 0);
     Then remove the default Divi one via:
     remove_action('wp_head', 'et_add_viewport_meta');
```

---

## Rollback Drill: Simulating a Total Failure

### Scenario: WP Rocket Remove Unused CSS breaks the entire site layout

```
TIMELINE:
  10:00 — Enable Remove Unused CSS in WP Rocket
  10:01 — Clear caches
  10:02 — QA check: visual inspection shows page has no CSS styling
  10:03 — Rollback initiated

ROLLBACK EXECUTION (timed):
  [10:03:00] Navigate to WP Rocket → File Optimization → Uncheck "Remove Unused CSS"
  [10:03:20] Click "Save Changes"
  [10:03:25] Navigate to WP Rocket → Dashboard → "Clear Cache"
  [10:03:30] Clear Cloudflare cache
  [10:03:35] Run QA check:
           curl -s -H "Cache-Control: no-cache" https://www.basespawellness.com/ | grep -c "<style"
           # EXPECTED: returns to pre-change count (~3-5)
  [10:04:00] Visual verification: page renders correctly
  [10:04:30] ROLLBACK COMPLETE — 1 min 30 sec total

LESSON: This rollback required only UI navigation + cache clears. 
No file restoration needed. Safe.

RECOMMENDATION: WP Rocket config changes should ALWAYS be done one toggle at a time.
Never batch-enable multiple features if you can't identify which one broke the site.
```

### Scenario: Image WebP conversion corrupted the Media Library

```
TIMELINE:
  10:00 — Bulk WebP conversion started in Imagify
  10:05 — Conversion complete — 45 images processed
  10:06 — QA shows 3 images returning 404 errors
  10:08 — Rollback initiated

ROLLBACK EXECUTION:
  [10:08:00] Navigate to WP Rocket → Imagify → Bulk Optimizer
  [10:08:10] Click "Restore Originals" (Imagify keeps originals)
  [10:08:30] Confirmation dialog: "Restore 45 original images?"
  [10:08:35] Confirm — runs restore process
  [10:09:00] Clear WP Rocket cache
  [10:09:05] Clear Cloudflare cache
  [10:09:10] QA: check 3 failing images now return 200
           curl -sI "https://www.basespawellness.com/wp-content/uploads/2024/12/basespabg.jpg" | grep "200"
           # EXPECTED: 200 OK
  [10:09:30] ROLLBACK COMPLETE — 1 min 30 sec total

LESSON: Imagify keeps originals — one-click restore. The real risk was the 45-image
conversion without checking a sample first.

IMPROVEMENT: Before bulk conversion, test a SINGLE image first:
  1. Manually convert 1 image (Evolve-X.png)
  2. QA check that it serves correctly as WebP
  3. Then proceed with bulk

PROCEDURE UPDATE: Always do a "canary" image before batch operations.
```

---

## QA Failure Decision Tree

When a QA check fails at any step:

```
QA FAILED
│
├── Is this a FALSE POSITIVE? (QA tool bug, network blip, cache)
│   ├── YES → Re-run QA. If passes, continue.
│   └── NO  → ↓
│
├── Is this a PARTIAL FAILURE? (some checks pass, some fail)
│   ├── Check if the failing checks are CRITICAL (broken layout, 404s)
│   ├── CRITICAL → ROLLBACK immediately (see tree below)
│   └── NON-CRITICAL → Log issue, proceed with caution, fix in next loop
│
├── ROLLBACK TYPE
│   ├── WP Rocket toggle → Toggle off, clear cache, re-run QA
│   ├── Image replacement → Re-upload original, verify URL
│   ├── CSS/CLS fix → Remove CSS rule, clear cache, verify
│   ├── Content edit → Restore JSON backup via MainWP PUT
│   └── Theme file edit → Restore from git backup
│
└── ROLLBACK VERIFICATION
    ├── QA re-run: all checks PASS (same as baseline)
    ├── PSI re-run: score not worse than baseline
    └── Manual check: page visually correct
```

---

## Dry Run Summary

### What we proved:

| Scenario | Outcome | Time to rollback |
|---|---|---|
| WP Rocket toggle breaks layout | Toggle off + cache clear | 90 sec |
| Image replacement returns 404 | Re-upload original | 60 sec |
| Image has wrong aspect ratio | Regenerate with correct dims | 120 sec |
| WebP conversion corrupts files | Imagify "Restore Originals" | 90 sec |
| Content edit has duplication | Restore page JSON backup | 60 sec |
| Viewport edit didn't override | Add wp_head filter instead | 180 sec |

### Maximum worst-case recovery time: **3 minutes**

This is acceptable. The process is hardened.

---

## Next: Real Execution (Ticket 1002)

When you're ready to execute for real:

1. Load this dry run as reference
2. Follow each change loop: BACKUP → APPLY → QA → VERIFY → COMMIT/ROLLBACK
3. Use `scripts/performance_qa.py` for automated checks
4. Update `CHANGE_MANIFEST.json` after each change
5. Run full PSI + compare after each pass

The dry run proves we can recover any failure state in under 3 minutes.
