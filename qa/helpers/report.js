import { writeFileSync, mkdirSync } from 'fs';
import { resolve } from 'path';

export function ensureOutputDir(outputDir) {
  mkdirSync(resolve(outputDir, 'screenshots'), { recursive: true });
  return outputDir;
}

export function escapeHtml(text) {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function writeJSON(outputDir, fileName, data) {
  const path = resolve(outputDir, fileName);
  writeFileSync(path, JSON.stringify(data, null, 2));
  return path;
}

export function statusBadge(passed) {
  return passed
    ? '<span class="badge badge-good">PASS</span>'
    : '<span class="badge badge-bad">FAIL</span>';
}
