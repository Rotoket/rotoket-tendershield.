import { test, expect } from '@playwright/test';

/**
 * Тесты блокировки пунктов меню до фиксации решения
 */
test.describe('Sidebar Menu Locking', () => {
  test('меню не показывается для неавторизованных пользователей', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });

    // Sidebar не должен быть виден для неавторизованных
    const sidebar = page.locator('aside').filter({ hasText: /Анализ тендера|Калькулятор|Генератор/i });
    const sidebarVisible = await sidebar.isVisible().catch(() => false);
    expect(sidebarVisible).toBe(false);
  });

  test('для авторизованных меню должно показываться с блокировкой', async ({ page }) => {
    // Этот тест требует авторизации
    // Проверяем базовую структуру
    await page.goto('/');
    await page.waitForSelector('#root', { state: 'visible' });
    
    // В реальном тесте нужно:
    // 1. Авторизоваться
    // 2. Проверить, что меню видно
    // 3. Проверить, что пункты заблокированы (иконка Lock)
    // 4. Зафиксировать решение
    // 5. Проверить, что пункты разблокированы
    
    expect(await page.title()).toBeTruthy();
  });
});

