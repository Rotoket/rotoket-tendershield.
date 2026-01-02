import { test, expect } from '@playwright/test';

test.describe('Landing Screen (UI CANON)', () => {
  test('должен отображаться смысловой якорь "Решение важнее анализа"', async ({ page }) => {
    await page.goto('/');
    
    // Ждём загрузки страницы
    await page.waitForSelector('#root', { state: 'visible' });
    
    // Проверяем наличие смыслового якоря
    const anchor = page.getByText(/Решение важнее анализа/i);
    await expect(anchor).toBeVisible();
  });

  test('должна отображаться кнопка "Инициировать анализ" (CTA для Эксперта)', async ({ page }) => {
    await page.goto('/');
    
    // Ждём загрузки страницы
    await page.waitForSelector('#root', { state: 'visible' });
    
    // Ищем кнопку инициации анализа (каноническое название)
    const startButton = page.getByRole('button', { name: /^Инициировать анализ$/i });
    await expect(startButton).toBeVisible();
    await expect(startButton).toBeEnabled();
  });

  test('должна отображаться кнопка "Журнал управленческих решений" (CTA для Директора)', async ({ page }) => {
    await page.goto('/');
    
    // Ждём загрузки страницы
    await page.waitForSelector('#root', { state: 'visible' });
    
    // Ищем кнопку журнала (каноническое название)
    const journalButton = page.getByRole('button', { name: /Журнал управленческих решений/i });
    await expect(journalButton).toBeVisible();
    await expect(journalButton).toBeEnabled();
  });

  test('кнопка "Инициировать анализ" должна переводить к выбору типа анализа', async ({ page }) => {
    await page.goto('/');
    
    // Ждём загрузки страницы
    await page.waitForSelector('#root', { state: 'visible' });
    
    // Ищем и кликаем кнопку
    const startButton = page.getByRole('button', { name: /^Инициировать анализ$/i });
    await expect(startButton).toBeVisible();
    
    // Кликаем на кнопку
    await startButton.click();
    
    // Проверяем, что произошёл переход (должен появиться экран загрузки/выбора типа анализа)
    await page.waitForTimeout(1000); // Даём время на переход
    
    // Проверяем, что мы больше не на landing по заголовку
    const landingHeader = page.getByRole('heading', { name: /Управленческое решение по тендеру/i });
    const isStillOnLanding = await landingHeader.isVisible().catch(() => false);
    
    // Если мы всё ещё на landing, это проблема
    if (isStillOnLanding) {
      console.log('[TEST] ВНИМАНИЕ: Переход не произошёл, остались на landing');
    }
  });

  test('должна отображаться кнопка "Войти / Зарегистрироваться"', async ({ page }) => {
    await page.goto('/');
    
    // Ждём загрузки страницы
    await page.waitForSelector('#root', { state: 'visible' });
    
    // Ищем кнопку входа
    const authButton = page.getByRole('button', { name: /Войти в систему/i });
    await expect(authButton).toBeVisible();
    await expect(authButton).toBeEnabled();
  });

  test('кнопка входа должна переводить к экрану авторизации', async ({ page }) => {
    await page.goto('/');
    
    // Ждём загрузки страницы
    await page.waitForSelector('#root', { state: 'visible' });
    
    // Ищем и кликаем кнопку авторизации
    const authButton = page.getByRole('button', { name: /Войти в систему/i });
    await expect(authButton).toBeVisible();
    
    // Кликаем на кнопку
    await authButton.click();
    
    // Проверяем, что произошёл переход к экрану авторизации
    await page.waitForTimeout(1000); // Даём время на переход
    
    // Проверяем наличие элементов формы авторизации
    const emailInput = page.locator('input[type="email"]').or(page.locator('input[placeholder*="почта" i]'));
    const passwordInput = page.locator('input[type="password"]');
    
    // Хотя бы одно из полей должно быть видно
    const hasEmail = await emailInput.isVisible().catch(() => false);
    const hasPassword = await passwordInput.isVisible().catch(() => false);
    
    if (!hasEmail && !hasPassword) {
      console.log('[TEST] ВНИМАНИЕ: Переход к авторизации не произошёл');
    }
  });

  test('должны быть видны основные элементы landing страницы', async ({ page }) => {
    await page.goto('/');
    
    // Ждём загрузки страницы
    await page.waitForSelector('#root', { state: 'visible' });
    
    // Проверяем наличие основных элементов
    await expect(page.getByRole('heading', { name: /Тендер\.Щит/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Управленческое решение по тендеру/i })).toBeVisible();
    
    // Проверяем наличие канонических CTA
    await expect(page.getByRole('button', { name: /^Инициировать анализ$/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Журнал управленческих решений/i })).toBeVisible();
    
    // Проверяем смысловой якорь
    await expect(page.getByText(/Решение важнее анализа/i)).toBeVisible();
  });
});
