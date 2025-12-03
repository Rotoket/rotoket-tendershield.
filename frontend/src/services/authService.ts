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
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Неверный email или пароль' }));
    throw new Error(errorData.detail || `Ошибка входа: ${response.status}`);
  }

  const loginData: LoginResponse = await response.json();

  // Сохраняем токен
  saveToken(loginData.access_token);

  // Получаем информацию о пользователе
  const user = await getCurrentUser();
  if (!user) {
    throw new Error('Не удалось получить информацию о пользователе');
  }

  return {
    ...loginData,
    user,
  };
};

/**
 * Получение информации о текущем пользователе
 */
export const getCurrentUser = async (): Promise<AuthUser | null> => {
  const token = getToken();
  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // Токен невалиден, удаляем его
      if (response.status === 401) {
        removeToken();
      }
      return null;
    }

    const user: AuthUser = await response.json();
    return user;
  } catch (error) {
    console.error('[Auth Error]', error);
    return null;
  }
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

