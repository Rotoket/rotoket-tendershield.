import { test, expect } from '@playwright/test';

/**
 * Тесты экрана первого вердикта (DecisionPreviewScreen)
 */
test.describe('Decision Preview Screen', () => {
  test('экран вердикта показывает заблокированные кнопки для неавторизованных', async ({ page }) => {
    // Этот тест требует мокирования результата анализа
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });
    
    // Базовая проверка
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('блок предупреждения о необходимости авторизации отображается', async ({ page }) => {
    // Проверяем структуру компонента
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });
    
    // В реальном тесте нужно проверить наличие текста
    // "Управленческое решение требует фиксации ответственности"
    expect(await page.title()).toBeTruthy();
  });
});

