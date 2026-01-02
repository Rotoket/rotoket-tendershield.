import { test, expect } from '@playwright/test';

test('главная страница фронтенда открывается', async ({ page }) => {
  await page.goto('/');

  // Проверяем, что root существует
  const root = page.locator('#root');
  await expect(root).toBeVisible();

  // Проверяем, что заголовок страницы загружается без ошибки
  await expect(page).toHaveTitle(/Тендер\.Щит\.AI|Tender|Тендер/i);
});







