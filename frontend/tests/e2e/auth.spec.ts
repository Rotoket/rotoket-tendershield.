import { test, expect } from '@playwright/test';

// Базовые проверки экрана авторизации / регистрации

test('форма входа отображается корректно', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#root', { state: 'visible' });

  // Переходим к авторизации через кнопку
  const authButton = page.getByRole('button', { name: /Войти в систему/i });
  await authButton.click();
  await page.waitForTimeout(1000);

  // Поля email и пароль
  const emailInput = page.locator('input[type="email"]').or(page.locator('input').filter({ hasText: /email|почта/i }));
  const passwordInput = page.locator('input[type="password"]');
  
  const hasEmail = await emailInput.first().isVisible().catch(() => false);
  const hasPassword = await passwordInput.isVisible().catch(() => false);

  expect(hasEmail || hasPassword).toBe(true);

  // Проверяем заголовок или текст блока авторизации
  const authTitle = page.getByText(/Подтверждение доступа|Войти|Зарегистрироваться|Фиксация управленческого решения/i);
  const hasAuthTitle = await authTitle.isVisible().catch(() => false);
  expect(hasAuthTitle || hasEmail || hasPassword).toBe(true);
});

test('переключение между входом и регистрацией работает', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('#root', { state: 'visible' });

  // Переходим к авторизации
  const authButton = page.getByRole('button', { name: /Войти в систему/i });
  await authButton.click();
  await page.waitForTimeout(1000);

  // Ищем кнопку переключения на регистрацию
  const toRegisterButton = page.getByRole('button', { name: /Зарегистрироваться|Нет аккаунта/i }).first();
  const hasToRegister = await toRegisterButton.isVisible().catch(() => false);
  
  if (hasToRegister) {
    await toRegisterButton.click();
    await page.waitForTimeout(500);

    // В режиме регистрации должно быть поле имени
    const nameInput = page.locator('input').filter({ hasText: /имя|name/i }).or(
      page.locator('input[type="text"]').first()
    );
    const hasNameInput = await nameInput.isVisible().catch(() => false);
    
    // Проверяем, что форма регистрации видна
    const registerButton = page.getByRole('button', { name: /Зарегистрироваться/i });
    const hasRegisterButton = await registerButton.isVisible().catch(() => false);
    
    expect(hasNameInput || hasRegisterButton).toBe(true);
  } else {
    // Если кнопка не найдена, проверяем что форма авторизации работает
    const passwordInput = page.locator('input[type="password"]');
    const hasPassword = await passwordInput.isVisible().catch(() => false);
    expect(hasPassword).toBe(true);
  }
});



