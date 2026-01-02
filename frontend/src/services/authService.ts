/**
 * Сервис для работы с авторизацией
 * Реализует регистрацию, вход, хранение токена
 */

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';
const TOKEN_KEY = 'tender_shield_token';

export interface AuthUser {
  id: number;
  email: string;
  name?: string;
  company?: string;
  tariff_id?: number;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
  company?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Сохраняет токен в localStorage
 */
export const saveToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * Получает токен из localStorage
 */
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Удаляет токен из localStorage
 */
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Получает заголовки авторизации для API запросов
 */
export const getAuthHeaders = (): HeadersInit => {
  const token = getToken();
  if (token) {
    return {
      'Authorization': `Bearer ${token}`,
    };
  }
  return {};
};

/**
 * Регистрация нового пользователя
 */
export const register = async (data: RegisterRequest): Promise<AuthUser> => {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Ошибка регистрации' }));
    throw new Error(errorData.detail || `Ошибка регистрации: ${response.status}`);
  }

  const user: AuthUser = await response.json();
  return user;
};

/**
 * Вход в систему
 */
export const login = async (data: LoginRequest): Promise<LoginResponse & { user: AuthUser }> => {
  // Нормализуем email (trim и lowercase для консистентности)
  const normalizedEmail = (data.email || '').trim().toLowerCase();
  const normalizedData = {
    ...data,
    email: normalizedEmail,
  };
  
  console.log('[AuthService] Login attempt:', { email: normalizedEmail, passwordLength: data.password?.length });
  
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(normalizedData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Неверный email или пароль' }));
    throw new Error(errorData.detail || `Ошибка входа: ${response.status}`);
  }

  const loginData: LoginResponse = await response.json();

  // Сохраняем токен
  saveToken(loginData.access_token);
  console.log('[AuthService] Token saved, getting user info...');

  // Получаем информацию о пользователе с retry механизмом
  const user = await getCurrentUserWithRetry();
  
  if (!user) {
    // Удаляем токен, если не удалось получить пользователя
    removeToken();
    throw new Error('Не удалось получить информацию о пользователе. Попробуйте войти снова.');
  }
  
  console.log('[AuthService] User info received:', { id: user.id, email: user.email });
  
  return {
    ...loginData,
    user,
  };
};

/**
 * Получение информации о текущем пользователе (с retry механизмом)
 * Внутренняя функция для использования в login
 */
const getCurrentUserWithRetry = async (maxRetries: number = 3): Promise<AuthUser | null> => {
  const token = getToken();
  if (!token) {
    console.warn('[AuthService] No token found');
    return null;
  }

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`[AuthService] Fetching user info from /auth/me (attempt ${attempt}/${maxRetries})...`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 секунд таймаут
      
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      console.log('[AuthService] /auth/me response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Ошибка получения информации о пользователе' }));
        console.error('[AuthService] /auth/me error:', response.status, errorData);
        if (response.status === 401) {
          console.warn('[AuthService] Token invalid, removing from storage');
          removeToken();
          return null;
        }
        
        // Для других ошибок пробуем повторить
        if (attempt < maxRetries) {
          const delay = 1000 * attempt; // Экспоненциальная задержка
          console.log(`[AuthService] Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        return null;
      }

      const userData: AuthUser = await response.json();
      console.log('[AuthService] User data received:', { id: userData.id, email: userData.email });
      return userData;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.error(`[AuthService] Timeout getting user info (attempt ${attempt}/${maxRetries})`);
        if (attempt < maxRetries) {
          const delay = 1000 * attempt;
          console.log(`[AuthService] Retrying after timeout in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        return null;
      }
      
      console.error(`[AuthService] Error in getCurrentUser (attempt ${attempt}/${maxRetries}):`, error);
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('[AuthService] Network error - возможно, backend не запущен или недоступен');
        if (attempt < maxRetries) {
          const delay = 1000 * attempt;
          console.log(`[AuthService] Retrying after network error in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      }
      
      // Для последней попытки возвращаем null
      if (attempt === maxRetries) {
        return null;
      }
      
      // Для других ошибок пробуем повторить
      const delay = 1000 * attempt;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  return null;
};

/**
 * Получение информации о текущем пользователе (с таймаутом)
 * Внутренняя функция для использования в getCurrentUser
 */
const getCurrentUserWithTimeout = async (signal?: AbortSignal): Promise<AuthUser | null> => {
  const token = getToken();
  if (!token) {
    console.warn('[AuthService] No token found');
    return null;
  }

  try {
    console.log('[AuthService] Fetching user info from /auth/me...');
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      signal,
    });

    console.log('[AuthService] /auth/me response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Ошибка получения информации о пользователе' }));
      console.error('[AuthService] /auth/me error:', response.status, errorData);
      if (response.status === 401) {
        console.warn('[AuthService] Token invalid, removing from storage');
        removeToken();
      }
      return null;
    }

    const userData: AuthUser = await response.json();
    console.log('[AuthService] User data received:', { id: userData.id, email: userData.email });
    return userData;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('[AuthService] Timeout getting user info');
      return null;
    }
    console.error('[AuthService] Error in getCurrentUser:', error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error('[AuthService] Network error - возможно, backend не запущен или недоступен');
    }
    return null;
  }
};

/**
 * Получение информации о текущем пользователе (публичная версия)
 */
export const getCurrentUser = async (): Promise<AuthUser | null> => {
  return getCurrentUserWithTimeout();
};

/**
 * Выход из системы
 */
export const logout = (): void => {
  removeToken();
};

/**
 * Проверка, авторизован ли пользователь
 */
export const isAuthenticated = (): boolean => {
  return getToken() !== null;
};

/**
 * Запрос на сброс пароля
 */
export const forgotPassword = async (email: string): Promise<{ ok: boolean }> => {
  try {
    // Таймаут 15 секунд
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    
    const response = await fetch(`${API_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      // Всегда возвращаем успех для безопасности (не раскрываем существование email)
      console.warn(`[ForgotPassword] HTTP ${response.status}, но возвращаем успех для безопасности`);
      return { ok: true };
    }

    const data = await response.json();
    return { ok: data.ok !== false }; // Если нет поля ok, считаем успехом
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('[ForgotPassword] Таймаут запроса');
    } else {
      console.error('[ForgotPassword] Ошибка сети:', error);
    }
    // Всегда возвращаем успех для безопасности
    return { ok: true };
  }
};

/**
 * Сброс пароля по токену
 */
export const resetPassword = async (token: string, newPassword: string): Promise<{ message: string }> => {
  const response = await fetch(`${API_URL}/auth/reset-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token, new_password: newPassword }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Ошибка сброса пароля' }));
    throw new Error(errorData.detail || `Ошибка сброса пароля: ${response.status}`);
  }

  return await response.json();
};

