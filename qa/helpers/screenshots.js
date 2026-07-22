import { resolve } from 'path';

export async function captureFullPage(page, outputDir, fileName) {
  const filePath = resolve(outputDir, 'screenshots', fileName);
  await page.screenshot({ path: filePath, fullPage: true });
  return filePath;
}

export async function captureElement(page, testId, outputDir, fileName) {
  try {
    const el = page.locator(`[data-testid="${testId}"]`).first();
    if (!(await el.isVisible({ timeout: 3000 }).catch(() => false))) return null;
    const filePath = resolve(outputDir, 'screenshots', fileName);
    await el.screenshot({ path: filePath });
    return filePath;
  } catch {
    return null;
  }
}
