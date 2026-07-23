import { createServer } from 'http';
import { spawn } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 8766;

const dashboardHtml = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Unified QA Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.box{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:40px;width:100%;max-width:560px}
h1{font-size:24px;margin-bottom:8px}
p{color:#94a3b8;margin-bottom:20px;font-size:14px}
label{display:block;font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
input{width:100%;padding:12px 14px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#e2e8f0;font-size:15px;outline:none}
input:focus{border-color:#38bdf8}
.buttons{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px}
button{padding:12px;border:none;border-radius:8px;background:#38bdf8;color:#0f172a;font-weight:700;font-size:14px;cursor:pointer}
button:hover{background:#7dd3fc}
button:disabled{opacity:.6;cursor:not-allowed}
button.secondary{background:#334155;color:#e2e8f0}
button.secondary:hover{background:#475569}
#status{margin-top:20px;font-size:13px;color:#94a3b8;white-space:pre-wrap}
#result{margin-top:16px;display:none}
#result a{color:#38bdf8;font-weight:600}
.error{color:#fca5a5}
.success{color:#86efac}
.demo-link{display:block;margin-top:16px;color:#38bdf8;font-size:13px}
</style>
</head>
<body>
<div class="box">
  <h1>Unified QA Dashboard</h1>
  <p>Enter a base URL, then run the QA suite you need.</p>
  <label for="url">Base URL</label>
  <input id="url" type="url" placeholder="http://localhost:8765" value="http://localhost:8765">

  <div class="buttons">
    <button id="run-images" onclick="runSuite('images')">Check Images</button>
    <button id="run-buttons" onclick="runSuite('buttons')">Check Buttons</button>
    <button id="run-values" onclick="runSuite('values')">QA: Values</button>
    <button id="run-sweep" onclick="runSuite('sweep')">QA: Sweep</button>
    <button id="run-full" class="secondary" onclick="runSuite('full')" style="grid-column:span 2">QA: Full Run</button>
  </div>

  <a class="demo-link" href="/dashboard-demo.html" target="_blank">Open sample dashboard →</a>

  <div id="status"></div>
  <div id="result">
    <a id="reportLink" href="#" target="_blank">Open Report</a>
  </div>
</div>
<script>
async function runSuite(suite){
  const url = document.getElementById('url').value.trim();
  const status = document.getElementById('status');
  const result = document.getElementById('result');
  const link = document.getElementById('reportLink');
  const buttons = document.querySelectorAll('button');

  if(!url){ status.textContent = 'Please enter a base URL.'; status.className='error'; return; }

  buttons.forEach(b => b.disabled = true);
  status.textContent = 'Running ' + suite + '... please wait.';
  status.className = '';
  result.style.display = 'none';

  try {
    const res = await fetch('/qa?suite=' + suite + '&url=' + encodeURIComponent(url));
    const data = await res.json();
    if(data.error){
      status.textContent = 'Error: ' + data.error;
      status.className = 'error';
    } else {
      status.textContent = data.output || 'Done!';
      status.className = data.success ? 'success' : 'error';
      if(data.reportUrl){
        link.href = data.reportUrl;
        link.textContent = 'Open Report: ' + data.reportUrl;
        result.style.display = 'block';
      }
    }
  } catch(err) {
    status.textContent = 'Error: ' + err.message;
    status.className = 'error';
  } finally {
    buttons.forEach(b => b.disabled = false);
  }
}
</script>
</body>
</html>`;

function runChild(scriptArgs, timeoutMs = 180000) {
  return new Promise((resolvePromise) => {
    const child = spawn('node', scriptArgs, {
      cwd: __dirname,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (d) => (stdout += d));
    child.stderr.on('data', (d) => (stderr += d));

    const timer = setTimeout(() => {
      child.kill();
      resolvePromise({
        code: 1,
        stdout,
        stderr: stderr || 'Timed out after ' + timeoutMs + 'ms',
      });
    }, timeoutMs);

    child.on('close', (code) => {
      clearTimeout(timer);
      resolvePromise({ code, stdout, stderr });
    });
  });
}

function extractReportPath(stdout) {
  const htmlMatch = stdout.match(/HTML Report: (.+)/);
  const reportPath = htmlMatch ? htmlMatch[1].trim() : null;
  return reportPath ? `file://${reportPath}` : null;
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  // Serve static demo files
  if (url.pathname === '/dashboard-demo.html' || url.pathname === '/test-images.html' || url.pathname === '/test-buttons.html') {
    const filePath = resolve(__dirname, url.pathname.slice(1));
    if (existsSync(filePath)) {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(readFileSync(filePath));
      return;
    }
  }

  if (url.pathname === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(dashboardHtml);
    return;
  }

  if (url.pathname === '/check') {
    const targetUrl = url.searchParams.get('url');
    if (!targetUrl) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'URL is required' }));
      return;
    }

    console.log(`[dashboard] Running image check for: ${targetUrl}`);
    const { code, stdout, stderr } = await runChild(['broken-images-checker.js', targetUrl]);

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        success: code === 0,
        output: stdout + (stderr ? '\n' + stderr : ''),
        reportUrl: extractReportPath(stdout),
        error: code !== 0 ? stderr || 'Check failed' : undefined,
      })
    );
    return;
  }

  if (url.pathname === '/qa') {
    const suite = url.searchParams.get('suite');
    const targetUrl = url.searchParams.get('url');

    if (!targetUrl) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'URL is required' }));
      return;
    }

    console.log(`[dashboard] Running QA suite=${suite} for: ${targetUrl}`);

    let args;
    switch (suite) {
      case 'images':
        args = ['broken-images-checker.js', targetUrl];
        break;
      case 'buttons':
        args = ['button-checker.js', targetUrl];
        break;
      case 'values':
        args = ['qa/run.js', targetUrl, 'values'];
        break;
      case 'sweep':
        args = ['qa/run.js', targetUrl, 'sweep'];
        break;
      case 'full':
        args = ['qa/run.js', targetUrl, 'all'];
        break;
      default:
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Unknown suite: ' + suite }));
        return;
    }

    const { code, stdout, stderr } = await runChild(args, suite === 'full' ? 300000 : 180000);

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        success: code === 0,
        output: stdout + (stderr ? '\n' + stderr : ''),
        reportUrl: extractReportPath(stdout),
        error: code !== 0 ? stderr || 'QA run failed' : undefined,
      })
    );
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not found');
});

server.listen(PORT, () => {
  console.log(`\nUnified QA Dashboard ready: http://localhost:${PORT}`);
  console.log('Use the form to run image, button, filter-value, sweep, or full QA checks.\n');
});
