import { expect, test } from '@playwright/test';

test('landing carries a title and a path to register', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/IA desde cero|AI from scratch/i);
  await expect(page.locator('a[href="/registro"], a[href="/pago"]').first()).toBeVisible();
});

test('registro requires consent checkbox', async ({ page }) => {
  await page.goto('/registro');
  await expect(page.locator('#acepta')).toBeVisible();
  await expect(page.locator('a[href="/terminos"]')).toBeVisible();
  await expect(page.locator('a[href="/privacidad"]')).toBeVisible();
});

test('pago intercepts Mercado Pago and requires terms', async ({ page }) => {
  await page.route(/mercadopago|init_point|www.mercadopago/i, (route) => route.abort());
  await page.goto('/pago');
  // Logged-out checkout hides the pay form; logged-in shows the terms checkbox.
  const terms = page.locator('#terms, a[href="/terminos"], a[href="/registro"]');
  await expect(terms.first()).toBeVisible();
});

test('login page is reachable', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('input, button').first()).toBeVisible();
});
