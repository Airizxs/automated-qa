// Helpers for interacting with dashboard filters.

export async function selectChannel(page, value) {
  await page.selectOption('[data-testid="channel-filter"]', value);
  // Wait for the dashboard JS to update values.
  await page.waitForTimeout(400);
}

export async function selectDateRange(page, value) {
  await page.selectOption('[data-testid="date-filter"]', value);
  await page.waitForTimeout(400);
}

export async function getCurrentChannel(page) {
  return page.evaluate(() => document.querySelector('[data-testid="channel-filter"]').value);
}

export async function getCurrentDateRange(page) {
  return page.evaluate(() => document.querySelector('[data-testid="date-filter"]').value);
}

export async function resetFilters(page) {
  await selectChannel(page, 'all');
  await selectDateRange(page, '7');
}
