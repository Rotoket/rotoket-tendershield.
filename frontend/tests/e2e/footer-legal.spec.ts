import { test, expect } from '@playwright/test';

test.describe('Footer legal documents', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });
  });

  test('открывается Пользовательское соглашение из подвала', async ({ page }) => {
    const link = page.getByRole('button', { name: /Пользовательское соглашение/i });
    await expect(link).toBeVisible();

    await link.click();

    const dialogTitle = page.getByRole('heading', { name: /Пользовательское соглашение/i });
    await expect(dialogTitle).toBeVisible();
  });

  test('открывается Политика конфиденциальности из подвала', async ({ page }) => {
    const link = page.getByRole('button', { name: /Политика конфиденциальности/i });
    await expect(link).toBeVisible();

    await link.click();

    const dialogTitle = page.getByRole('heading', { name: /Политика конфиденциальности/i });
    await expect(dialogTitle).toBeVisible();
  });

  test('открывается Политика обработки персональных данных из подвала', async ({ page }) => {
    const link = page.getByRole('button', { name: /Политика обработки персональных данных/i });
    await expect(link).toBeVisible();

    await link.click();

    const dialogTitle = page.getByRole('heading', { name: /Политика обработки персональных данных/i });
    await expect(dialogTitle).toBeVisible();
  });

  test('открывается Согласие на обработку персональных данных из подвала', async ({ page }) => {
    const link = page.getByRole('button', { name: /Согласие на обработку персональных данных/i });
    await expect(link).toBeVisible();

    await link.click();

    const dialogTitle = page.getByRole('heading', { name: /Согласие на обработку персональных данных/i });
    await expect(dialogTitle).toBeVisible();
  });
});

































