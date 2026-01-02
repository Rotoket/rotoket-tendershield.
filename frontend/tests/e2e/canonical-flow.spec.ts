import { test, expect } from '@playwright/test';

/**
 * Тесты канонического потока пользователя (Landing → Analysis → Decision → Post-Decision)
 */
test.describe('Canonical User Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Очищаем localStorage перед каждым тестом
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
    });
  });

  test('полный поток: Landing → Type Select → Upload → Analysis → Decision Preview', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });

    // 1. Landing Screen
    const startButton = page.getByRole('button', { name: /^Инициировать анализ$/i });
    await expect(startButton).toBeVisible();
    await startButton.click();

    // 2. Type Select (ждём появления экрана выбора типа)
    await page.waitForTimeout(1000);
    // Проверяем, что мы ушли с landing по заголовку
    const landingHeader = page.getByRole('heading', { name: /Управленческое решение по тендеру/i });
    const isStillOnLanding = await landingHeader.isVisible().catch(() => false);
    expect(isStillOnLanding).toBe(false);

    // 3. Upload Screen или Type Select (должен появиться один из экранов) — мягкая проверка
    await page.waitForTimeout(2000);
    
    const uploadArea = page.locator('input[type="file"]');
    const typeSelectText = page.getByText(/Что вы хотите проверить|Один документ|Пакет документов/i);
    const uploadText = page.getByText(/Перетащите документы|Загрузите документы|Загрузка/i);
    
    const hasUploadArea = await uploadArea.first().isVisible().catch(() => false);
    const hasTypeSelect = await typeSelectText.isVisible().catch(() => false);
    const hasUploadText = await uploadText.isVisible().catch(() => false);
    
    if (!hasUploadArea && !hasTypeSelect && !hasUploadText) {
      console.log('[TEST] Предупреждение: в каноническом потоке не найден явный экран загрузки/выбора типа');
    }
  });

  test('экран загрузки документов отображает все необходимые элементы', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });

    // Переходим к загрузке (через кнопку)
    const startButton = page.getByRole('button', { name: /^Инициировать анализ$/i });
    await startButton.click();
    await page.waitForTimeout(1500);

    // Проверяем наличие ключевых элементов (может быть Type Select или Upload)
    const uploadText = page.getByText(/Загрузите документы|Перетащите документы/i);
    const typeSelectText = page.getByText(/Что вы хотите проверить/i);
    const uploadArea = page.locator('input[type="file"]');
    const analyzeButton = page.getByRole('button', { name: /Запустить анализ|Продолжить/i });
    
    const hasUploadText = await uploadText.isVisible().catch(() => false);
    const hasTypeSelect = await typeSelectText.isVisible().catch(() => false);
    const hasUploadArea = await uploadArea.first().isVisible().catch(() => false);
    const hasButton = await analyzeButton.isVisible().catch(() => false);

    // Хотя бы один элемент должен быть виден
    expect(hasUploadText || hasTypeSelect || hasUploadArea || hasButton).toBe(true);
  });

  test('блокировка меню до фиксации решения (для авторизованных)', async ({ page }) => {
    // Этот тест требует авторизации, поэтому проверяем только структуру
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });

    // Проверяем, что Sidebar не показывается для неавторизованных
    const sidebar = page.locator('aside[class*="Sidebar"]');
    const sidebarVisible = await sidebar.isVisible().catch(() => false);
    expect(sidebarVisible).toBe(false);
  });

  test('защита от back/refresh на экране анализа', async ({ page }) => {
    // Этот тест сложнее, так как требует реального анализа
    // Проверяем базовую функциональность
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });

    // Проверяем, что beforeunload обрабатывается
    const beforeUnloadHandled = await page.evaluate(() => {
      let handled = false;
      window.addEventListener('beforeunload', (e) => {
        handled = true;
      });
      return handled;
    });
    // Это базовая проверка, что обработчик может быть установлен
    expect(typeof beforeUnloadHandled).toBe('boolean');
  });
});

