// Helpers for reading values and labels from the DOM.

export async function getTextByTestId(page, testId) {
  const el = page.locator(`[data-testid="${testId}"]`).first();
  const visible = await el.isVisible({ timeout: 5000 }).catch(() => false);
  if (!visible) return null;
  return el.textContent();
}

export async function getCardSnapshot(page, card) {
  const [value, label] = await Promise.all([
    getTextByTestId(page, card.valueTestId),
    getTextByTestId(page, card.labelTestId),
  ]);
  return {
    id: card.id,
    name: card.name,
    type: card.type,
    value: value?.trim() ?? null,
    label: label?.trim() ?? null,
  };
}

export async function getAllCardSnapshots(page, cards) {
  const snapshots = [];
  for (const card of cards) {
    snapshots.push(await getCardSnapshot(page, card));
  }
  return snapshots;
}
