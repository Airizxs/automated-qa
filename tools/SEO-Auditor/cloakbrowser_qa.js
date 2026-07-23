#!/usr/bin/env node
/**
 * Cloakbrowser QA Test Suite
 * Usage: node cloakbrowser_qa.js
 */
import { launch } from 'cloakbrowser';

const TESTS = [
  {
    name: 'Basic page load',
    url: 'https://example.com',
    fn: async (page) => ({ title: await page.title() }),
    expect: (r) => r.title.length > 0,
  },
  {
    name: 'navigator.webdriver === false',
    url: 'https://example.com',
    fn: async (page) => ({ webdriver: await page.evaluate(() => navigator.webdriver) }),
    expect: (r) => r.webdriver === false,
  },
  {
    name: 'window.chrome exists',
    url: 'https://example.com',
    fn: async (page) => ({ chrome: await page.evaluate(() => typeof window.chrome) }),
    expect: (r) => r.chrome === 'object',
  },
  {
    name: 'navigator.plugins.length > 0',
    url: 'https://example.com',
    fn: async (page) => ({ plugins: await page.evaluate(() => navigator.plugins.length) }),
    expect: (r) => r.plugins > 0,
  },
  {
    name: 'User Agent does not contain HeadlessChrome',
    url: 'https://httpbin.org/user-agent',
    fn: async (page) => {
      const text = await page.evaluate(() => document.body.innerText);
      return { ua: text.includes('HeadlessChrome') };
    },
    expect: (r) => r.ua === false,
  },
  {
    name: 'Screenshot works',
    url: 'https://example.com',
    fn: async (page) => {
      await page.screenshot({ path: 'cloakbrowser_test.png', fullPage: true });
      return { ok: true };
    },
    expect: (r) => r.ok === true,
  },
];

async function main() {
  console.log('Cloakbrowser QA Test Suite\n');
  
  const browser = await launch({ headless: true });
  let passed = 0;
  let failed = 0;

  try {
    for (const test of TESTS) {
      try {
        const page = await browser.newPage();
        await page.goto(test.url, { timeout: 15000, waitUntil: 'domcontentloaded' });
        const result = await test.fn(page);
        await page.close();

        if (test.expect(result)) {
          console.log(`  PASS  ${test.name}`);
          passed++;
        } else {
          console.log(`  FAIL  ${test.name} — ${JSON.stringify(result)}`);
          failed++;
        }
      } catch (e) {
        console.log(`  ERROR ${test.name} — ${e.message}`);
        failed++;
      }
    }
  } finally {
    await browser.close();
  }

  console.log(`\n${passed} passed, ${failed} failed, ${TESTS.length} total`);
}

main().catch(e => console.error('FATAL:', e.message));
