import { mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { runFilterValueTests } from './specs/filter-value-change.spec.js';
import { runSectionSweep } from './specs/section-sweep.spec.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

function showUsage() {
  console.log(`\nUsage: node qa/run.js <base-url> [suite]`);
  console.log(`\nSuites:`);
  console.log(`  all      Run filter-value + section-sweep tests (default)`);
  console.log(`  values   Run filter-value change tests only`);
  console.log(`  sweep    Run section sweep tests only`);
  console.log(`\nExample:`);
  console.log(`  node qa/run.js http://localhost:8765`);
  console.log(`  node qa/run.js http://localhost:8765 values\n`);
}

function detectSuite() {
  const event = process.env.npm_lifecycle_event;
  if (event === 'qa:values') return 'values';
  if (event === 'qa:sweep') return 'sweep';
  if (event === 'qa:full') return 'all';
  return process.argv[3] || 'all';
}

async function main() {
  const baseUrl = process.argv[2];
  const suite = detectSuite();

  if (!baseUrl) {
    showUsage();
    process.exit(1);
  }

  const outputDir = resolve(__dirname, '..', 'reports', `qa-${Date.now()}`);
  mkdirSync(outputDir, { recursive: true });
  mkdirSync(resolve(outputDir, 'screenshots'), { recursive: true });

  console.log(`\n========================================`);
  console.log(`Unified QA Runner`);
  console.log(`Base URL: ${baseUrl}`);
  console.log(`Suite:    ${suite}`);
  console.log(`Output:   ${outputDir}`);
  console.log(`========================================`);

  const outcomes = [];

  if (suite === 'all' || suite === 'values') {
    const valuesOutput = resolve(outputDir, 'filter-values');
    mkdirSync(valuesOutput, { recursive: true });
    mkdirSync(resolve(valuesOutput, 'screenshots'), { recursive: true });
    const values = await runFilterValueTests(baseUrl, valuesOutput);
    outcomes.push({ name: 'Filter Value Changes', ...values });
  }

  if (suite === 'all' || suite === 'sweep') {
    const sweepOutput = resolve(outputDir, 'section-sweep');
    mkdirSync(sweepOutput, { recursive: true });
    mkdirSync(resolve(sweepOutput, 'screenshots'), { recursive: true });
    const sweep = await runSectionSweep(baseUrl, sweepOutput);
    outcomes.push({ name: 'Section Sweep', ...sweep });
  }

  console.log(`\n========================================`);
  console.log(`QA Run Complete`);
  for (const o of outcomes) {
    const status = o.allPassed ? 'PASS' : 'FAIL';
    console.log(`  [${status}] ${o.name}: ${o.summary.passed}/${o.summary.total} passed`);
    console.log(`         Report: ${o.htmlPath}`);
  }
  console.log(`========================================\n`);

  const allPassed = outcomes.every((o) => o.allPassed);
  process.exit(allPassed ? 0 : 1);
}

main().catch((err) => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
